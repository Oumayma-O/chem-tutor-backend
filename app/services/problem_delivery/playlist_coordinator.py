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
        # Cache the last playlist fetched by try_resume so get_previous_problem_summaries
        # can reuse it without a duplicate DB query.
        self._last_playlist_problems: list[dict] | None = None

    async def try_resume(
        self,
        req: GenerateProblemRequest,
        effective_difficulty: str,
        max_problems: int,
        *,
        allow_answer_reveal: bool | None = None,
        max_answer_reveals_per_lesson: int | None = None,
        min_level1_examples_for_level2: int | None = None,
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
            self._last_playlist_problems = None
            return None

        self._last_playlist_problems = list(playlist.problems)

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
                allow_answer_reveal=allow_answer_reveal,
                max_answer_reveals_per_lesson=max_answer_reveals_per_lesson,
                min_level1_examples_for_level2=min_level1_examples_for_level2,
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
                allow_answer_reveal=allow_answer_reveal,
                max_answer_reveals_per_lesson=max_answer_reveals_per_lesson,
                min_level1_examples_for_level2=min_level1_examples_for_level2,
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

    async def get_previous_problem_summaries(
        self,
        user_id: uuid.UUID | None,
        unit_id: str,
        lesson_index: int,
        level: int,
        difficulty: str,
    ) -> list[str]:
        """Return short summaries (title + first sentence of statement) of problems
        the student has already seen in this playlist slot. Used to tell the LLM
        what scenarios to avoid repeating.

        Reuses the playlist fetched by try_resume() when available to avoid a duplicate query.
        """
        problems: list = []
        if self._last_playlist_problems is not None:
            problems = self._last_playlist_problems
        elif user_id:
            repo = UserLessonPlaylistRepository(self._db)
            playlist = await repo.get(user_id, unit_id, lesson_index, level, difficulty)
            problems = list(playlist.problems) if playlist and playlist.problems else []

        summaries: list[str] = []
        for p in problems:
            if not isinstance(p, dict):
                continue
            title = p.get("title", "")
            statement = p.get("statement", "")
            first_sentence = statement.split(".")[0].strip() if statement else ""
            summary = f"{title}: {first_sentence}" if first_sentence else title
            if summary:
                summaries.append(summary)
        return summaries

