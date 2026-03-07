"""Pydantic schemas for unit and lesson catalog."""

from pydantic import BaseModel, Field


class StandardOut(BaseModel):
    code: str
    framework: str
    description: str | None = None


class LessonOut(BaseModel):
    id: int
    unit_id: str
    title: str
    description: str
    lesson_index: int
    slug: str
    is_ap_only: bool = False
    objectives: list[str] = Field(default_factory=list)
    key_equations: list[str] = Field(default_factory=list)
    key_rules: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    standards: list[StandardOut] = Field(default_factory=list)
    is_active: bool
    required_tools: list[str] = Field(default_factory=list)


class UnitOut(BaseModel):
    id: str
    title: str
    description: str
    icon: str | None = None
    gradient: str | None = None
    grade_id: int | None = None
    course_id: int | None = None
    course_name: str | None = None
    sort_order: int
    is_active: bool
    is_coming_soon: bool
    lessons: list[LessonOut] = Field(default_factory=list)


class UnitListItem(BaseModel):
    """Lightweight unit entry for the unit list view."""
    id: str
    title: str
    description: str
    icon: str | None = None
    gradient: str | None = None
    grade_id: int | None = None
    course_id: int | None = None
    course_name: str | None = None
    sort_order: int
    is_active: bool
    is_coming_soon: bool
    lesson_count: int
    skill_count: int
    lesson_titles: list[str] = Field(default_factory=list)


class LessonCreate(BaseModel):
    title: str
    description: str = ""
    lesson_index: int
    objectives: list[str] = Field(default_factory=list)
    key_equations: list[str] = Field(default_factory=list)
    key_rules: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    standard_codes: list[str] = Field(default_factory=list)  # ["NGSS HS-PS1-5", …]
    is_active: bool = True
    required_tools: list[str] = Field(default_factory=list)  # e.g. ["periodic_table", "calculator"]


class UnitCreate(BaseModel):
    id: str  # slug, e.g. "unit-gas-laws"
    title: str
    description: str = ""
    icon: str | None = None
    gradient: str | None = None
    grade_id: int | None = None
    course_id: int | None = None
    sort_order: int = 0
    is_coming_soon: bool = False
    lessons: list[LessonCreate] = Field(default_factory=list)


class CurriculumUploadRequest(BaseModel):
    """Request body for uploading a curriculum document for RAG context."""
    unit_id: str | None = None
    lesson_id: int | None = None
    title: str
    source_type: str = "text"   # pdf | text | standards_json
    content_text: str
    filename: str | None = None
    # Structured metadata extracted by caller
    standards: list[str] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class CurriculumDocOut(BaseModel):
    id: str
    unit_id: str | None
    lesson_id: int | None
    title: str
    source_type: str
    filename: str | None
    standards: list[str] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)
