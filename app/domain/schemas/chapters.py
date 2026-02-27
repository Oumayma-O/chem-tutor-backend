"""Pydantic schemas for chapter and topic catalog."""

from pydantic import BaseModel, Field


class StandardOut(BaseModel):
    code: str
    framework: str
    description: str | None = None


class TopicOut(BaseModel):
    id: int
    chapter_id: str
    title: str
    description: str
    topic_index: int
    key_equations: list[str] = Field(default_factory=list)
    standards: list[StandardOut] = Field(default_factory=list)
    is_active: bool


class ChapterOut(BaseModel):
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
    topics: list[TopicOut] = Field(default_factory=list)


class ChapterListItem(BaseModel):
    """Lightweight chapter entry for the chapter list view."""
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
    topic_count: int
    topic_titles: list[str] = Field(default_factory=list)


class TopicCreate(BaseModel):
    title: str
    description: str = ""
    topic_index: int
    key_equations: list[str] = Field(default_factory=list)
    standard_codes: list[str] = Field(default_factory=list)  # ["NGSS HS-PS1-5", …]
    is_active: bool = True


class ChapterCreate(BaseModel):
    id: str  # slug, e.g. "chemical-kinetics"
    title: str
    description: str = ""
    icon: str | None = None
    gradient: str | None = None
    grade_id: int | None = None
    course_id: int | None = None
    sort_order: int = 0
    is_coming_soon: bool = False
    topics: list[TopicCreate] = Field(default_factory=list)


class CurriculumUploadRequest(BaseModel):
    """Request body for uploading a curriculum document for RAG context."""
    chapter_id: str | None = None
    topic_id: int | None = None
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
    chapter_id: str | None
    topic_id: int | None
    title: str
    source_type: str
    filename: str | None
    standards: list[str] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)
