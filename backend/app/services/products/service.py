"""Product service layer with filtering and pagination."""
from __future__ import annotations

from typing import Any, Dict, Iterable

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.websocket import broadcast_product_event
from app.models.product import Product
from app.schemas.product import PaginatedProducts, ProductCreate, ProductRead, ProductUpdate
from app.utils.errors import ErrorCodes, not_found

FILTERABLE_FIELDS = {"title", "price", "in_stock", "created_at"}
SORTABLE_FIELDS = {"id", "title", "price", "created_at"}


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


async def list_products(
    db: AsyncSession,
    page: int,
    size: int,
    sort_by: str,
    sort_order: str,
    filters: Dict[str, Any],
) -> PaginatedProducts:
    statements = build_filters(filters)
    stmt = select(Product)
    if statements:
        stmt = stmt.where(and_(*statements))
    if sort_by in SORTABLE_FIELDS:
        order_column = getattr(Product, sort_by)
        stmt = stmt.order_by(asc(order_column) if sort_order == "asc" else desc(order_column))
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    count_stmt = select(func.count()).select_from(Product)
    if statements:
        count_stmt = count_stmt.where(and_(*statements))
    total = (await db.execute(count_stmt)).scalar_one()
    return PaginatedProducts(
        total=total,
        page=page,
        size=size,
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
