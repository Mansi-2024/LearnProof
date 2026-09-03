"""AI package — Grok client, artifact breaker, progressive hints, and AI Judge."""

from ai.breaker import generate_broken_artifact, generate_hint
from ai.grok_client import GrokClient
from ai.judge import VerificationResult, verify_submission

__all__ = [
    "GrokClient",
    "generate_broken_artifact",
    "generate_hint",
    "verify_submission",
    "VerificationResult",
]
