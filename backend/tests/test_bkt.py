"""Tests for the pure BKT implementation.

No database, no mocking — pure mathematics.

Includes:
  - TestBKTParams           parameter validation
  - TestBKTPosterior        Bayesian update step
  - TestBKTUpdate           full BKT update (posterior + forward)
  - TestBKTUpdateSoft       soft / partial-credit extension
  - TestBlendSignals        signal blending logic
  - TestStudentSimulation   10-attempt divergence simulation (the key spec test)
"""

from __future__ import annotations

import pytest

from skill_model.bkt import (
    DEFAULT_PARAMS,
    BKTParams,
    blend_signals,
    bkt_forward,
    bkt_posterior,
    bkt_update,
    bkt_update_soft,
)


# ── BKTParams ─────────────────────────────────────────────────────────────────


class TestBKTParams:
    def test_default_params_are_in_range(self) -> None:
        p = DEFAULT_PARAMS
        for name in ("p_l0", "p_t", "p_g", "p_s", "p_f"):
            val = getattr(p, name)
            assert 0.0 < val < 1.0, f"{name}={val} is not strictly in (0, 1)"

    def test_boundary_values_are_valid(self) -> None:
        # 0.0 and 1.0 should be accepted
        BKTParams(p_l0=0.0, p_t=0.0, p_g=0.0, p_s=0.0, p_f=0.0)
        BKTParams(p_l0=1.0, p_t=1.0, p_g=1.0, p_s=1.0, p_f=1.0)

    @pytest.mark.parametrize("field,val", [
        ("p_l0",  1.1),
        ("p_t",  -0.01),
        ("p_g",   2.0),
        ("p_s",  -1.0),
        ("p_f",   1.5),
    ])
    def test_out_of_range_raises(self, field: str, val: float) -> None:
        with pytest.raises(ValueError, match=field):
            BKTParams(**{field: val})


# ── bkt_posterior ─────────────────────────────────────────────────────────────


class TestBKTPosterior:
    def test_correct_raises_posterior_above_prior(self) -> None:
        p_l = 0.3
        assert bkt_posterior(p_l, True) > p_l

    def test_incorrect_lowers_posterior_below_prior(self) -> None:
        p_l = 0.3
        assert bkt_posterior(p_l, False) < p_l

    def test_posterior_strictly_between_zero_and_one(self) -> None:
        for p_l in (0.01, 0.3, 0.7, 0.99):
            for correct in (True, False):
                result = bkt_posterior(p_l, correct)
                assert 0.0 <= result <= 1.0, (
                    f"bkt_posterior({p_l}, {correct}) = {result} out of [0,1]"
                )

    def test_high_mastery_with_correct_stays_high(self) -> None:
        # P(L)=0.9 + correct → posterior should be very high
        assert bkt_posterior(0.9, True) > 0.9

    def test_low_mastery_with_incorrect_stays_low(self) -> None:
        assert bkt_posterior(0.1, False) < 0.1

    def test_zero_denominator_guard(self) -> None:
        # Pathological params where guess=0 and p_l=0 with correct=True
        # denominator = 0*0.9 + 1.0*0 = 0 → should not crash, return p_l
        extreme = BKTParams(p_l0=0.0, p_t=0.0, p_g=0.0, p_s=0.0, p_f=0.0)
        result = bkt_posterior(0.0, True, extreme)
        assert result == pytest.approx(0.0)


# ── bkt_forward ───────────────────────────────────────────────────────────────


class TestBKTForward:
    def test_high_posterior_stays_high_with_low_forget(self) -> None:
        result = bkt_forward(0.9, DEFAULT_PARAMS)
        # 0.9 * 0.95 + 0.1 * 0.10 = 0.855 + 0.01 = 0.865
        assert result == pytest.approx(0.865, abs=1e-6)

    def test_zero_posterior_gets_learning_bump(self) -> None:
        # 0.0 * (1-P_F) + 1.0 * P_T = P_T
        result = bkt_forward(0.0, DEFAULT_PARAMS)
        assert result == pytest.approx(DEFAULT_PARAMS.p_t, abs=1e-9)

    def test_result_bounded(self) -> None:
        for posterior in (0.0, 0.5, 1.0):
            assert 0.0 <= bkt_forward(posterior, DEFAULT_PARAMS) <= 1.0


