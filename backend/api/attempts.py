"""Attempts API routes.

Stubs for submitting and retrieving fix attempts.
Full implementations call ``DomainHandler.validate_fix()`` and then
``MasteryService.update_mastery()`` (BKT-based) after scoring.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.auth import get_current_user
from db.supabase_client import get_supabase
from domains import DOMAIN_REGISTRY
from skill_model.mastery import MasteryService

router = APIRouter(prefix="/attempts", tags=["attempts"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class SubmitAttemptRequest(BaseModel):
    artifact_id: str
    submitted_fix: dict[str, Any]
    submitted_explanation: str


class AttemptResult(BaseModel):
    attempt_id: str
    fix_correctness: float
    understanding_score: float
    feedback: str
    mastery_updated: bool


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("", summary="Submit a fix attempt for an artifact", status_code=status.HTTP_201_CREATED)
async def submit_attempt(
    body: SubmitAttemptRequest,
    current_user: dict = Depends(get_current_user),
) -> AttemptResult:
    """Validate a submitted fix and update mastery scores.

    Flow:
    1. Fetch artifact + its domain.
    2. Call ``DomainHandler.validate_fix()`` to score the submission.
    3. Persist the attempt row.
    4. Call ``MasteryService.record_attempt()`` to update mastery.
    5. Return scores + feedback.
    """
    db = get_supabase()
    user_id: str = current_user["sub"]

    # Fetch artifact with its domain name
    artifact_result = (
        db.table("artifacts")
        .select("*, domains(name)")
        .eq("id", body.artifact_id)
        .maybe_single()
        .execute()
    )
    if not artifact_result.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact = artifact_result.data
    domain_slug = artifact.get("domains", {}).get("name", "")
    handler = DOMAIN_REGISTRY.get(domain_slug)
    if handler is None:
        raise HTTPException(status_code=422, detail=f"Unknown domain: {domain_slug}")

    # Validate the fix using the domain handler
    fix_result = handler.validate_fix(
        artifact=artifact,
        submitted_fix=body.submitted_fix,
        submitted_explanation=body.submitted_explanation,
    )

    # Persist the attempt
    attempt_row = {
        "artifact_id": body.artifact_id,
        "user_id": user_id,
        "submitted_fix": body.submitted_fix,
        "submitted_explanation": body.submitted_explanation,
        "fix_correctness": fix_result.correctness_score,
        "understanding_score": fix_result.understanding_score,
    }
    insert_result = db.table("attempts").insert(attempt_row).execute()
    attempt_id: str = insert_result.data[0]["id"]

    # Update mastery using BKT.
    # fix_correctness is a float [0,1] from the domain handler; convert to
    # bool by thresholding at 0.5 — the BKT layer then re-blends it with
    # understanding_score at 30% / 70% weights internally.
    was_correct = fix_result.correctness_score >= 0.5
    mastery_svc = MasteryService()
    await mastery_svc.update_mastery(
        user_id=user_id,
        concept_id=artifact["target_concept_id"],
        was_correct=was_correct,
        understanding_score=fix_result.understanding_score,
    )

    return AttemptResult(
        attempt_id=attempt_id,
        fix_correctness=fix_result.correctness_score,
        understanding_score=fix_result.understanding_score,
        feedback=fix_result.feedback,
        mastery_updated=True,
    )


@router.get("/my", summary="List the current user's attempts")
async def list_my_attempts(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return paginated attempts for the authenticated user."""
    db = get_supabase()
    result = (
        db.table("attempts")
        .select("*")
        .eq("user_id", current_user["sub"])
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
    )
    return result.data or []


@router.get("/{attempt_id}", summary="Fetch a single attempt by ID")
async def get_attempt(
    attempt_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    db = get_supabase()
    result = (
        db.table("attempts")
        .select("*")
        .eq("id", str(attempt_id))
        .eq("user_id", current_user["sub"])
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return result.data
