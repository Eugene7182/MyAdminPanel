from __future__ import annotations

import pytest

from app.core.security import create_access_token
from app.models.user import UserRole
from app.tests.utils.simple_client import AsyncClient
from app.utils.errors import ErrorCodes


async def auth_headers(email: str, role: UserRole) -> dict[str, str]:
    token = create_access_token(email, role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, seeded_admin):
    response = await client.post(
        "/api/v1/products/",
        json={"title": "Test", "price": "10.50", "in_stock": True},
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"


@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient, seeded_admin):
    for i in range(5):
        await client.post(
            "/api/v1/products/",
            json={"title": f"Item {i}", "price": "5.00", "in_stock": True},
            headers=await auth_headers("admin@test.kz", UserRole.admin),
        )
    response = await client.get(
        "/api/v1/products/?page=1&size=2",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == 2
    assert data["total"] >= 5
    assert data["page"] == 1
    assert data["sort"] == {"by": "id", "order": "asc"}
    assert data["next_offset"] == 2
    assert data["prev_offset"] is None


@pytest.mark.asyncio
async def test_filter_by_title(client: AsyncClient, seeded_admin):
    await client.post(
        "/api/v1/products/",
        json={"title": "Filterable", "price": "33.00", "in_stock": True},
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    response = await client.get(
        "/api/v1/products/?title_contains=Filter",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filters_applied"]["title_contains"] == "Filter"
    assert any(item["title"] == "Filterable" for item in body["items"])


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, seeded_admin):
    create = await client.post(
        "/api/v1/products/",
        json={"title": "Up", "price": "20.00", "in_stock": True},
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    product_id = create.json()["id"]
    response = await client.put(
        f"/api/v1/products/{product_id}",
        json={"title": "Updated"},
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, seeded_admin):
    create = await client.post(
        "/api/v1/products/",
        json={"title": "Del", "price": "30.00", "in_stock": True},
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    product_id = create.json()["id"]
    response = await client.delete(
        f"/api/v1/products/{product_id}",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_viewer_cannot_create(client: AsyncClient, seeded_admin):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "viewer@test.kz", "password": "Viewer123!"},
    )
    if login.status_code != 200:
        admin_headers = await auth_headers("admin@test.kz", UserRole.admin)
        await client.post(
            "/api/v1/auth/users",
            json={
                "email": "viewer@test.kz",
                "full_name": "Viewer",
                "password": "Viewer123!",
                "role": "promoter",
                "is_active": True,
            },
            headers=admin_headers,
        )
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "viewer@test.kz", "password": "Viewer123!"},
        )
    viewer_token = login.json()["access_token"]
    response = await client.post(
        "/api/v1/products/",
        json={"title": "No", "price": "40.00", "in_stock": True},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bool_filter(client: AsyncClient, seeded_admin):
    await client.post(
        "/api/v1/products/",
        json={"title": "InStock", "price": "99.00", "in_stock": True},
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    response = await client.get(
        "/api/v1/products/?in_stock=true",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filters_applied"]["in_stock"] is True
    assert all(item["in_stock"] for item in body["items"])


@pytest.mark.asyncio
async def test_offset_pagination(client: AsyncClient, seeded_admin):
    for i in range(3):
        await client.post(
            "/api/v1/products/",
            json={"title": f"Offset {i}", "price": "7.00", "in_stock": True},
            headers=await auth_headers("admin@test.kz", UserRole.admin),
        )
    response = await client.get(
        "/api/v1/products/?limit=1&offset=1&sort_by=id&sort_order=asc",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 2
    assert payload["size"] == 1
    assert payload["prev_offset"] == 0
    assert payload["next_offset"] == 2 or payload["next_offset"] is None


@pytest.mark.asyncio
async def test_invalid_mix_pagination_params(client: AsyncClient, seeded_admin):
    response = await client.get(
        "/api/v1/products/?page=1&limit=5",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["error_code"] == ErrorCodes.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_invalid_sort_field(client: AsyncClient, seeded_admin):
    response = await client.get(
        "/api/v1/products/?sort_by=unknown",
        headers=await auth_headers("admin@test.kz", UserRole.admin),
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == ErrorCodes.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_refresh_flow(client: AsyncClient, seeded_admin):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.kz", "password": "Admin123!"},
    )
    refresh_token = login.json()["refresh_token"]
    response = await client.post("/api/v1/auth/refresh", params={"token": refresh_token})
    assert response.status_code == 200
    assert response.json()["access_token"]
