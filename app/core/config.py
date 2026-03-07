from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file's location so it works regardless of CWD
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "info"
    api_v1_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(default_factory=lambda: ["https://your-domain.com"])

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://chem_user:chem_pass@localhost:5433/chem_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── AI Providers ─────────────────────────────────────────
    # Default (powerful) provider — problem generation
    default_ai_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    openai_api_key: str = ""
    openai_model: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = ""
    google_api_key: str = ""
    gemini_model: str = ""

    # Fast (lightweight) provider — hints, validation
    fast_ai_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    fast_openai_model: str = ""
    fast_anthropic_model: str = ""
    fast_gemini_model: str = ""

    # ── Mastery ──────────────────────────────────────────────
    mastery_threshold: float = 0.75
    mastery_window: int = 5

    # ── Auth ─────────────────────────────────────────────────
    jwt_secret_key: str = "chemtutor-dev-secret-key-change-in-production-32chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    supabase_jwt_secret: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
