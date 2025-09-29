"""Seed script to populate sample data."""
from __future__ import annotations

import asyncio
from decimal import Decimal
from random import Random

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.product import Product
from app.models.user import User, UserRole

RANDOM = Random(42)


async def seed_users(session):
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


async def seed_products(session):
    result = await session.execute(select(Product.id))
    existing = result.scalars().count()
    if existing >= 200:
        return
    for i in range(existing, 200):
        session.add(
            Product(
                title=f"Product {i+1}",
                price=Decimal(str(RANDOM.uniform(10, 999))),
                in_stock=RANDOM.choice([True, False]),
            )
        )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_users(session)
        await seed_products(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
