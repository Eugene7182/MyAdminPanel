"""FastAPI entry point."""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import auth as auth_routes
from app.api.v1.routes import products as product_routes
from app.api.v1.routes import websocket as ws_routes
from app.api.v1.dependencies.auth import get_correlation_id
from app.core.logging import configure_logging
from app.core.settings import settings

logger = logging.getLogger(__name__)
context_filter = configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version=settings.app_version, openapi_url="/api/v1/openapi.json")

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.middleware("http")
async def add_security_headers(request, call_next):
    correlation_id: str = request.headers.get("X-Request-ID", "anonymous")
    context_filter.set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Request-ID"] = correlation_id
    return response


@app.get("/api/v1/health", tags=["ops"], summary="Проверка работоспособности")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/ready", tags=["ops"], summary="Готовность к трафику")
async def ready():
    return {"status": "ready"}


@app.get("/api/v1/version", tags=["ops"], summary="Версия сервиса")
async def version():
    return {"version": settings.app_version}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):  # type: ignore[override]
    logger.exception("Unhandled error", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_SERVER_ERROR", "message": "Внутренняя ошибка", "details": {}})


app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(product_routes.router, prefix="/api/v1/products", tags=["products"])
app.include_router(ws_routes.router, prefix="/api/v1/ws", tags=["ws"])
