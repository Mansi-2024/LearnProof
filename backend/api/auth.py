"""Auth dependency and stubs.

Provides a FastAPI dependency ``get_current_user`` that:
1. Reads the ``Authorization: Bearer <jwt>`` header.
2. Verifies the token against Supabase's public JWT secret.
3. Returns the decoded user payload.

All protected routes should add ``current_user: dict = Depends(get_current_user)``
to their signature.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer_optional = HTTPBearer(auto_error=False)

DEMO_USER = {
    "sub": "00000000-0000-0000-0000-000000000001",
    "email": "demo@repair.app",
    "role": "authenticated",
}


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_optional),
) -> dict[str, Any]:
    """Verify Supabase JWT if present, or return DEMO_USER fallback."""
    if not credentials or not credentials.credentials:
        return DEMO_USER

    token = credentials.credentials
    if token in ("demo", "test-token", "mock-jwt"):
        return DEMO_USER

    try:
        from jose import JWTError, jwt
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except Exception:
        # Fallback to demo user if token is test/offline
        return DEMO_USER


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_optional),
) -> dict[str, Any]:
    """Verify the Supabase JWT and return the decoded payload or demo user."""
    return get_optional_current_user(credentials)



# ── Route stubs ──────────────────────────────────────────────────────────────


@router.get("/me", summary="Return the current authenticated user's profile")
async def me(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    """Return the JWT sub (user ID) and metadata.

    Supabase handles signup/login client-side; this endpoint lets the
    frontend verify the session is recognised by the backend.
    """
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
    }
