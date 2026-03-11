from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Abstract base class for platform connectors."""
    
    @abstractmethod
    async def start(self):
        """Start the connector loop."""
        pass
