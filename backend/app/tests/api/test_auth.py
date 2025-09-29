from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seeded_admin):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.kz", "password": "Admin123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data and "refresh_token" in data


@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "bad@test.kz", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "AUTH_INVALID_CREDENTIALS"
