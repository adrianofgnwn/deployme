"""JWT verification for protected endpoints.

Rather than verifying Supabase JWT signatures locally (which would require the
project's JWT secret and tracking Supabase's signing-key rotations), we verify
each access token against Supabase's own ``/auth/v1/user`` endpoint. A valid,
unexpired token returns the user; anything else is rejected with 401.

This keeps verification authoritative and side-steps key management, at the cost
of one lightweight HTTP round-trip per protected request.
"""

import logging

import httpx
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import get_settings

logger = logging.getLogger("deployme.auth")

# auto_error=False so we can raise our own consistent 401 shape.
_bearer = HTTPBearer(auto_error=False)

# Reused across requests; Supabase auth calls are short-lived.
_http_client = httpx.AsyncClient(timeout=10.0)


class AuthError(Exception):
    """Raised on any authentication failure. Mapped to 401 by the app handler."""


async def _fetch_supabase_user(token: str) -> dict:
    """Validate ``token`` with Supabase and return the user payload.

    Raises:
        AuthError: If the token is missing, malformed, expired, or rejected.
    """
    settings = get_settings()
    try:
        resp = await _http_client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                # The anon key identifies the project to GoTrue. It is public.
                "apikey": settings.supabase_anon_key.get_secret_value(),
            },
        )
    except httpx.HTTPError:
        # Network/Supabase outage — log server-side, stay generic to the client.
        logger.exception("Supabase auth request failed")
        raise AuthError("Could not verify authentication. Please try again.")

    if resp.status_code != 200:
        raise AuthError("Invalid or expired authentication token.")

    user = resp.json()
    if not user.get("id"):
        raise AuthError("Invalid authentication token.")
    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """FastAPI dependency that returns the authenticated Supabase user.

    Also stashes the user id on ``request.state.user_id`` so per-user rate
    limiting (see ``core/rate_limiter.user_or_ip_key``) can key on it.

    Raises:
        AuthError: If no valid Bearer token is present.
    """
    if credentials is None or not credentials.credentials:
        raise AuthError("Authentication required.")

    user = await _fetch_supabase_user(credentials.credentials)
    request.state.user_id = user["id"]
    return user


async def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    """Convenience dependency returning just the authenticated user's id."""
    return user["id"]