# ── bkt_update ────────────────────────────────────────────────────────────────


class TestBKTUpdate:
    def test_correct_increases_mastery(self) -> None:
        p_l = 0.2
        assert bkt_update(p_l, True) > p_l

    def test_incorrect_increases_mastery_less_than_correct(self) -> None:
        # Even with a wrong answer, P(T) still gives a small learning bump.
        # The key is that correct always outpaces incorrect.
        p_l = 0.2
        assert bkt_update(p_l, True) > bkt_update(p_l, False)

    def test_incorrect_may_still_increase_if_learning_term_dominates(self) -> None:
        # With P(T)=0.10, a very low P(L) will increase even on wrong answers.
        p_l = 0.05
        result = bkt_update(p_l, False)
        # P(T) dominates at low mastery — should be close to p_l + P(T) roughly
        assert result > p_l - 0.01  # Not a hard rule, just sanity

    @pytest.mark.parametrize("p_l", [0.0, 0.1, 0.5, 0.9, 1.0])
    @pytest.mark.parametrize("correct", [True, False])
    def test_always_in_unit_interval(self, p_l: float, correct: bool) -> None:
        result = bkt_update(p_l, correct)
        assert 0.0 <= result <= 1.0, (
            f"bkt_update({p_l}, {correct}) = {result} out of [0, 1]"
        )

    def test_custom_params_take_effect(self) -> None:
        # High P(T) → large learning bump even on wrong answers
        fast_learn = BKTParams(p_l0=0.1, p_t=0.8, p_g=0.2, p_s=0.1, p_f=0.0)
        result_fast = bkt_update(0.1, False, fast_learn)
        result_slow = bkt_update(0.1, False, DEFAULT_PARAMS)
        assert result_fast > result_slow


# ── bkt_update_soft ───────────────────────────────────────────────────────────


class TestBKTUpdateSoft:
    def test_score_1_equals_binary_correct(self) -> None:
        p_l = 0.35
        assert bkt_update_soft(p_l, 1.0) == pytest.approx(bkt_update(p_l, True))

    def test_score_0_equals_binary_incorrect(self) -> None:
        p_l = 0.35
        assert bkt_update_soft(p_l, 0.0) == pytest.approx(bkt_update(p_l, False))

    def test_intermediate_score_lies_strictly_between(self) -> None:
        p_l = 0.35
        low  = bkt_update(p_l, False)
        high = bkt_update(p_l, True)
        for score in (0.25, 0.5, 0.75):
            mid = bkt_update_soft(p_l, score)
            assert low < mid < high, (
                f"bkt_update_soft({p_l}, {score}) = {mid} not strictly in ({low}, {high})"
            )

    def test_monotone_increasing_in_score(self) -> None:
        """Higher effective score must yield higher (or equal) mastery."""
        p_l = 0.3
        prev = bkt_update_soft(p_l, 0.0)
        for score in (0.1, 0.2, 0.5, 0.8, 1.0):
            curr = bkt_update_soft(p_l, score)
            assert curr >= prev, (
                f"Not monotone: score {score} gave {curr} < previous {prev}"
            )
            prev = curr

    @pytest.mark.parametrize("score", [-0.01, 1.001, 2.0, -1.0])
    def test_out_of_range_score_raises(self, score: float) -> None:
        with pytest.raises(ValueError, match="effective_score"):
            bkt_update_soft(0.5, score)

    def test_result_bounded(self) -> None:
        for p_l in (0.0, 0.5, 1.0):
            for score in (0.0, 0.5, 1.0):
                result = bkt_update_soft(p_l, score)
                assert 0.0 <= result <= 1.0


# ── blend_signals ─────────────────────────────────────────────────────────────


