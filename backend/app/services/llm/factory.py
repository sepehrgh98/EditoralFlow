from app.services.llm.anthropic_service import AnthropicService
from app.services.llm.openai_service import OpenAIService


def get_llm_service(provider: str):

    if provider == "anthropic":
        return AnthropicService()

    if provider == "openai":
        return OpenAIService()

    raise ValueError(f"Unsupported provider: {provider}")