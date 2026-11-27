"""Build the LLM client chosen by settings."""

from app.core.config import Settings
from app.llm.anthropic import AnthropicClient
from app.llm.base import LLMClient
from app.llm.ollama import OllamaClient


def build_llm_client(settings: Settings) -> LLMClient:
    """Return the client for `settings.llm_provider`."""
    if settings.llm_provider == "anthropic":
        return AnthropicClient(settings)
    return OllamaClient(settings)
