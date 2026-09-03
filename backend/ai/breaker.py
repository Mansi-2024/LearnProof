"""Generalized multi-domain artifact breaking and hint generation engine.

Provides:
- ``generate_broken_artifact(domain, target_concept, difficulty)``:
    Generates a calibrated broken artifact across any of the 5 domains
    (code, physics, story, business_model, chemistry) backed by Grok.
- ``generate_hint(artifact, hint_level)``:
    Generates progressive, non-leaking pedagogical hints (levels 1, 2, 3).
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import re
from typing import Any
from uuid import UUID

from ai.grok_client import GrokClient

logger = logging.getLogger(__name__)

SUPPORTED_DOMAINS = ("code", "physics", "story", "business_model", "chemistry")


# ── JSON extraction & repair utilities ────────────────────────────────────────


def extract_json(raw_text: str) -> dict[str, Any]:
    """Extract and parse a JSON object from raw LLM text.

    Handles markdown fences (```json ... ```), raw strings, and trailing text.
    """
    cleaned = raw_text.strip()

    # 1. Strip markdown code fences if present
    if "```" in cleaned:
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    # 2. Try direct JSON parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 3. Fallback: Find outermost '{' and '}'
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse extracted JSON substring: {exc}") from exc

    raise ValueError(f"Could not extract valid JSON object from model output:\n{raw_text[:200]}...")


def validate_artifact_structure(data: dict[str, Any], domain: str) -> dict[str, Any]:
    """Ensure the parsed artifact dictionary matches the required top-level and payload keys."""
    required_top = {"artifact_payload", "root_cause", "expected_behavior", "actual_behavior"}
    missing = required_top - set(data.keys())
    if missing:
        raise ValueError(f"Artifact output is missing required top-level keys: {missing}")

    payload = data.get("artifact_payload")
    if not isinstance(payload, dict):
        raise ValueError(f"'artifact_payload' must be a JSON object, got {type(payload)}")

    # Domain specific payload key verification
    domain_rules: dict[str, set[str]] = {
        "code": {"language", "code"},
        "physics": {"sim_type", "constants", "correct_constants"},
        "story": {"text", "inconsistency_type"},
        "business_model": {"model_description", "flawed_assumption"},
        "chemistry": {"equation", "reactants", "products"},
    }

    expected_payload_keys = domain_rules.get(domain, set())
    missing_payload = expected_payload_keys - set(payload.keys())
    if missing_payload:
        raise ValueError(
            f"Domain '{domain}' payload is missing expected keys: {missing_payload}"
        )

    return data


# ── Domain Prompt Loader ─────────────────────────────────────────────────────


def get_domain_prompt_module(domain: str) -> Any:
    """Dynamically import and return the prompt module for a domain."""
    slug = domain.lower().strip()
    if slug not in SUPPORTED_DOMAINS:
        raise ValueError(
            f"Unsupported domain '{domain}'. Supported domains: {list(SUPPORTED_DOMAINS)}"
        )
    module_path = f"domains.{slug}.prompts"
    try:
        return importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(f"Could not load domain prompt module '{module_path}': {exc}") from exc


# ── Core Artifact Generation ──────────────────────────────────────────────────


async def generate_broken_artifact(
    domain: str,
    target_concept: str,
    difficulty: float = 0.5,
    *,
    grok_client: GrokClient | None = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Generate a domain-specific broken artifact targeting a learning concept.

    Args:
        domain: One of ('code', 'physics', 'story', 'business_model', 'chemistry').
        target_concept: The specific misconception or skill to target (e.g. 'recursion-base-case').
        difficulty: Difficulty value in range [0.0, 1.0].
        grok_client: Optional GrokClient instance (creates one if not provided).
        max_retries: Number of attempts with backoff / fallback prompts.

    Returns:
        A dict matching:
        {
          "artifact_payload": <domain-specific dict>,
          "root_cause": str,
          "expected_behavior": str,
          "actual_behavior": str
        }
    """
    # Clamp difficulty to [0.0, 1.0]
    difficulty = float(min(max(difficulty, 0.0), 1.0))
    prompt_mod = get_domain_prompt_module(domain)
    client = grok_client or GrokClient()

    system_prompt = prompt_mod.SYSTEM_PROMPT
    user_prompt = prompt_mod.build_generation_prompt(target_concept, difficulty)

    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        # On last retry attempt, switch to simpler fallback prompt
        active_user_prompt = (
            prompt_mod.build_fallback_prompt(target_concept, difficulty)
            if attempt == max_retries
            else user_prompt
        )

        try:
            response = await client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": active_user_prompt},
                ],
                temperature=0.7 if attempt == 1 else 0.4,
                response_format={"type": "json_object"},
            )

            raw_text = response["choices"][0]["message"]["content"]
            parsed = extract_json(raw_text)
            validated = validate_artifact_structure(parsed, domain)
            return validated

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Attempt %d/%d failed generating artifact for domain '%s', concept '%s': %s",
                attempt,
                max_retries,
                domain,
                target_concept,
                exc,
            )
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

    raise RuntimeError(
        f"Failed to generate valid broken artifact for domain '{domain}' after {max_retries} attempts. Last error: {last_error}"
    ) from last_error


