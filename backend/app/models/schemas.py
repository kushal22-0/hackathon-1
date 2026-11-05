"""Pydantic schemas shared by the API and domain services."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Response returned by the public health check."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: "ApiError"


class ApiError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict | list | None = None


ErrorResponse.model_rebuild()