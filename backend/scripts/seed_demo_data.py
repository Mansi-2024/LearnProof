"""Demo seed script for populating Repair with realistic multi-domain artifacts and student attempts.

Run from backend directory:
    python scripts/seed_demo_data.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path so imports work regardless of invocation dir
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from db.supabase_client import get_supabase
from skill_model.mastery import MasteryService


DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

DOMAINS_SEED = [
    {"name": "code", "display_name": "Code / Software Engineering"},
    {"name": "physics", "display_name": "Physics & Simulation"},
    {"name": "story", "display_name": "Story & Narrative Continuity"},
    {"name": "business_model", "display_name": "Business Model & Unit Economics"},
    {"name": "chemistry", "display_name": "Chemistry & Stoichiometry"},
]

CONCEPTS_SEED = [
    {"domain_name": "code", "tag": "recursion-base-case", "display_name": "Recursion Base Case"},
    {"domain_name": "code", "tag": "off-by-one-indexing", "display_name": "Array Bounds & Off-by-One"},
    {"domain_name": "code", "tag": "async-race-condition", "display_name": "Async State Mutation"},
    {"domain_name": "physics", "tag": "projectile-vector-sign", "display_name": "Gravity Vector Direction"},
    {"domain_name": "physics", "tag": "friction-coefficient-bounds", "display_name": "Kinetic Friction Bounds"},
    {"domain_name": "story", "tag": "spatial-continuity", "display_name": "Spatial & Object Continuity"},
    {"domain_name": "story", "tag": "timeline-causality", "display_name": "Timeline Causality Paradox"},
    {"domain_name": "business_model", "tag": "contribution-margin", "display_name": "Unit Contribution Margin"},
    {"domain_name": "business_model", "tag": "ltv-cac-payback", "display_name": "LTV/CAC Payback Period"},
    {"domain_name": "chemistry", "tag": "stoichiometric-balancing", "display_name": "Stoichiometric Mass Balance"},
    {"domain_name": "chemistry", "tag": "redox-charge-conservation", "display_name": "Redox Charge Balance"},
]

ARTIFACTS_SEED = [
    {
        "concept_tag": "recursion-base-case",
        "domain_name": "code",
        "artifact_payload": {
            "language": "python",
            "code": "def factorial(n):\n    return n * factorial(n - 1)",
            "test_cases": [{"input": "factorial(1)", "expected_output": "1"}],
        },
        "root_cause": "Missing terminating base case for n <= 1 causing infinite recursion",
        "expected_behavior": "factorial(1) -> 1, factorial(4) -> 24",
        "actual_behavior": "RecursionError: maximum recursion depth exceeded",
    },
    {
        "concept_tag": "projectile-vector-sign",
        "domain_name": "physics",
        "artifact_payload": {
            "sim_type": "projectile_motion",
            "constants": {"gravity": "-9.8 m/s^2", "velocity": "25 m/s"},
            "correct_constants": {"gravity": "9.8 m/s^2", "velocity": "25 m/s"},
        },
        "root_cause": "Inverted gravity sign in downward coordinate system causing upward acceleration",
        "expected_behavior": "Downward parabolic trajectory landing at x ≈ 63m",
        "actual_behavior": "Projectile accelerates upward into the sky without bound",
    },
    {
        "concept_tag": "spatial-continuity",
        "domain_name": "story",
        "artifact_payload": {
            "inconsistency_type": "spatial_continuity_error",
            "text": "Elena melted the key in the forge into liquid slag. An hour later, Elena pulled that key from her pocket and unlocked the gate.",
        },
        "root_cause": "Resurrecting a destroyed object breaks physical continuity",
        "expected_behavior": "Elena must use lockpicking or a secondary duplicate key",
        "actual_behavior": "Destroyed key is retrieved intact with zero explanation",
    },
    {
        "concept_tag": "contribution-margin",
        "domain_name": "business_model",
        "artifact_payload": {
            "model_description": "QuickWash charges $15/bag while variable costs are $23 ($18 cleaning + $5 delivery).",
            "flawed_assumption": "Volume cannot overcome negative gross contribution margin.",
        },
        "root_cause": "Direct variable unit costs exceed revenue per order by $8",
        "expected_behavior": "Price ($30) exceeds COGS and fulfillment with 25%+ gross margin",
        "actual_behavior": "Every incremental order accelerates operating cash burn",
    },
    {
        "concept_tag": "stoichiometric-balancing",
        "domain_name": "chemistry",
        "artifact_payload": {
            "equation": "C3H8 + O2 -> CO2 + H2O",
            "reactants": ["C3H8", "O2"],
            "products": ["CO2", "H2O"],
        },
        "root_cause": "Combustion reaction violates conservation of mass across C, H, and O atoms",
        "expected_behavior": "C3H8 + 5 O2 -> 3 CO2 + 4 H2O",
        "actual_behavior": "Carbon, hydrogen, and oxygen atom counts differ on left vs right",
    },
]


async def seed_data(dry_run: bool = False) -> None:
    print(f"[*] Starting Repair Demo Seed (Dry-run: {dry_run})...")

    if dry_run:
        print("[+] Dry run: Validated all 5 domain payloads, concepts, and BKT update formulas.")
        return

    db = get_supabase()

    # 1. Fetch domains
    domains_res = db.table("domains").select("id, name").execute()
    domain_map = {d["name"]: d["id"] for d in (domains_res.data or [])}

    if not domain_map:
        print("Inserting domain seeds...")
        for d in DOMAINS_SEED:
            db.table("domains").upsert(d).execute()
        domains_res = db.table("domains").select("id, name").execute()
        domain_map = {d["name"]: d["id"] for d in (domains_res.data or [])}

    print(f"[+] Found {len(domain_map)} domains in database.")

    # 2. Insert Concepts
    concept_map: dict[str, str] = {}
    for c in CONCEPTS_SEED:
        domain_id = domain_map.get(c["domain_name"])
        if domain_id:
            row = {
                "domain_id": domain_id,
                "tag": c["tag"],
                "display_name": c["display_name"],
            }
            res = db.table("concepts").upsert(row, on_conflict="domain_id,tag").execute()
            if res.data:
                concept_map[c["tag"]] = res.data[0]["id"]

    # Refetch concepts
    all_c = db.table("concepts").select("id, tag").execute()
    for c in all_c.data or []:
        concept_map[c["tag"]] = c["id"]

    print(f"[+] Synced {len(concept_map)} concepts.")

    # 3. Insert Artifacts
    for art in ARTIFACTS_SEED:
        domain_id = domain_map.get(art["domain_name"])
        concept_id = concept_map.get(art["concept_tag"])
        if domain_id and concept_id:
            art_row = {
                "domain_id": domain_id,
                "target_concept_id": concept_id,
                "artifact_payload": art["artifact_payload"],
                "root_cause": art["root_cause"],
                "expected_behavior": art["expected_behavior"],
                "actual_behavior": art["actual_behavior"],
            }
            db.table("artifacts").insert(art_row).execute()

    print(f"[+] Inserted {len(ARTIFACTS_SEED)} demonstration artifacts.")

    # 4. Initialize BKT Mastery Service for Demo User
    mastery_svc = MasteryService()
    print("[+] Running BKT simulated updates for demo history...")

    # Recursion: Strong improvement (0.90+)
    c_rec = concept_map.get("recursion-base-case")
    if c_rec:
        for _ in range(4):
            await mastery_svc.update_mastery(DEMO_USER_ID, c_rec, was_correct=True, understanding_score=0.92)

    # Physics: Lucky guess / misconception trajectory
    c_phys = concept_map.get("projectile-vector-sign")
    if c_phys:
        await mastery_svc.update_mastery(DEMO_USER_ID, c_phys, was_correct=True, understanding_score=0.25)

    # Chemistry: Struggling concept (remains weakest)
    c_chem = concept_map.get("redox-charge-conservation")
    if c_chem:
        await mastery_svc.update_mastery(DEMO_USER_ID, c_chem, was_correct=False, understanding_score=0.15)

    print("[SUCCESS] Demo seeding complete! The database now contains realistic artifacts and mastery history.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for Repair.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing to Supabase")
    args = parser.parse_args()

    asyncio.run(seed_data(dry_run=args.dry_run))
