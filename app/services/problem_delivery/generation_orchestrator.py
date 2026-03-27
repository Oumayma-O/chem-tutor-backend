"""Lesson-context loading for problem delivery."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.unit_repo import LessonRepository


class LessonContextLoader:
    def __init__(self, db: AsyncSession) -> None:
        self._lessons = LessonRepository(db)

    @staticmethod
    def build_lesson_context(lesson: object | None) -> dict | None:
        if lesson is None:
            return None
        raw_standards = getattr(lesson, "standards", None) or []
        standards = [
            f"{ls.standard.code}: {ls.standard.description}"
            for ls in raw_standards
            if getattr(ls, "standard", None)
        ]
        return {
            "equations": getattr(lesson, "key_equations", None) or [],
            "objectives": getattr(lesson, "objectives", None) or [],
            "key_rules": getattr(lesson, "key_rules", None) or [],
            "misconceptions": getattr(lesson, "misconceptions", None) or [],
            "standards": standards,
        }

    async def load_lesson_and_context(
        self,
        unit_id: str,
        lesson_index: int,
    ) -> tuple[object | None, dict | None]:
        lesson = await self._lessons.get_by_index(unit_id, lesson_index)
        return lesson, self.build_lesson_context(lesson)


