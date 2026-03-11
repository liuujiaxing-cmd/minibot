from openai import AsyncOpenAI
from .config import config
import os

class LLMClient:
    """Async LLM Client wrapper for OpenAI-compatible APIs."""
    
    def __init__(self):
        self.provider = config.llm_provider
        
        if self.provider == "openai":
            base_url = os.getenv("OPENAI_BASE_URL", None)
            api_key = os.getenv("OPENAI_API_KEY", config.openai_api_key)
            if not api_key:
                print("Warning: OPENAI_API_KEY not set for OpenAI provider.")
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            
        elif self.provider == "ollama":
            # Ollama typically runs on localhost:11434/v1
            self.client = AsyncOpenAI(
                base_url=f"{config.ollama_base_url}/v1",
                api_key="ollama"  # Dummy key required by library
            )
            
        elif self.provider == "deepseek":
             # Example for other providers using OpenAI format
            self.client = AsyncOpenAI(
                base_url="https://api.deepseek.com/v1",
                api_key=config.openai_api_key # Assuming using same env var or add new one
            )
            
        else:
            # Default to OpenAI if unknown, but warn
            print(f"Warning: Unknown provider '{self.provider}', defaulting to OpenAI client structure.")
            self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def chat(self, messages, model=None, temperature=0.7, **kwargs):
        """
        Send a chat completion request.
        
        Args:
            messages (list): List of message dicts (role, content).
            model (str, optional): Model name override.
            temperature (float): Sampling temperature.
            **kwargs: Additional arguments for the API.
            
        Returns:
            str: The generated response content.
        """
        model = model or config.default_model
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            if ("Connection" in str(e) or "502" in str(e)) and self.provider == "ollama":
                return f"LLM Connection Error: Is Ollama running? Please check if 'ollama serve' is running and reachable at {config.ollama_base_url}. Details: {str(e)}"
            return f"LLM Error: {str(e)}"

# Singleton instance
llm_client = LLMClient()
