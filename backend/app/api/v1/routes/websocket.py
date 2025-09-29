"""WebSocket endpoints for product events."""
from __future__ import annotations

import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.models.user import UserRole

router = APIRouter()

connections: Dict[UserRole, Set[WebSocket]] = {
    UserRole.admin: set(),
    UserRole.office: set(),
    UserRole.supervisor: set(),
    UserRole.promoter: set(),
}


async def authorize_websocket(websocket: WebSocket) -> UserRole:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        raise ValueError("Token required")
    payload = decode_token(token)
    if payload.get("type") != "access":
        await websocket.close(code=4401)
        raise ValueError("Access token required")
    role = UserRole(payload.get("role"))
    return role


@router.websocket("/products")
async def product_events(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        role = await authorize_websocket(websocket)
    except Exception:
        return
    connections[role].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connections[role].discard(websocket)


async def broadcast_product_event(event: str, payload: dict) -> None:
    message = json.dumps({"event": event, "data": payload}, default=str)
    for role_connections in connections.values():
        stale: Set[WebSocket] = set()
        for conn in role_connections:
            try:
                await conn.send_text(message)
            except RuntimeError:
                stale.add(conn)
        role_connections.difference_update(stale)
