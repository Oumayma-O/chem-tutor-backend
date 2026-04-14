"""Centralized user creation — single source of truth for User + UserProfile rows."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import User, UserProfile
from app.services.auth.security import hash_password


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role: str,
    name: str,
    district: str | None = None,
    school: str | None = None,
    is_active: bool = True,
    commit: bool = True,
) -> User:
    """Create a User + UserProfile in one call. Normalizes email, hashes password.

    Set ``commit=False`` when the caller manages the transaction (e.g. register
    endpoint that also creates interests/classrooms before committing).
    """
    user = User(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        role=role,
        name=name.strip(),
        district=district.strip() if district else None,
        school=school.strip() if school else None,
        is_active=is_active,
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(user_id=user.id, role=role, name=user.name)
    db.add(profile)

    if commit:
        await db.commit()
    else:
        await db.flush()

    return user
