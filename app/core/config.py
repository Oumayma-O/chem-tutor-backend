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
    mastery_window: int = 5
    # Minimum attempt score to count toward band-filling (below this = ignored)
    mastery_passing_score: float = 0.6
    # Mastery ceilings per level band  (exit ticket unlocks the remaining 0.15)
    l2_mastery_ceiling: float = 0.60
    l3_mastery_ceiling: float = 0.85
    # Qualifying attempts needed to fully fill each level's band
    l2_attempts_to_fill: int = 3
    l3_attempts_to_fill: int = 3

    # ── Playlist caps ────────────────────────────────────────
    # Max new problems a student can generate per (user, unit, lesson, level) slot.
    l1_max_problems: int = 3   # worked examples — see pattern, then do it yourself
    l2_max_problems: int = 5   # faded practice — variety before mastery check
    l3_max_problems: int = 5   # challenge — high-effort; spaced practice elsewhere

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
