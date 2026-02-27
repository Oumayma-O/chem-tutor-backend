from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
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
    database_url: str = Field(
        default="postgresql+asyncpg://chem_user:chem_pass@localhost:5433/chem_db"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── AI Providers ─────────────────────────────────────────
    default_ai_provider: Literal["openai", "anthropic", "gemini"] = "openai"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # ── Mastery ──────────────────────────────────────────────
    mastery_threshold: float = 0.75   # 75% accuracy to advance
    mastery_window: int = 5           # Rolling window of last N attempts

    # ── Problem Cache ─────────────────────────────────────────
    cache_min_per_slot: int = 3       # Min Level 1 worked examples per slot
    cache_l2_l3_ttl_days: int = 7     # Days before L2/L3 entries expire

    # ── Auth / JWT ───────────────────────────────────────────
    jwt_secret_key: str = "chemtutor-dev-secret-key-change-in-production-32chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    supabase_jwt_secret: str = ""

    @model_validator(mode="after")
    def check_active_provider_key(self) -> "Settings":
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.google_api_key,
        }
        if not key_map.get(self.default_ai_provider):
            raise ValueError(
                f"No API key configured for default provider '{self.default_ai_provider}'. "
                f"Set the corresponding *_API_KEY in your .env file."
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
