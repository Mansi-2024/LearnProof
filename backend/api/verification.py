"""Verification API route — evaluates student fix submissions via the Grok Judge."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ai.judge import verify_submission
from api.auth import get_current_user
from db.supabase_client import get_supabase
from skill_model.mastery import MasteryService

logger = logging.getLogger("repair.analytics")

router = APIRouter(tags=["verification"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class VerifyFixRequest(BaseModel):
    artifact_id: str = Field(..., description="UUID string of the target artifact")
    submitted_fix: dict[str, Any] = Field(..., description="Domain-specific fix payload")
    submitted_explanation: str = Field(
        ..., description="Student's explanation of why the artifact was broken and what was fixed"
    )
    artifact_context: dict[str, Any] | None = Field(
        default=None, description="Optional embedded artifact context for newly-generated or in-memory artifacts"
    )


class VerifyFixResponse(BaseModel):
    fix_correctness: float = Field(..., description="Score [0.0, 1.0] for fix validity")
    understanding_score: float = Field(
        ..., description="Score [0.0, 1.0] comparing explanation against root cause"
    )
    feedback_text: str = Field(..., description="Constructive feedback for the student")
    misunderstanding_flag: bool = Field(
        ..., description="True if fix succeeded but explanation revealed a fundamental misconception"
    )
    attempt_id: str | None = Field(default=None, description="Persisted attempt ID")
    mastery_updated: bool = Field(default=True)


# ── Route ───────────────────────────────────────────────────────────────────


@router.post(
    "/verify-fix",
    response_model=VerifyFixResponse,
    summary="Verify a student fix and explanation using the AI Judge",
    status_code=status.HTTP_200_OK,
)
async def verify_fix_endpoint(
    body: VerifyFixRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> VerifyFixResponse:
    """Evaluate a student's fix submission and explanation.

    1. Fetches artifact context from database (or uses embedded artifact_context).
    2. Runs ``verify_submission()`` (hybrid deterministic + Grok semantic judge).
    3. Detects lucky guesses / misconceptions (``misunderstanding_flag``).
    4. Updates user BKT mastery probability via ``update_mastery()``.
    5. Logs the verification event for downstream learning analytics.
    """
    db = get_supabase()
    user_id: str = current_user["sub"]

    # 1. Fetch artifact
    artifact: dict[str, Any] | None = None
    try:
        artifact_result = (
            db.table("artifacts")
            .select("*, domains(name)")
            .eq("id", body.artifact_id)
            .maybe_single()
            .execute()
        )
        if artifact_result.data:
            artifact = artifact_result.data
    except Exception as exc:
        logger.warning("Could not query artifacts table: %s", exc)

    if not artifact:
        if body.artifact_context:
            artifact = body.artifact_context
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    # 2. Judge submission
    result = await verify_submission(
        artifact=artifact,

        submitted_fix=body.submitted_fix,
        submitted_explanation=body.submitted_explanation,
    )

    # 3. Persist attempt
    attempt_id: str | None = None
    try:
        attempt_row = {
            "artifact_id": body.artifact_id,
            "user_id": user_id,
            "submitted_fix": body.submitted_fix,
            "submitted_explanation": body.submitted_explanation,
            "fix_correctness": result.fix_correctness,
            "understanding_score": result.understanding_score,
        }
        insert_res = db.table("attempts").insert(attempt_row).execute()
        if insert_res.data:
            attempt_id = insert_res.data[0].get("id")
    except Exception as exc:
        logger.warning("Failed to persist attempt record: %s", exc)

    # 4. Update BKT mastery
    try:
        was_correct = result.fix_correctness >= 0.5
        mastery_svc = MasteryService()
        await mastery_svc.update_mastery(
            user_id=user_id,
            concept_id=artifact["target_concept_id"],
            was_correct=was_correct,
            understanding_score=result.understanding_score,
        )
    except Exception as exc:
        logger.error("Failed to update mastery: %s", exc)

    # 5. Log verification for analytics
    analytics_event = {
        "event": "fix_verification",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "user_id": user_id,
        "artifact_id": body.artifact_id,
        "domain": artifact.get("domains", {}).get("name", "unknown"),
        "target_concept_id": artifact.get("target_concept_id"),
        "fix_correctness": result.fix_correctness,
        "understanding_score": result.understanding_score,
        "misunderstanding_flag": result.misunderstanding_flag,
        "attempt_id": attempt_id,
    }
    logger.info("VERIFICATION_ANALYTICS: %s", analytics_event)

    return VerifyFixResponse(
        fix_correctness=result.fix_correctness,
        understanding_score=result.understanding_score,
        feedback_text=result.feedback_text,
        misunderstanding_flag=result.misunderstanding_flag,
        attempt_id=attempt_id,
        mastery_updated=True,
    )
