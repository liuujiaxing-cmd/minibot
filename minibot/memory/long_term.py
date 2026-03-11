import json
import os
from typing import List, Dict, Any
from .base import BaseMemory

class LongTermMemory(BaseMemory):
    """
    File-based long-term memory.
    Stores important facts or summaries in a JSON/Markdown file.
    This is not for full chat history, but for persistent knowledge.
    """
    
    def __init__(self, file_path: str = "memory.json"):
        self.file_path = file_path
        self.memories: List[Dict[str, str]] = []
        self.load()

    def load(self):
        """Load memories from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except json.JSONDecodeError:
                self.memories = []
        else:
            self.memories = []

    def save(self):
        """Save memories to file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, indent=2, ensure_ascii=False)

    def add(self, key: str, value: str):
        """Add or update a memory entry."""
        # Check if key exists, update if so
        for mem in self.memories:
            if mem["key"] == key:
                mem["value"] = value
                self.save()
                return
        
        # Else add new
        self.memories.append({"key": key, "value": value})
        self.save()

    def get(self, key: str) -> str:
        """Retrieve a specific memory."""
        for mem in self.memories:
            if mem["key"] == key:
                return mem["value"]
        return None
    
    def search(self, query: str) -> str:
        """Simple keyword search (placeholder for vector search)."""
        results = []
        query = query.lower()
        for mem in self.memories:
            if query in mem["key"].lower() or query in mem["value"].lower():
                results.append(f"- {mem['key']}: {mem['value']}")
        
        if not results:
            return "No relevant long-term memories found."
        return "Relevant Memories:\n" + "\n".join(results)

    def get_context(self) -> List[Dict[str, str]]:
        """Return all memories as a system message context string (if small)."""
        # For simplicity, we dump all memories. In production, use retrieval.
        if not self.memories:
            return []
        
        memory_text = "Long-Term Memory:\n"
        for mem in self.memories:
            memory_text += f"- {mem['key']}: {mem['value']}\n"
            
        return [{"role": "system", "content": memory_text}]

    def clear(self):
        self.memories = []
        self.save()
