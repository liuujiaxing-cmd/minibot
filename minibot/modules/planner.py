import json

from ..llm import llm_client


def _has_cjk(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def _extract_json(text: str) -> dict | None:
    clean = (text or "").strip().replace("```json", "").replace("```", "")
    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(clean[start : end + 1])
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def format_plan(plan: dict) -> str:
    steps = plan.get("steps") or []
    if not isinstance(steps, list) or not steps:
        return ""
    lang_is_zh = _has_cjk(" ".join([str(s.get("title") or "") for s in steps if isinstance(s, dict)]))

    lines = []
    id_to_number = {}
    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        sid = step.get("id")
        if isinstance(sid, int):
            id_to_number[sid] = i
        title = str(step.get("title") or "").strip()
        details = str(step.get("details") or "").strip()
        success = str(step.get("success") or "").strip()
        line = f"{i}. {title}" if title else f"{i}."
        lines.append(line)
        if details:
            lines.append(f"   - {details}")
        if success:
            label = "验收" if lang_is_zh else "Success"
            lines.append(f"   - {label}: {success}")

    groups = plan.get("parallel_groups") or []
    if isinstance(groups, list) and groups:
        lines.append("")
        lines.append("并行任务组：" if lang_is_zh else "Parallel Groups:")
        for g in groups:
            if not isinstance(g, dict):
                continue
            title = str(g.get("title") or "").strip()
            step_ids = g.get("step_ids") if isinstance(g.get("step_ids"), list) else []
            nums = []
            for sid in step_ids:
                if isinstance(sid, int) and sid in id_to_number:
                    nums.append(str(id_to_number[sid]))
            if not nums:
                continue
            header = f"- {title}" if title else "- (group)"
            lines.append(f"{header}: " + ", ".join(nums))
    return "\n".join(lines).strip()


class Planner:
    """Decomposes complex tasks into simpler subtasks."""
    
    async def decompose(self, user_intent: str) -> str:
        """
        Ask LLM to break down the task into a structured plan.
        """
        language = "Chinese" if _has_cjk(user_intent) else "English"
        simple_token = "SIMPLE"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert planning module. Your goal is to break down complex user requests into a logical, step-by-step execution plan.\n\n"
                    f"Output language: {language}.\n"
                    f"If the task is simple (can be done in 1 step or tool call), return '{simple_token}' only.\n\n"
                    "Rules:\n"
                    "1. If complex, return a numbered list of steps.\n"
                    "2. Each step must be actionable and clear.\n"
                    "3. Consider dependencies (install before execute, create before use).\n"
                    "4. Do not add any extra text outside the plan.\n"
                    "5. Prefer verbs at the start of each step.\n"
                ),
            },
            {"role": "user", "content": user_intent},
        ]
        
        plan = await llm_client.chat(messages, temperature=0.1)
        return plan.strip()

    async def decompose_structured(self, user_intent: str) -> dict:
        language = "Chinese" if _has_cjk(user_intent) else "English"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert planning module.\n"
                    "Return a structured plan as JSON only.\n\n"
                    f"Output language: {language}.\n\n"
                    "Rules:\n"
                    "- If the task is simple (can be done in 1 step or tool call), set {\"simple\": true}.\n"
                    "- Otherwise set {\"simple\": false} and provide steps.\n"
                    "- Add parallel_groups when some steps can be done concurrently (optional).\n"
                    "- Each step must be actionable.\n"
                    "- Do not include any text outside JSON.\n\n"
                    "JSON Schema:\n"
                    "{\n"
                    "  \"simple\": boolean,\n"
                    "  \"goal\": string,\n"
                    "  \"steps\": [\n"
                    "    {\n"
                    "      \"id\": number,\n"
                    "      \"title\": string,\n"
                    "      \"details\": string,\n"
                    "      \"success\": string,\n"
                    "      \"tool_hints\": [string]\n"
                    "    }\n"
                    "  ]\n"
                    "  ,\"parallel_groups\": [\n"
                    "    {\n"
                    "      \"id\": number,\n"
                    "      \"title\": string,\n"
                    "      \"step_ids\": [number]\n"
                    "    }\n"
                    "  ]\n"
                    "}\n"
                ),
            },
            {"role": "user", "content": user_intent},
        ]

        resp = await llm_client.chat(messages, temperature=0.1)
        data = _extract_json(resp)
        if not data:
            return {"simple": True, "goal": "", "steps": []}
        simple = bool(data.get("simple", False))
        goal = str(data.get("goal") or "").strip()
        steps = data.get("steps") or []
        if not isinstance(steps, list):
            steps = []
        normalized_steps = []
        for idx, step in enumerate(steps[:20], start=1):
            if not isinstance(step, dict):
                continue
            normalized_steps.append(
                {
                    "id": int(step.get("id") or idx),
                    "title": str(step.get("title") or "").strip(),
                    "details": str(step.get("details") or "").strip(),
                    "success": str(step.get("success") or "").strip(),
                    "tool_hints": step.get("tool_hints") if isinstance(step.get("tool_hints"), list) else [],
                }
            )
        groups = data.get("parallel_groups") or []
        normalized_groups = []
        if isinstance(groups, list):
            for gidx, g in enumerate(groups[:8], start=1):
                if not isinstance(g, dict):
                    continue
                step_ids = g.get("step_ids") if isinstance(g.get("step_ids"), list) else []
                normalized_groups.append(
                    {
                        "id": int(g.get("id") or gidx),
                        "title": str(g.get("title") or "").strip(),
                        "step_ids": [int(x) for x in step_ids if isinstance(x, int) or (isinstance(x, str) and str(x).isdigit())],
                    }
                )
        return {"simple": simple, "goal": goal, "steps": normalized_steps, "parallel_groups": normalized_groups}
