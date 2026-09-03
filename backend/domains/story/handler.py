"""Story domain handler.

Handles artifacts where the broken element is a narrative — a story excerpt
with a logical inconsistency, a plot hole, a character motivation error, or
a structural flaw.

Expected ``artifact_payload`` shape:

    {
        "genre": "mystery",             # story genre
        "broken_excerpt": "...",        # the flawed passage
        "characters": ["Alice", "Bob"], # optional cast
        "flaw_type": "plot_hole"        # optional classification
    }
"""

from __future__ import annotations

from typing import Any

from domains.base import DomainHandler, FixResult


class StoryHandler(DomainHandler):
    domain_slug = "story"

    def generate_prompt_context(self, artifact: dict[str, Any]) -> str:
        payload = artifact.get("artifact_payload", {})
        text = payload.get("text") or payload.get("broken_excerpt", "")
        inconsistency_type = payload.get("inconsistency_type") or payload.get("flaw_type", "narrative flaw")
        root_cause = artifact.get("root_cause", "")
        expected = artifact.get("expected_behavior", "")
        actual = artifact.get("actual_behavior", "")

        return (
            f"Domain: story (inconsistency_type: {inconsistency_type})\n"
            f"Broken narrative:\n{text}\n"
            f"Root cause: {root_cause}\n"
            f"Expected coherence: {expected}\n"
            f"Actual problem: {actual}"
        )

    def validate_fix(
        self,
        artifact: dict[str, Any],
        submitted_fix: dict[str, Any],
        submitted_explanation: str,
    ) -> FixResult:
        """Validate story fix.

        Accepts submitted_fix with keys: ``text``, ``revised_text``, or ``inconsistency_type``.
        Checks whether text has been revised and delegates semantic grading to Grok.
        """
        payload = artifact.get("artifact_payload", {})
        original_text = payload.get("text") or payload.get("broken_excerpt", "")
        revised_text = (
            submitted_fix.get("text")
            or submitted_fix.get("revised_text")
            or submitted_fix.get("revised_excerpt")
            or ""
        )

        if not revised_text.strip() and not submitted_explanation.strip():
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback="No revised story text or explanation was submitted.",
                details={"deterministic": True, "error": "empty_submission"},
            )

        # If identical to original broken text with no change
        if revised_text.strip() == original_text.strip() and original_text.strip():
            return FixResult(
                is_correct=False,
                correctness_score=0.1,
                understanding_score=0.0,
                feedback="The narrative text was submitted without any revisions.",
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
        flaw_type = payload.get("flaw_type", "narrative flaw")
        return f"Hint: focus on resolving the {flaw_type}. Consider cause and effect within the excerpt."
