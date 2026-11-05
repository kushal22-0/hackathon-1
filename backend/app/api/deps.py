"""FastAPI dependencies for repositories and services."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from app.repositories.container import RepositoryContainer
from app.services.transactions import TransactionService


def get_repositories(request: Request) -> Iterator[RepositoryContainer]:
    """Yield request-scoped repositories.

    The in-memory backend is a shared process-local store. PostgreSQL uses a
    fresh session per request; services explicitly commit writes so a response
    is never sent before durable persistence.
    """

    state = request.app.state
    if state.settings.repository_backend == "memory":
        yield state.memory_repositories.container
        return

    session = state.session_factory()
    repositories = RepositoryContainer.from_session(session)
    try:
        yield repositories
    except Exception:
        repositories.rollback()
        raise
    finally:
        session.close()


def get_transaction_service(
    request: Request,
    repositories: Annotated[RepositoryContainer, Depends(get_repositories)],
) -> TransactionService:
    return TransactionService(
        repositories,
        max_rows=request.app.state.settings.max_ingest_rows,
    )
