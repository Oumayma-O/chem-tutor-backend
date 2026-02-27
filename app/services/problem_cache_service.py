"""
ProblemCacheService — manages caching of AI-generated problems.

Level 1 (worked examples):
  - Always served from cache if available (min_cache_size per context)
  - Backfilled in the background once served
  - Cache target: CACHE_MIN_PER_SLOT per (chapter, topic, difficulty, context_tag)

Level 2/3:
  - Optionally cached; fresher problems preferred to avoid repetition

Design: pure service, no AI calls — delegates to ProblemCacheRepository.
"""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import ProblemOutput
from app.infrastructure.database.repositories.problem_cache_repo import ProblemCacheRepository

logger = get_logger(__name__)
settings = get_settings()

# Minimum cached worked examples per (chapter, topic, difficulty, context_tag) slot
CACHE_MIN_PER_SLOT = 3

# Level 1 cache entries never expire (worked examples are stable)
# Level 2/3 entries expire after 7 days to keep problems fresh
L2_L3_TTL_DAYS = 7


class ProblemCacheService:
    """
    Wraps ProblemCacheRepository with higher-level cache management logic.

    Usage:
      service = ProblemCacheService(db)
      problem = await service.get_or_none(chapter_id, topic_index, "medium", 1, "sports")
      if problem is None:
          problem = await ai_gen_service.generate(...)
          await service.store(problem, chapter_id, topic_index)
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = ProblemCacheRepository(db)

    async def get_or_none(
        self,
        chapter_id: str,
        topic_index: int,
        difficulty: str,
        level: int,
        context_tag: str | None,
    ) -> ProblemOutput | None:
        """
        Pick a random cached problem for the given slot.
        Returns None if cache is empty (caller must generate fresh).
        """
        entry = await self._repo.pick_random(
            chapter_id=chapter_id,
            topic_index=topic_index,
            difficulty=difficulty,
            level=level,
            context_tag=context_tag,
        )
        if entry is None:
            logger.debug(
                "cache_miss",
                chapter=chapter_id,
                topic=topic_index,
                level=level,
                difficulty=difficulty,
                context_tag=context_tag,
            )
            return None

        logger.debug(
            "cache_hit",
            cache_id=str(entry.id),
            chapter=chapter_id,
            topic=topic_index,
            level=level,
        )
        return ProblemOutput.model_validate(entry.problem_data)

    async def store(
        self,
        problem: ProblemOutput,
        chapter_id: str,
        topic_index: int,
    ) -> None:
        """
        Persist a generated problem to the cache.

        Level 1 entries never expire.
        Level 2/3 entries expire after L2_L3_TTL_DAYS.
        """
        level = problem.level
        expires_at: datetime | None = None
        if level in (2, 3):
            expires_at = datetime.utcnow() + timedelta(days=L2_L3_TTL_DAYS)

        await self._repo.save(
            chapter_id=chapter_id,
            topic_index=topic_index,
            difficulty=problem.difficulty,
            level=level,
            context_tag=problem.context_tag,
            problem_data=problem.model_dump(by_alias=True),
            expires_at=expires_at,
        )
        logger.info(
            "problem_cached",
            chapter=chapter_id,
            topic=topic_index,
            level=level,
            difficulty=problem.difficulty,
            context_tag=problem.context_tag,
        )

    async def needs_backfill(
        self,
        chapter_id: str,
        topic_index: int,
        difficulty: str,
        level: int,
        context_tag: str | None,
    ) -> bool:
        """
        Returns True if the cache slot is below CACHE_MIN_PER_SLOT.
        Used to decide whether to backfill in background.
        """
        if level != 1:
            return False  # Only backfill Level 1 worked examples
        count = await self._repo.count(
            chapter_id=chapter_id,
            topic_index=topic_index,
            difficulty=difficulty,
            level=level,
            context_tag=context_tag,
        )
        return count < CACHE_MIN_PER_SLOT


def get_problem_cache_service(db: AsyncSession) -> ProblemCacheService:
    return ProblemCacheService(db)
