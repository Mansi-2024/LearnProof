"""Prompt templates and generation logic for the Business Model domain."""

from __future__ import annotations

DOMAIN_NAME = "business_model"

SYSTEM_PROMPT = """You are a venture capital partner, startup strategist, and unit economics diagnostician.
Your goal is to generate broken business model / startup pitch artifacts containing fatal structural or financial flaws for students to diagnose and fix.

You must output ONLY valid JSON matching this schema:
{
  "artifact_payload": {
    "model_description": "<concise description of the startup, product, target customer, monetization model, and stated unit economics (150-250 words)>",
    "flawed_assumption": "<the underlying hidden or flawed assumption that renders the business model unsustainable>"
  },
  "root_cause": "<plain-language explanation of the financial or strategic failure mechanism e.g. negative unit contribution, customer acquisition cost > lifetime value, unscalable manual fulfillment disguised as software margin>",
  "expected_behavior": "<what a sustainable, viable unit economics model would look like for this venture>",
  "actual_behavior": "<how the venture burns capital, achieves negative gross margin, or stalls at scale due to the flawed assumption>"
}
"""


def build_difficulty_instruction(difficulty: float) -> str:
    """Return specific generation instructions tuned to difficulty level (0.0 - 1.0)."""
    if difficulty < 0.35:
        return (
            "DIFFICULTY LEVEL: EASY (0.0 - 0.35)\n"
            "- A glaring arithmetic or economic flaw (e.g. selling $10 gift cards for $8 with 'we make it up on volume', or COGS directly exceeding selling price).\n"
            "- Flawed assumption is obvious from the raw numbers presented."
        )
    elif difficulty < 0.75:
        return (
            "DIFFICULTY LEVEL: MEDIUM (0.35 - 0.75)\n"
            "- Moderate subtlety: hidden second-order costs (e.g. ignoring high chargeback/returns rates, customer onboarding cost eroding 24-month LTV, regulatory licensing overhead).\n"
            "- The headline metric (e.g. 70% gross margin) hides the structural trap in payback period or churn dynamics."
        )
    else:
        return (
            "DIFFICULTY LEVEL: HARD (0.75 - 1.0)\n"
            "- High subtlety: complex marketplace dynamics (e.g. multi-sided chicken-and-egg disintermediation risk, adverse selection in risk underwriting, platform leakage where buyers and sellers transact offline after discovery).\n"
            "- Requires strategic systems thinking across ecosystem incentives."
        )


def build_generation_prompt(target_concept: str, difficulty: float) -> str:
    """Construct the user prompt for generating a broken business model artifact."""
    diff_guide = build_difficulty_instruction(difficulty)
    return f"""Generate a broken business model artifact targeting the concept: "{target_concept}".

{diff_guide}

Requirements:
1. Target Concept / Strategic Trap: {target_concept}
2. Include concrete operational and pricing numbers in "model_description".
3. Formulate the hidden trap in "flawed_assumption".
4. Strictly output valid JSON without markdown code fences or narrative introductions.
"""


def build_fallback_prompt(target_concept: str, difficulty: float) -> str:
    """Simpler fallback prompt in case the model failed schema adherence."""
    return f"""Generate a broken startup business model for concept "{target_concept}" (difficulty {difficulty:.1f}).
Output strict JSON with keys "artifact_payload" (containing "model_description", "flawed_assumption"), "root_cause", "expected_behavior", "actual_behavior".
No markdown fences, only raw JSON.
"""
