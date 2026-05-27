"""Server-side Supabase admin client.

IMPORTANT: This module initializes the Supabase client with the SERVICE ROLE
KEY. That key BYPASSES Row Level Security and has full read/write access to the
database — treat it like a Postgres root password. It is used ONLY for trusted
server-side operations (e.g. admin queries). It must never be sent to the
frontend, logged, or returned in an API response.

User-scoped data access still goes through RLS: when acting on behalf of a
signed-in user we rely on the user's own JWT (verified in ``core/auth.py``), not
on this admin client, so that RLS remains the last line of defense.
"""

from functools import lru_cache

from supabase import Client, create_client

from core.config import get_settings


@lru_cache
def get_admin_client() -> Client:
    """Return a cached Supabase client authenticated with the service role key.

    Cached so we reuse one client per process. Do not expose this client or its
    key to any frontend-facing code path.
    """
    settings = get_settings()
    # IMPORTANT: SERVICE ROLE KEY — server-side only, bypasses RLS.
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key.get_secret_value(),
    )
