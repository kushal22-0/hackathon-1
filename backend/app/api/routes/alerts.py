"""Paginated alert search and alert detail routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_alert_service
from app.models.alert import Alert, AlertPage, AlertSearchQuery
from app.models.errors import ErrorResponse
from app.services.alerts import AlertService

router = APIRouter()

ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
    422: {"model": ErrorResponse, "description": "Validation failed"},
}


@router.get(
    "",
    response_model=AlertPage,
    summary="Search alerts with pagination",
    responses=ERROR_RESPONSES,
)
def list_alerts(
    query: Annotated[AlertSearchQuery, Query()],
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertPage:
    return service.search(query)


@router.get(
    "/{alert_id}",
    response_model=Alert,
    summary="Get one alert by ID",
    responses=ERROR_RESPONSES,
)
def get_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> Alert:
    return service.get(alert_id)
