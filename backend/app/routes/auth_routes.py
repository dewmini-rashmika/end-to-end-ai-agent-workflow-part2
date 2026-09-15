"""
Auth routes — register, login, logout, token refresh, profile.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.user import User
from app.services.auth_service import (
    verify_password,
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
    revoke_all_refresh_tokens,
)
from app.services.user_service import (
    create_user,
    get_user_by_email,
    update_user_profile,
    email_exists,
    username_exists,
)
from app.utils.dependencies import get_current_active_user
from app.utils.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    UpdateProfileRequest,
)
from app.config.settings import settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    if await email_exists(db, body.email):
        raise HTTPException(status_code=409, detail="Email already registered.")
    if await username_exists(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken.")

    user = await create_user(
        db,
        email=body.email,
        username=body.username,
        password=body.password,
        full_name=body.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return access + refresh tokens."""
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    access_token = create_access_token(str(user.id), user.email)
    refresh_token = await create_refresh_token(
        db,
        user_id=str(user.id),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    logger.info("user_login", user_id=str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and return new token pair."""
    result = await rotate_refresh_token(
        db,
        raw_token=body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
    access, new_refresh = result
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all refresh tokens (logout from all devices)."""
    await revoke_all_refresh_tokens(db, str(current_user.id))
    logger.info("user_logout", user_id=str(current_user.id))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    updated = await update_user_profile(
        db,
        user_id=str(current_user.id),
        full_name=body.full_name,
        avatar_url=body.avatar_url,
    )
    return updated
