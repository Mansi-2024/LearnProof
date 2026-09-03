"""Artifacts API routes.

Stubs for CRUD + domain-specific artifact operations.
Full implementations will call ``DOMAIN_REGISTRY[domain_slug]`` for
context generation and hint rendering.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.auth import get_current_user
from db.supabase_client import get_supabase
from domains import DOMAIN_REGISTRY

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class GenerateArtifactRequest(BaseModel):
    domain: str
    target_concept: str
    difficulty: float = 0.5


class ArtifactOut(BaseModel):
    id: str
    domain_id: str
    target_concept_id: str
    artifact_payload: dict[str, Any]
    root_cause: str
    expected_behavior: str
    actual_behavior: str
    created_at: str


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("/generate", summary="Generate a broken artifact using Grok AI", status_code=status.HTTP_201_CREATED)
async def create_generated_artifact(
    body: GenerateArtifactRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate a new broken artifact using Grok AI across any of the 5 domains and persist it."""
    from ai.breaker import generate_broken_artifact
    import uuid

    generated = await generate_broken_artifact(
        domain=body.domain,
        target_concept=body.target_concept,
        difficulty=body.difficulty,
    )

    # Attach metadata
    artifact_id = str(uuid.uuid4())
    generated["id"] = artifact_id
    generated["domain_slug"] = body.domain
    generated["target_concept"] = body.target_concept

    # Attempt to persist in Supabase
    try:
        db = get_supabase()
        # Find domain_id
        dom_res = db.table("domains").select("id").eq("name", body.domain).maybe_single().execute()
        domain_id = dom_res.data["id"] if dom_res.data else None

        # Find or create concept_id
        concept_id = None
        if domain_id:
            con_res = (
                db.table("concepts")
                .select("id")
                .eq("domain_id", domain_id)
                .eq("tag", body.target_concept)
                .maybe_single()
                .execute()
            )
            if con_res.data:
                concept_id = con_res.data["id"]
            else:
                new_con = db.table("concepts").insert({
                    "domain_id": domain_id,
                    "tag": body.target_concept,
                    "display_name": body.target_concept.replace("-", " ").title(),
                }).execute()
                if new_con.data:
                    concept_id = new_con.data[0]["id"]

        if domain_id and concept_id:
            row = {
                "id": artifact_id,
                "domain_id": domain_id,
                "target_concept_id": concept_id,
                "artifact_payload": generated["artifact_payload"],
                "root_cause": generated["root_cause"],
                "expected_behavior": generated["expected_behavior"],
                "actual_behavior": generated["actual_behavior"],
            }
            insert_res = db.table("artifacts").insert(row).execute()
            if insert_res.data:
                generated["domain_id"] = domain_id
                generated["target_concept_id"] = concept_id
    except Exception as exc:
        logger.warning("Could not persist generated artifact in DB (running in memory/offline mode): %s", exc)

    return generated



@router.get("", summary="List artifacts (optionally filtered by domain)")
async def list_artifacts(
    domain_slug: str | None = None,
    limit: int = 20,
    offset: int = 0,
    _: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return a paginated list of artifacts.

    Pass ``?domain_slug=code`` to filter by domain name.
    """
    db = get_supabase()
    query = db.table("artifacts").select("*").limit(limit).offset(offset)
    result = query.execute()
    return result.data or []


@router.get("/{artifact_id}", summary="Fetch a single artifact by ID")
async def get_artifact(
    artifact_id: UUID,
    _: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Return a single artifact row, or 404 if not found."""
    db = get_supabase()
    result = (
        db.table("artifacts")
        .select("*")
        .eq("id", str(artifact_id))
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return result.data


@router.get("/{artifact_id}/hint", summary="Get a progressive hint for an artifact")
async def get_hint(
    artifact_id: UUID,
    hint_level: int = 1,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Return a progressive, non-leaking hint generated by Grok AI."""
    from ai.breaker import generate_hint
    db = get_supabase()
    result = (
        db.table("artifacts")
        .select("*")
        .eq("id", str(artifact_id))
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    hint_text = await generate_hint(result.data, hint_level=hint_level)
    return {
        "artifact_id": str(artifact_id),
        "hint_level": hint_level,
        "hint": hint_text,
    }

