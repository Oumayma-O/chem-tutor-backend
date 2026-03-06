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
    pool_pre_ping=True,   # Detect stale connections
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


# ── Dependency for FastAPI routes ─────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Run Alembic migrations on startup ────────────────────────
async def run_migrations() -> None:
    """
    Startup table setup.

    Strategy:
      1. Try Alembic 'upgrade head' (uses alembic/versions/ migration files).
      2. If no migration files exist yet (fresh install / dev), fall back to
         SQLAlchemy create_all — creates all tables defined in models.py.
         This is safe to call repeatedly (CREATE TABLE IF NOT EXISTS).

    For production deployments, always run:
        alembic revision --autogenerate -m "description"
        alembic upgrade head
    before starting the container.
    """
    import asyncio
    import os
    from alembic.config import Config
    from alembic import command

    # Check whether any migration files exist
    versions_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "alembic", "versions")
    versions_dir = os.path.normpath(versions_dir)
    has_migrations = (
        os.path.isdir(versions_dir)
        and any(f.endswith(".py") for f in os.listdir(versions_dir))
    )

    # Always use create_all (idempotent: CREATE TABLE IF NOT EXISTS).
    # Alembic migrations are applied via CLI (`alembic upgrade head`)
    # before deployment — running them inside uvicorn's async loop causes
    # deadlocks because alembic env.py calls asyncio.run() from a thread.
    logger.info("running_create_all")
    import app.infrastructure.database.models  # noqa: F401 — registers all ORM models
    import asyncio
    for attempt in range(1, 6):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("create_all_complete")
            return
        except Exception as exc:
            if attempt == 5:
                raise
            wait = attempt * 3
            logger.warning("create_all_retry", attempt=attempt, wait_s=wait, error=str(exc))
            await asyncio.sleep(wait)
