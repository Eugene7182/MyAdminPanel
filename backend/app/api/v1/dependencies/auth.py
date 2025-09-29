"""Authentication and authorization dependencies."""
from __future__ import annotations

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenPayload
from app.utils.errors import ErrorCodes, forbidden, http_error, unauthorized

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the current authenticated user from JWT token."""

    if not credentials:
        raise unauthorized()
    token = credentials.credentials
    try:
        payload = TokenPayload(**decode_token(token))
    except (JWTError, ValueError):
        raise http_error(401, ErrorCodes.AUTH_INVALID_CREDENTIALS, "Невалидный токен") from None

    if payload.type != "access":
        raise unauthorized("Ожидается access-токен")

    result = await db.execute(select(User).where(User.email == payload.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise unauthorized("Пользователь не найден")
    if not user.is_active:
        raise forbidden("Пользователь деактивирован")
    return user


def require_roles(*roles: UserRole):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise forbidden()
        return user

    return dependency


async def get_correlation_id(x_request_id: str | None = Header(default=None)) -> str:
    return x_request_id or "anonymous"
