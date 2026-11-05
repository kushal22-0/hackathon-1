"""Database engine and session construction.

The application only builds an engine when `REPOSITORY_BACKEND=postgres`.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def normalize_database_url(database_url: str) -> str:
    """Select the installed psycopg 3 driver for Supabase connection strings."""

    url = database_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def build_database(
    database_url: str,
) -> tuple[Engine, sessionmaker[Session]]:
    engine = create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    return engine, factory
