"""
Bayesian Knowledge Tracing (BKT) — pure stateless implementation.

BKT models student knowledge as a latent binary variable: the student either
knows a concept (L=1) or doesn't (L=0).  Four parameters govern the model:

    P(L_0)  prior probability of mastery before any attempt
    P(T)    probability of transitioning unknown → known on an attempt
    P(G)    probability of guessing correctly when NOT knowing
    P(S)    probability of slipping (error) when knowing
    P(F)    probability of forgetting (knowing → unknown) per attempt

Update equations
----------------
Given current mastery P(L_n) and an observed response, the update is:

1. Posterior step  —  Bayesian update on the observation:

   Correct:    P(L | corr)  =  P(L)*[1-P(S)]   /  (P(L)*[1-P(S)] + [1-P(L)]*P(G))
   Incorrect:  P(L | incorr) = P(L)*P(S)        /  (P(L)*P(S)     + [1-P(L)]*[1-P(G)])

2. Forward step  —  advance to next time-step, allowing learning and forgetting:

   P(L_{n+1}) = P(L|obs) * [1 - P(F)]  +  [1 - P(L|obs)] * P(T)

Soft (partial-credit) extension
--------------------------------
Rather than forcing a binary signal, ``bkt_update_soft`` accepts a continuous
``effective_score`` in [0, 1] and interpolates between the correct and incorrect
posteriors.  This lets understanding quality carry more signal than a binary
was_correct flag.

References
----------
Corbett & Anderson (1994) "Knowledge tracing: Modeling the acquisition of
procedural knowledge". User Modeling and User-Adapted Interaction, 4(4), 253–278.
"""

from __future__ import annotations

from dataclasses import dataclass


# ── Parameter set ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BKTParams:
    """Immutable BKT parameter set for a single concept.

    All values must lie in [0, 1].  The defaults are the commonly cited
    "standard" values from the ITS/AIED literature and the ASSIST system.
    """

    p_l0: float = 0.10  # Prior probability of mastery
    p_t: float  = 0.10  # P(learn):  unknown → known per attempt
    p_g: float  = 0.20  # P(guess):  correct response when NOT knowing
    p_s: float  = 0.10  # P(slip):   incorrect response when knowing
    p_f: float  = 0.05  # P(forget): known → unknown per attempt

    def __post_init__(self) -> None:
        for name, val in [
            ("p_l0", self.p_l0), ("p_t", self.p_t), ("p_g", self.p_g),
            ("p_s", self.p_s),   ("p_f", self.p_f),
        ]:
            if not 0.0 <= val <= 1.0:
                raise ValueError(
                    f"BKTParams.{name} must be in [0, 1], got {val}"
                )


#: Default parameters used when no concept-specific override is provided.
DEFAULT_PARAMS = BKTParams()


# ── Core BKT steps ────────────────────────────────────────────────────────────


def bkt_posterior(
    p_l: float,
    was_correct: bool,
    params: BKTParams = DEFAULT_PARAMS,
) -> float:
    """Bayesian update: compute P(L | observation).

    Answers the question: given that the student responded correctly (or not),
    what is the updated probability that they actually know the concept?

    This is *not* the final next-step estimate — call ``bkt_forward`` afterwards.

    Args:
        p_l:         Current mastery probability P(L_n).
        was_correct: Whether the response was correct.
        params:      BKT parameter set.

    Returns:
        P(L | observation) — posterior before the forward step.
    """
    if was_correct:
        numerator   = p_l * (1.0 - params.p_s)
        denominator = numerator + (1.0 - p_l) * params.p_g
    else:
        numerator   = p_l * params.p_s
        denominator = numerator + (1.0 - p_l) * (1.0 - params.p_g)

    return numerator / denominator if denominator > 0.0 else p_l


