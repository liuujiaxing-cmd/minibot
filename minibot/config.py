import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management for Minibot."""
    
    def __init__(self):
        # LLM Settings
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Bot Identity
        self.bot_name = os.getenv("BOT_NAME", "minibot")
        self.default_model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        
        # Connector Tokens
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.discord_token = os.getenv("DISCORD_BOT_TOKEN")

    def validate(self):
        """Validate critical configuration."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider.")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider.")
            
# Singleton instance
config = Config()
