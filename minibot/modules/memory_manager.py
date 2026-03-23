import json
from ..llm import llm_client
from ..memory.long_term import LongTermMemory


def _has_cjk(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False

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

    async def extract_from_daily_log(self, date_str: str, markdown: str) -> dict:
        if not markdown.strip():
            return {"summary": "", "memories": {}, "fallback_summary": ""}

        language_rule = "Write the summary and memories in Chinese." if _has_cjk(markdown) else "Write the summary and memories in English."

        prompt = (
            "You are a memory consolidation module. Given a full day's conversation log in Markdown, "
            "produce (1) a concise daily summary and (2) key long-term memories worth saving.\n\n"
            f"{language_rule}\n"
            "Rules:\n"
            "- Only include durable, user-related facts, preferences, ongoing projects, commitments, and decisions.\n"
            "- Do NOT include raw chat history.\n"
            "- Output MUST be a JSON object only.\n"
            "- JSON format: {\"summary\": string, \"memories\": {string: string}}\n\n"
            f"Date: {date_str}\n\n"
            "Daily Log (Markdown):\n"
            f"{markdown}\n\n"
            "JSON Output:"
        )

        fallback_summary = "\n".join([line for line in markdown.splitlines() if line.strip()][:40])

        try:
            response = await llm_client.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            if isinstance(response, str) and response.startswith("LLM Error"):
                return {"summary": "", "memories": {}, "fallback_summary": fallback_summary}

            clean = response.strip().replace("```json", "").replace("```", "")
            start = clean.find("{")
            end = clean.rfind("}")
            if start == -1 or end == -1:
                return {"summary": "", "memories": {}, "fallback_summary": fallback_summary}
            clean = clean[start : end + 1]
            data = json.loads(clean)
            if not isinstance(data, dict):
                return {"summary": "", "memories": {}, "fallback_summary": fallback_summary}

            summary = data.get("summary") or ""
            memories = data.get("memories") or {}
            if not isinstance(memories, dict):
                memories = {}

            return {
                "summary": str(summary).strip(),
                "memories": {str(k): str(v) for k, v in memories.items()},
                "fallback_summary": fallback_summary,
            }
        except Exception:
            return {"summary": "", "memories": {}, "fallback_summary": fallback_summary}
