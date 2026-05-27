"""Pydantic schemas shared across the API.

Phase 0 defines the response envelope and health schema. Feature-specific
request/response models (queries, CVs, tracker entries) are added to this module
as each phase is built, so every endpoint keeps validating against an explicit
model rather than raw dicts.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Returned by ``GET /api/health``."""

    status: str = Field(default="ok", examples=["ok"])
    service: str = Field(default="deployme-backend")
    version: str = Field(default="0.1.0")


class ErrorResponse(BaseModel):
    """Consistent error envelope. Never carries stack traces or internals."""

    error: str = Field(description="Machine-readable error code.")
    detail: str = Field(description="Human-readable, user-safe message.")
