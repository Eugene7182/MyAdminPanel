"""Product CRUD API."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import require_roles
from app.db.session import get_db
from app.models.user import UserRole
from app.schemas.product import PaginatedProducts, ProductCreate, ProductRead, ProductUpdate
from app.services.products import service as product_service

router = APIRouter()


@router.get("/", response_model=PaginatedProducts, summary="Получить список товаров с фильтрами")
async def list_products(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    sort_by: str = Query("id", description="Поле сортировки"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Порядок сортировки"),
    title_contains: str | None = Query(None, description="Фильтр по части названия"),
    title_eq: str | None = Query(None, description="Фильтр по точному названию"),
    price_from: float | None = Query(None, description="Минимальная цена"),
    price_to: float | None = Query(None, description="Максимальная цена"),
    price_in: list[float] | None = Query(None, description="Список цен"),
    in_stock: bool | None = Query(None, description="Наличие на складе"),
    created_from: datetime | None = Query(None, description="Создан с даты"),
    created_to: datetime | None = Query(None, description="Создан до даты"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.office, UserRole.supervisor, UserRole.promoter)),
) -> PaginatedProducts:
    filters: dict = {}
    if title_contains:
        filters["title_contains"] = title_contains
    if title_eq:
        filters["title_eq"] = title_eq
    if price_from is not None and price_to is not None:
        filters["price_between"] = (price_from, price_to)
    if price_in:
        filters["price_in"] = price_in
    if in_stock is not None:
        filters["in_stock"] = in_stock
    if created_from:
        filters["created_from"] = created_from
    if created_to:
        filters["created_to"] = created_to
    return await product_service.list_products(db, page, size, sort_by, sort_order, filters)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.office)),
) -> ProductRead:
    return await product_service.create_product(db, payload)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.office)),
) -> ProductRead:
    return await product_service.update_product(db, product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(UserRole.admin)),
) -> Response:
    await product_service.delete_product(db, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
