"""Security helpers for hashing and JWT."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from passlib.context import CryptContext

from app.core.settings import get_settings
from app.models.user import UserRole

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_access_token(subject: str, role: UserRole, expires_delta: timedelta | None = None) -> str:
    """Generate a signed JWT access token."""

    settings = get_settings()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode: Dict[str, Any] = {"exp": expire, "sub": subject, "role": role.value, "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def create_refresh_token(subject: str, role: UserRole, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes)
    )
    to_encode: Dict[str, Any] = {"exp": expire, "sub": subject, "role": role.value, "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
