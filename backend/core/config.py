"""Application configuration loaded from environment variables.

All secrets are loaded here via ``pydantic-settings`` and nowhere else. Secret
values are wrapped in :class:`pydantic.SecretStr` so they are never accidentally
printed, logged, or serialized — ``repr`` and ``str`` render them as
``**********``. Call ``.get_secret_value()`` only at the exact point of use.
"""

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings sourced from ``.env`` / the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # The .env file also holds VITE_-prefixed frontend vars the backend
        # must never read. ``extra="ignore"`` keeps them out of the backend.
        extra="ignore",
    )

    # ─── API keys (secret) ────────────────────────────────────────────────
    anthropic_api_key: SecretStr
    admin_api_key: SecretStr

    # ─── Supabase ─────────────────────────────────────────────────────────
    # URL is not secret. The anon key is public-by-design but still treated as
    # a secret on the backend to keep it out of logs. The service role key
    # BYPASSES Row Level Security and must never leave the backend.
    supabase_url: str
    supabase_anon_key: SecretStr
    supabase_service_role_key: SecretStr

    # ─── Models ───────────────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "claude-sonnet-4-20250514"

    # ─── Storage ──────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_data"

    # ─── Server ───────────────────────────────────────────────────────────
    backend_port: int = 8000
    frontend_port: int = 5173

    # ─── CORS ─────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g.
    # "http://localhost:5173,https://deployme.example.com".
    allowed_origins: str = "http://localhost:5173"

    # ─── Rate limiting ────────────────────────────────────────────────────
    rate_limit_enabled: bool = True

    @field_validator("supabase_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def cors_origins(self) -> list[str]:
        """Allowed origins as a clean list (never ``["*"]`` from config)."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Cached so the ``.env`` file is parsed once per process. Import this function
    (not a module-level instance) so tests can override the cache if needed.
    """
    return Settings()  # type: ignore[call-arg]
