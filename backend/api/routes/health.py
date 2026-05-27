"""Health check endpoint.

Public and unauthenticated, with no rate limit, so orchestrators and uptime
checks can poll it freely. Deliberately reveals nothing about internals.
"""

from fastapi import APIRouter

from models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report that the API is up. Returns a static, safe payload."""
    return HealthResponse()
