"""Tests for MasteryService static helpers.

These tests exercise the pure, DB-free static methods on MasteryService:
  - _composite_score  — priority scoring for weakest-concept selection
  - _select_weakest   — picks the concept to practise next

No database or mocking is required.  The full async update_mastery flow
is covered by integration tests (when a Supabase instance is available).
"""

from __future__ import annotations

import pytest

from skill_model.mastery import (
    NOVELTY_MAX_ATTEMPTS,
    NOVELTY_WEIGHT,
    MasteryService,
)


# ── _composite_score ──────────────────────────────────────────────────────────


class TestCompositeScore:
    def test_zero_attempts_adds_no_novelty_penalty(self) -> None:
        score = MasteryService._composite_score(0.20, 0)
        assert score == pytest.approx(0.20)

    def test_penalty_increases_with_attempts(self) -> None:
        s0   = MasteryService._composite_score(0.20, 0)
        s5   = MasteryService._composite_score(0.20, 5)
        s_max = MasteryService._composite_score(0.20, NOVELTY_MAX_ATTEMPTS)
        assert s0 < s5 < s_max

    def test_penalty_caps_at_max_attempts(self) -> None:
        """Penalty must not grow beyond NOVELTY_WEIGHT regardless of attempt count."""
        s_max    = MasteryService._composite_score(0.20, NOVELTY_MAX_ATTEMPTS)
        s_beyond = MasteryService._composite_score(0.20, NOVELTY_MAX_ATTEMPTS * 10)
        assert s_max == pytest.approx(s_beyond)

    def test_maximum_penalty_equals_novelty_weight(self) -> None:
        base = 0.30
        s_max = MasteryService._composite_score(base, NOVELTY_MAX_ATTEMPTS)
        assert s_max == pytest.approx(base + NOVELTY_WEIGHT)

    def test_mastery_dominates_novelty(self) -> None:
        """A high-mastery concept with 0 attempts must score higher than a
        low-mastery concept at max attempts (novelty cannot flip the ranking)."""
        high_mastery_new    = MasteryService._composite_score(0.90, 0)
        low_mastery_veteran = MasteryService._composite_score(0.10, NOVELTY_MAX_ATTEMPTS)
        assert high_mastery_new > low_mastery_veteran, (
            "Novelty must not override the mastery signal"
        )

    def test_result_is_non_negative(self) -> None:
        assert MasteryService._composite_score(0.0, 0) >= 0.0

    def test_result_upper_bound(self) -> None:
        # Maximum possible score: mastery=1.0 + full novelty penalty
        s = MasteryService._composite_score(1.0, NOVELTY_MAX_ATTEMPTS)
        assert s == pytest.approx(1.0 + NOVELTY_WEIGHT)


# ── _select_weakest ───────────────────────────────────────────────────────────


class TestSelectWeakest:

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_empty_list_returns_none(self) -> None:
        assert MasteryService._select_weakest([]) is None

    def test_single_concept_returns_it(self) -> None:
        candidates = [
            {"concept_id": "only", "mastery_score": 0.5, "attempts_count": 3}
        ]
        assert MasteryService._select_weakest(candidates) == "only"

    # ── Mastery ranking ───────────────────────────────────────────────────────

    def test_lowest_mastery_wins(self) -> None:
        candidates = [
            {"concept_id": "A", "mastery_score": 0.80, "attempts_count": 5},
            {"concept_id": "B", "mastery_score": 0.20, "attempts_count": 5},
            {"concept_id": "C", "mastery_score": 0.50, "attempts_count": 5},
        ]
        assert MasteryService._select_weakest(candidates) == "B"

    def test_highest_mastery_never_wins_over_lowest(self) -> None:
        candidates = [
            {"concept_id": "new",    "mastery_score": 0.90, "attempts_count": 0},
            {"concept_id": "weak",   "mastery_score": 0.15, "attempts_count": 10},
            {"concept_id": "medium", "mastery_score": 0.50, "attempts_count": 3},
        ]
        assert MasteryService._select_weakest(candidates) == "weak"

    # ── Novelty tie-breaking ──────────────────────────────────────────────────

    def test_tiebreak_by_fewer_attempts(self) -> None:
        """When mastery is identical, pick the concept with fewest attempts."""
        candidates = [
            {"concept_id": "A", "mastery_score": 0.30, "attempts_count": 8},
            {"concept_id": "B", "mastery_score": 0.30, "attempts_count": 0},  # ← pick this
            {"concept_id": "C", "mastery_score": 0.30, "attempts_count": 5},
        ]
        assert MasteryService._select_weakest(candidates) == "B"

    def test_new_concept_beats_equal_mastery_with_attempts(self) -> None:
        """A brand-new concept (0 attempts, P(L_0) mastery) is preferred over the
        same mastery level that has already been hammered."""
        p_l0 = 0.10
        candidates = [
            {"concept_id": "new",      "mastery_score": p_l0, "attempts_count": 0},
            {"concept_id": "attempted","mastery_score": p_l0, "attempts_count": 5},
        ]
        assert MasteryService._select_weakest(candidates) == "new"

    def test_novelty_does_not_override_mastery_gap(self) -> None:
        """A new concept at moderate mastery must lose to a higher-attempted weak concept."""
        candidates = [
            {"concept_id": "new_moderate", "mastery_score": 0.60, "attempts_count": 0},
            {"concept_id": "old_weak",     "mastery_score": 0.10, "attempts_count": 10},
        ]
        # Even with full novelty penalty, 0.10 + 0.05 = 0.15 < 0.60
        assert MasteryService._select_weakest(candidates) == "old_weak"

    # ── Larger field ──────────────────────────────────────────────────────────

    def test_many_concepts_returns_correct_minimum(self) -> None:
        import random
        rng = random.Random(42)
        candidates = [
            {
                "concept_id":     f"concept_{i}",
                "mastery_score":  rng.uniform(0.1, 0.9),
                "attempts_count": rng.randint(0, 20),
            }
            for i in range(50)
        ]
        # Force a known minimum
        candidates.append(
            {"concept_id": "guaranteed_weakest", "mastery_score": 0.01, "attempts_count": 0}
        )
        result = MasteryService._select_weakest(candidates)
        assert result == "guaranteed_weakest"

    def test_all_same_mastery_all_same_attempts_returns_any(self) -> None:
        """When everything is equal, any concept can be returned — just don't crash."""
        candidates = [
            {"concept_id": c, "mastery_score": 0.5, "attempts_count": 5}
            for c in ("X", "Y", "Z")
        ]
        result = MasteryService._select_weakest(candidates)
        assert result in ("X", "Y", "Z")

    # ── Determinism ───────────────────────────────────────────────────────────

    def test_deterministic_across_calls(self) -> None:
        """Same input must always produce the same output."""
        candidates = [
            {"concept_id": "A", "mastery_score": 0.3, "attempts_count": 2},
            {"concept_id": "B", "mastery_score": 0.3, "attempts_count": 0},
            {"concept_id": "C", "mastery_score": 0.6, "attempts_count": 1},
        ]
        results = {MasteryService._select_weakest(candidates) for _ in range(20)}
        assert len(results) == 1, f"Non-deterministic results: {results}"
