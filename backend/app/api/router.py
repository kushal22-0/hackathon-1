"""Versioned API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import alerts, detection, transactions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
)
api_router.include_router(
    detection.router,
    prefix="/detection",
    tags=["detection"],
)
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["alerts"],
)
