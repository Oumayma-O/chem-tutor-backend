"""Playlist fetch/resume and persistence helpers."""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.tutor import GenerateProblemRequest, ProblemDeliveryResponse, ProblemOutput
from app.infrastructure.database.connection import fresh_session
from app.infrastructure.database.repositories.playlist_repo import UserLessonPlaylistRepository
from app.services.ai.shared.step_types import enforce_step_types
from app.utils.markdown_sanitizer import normalize_strings

logger = get_logger(__name__)


class PlaylistCoordinator:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def try_resume(
        self,
        req: GenerateProblemRequest,
        effective_difficulty: str,
        max_problems: int,
    ) -> ProblemDeliveryResponse | None:
        if not req.user_id or req.force_regenerate:
            return None

        repo = UserLessonPlaylistRepository(self._db)
        playlist = await repo.get(
            req.user_id,
            req.unit_id,
            req.lesson_index,
            req.level,
            effective_difficulty,
        )
        if not playlist or not playlist.problems:
            return None

        ci = playlist.current_index
        total = len(playlist.problems)
        current_data = playlist.problems[ci]
        current_id = current_data.get("id") if isinstance(current_data, dict) else None
        exclude = set(req.exclude_ids or [])

        if current_id and current_id not in exclude:
            problem = ProblemOutput.model_validate(normalize_strings(current_data))
            enforce_step_types(problem, req.level)
            return ProblemDeliveryResponse(
                problem=problem,
                current_index=ci,
                total=total,
                max_problems=max_problems,
                has_prev=ci > 0,
                has_next=ci < total - 1,
                at_limit=total >= max_problems,
            )

        if total >= max_problems:
            problem = ProblemOutput.model_validate(normalize_strings(current_data))
            enforce_step_types(problem, req.level)
            return ProblemDeliveryResponse(
                problem=problem,
                current_index=ci,
                total=total,
                max_problems=max_problems,
                has_prev=ci > 0,
                has_next=ci < total - 1,
                at_limit=True,
            )
        return None

    async def persist_playlist_entry(
        self,
        *,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        difficulty: str,
        problem_data: dict,
    ):
        async def _persist():
            async with fresh_session() as session:
                repo = UserLessonPlaylistRepository(session)
                return await repo.append_and_advance(
                    user_id=user_id,
                    unit_id=unit_id,
                    lesson_index=lesson_index,
                    level=level,
                    difficulty=difficulty,
                    problem_data=problem_data,
                )

        return await asyncio.shield(_persist())