# ── Progressive Hint Generation ───────────────────────────────────────────────


def build_hint_instruction(hint_level: int) -> str:
    """Return pedagogical instructions based on hint level (1, 2, or 3)."""
    if hint_level <= 1:
        return (
            "HINT LEVEL 1 (Subtle Socratic Nudge):\n"
            "- Ask an insightful question or point the student to look at a high-level area.\n"
            "- Do NOT mention the error type or specific variables/lines.\n"
            "- Help the student observe the mismatch between expected and actual behavior."
        )
    elif hint_level == 2:
        return (
            "HINT LEVEL 2 (Conceptual Rule / Invariant Clue):\n"
            "- State the underlying principle, law, or logic rule that might be violated.\n"
            "- Guide the student on what invariant or assumption they should test.\n"
            "- Do NOT state the root cause or give away the exact location."
        )
    else:
        return (
            "HINT LEVEL 3 (Diagnostic Focus):\n"
            "- Pinpoint the specific component, step, equation, or section where the flaw resides.\n"
            "- Explain what mechanism is behaving unexpectedly in that specific part.\n"
            "- Do NOT provide the ready-made solution code/text or quote the root cause verbatim."
        )


async def generate_hint(
    artifact: str | UUID | dict[str, Any],
    hint_level: int = 1,
    *,
    grok_client: GrokClient | None = None,
    max_retries: int = 3,
) -> str:
    """Generate a progressive, non-leaking hint for a broken artifact.

    Args:
        artifact: Artifact row dict (including 'artifact_payload', 'root_cause',
                  'expected_behavior', 'actual_behavior') or artifact_id string.
        hint_level: 1 (Socratic nudge), 2 (Conceptual clue), 3 (Diagnostic focus).
        grok_client: Optional GrokClient instance.
        max_retries: Retries for Grok call.

    Returns:
        Hint text string tailored to the given hint level.
    """
    hint_level = max(1, min(int(hint_level), 3))
    client = grok_client or GrokClient()

    # If artifact is an ID / UUID, fetch it from Supabase
    artifact_data: dict[str, Any]
    if isinstance(artifact, (str, UUID)):
        from db.supabase_client import get_supabase
        db = get_supabase()
        res = db.table("artifacts").select("*").eq("id", str(artifact)).maybe_single().execute()
        if not res.data:
            raise ValueError(f"Artifact '{artifact}' not found in database.")
        artifact_data = res.data
    elif isinstance(artifact, dict):
        artifact_data = artifact
    else:
        raise TypeError(f"Expected artifact dict or ID, got {type(artifact)}")

    payload = artifact_data.get("artifact_payload", {})
    root_cause = artifact_data.get("root_cause", "Unspecified root cause")
    expected = artifact_data.get("expected_behavior", "Unspecified expected behavior")
    actual = artifact_data.get("actual_behavior", "Unspecified actual behavior")

    level_guide = build_hint_instruction(hint_level)

    system_prompt = (
        "You are an expert tutor guiding a student through a debugging / repair challenge.\n"
        "Your mission is to provide helpful hints without ever revealing the root cause or the final solution.\n"
        "Be concise, engaging, and pedagogically effective."
    )

    user_prompt = f"""Generate a Level {hint_level} hint for the following broken artifact.

ARTIFACT CONTEXT:
- Expected Behavior: {expected}
- Actual Behavior: {actual}
- Payload: {json.dumps(payload, indent=2)}

INTERNAL ROOT CAUSE (FOR YOUR CONTEXT ONLY - DO NOT LEAK OR QUOTE DIRECTLY):
{root_cause}

HINT SPECIFICATION:
{level_guide}

CRITICAL RULES:
1. Provide ONLY the hint message for the student.
2. Under no circumstances quote or state the root cause text directly.
3. Keep the hint between 1 and 3 sentences.
"""

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.complete(
                prompt=user_prompt,
                temperature=0.7,
            )
            hint_text = response.strip()
            # Basic sanity check
            if hint_text:
                return hint_text
        except Exception as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed generating hint: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

    # Fallback template hint if AI call completely failed
    return f"Hint (Level {hint_level}): Review the difference between expected behavior ('{expected[:60]}...') and actual behavior ('{actual[:60]}...')."
