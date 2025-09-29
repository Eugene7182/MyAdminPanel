"""Compact FastAPI backend for product filtering and sorting demo."""
from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timedelta
from typing import Any, Iterable

from fastapi import Body, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="FastAPI CRUD Booster", version="0.6.1")


class Product(BaseModel):
    """Public product DTO."""

    id: int
    title: str
    category: str
    price: float
    stock: int
    available: bool
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    """Payload for product creation."""

    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    available: bool = True
    description: str | None = None


class ProductUpdate(BaseModel):
    """Patch payload."""

    title: str | None = Field(None, min_length=1)
    category: str | None = Field(None, min_length=1)
    price: float | None = Field(None, ge=0)
    stock: int | None = Field(None, ge=0)
    available: bool | None = None
    description: str | None = None


class PaginatedProducts(BaseModel):
    """Paginated response wrapper."""

    items: list[Product]
    page: int
    page_size: int
    total: int
    total_pages: int
    sort: str
    filters: list[dict[str, Any]]
    q: str | None = None


FIELD_META = {
    "id": {"type": int, "ops": {"eq", "neq", "gt", "gte", "lt", "lte", "between", "in"}},
    "title": {"type": str, "ops": {"eq", "neq", "contains", "startswith", "endswith", "in"}},
    "category": {"type": str, "ops": {"eq", "neq", "contains", "startswith", "endswith", "in"}},
    "price": {"type": float, "ops": {"eq", "neq", "gt", "gte", "lt", "lte", "between", "in"}},
    "stock": {"type": int, "ops": {"eq", "neq", "gt", "gte", "lt", "lte", "between", "in"}},
    "available": {"type": bool, "ops": {"eq", "neq", "istrue", "isfalse"}},
    "description": {"type": str, "ops": {"eq", "neq", "contains", "startswith", "endswith", "isnull"}},
    "created_at": {"type": datetime, "ops": {"eq", "neq", "gt", "gte", "lt", "lte", "between"}},
    "updated_at": {"type": datetime, "ops": {"eq", "neq", "gt", "gte", "lt", "lte", "between"}},
}
SEARCH_FIELDS = ("title", "description", "category")
DEFAULT_SORT = "id,asc"

_DATA: list[dict[str, Any]] = []
_LOCK = threading.Lock()
_NEXT_ID = 1


