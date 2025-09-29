"""Seed script to populate sample data."""
from __future__ import annotations

import asyncio
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.product import Product
from app.models.user import User, UserRole

TOTAL_PRODUCTS = 250
PRICE_MIN = Decimal("50.00")
PRICE_MAX = Decimal("1500.00")


async def seed_users(session):
    """Ensure that the default admin account exists."""

    result = await session.execute(select(User).where(User.email == "admin@oppo.kz"))
    if not result.scalar_one_or_none():
        session.add(
            User(
                email="admin@oppo.kz",
                full_name="Администратор",
                hashed_password=get_password_hash("Admin123!"),
                role=UserRole.admin,
            )
        )


def build_price(index: int) -> Decimal:
    """Return a price evenly distributed across the configured range."""

    if TOTAL_PRODUCTS == 1:
        return PRICE_MIN
    step = (PRICE_MAX - PRICE_MIN) / Decimal(TOTAL_PRODUCTS - 1)
    raw_price = PRICE_MIN + step * Decimal(index)
    return raw_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_stock_flag(index: int) -> bool:
    """Distribute stock availability evenly between True/False values."""

    return index % 2 == 0


async def seed_products(session):
    """Populate the catalogue with deterministic mock products."""

    result = await session.execute(select(func.count()).select_from(Product))
    existing = int(result.scalar_one())
    if existing >= TOTAL_PRODUCTS:
        return
    for i in range(existing, TOTAL_PRODUCTS):
        session.add(
            Product(
                title=f"Demo Product {i + 1:03d}",
                price=build_price(i),
                in_stock=build_stock_flag(i),
            )
        )


async def main() -> None:
    """Entry point for the async seed runner."""

    async with AsyncSessionLocal() as session:
        await seed_users(session)
        await seed_products(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
