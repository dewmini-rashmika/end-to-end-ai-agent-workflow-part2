"""
User service — CRUD operations for user accounts.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import hash_password
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """Create and persist a new user account."""
    user = User(
        email=email.lower().strip(),
        username=username.strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    logger.info("user_created", user_id=str(user.id), email=email)
    return user


async def get_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email.lower().strip())
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(
        select(User).where(User.username == username.strip())
    )
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession,
    user_id: str,
    full_name: str | None = None,
    avatar_url: str | None = None,
) -> User | None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if full_name is not None:
        user.full_name = full_name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    await db.flush()
    return user


async def change_password(
    db: AsyncSession, user_id: str, new_password: str
) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    user.hashed_password = hash_password(new_password)
    await db.flush()
    return True


async def email_exists(db: AsyncSession, email: str) -> bool:
    user = await get_user_by_email(db, email)
    return user is not None


async def username_exists(db: AsyncSession, username: str) -> bool:
    user = await get_user_by_username(db, username)
    return user is not None