def bkt_forward(
    p_l_posterior: float,
    params: BKTParams = DEFAULT_PARAMS,
) -> float:
    """Forward step: advance from posterior to P(L_{n+1}).

    Applies the learning and forgetting transitions:
        P(L_{n+1}) = P(L|obs) * (1 - P(F))  +  (1 - P(L|obs)) * P(T)

    Args:
        p_l_posterior: Result of ``bkt_posterior()``.
        params:        BKT parameter set.

    Returns:
        P(L_{n+1}) — mastery estimate after this attempt.
    """
    return (
        p_l_posterior * (1.0 - params.p_f)
        + (1.0 - p_l_posterior) * params.p_t
    )


def bkt_update(
    p_l: float,
    was_correct: bool,
    params: BKTParams = DEFAULT_PARAMS,
) -> float:
    """Full BKT update (posterior + forward), returning P(L_{n+1}).

    Convenience wrapper combining ``bkt_posterior`` and ``bkt_forward``.

    Args:
        p_l:         Current mastery probability P(L_n).
        was_correct: Whether the response was correct.
        params:      BKT parameter set.

    Returns:
        P(L_{n+1}) clamped to [0, 1].
    """
    posterior = bkt_posterior(p_l, was_correct, params)
    return float(min(max(bkt_forward(posterior, params), 0.0), 1.0))


# ── Soft (partial-credit) extension ──────────────────────────────────────────


def bkt_update_soft(
    p_l: float,
    effective_score: float,
    params: BKTParams = DEFAULT_PARAMS,
) -> float:
    """Soft BKT update using a continuous correctness signal in [0, 1].

    Interpolates between the fully-correct and fully-incorrect next-step
    mastery estimates, weighted by ``effective_score``:

        P(L_{n+1}) = score * P(L_{n+1}|correct)  +  (1-score) * P(L_{n+1}|incorrect)

    This enables partial credit: a student who scores 0.7 should benefit less
    than one who scores 1.0, even if the raw fix was technically "right".

    Boundary cases:
        bkt_update_soft(p_l, 1.0, params) == bkt_update(p_l, True,  params)
        bkt_update_soft(p_l, 0.0, params) == bkt_update(p_l, False, params)

    Args:
        p_l:             Current mastery probability P(L_n).
        effective_score: Blended correctness signal in [0.0, 1.0].
        params:          BKT parameter set.

    Returns:
        P(L_{n+1}) clamped to [0, 1].

    Raises:
        ValueError: If effective_score is outside [0, 1].
    """
    if not 0.0 <= effective_score <= 1.0:
        raise ValueError(
            f"effective_score must be in [0, 1], got {effective_score}"
        )

    p_l_correct   = bkt_update(p_l, True,  params)
    p_l_incorrect = bkt_update(p_l, False, params)
    blended = effective_score * p_l_correct + (1.0 - effective_score) * p_l_incorrect
    return float(min(max(blended, 0.0), 1.0))


# ── Signal blending ───────────────────────────────────────────────────────────


def blend_signals(
    was_correct: bool,
    understanding_score: float,
    *,
    fix_weight: float = 0.30,
    understanding_weight: float = 0.70,
) -> float:
    """Blend fix correctness and explanation quality into a single score.

    A submitted fix can be a lucky guess, so understanding_score receives
    the higher weight (0.70) by default.  The two weights must sum to 1.0.

    Args:
        was_correct:          Whether the submitted fix was correct.
        understanding_score:  Quality of the student's explanation, in [0, 1].
        fix_weight:           Weight given to the binary correctness signal.
        understanding_weight: Weight given to understanding_score.

    Returns:
        Blended effective score in [0.0, 1.0].

    Raises:
        ValueError: If weights do not sum to 1.0 or understanding_score is
                    outside [0, 1].
    """
    if abs(fix_weight + understanding_weight - 1.0) > 1e-6:
        raise ValueError(
            f"fix_weight ({fix_weight}) + understanding_weight ({understanding_weight})"
            " must equal 1.0"
        )
    if not 0.0 <= understanding_score <= 1.0:
        raise ValueError(
            f"understanding_score must be in [0, 1], got {understanding_score}"
        )

    return fix_weight * float(was_correct) + understanding_weight * understanding_score
