"""Domain handlers package.

Exports:
    DomainHandler  — abstract base class all domain modules implement
    FixResult      — dataclass returned by validate_fix()
    DOMAIN_REGISTRY — slug → handler instance dict

Usage::

    from domains import DOMAIN_REGISTRY

    handler = DOMAIN_REGISTRY["code"]
    ctx = handler.generate_prompt_context(artifact)
"""

from domains.base import DOMAIN_REGISTRY, DomainHandler, FixResult

__all__ = ["DomainHandler", "FixResult", "DOMAIN_REGISTRY"]
