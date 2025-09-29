"""Product service layer with filtering and pagination."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Literal

from fastapi import status
from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.websocket import broadcast_product_event
from app.models.product import Product
from app.schemas.product import PaginatedProducts, ProductCreate, ProductRead, ProductUpdate
from app.utils.errors import ErrorCodes, http_error, not_found

FILTERABLE_FIELDS = {"title", "price", "in_stock", "created_at"}
SORTABLE_FIELDS = {"id", "title", "price", "created_at"}


@dataclass(frozen=True)
class PaginationParams:
    """Container for unified pagination parameters."""

    offset: int
    limit: int
    page: int
    size: int
    mode: Literal["page", "offset"]


DEFAULT_PAGE = 1
DEFAULT_SIZE = 20


def prepare_pagination_params(
    *,
    page: int | None,
    size: int | None,
    limit: int | None,
    offset: int | None,
) -> PaginationParams:
    """Validate and normalize pagination query parameters."""

    use_offset = limit is not None or offset is not None
    if use_offset and (page is not None or size is not None):
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCodes.VALIDATION_ERROR,
            "Нельзя одновременно использовать page/size и limit/offset",
        )

    if use_offset:
        if limit is None:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCodes.VALIDATION_ERROR,
                "Параметр limit обязателен при использовании offset-пагинации",
            )
        normalized_offset = offset or 0
        normalized_limit = limit
        normalized_page = normalized_offset // normalized_limit + 1
        return PaginationParams(
            offset=normalized_offset,
            limit=normalized_limit,
            page=normalized_page,
            size=normalized_limit,
            mode="offset",
        )

    normalized_page = page or DEFAULT_PAGE
    normalized_size = size or DEFAULT_SIZE
    return PaginationParams(
        offset=(normalized_page - 1) * normalized_size,
        limit=normalized_size,
        page=normalized_page,
        size=normalized_size,
        mode="page",
    )


def build_filters(params: Dict[str, Any]) -> Iterable[Any]:
    expressions: list[Any] = []
    if "title_contains" in params:
        expressions.append(Product.title.ilike(f"%{params['title_contains']}%"))
    if "price_between" in params:
        start, end = params["price_between"]
        expressions.append(Product.price.between(start, end))
    if "price_in" in params:
        expressions.append(Product.price.in_(params["price_in"]))
    if "in_stock" in params:
        expressions.append(Product.in_stock.is_(params["in_stock"]))
    if "created_from" in params and "created_to" in params:
        expressions.append(Product.created_at.between(params["created_from"], params["created_to"]))
    elif "created_from" in params:
        expressions.append(Product.created_at >= params["created_from"])
    elif "created_to" in params:
        expressions.append(Product.created_at <= params["created_to"])
    if "title_eq" in params:
        expressions.append(Product.title == params["title_eq"])
    return expressions


def _serialize_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare filters for JSON serialization in API responses."""

    def _serialize_value(value: Any) -> Any:
        if isinstance(value, tuple):
            return [_serialize_value(v) for v in value]
        if isinstance(value, list):
            return [_serialize_value(v) for v in value]
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    return {key: _serialize_value(value) for key, value in filters.items()}


async def list_products(
    *,
    db: AsyncSession,
    pagination: PaginationParams,
    sort_by: str,
    sort_order: str,
    filters: Dict[str, Any],
) -> PaginatedProducts:
    statements = build_filters(filters)
    stmt = select(Product)
    if statements:
        stmt = stmt.where(and_(*statements))

    if sort_by not in SORTABLE_FIELDS:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCodes.VALIDATION_ERROR,
            "Недопустимое поле сортировки",
        )

    order_column = getattr(Product, sort_by)
    stmt = stmt.order_by(asc(order_column) if sort_order == "asc" else desc(order_column))
    stmt = stmt.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    count_stmt = select(func.count()).select_from(Product)
    if statements:
        count_stmt = count_stmt.where(and_(*statements))
    total = (await db.execute(count_stmt)).scalar_one()

    next_offset = pagination.offset + pagination.limit
    if next_offset >= total:
        next_offset = None

    prev_offset = pagination.offset - pagination.limit
    if prev_offset < 0:
        prev_offset = None if pagination.offset == 0 else 0

    filters_applied = _serialize_filters(filters)

    return PaginatedProducts(
        total=total,
        page=pagination.page,
        size=pagination.size,
        sort={"by": sort_by, "order": sort_order},
        filters_applied=filters_applied,
        next_offset=next_offset,
        prev_offset=prev_offset,
        items=[ProductRead.model_validate(item) for item in items],
    )


async def create_product(db: AsyncSession, payload: ProductCreate) -> ProductRead:
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    product_read = ProductRead.model_validate(product)
    await broadcast_product_event("product.created", product_read.model_dump())
    return product_read


async def update_product(db: AsyncSession, product_id: int, payload: ProductUpdate) -> ProductRead:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise not_found("Товар не найден", ErrorCodes.PRODUCT_NOT_FOUND)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    product_read = ProductRead.model_validate(product)
    await broadcast_product_event("product.updated", product_read.model_dump())
    return product_read


async def delete_product(db: AsyncSession, product_id: int) -> None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise not_found("Товар не найден", ErrorCodes.PRODUCT_NOT_FOUND)
    await db.delete(product)
    await db.commit()
    await broadcast_product_event("product.deleted", {"id": product_id})
