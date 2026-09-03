"""Prompt templates and generation logic for the Code domain."""

from __future__ import annotations

DOMAIN_NAME = "code"

SYSTEM_PROMPT = """You are an expert software engineering instructor and test artifact generator.
Your goal is to generate broken code artifacts for students to diagnose and repair.

You must output ONLY valid JSON matching this schema:
{
  "artifact_payload": {
    "language": "<programming language e.g. python, typescript, etc.>",
    "code": "<the complete broken code snippet>",
    "test_cases": [
      {
        "input": "<description or representation of input>",
        "expected_output": "<what correct execution produces>",
        "actual_output": "<what broken execution produces or error>"
      }
    ]
  },
  "root_cause": "<concise explanation of the underlying bug>",
  "expected_behavior": "<what the program should accomplish>",
  "actual_behavior": "<how the program fails or misbehaves>"
}
"""


def build_difficulty_instruction(difficulty: float) -> str:
    """Return specific generation instructions tuned to difficulty level (0.0 - 1.0)."""
    if difficulty < 0.35:
        return (
            "DIFFICULTY LEVEL: EASY (0.0 - 0.35)\n"
            "- The bug should be a single, obvious flaw (e.g., simple off-by-one, typo in variable, missing base case check).\n"
            "- Code snippet should be concise (10-20 lines).\n"
            "- The failure should be immediately visible in the primary test case."
        )
    elif difficulty < 0.75:
        return (
            "DIFFICULTY LEVEL: MEDIUM (0.35 - 0.75)\n"
            "- The bug should be moderately subtle (e.g., unintended mutation of shared state, edge case in recursion, inverted boolean predicate, incorrect boundary condition).\n"
            "- Code snippet should be 20-35 lines with realistic helper logic.\n"
            "- Standard cases might pass, but specific edge-case test cases fail."
        )
    else:
        return (
            "DIFFICULTY LEVEL: HARD (0.75 - 1.0)\n"
            "- The bug must be subtle and emergent across multiple steps (e.g., race condition simulation, subtle asymptotic explosion, shallow vs deep copy lifecycle flaw, complex invariant violation).\n"
            "- Code snippet should be 30-50 lines with layered logic.\n"
            "- Requires tracing execution flow across multiple functions or iterations to pinpoint root cause."
        )


def build_generation_prompt(target_concept: str, difficulty: float) -> str:
    """Construct the user prompt for generating a broken code artifact."""
    diff_guide = build_difficulty_instruction(difficulty)
    return f"""Generate a broken code artifact targeting the concept: "{target_concept}".

{diff_guide}

Requirements:
1. Target Concept: {target_concept}
2. Ensure the code is realistic and self-contained.
3. Include at least 2 test cases (at least one failing test demonstrating the bug).
4. Strictly output valid JSON without any markdown code fence wrappers or extraneous commentary.
"""


def build_fallback_prompt(target_concept: str, difficulty: float) -> str:
    """Simpler fallback prompt in case the model failed schema adherence."""
    return f"""Generate a broken Python code snippet for concept "{target_concept}" (difficulty {difficulty:.1f}).
Output strict JSON with keys "artifact_payload" (containing "language", "code", "test_cases"), "root_cause", "expected_behavior", "actual_behavior".
No markdown fences, only raw JSON.
"""
