"""Abstract base class for all domain handlers.

Every domain (code, physics, story, business_model, chemistry) must subclass
``DomainHandler`` and implement the three abstract methods below.  Callers
should never import domain-specific handlers directly; instead use the
``DOMAIN_REGISTRY`` dict to look up a handler by slug::

    from domains import DOMAIN_REGISTRY

    handler = DOMAIN_REGISTRY["physics"]

This keeps domain-specific logic isolated and makes adding new domains trivial:
create a new subpackage, implement ``DomainHandler``, and register the handler.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ── Data transfer objects ────────────────────────────────────────────────────


@dataclass
class FixResult:
    """Returned by ``DomainHandler.validate_fix()``."""

    is_correct: bool
    correctness_score: float  # 0.0 – 1.0
    understanding_score: float  # 0.0 – 1.0
    feedback: str
    details: dict[str, Any] = field(default_factory=dict)


# ── Abstract base ────────────────────────────────────────────────────────────


class DomainHandler(ABC):
    """Common interface that every domain module must implement.

    Parameters
    ----------
    artifact:
        A dict representation of an ``artifacts`` row (including its
        ``artifact_payload`` JSONB field).
    attempt:
        A dict representation of an ``attempts`` row.
    """

    # Slug must match the ``domains.name`` column in the DB.
    domain_slug: str

    @abstractmethod
    def generate_prompt_context(self, artifact: dict[str, Any]) -> str:
        """Return a domain-specific string to inject into the LLM prompt.

        The context should describe the artifact's broken state in terms that
        make sense for the domain, so the AI can give relevant hints/feedback.

        Example for ``code``: include the language, the broken snippet, and
        the expected vs. actual output.
        """

    @abstractmethod
    def validate_fix(
        self,
        artifact: dict[str, Any],
        submitted_fix: dict[str, Any],
        submitted_explanation: str,
    ) -> FixResult:
        """Validate a user's submitted fix against the artifact.

        Returns a ``FixResult`` with correctness + understanding scores and
        human-readable feedback.  This method may call ``GrokClient`` for
        AI-assisted grading, or use deterministic checks — the caller does
        not care which.
        """

    @abstractmethod
    def render_hint(
        self,
        artifact: dict[str, Any],
        attempt: dict[str, Any],
    ) -> str:
        """Generate a progressive hint string for the current attempt.

        The hint should be informative but not give the answer away entirely.
        """


# ── Registry ─────────────────────────────────────────────────────────────────
# Populated at the bottom of this file after all handlers are imported.
# New domains: add one line here.

def _build_registry() -> dict[str, DomainHandler]:
    from domains.code.handler import CodeHandler
    from domains.physics.handler import PhysicsHandler
    from domains.story.handler import StoryHandler
    from domains.business_model.handler import BusinessModelHandler
    from domains.chemistry.handler import ChemistryHandler

    handlers: list[DomainHandler] = [
        CodeHandler(),
        PhysicsHandler(),
        StoryHandler(),
        BusinessModelHandler(),
        ChemistryHandler(),
    ]
    return {h.domain_slug: h for h in handlers}


DOMAIN_REGISTRY: dict[str, DomainHandler] = _build_registry()
