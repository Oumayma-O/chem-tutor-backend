"""Shared unit + lesson creation for /units and /admin/chapters."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.units import UnitCreate
from app.infrastructure.database.models import Lesson, LessonStandard, Unit, UnitLesson
from app.infrastructure.database.repositories.unit_repo import StandardRepository, UnitRepository


async def create_unit_with_lessons(db: AsyncSession, req: UnitCreate) -> None:
    """Persist a new unit and its lessons (same logic as POST /units)."""
    unit_repo = UnitRepository(db)
    std_repo = StandardRepository(db)

    unit = Unit(
        id=req.id,
        title=req.title,
        description=req.description,
        icon=req.icon,
        gradient=req.gradient,
        grade_id=req.grade_id,
        course_id=req.course_id,
        sort_order=req.sort_order,
        is_coming_soon=req.is_coming_soon,
    )
    await unit_repo.create(unit)

    for order, l in enumerate(req.lessons):
        slug = f"{req.id}-l{order}"
        lesson = Lesson(
            title=l.title,
            description=l.description,
            lesson_index=l.lesson_index,
            objectives=l.objectives,
            key_equations=l.key_equations,
            key_rules=l.key_rules,
            misconceptions=l.misconceptions,
            is_active=l.is_active,
            required_tools=l.required_tools,
            slug=slug,
        )
        db.add(lesson)
        await db.flush()

        db.add(UnitLesson(unit_id=req.id, lesson_id=lesson.id, lesson_order=order))

        for code in l.standard_codes:
            framework = code.split(" ")[0] if " " in code else "OTHER"
            std = await std_repo.get_or_create(code=code, framework=framework)
            db.add(LessonStandard(lesson_id=lesson.id, standard_id=std.id))
