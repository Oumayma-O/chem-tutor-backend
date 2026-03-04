"""
Backward-compatibility shim — re-exports everything from unit_repo.

New code should import from unit_repo directly.
"""
from app.infrastructure.database.repositories.unit_repo import (  # noqa: F401
    UnitRepository,
    UnitRepository as ChapterRepository,
    LessonRepository,
    LessonRepository as TopicRepository,
    StandardRepository,
    CurriculumDocumentRepository,
)
