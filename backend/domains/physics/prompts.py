"""Prompt templates and generation logic for the Physics domain."""

from __future__ import annotations

DOMAIN_NAME = "physics"

SYSTEM_PROMPT = """You are an expert physics educator and simulation designer.
Your goal is to generate broken physics simulation/problem artifacts for students to diagnose and repair.

You must output ONLY valid JSON matching this schema:
{
  "artifact_payload": {
    "sim_type": "<e.g. projectile_motion, orbital_mechanics, harmonic_oscillator, thermodynamics_cycle, circuit_rc, etc.>",
    "constants": {
      "<parameter_name>": "<flawed value with unit e.g. 'gravity': '19.6 m/s^2' or 'spring_k': '0.5 N/m' or equation expression>"
    },
    "correct_constants": {
      "<parameter_name>": "<correct ground truth value with unit>"
    }
  },
  "root_cause": "<plain-language explanation of which physical law, constant, or unit dimensional analysis is violated>",
  "expected_behavior": "<description of the physical system's expected trajectory/outcome if laws were satisfied>",
  "actual_behavior": "<description of the erroneous simulation outcome or physical paradox resulting from the broken constant>"
}
"""


def build_difficulty_instruction(difficulty: float) -> str:
    """Return specific generation instructions tuned to difficulty level (0.0 - 1.0)."""
    if difficulty < 0.35:
        return (
            "DIFFICULTY LEVEL: EASY (0.0 - 0.35)\n"
            "- A single obvious constant error or inverted sign (e.g. negative mass, gravity = 98 m/s^2, friction acting in direction of motion).\n"
            "- The violation is direct and visible from 1 basic equation."
        )
    elif difficulty < 0.75:
        return (
            "DIFFICULTY LEVEL: MEDIUM (0.35 - 0.75)\n"
            "- Moderate subtlety: unit mismatch (e.g., grams vs kg in F=ma, degrees vs radians in trigonometric angles, wrong gas constant R unit).\n"
            "- Requires checking conservation of energy or momentum across a 2-stage interaction."
        )
    else:
        return (
            "DIFFICULTY LEVEL: HARD (0.75 - 1.0)\n"
            "- Multi-variable coupling or subtle non-inertial frame / thermodynamic efficiency bound violation.\n"
            "- The error appears plausible on surface examination but violates second-order physical invariants when simulated over time."
        )


def build_generation_prompt(target_concept: str, difficulty: float) -> str:
    """Construct the user prompt for generating a broken physics artifact."""
    diff_guide = build_difficulty_instruction(difficulty)
    return f"""Generate a broken physics artifact targeting the concept: "{target_concept}".

{diff_guide}

Requirements:
1. Target Concept: {target_concept}
2. Ensure realistic physical parameter names in "constants" and ground truth in "correct_constants".
3. Provide clear explanation in "root_cause", "expected_behavior", and "actual_behavior".
4. Strictly output valid JSON without markdown code fences or conversational text.
"""


def build_fallback_prompt(target_concept: str, difficulty: float) -> str:
    """Simpler fallback prompt in case the model failed schema adherence."""
    return f"""Generate a broken physics problem for concept "{target_concept}" (difficulty {difficulty:.1f}).
Output strict JSON with keys "artifact_payload" (containing "sim_type", "constants", "correct_constants"), "root_cause", "expected_behavior", "actual_behavior".
No markdown fences, only raw JSON.
"""
