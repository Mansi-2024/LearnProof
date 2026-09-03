"""Mastery API routes.

Read-only endpoints for surfacing a user's mastery scores across concepts
and domains.  Writes happen automatically via the attempts endpoint.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.auth import get_current_user
from skill_model.mastery import MasteryService

router = APIRouter(prefix="/mastery", tags=["mastery"])


@router.get("/me", summary="Get mastery snapshot across all domains for current user")
async def get_my_mastery(
    current_user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return mastery snapshot across all domains for the authenticated user, sorted weakest first."""
    svc = MasteryService()
    return await svc.get_mastery_snapshot(current_user["sub"])


@router.get("/weakest/{domain_id}", summary="Get weakest concept for user in a domain")
async def get_weakest_concept_for_domain(
    domain_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Return the concept_id the student should practice next in the given domain."""
    svc = MasteryService()
    concept_id = await svc.get_weakest_concept(current_user["sub"], domain_id)
    return {"concept_id": concept_id}


@router.get("/me/{concept_id}", summary="Get mastery for a specific concept")
async def get_mastery_for_concept(
    concept_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any] | dict[str, float]:
    """Return the mastery row for a concept, or a zeroed record if none exists yet."""
    svc = MasteryService()
    record = await svc.get_mastery(current_user["sub"], concept_id)
    return record or {
        "user_id": current_user["sub"],
        "concept_id": concept_id,
        "mastery_score": 0.0,
        "attempts_count": 0,
        "last_updated": None,
    }

