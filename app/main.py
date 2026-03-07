from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.database.connection import engine, run_migrations
from app.api.v1.routers import mastery, analytics, phases
from app.api.v1.routers import units, classrooms, students, problems
from app.api.v1.routers import auth

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


async def _patch_schema() -> None:
    """
    One-time column rename: execution_time_ms (int) → execution_time_s (float).
    Safe to run every startup — skips if old column no longer exists.
    """
    from sqlalchemy import text
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='generation_logs' AND column_name='execution_time_ms'"
        ))
        if result.fetchone():
            await conn.execute(text(
                "ALTER TABLE generation_logs RENAME COLUMN execution_time_ms TO execution_time_s"
            ))
            await conn.execute(text(
                "ALTER TABLE generation_logs "
                "ALTER COLUMN execution_time_s TYPE FLOAT USING execution_time_s::float"
            ))
            logger.info("schema_patched", change="execution_time_ms→execution_time_s")


async def _patch_prompt_version_column() -> None:
    """
    Widen prompt_versions.version from VARCHAR(20) to VARCHAR(50) if needed.
    Safe to run every startup — no-op if already 50.
    """
    from sqlalchemy import text
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT character_maximum_length FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'prompt_versions' AND column_name = 'version'"
        ))
        row = result.fetchone()
        if row and row[0] is not None and row[0] < 50:
            await conn.execute(text(
                "ALTER TABLE prompt_versions ALTER COLUMN version TYPE VARCHAR(50)"
            ))
            logger.info("schema_patched", change="prompt_versions.version→VARCHAR(50)")
        # Also widen generation_logs.prompt_version if still 20
        result2 = await conn.execute(text(
            "SELECT character_maximum_length FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'generation_logs' AND column_name = 'prompt_version'"
        ))
        row2 = result2.fetchone()
        if row2 and row2[0] is not None and row2[0] < 50:
            await conn.execute(text(
                "ALTER TABLE generation_logs ALTER COLUMN prompt_version TYPE VARCHAR(50)"
            ))
            logger.info("schema_patched", change="generation_logs.prompt_version→VARCHAR(50)")


async def _seed_prompt_version() -> None:
    """
    Upsert the current PROMPT_VERSION into prompt_versions.
    Bumping the constant in prompts.py + restarting the server
    automatically archives the new template with a timestamp.
    """
    from app.infrastructure.database.connection import AsyncSessionFactory
    from app.infrastructure.database.models import PromptVersion
    from app.services.ai.problem_generation.prompts import PROMPT_VERSION, GENERATE_PROBLEM_SYSTEM
    async with AsyncSessionFactory() as session:
        existing = await session.get(PromptVersion, PROMPT_VERSION)
        if not existing:
            session.add(PromptVersion(version=PROMPT_VERSION, template=GENERATE_PROBLEM_SYSTEM))
            await session.commit()
            logger.info("prompt_version_saved", version=PROMPT_VERSION)
        else:
            logger.info("prompt_version_exists", version=PROMPT_VERSION)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.environment, provider=settings.default_ai_provider)
    await run_migrations()
    await _patch_schema()
    await _patch_prompt_version_column()
    await _seed_prompt_version()
    yield
    logger.info("shutdown")
    await engine.dispose()


app = FastAPI(
    title="ChemTutor — AI Tutor API",
    description="Backend for mastery-based AI chemistry tutoring with adaptive scaffolding.",
    version="0.2.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global error handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )


# ── Routers ──────────────────────────────────────────────────
prefix = settings.api_v1_prefix

app.include_router(auth.router, prefix=prefix, tags=["Auth"])
app.include_router(mastery.router, prefix=prefix, tags=["Mastery"])
app.include_router(analytics.router, prefix=prefix, tags=["Analytics"])

# Dedicated problem delivery (cache-aware, SRP services)
app.include_router(problems.router, prefix=prefix, tags=["Problems"])

# Content catalog
app.include_router(units.router, prefix=prefix, tags=["Units"])
app.include_router(phases.router, prefix=prefix, tags=["Phases"])

# Classroom management
app.include_router(classrooms.router, prefix=prefix, tags=["Classrooms"])

# Student profiles
app.include_router(students.router, prefix=prefix, tags=["Students"])


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment, "version": "0.2.0"}
