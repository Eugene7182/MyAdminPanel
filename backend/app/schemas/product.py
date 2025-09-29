"""Pydantic schemas for product CRUD."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from pydantic.types import condecimal

PriceDecimal = Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]


class ProductBase(BaseModel):
    title: str = Field(..., max_length=120)
    price: PriceDecimal
    in_stock: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: str | None = Field(None, max_length=120)
    price: PriceDecimal | None = None
    in_stock: bool | None = None


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SortMeta(BaseModel):
    by: str
    order: str


class PaginatedProducts(BaseModel):
    total: int
    page: int
    size: int
    sort: SortMeta
    filters_applied: dict[str, object]
    next_offset: int | None
    prev_offset: int | None
    items: list[ProductRead]
