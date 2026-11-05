"""Consistent API error envelope."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable error summary")
    details: Any | None = Field(
        default=None,
        description="Structured field/row errors when available",
    )


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
