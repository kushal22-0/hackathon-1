"""Versioned API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import transactions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
)
