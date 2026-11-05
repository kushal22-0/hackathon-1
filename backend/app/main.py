"""FastAPI application factory and ASGI entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.database import build_database
from app.core.errors import register_exception_handlers
from app.repositories.container import build_memory_repositories


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    engine = getattr(app.state, "db_engine", None)
    if engine is not None:
        engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application.

    The factory accepts an explicit settings object so tests can construct an
    isolated app without touching the developer's environment file.
    """

    app_settings = settings or get_settings()
    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description=(
            "Fraud detection, investigation, and explanation API. "
            "Phase 1: ingestion, detection, account risk, and fund-flow tracing."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
    )
    app.state.settings = app_settings

    if app_settings.repository_backend == "memory":
        app.state.memory_repositories = build_memory_repositories()
    else:
        engine, session_factory = build_database(
            app_settings.sqlalchemy_database_url
        )
        app.state.db_engine = engine
        app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()
