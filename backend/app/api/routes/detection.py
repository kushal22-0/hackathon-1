"""Detection scan and single-transaction assessment routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_detection_service
from app.models.alert import (
    DetectionResult,
    DetectionRunRequest,
    DetectionRunResult,
)
from app.models.errors import ErrorResponse
from app.services.detection import DetectionService

router = APIRouter()

ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
    422: {"model": ErrorResponse, "description": "Validation failed"},
}


@router.post(
    "/scan",
    response_model=DetectionRunResult,
    summary="Scan recent or explicitly selected transactions",
    responses=ERROR_RESPONSES,
)
def scan_transactions(
    request: DetectionRunRequest,
    service: Annotated[DetectionService, Depends(get_detection_service)],
) -> DetectionRunResult:
    return service.scan(request)


@router.post(
    "/transactions/{transaction_id}",
    response_model=DetectionResult,
    summary="Assess one transaction and open or refresh its alert",
    responses=ERROR_RESPONSES,
)
def assess_transaction(
    transaction_id: UUID,
    service: Annotated[DetectionService, Depends(get_detection_service)],
) -> DetectionResult:
    return service.assess_transaction(transaction_id)
