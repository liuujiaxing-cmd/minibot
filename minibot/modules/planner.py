from ..llm import llm_client

class Planner:
    """Decomposes complex tasks into simpler subtasks."""
    
    async def decompose(self, user_intent: str) -> str:
        """
        Ask LLM to break down the task.
        """
        messages = [
            {"role": "system", "content": "You are a planning module. Your job is to break down a complex user request into a simple, numbered list of steps. If the task is simple (1 step), just return 'SIMPLE'. Do not add any other text."},
            {"role": "user", "content": user_intent}
        ]
        
        plan = await llm_client.chat(messages, temperature=0.1)
        return plan.strip()
