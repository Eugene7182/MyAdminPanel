"""Application settings and configuration management."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application settings sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = Field(default="OPPO KZ Data Platform API")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="dev")

    database_url: str = Field(default="sqlite+aiosqlite:///./app.db", alias="DATABASE_URL")
    secret_key: str = Field(default="insecure-secret", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 7)
    cors_origins: List[AnyHttpUrl] | List[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    enable_bonuses: bool = Field(default=False, alias="ENABLE_BONUSES")
    enable_messages: bool = Field(default=False, alias="ENABLE_MESSAGES")

    log_level: str = Field(default="INFO")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | List[str]):
        """Allow comma-separated strings or list inputs for CORS origins."""
        if isinstance(value, str) and value:
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            return list(value)
        return []


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of :class:`Settings`."""

    return Settings()


settings = get_settings()
