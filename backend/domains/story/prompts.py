"""Prompt templates and generation logic for the Story / Narrative domain."""

from __future__ import annotations

DOMAIN_NAME = "story"

SYSTEM_PROMPT = """You are an expert narrative theorist, creative writing editor, and cognitive puzzle designer.
Your goal is to generate short literary/narrative artifacts containing deliberate narrative, logical, or structural inconsistencies for students to identify and repair.

You must output ONLY valid JSON matching this schema:
{
  "artifact_payload": {
    "text": "<the narrative excerpt (150-300 words) containing the embedded flaw>",
    "inconsistency_type": "<e.g. timeline_paradox, character_knowledge_leak, spatial_continuity_error, motivation_inversion, chekhovs_gun_contradiction, causal_inversion>"
  },
  "root_cause": "<plain-language explanation of exactly where and why the narrative logic breaks down>",
  "expected_behavior": "<how the scene should logically progress or what narrative consistency requires>",
  "actual_behavior": "<what contradiction or impossibility occurs in the text>"
}
"""


def build_difficulty_instruction(difficulty: float) -> str:
    """Return specific generation instructions tuned to difficulty level (0.0 - 1.0)."""
    if difficulty < 0.35:
        return (
            "DIFFICULTY LEVEL: EASY (0.0 - 0.35)\n"
            "- A direct, obvious contradiction in consecutive sentences (e.g. John locked the wooden door from the outside, then reached inside and grabbed his keys off the table).\n"
            "- Flaw is localized to a single sentence or explicit fact."
        )
    elif difficulty < 0.75:
        return (
            "DIFFICULTY LEVEL: MEDIUM (0.35 - 0.75)\n"
            "- Moderate subtlety: character acts on information they could not yet know, or an unmentioned time gap violates travel distance logic across two paragraphs.\n"
            "- Requires cross-referencing facts established earlier in the excerpt."
        )
    else:
        return (
            "DIFFICULTY LEVEL: HARD (0.75 - 1.0)\n"
            "- High subtlety: a deep psychological motivation paradox or multi-character causal chain where a subtle assumption about off-screen events renders the climax impossible.\n"
            "- Requires deductive reasoning across the entire text to isolate the underlying narrative flaw."
        )


def build_generation_prompt(target_concept: str, difficulty: float) -> str:
    """Construct the user prompt for generating a broken story artifact."""
    diff_guide = build_difficulty_instruction(difficulty)
    return f"""Generate a broken narrative artifact targeting the concept: "{target_concept}".

{diff_guide}

Requirements:
1. Target Concept / Inconsistency: {target_concept}
2. The excerpt in "text" should be engaging, coherent in style, but contain the deliberate flaw.
3. Classify the flaw accurately in "inconsistency_type".
4. Strictly output valid JSON without markdown formatting fences or conversational preamble.
"""


def build_fallback_prompt(target_concept: str, difficulty: float) -> str:
    """Simpler fallback prompt in case the model failed schema adherence."""
    return f"""Generate a short story excerpt with a narrative inconsistency for concept "{target_concept}" (difficulty {difficulty:.1f}).
Output strict JSON with keys "artifact_payload" (containing "text", "inconsistency_type"), "root_cause", "expected_behavior", "actual_behavior".
No markdown fences, only raw JSON.
"""
