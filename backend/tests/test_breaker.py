"""Unit tests for the AI artifact breaking and progressive hint generation engine."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.breaker import (
    SUPPORTED_DOMAINS,
    build_hint_instruction,
    extract_json,
    generate_broken_artifact,
    generate_hint,
    get_domain_prompt_module,
    validate_artifact_structure,
)
from ai.grok_client import GrokClient


# ── Test JSON extraction and validation ──────────────────────────────────────


class TestJsonExtractionAndValidation:
    def test_extract_clean_json(self) -> None:
        raw = '{"artifact_payload": {"code": "x = 1"}, "root_cause": "test"}'
        parsed = extract_json(raw)
        assert parsed["artifact_payload"]["code"] == "x = 1"
        assert parsed["root_cause"] == "test"

    def test_extract_markdown_fenced_json(self) -> None:
        raw = """```json
{
  "artifact_payload": {
    "language": "python",
    "code": "def f(): return 1"
  },
  "root_cause": "none",
  "expected_behavior": "1",
  "actual_behavior": "1"
}
```"""
        parsed = extract_json(raw)
        assert parsed["artifact_payload"]["language"] == "python"

    def test_extract_json_with_surrounding_commentary(self) -> None:
        raw = """Here is your generated artifact:
{
  "artifact_payload": {
    "text": "It was night.",
    "inconsistency_type": "timeline"
  },
  "root_cause": "wrong time",
  "expected_behavior": "day",
  "actual_behavior": "night"
}
Hope this helps!"""
        parsed = extract_json(raw)
        assert parsed["artifact_payload"]["text"] == "It was night."

    def test_extract_invalid_json_raises(self) -> None:
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json("This has no json object at all.")

    def test_validate_artifact_structure_missing_top_level(self) -> None:
        data = {"artifact_payload": {}, "root_cause": "test"}
        with pytest.raises(ValueError, match="missing required top-level keys"):
            validate_artifact_structure(data, "code")

    def test_validate_artifact_structure_missing_domain_payload(self) -> None:
        data = {
            "artifact_payload": {"language": "python"},  # missing "code"
            "root_cause": "bug",
            "expected_behavior": "work",
            "actual_behavior": "fail",
        }
        with pytest.raises(ValueError, match="missing expected keys"):
            validate_artifact_structure(data, "code")


# ── Test Domain Prompt Modules ───────────────────────────────────────────────


class TestDomainPromptModules:
    @pytest.mark.parametrize("domain", SUPPORTED_DOMAINS)
    def test_domain_prompt_module_loaded(self, domain: str) -> None:
        mod = get_domain_prompt_module(domain)
        assert hasattr(mod, "SYSTEM_PROMPT")
        assert hasattr(mod, "build_generation_prompt")
        assert hasattr(mod, "build_difficulty_instruction")
        assert hasattr(mod, "build_fallback_prompt")

    def test_unsupported_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported domain"):
            get_domain_prompt_module("unknown_domain")

    @pytest.mark.parametrize("difficulty", [0.1, 0.5, 0.9])
    def test_difficulty_instructions_per_domain(self, difficulty: float) -> None:
        for domain in SUPPORTED_DOMAINS:
            mod = get_domain_prompt_module(domain)
            prompt = mod.build_generation_prompt("sample_concept", difficulty)
            assert "sample_concept" in prompt
            assert "DIFFICULTY LEVEL" in prompt


# ── Test Artifact Generation across 5 Domains (Mocked Grok) ──────────────────


class TestGenerateBrokenArtifact:
    @pytest.mark.asyncio
    async def test_generate_code_artifact(self) -> None:
        mock_payload = {
            "artifact_payload": {
                "language": "python",
                "code": "def fib(n):\n    return fib(n-1) + fib(n-2)",
                "test_cases": [
                    {"input": "n=1", "expected_output": "1", "actual_output": "RecursionError"}
                ],
            },
            "root_cause": "Missing base case condition for n <= 1",
            "expected_behavior": "Return the nth Fibonacci number",
            "actual_behavior": "Infinite recursion leading to RecursionError",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={"choices": [{"message": {"content": json.dumps(mock_payload)}}]}
        )

        artifact = await generate_broken_artifact(
            domain="code",
            target_concept="recursion-base-case",
            difficulty=0.2,
            grok_client=mock_client,
        )

        assert artifact["artifact_payload"]["language"] == "python"
        assert "def fib" in artifact["artifact_payload"]["code"]
        assert "Missing base case" in artifact["root_cause"]
        assert mock_client.chat.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_physics_artifact(self) -> None:
        mock_payload = {
            "artifact_payload": {
                "sim_type": "projectile_motion",
                "constants": {"gravity": "-9.8 m/s^2", "initial_velocity": "20 m/s"},
                "correct_constants": {"gravity": "9.8 m/s^2 (downward)"},
            },
            "root_cause": "Double negative sign in upward acceleration equation",
            "expected_behavior": "Parabolic arc with downward deceleration",
            "actual_behavior": "Object accelerates upward without bound",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={"choices": [{"message": {"content": json.dumps(mock_payload)}}]}
        )

        artifact = await generate_broken_artifact(
            domain="physics",
            target_concept="projectile-acceleration-sign",
            difficulty=0.3,
            grok_client=mock_client,
        )

        assert artifact["artifact_payload"]["sim_type"] == "projectile_motion"
        assert "gravity" in artifact["artifact_payload"]["constants"]

    @pytest.mark.asyncio
    async def test_generate_story_artifact(self) -> None:
        mock_payload = {
            "artifact_payload": {
                "text": "Elena locked the only door from the hallway and pocketed the key. A moment later, Marcus walked in through that same door without unlocking it.",
                "inconsistency_type": "spatial_continuity_error",
            },
            "root_cause": "Marcus enters through a locked door without possessing a key or picking the lock",
            "expected_behavior": "Marcus knocks or unlocks the door before entering",
            "actual_behavior": "Marcus walks through a locked locked door",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={"choices": [{"message": {"content": json.dumps(mock_payload)}}]}
        )

        artifact = await generate_broken_artifact(
            domain="story",
            target_concept="locked-room-continuity",
            difficulty=0.4,
            grok_client=mock_client,
        )

        assert artifact["artifact_payload"]["inconsistency_type"] == "spatial_continuity_error"
        assert "Elena locked" in artifact["artifact_payload"]["text"]

    @pytest.mark.asyncio
    async def test_generate_business_model_artifact(self) -> None:
        mock_payload = {
            "artifact_payload": {
                "model_description": "On-demand dog walking app charging $15/walk while paying walkers $18/walk plus $5 fuel subsidy.",
                "flawed_assumption": "Negative unit contribution margin cannot be overcome by customer volume.",
            },
            "root_cause": "Variable delivery cost exceeds gross revenue per transaction",
            "expected_behavior": "Positive unit margin where price exceeds walker compensation + CAC amortisation",
            "actual_behavior": "Each incremental transaction burns $8 of operating cash",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={"choices": [{"message": {"content": json.dumps(mock_payload)}}]}
        )

        artifact = await generate_broken_artifact(
            domain="business_model",
            target_concept="unit-economics-contribution-margin",
            difficulty=0.1,
            grok_client=mock_client,
        )

        assert "flawed_assumption" in artifact["artifact_payload"]
        assert "Negative unit contribution" in artifact["artifact_payload"]["flawed_assumption"]

    @pytest.mark.asyncio
    async def test_generate_chemistry_artifact(self) -> None:
        mock_payload = {
            "artifact_payload": {
                "equation": "H2 + O2 -> H2O",
                "reactants": ["H2", "O2"],
                "products": ["H2O"],
            },
            "root_cause": "Oxygen atoms are unbalanced (2 on reactant side, 1 on product side)",
            "expected_behavior": "2H2 + O2 -> 2H2O",
            "actual_behavior": "One oxygen atom disappears during the reaction",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={"choices": [{"message": {"content": json.dumps(mock_payload)}}]}
        )

        artifact = await generate_broken_artifact(
            domain="chemistry",
            target_concept="stoichiometry-oxygen-balance",
            difficulty=0.2,
            grok_client=mock_client,
        )

        assert artifact["artifact_payload"]["equation"] == "H2 + O2 -> H2O"
        assert artifact["artifact_payload"]["reactants"] == ["H2", "O2"]

    @pytest.mark.asyncio
    async def test_retry_on_malformed_json_and_recover(self) -> None:
        valid_payload = {
            "artifact_payload": {"language": "python", "code": "print('hello')"},
            "root_cause": "none",
            "expected_behavior": "hello",
            "actual_behavior": "hello",
        }

        mock_client = MagicMock(spec=GrokClient)
        # 1st call returns malformed string, 2nd call returns valid JSON
        mock_client.chat = AsyncMock(
            side_effect=[
                {"choices": [{"message": {"content": "Not JSON at all!"}}]},
                {"choices": [{"message": {"content": json.dumps(valid_payload)}}]},
            ]
        )

        artifact = await generate_broken_artifact(
            domain="code",
            target_concept="print-statement",
            difficulty=0.5,
            grok_client=mock_client,
            max_retries=3,
        )

        assert artifact["artifact_payload"]["code"] == "print('hello')"
        assert mock_client.chat.call_count == 2

    @pytest.mark.asyncio
    async def test_exhaust_retries_raises_runtime_error(self) -> None:
        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={"choices": [{"message": {"content": "Malformed response"}}]}
        )

        with pytest.raises(RuntimeError, match="Failed to generate valid broken artifact"):
            await generate_broken_artifact(
                domain="code",
                target_concept="failure-test",
                difficulty=0.5,
                grok_client=mock_client,
                max_retries=2,
            )


# ── Test Progressive Hint Generation ─────────────────────────────────────────


class TestGenerateHint:
    @pytest.mark.parametrize("level", [1, 2, 3])
    def test_hint_instruction_levels(self, level: int) -> None:
        instr = build_hint_instruction(level)
        assert f"HINT LEVEL {level}" in instr

    @pytest.mark.asyncio
    async def test_generate_hint_from_dict(self) -> None:
        artifact = {
            "artifact_payload": {"code": "def f(x): return f(x-1)"},
            "root_cause": "Missing base case in recursion",
            "expected_behavior": "Terminates when x <= 0",
            "actual_behavior": "RecursionError: maximum recursion depth exceeded",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.complete = AsyncMock(
            return_value="Notice what happens when x reaches zero — does the function stop or keep calling itself?"
        )

        hint = await generate_hint(artifact, hint_level=1, grok_client=mock_client)
        assert "Notice what happens" in hint
        assert mock_client.complete.call_count == 1

        # Verify that user prompt contains expected behaviors and asks not to quote root cause
        call_prompt = mock_client.complete.call_args[1]["prompt"]
        assert "Missing base case in recursion" in call_prompt
        assert "DO NOT LEAK OR QUOTE DIRECTLY" in call_prompt

    @pytest.mark.asyncio
    async def test_generate_hint_fallback_on_network_failure(self) -> None:
        artifact = {
            "artifact_payload": {"code": "x = 1"},
            "root_cause": "Bug",
            "expected_behavior": "Prints 1",
            "actual_behavior": "Prints 2",
        }

        mock_client = MagicMock(spec=GrokClient)
        mock_client.complete = AsyncMock(side_effect=Exception("API connection timeout"))

        hint = await generate_hint(artifact, hint_level=2, grok_client=mock_client, max_retries=1)
        assert "Hint (Level 2)" in hint
        assert "Review the difference between expected behavior" in hint
