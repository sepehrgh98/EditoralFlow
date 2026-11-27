import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.logging import setup_logging

ENV_VARS = [
    "LLM_PROVIDER",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_FAST_MODEL",
    "ANTHROPIC_STRONG_MODEL",
    "OPENAI_MODEL",
    "LLM_TIMEOUT_SECONDS",
    "LLM_MAX_RETRIES",
    "LLM_MAX_TOKENS",
    "LOG_LEVEL",
    "CORS_ORIGINS",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from the developer's shell environment."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def make_settings(**overrides: object) -> Settings:
    """Build settings without reading backend/.env."""
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    settings = make_settings()

    assert settings.llm_provider == "anthropic"
    assert settings.anthropic_fast_model == "claude-haiku-5-5"
    assert settings.anthropic_strong_model == "claude-sonnet-5-5"
    assert settings.llm_timeout_seconds == 60.0
    assert settings.llm_max_retries == 3
    assert settings.log_level == "INFO"
    assert settings.cors_origins == ["http://localhost:3000"]


def test_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("CORS_ORIGINS", '["http://a", "http://b"]')

    settings = make_settings()

    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-test"
    assert settings.llm_timeout_seconds == 5.0
    assert settings.cors_origins == ["http://a", "http://b"]


def test_reads_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=from-file\nLLM_MAX_TOKENS=123\n")

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "from-file"
    assert settings.llm_max_tokens == 123


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_missing_provider_key_fails_clearly(provider: str) -> None:
    with pytest.raises(ValidationError, match=f"{provider.upper()}_API_KEY is not set"):
        make_settings(llm_provider=provider)


def test_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        make_settings(anthropic_api_key="k", llm_provider="gemini")
    with pytest.raises(ValidationError):
        make_settings(anthropic_api_key="k", llm_timeout_seconds=0)


def test_api_key_is_hidden() -> None:
    settings = make_settings(anthropic_api_key="super-secret")

    assert "super-secret" not in repr(settings)
    assert "super-secret" not in str(settings.model_dump())


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(Settings.model_config, "env_file", None)  # ignore backend/.env
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()


def test_setup_logging_sets_level_and_is_repeatable() -> None:
    root = logging.getLogger()
    original_level, original_handlers = root.level, root.handlers[:]
    try:
        setup_logging("debug")
        setup_logging("WARNING")

        assert root.level == logging.WARNING
        assert len(root.handlers) == 1
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)
