"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import require_roles
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenPair, UserCreate, UserRead
from app.utils.errors import ErrorCodes, http_error

router = APIRouter()


@router.post("/login", response_model=TokenPair, summary="Вход по email/паролю")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> TokenPair:
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise http_error(status.HTTP_401_UNAUTHORIZED, ErrorCodes.AUTH_INVALID_CREDENTIALS, "Неверный логин или пароль")

    access_token = create_access_token(user.email, user.role)
    refresh_token = create_refresh_token(user.email, user.role)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair, summary="Обновление access токена")
async def refresh_tokens(token: str, db: AsyncSession = Depends(get_db)) -> TokenPair:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise http_error(status.HTTP_400_BAD_REQUEST, ErrorCodes.AUTH_INVALID_CREDENTIALS, "Ожидается refresh токен")

    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise http_error(status.HTTP_401_UNAUTHORIZED, ErrorCodes.AUTH_INVALID_CREDENTIALS, "Пользователь не найден")

    return TokenPair(
        access_token=create_access_token(user.email, user.role),
        refresh_token=create_refresh_token(user.email, user.role),
    )


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(UserRole.admin)),
) -> UserRead:
    user_obj = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user_obj)
    await db.commit()
    await db.refresh(user_obj)
    return UserRead.model_validate(user_obj)
