import re
import json
import ast
import asyncio
from typing import List, Dict, Any
from .llm import llm_client
from .tools import get_tools_description, execute_tool, tools_registry, load_plugins
from .memory.short_term import ShortTermMemory
from .memory.long_term import LongTermMemory
from .modules.safety import SafetyChecker
from .modules.planner import Planner
from .modules.personality import PersonalityManager
from .modules.memory_manager import MemoryManager
from .ui import ui  # Import UI

class Agent:
    """Core agent logic handling the ReAct loop."""
    
    def __init__(self, system_prompt: str = None):
        # Initialize plugins dynamically
        load_plugins()
        ui.log_event("SYSTEM", "Plugins Loaded", "Ready to serve.")
        
        self.safety = SafetyChecker()
        self.planner = Planner()
        self.personality = PersonalityManager()
        self.memory_manager = MemoryManager()
        
        self.short_term_memory = ShortTermMemory(max_turns=10)
        self.long_term_memory = LongTermMemory(file_path="minibot_memory.json")
        self.max_steps = 15  # Increased from 5 to allow for learning/installing/executing loops
        
        # Base system prompt template
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

    async def process_message(self, user_message: str) -> str:
        """Process a user message through the full cognitive pipeline."""
        
        # 1. Safety Check (Input)
        if not self.safety.check_input(user_message):
            ui.log_event("SAFETY", "Input Blocked", "Dangerous command detected.")
            return "I cannot process this request due to safety restrictions."

        # 2. Add to Short-Term Memory
        self.short_term_memory.add("user", user_message)
        
        # 3. Retrieve Context (LTM & STM)
        ui.log_event("MEMORY", "Context Retrieved", "Loading STM & LTM...")
        ltm_context = self.long_term_memory.get_context()
        stm_context = self.short_term_memory.get_context()
        
        # Extract user profile from LTM for personalization
        # Simple extraction: look for 'user_name' key in memory
        user_name = self.long_term_memory.get("user_name")
        user_profile = {"user_name": user_name} if user_name else {}
        
        # 4. Personality & Style Analysis
        style_instruction = self.personality.get_style_prompt(user_profile)
        
        # 5. Planning (Task Decomposition)
        # Only decompose if the input is complex (naive heuristic: long input or keywords)
        plan = "Standard Execution"
        if len(user_message) > 20 or "plan" in user_message.lower() or "step" in user_message.lower():
             ui.log_event("PLAN", "Decomposing Task", "Generating step-by-step plan...")
             decomposed_plan = await self.planner.decompose(user_message)
             if decomposed_plan != "SIMPLE":
                 plan = f"Follow these steps:\n{decomposed_plan}"
                 ui.log_event("PLAN", "Plan Created", decomposed_plan[:50] + "...")
        
        # 6. Prompt Engineering (Construct System Prompt)
        tools_desc = get_tools_description()
        current_system_prompt = self.system_prompt_template.format(
            style_instruction=style_instruction,
            tools_desc=tools_desc,
            plan=plan
        )
        
        # Build message chain
        messages = [{"role": "system", "content": current_system_prompt}]
        messages.extend(ltm_context)
        messages.extend(stm_context)
        
        # 7. ReAct Loop (Select Tool -> Execute -> Observe)
        step = 0
        final_response = ""
        current_turn_messages = list(messages)
        
        while step < self.max_steps:
            # Call LLM
            ui.log_event("LLM", f"Step {step+1}", "Thinking...")
            response_text = await llm_client.chat(current_turn_messages)
            
            # Check for tool usage
            tool_match = re.search(r"Action:\s*(\w+)\s*Action Input:\s*(.*?)(?:\nObservation:|$)", response_text, re.DOTALL)
            
            if tool_match:
                tool_name = tool_match.group(1).strip()
                tool_args_str = tool_match.group(2).strip()
                
                # Parse arguments
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
                    
                    # Execute tool
                    if isinstance(tool_args, dict):
                        observation = execute_tool(tool_name, **tool_args)
                    else:
                         observation = execute_tool(tool_name, tool_args)
                    
                    # Truncate observation for UI logs (full observation goes to LLM)
                    obs_preview = str(observation)[:100] + "..." if len(str(observation)) > 100 else str(observation)
                    ui.log_event("TOOL", "Observation", obs_preview)

                except Exception as e:
                    observation = f"Error parsing/executing tool: {str(e)}"
                    ui.log_event("ERROR", "Tool Execution Failed", str(e))
                
                # Update loop context
                current_turn_messages.append({"role": "assistant", "content": response_text})
                current_turn_messages.append({"role": "user", "content": f"Observation: {observation}"})
                step += 1
            else:
                final_response = response_text
                self.short_term_memory.add("assistant", final_response)
                break
        
        if not final_response:
             final_response = "I apologize, but I ran out of steps to complete your request."
        
        # 8. Safety Check (Output)
        final_response = self.safety.sanitize_output(final_response)
        
        # 9. Automatic Memory Extraction (Background Task)
        # In a real app, this should be a background task (asyncio.create_task)
        # to avoid delaying the response.
        # But for simplicity, we'll run it here or in parallel.
        # However, calling LLM again might slow down the interaction significantly if not parallel.
        # Let's use asyncio.create_task to fire and forget.
        asyncio.create_task(self.memory_manager.auto_extract(user_message, final_response))
        
        return final_response

# Singleton instance for simple usage
agent = Agent()
