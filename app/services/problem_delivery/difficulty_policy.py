"""Difficulty selection policy for delivered problems."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.tutor import GenerateProblemRequest
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository


class DifficultyPolicy:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(self, req: GenerateProblemRequest) -> str:
        """
        Derive effective difficulty from mastery for L2/L3.
        L1 stays at request difficulty (typically medium worked examples).
        """
        effective_difficulty = req.difficulty
        if req.user_id and req.level >= 2:
            mastery_record = await MasteryRepository(self._db).get_for_lesson(
                req.user_id,
                req.unit_id,
                req.lesson_index,
            )
            if mastery_record:
                effective_difficulty = mastery_record.current_difficulty
        return effective_difficulty

