from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core import settings as settings_module  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.core.settings import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.tests.utils.simple_client import AsyncClient  # noqa: E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def override_settings() -> Settings:
    return Settings(database_url=TEST_DATABASE_URL, secret_key="test", cors_origins=["http://localhost"])


@pytest.fixture(scope="session", autouse=True)
def apply_settings_override():
    settings_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    settings_module.settings = override_settings()  # type: ignore[attr-defined]
    yield
    settings_module.get_settings.cache_clear()  # type: ignore[attr-defined]


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncClient:
    async def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    client = AsyncClient(app=app, base_url="http://testserver")
    yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def seeded_admin(db_session: AsyncSession):
    result = await db_session.execute(select(User).where(User.email == "admin@test.kz"))
    user = result.scalar_one_or_none()
    if user:
        return user
    admin = User(
        email="admin@test.kz",
        full_name="Admin Test",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin
