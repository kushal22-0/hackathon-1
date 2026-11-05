"""Transaction ingestion and search routes."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status

from app.api.deps import get_transaction_service
from app.core.errors import AppError
from app.models.errors import ErrorResponse
from app.models.transaction import (
    Transaction,
    TransactionIngestResult,
    TransactionPage,
    TransactionSearchQuery,
)
from app.services.transactions import TransactionService

router = APIRouter()

ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    413: {"model": ErrorResponse, "description": "Upload too large"},
    415: {"model": ErrorResponse, "description": "Unsupported file type"},
    422: {"model": ErrorResponse, "description": "Validation failed"},
}


@router.post(
    "/ingest",
    response_model=TransactionIngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest transactions from a CSV file",
    responses=ERROR_RESPONSES,
)
async def ingest_transactions(
    request: Request,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    file: Annotated[UploadFile, File(description="UTF-8 CSV transaction export")],
) -> TransactionIngestResult:
    filename = Path(file.filename or "upload.csv").name
    if not filename.lower().endswith(".csv"):
        raise AppError(
            code="unsupported_file_type",
            message="Only .csv files are accepted",
            status_code=415,
        )

    settings = request.app.state.settings
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise AppError(
            code="file_too_large",
            message="Uploaded CSV exceeds the configured size limit",
            status_code=413,
            details={"max_upload_bytes": settings.max_upload_bytes},
        )

    return service.ingest_csv(content, filename=filename)


@router.get(
    "",
    response_model=TransactionPage,
    summary="Search and filter transactions with pagination",
    responses=ERROR_RESPONSES,
)
def list_transactions(
    query: Annotated[TransactionSearchQuery, Query()],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionPage:
    return service.search(query)


@router.get(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Get one transaction by ID",
    responses=ERROR_RESPONSES,
)
def get_transaction(
    transaction_id: UUID,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> Transaction:
    return service.get(transaction_id)
