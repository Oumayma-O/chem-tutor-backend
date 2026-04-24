"""Admin bootstrap — ensures seed superadmin users exist on startup.

Runs only when ADMIN_EMAIL + ADMIN_PASSWORD are set in the environment.
Idempotent: skips creation if the email is already registered as superadmin.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.models import User
from app.services.auth.user_factory import create_user

logger = get_logger(__name__)


async def _seed_superadmin(session: AsyncSession, email: str, password: str) -> None:
    existing = await session.scalar(select(User).where(User.email == email))
    if existing:
        if existing.role != "superadmin":
            logger.warning(
                "superadmin_bootstrap_skipped_wrong_role",
                email=email,
                current_role=existing.role,
            )
        return

    user = await create_user(
        session,
        email=email,
        password=password,
        role="superadmin",
        name="Super Admin",
        commit=False,
    )
    await session.flush()
    logger.info("superadmin_user_created", email=email, user_id=str(user.id))


async def ensure_admin_user(session: AsyncSession) -> None:
    """Insert seed superadmin accounts if they do not already exist."""
    settings = get_settings()

    pairs = [
        (settings.superadmin_email, settings.superadmin_password),
        (settings.superadmin_email_2, settings.superadmin_password_2),
    ]

    any_seeded = False
    for email, password in pairs:
        if not email or not password:
            continue
        await _seed_superadmin(session, email.lower().strip(), password)
        any_seeded = True

    if any_seeded:
        await session.commit()