class ConnectionManager:
    """Tracks WebSocket subscribers."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        message = json.dumps(payload, default=_jsonify)
        stale: list[WebSocket] = []
        async with self._lock:
            for client in self._clients:
                try:
                    await client.send_text(message)
                except Exception:
                    stale.append(client)
        for client in stale:
            await self.disconnect(client)


manager = ConnectionManager()


def _jsonify(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported type: {type(value)!r}")


def _seed() -> None:
    """Fill the in-memory dataset."""

    global _DATA, _NEXT_ID
    base = datetime.utcnow() - timedelta(days=30)
    _DATA = [
        {
            "id": idx,
            "title": f"Product {idx}",
            "category": "Electronics" if idx % 2 else "Accessories",
            "price": round(59 + idx * 3.2, 2),
            "stock": 120 - idx * 2,
            "available": idx % 3 != 0,
            "description": None if idx % 5 == 0 else f"SKU {idx}",
            "created_at": base + timedelta(days=idx),
            "updated_at": base + timedelta(days=idx // 2),
        }
        for idx in range(1, 26)
    ]
    _NEXT_ID = len(_DATA) + 1


def _error(message: str, *, details: dict[str, Any] | None = None) -> HTTPException:
    payload = {"error_code": "invalid_request", "message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=payload)


def _coerce(value: Any, target: type) -> Any:
    if target is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in {"true", "1", "yes", "да"}:
            return True
        if isinstance(value, str) and value.lower() in {"false", "0", "no", "нет"}:
            return False
        raise _error("Неверное булево значение", details={"value": value})
    if target is datetime:
        try:
            return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise _error("Некорректная дата", details={"value": value}) from exc
    try:
        return target(value)
    except (TypeError, ValueError) as exc:
        raise _error("Не удалось привести значение", details={"value": value, "type": target.__name__}) from exc


def _parse_filter(field: str, operator: str, raw: Any) -> dict[str, Any]:
    meta = FIELD_META.get(field)
    if not meta:
        raise _error("Неизвестное поле", details={"field": field})
    operator = operator.lower()
    if operator not in meta["ops"]:
        raise _error("Оператор не поддерживается", details={"field": field, "operator": operator})
    target = meta["type"]
    if operator == "between":
        if isinstance(raw, str):
            raw = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            raise _error("between ожидает два значения", details={"field": field})
        value = tuple(_coerce(item, target) for item in raw)
    elif operator == "in":
        if isinstance(raw, str):
            raw = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
        if not isinstance(raw, Iterable) or not raw:
            raise _error("in ожидает непустой список", details={"field": field})
        value = [_coerce(item, target) for item in raw]
    elif operator in {"istrue", "isfalse"}:
        value = operator == "istrue"
    elif operator == "isnull":
        value = None
    else:
        value = _coerce(raw, target)
    return {"field": field, "operator": operator, "value": value}


def _normalize_filters(filters: str | None, field: str | None, operator: str | None, value: str | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if filters:
        try:
            raw_filters = json.loads(filters)
        except json.JSONDecodeError as exc:
            raise _error("Не удалось распарсить filters", details={"filters": filters}) from exc
        raw_filters = raw_filters if isinstance(raw_filters, list) else [raw_filters]
        for item in raw_filters:
            if not isinstance(item, dict) or not {"field", "operator", "value"}.issubset(item):
                raise _error("Каждый фильтр должен содержать field/operator/value", details={"filter": item})
            normalized.append(_parse_filter(item["field"], item["operator"], item["value"]))
    if field and operator:
        direct = value
        if operator.lower() == "between" and isinstance(value, str):
            direct = [chunk.strip() for chunk in value.split(",") if chunk.strip()]
        normalized.append(_parse_filter(field, operator, direct))
    return normalized


def _apply_filters(items: list[dict[str, Any]], filters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not filters:
        return items

    def match(row: dict[str, Any], flt: dict[str, Any]) -> bool:
        actual = row.get(flt["field"])
        op = flt["operator"]
        expected = flt["value"]
        if op == "eq":
            return actual == expected
        if op == "neq":
            return actual != expected
        if op == "contains":
            return isinstance(actual, str) and isinstance(expected, str) and expected.lower() in actual.lower()
        if op == "startswith":
            return isinstance(actual, str) and isinstance(expected, str) and actual.lower().startswith(expected.lower())
        if op == "endswith":
            return isinstance(actual, str) and isinstance(expected, str) and actual.lower().endswith(expected.lower())
        if op == "gt":
            return actual is not None and actual > expected
        if op == "gte":
            return actual is not None and actual >= expected
        if op == "lt":
            return actual is not None and actual < expected
        if op == "lte":
            return actual is not None and actual <= expected
        if op == "between":
            lo, hi = expected
            return actual is not None and lo <= actual <= hi
        if op == "in":
            return actual in expected
        if op == "istrue":
            return bool(actual) is True
        if op == "isfalse":
            return bool(actual) is False
        if op == "isnull":
            return actual is None
        return False

    return [row for row in items if all(match(row, flt) for flt in filters)]


def _apply_search(items: list[dict[str, Any]], query: str | None) -> list[dict[str, Any]]:
    if not query:
        return items
    needle = query.strip().lower()
    if not needle:
        return items
    return [row for row in items if any(isinstance(row.get(f), str) and needle in row[f].lower() for f in SEARCH_FIELDS)]


def _parse_sort(sort: str | None) -> list[tuple[str, bool]]:
    raw = sort or DEFAULT_SORT
    order: list[tuple[str, bool]] = []
    for chunk in [segment.strip() for segment in raw.split(";") if segment.strip()]:
        parts = [piece.strip() for piece in chunk.split(",") if piece.strip()]
        field = parts[0]
        direction = parts[1].lower() if len(parts) > 1 else "asc"
        if field not in FIELD_META or direction not in {"asc", "desc"}:
            raise _error("Некорректная сортировка", details={"segment": chunk})
        order.append((field, direction == "desc"))
    if all(field != "id" for field, _ in order):
        order.append(("id", False))
    return order


def _apply_sort(items: list[dict[str, Any]], order: list[tuple[str, bool]]) -> list[dict[str, Any]]:
    result = list(items)
    for field, desc in reversed(order):
        result.sort(key=lambda row: row.get(field).lower() if isinstance(row.get(field), str) else row.get(field), reverse=desc)
    return result


def _paginate(items: list[dict[str, Any]], page: int, size: int) -> tuple[list[dict[str, Any]], int]:
    total = len(items)
    start = (page - 1) * size
    end = start + size
    return items[start:end], total


def _find(product_id: int) -> int:
    for idx, row in enumerate(_DATA):
        if row["id"] == product_id:
            return idx
    raise _error("Товар не найден", details={"product_id": product_id})


@app.on_event("startup")
async def _startup() -> None:
    _seed()


@app.get("/products", response_model=PaginatedProducts)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Поисковая строка"),
    filters: str | None = Query(None, description="JSON-массив фильтров"),
    field: str | None = Query(None, description="Поле одиночного фильтра"),
    operator: str | None = Query(None, description="Оператор одиночного фильтра"),
    value: str | None = Query(None, description="Значение одиночного фильтра"),
    sort: str | None = Query(None, description="Сортировка вида field,asc;field2,desc"),
) -> PaginatedProducts:
    normalized = _normalize_filters(filters, field, operator, value)
    order = _parse_sort(sort)
    with _LOCK:
        snapshot = list(_DATA)
    filtered = _apply_filters(snapshot, normalized)
    searched = _apply_search(filtered, q)
    ordered = _apply_sort(searched, order)
    items, total = _paginate(ordered, page, page_size)
    if page > 1 and not items:
        raise _error("Страница вне диапазона", details={"page": page})
    return PaginatedProducts(
        items=[Product(**item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
        sort=";".join(f"{field},{'desc' if desc else 'asc'}" for field, desc in order),
        filters=normalized,
        q=q,
    )


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate = Body(...)) -> Product:
    now = datetime.utcnow()
    with _LOCK:
        global _NEXT_ID
        record = {
            "id": _NEXT_ID,
            "title": payload.title,
            "category": payload.category,
            "price": payload.price,
            "stock": payload.stock,
            "available": payload.available,
            "description": payload.description,
            "created_at": now,
            "updated_at": now,
        }
        _DATA.append(record)
        _NEXT_ID += 1
    await manager.broadcast({"event": "product.created", "payload": record})
    return Product(**record)


@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, payload: ProductUpdate = Body(...)) -> Product:
    with _LOCK:
        index = _find(product_id)
        record = _DATA[index]
        updates = payload.model_dump(exclude_unset=True)
        record.update(updates)
        record["updated_at"] = datetime.utcnow()
    await manager.broadcast({"event": "product.updated", "payload": record})
    return Product(**record)


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int) -> JSONResponse:
    with _LOCK:
        index = _find(product_id)
        _DATA.pop(index)
    await manager.broadcast({"event": "product.deleted", "payload": {"id": product_id}})
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@app.websocket("/ws/products")
async def products_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


_seed()
