"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Supabase ────────────────────────────────────────────────────────────
    supabase_url: AnyHttpUrl = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anon/public key")
    supabase_service_role_key: str = Field(..., description="Supabase service-role key (backend only)")

    # ── Grok AI ─────────────────────────────────────────────────────────────
    grok_api_key: str = Field(..., description="xAI Grok API key")
    grok_base_url: AnyHttpUrl = Field(
        default="https://api.x.ai/v1",  # type: ignore[assignment]
        description="Base URL for the Grok API",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    debug: bool = Field(default=False, description="Enable debug mode")
    app_title: str = "Repair API"
    app_version: str = "0.1.0"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return Settings()
