from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routers import (
    admin,
    analytics,
    auth,
    classrooms,
    exit_tickets,
    mastery,
    phases,
    presence,
    problems,
    students,
    teacher,
    units,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.database.connection import AsyncSessionFactory, engine, run_migrations
from app.services.auth.bootstrap import ensure_admin_user

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

if "*" in settings.allowed_origins:
    raise ValueError("Wildcard origins are not allowed; configure explicit ALLOWED_ORIGINS.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.environment, provider=settings.default_ai_provider)
    await run_migrations()
    async with AsyncSessionFactory() as session:
        await ensure_admin_user(session)
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
    allow_origins=settings.allowed_origins,
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

# Teacher & admin dashboards (JWT role guards)
app.include_router(teacher.router, prefix=prefix, tags=["Teacher"])
app.include_router(exit_tickets.router, prefix=prefix, tags=["Exit Tickets"])
app.include_router(presence.router, prefix=prefix, tags=["Presence"])
app.include_router(admin.router, prefix=prefix, tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment, "version": "0.2.0"}
