"""Supabase client singleton.

Usage::

    from db.supabase_client import get_supabase

    sb = get_supabase()
    result = sb.table("domains").select("*").execute()

The service-role client is used for backend operations that require elevated
privileges (e.g. writing mastery scores). Never expose this key to clients.
"""

from functools import lru_cache

from supabase import Client, create_client

from config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase service-role client."""
    settings = get_settings()
    return create_client(
        str(settings.supabase_url),
        settings.supabase_service_role_key,
    )