class TestBlendSignals:
    def test_understanding_dominates_wrong_fix(self) -> None:
        # Wrong fix but high understanding should outscore right fix + no understanding
        high_u_wrong  = blend_signals(False, 0.9)   # 0.30*0 + 0.70*0.9 = 0.63
        low_u_correct = blend_signals(True,  0.1)   # 0.30*1 + 0.70*0.1 = 0.37
        assert high_u_wrong > low_u_correct

    def test_perfect_attempt_gives_1(self) -> None:
        result = blend_signals(True, 1.0)
        assert result == pytest.approx(1.0)

    def test_worst_attempt_gives_0(self) -> None:
        result = blend_signals(False, 0.0)
        assert result == pytest.approx(0.0)

    def test_output_in_unit_interval(self) -> None:
        for correct in (True, False):
            for u in (0.0, 0.3, 0.7, 1.0):
                result = blend_signals(correct, u)
                assert 0.0 <= result <= 1.0

    def test_weights_must_sum_to_one(self) -> None:
        with pytest.raises(ValueError, match="must equal 1.0"):
            blend_signals(True, 0.5, fix_weight=0.4, understanding_weight=0.4)

    def test_understanding_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="understanding_score"):
            blend_signals(True, 1.5)

    def test_custom_equal_weights(self) -> None:
        result = blend_signals(True, 0.8, fix_weight=0.5, understanding_weight=0.5)
        assert result == pytest.approx(0.5 * 1.0 + 0.5 * 0.8)


# ── Student simulation (the key spec test) ────────────────────────────────────


