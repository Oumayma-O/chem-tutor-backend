"""AI/ML models: GenerationLog, PromptVersion, FewShotExample."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now, _uuid


class GenerationLog(Base):
    """One row per problem generation call — benchmarks provider/model/prompt performance."""
    __tablename__ = "generation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    problem_id: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)

    execution_time_s: Mapped[float] = mapped_column(Float, nullable=False)
    problem_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_gen_logs_provider_model", "provider", "model_name"),
        Index("ix_gen_logs_prompt_version", "prompt_version"),
        Index("ix_gen_logs_unit_lesson", "unit_id", "lesson_index"),
    )


class PromptVersion(Base):
    """Audit trail for prompt changes. One row per version string."""
    __tablename__ = "prompt_versions"

    version: Mapped[str] = mapped_column(String(50), primary_key=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class FewShotExample(Base):
    """
    Curated few-shot examples served to the LLM at generation time.
    Keyed by (unit_id, lesson_index, difficulty, level).
    """
    __tablename__ = "few_shot_examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    strategy: Mapped[str | None] = mapped_column(String(20), nullable=True)
    example_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_few_shot_lookup", "unit_id", "lesson_index", "difficulty", "level"),
    )
