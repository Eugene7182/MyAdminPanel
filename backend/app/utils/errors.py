"""Shared error helpers."""
from __future__ import annotations

from fastapi import HTTPException, status


class ErrorCodes:
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"


def http_error(status_code: int, error_code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error_code": error_code, "message": message, "details": details or {}})


def unauthorized(message: str = "Требуется аутентификация") -> HTTPException:
    return http_error(status.HTTP_401_UNAUTHORIZED, ErrorCodes.AUTH_UNAUTHORIZED, message)


def forbidden(message: str = "Недостаточно прав") -> HTTPException:
    return http_error(status.HTTP_403_FORBIDDEN, ErrorCodes.AUTH_FORBIDDEN, message)


def not_found(message: str, error_code: str) -> HTTPException:
    return http_error(status.HTTP_404_NOT_FOUND, error_code, message)
