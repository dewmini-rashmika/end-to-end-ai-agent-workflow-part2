"""
Authentication service - JWT creation/validation, password hashing,
refresh token rotation.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.models.user import User
from app.models.auth import RefreshToken

logger = get_logger(__name__)


# -- Passwords -----------------------------------------------------------------

def hash_password(plain: str) -> str:
    # Hash password with a salt
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# -- JWT -----------------------------------------------------------------------

def create_access_token(user_id: str, email: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT. Raises JWTError on failure."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# -- Refresh tokens ------------------------------------------------------------

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def create_refresh_token(
    db: AsyncSession,
    user_id: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> str:
    """Generate, persist, and return a new raw refresh token."""
    raw = secrets.token_urlsafe(64)
    hashed = _hash_token(raw)
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token = RefreshToken(
        user_id=user_id,
        token_hash=hashed,
        expires_at=expires,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(token)
    await db.flush()
    return raw


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str] | None:
    """
    Validate old refresh token, revoke it, issue new access + refresh tokens.
    Returns (access_token, new_refresh_token) or None if invalid.
    """
    hashed = _hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    token_obj = result.scalar_one_or_none()

    if not token_obj:
        return None
    if token_obj.expires_at < datetime.now(timezone.utc):
        token_obj.is_revoked = True
        await db.flush()
        return None

    # Revoke old token
    token_obj.is_revoked = True
    await db.flush()

    # Load user
    user_result = await db.execute(select(User).where(User.id == token_obj.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        return None

    access = create_access_token(str(user.id), user.email)
    new_refresh = await create_refresh_token(db, str(user.id), user_agent, ip_address)
    return access, new_refresh


async def revoke_all_refresh_tokens(db: AsyncSession, user_id: str) -> None:
    """Revoke all refresh tokens for a user (logout everywhere)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    for token in result.scalars().all():
        token.is_revoked = True
    await db.flush()
