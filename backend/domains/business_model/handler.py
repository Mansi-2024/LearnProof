"""Business model domain handler.

Handles artifacts where the broken element is a business model component —
a flawed value proposition, broken revenue logic, misaligned customer segment,
or incorrect unit economics.

Expected ``artifact_payload`` shape:

    {
        "framework": "lean_canvas",     # e.g. lean_canvas, business_model_canvas
        "broken_section": "revenue_streams",
        "broken_content": "...",        # the flawed text/numbers
        "context": "..."                # surrounding business context
    }
"""

from __future__ import annotations

from typing import Any

from domains.base import DomainHandler, FixResult


class BusinessModelHandler(DomainHandler):
    domain_slug = "business_model"

    def generate_prompt_context(self, artifact: dict[str, Any]) -> str:
        payload = artifact.get("artifact_payload", {})
        model_desc = payload.get("model_description") or payload.get("context", "")
        flawed_assumption = payload.get("flawed_assumption") or payload.get("broken_content", "")
        root_cause = artifact.get("root_cause", "")
        expected = artifact.get("expected_behavior", "")
        actual = artifact.get("actual_behavior", "")

        return (
            f"Domain: business_model\n"
            f"Model description: {model_desc}\n"
            f"Flawed assumption: {flawed_assumption}\n"
            f"Root cause: {root_cause}\n"
            f"Expected viable model: {expected}\n"
            f"Actual structural flaw: {actual}"
        )

    def validate_fix(
        self,
        artifact: dict[str, Any],
        submitted_fix: dict[str, Any],
        submitted_explanation: str,
    ) -> FixResult:
        """Validate business model fix.

        Accepts submitted_fix with keys: ``model_description``, ``price``, ``cogs``,
        ``variable_cost``, or ``fixed_assumption``.
        """
        payload = artifact.get("artifact_payload", {})
        original_desc = payload.get("model_description", "")
        sub_desc = (
            submitted_fix.get("model_description")
            or submitted_fix.get("fixed_section")
            or submitted_fix.get("revised_model")
            or ""
        )

        if not sub_desc.strip() and not submitted_explanation.strip() and not submitted_fix:
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback="No business model fix or explanation was submitted.",
                details={"deterministic": True, "error": "empty_submission"},
            )

        if sub_desc.strip() == original_desc.strip() and original_desc.strip():
            return FixResult(
                is_correct=False,
                correctness_score=0.1,
                understanding_score=0.0,
                feedback="The business model description was submitted without any adjustments.",
                details={"deterministic": True, "unmodified": True},
            )

        # Requires semantic evaluation by Grok judge
        return FixResult(
            is_correct=False,
            correctness_score=0.0,
            understanding_score=0.0,
            feedback="Requires semantic evaluation by Grok judge.",
            details={"deterministic": False, "requires_llm_judgment": True},
        )


    def render_hint(
        self,
        artifact: dict[str, Any],
        attempt: dict[str, Any],
    ) -> str:
        payload = artifact.get("artifact_payload", {})
        section = payload.get("broken_section", "this section")
        return (
            f"Hint: re-examine how '{section}' connects to the customer segment "
            "and value proposition. Look for internal contradictions."
        )
