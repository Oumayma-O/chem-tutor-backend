"""
Pydantic schemas for Phases and Classroom Curriculum Overrides.
"""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.domain.schemas.units import UnitListItem


# ── Phase schemas ─────────────────────────────────────────────

class PhaseCreate(BaseModel):
    name: str
    description: str | None = None
    course_id: int | None = None
    sort_order: int = 0
    color: str | None = None


class PhaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    color: str | None = None


class PhaseOut(BaseModel):
    id: int
    name: str
    description: str | None
    course_id: int | None
    sort_order: int
    color: str | None

    model_config = {"from_attributes": True}


# ── Unit inside a curriculum response ─────────────────────────

class CurriculumUnit(BaseModel):
    """A unit as it appears in a curriculum fetch — includes effective ordering."""
    id: str
    title: str
    description: str
    icon: str | None
    gradient: str | None
    grade_id: int | None
    course_id: int | None
    course_name: str | None = None
    sort_order: int
    is_active: bool
    is_coming_soon: bool
    lesson_count: int
    skill_count: int = 0
    lesson_titles: list[str]

    effective_phase_id: int | None
    effective_order: int
    is_hidden: bool
    has_override: bool

    model_config = {"from_attributes": False}


class PhaseCurriculumGroup(BaseModel):
    """One phase with its ordered, visible units."""
    phase_id: int | None
    phase_name: str
    phase_description: str | None
    phase_color: str | None
    phase_course_id: int | None = None
    sort_order: int
    units: list[CurriculumUnit]


class CurriculumResponse(BaseModel):
    """Full curriculum response — phases with units."""
    classroom_id: uuid.UUID | None
    is_customised: bool          # True if at least one override exists
    phases: list[PhaseCurriculumGroup]


# ── Override schemas ──────────────────────────────────────────

class OverrideUpsert(BaseModel):
    """Create or update a single classroom ↔ unit override."""
    unit_id: str
    phase_id: int | None = None
    custom_order: int | None = None
    is_hidden: bool = False


class BulkOverrideRequest(BaseModel):
    """Upsert multiple overrides for a classroom in one call."""
    overrides: list[OverrideUpsert] = Field(min_length=1)


class OverrideOut(BaseModel):
    id: str
    classroom_id: str
    unit_id: str
    phase_id: int | None
    custom_order: int | None
    is_hidden: bool

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    """Result of a classroom 'sync with global default' action."""
    added: int    # new units pulled in from the global curriculum
    unchanged: int
