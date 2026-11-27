from app.core.config import Settings
from app.llm.anthropic import AnthropicClient
from app.llm.factory import build_llm_client
from app.llm.ollama import OllamaClient
from app.llm.pricing import estimate_cost


def test_default_provider_is_ollama() -> None:
    assert isinstance(build_llm_client(Settings(_env_file=None)), OllamaClient)  # type: ignore[call-arg]


def test_anthropic_provider() -> None:
    settings = Settings(_env_file=None, llm_provider="anthropic", anthropic_api_key="k")  # type: ignore[call-arg]
    assert isinstance(build_llm_client(settings), AnthropicClient)


def test_estimate_cost() -> None:
    assert estimate_cost("claude-sonnet-5-5", 1_000_000, 100_000) == 2.00 + 1.00
    assert estimate_cost("some-unknown-model", 10, 10) is None
