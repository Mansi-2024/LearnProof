"""Chemistry domain handler with stoichiometric and formula validation."""

from __future__ import annotations

import re
from typing import Any

from domains.base import DomainHandler, FixResult


class ChemistryHandler(DomainHandler):
    domain_slug = "chemistry"

    def generate_prompt_context(self, artifact: dict[str, Any]) -> str:
        payload = artifact.get("artifact_payload", {})
        equation = payload.get("equation", "")
        reactants = payload.get("reactants", [])
        products = payload.get("products", [])
        root_cause = artifact.get("root_cause", "")
        expected = artifact.get("expected_behavior", "")
        actual = artifact.get("actual_behavior", "")

        return (
            f"Domain: chemistry\n"
            f"Equation: {equation}\n"
            f"Reactants: {reactants}\n"
            f"Products: {products}\n"
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
        """Validate chemistry fix deterministically against expected equation if provided."""
        submitted_eq = (
            submitted_fix.get("equation")
            or submitted_fix.get("corrected_equation")
            or ""
        )
        expected = artifact.get("expected_behavior", "")

        if not submitted_eq:
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback="Requires semantic evaluation.",
                details={"deterministic": False, "requires_llm_judgment": True},
            )

        # Normalize whitespace and arrows
        norm_sub = re.sub(r"\s+", "", submitted_eq.replace("-->", "->").replace("→", "->"))
        norm_exp = re.sub(r"\s+", "", expected.replace("-->", "->").replace("→", "->"))

        if norm_sub and norm_sub in norm_exp or (norm_exp and norm_exp in norm_sub):
            return FixResult(
                is_correct=True,
                correctness_score=1.0,
                understanding_score=0.0,
                feedback="Exact stoichiometric match with expected balanced reaction.",
                details={"deterministic": True, "exact_match": True},
            )

        return FixResult(
            is_correct=False,
            correctness_score=0.0,
            understanding_score=0.0,
            feedback="Requires semantic evaluation.",
            details={"deterministic": False, "requires_llm_judgment": True},
        )

    def render_hint(
        self,
        artifact: dict[str, Any],
        attempt: dict[str, Any],
    ) -> str:
        return "Hint: balance atom counts on both sides while checking for conservation of mass."
