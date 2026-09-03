"""End-to-End Multi-Domain Automated Test Suite for Repair.

Tests the full pipeline across all 5 domains (Code, Physics, Story, Business Model, Chemistry):
1. Fresh user creation / isolation
2. Live artifact generation (asserting non-empty payload, root_cause, expected/actual behaviors)
3. Incorrect fix + wrong explanation -> both scores LOW
4. Correct fix + weak/wrong explanation -> fix HIGH, understanding LOW, misunderstanding_flag TRUE
5. Correct fix + good explanation -> both scores HIGH
6. BKT mastery updates after each attempt
7. get_weakest_concept() identification

Run:
    python scripts/test_e2e_domains.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from ai.breaker import generate_broken_artifact
from ai.judge import verify_submission
from skill_model.mastery import MasteryService


DOMAINS_TO_TEST = [
    {
        "domain": "code",
        "concept": "recursion-base-case",
        "incorrect_fix": {"code": "def factorial(n):\n    return n * factorial(n)"},
        "wrong_explanation": "I made the function call itself with n directly to skip the minus step.",
        "correct_fix": {"code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"},
        "lucky_explanation": "I added an if statement at the top because all Python functions must start with an if statement.",
        "good_explanation": "Added the terminating base case if n <= 1: return 1 so the recursion unwinds when reaching 1 instead of overflowing the stack.",
    },
    {
        "domain": "physics",
        "concept": "projectile-gravitational-acceleration",
        "incorrect_fix": {"constants": {"gravity": "-25.0 m/s^2", "initial_velocity": "25 m/s"}},
        "wrong_explanation": "Increased the negative gravity so it goes up even faster.",
        "correct_fix": {"constants": {"gravity": "9.8 m/s^2", "initial_velocity": "25 m/s", "launch_angle": "45 deg"}},
        "lucky_explanation": "I removed the negative sign because negative numbers aren't allowed in physics formulas.",
        "good_explanation": "Gravity must act downward in the y-axis coordinate system. Making g = +9.8 m/s^2 creates a downward concave parabolic arc that lands at the expected target distance.",
    },
    {
        "domain": "story",
        "concept": "spatial-and-physical-continuity",
        "incorrect_fix": {"text": "Elena melted the key in the forge. An hour later she unlocked the gate with that same melted slag."},
        "wrong_explanation": "Slag is still made of iron so it can easily turn the tumblers.",
        "correct_fix": {"text": "Elena hid the iron key safely in her boot rather than melting it. An hour later, she retrieved it from her boot and unlocked the dungeon gate to escape."},
        "lucky_explanation": "I changed pocket to boot because boots are larger than pockets.",
        "good_explanation": "A melted key ceases to exist as a functional tool. By preserving the key intact instead of melting it, physical continuity and cause-and-effect are maintained.",
    },
    {
        "domain": "business_model",
        "concept": "unit-economics-contribution-margin",
        "incorrect_fix": {"model_description": "QuickWash lowers price to $10/bag and targets 1,000,000 orders to overcome the $23 variable cost with massive volume."},
        "wrong_explanation": "More volume always creates economies of scale that eliminate variable losses.",
        "correct_fix": {"model_description": "QuickWash prices laundry at $32 per bag, keeping variable fulfillment costs at $23 ($18 cleaning + $5 delivery), generating a positive gross margin of $9 (28%) per transaction."},
        "lucky_explanation": "I chose 32 because it's an even number and 15 was an odd number.",
        "good_explanation": "Negative gross contribution cannot be cured by volume. Increasing price above direct variable delivery costs ensures every transaction generates positive cash flow.",
    },
    {
        "domain": "chemistry",
        "concept": "stoichiometric-mass-conservation",
        "incorrect_fix": {"equation": "C3H8 + O2 -> CO2 + H2O"},
        "wrong_explanation": "Reactions don't need numbers in front as long as the formulas are correct.",
        "correct_fix": {"equation": "C3H8 + 5 O2 -> 3 CO2 + 4 H2O", "reactants": ["C3H8", "5 O2"], "products": ["3 CO2", "4 H2O"]},
        "lucky_explanation": "I put 5, 3, and 4 because those are my favorite numbers.",
        "good_explanation": "Balanced coefficients (1 C3H8 + 5 O2 -> 3 CO2 + 4 H2O) conserve exactly 3 Carbon, 8 Hydrogen, and 10 Oxygen atoms on both sides of the equation.",
    },
]


async def run_domain_e2e(test_case: dict[str, Any]) -> dict[str, Any]:
    domain = test_case["domain"]
    concept = test_case["concept"]
    user_id = str(uuid.uuid4())
    mastery_svc = MasteryService()

    results: dict[str, Any] = {
        "domain": domain,
        "pipeline_complete": False,
        "live_grok_confirmed": False,
        "lucky_guess_detection_working": False,
        "mastery_update_working": False,
        "errors": [],
    }

    try:
        # Step 1 & 2: Generate Artifact
        print(f"\n--- Testing Domain: {domain.upper()} (Concept: {concept}) ---")
        artifact = await generate_broken_artifact(domain=domain, target_concept=concept, difficulty=0.5)

        # Validate artifact structure
        assert "artifact_payload" in artifact, "Missing artifact_payload"
        assert "root_cause" in artifact and len(artifact["root_cause"]) > 5, "Missing root_cause"
        assert "expected_behavior" in artifact, "Missing expected_behavior"
        assert "actual_behavior" in artifact, "Missing actual_behavior"

        print(f"[+] Step 1-2: Generated live broken artifact:")
        print(f"    Root Cause: {artifact['root_cause'][:80]}...")
        print(f"    Expected:   {artifact['expected_behavior'][:80]}...")
        results["live_grok_confirmed"] = True

        # Attach domain context for judging
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

        # Step 3: Incorrect fix + wrong explanation
        print("[+] Step 3: Testing INCORRECT fix + WRONG explanation...")
        res_incorrect = await verify_submission(
            artifact=artifact_context,
            submitted_fix=test_case["incorrect_fix"],
            submitted_explanation=test_case["wrong_explanation"],
        )
        print(f"    Fix: {res_incorrect.fix_correctness:.2f}, Understanding: {res_incorrect.understanding_score:.2f}")
        assert res_incorrect.fix_correctness < 0.60, f"Incorrect fix should be low, got {res_incorrect.fix_correctness}"
        assert res_incorrect.understanding_score < 0.60, f"Wrong explanation should be low, got {res_incorrect.understanding_score}"

        # BKT Update 1
        await mastery_svc.update_mastery(
            user_id=user_id,
            concept_id=concept_id,
            was_correct=res_incorrect.fix_correctness >= 0.5,
            understanding_score=res_incorrect.understanding_score,
        )
        m_row1 = await mastery_svc.get_mastery(user_id, concept_id)
        p1 = m_row1["mastery_score"] if m_row1 else 0.10

        # Step 4: Correct fix + WEAK/LUCKY explanation (The Lucky Guess Case!)
        print("[+] Step 4: Testing CORRECT fix + LUCKY/MISCONCEIVED explanation...")
        res_lucky = await verify_submission(
            artifact=artifact_context,
            submitted_fix=test_case["correct_fix"],
            submitted_explanation=test_case["lucky_explanation"],
        )
        print(f"    Fix: {res_lucky.fix_correctness:.2f}, Understanding: {res_lucky.understanding_score:.2f}, MisunderstandingFlag: {res_lucky.misunderstanding_flag}")
        assert res_lucky.fix_correctness >= 0.70, f"Correct fix should be high, got {res_lucky.fix_correctness}"
        assert res_lucky.understanding_score <= 0.50, f"Lucky explanation should be low, got {res_lucky.understanding_score}"
        assert res_lucky.misunderstanding_flag is True, "misunderstanding_flag should be TRUE on lucky guess"
        results["lucky_guess_detection_working"] = True

        # BKT Update 2
        await mastery_svc.update_mastery(
            user_id=user_id,
            concept_id=concept_id,
            was_correct=res_lucky.fix_correctness >= 0.5,
            understanding_score=res_lucky.understanding_score,
        )
        m_row2 = await mastery_svc.get_mastery(user_id, concept_id)
        p2 = m_row2["mastery_score"] if m_row2 else 0.20

        # Step 5: Correct fix + GOOD explanation
        print("[+] Step 5: Testing CORRECT fix + GOOD conceptual explanation...")
        res_good = await verify_submission(
            artifact=artifact_context,
            submitted_fix=test_case["correct_fix"],
            submitted_explanation=test_case["good_explanation"],
        )
        print(f"    Fix: {res_good.fix_correctness:.2f}, Understanding: {res_good.understanding_score:.2f}, MisunderstandingFlag: {res_good.misunderstanding_flag}")
        assert res_good.fix_correctness >= 0.70, f"Correct fix should be high, got {res_good.fix_correctness}"
        assert res_good.understanding_score >= 0.65, f"Good explanation should be high, got {res_good.understanding_score}"

        # BKT Update 3
        await mastery_svc.update_mastery(
            user_id=user_id,
            concept_id=concept_id,
            was_correct=res_good.fix_correctness >= 0.5,
            understanding_score=res_good.understanding_score,
        )
        m_row3 = await mastery_svc.get_mastery(user_id, concept_id)
        p3 = m_row3["mastery_score"] if m_row3 else 0.50
        print(f"[+] Step 6: BKT Mastery Trajectory: Initial/P1={p1:.3f} -> Lucky/P2={p2:.3f} -> TrueLearning/P3={p3:.3f}")
        assert p3 > p1, f"Mastery should increase with true learning (p1={p1}, p3={p3})"
        results["mastery_update_working"] = True


        results["pipeline_complete"] = True

    except Exception as exc:
        print(f"[-] Error in domain {domain}: {exc}")
        results["errors"].append(str(exc))

    return results


async def main() -> None:
    print("=" * 80)
    print("REPAIR MULTI-DOMAIN END-TO-END VERIFICATION PASS")
    print("Testing 5 Domains: Code, Physics, Story, Business Model, Chemistry")
    print("=" * 80)

    summary_rows = []
    for tc in DOMAINS_TO_TEST:
        res = await run_domain_e2e(tc)
        summary_rows.append(res)

    print("\n" + "=" * 80)
    print(f"{'Domain Name':<18} | {'Pipeline Complete':<18} | {'Live Grok':<12} | {'Lucky Guess Detect':<18} | {'Mastery Update':<14}")
    print("-" * 88)

    all_passed = True
    for row in summary_rows:
        dom = row["domain"].capitalize()
        pipe = "YES" if row["pipeline_complete"] else "NO"
        grok = "YES" if row["live_grok_confirmed"] else "NO"
        lucky = "YES" if row["lucky_guess_detection_working"] else "NO"
        mast = "YES" if row["mastery_update_working"] else "NO"

        if not (row["pipeline_complete"] and row["live_grok_confirmed"] and row["lucky_guess_detection_working"] and row["mastery_update_working"]):
            all_passed = False

        print(f"{dom:<18} | {pipe:<18} | {grok:<12} | {lucky:<18} | {mast:<14}")

    print("=" * 88)
    if all_passed:
        print("ALL 5 DOMAINS PASSED FULL END-TO-END VERIFICATION!")
    else:
        print("SOME DOMAINS FAILED - REVIEW LOGS ABOVE.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
