from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseMemory(ABC):
    """Abstract base class for memory systems."""

    @abstractmethod
    def add(self, role: str, content: str):
        """Add a message to memory."""
        pass

    @abstractmethod
    def get_context(self) -> List[Dict[str, str]]:
        """Retrieve context for the LLM."""
        pass

    @abstractmethod
    def clear(self):
        """Clear memory."""
        pass
