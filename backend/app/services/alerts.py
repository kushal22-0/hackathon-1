"""Alert search and retrieval business logic."""

from __future__ import annotations

import math
from uuid import UUID

from app.core.errors import AppError
from app.models.alert import Alert, AlertPage, AlertSearchQuery
from app.repositories.container import RepositoryContainer


class AlertService:
    def __init__(self, repositories: RepositoryContainer) -> None:
        self.repositories = repositories

    def search(self, query: AlertSearchQuery) -> AlertPage:
        items, total = self.repositories.alerts.search(query)
        total_pages = math.ceil(total / query.page_size) if total else 0
        return AlertPage(
            items=items,
            page=query.page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
        )

    def get(self, alert_id: UUID) -> Alert:
        alert = self.repositories.alerts.get_by_id(alert_id)
        if alert is None:
            raise AppError(
                code="alert_not_found",
                message="Alert not found",
                status_code=404,
                details={"alert_id": str(alert_id)},
            )
        return alert
