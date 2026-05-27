"""Shared FastAPI dependencies.

Re-exports the auth dependencies and provides admin-key verification for the
ingestion endpoint. Keeping these in one place means routes import their guards
from a single, auditable module.
"""

import hmac
import logging

from fastapi import Header

from core.auth import AuthError, get_current_user, get_current_user_id
from core.config import get_settings

logger = logging.getLogger("deployme.auth")

# Re-exported so routes can do `from api.dependencies import get_current_user`.
__all__ = [
    "get_current_user",
    "get_current_user_id",
    "verify_admin_key",
    "AuthError",
]


async def verify_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """Guard the ingestion endpoint with the ``X-Admin-Key`` header.

    Uses a constant-time comparison to avoid leaking the key via timing. The
    key itself is never logged.

    Raises:
        AuthError: If the header is missing or does not match. Mapped to 401.
    """
    settings = get_settings()
    expected = settings.admin_api_key.get_secret_value()
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        logger.warning("Rejected request with missing/invalid admin key")
        raise AuthError("Invalid admin key.")
