"""Application settings, loaded once from environment variables and `backend/.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
# backend/.env, independent of the directory the app is started from
ENV_FILE = BACKEND_DIR / ".env"
# backend/data/scifact/corpus.jsonl, written by `make data`
DEFAULT_CORPUS_PATH = BACKEND_DIR / "data" / "scifact" / "corpus.jsonl"

# ollama: free, local models (default for development). anthropic: Claude API (paid).
Provider = Literal["ollama", "anthropic"]


class Settings(BaseSettings):
    """All configuration in one place. Field names map to upper-case env variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Which LLM provider the app uses
    llm_provider: Provider = "ollama"

    # Ollama (local). No API key needed.
    ollama_host: str = "http://localhost:11434"
    ollama_fast_model: str = "qwen3:8b"
    ollama_strong_model: str = "qwen3:14b"
    ollama_num_ctx: int = Field(default=16384, gt=0)  # context window; Ollama's default is small
    ollama_think: bool = False  # let thinking models reason first (slower, sometimes better)

    # Anthropic (Claude API). SecretStr hides the key in logs and reprs.
    anthropic_api_key: SecretStr | None = None
    anthropic_fast_model: str = "claude-haiku-5-5"
    anthropic_strong_model: str = "claude-sonnet-5-5"

    # LLM call reliability
    llm_timeout_seconds: float = Field(default=120.0, gt=0)
    llm_max_retries: int = Field(default=3, ge=0)
    # Models think before answering and that counts toward this limit, so keep it generous
    llm_max_tokens: int = Field(default=16000, gt=0)

    # Fact-checking
    corpus_path: Path = DEFAULT_CORPUS_PATH
    fact_check_top_k: int = Field(default=3, gt=0)  # abstracts searched per claim
    fact_check_max_claims: int = Field(default=20, gt=0)  # claims checked per draft
    fact_check_max_concurrency: int = Field(default=4, gt=0)  # claims checked at once
    # Also fact-check inside POST /review (ADR 0010); off because it makes many model calls
    review_include_fact_check: bool = False

    # App
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def _require_provider_key(self) -> "Settings":
        if self.llm_provider == "anthropic" and self.anthropic_api_key is None:
            raise ValueError(
                "LLM_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY is not set. "
                "Add it to backend/.env (see backend/.env.example) or the environment, "
                "or use LLM_PROVIDER=ollama for free local models."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the settings, reading the environment only on the first call."""
    return Settings()
