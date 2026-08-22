import os
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    @classmethod
    def get_available_provider(cls):
        """Returns the first available LLM provider name and validation status."""
        if cls.GEMINI_API_KEY:
            return "gemini", cls.GEMINI_API_KEY
        elif cls.OPENAI_API_KEY:
            return "openai", cls.OPENAI_API_KEY
        elif cls.ANTHROPIC_API_KEY:
            return "anthropic", cls.ANTHROPIC_API_KEY
        elif cls.GROQ_API_KEY:
            return "groq", cls.GROQ_API_KEY
        return None, None

    @classmethod
    def get_client(cls):
        """Initializes and returns the appropriate client library based on available keys."""
        provider, key = cls.get_available_provider()
        if not provider:
            raise ValueError(
                "No LLM API keys found! Please set GEMINI_API_KEY, OPENAI_API_KEY, "
                "or ANTHROPIC_API_KEY in your environment or a .env file."
            )

        if provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=key)
            return "gemini", genai
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=key)
            return "openai", client
        elif provider == "anthropic":
            # Lazy import to avoid crashes if library not installed
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            return "anthropic", client
        elif provider == "groq":
            from openai import OpenAI
            # Groq is compatible with the OpenAI SDK
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return "groq", client

        raise ValueError(f"Unsupported provider: {provider}")
