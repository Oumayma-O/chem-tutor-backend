"""Admin bootstrap — ensures a seed admin user exists on startup.

Runs only when ADMIN_EMAIL + ADMIN_PASSWORD are set in the environment.
Idempotent: skips creation if the email is already registered.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.models import User
from app.services.auth.user_factory import create_user

logger = get_logger(__name__)


async def ensure_admin_user(session: AsyncSession) -> None:
    """Insert the seed admin account if it does not already exist."""
    settings = get_settings()

    if not settings.admin_email or not settings.admin_password:
        return  # bootstrap disabled — no env vars set

    email = settings.admin_email.lower().strip()

    result = await session.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        if existing.role != "superadmin":
            logger.warning(
                "superadmin_bootstrap_skipped_wrong_role",
                email=email,
                current_role=existing.role,
            )
        return  # already exists, nothing to do

    user = await create_user(
        session,
        email=email,
        password=settings.admin_password,
        role="superadmin",
        name="Super Admin",
        commit=False,
    )
    await session.commit()

    logger.info("superadmin_user_created", email=email, user_id=str(user.id))