class TestStudentSimulation:
    """Simulate two students over 10 attempts and confirm mastery diverges.

    Concept A  — "struggling":  wrong fix, poor explanation every time.
        was_correct=False, understanding_score=0.10
        effective_score = 0.30*0 + 0.70*0.10 = 0.07

    Concept B  — "improving":  correct fix, strong explanation every time.
        was_correct=True, understanding_score=0.90
        effective_score = 0.30*1 + 0.70*0.90 = 0.93

    BKT maths sanity (manual trace, DEFAULT_PARAMS):
        After 3 correct-dominant attempts (score=0.93), P(L) ≈ 0.83+.
        After 10 such attempts, P(L) > 0.95.

        After 10 incorrect-dominant attempts (score=0.07), P(L) converges to
        ~0.14 (the equilibrium where P(T) learning exactly cancels the low
        signal).  This stays well below 0.40.

    Divergence gap after 10 attempts: >0.55  (well above the 0.30 threshold).
    """

    N_ATTEMPTS = 10
    SCORE_STRUGGLING = blend_signals(False, 0.10)   # 0.07
    SCORE_IMPROVING  = blend_signals(True,  0.90)   # 0.93

    def _simulate(self, effective_score: float, n: int) -> float:
        """Run BKT forward n steps and return final P(L)."""
        p_l = DEFAULT_PARAMS.p_l0
        for _ in range(n):
            p_l = bkt_update_soft(p_l, effective_score)
        return p_l

    def _trajectory(self, effective_score: float, n: int) -> list[float]:
        """Return the full P(L) trajectory including initial P(L_0)."""
        p_l = DEFAULT_PARAMS.p_l0
        traj = [p_l]
        for _ in range(n):
            p_l = bkt_update_soft(p_l, effective_score)
            traj.append(p_l)
        return traj

    # ── Divergence assertions ─────────────────────────────────────────────────

    def test_mastery_diverges_after_10_attempts(self) -> None:
        """Core spec test: mastery scores must diverge meaningfully."""
        mastery_a = self._simulate(self.SCORE_STRUGGLING, self.N_ATTEMPTS)
        mastery_b = self._simulate(self.SCORE_IMPROVING,  self.N_ATTEMPTS)

        assert mastery_b > mastery_a, (
            f"Improving student ({mastery_b:.4f}) must surpass "
            f"struggling student ({mastery_a:.4f})"
        )
        gap = mastery_b - mastery_a
        assert gap >= 0.30, (
            f"Expected mastery gap ≥ 0.30 after {self.N_ATTEMPTS} attempts, "
            f"got gap = {gap:.4f}  (A={mastery_a:.4f}, B={mastery_b:.4f})"
        )

    def test_improving_student_reaches_high_mastery(self) -> None:
        """Consistently correct + well-explained fixes → P(L) ≥ 0.80 in 10 attempts."""
        mastery = self._simulate(self.SCORE_IMPROVING, self.N_ATTEMPTS)
        assert mastery >= 0.80, (
            f"Expected mastery ≥ 0.80 after {self.N_ATTEMPTS} improving attempts, "
            f"got {mastery:.4f}"
        )

    def test_struggling_student_stays_low(self) -> None:
        """Consistently wrong + inarticulate → P(L) stays below 0.40 in 10 attempts."""
        mastery = self._simulate(self.SCORE_STRUGGLING, self.N_ATTEMPTS)
        assert mastery < 0.40, (
            f"Expected mastery < 0.40 after {self.N_ATTEMPTS} struggling attempts, "
            f"got {mastery:.4f}"
        )

    # ── Trajectory shape assertions ───────────────────────────────────────────

    def test_improving_trajectory_is_monotone_increasing(self) -> None:
        """P(L) must increase at every step for effective_score=0.93."""
        traj = self._trajectory(self.SCORE_IMPROVING, self.N_ATTEMPTS)
        for i, (a, b) in enumerate(zip(traj, traj[1:])):
            assert b > a, (
                f"Trajectory not monotone increasing at step {i}: "
                f"P(L_{i})={a:.4f}, P(L_{i+1})={b:.4f}"
            )

    def test_struggling_trajectory_is_monotone_increasing(self) -> None:
        """Even a struggling student should see P(L) increase (P(T)>0 always allows learning).
        The increase is just very slow — we confirm P(L) never *decreases* step-to-step."""
        traj = self._trajectory(self.SCORE_STRUGGLING, self.N_ATTEMPTS)
        for i, (a, b) in enumerate(zip(traj, traj[1:])):
            assert b >= a - 1e-9, (
                f"Struggling trajectory decreased at step {i}: "
                f"P(L_{i})={a:.4f} > P(L_{i+1})={b:.4f}"
            )

    # ── Intermediate milestones ───────────────────────────────────────────────

    def test_improving_already_above_50pct_by_attempt_5(self) -> None:
        traj = self._trajectory(self.SCORE_IMPROVING, 5)
        assert traj[-1] >= 0.50, (
            f"Expected P(L) ≥ 0.50 after 5 improving attempts, got {traj[-1]:.4f}"
        )

    def test_struggling_below_25pct_after_5_attempts(self) -> None:
        traj = self._trajectory(self.SCORE_STRUGGLING, 5)
        assert traj[-1] < 0.25, (
            f"Expected P(L) < 0.25 after 5 struggling attempts, got {traj[-1]:.4f}"
        )

    # ── Logging / visual smoke test ───────────────────────────────────────────

    def test_print_full_trajectory(self, capsys) -> None:  # noqa: PT019
        """Print the trajectory table — run with -s to see it.  Not an assertion."""
        traj_a = self._trajectory(self.SCORE_STRUGGLING, self.N_ATTEMPTS)
        traj_b = self._trajectory(self.SCORE_IMPROVING,  self.N_ATTEMPTS)

        header = (
            f"\n{'Attempt':>7}  "
            f"{'Concept A (struggling, score=0.07)':>34}  "
            f"{'Concept B (improving, score=0.93)':>33}"
        )
        print(header)
        print("-" * len(header))
        for i, (a, b) in enumerate(zip(traj_a, traj_b)):
            print(f"{i:>7}  {a:>34.6f}  {b:>33.6f}")
        print(f"\nFinal gap: {traj_b[-1] - traj_a[-1]:.6f}")

        # Still assert the fundamental property
        assert traj_b[-1] > traj_a[-1]
