from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ── Engine ────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,        # Detect stale connections before checkout
    pool_recycle=300,          # Recycle connections every 5 min (Neon drops idle ~5–10 min)
    pool_timeout=30,           # Raise after 30s waiting for a connection
    echo=settings.log_level.lower() == "debug",
    connect_args={"timeout": 30},  # Neon free-tier can take ~15s to wake from suspend
)

# ── Session factory ───────────────────────────────────────────
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base class for all ORM models ─────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Reusable context manager for background tasks ─────────────
@asynccontextmanager
async def fresh_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Open a fresh DB session for background tasks (fire-and-forget coroutines).
    Auto-commits on success; rolls back on exception.
    Use instead of duplicating the AsyncSessionFactory pattern in every task.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Dependency for FastAPI routes ─────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Migration readiness check ─────────────────────────────────
async def run_migrations() -> None:
    """
    Ensure Alembic migrations have been applied before app startup.
    This performs a read-only check and never mutates schema at runtime.
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        except Exception as exc:
            raise RuntimeError(
                "Database is not migration-ready. "
                "Run `alembic upgrade head` before starting the API."
            ) from exc
    logger.info("migration_check_ok")
