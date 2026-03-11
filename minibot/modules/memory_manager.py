import json
from ..llm import llm_client
from ..memory.long_term import LongTermMemory

class MemoryManager:
    """Handles automatic extraction and management of memories."""
    
    def __init__(self):
        self.ltm = LongTermMemory(file_path="minibot_memory.json")
    
    async def auto_extract(self, user_message: str, assistant_response: str):
        """
        Analyze the conversation turn to extract facts about the user.
        This runs asynchronously and doesn't block the main response.
        """
        # Skip extraction for very short messages to save tokens
        if len(user_message) < 5:
            return

        prompt = (
            "Analyze the following conversation turn and extract any new facts about the USER.\n"
            "If the user mentioned their name, age, location, preferences, or any other personal detail, extract it.\n"
            "Return the result as a JSON object with keys as the fact name and values as the fact content.\n"
            "If no new facts are found, return an empty JSON object {}.\n"
            "IMPORTANT: Only return the JSON object, no other text.\n\n"
            f"User: {user_message}\n"
            f"Assistant: {assistant_response}\n\n"
            "JSON Output:"
        )
        
        try:
            # Use a lower temperature for extraction
            response = await llm_client.chat(
                [{"role": "user", "content": prompt}], 
                temperature=0.1,
                # response_format={"type": "json_object"} # If supported, otherwise just parse
            )
            
            # Simple parsing (assuming LLM returns JSON or JSON-like string)
            # Clean up response (remove markdown code blocks if any)
            clean_response = response.strip().replace("```json", "").replace("```", "")
            
            # Find the first { and last }
            start = clean_response.find("{")
            end = clean_response.rfind("}")
            if start != -1 and end != -1:
                clean_response = clean_response[start:end+1]
                facts = json.loads(clean_response)
                
                if facts:
                    # Filter out empty or trivial facts if needed
                    for key, value in facts.items():
                        # Check if we already know this (simple check)
                        existing = self.ltm.get(key)
                        # Only update if new or different
                        if existing != str(value):
                            self.ltm.add(key, str(value))
                            # Print a log so user can see it happening in console
                            # Use ansi colors for better visibility
                            print(f"\n\033[96m🧠 [Auto-Memory] I learned a new fact: {key} = {value}\033[0m")
                            
        except Exception as e:
            # Silently fail or log to debug file, don't spam console
            pass
