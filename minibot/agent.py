import re
import json
import ast
import asyncio
import os
import time
import uuid
from typing import List, Dict, Any
from .llm import llm_client
from .tools import get_tools_description, execute_tool, tools_registry, load_plugins
from .memory.short_term import ShortTermMemory
from .memory.long_term import LongTermMemory
from .modules.safety import SafetyChecker
from .modules.planner import Planner, format_plan
from .modules.personality import PersonalityManager
from .modules.memory_manager import MemoryManager
from .modules.daily_journal import daily_journal
from .memory.vector_memory import vector_memory
from .modules.perf import PerfTracer, perf_include_in_response
from .modules.checkpoint_store import save_checkpoint, load_checkpoint, latest_task_id
from .modules.task_runtime import register as register_runtime_task, cancel as cancel_runtime_task, is_running as is_task_running
from .ui import ui


def _is_chinese(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def _truncate(value: object, limit: int = 120) -> str:
    s = str(value)
    if len(s) <= limit:
        return s
    return s[:limit] + "..."

def _looks_like_failure(text: object) -> bool:
    s = str(text).lower()
    return any(k in s for k in ["error", "failed", "timed out", "timeout", "not found", "exception", "traceback"])


def _extract_paths(text: object) -> List[str]:
    s = str(text)
    paths: List[str] = []
    for m in re.findall(r"(~/[^\s'\"`]+|/Users/[^\s'\"`]+)", s):
        paths.append(m)
    seen = set()
    out: List[str] = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _verify_existing_paths(paths: List[str]) -> List[str]:
    verified: List[str] = []
    for p in paths:
        try:
            expanded = os.path.expanduser(p)
            if os.path.exists(expanded):
                verified.append(p)
        except Exception:
            continue
    return verified


def _needs_audit_disclaimer(core_response: str, executed_steps: List[Dict[str, Any]]) -> bool:
    if executed_steps:
        return False
    s = core_response or ""
    if not s:
        return False
    if not re.search(r"(/Users/|~/)", s) and not any(k in s for k in ["文件", "文件夹", "目录", "脚本"]):
        return False
    return bool(re.search(r"(已|已经)\s*(创建|生成|写入|保存|上传|部署|完成)", s))


def _needs_failure_disclaimer(core_response: str, failures: List[str]) -> bool:
    if not failures:
        return False
    s = core_response or ""
    if not s:
        return False
    if re.search(r"(全部|已经|已)\s*(完成|成功|创建|生成|保存|部署|上传)", s) or "✅" in s:
        return True
    return False


def _should_decompose(user_message: str) -> bool:
    text = user_message.strip()
    if not text:
        return False

    lower = text.lower()
    if "\n" in text:
        return True

    if re.search(r"(^|\n)\s*\d+[\.\)]\s+", text):
        return True

    if len(text) >= 60:
        return True

    if len(re.findall(r"[。！？!?;；]", text)) >= 2:
        return True

    en_keys = [
        "plan",
        "step",
        "steps",
        "workflow",
        "checklist",
        "todo",
        "break down",
        "decompose",
    ]
    if any(k in lower for k in en_keys):
        return True

    zh_keys = ["计划", "步骤", "流程", "拆解", "分解", "依次", "分别"]
    if any(k in text for k in zh_keys):
        return True

    connectors = ["然后", "接着", "之后", "同时", "并且", "先", "再", "最后", "另外"]
    connector_hits = sum(text.count(k) for k in connectors)
    if connector_hits >= 2:
        return True

    if "支持" in text:
        if any(k in text for k in ["并", "以及", "同时"]):
            return True
        if len(re.findall(r"[、/,，,]", text)) >= 2:
            return True

    return False


def _parse_resume_task_id(user_message: str) -> str | None:
    text = (user_message or "").strip()
    if not text:
        return None
    m = re.match(r"^(?:resume|继续|恢复)\b\s*([a-f0-9]{8,64})?\s*$", text, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1)
    if v:
        return v.lower()
    return None


def _parse_control_command(user_message: str) -> Dict[str, str] | None:
    text = (user_message or "").strip()
    if not text:
        return None

    m = re.match(r"^(?:status|状态)\b\s*([a-f0-9]{8,64})?\s*$", text, re.IGNORECASE)
    if m:
        return {"cmd": "status", "task_id": (m.group(1) or "").lower()}

    m = re.match(r"^(?:pause|暂停)\b\s*([a-f0-9]{8,64})?\s*$", text, re.IGNORECASE)
    if m:
        return {"cmd": "pause", "task_id": (m.group(1) or "").lower()}

    m = re.match(r"^(?:cancel|取消)\b\s*([a-f0-9]{8,64})?\s*$", text, re.IGNORECASE)
    if m:
        return {"cmd": "cancel", "task_id": (m.group(1) or "").lower()}

    m = re.match(r"^(?:bg|后台)\b[:：]?\s+(.+)$", text, re.IGNORECASE | re.DOTALL)
    if m:
        return {"cmd": "bg", "message": m.group(1).strip()}

    return None

class Agent:
    """Core agent logic handling the ReAct loop."""
    
    def __init__(self, system_prompt: str = None):
        load_plugins()
        ui.log_event("SYSTEM", "Plugins Loaded", "Ready to serve.")
        
        self.safety = SafetyChecker()
        self.planner = Planner()
        self.personality = PersonalityManager()
        self.memory_manager = MemoryManager()
        
        self.short_term_memory = ShortTermMemory(max_turns=10)
        self.long_term_memory = LongTermMemory(file_path="minibot_memory.json")
        self.max_steps = 50
        
        soul_path = os.path.join(os.path.dirname(__file__), "soul.txt")
        if os.path.exists(soul_path):
            with open(soul_path, "r", encoding="utf-8") as f:
                self.system_prompt_template = f.read()
        else:
            self.system_prompt_template = (
                "You are Minibot, a helpful AI assistant. Always respond in the user's language.\n"
                "{style_instruction}\n"
                "You have access to the following tools:\n"
                "{tools_desc}\n\n"
                "Task Plan: {plan}\n\n"
                "To use a tool, you MUST use the following format:\n"
                "Thought: <your reasoning>\n"
                "Action: <tool_name>\n"
                "Action Input: <json_arguments>\n"
                "Observation: <result of the tool>\n\n"
                "Example:\n"
                "Action: remember\n"
                "Action Input: {{\"key\": \"birthday\", \"value\": \"2000-01-01\"}}\n\n"
                "Important Rules:\n"
                "1. ALWAYS check the current date using 'get_current_time' before calculating age or time durations.\n"
                "2. If the user provides personal information (name, birthday, preferences), use the 'remember' tool to save it.\n"
                "3. If you need to recall information, use the 'recall' tool.\n"
                "4. If you have enough information to answer, just reply directly without using tools.\n"
                "5. Do NOT use tools if not necessary.\n"
                "6. Do NOT provide explanations about tools, just use them.\n"
                "7. Output ONLY the 'Action' and 'Action Input' when using a tool.\n"
                "8. Speak Chinese if the user speaks Chinese.\n"
                "9. LEARNING PROTOCOL (CRITICAL):\n"
                "   - NEVER refuse a request by saying you 'cannot' do something or that you lack knowledge.\n"
                "   - If a task requires a skill you don't have (e.g., getting news, checking weather, controlling apps), you MUST:\n"
                "     a. Discover: Action: find_skills(query='xxx')\n"
                "     b. If found in Vercel Remote: Action: add_skill_from_git(repo='...', skill_name='...')\n"
                "     c. If found in Local Remote: Action: install_skill(skill_name='xxx')\n"
                "     d. Then Execute it: Action: execute_skill(skill_name='xxx')\n"
                "   - If not found in any marketplace, use your internal knowledge to WRITE a bash function and use 'add_skill' to save it.\n"
                "   - BE AUTONOMOUS. Do not ask for permission to learn. Just do it."
            )

    def _new_task_id(self) -> str:
        return uuid.uuid4().hex

    def _save_checkpoint(self, task_id: str, payload: Dict[str, Any]) -> None:
        try:
            save_checkpoint(task_id, payload)
        except Exception:
            pass

    async def _parallel_agent_notes(self, base_messages: List[Dict[str, str]], user_message: str, plan_text: str, use_zh: bool, perf: PerfTracer) -> Dict[str, str]:
        system_common = (
            "You must not call tools. You must not claim to have created files, executed commands, or verified results.\n"
            "Return only actionable notes, assumptions, and risks. Keep it concise.\n"
        )
        if use_zh:
            system_common = (
                "你不得调用任何工具。你不得宣称已创建文件、已执行命令或已验证结果。\n"
                "只输出可执行的要点、假设与风险，保持简洁。\n"
            )

        researcher_system = (
            "Role: Researcher.\n"
            + system_common
            + "Focus: gather needed info, propose parallel subtasks, list what to check.\n"
        )
        reviewer_system = (
            "Role: Reviewer.\n"
            + system_common
            + "Focus: detect missing steps, contradictions, unsafe claims, and acceptance criteria.\n"
        )
        if use_zh:
            researcher_system = (
                "角色：Researcher（信息收集）。\n"
                + system_common
                + "重点：需要补充的信息、可并行的子任务、要验证的点。\n"
            )
            reviewer_system = (
                "角色：Reviewer（复核）。\n"
                + system_common
                + "重点：缺失步骤、矛盾点、可能的虚假完成宣称、验收标准。\n"
            )

        payload = f"User request:\n{user_message}\n\nPlan:\n{plan_text}".strip()
        r_msgs = [{"role": "system", "content": researcher_system}] + base_messages + [{"role": "user", "content": payload}]
        v_msgs = [{"role": "system", "content": reviewer_system}] + base_messages + [{"role": "user", "content": payload}]

        async def _call(msgs: List[Dict[str, str]]):
            return await llm_client.chat(msgs)

        ts = time.perf_counter()
        try:
            res, rev = await asyncio.gather(
                asyncio.wait_for(_call(r_msgs), timeout=20),
                asyncio.wait_for(_call(v_msgs), timeout=20),
            )
            perf.mark("parallel_agents", (time.perf_counter() - ts) * 1000.0)
            return {"researcher": str(res).strip(), "reviewer": str(rev).strip()}
        except Exception:
            perf.mark("parallel_agents", (time.perf_counter() - ts) * 1000.0)
            return {}

    async def _react_loop(
        self,
        current_turn_messages: List[Dict[str, str]],
        user_message: str,
        style_instruction: str,
        tools_desc: str,
        plan: str,
        structured_plan: Dict[str, Any] | None,
        decomposed_plan: str | None,
        executed_steps: List[Dict[str, Any]],
        failures: List[str],
        replan_count: int,
        perf: PerfTracer,
        task_id: str | None,
        start_step: int = 0,
    ) -> Dict[str, Any]:
        step = start_step
        final_response = ""
        while step < self.max_steps:
            if task_id:
                try:
                    st = (load_checkpoint(task_id) or {}).get("status")
                    if st in {"paused", "canceled", "cancelled"}:
                        final_response = "已暂停。" if st == "paused" else "已取消。"
                        break
                except Exception:
                    pass
            ui.log_event("LLM", f"Step {step+1}", "Thinking...")
            ts = time.perf_counter()
            response_text = await llm_client.chat(current_turn_messages)
            perf.mark("llm_chat", (time.perf_counter() - ts) * 1000.0, {"step": step + 1})
            perf.incr("llm_calls", 1)

            tool_match = re.search(r"Action:\s*(\w+)\s*Action Input:\s*(.*?)(?:\nObservation:|$)", response_text, re.DOTALL)
            if tool_match:
                tool_name = tool_match.group(1).strip()
                tool_args_str = tool_match.group(2).strip()

                try:
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        try:
                            tool_args = ast.literal_eval(tool_args_str)
                        except (ValueError, SyntaxError):
                            if tool_args_str.startswith("{") or tool_args_str.startswith("["):
                                raise ValueError("Invalid JSON/Dict format")
                            tool_args = {"arg": tool_args_str}

                    ui.log_event("TOOL", f"Executing {tool_name}", str(tool_args))
                    ts = time.perf_counter()
                    if isinstance(tool_args, dict):
                        observation = execute_tool(tool_name, **tool_args)
                    else:
                        observation = execute_tool(tool_name, tool_args)
                    tool_ms = (time.perf_counter() - ts) * 1000.0
                    perf.mark("tool_exec", tool_ms, {"tool": tool_name})
                    perf.incr("tool_calls", 1)

                    obs_preview = str(observation)[:100] + "..." if len(str(observation)) > 100 else str(observation)
                    ui.log_event("TOOL", "Observation", obs_preview)
                    ok = not _looks_like_failure(observation)
                    evidence_paths: List[str] = []
                    try:
                        if isinstance(tool_args, dict):
                            for key in ["path", "file_path", "dir", "directory", "output", "out_path", "target_path"]:
                                v = tool_args.get(key)
                                if isinstance(v, str) and v:
                                    evidence_paths.extend(_extract_paths(v))
                        evidence_paths.extend(_extract_paths(observation))
                    except Exception:
                        evidence_paths = []
                    verified_paths = _verify_existing_paths(evidence_paths)
                    executed_steps.append(
                        {
                            "tool": tool_name,
                            "args": _truncate(tool_args, 120),
                            "observation": _truncate(observation, 160),
                            "ok": ok,
                            "verified_paths": verified_paths[:6],
                        }
                    )
                    if not ok:
                        failures.append(f"{tool_name}: {_truncate(observation, 180)}")
                        perf.incr("tool_failures", 1)

                    if structured_plan and len(failures) >= 3 and replan_count < 1:
                        replan_count += 1
                        ui.log_event("PLAN", "Replanning", _truncate("\n".join(failures[-3:]), 160))
                        ts = time.perf_counter()
                        sp2 = await self.planner.decompose_structured(
                            user_message + "\n\nKnown failures:\n" + "\n".join(failures[-5:])
                        )
                        perf.mark("planner_replan_structured", (time.perf_counter() - ts) * 1000.0)
                        if sp2 and not sp2.get("simple", False):
                            structured_plan = sp2
                            decomposed_plan = format_plan(sp2)
                            if decomposed_plan:
                                plan = f"Follow these steps:\n{decomposed_plan}"
                                current_system_prompt = self.system_prompt_template.format(
                                    style_instruction=style_instruction,
                                    tools_desc=tools_desc,
                                    plan=plan,
                                )
                                current_turn_messages[0]["content"] = current_system_prompt
                                failures = []

                except Exception as e:
                    observation = f"Error parsing/executing tool: {str(e)}"
                    ui.log_event("ERROR", "Tool Execution Failed", str(e))

                current_turn_messages.append({"role": "assistant", "content": response_text})
                current_turn_messages.append({"role": "user", "content": f"Observation: {observation}"})
                step += 1

                if task_id:
                    self._save_checkpoint(
                        task_id,
                        {
                            "status": "running",
                            "original_user_message": user_message,
                            "current_turn_messages": current_turn_messages,
                            "step": step,
                            "plan": plan,
                            "decomposed_plan": decomposed_plan,
                            "structured_plan": structured_plan,
                            "executed_steps": executed_steps,
                            "failures": failures,
                            "replan_count": replan_count,
                        },
                    )
            else:
                final_response = response_text
                break

        return {
            "final_response": final_response,
            "step": step,
            "executed_steps": executed_steps,
            "failures": failures,
            "replan_count": replan_count,
            "plan": plan,
            "decomposed_plan": decomposed_plan,
            "structured_plan": structured_plan,
            "current_turn_messages": current_turn_messages,
        }

    async def _finalize_turn(
        self,
        user_message: str,
        core_response: str,
        plan: str,
        decomposed_plan: str | None,
        structured_plan: Dict[str, Any] | None,
        executed_steps: List[Dict[str, Any]],
        failures: List[str],
        perf: PerfTracer,
        t0: float,
        step: int,
        replan_count: int,
    ) -> str:
        if not core_response:
            core_response = "I apologize, but I ran out of steps to complete your request."

        use_zh = _is_chinese(user_message)
        core_response = self.safety.sanitize_output(core_response)
        if _needs_audit_disclaimer(core_response, executed_steps):
            if use_zh:
                core_response = "注意：我在这轮对话里没有执行任何工具/命令，也没有对文件系统做修改；下面内容是建议或计划，并非已落地结果。\n\n" + core_response
            else:
                core_response = "Note: I did not execute any tools/commands or modify the filesystem in this turn; the content below is advice/plan, not a completed result.\n\n" + core_response
        elif _needs_failure_disclaimer(core_response, failures):
            if use_zh:
                core_response = "注意：本轮执行中存在失败或未完成的步骤；下面若出现“已完成/已创建/已成功”等表述，请以“工具执行记录”里的实际观察结果为准。\n\n" + core_response
            else:
                core_response = "Note: There were failed or incomplete steps in this turn; if the text below claims completion, trust the tool execution record and observations instead.\n\n" + core_response

        plan_prefix = ""
        if decomposed_plan:
            if use_zh:
                plan_prefix = "任务分解（自动生成）：\n" + decomposed_plan.strip()
            else:
                plan_prefix = "Task Breakdown (Auto):\n" + decomposed_plan.strip()

        header = "我刚才做了这些：" if use_zh else "Here is what I did:"
        lines = [header]
        idx = 1
        if plan and plan != "Standard Execution":
            if use_zh:
                lines.append(f"{idx}. 生成并采用任务计划：{_truncate(plan, 200)}")
            else:
                lines.append(f"{idx}. Created and followed a task plan: {_truncate(plan, 200)}")
            idx += 1

        if executed_steps:
            for item in executed_steps:
                status = "成功" if item.get("ok") else "失败/未完成"
                verified = item.get("verified_paths") or []
                verified_text = ""
                if verified:
                    verified_text = "，已确认存在：" + ", ".join(verified) if use_zh else "; verified exists: " + ", ".join(verified)
                if use_zh:
                    lines.append(
                        f"{idx}. 调用 `{item['tool']}`（{status}），参数：{item['args']}，结果：{item['observation']}{verified_text}"
                    )
                else:
                    lines.append(
                        f"{idx}. Called `{item['tool']}` ({'ok' if item.get('ok') else 'failed'}), args: {item['args']}; result: {item['observation']}{verified_text}"
                    )
                idx += 1
        else:
            if use_zh:
                lines.append(f"{idx}. 直接分析并给出答复（未调用工具，也未对文件系统做修改）")
            else:
                lines.append(f"{idx}. Answered directly (no tool calls; no filesystem changes)")

        perf.mark("total_turn", (time.perf_counter() - t0) * 1000.0, {"steps": step, "replans": replan_count})
        summary = perf.summary()
        if summary.get("enabled"):
            top = summary.get("top_spans") or []
            top_text = ", ".join([f"{t.get('name')}={t.get('ms')}ms" for t in top[:5]])
            ui.log_event("PERF", f"total={summary.get('total_ms')}ms", top_text)
            try:
                path = perf.persist(
                    {
                        "ts": summary.get("ts"),
                        "message_len": len(user_message),
                        "steps": step,
                        "replans": replan_count,
                    }
                )
                if path:
                    ui.log_event("PERF", "logged", path)
            except Exception:
                pass

        perf_prefix = ""
        if summary.get("enabled") and perf_include_in_response():
            if use_zh:
                perf_prefix = f"性能统计：总耗时 {summary.get('total_ms')}ms，LLM 调用 {summary.get('counts', {}).get('llm_calls', 0)} 次，工具调用 {summary.get('counts', {}).get('tool_calls', 0)} 次"
            else:
                perf_prefix = f"Performance: total {summary.get('total_ms')}ms, LLM calls {summary.get('counts', {}).get('llm_calls', 0)}, tool calls {summary.get('counts', {}).get('tool_calls', 0)}"

        prefix_parts = ["\n".join(lines)]
        if perf_prefix:
            prefix_parts.append(perf_prefix)
        if plan_prefix:
            prefix_parts.append(plan_prefix)
        final_response = "\n\n".join(prefix_parts) + "\n\n" + core_response

        asyncio.create_task(self.memory_manager.auto_extract(user_message, final_response))

        try:
            if daily_journal:
                daily_journal.append_turn("Minibot", final_response)
        except Exception:
            pass

        try:
            if vector_memory:
                core = final_response
                if core.startswith("我刚才做了这些：") or core.startswith("Here is what I did:"):
                    parts = core.split("\n\n", 1)
                    if len(parts) == 2:
                        core = parts[1]
                if core.startswith("性能统计：") or core.startswith("Performance:"):
                    parts = core.split("\n\n", 1)
                    if len(parts) == 2:
                        core = parts[1]
                if core.startswith("任务分解（自动生成）：") or core.startswith("Task Breakdown (Auto):"):
                    parts = core.split("\n\n", 1)
                    if len(parts) == 2:
                        core = parts[1]
                asyncio.create_task(vector_memory.add("assistant", core, {"type": "turn"}))
        except Exception:
            pass

        self.short_term_memory.add("assistant", final_response)
        return final_response

    async def _resume_from_checkpoint(self, task_id: str, perf: PerfTracer, t0: float) -> str:
        cp = load_checkpoint(task_id)
        if not cp:
            return f"找不到任务 {task_id} 的检查点。"

        original_user_message = str(cp.get("original_user_message") or "")
        current_turn_messages = cp.get("current_turn_messages") or []
        if not isinstance(current_turn_messages, list) or not current_turn_messages:
            return "检查点数据不完整，无法恢复。" if _is_chinese(original_user_message) else "Checkpoint is incomplete; cannot resume."

        executed_steps = cp.get("executed_steps") or []
        failures = cp.get("failures") or []
        replan_count = int(cp.get("replan_count") or 0)
        step = int(cp.get("step") or 0)
        plan = str(cp.get("plan") or "Standard Execution")
        decomposed_plan = cp.get("decomposed_plan")
        structured_plan = cp.get("structured_plan")

        use_zh = _is_chinese(original_user_message) or _is_chinese(str(cp.get("use_zh") or ""))
        user_name = self.long_term_memory.get("user_name")
        user_profile = {"user_name": user_name} if user_name else {}
        style_instruction = self.personality.get_style_prompt(user_profile)
        tools_desc = get_tools_description()

        result = await self._react_loop(
            current_turn_messages=current_turn_messages,
            user_message=original_user_message,
            style_instruction=style_instruction,
            tools_desc=tools_desc,
            plan=plan,
            structured_plan=structured_plan,
            decomposed_plan=decomposed_plan,
            executed_steps=executed_steps,
            failures=failures,
            replan_count=replan_count,
            perf=perf,
            task_id=task_id,
            start_step=step,
        )

        final = await self._finalize_turn(
            user_message=original_user_message,
            core_response=str(result.get("final_response") or ""),
            plan=str(result.get("plan") or plan),
            decomposed_plan=result.get("decomposed_plan"),
            structured_plan=result.get("structured_plan"),
            executed_steps=result.get("executed_steps") or [],
            failures=result.get("failures") or [],
            perf=perf,
            t0=t0,
            step=int(result.get("step") or 0),
            replan_count=int(result.get("replan_count") or 0),
        )
        self._save_checkpoint(task_id, {"status": "completed", "final_response": final})
        return final

    async def process_message(self, user_message: str, forced_task_id: str | None = None, background: bool = False) -> str:
        """Process a user message through the full cognitive pipeline."""
        perf = PerfTracer()
        t0 = time.perf_counter()
        
        ts = time.perf_counter()
        safe_ok = self.safety.check_input(user_message)
        perf.mark("safety_check_input", (time.perf_counter() - ts) * 1000.0)
        if not safe_ok:
            ui.log_event("SAFETY", "Input Blocked", "Dangerous command detected.")
            return "I cannot process this request due to safety restrictions."

        ctrl = _parse_control_command(user_message)
        if ctrl:
            cmd = ctrl.get("cmd")
            tid = ctrl.get("task_id") or (latest_task_id() or "")
            if cmd == "bg":
                msg = (ctrl.get("message") or "").strip()
                if not msg:
                    return "用法：后台 <要执行的任务>"
                task_id = self._new_task_id()
                self._save_checkpoint(task_id, {"status": "queued", "original_user_message": msg, "step": 0})
                t = asyncio.create_task(self.process_message(msg, forced_task_id=task_id, background=True))
                register_runtime_task(task_id, t)
                return f"已在后台启动任务。任务ID：{task_id}\n- 查看：状态 {task_id}\n- 暂停：暂停 {task_id}\n- 取消：取消 {task_id}\n- 恢复：继续 {task_id}"
            if not tid:
                return "没有可用的任务ID。"
            if cmd == "status":
                cp = load_checkpoint(tid) or {}
                status = str(cp.get("status") or "unknown")
                step = cp.get("step")
                running = is_task_running(tid)
                last_tool = ""
                try:
                    xs = cp.get("executed_steps") or []
                    if xs:
                        last_tool = str(xs[-1].get("tool") or "")
                except Exception:
                    last_tool = ""
                parts = [f"任务ID：{tid}", f"状态：{status}" + ("（运行中）" if running else ""), f"步骤：{step if step is not None else '-'}"]
                if last_tool:
                    parts.append(f"最近工具：{last_tool}")
                return "\n".join(parts)
            if cmd == "pause":
                cp = load_checkpoint(tid) or {"original_user_message": ""}
                cp["status"] = "paused"
                save_checkpoint(tid, cp)
                return f"已请求暂停。任务ID：{tid}"
            if cmd == "cancel":
                cp = load_checkpoint(tid) or {"original_user_message": ""}
                cp["status"] = "canceled"
                save_checkpoint(tid, cp)
                cancel_runtime_task(tid)
                return f"已请求取消。任务ID：{tid}"

        if re.match(r"^(?:resume|继续|恢复)\b", (user_message or "").strip(), re.IGNORECASE):
            tid = _parse_resume_task_id(user_message) or (latest_task_id() or "")
            if not tid:
                return "没有可恢复的任务检查点。"
            return await self._resume_from_checkpoint(tid, perf, t0)

        ts = time.perf_counter()
        self.short_term_memory.add("user", user_message)
        perf.mark("stm_add_user", (time.perf_counter() - ts) * 1000.0)

        ts = time.perf_counter()
        try:
            if daily_journal:
                daily_journal.append_turn("用户", user_message)
        except Exception:
            pass
        perf.mark("daily_journal_append_user", (time.perf_counter() - ts) * 1000.0)

        ts = time.perf_counter()
        try:
            if vector_memory:
                asyncio.create_task(vector_memory.add("user", user_message, {"type": "turn"}))
        except Exception:
            pass
        perf.mark("vector_add_user_scheduled", (time.perf_counter() - ts) * 1000.0)
        
        ui.log_event("MEMORY", "Context Retrieved", "Loading STM & LTM...")
        ts = time.perf_counter()
        ltm_context = self.long_term_memory.get_context()
        perf.mark("ltm_get_context", (time.perf_counter() - ts) * 1000.0)
        vector_context = []
        try:
            if vector_memory:
                ts = time.perf_counter()
                vector_context = await vector_memory.get_context(user_message, top_k=5)
                perf.mark("vector_get_context", (time.perf_counter() - ts) * 1000.0)
        except Exception:
            vector_context = []
        ts = time.perf_counter()
        stm_context = self.short_term_memory.get_context()
        perf.mark("stm_get_context", (time.perf_counter() - ts) * 1000.0)
        
        user_name = self.long_term_memory.get("user_name")
        user_profile = {"user_name": user_name} if user_name else {}
        
        style_instruction = self.personality.get_style_prompt(user_profile)
        
        plan = "Standard Execution"
        decomposed_plan = None
        structured_plan = None
        if _should_decompose(user_message):
             ui.log_event("PLAN", "Decomposing Task", "Generating step-by-step plan...")
             ts = time.perf_counter()
             sp = await self.planner.decompose_structured(user_message)
             perf.mark("planner_decompose_structured", (time.perf_counter() - ts) * 1000.0)
             if sp and not sp.get("simple", False):
                 structured_plan = sp
                 decomposed_plan = format_plan(sp)
                 if decomposed_plan:
                     plan = f"Follow these steps:\n{decomposed_plan}"
                     ui.log_event("PLAN", "Plan Created", decomposed_plan[:50] + "...")
        
        ts = time.perf_counter()
        tools_desc = get_tools_description()
        current_system_prompt = self.system_prompt_template.format(
            style_instruction=style_instruction,
            tools_desc=tools_desc,
            plan=plan
        )
        perf.mark("prompt_build", (time.perf_counter() - ts) * 1000.0)
        
        messages = [{"role": "system", "content": current_system_prompt}]
        messages.extend(ltm_context)
        messages.extend(vector_context)
        messages.extend(stm_context)
        current_turn_messages = list(messages)
        executed_steps: List[Dict[str, Any]] = []
        failures: List[str] = []
        replan_count = 0

        use_zh = _is_chinese(user_message)
        task_id = forced_task_id or (self._new_task_id() if structured_plan else None)

        if task_id and forced_task_id:
            try:
                existing = load_checkpoint(task_id) or {}
                st = str(existing.get("status") or "").lower()
                if st in {"paused", "canceled", "cancelled"}:
                    return "已暂停。" if st == "paused" else "已取消。"
            except Exception:
                pass

        if structured_plan:
            notes = await self._parallel_agent_notes(
                base_messages=ltm_context + vector_context + stm_context,
                user_message=user_message,
                plan_text=plan,
                use_zh=use_zh,
                perf=perf,
            )
            if notes:
                if use_zh:
                    block = "并行代理要点：\n\n" + "Researcher：\n" + notes.get("researcher", "").strip() + "\n\nReviewer：\n" + notes.get("reviewer", "").strip()
                else:
                    block = "Parallel Agent Notes:\n\nResearcher:\n" + notes.get("researcher", "").strip() + "\n\nReviewer:\n" + notes.get("reviewer", "").strip()
                current_turn_messages.append({"role": "user", "content": block})

        if task_id:
            self._save_checkpoint(
                task_id,
                {
                    "status": "running",
                    "use_zh": use_zh,
                    "original_user_message": user_message,
                    "current_turn_messages": current_turn_messages,
                    "step": 0,
                    "plan": plan,
                    "decomposed_plan": decomposed_plan,
                    "structured_plan": structured_plan,
                    "executed_steps": executed_steps,
                    "failures": failures,
                    "replan_count": replan_count,
                },
            )

        pause_req = ("暂停" in user_message) or ("pause" in user_message.lower())
        if pause_req and task_id:
            self._save_checkpoint(
                task_id,
                {
                    "status": "paused",
                    "use_zh": use_zh,
                    "original_user_message": user_message,
                    "current_turn_messages": current_turn_messages,
                    "step": 0,
                    "plan": plan,
                    "decomposed_plan": decomposed_plan,
                    "structured_plan": structured_plan,
                    "executed_steps": executed_steps,
                    "failures": failures,
                    "replan_count": replan_count,
                },
            )
            if use_zh:
                return f"已暂停并保存检查点。任务ID：{task_id}\n发送：继续 {task_id} 来恢复执行。"
            return f"Paused. Task ID: {task_id}\nSend: resume {task_id} to continue."

        result = await self._react_loop(
            current_turn_messages=current_turn_messages,
            user_message=user_message,
            style_instruction=style_instruction,
            tools_desc=tools_desc,
            plan=plan,
            structured_plan=structured_plan,
            decomposed_plan=decomposed_plan,
            executed_steps=executed_steps,
            failures=failures,
            replan_count=replan_count,
            perf=perf,
            task_id=task_id,
            start_step=0,
        )

        final = await self._finalize_turn(
            user_message=user_message,
            core_response=str(result.get("final_response") or ""),
            plan=str(result.get("plan") or plan),
            decomposed_plan=result.get("decomposed_plan"),
            structured_plan=result.get("structured_plan"),
            executed_steps=result.get("executed_steps") or [],
            failures=result.get("failures") or [],
            perf=perf,
            t0=t0,
            step=int(result.get("step") or 0),
            replan_count=int(result.get("replan_count") or 0),
        )

        if task_id:
            self._save_checkpoint(task_id, {"status": "completed", "final_response": final})
        return final

agent = Agent()
