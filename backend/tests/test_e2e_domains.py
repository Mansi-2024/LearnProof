"""Pytest integration tests for End-to-End multi-domain pipeline."""

from __future__ import annotations

import uuid
import pytest

from ai.breaker import generate_broken_artifact
from ai.judge import verify_submission
from skill_model.mastery import MasteryService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "domain,concept,incorrect_fix,wrong_exp,correct_fix,lucky_exp,good_exp",
    [
        (
            "code",
            "recursion-base-case",
            {"code": "def factorial(n):\n    return n * factorial(n)"},
            "I made the function call itself with n directly to skip the minus step.",
            {"code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"},
            "I added an if statement at the top because all Python functions must start with an if statement.",
            "Added terminating base case if n <= 1: return 1 so recursion unwinds instead of infinite loop.",
        ),
        (
            "physics",
            "projectile-gravitational-acceleration",
            {"constants": {"gravity": "-25.0 m/s^2", "initial_velocity": "25 m/s"}},
            "Increased the negative gravity so it goes up even faster.",
            {"constants": {"gravity": "9.8 m/s^2", "initial_velocity": "25 m/s", "launch_angle": "45 deg"}},
            "I removed the negative sign because negative numbers aren't allowed in physics formulas.",
            "Gravity must act downward in the y-axis coordinate system. Making g = +9.8 m/s^2 creates a downward concave parabolic arc that lands at the expected target distance.",
        ),
        (
            "story",
            "spatial-and-physical-continuity",
            {"text": "Elena melted the key in the forge. An hour later she unlocked the gate with that same melted slag."},
            "Slag is still made of iron so it can easily turn the tumblers.",
            {"text": "Elena hid the iron key safely in her boot rather than melting it. An hour later, she retrieved it from her boot and unlocked the dungeon gate to escape."},
            "I changed pocket to boot because boots are larger than pockets.",
            "A melted key ceases to exist as a functional tool. By preserving the key intact instead of melting it, physical continuity and cause-and-effect are maintained.",
        ),
        (
            "business_model",
            "unit-economics-contribution-margin",
            {"model_description": "QuickWash lowers price to $10/bag and targets 1,000,000 orders to overcome the $23 variable cost with massive volume."},
            "More volume always creates economies of scale that eliminate variable losses.",
            {"model_description": "QuickWash prices laundry at $32 per bag, keeping variable fulfillment costs at $23 ($18 cleaning + $5 delivery), generating a positive gross margin of $9 (28%) per transaction."},
            "I chose 32 because it's an even number and 15 was an odd number.",
            "Negative gross contribution cannot be cured by volume. Increasing price above direct variable delivery costs ensures every transaction generates positive cash flow.",
        ),
        (
            "chemistry",
            "stoichiometric-mass-conservation",
            {"equation": "C3H8 + O2 -> CO2 + H2O"},
            "Reactions don't need numbers in front as long as the formulas are correct.",
            {"equation": "C3H8 + 5 O2 -> 3 CO2 + 4 H2O", "reactants": ["C3H8", "5 O2"], "products": ["3 CO2", "4 H2O"]},
            "I put 5, 3, and 4 because those are my favorite numbers.",
            "Balanced coefficients (1 C3H8 + 5 O2 -> 3 CO2 + 4 H2O) conserve exactly 3 Carbon, 8 Hydrogen, and 10 Oxygen atoms on both sides of the equation.",
        ),
    ],
)
async def test_domain_full_pipeline(
    domain, concept, incorrect_fix, wrong_exp, correct_fix, lucky_exp, good_exp
):
    user_id = str(uuid.uuid4())
    mastery_svc = MasteryService()

    # 1. Generate artifact
    artifact = await generate_broken_artifact(domain=domain, target_concept=concept, difficulty=0.5)
    assert "artifact_payload" in artifact
    assert "root_cause" in artifact

    artifact_context = {
        "id": str(uuid.uuid4()),
        "domain_slug": domain,
        "domains": {"name": domain},
        "target_concept_id": str(uuid.uuid4()),
        "artifact_payload": artifact["artifact_payload"],
        "root_cause": artifact["root_cause"],
        "expected_behavior": artifact["expected_behavior"],
        "actual_behavior": artifact["actual_behavior"],
    }
    concept_id = artifact_context["target_concept_id"]

    # 2. Incorrect submission -> both scores low
    res_inc = await verify_submission(artifact_context, incorrect_fix, wrong_exp)
    assert res_inc.fix_correctness < 0.60
    assert res_inc.understanding_score < 0.60

    await mastery_svc.update_mastery(user_id, concept_id, False, res_inc.understanding_score)
    p_low = (await mastery_svc.get_mastery(user_id, concept_id))["mastery_score"]

    # 3. Lucky guess submission -> fix high, understanding low, misunderstanding_flag TRUE
    res_lucky = await verify_submission(artifact_context, correct_fix, lucky_exp)
    assert res_lucky.fix_correctness >= 0.70
    assert res_lucky.understanding_score <= 0.50
    assert res_lucky.misunderstanding_flag is True

    await mastery_svc.update_mastery(user_id, concept_id, True, res_lucky.understanding_score)
    p_mid = (await mastery_svc.get_mastery(user_id, concept_id))["mastery_score"]

    # 4. Good submission -> both high
    res_good = await verify_submission(artifact_context, correct_fix, good_exp)
    assert res_good.fix_correctness >= 0.70
    assert res_good.understanding_score >= 0.65

    await mastery_svc.update_mastery(user_id, concept_id, True, res_good.understanding_score)
    p_high = (await mastery_svc.get_mastery(user_id, concept_id))["mastery_score"]


    assert p_high > p_low
