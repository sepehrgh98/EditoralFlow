"""Application settings, loaded once from environment variables and `backend/.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, independent of the directory the app is started from
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

Provider = Literal["anthropic", "openai"]


class Settings(BaseSettings):
    """All configuration in one place. Field names map to upper-case env variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Which LLM provider the app uses
    llm_provider: Provider = "anthropic"

    # API keys (SecretStr hides the value in logs and reprs)
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # Model names: a cheap, fast model and a stronger one for harder tasks
    anthropic_fast_model: str = "claude-haiku-5-5"
    anthropic_strong_model: str = "claude-sonnet-5-5"
    openai_model: str = "gpt-4.1-mini"

    # LLM call reliability
    llm_timeout_seconds: float = Field(default=60.0, gt=0)
    llm_max_retries: int = Field(default=3, ge=0)
    llm_max_tokens: int = Field(default=2000, gt=0)

    # App
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def _require_provider_key(self) -> "Settings":
        key_name = f"{self.llm_provider}_api_key"
        if getattr(self, key_name) is None:
            raise ValueError(
                f"LLM_PROVIDER is '{self.llm_provider}' but {key_name.upper()} is not set. "
                "Add it to backend/.env (see backend/.env.example) or the environment."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the settings, reading the environment only on the first call."""
    return Settings()
