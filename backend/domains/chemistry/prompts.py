"""Prompt templates and generation logic for the Chemistry domain."""

from __future__ import annotations

DOMAIN_NAME = "chemistry"

SYSTEM_PROMPT = """You are a chemistry professor and chemical reaction simulator designer.
Your goal is to generate broken chemical equation, reaction stoichiometry, or reaction mechanism artifacts for students to diagnose and repair.

You must output ONLY valid JSON matching this schema:
{
  "artifact_payload": {
    "equation": "<the unbalanced, impossible, or erroneous chemical reaction equation string>",
    "reactants": ["<species 1 with stoichiometric coefficient if applicable>", "<species 2>"],
    "products": ["<species 3>", "<species 4>"]
  },
  "root_cause": "<plain-language explanation of which chemical rule is violated (e.g. conservation of mass/atoms, oxidation state impossible, violation of charge balance in redox, impossible valency/octet rule)>",
  "expected_behavior": "<the correctly balanced reaction equation and valid stoichiometric mole ratios>",
  "actual_behavior": "<the stoichiometric contradiction, atom discrepancy, or impossible intermediate created by the broken equation>"
}
"""


def build_difficulty_instruction(difficulty: float) -> str:
    """Return specific generation instructions tuned to difficulty level (0.0 - 1.0)."""
    if difficulty < 0.35:
        return (
            "DIFFICULTY LEVEL: EASY (0.0 - 0.35)\n"
            "- A simple stoichiometry imbalance or incorrect subscript on a common diatomic molecule (e.g. H + O2 -> H2O without balancing, or 2H2 + O2 -> 2H2O2).\n"
            "- Discrepancy is readily apparent by counting a single element's atoms on left vs right."
        )
    elif difficulty < 0.75:
        return (
            "DIFFICULTY LEVEL: MEDIUM (0.35 - 0.75)\n"
            "- Moderate subtlety: Polyatomic ion preservation error, combustion of complex hydrocarbon with fractional oxygen imbalance, or redox reaction where atoms balance but charge is unbalanced.\n"
            "- Requires tracking oxidation states or multiple elements simultaneously."
        )
    else:
        return (
            "DIFFICULTY LEVEL: HARD (0.75 - 1.0)\n"
            "- High subtlety: Multi-step reaction pathway, non-spontaneous thermodynamic step presented as favorable without energy coupling, or complex coordination complex ligand exchange with wrong geometry/coordination number.\n"
            "- Requires deep chemical intuition regarding reaction feasibility, intermediate stability, and electron counting."
        )


def build_generation_prompt(target_concept: str, difficulty: float) -> str:
    """Construct the user prompt for generating a broken chemistry artifact."""
    diff_guide = build_difficulty_instruction(difficulty)
    return f"""Generate a broken chemistry reaction artifact targeting the concept: "{target_concept}".

{diff_guide}

Requirements:
1. Target Concept: {target_concept}
2. Ensure realistic chemical formulas in "equation", "reactants", and "products".
3. Provide explicit explanation in "root_cause", "expected_behavior", and "actual_behavior".
4. Strictly output valid JSON without markdown code blocks or explanatory narrative.
"""


def build_fallback_prompt(target_concept: str, difficulty: float) -> str:
    """Simpler fallback prompt in case the model failed schema adherence."""
    return f"""Generate a broken chemical reaction for concept "{target_concept}" (difficulty {difficulty:.1f}).
Output strict JSON with keys "artifact_payload" (containing "equation", "reactants", "products"), "root_cause", "expected_behavior", "actual_behavior".
No markdown fences, only raw JSON.
"""
