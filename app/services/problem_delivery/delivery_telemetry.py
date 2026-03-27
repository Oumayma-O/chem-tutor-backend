"""Telemetry side effects for problem delivery."""

from app.domain.schemas.tutor import GenerateProblemRequest, ProblemOutput
from app.infrastructure.database.connection import AsyncSessionFactory
from app.infrastructure.database.models import GenerationLog


class DeliveryTelemetry:
    @staticmethod
    async def log_generation(
        problem: ProblemOutput,
        req: GenerateProblemRequest,
        elapsed_s: float,
        provider: str,
        model: str,
        prompt_version: str,
    ) -> None:
        async with AsyncSessionFactory() as session:
            session.add(
                GenerationLog(
                    problem_id=problem.id,
                    unit_id=req.unit_id,
                    lesson_index=req.lesson_index,
                    level=req.level,
                    difficulty=req.difficulty,
                    provider=provider,
                    model_name=model,
                    prompt_version=prompt_version,
                    execution_time_s=elapsed_s,
                    problem_json=problem.model_dump(mode="json", by_alias=False),
                )
            )
            await session.commit()

