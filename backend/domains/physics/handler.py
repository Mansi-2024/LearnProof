"""Physics domain handler with deterministic constant tolerance checking."""

from __future__ import annotations

import re
from typing import Any

from domains.base import DomainHandler, FixResult


def extract_first_number(val: Any) -> float | None:
    """Extract float from a numeric or string value (e.g. '-9.8 m/s^2' -> -9.8)."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", val)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


class PhysicsHandler(DomainHandler):
    domain_slug = "physics"

    def generate_prompt_context(self, artifact: dict[str, Any]) -> str:
        payload = artifact.get("artifact_payload", {})
        sim_type = payload.get("sim_type", "unknown")
        constants = payload.get("constants", {})
        root_cause = artifact.get("root_cause", "")
        expected = artifact.get("expected_behavior", "")
        actual = artifact.get("actual_behavior", "")

        return (
            f"Domain: physics (sim_type: {sim_type})\n"
            f"Constants: {constants}\n"
            f"Root cause: {root_cause}\n"
            f"Expected: {expected}\n"
            f"Actual: {actual}"
        )

    def validate_fix(
        self,
        artifact: dict[str, Any],
        submitted_fix: dict[str, Any],
        submitted_explanation: str,
    ) -> FixResult:
        """Deterministically check if submitted constants match correct_constants within tolerance."""
        payload = artifact.get("artifact_payload", {})
        correct_constants = payload.get("correct_constants", {})
        submitted_constants = (
            submitted_fix.get("constants")
            or submitted_fix.get("correct_constants")
            or submitted_fix
        )

        if not isinstance(submitted_constants, dict) or not correct_constants:
            # Fall back to Grok LLM check
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback="Requires semantic evaluation.",
                details={"deterministic": False, "requires_llm_judgment": True},
            )

        matches = 0
        total = len(correct_constants)

        for key, correct_val in correct_constants.items():
            sub_val = submitted_constants.get(key)
            if sub_val is None:
                continue

            num_correct = extract_first_number(correct_val)
            num_sub = extract_first_number(sub_val)

            if num_correct is not None and num_sub is not None:
                # Check within 5% tolerance or exact if near zero
                if abs(num_correct) < 1e-6:
                    if abs(num_sub) < 1e-4:
                        matches += 1
                elif abs((num_sub - num_correct) / num_correct) <= 0.05:
                    matches += 1
            else:
                # String comparison fallback
                if str(sub_val).strip().lower() == str(correct_val).strip().lower():
                    matches += 1

        score = float(matches / total) if total > 0 else 0.0
        return FixResult(
            is_correct=score >= 0.95,
            correctness_score=score,
            understanding_score=0.0,
            feedback=f"Constant check: {matches}/{total} parameters matched ground truth within tolerance.",
            details={
                "deterministic": True,
                "matches": matches,
                "total_constants": total,
            },
        )

    def render_hint(
        self,
        artifact: dict[str, Any],
        attempt: dict[str, Any],
    ) -> str:
        payload = artifact.get("artifact_payload", {})
        sim_type = payload.get("sim_type", "physical system")
        return f"Hint: review the physical conservation laws and constants for {sim_type}."
