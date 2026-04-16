from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file's location so it works regardless of CWD
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

_DEFAULT_PROD_ORIGINS = ["https://chem-tutor-frontend.vercel.app"]
_DEFAULT_DEV_LOCAL_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


def _default_allowed_origins() -> list[str]:
    # Keep config as source-of-truth: dev defaults include local frontend origins.
    # Deployments can still override via ALLOWED_ORIGINS env var.
    return [*_DEFAULT_PROD_ORIGINS, *_DEFAULT_DEV_LOCAL_ORIGINS]


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
    allowed_origins: list[str] = Field(
        default_factory=_default_allowed_origins,
        description="CORS allowed origins (set ALLOWED_ORIGINS as JSON array on Render)",
    )

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://chem_user:chem_pass@localhost:5433/chem_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── AI Providers ─────────────────────────────────────────
    # Default (powerful) provider — problem generation
    default_ai_provider: Literal["openai", "anthropic", "gemini", "mistral"] = "openai"
    openai_api_key: str = ""
    openai_model: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = ""
    google_api_key: str = ""
    gemini_model: str = ""
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"

    # Fast (lightweight) provider — hints, validation
    fast_ai_provider: Literal["openai", "anthropic", "gemini", "mistral"] = "openai"
    fast_openai_model: str = ""
    fast_anthropic_model: str = ""
    fast_gemini_model: str = ""
    fast_mistral_model: str = "mistral-small-latest"

    # Max seconds for a single LLM HTTP request (OpenAI client). Prevents indefinite hangs.
    llm_timeout_seconds: float = 180.0

    # ── Mastery ──────────────────────────────────────────────
    mastery_window: int = 5
    # Minimum attempt score to count toward band-filling (below this = ignored)
    mastery_passing_score: float = 0.6
    # Mastery band ceilings (cumulative):
    #   L1 (worked examples):  0 → 0.20  (2 qualifying attempts to fill)
    #   L2 (guided practice):  0.20 → 0.50  (3 qualifying attempts to fill)
    #   L3 (independent):      0.50 → 0.80  (3 qualifying attempts to fill)
    #   Exit ticket:           0.80 → 1.00  (handled in mastery_bridge.py)
    l1_mastery_ceiling: float = 0.20
    l2_mastery_ceiling: float = 0.50
    l3_mastery_ceiling: float = 0.80
    # Qualifying attempts needed to fully fill each level's band
    l1_attempts_to_fill: int = 2
    l2_attempts_to_fill: int = 3
    l3_attempts_to_fill: int = 3

    # ── Playlist caps ────────────────────────────────────────
    # Max new problems a student can generate per (user, unit, lesson, level) slot.
    l1_max_problems: int = 3   # worked examples — see pattern, then do it yourself
    l2_max_problems: int = 5   # faded practice — variety before mastery check
    l3_max_problems: int = 5   # challenge — high-effort; spaced practice elsewhere
    # Unique L1 examples a student must view before Level 2 unlocks (solo/no-classroom default).
    # Per-classroom override stored in classrooms.min_level1_examples_for_level2.
    min_level1_examples_for_level2: int = 2

    # Default for new classrooms: max “3-strikes” answer reveals per lesson (teachers can override per class).
    default_max_answer_reveals_per_lesson: int = Field(default=6, ge=1, le=200)

    # ── Auth ─────────────────────────────────────────────────
    jwt_secret_key: str = "chemtutor-dev-secret-key-change-in-production-32chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # ── Admin bootstrap ──────────────────────────────────────
    # When set, an admin account is created on startup if it doesn't exist yet.
    # Leave empty to disable.
    admin_email: str = ""
    admin_password: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
