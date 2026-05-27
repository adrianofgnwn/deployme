"""Rate limiting configuration built on slowapi.

A single shared :data:`limiter` instance is attached to the FastAPI app in
``main.py``. Per-endpoint limits are declared with the ``@limiter.limit(...)``
decorator on each route. Public endpoints key on client IP; tracker endpoints
key on the authenticated user id (see :func:`user_or_ip_key`).
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import get_settings

logger = logging.getLogger("deployme.rate_limit")

_settings = get_settings()


def user_or_ip_key(request: Request) -> str:
    """Rate-limit key: authenticated user id if present, else client IP.

    ``request.state.user_id`` is populated by the auth dependency on protected
    routes. Tracker limits are per-user; everything else falls back to IP.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_remote_address,
    enabled=_settings.rate_limit_enabled,
    headers_enabled=True,  # emit X-RateLimit-* and Retry-After headers
)


def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return a friendly 429 with a Retry-After header instead of a stack trace."""
    logger.info("Rate limit exceeded on %s", request.url.path)
    response = JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "detail": "Too many requests. Please wait a moment and try again.",
        },
    )
    # slowapi knows the retry window; expose it so clients can back off.
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    return response
