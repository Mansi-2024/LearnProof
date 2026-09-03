"""Grok-based AI Judge and Verification Engine.

Evaluates student repair submissions along two orthogonal dimensions:
1. ``fix_correctness`` (0.0 - 1.0): Evaluates if the fix resolves the artifact's
   root cause using deterministic checks (where available) or Grok LLM evaluation.
2. ``understanding_score`` (0.0 - 1.0): Semantically compares the student's explanation
   against the ground truth ``root_cause`` to verify conceptual comprehension.
3. ``misunderstanding_flag`` (bool): Detects when a student gets lucky with a working fix
   while holding a fundamental misconception (the most critical pedagogical signal).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from ai.breaker import extract_json
from ai.grok_client import GrokClient
from domains import DOMAIN_REGISTRY

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Structured result returned by ``verify_submission``."""

    fix_correctness: float  # [0.0, 1.0]
    understanding_score: float  # [0.0, 1.0]
    feedback_text: str
    misunderstanding_flag: bool
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fix_correctness": round(self.fix_correctness, 4),
            "understanding_score": round(self.understanding_score, 4),
            "feedback_text": self.feedback_text,
            "misunderstanding_flag": self.misunderstanding_flag,
            "details": self.details,
        }


# ── LLM Prompts for Judge ─────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an expert diagnostic tutor and code/problem evaluator.
Your mission is to rigorously evaluate a student's proposed fix and explanation for a broken artifact.

You must evaluate TWO orthogonal dimensions:
1. Fix Correctness: Did the submitted fix actually solve the root cause?
2. Understanding Score: Did the student's explanation correctly identify WHY the artifact was broken?

CRITICAL MISCONCEPTION DETECTION:
Pay special attention to lucky guesses — cases where the fix coincidentally works or passes, but the student's explanation reveals a fundamental misunderstanding (e.g. claiming Python lists are 1-indexed, confusing velocity with acceleration, or making up non-existent rules).
If the fix is correct (>=0.7) but the explanation contains a false rationale (<0.5), set "misunderstanding_flag": true.

Output strict JSON only matching:
{
  "fix_correctness": <float 0.0 to 1.0>,
  "understanding_score": <float 0.0 to 1.0>,
  "misunderstanding_flag": <bool>,
  "fix_analysis": "<concise review of the fix>",
  "explanation_analysis": "<concise review of whether explanation grasped root cause>",
  "feedback_text": "<clear, encouraging, constructive feedback for the student>"
}
"""


def build_judge_prompt(
    artifact: dict[str, Any],
    submitted_fix: dict[str, Any],
    submitted_explanation: str,
    deterministic_score: float | None = None,
) -> str:
    payload = artifact.get("artifact_payload", {})
    root_cause = artifact.get("root_cause", "")
    expected = artifact.get("expected_behavior", "")
    actual = artifact.get("actual_behavior", "")

    det_str = (
        f"Deterministic Check Score: {deterministic_score:.2f} (use this as strong baseline for fix_correctness)"
        if deterministic_score is not None
        else "No deterministic check available for this domain — judge fix_correctness semantically."
    )

    return f"""EVALUATE STUDENT SUBMISSION:

ARTIFACT CONTEXT:
- Expected Behavior: {expected}
- Actual Behavior: {actual}
- True Root Cause (Ground Truth): {root_cause}
- Broken Payload: {json.dumps(payload, indent=2)}

STUDENT SUBMISSION:
- Submitted Fix: {json.dumps(submitted_fix, indent=2)}
- Submitted Explanation: "{submitted_explanation}"

EVALUATION BASELINE:
{det_str}

Evaluate fix_correctness (0.0-1.0), understanding_score (0.0-1.0), misunderstanding_flag (bool), and provide constructive feedback_text. Output raw JSON only.
"""


# ── Core Judge Function ───────────────────────────────────────────────────────


async def verify_submission(
    artifact: dict[str, Any],
    submitted_fix: dict[str, Any],
    submitted_explanation: str,
    *,
    grok_client: GrokClient | None = None,
) -> VerificationResult:
    """Judge a student's fix and explanation.

    1. Executes deterministic validation via the domain handler if available.
    2. Calls Grok to evaluate conceptual understanding vs ground-truth root cause.
    3. Detects lucky guesses / misconceptions where fix worked but explanation was wrong.
    4. Returns a ``VerificationResult``.
    """
    domain_slug = artifact.get("domains", {}).get("name") or artifact.get("domain_slug") or ""
    handler = DOMAIN_REGISTRY.get(domain_slug)

    deterministic_result = None
    if handler is not None:
        try:
            deterministic_result = handler.validate_fix(
                artifact=artifact,
                submitted_fix=submitted_fix,
                submitted_explanation=submitted_explanation,
            )
        except Exception as exc:
            logger.warning("Deterministic validation failed: %s", exc)

    det_score: float | None = None
    if deterministic_result and deterministic_result.details.get("deterministic"):
        det_score = deterministic_result.correctness_score

    client = grok_client or GrokClient()
    prompt = build_judge_prompt(
        artifact=artifact,
        submitted_fix=submitted_fix,
        submitted_explanation=submitted_explanation,
        deterministic_score=det_score,
    )

    try:
        response = await client.chat(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw_text = response["choices"][0]["message"]["content"]
        data = extract_json(raw_text)

        # Extract scores
        fix_corr = float(data.get("fix_correctness", det_score if det_score is not None else 0.0))
        # Override with deterministic check if deterministic check is high confidence
        if det_score is not None:
            fix_corr = det_score

        understanding_score = float(data.get("understanding_score", 0.0))
        misunderstanding_flag = bool(data.get("misunderstanding_flag", False))

        # Explicit heuristic check: working fix (>=0.7) + low understanding (<0.5)
        if fix_corr >= 0.70 and understanding_score < 0.50:
            misunderstanding_flag = True

        feedback = str(data.get("feedback_text", "Submission evaluated."))
        if misunderstanding_flag and "misunderstanding" not in feedback.lower() and "guess" not in feedback.lower():
            feedback += " Note: While your fix resolved the symptom, your explanation indicates a misunderstanding of the true root cause."

        return VerificationResult(
            fix_correctness=min(max(fix_corr, 0.0), 1.0),
            understanding_score=min(max(understanding_score, 0.0), 1.0),
            feedback_text=feedback,
            misunderstanding_flag=misunderstanding_flag,
            details={
                "fix_analysis": data.get("fix_analysis", ""),
                "explanation_analysis": data.get("explanation_analysis", ""),
                "deterministic_used": det_score is not None,
            },
        )

    except Exception as exc:
        logger.error("AI Judge evaluation failed: %s", exc)
        # Fallback if Grok call fails
        fallback_fix_score = det_score if det_score is not None else 0.0
        fallback_u_score = 0.5 if len(submitted_explanation.strip()) > 30 else 0.0
        is_misunderstanding = fallback_fix_score >= 0.7 and fallback_u_score < 0.5

        return VerificationResult(
            fix_correctness=fallback_fix_score,
            understanding_score=fallback_u_score,
            feedback_text=(
                deterministic_result.feedback
                if deterministic_result
                else "Evaluation completed using fallback rules."
            ),
            misunderstanding_flag=is_misunderstanding,
            details={"fallback": True, "error": str(exc)},
        )
