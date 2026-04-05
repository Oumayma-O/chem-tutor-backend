"""Admin bootstrap — ensures a seed admin user exists on startup.

Runs only when ADMIN_EMAIL + ADMIN_PASSWORD are set in the environment.
Idempotent: skips creation if the email is already registered.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.models import User, UserProfile
from app.services.auth.security import hash_password

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
        if existing.role != "admin":
            logger.warning(
                "admin_bootstrap_skipped_wrong_role",
                email=email,
                current_role=existing.role,
            )
        return  # already exists, nothing to do

    user = User(
        email=email,
        password_hash=hash_password(settings.admin_password),
        role="admin",
        name="Admin",
        is_active=True,
    )
    session.add(user)
    await session.flush()

    profile = UserProfile(user_id=user.id, role="admin", name="Admin")
    session.add(profile)
    await session.commit()

    logger.info("admin_user_created", email=email, user_id=str(user.id))
