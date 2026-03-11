from typing import List, Dict
from collections import deque
from .base import BaseMemory

class ShortTermMemory(BaseMemory):
    """
    In-memory short-term memory (Context Window).
    Keeps only the last N turns of conversation.
    """
    
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        # Store messages. Each turn usually consists of user + assistant.
        # So max_len ~ max_turns * 2 (roughly)
        self.messages: deque = deque(maxlen=max_turns * 2) 

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_context(self) -> List[Dict[str, str]]:
        return list(self.messages)

    def clear(self):
        self.messages.clear()
