"""
MasteryService — database-backed student mastery tracking using BKT.

Each ``mastery`` row stores P(L) — the BKT mastery probability — in the
``mastery_score`` column.  On every attempt the service:

1. Reads the current P(L) for the concept (defaults to P(L_0) if unseen).
2. Blends fix correctness + understanding_score into a single effective score
   (understanding weighted at 70%, since a lucky fix should count for less).
3. Applies ``bkt_update_soft`` to produce the new P(L).
4. Writes the updated P(L) back to the ``mastery`` table.

Weakest-concept selection
--------------------------
``get_weakest_concept`` returns the concept a student should practice next,
using a composite priority score:

    composite = mastery_score + NOVELTY_WEIGHT * min(1, attempts / NOVELTY_MAX_ATTEMPTS)

Lower composite → higher priority.  This ensures:
  • Low-mastery concepts are always prioritised over high-mastery ones.
  • Among concepts of equal mastery, unseen / rarely-attempted concepts
    are picked first — preventing the model from hammering one weak spot.

The ``_composite_score`` and ``_select_weakest`` helpers are extracted as
static methods specifically so they can be unit-tested without a database.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from db.supabase_client import get_supabase
from skill_model.bkt import (
    DEFAULT_PARAMS,
    BKTParams,
    blend_signals,
    bkt_update_soft,
)

# ── Weakest-concept tuning knobs ──────────────────────────────────────────────

#: Small bonus added per attempt to the composite score.
#: Keeps novelty's influence well below the mastery signal (which spans 0–1).
NOVELTY_WEIGHT: float = 0.05

#: Attempt count at which the novelty penalty reaches its maximum.
NOVELTY_MAX_ATTEMPTS: int = 10


# ── Service ───────────────────────────────────────────────────────────────────


class MasteryService:
    """Service layer for reading and updating BKT mastery estimates.

    Args:
        params: BKT parameter set.  Defaults to ``DEFAULT_PARAMS``.
                Pass a custom ``BKTParams`` to override per-deploy or per-test.
    """

    def __init__(self, params: BKTParams = DEFAULT_PARAMS) -> None:
        self._db     = get_supabase()
        self._params = params

    # ── Public API ────────────────────────────────────────────────────────────

    async def update_mastery(
        self,
        user_id: str,
        concept_id: str,
        was_correct: bool,
        understanding_score: float,
    ) -> dict[str, Any]:
        """Update a user's mastery for a concept using BKT.

        The fix result and understanding score are blended — understanding
        carries 70% of the weight, because a correct fix may be a lucky
        guess whereas a well-justified explanation signals genuine learning.

        P(L_{n+1}) is computed via ``bkt_update_soft`` and written to the DB.
        If no mastery row exists yet it is created with P(L_0) as the starting
        point.

        Args:
            user_id:             Authenticated user UUID.
            concept_id:          Concept UUID.
            was_correct:         Whether the submitted fix was correct.
            understanding_score: Quality of the student's explanation in [0, 1].

        Returns:
            Updated mastery row dict including the new ``mastery_score``.
        """
        effective_score = blend_signals(was_correct, understanding_score)

        existing        = await self._fetch(user_id, concept_id)
        current_p_l     = existing["mastery_score"]   if existing else self._params.p_l0
        current_attempts = existing["attempts_count"] if existing else 0

        new_p_l = bkt_update_soft(current_p_l, effective_score, self._params)

        row = {
            "user_id":        user_id,
            "concept_id":     concept_id,
            "mastery_score":  new_p_l,
            "attempts_count": current_attempts + 1,
            "last_updated":   datetime.now(tz=timezone.utc).isoformat(),
        }

        # Update in-memory fallback cache
        key = f"{user_id}:{concept_id}"
        if not hasattr(self, "_cache"):
            self._cache: dict[str, dict[str, Any]] = {}
        self._cache[key] = row

        try:
            if existing is None:
                result = await asyncio.to_thread(
                    lambda: self._db.table("mastery").insert(row).execute()
                )
            else:
                update_fields = {
                    k: v for k, v in row.items()
                    if k not in ("user_id", "concept_id")
                }
                result = await asyncio.to_thread(
                    lambda: self._db
                    .table("mastery")
                    .update(update_fields)
                    .eq("user_id", user_id)
                    .eq("concept_id", concept_id)
                    .execute()
                )
            if result and result.data:
                return result.data[0]
        except Exception:
            pass

        return row


    async def get_weakest_concept(
        self,
        user_id: str,
        domain_id: str,
    ) -> str | None:
        """Return the concept_id the student should practise next.

        Selection algorithm:
        1. Fetch all concepts in the domain.
        2. Fetch the user's existing mastery rows for those concepts.
           Unseen concepts are treated as mastery = P(L_0), attempts = 0.
        3. Compute a composite score for each concept via ``_composite_score``.
        4. Return the concept_id with the *lowest* composite score.

        Args:
            user_id:   Authenticated user UUID.
            domain_id: Domain UUID to filter concepts.

        Returns:
            Concept UUID string, or None if the domain has no concepts.
        """
        # 1. All concepts in the domain
        concepts_result = await asyncio.to_thread(
            lambda: self._db
            .table("concepts")
            .select("id")
            .eq("domain_id", domain_id)
            .execute()
        )
        concepts = concepts_result.data or []
        if not concepts:
            return None

        concept_ids = [c["id"] for c in concepts]

        # 2. Existing mastery rows for this user
        mastery_result = await asyncio.to_thread(
            lambda: self._db
            .table("mastery")
            .select("concept_id, mastery_score, attempts_count")
            .eq("user_id", user_id)
            .in_("concept_id", concept_ids)
            .execute()
        )
        mastery_map: dict[str, dict[str, Any]] = {
            row["concept_id"]: row
            for row in (mastery_result.data or [])
        }

        # 3. Build candidate list — unseen concepts get P(L_0) / 0 attempts
        candidates = [
            {
                "concept_id":     c["id"],
                "mastery_score":  mastery_map[c["id"]]["mastery_score"]
                                  if c["id"] in mastery_map
                                  else self._params.p_l0,
                "attempts_count": mastery_map[c["id"]]["attempts_count"]
                                  if c["id"] in mastery_map
                                  else 0,
            }
            for c in concepts
        ]

        # 4. Delegate to the pure static helper (also used in tests)
        return self._select_weakest(candidates)

    async def get_mastery_snapshot(self, user_id: str) -> list[dict[str, Any]]:
        """Return mastery across ALL domains for the dashboard.

        Each item contains the mastery row plus nested concept + domain info.
        Results are sorted weakest-first so the dashboard can highlight gaps.
        Concepts with zero attempts are excluded (the UI can show P(L_0) for those).

        Args:
            user_id: Authenticated user UUID.

        Returns:
            List of dicts, sorted by mastery_score ascending.
        """
        result = await asyncio.to_thread(
            lambda: self._db
            .table("mastery")
            .select(
                "concept_id, mastery_score, attempts_count, last_updated,"
                " concepts(tag, display_name, domain_id,"
                "   domains(name, display_name))"
            )
            .eq("user_id", user_id)
            .order("mastery_score", desc=False)   # weakest first
            .execute()
        )
        return result.data or []

    async def get_mastery(
        self,
        user_id: str,
        concept_id: str,
    ) -> dict[str, Any] | None:
        """Return the mastery row for a single (user, concept) pair, or None."""
        return await self._fetch(user_id, concept_id)

    # ── Pure static helpers (also exercised by unit tests) ────────────────────

    @staticmethod
    def _composite_score(mastery_score: float, attempts_count: int) -> float:
        """Compute the composite priority score for weakest-concept selection.

        Lower score → higher urgency to practise.

        Formula:
            composite = mastery_score
                      + NOVELTY_WEIGHT * min(1, attempts_count / NOVELTY_MAX_ATTEMPTS)

        The novelty term is small (≤ NOVELTY_WEIGHT = 0.05) relative to the
        mastery signal (which spans 0–1).  This means mastery always dominates;
        novelty only acts as a tie-breaker within the same mastery band.

        Args:
            mastery_score:  BKT P(L) for the concept.
            attempts_count: Number of times this user has attempted this concept.

        Returns:
            Composite float in [0, 1 + NOVELTY_WEIGHT].
        """
        novelty_penalty = NOVELTY_WEIGHT * min(
            1.0, attempts_count / NOVELTY_MAX_ATTEMPTS
        )
        return mastery_score + novelty_penalty

    @staticmethod
    def _select_weakest(candidates: list[dict[str, Any]]) -> str | None:
        """Select the concept with the lowest composite score.

        Extracted as a static method so it can be unit-tested without a DB.

        Each candidate dict must have keys:
            concept_id    (str)
            mastery_score (float)
            attempts_count (int)

        Args:
            candidates: List of candidate concept dicts.

        Returns:
            The ``concept_id`` with the lowest composite score, or None.
        """
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda c: MasteryService._composite_score(
                c["mastery_score"], c["attempts_count"]
            ),
        )["concept_id"]

    # ── Private DB helpers ────────────────────────────────────────────────────

    async def _fetch(self, user_id: str, concept_id: str) -> dict[str, Any] | None:
        try:
            result = await asyncio.to_thread(
                lambda: self._db
                .table("mastery")
                .select("*")
                .eq("user_id", user_id)
                .eq("concept_id", concept_id)
                .maybe_single()
                .execute()
            )
            if result and result.data:
                return result.data
        except Exception:
            pass

        key = f"{user_id}:{concept_id}"
        if hasattr(self, "_cache") and key in self._cache:
            return self._cache[key]

        return None

