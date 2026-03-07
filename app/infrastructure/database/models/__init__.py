"""
Database ORM models package.

Import order matters — each module registers its models with the shared
SQLAlchemy Base so string-based relationship forward references resolve correctly.

All public names are re-exported here so existing imports like
    from app.infrastructure.database.models import Lesson, Unit
continue to work unchanged.
"""

from app.infrastructure.database.models.lookup import Grade, Course, Interest
from app.infrastructure.database.models.user import User, UserProfile, StudentInterest
from app.infrastructure.database.models.curriculum import (
    Phase, Unit, Lesson, UnitLesson, Standard, LessonStandard,
)
from app.infrastructure.database.models.classroom import (
    Classroom, ClassroomStudent, ClassroomCurriculumOverride,
)
from app.infrastructure.database.models.learning import (
    ProblemCache, ProblemAttempt, SkillMastery,
    ThinkingTrackerLog, MisconceptionLog,
    UserLessonPlaylist, LessonProgress,
)
from app.infrastructure.database.models.teacher import (
    ExitTicket, ExitTicketResponse, CurriculumDocument,
)
from app.infrastructure.database.models.ai import GenerationLog, PromptVersion, FewShotExample

__all__ = [
    # lookup
    "Grade", "Course", "Interest",
    # user
    "User", "UserProfile", "StudentInterest",
    # curriculum
    "Phase", "Unit", "Lesson", "UnitLesson", "Standard", "LessonStandard",
    # classroom
    "Classroom", "ClassroomStudent", "ClassroomCurriculumOverride",
    # learning
    "ProblemCache", "ProblemAttempt", "SkillMastery",
    "ThinkingTrackerLog", "MisconceptionLog",
    "UserLessonPlaylist", "LessonProgress",
    # teacher
    "ExitTicket", "ExitTicketResponse", "CurriculumDocument",
    # ai
    "GenerationLog", "PromptVersion", "FewShotExample",
]
