"""Unit and integration tests for the Grok Judge and POST /verify-fix endpoint."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ai.grok_client import GrokClient
from ai.judge import VerificationResult, verify_submission
from main import app


# ── Test verify_submission Judge Function ────────────────────────────────────


class TestVerifySubmissionJudge:
    @pytest.mark.asyncio
    async def test_deterministic_physics_pass_with_accurate_explanation(self) -> None:
        artifact = {
            "domain_slug": "physics",
            "artifact_payload": {
                "sim_type": "projectile_motion",
                "constants": {"gravity": "-9.8 m/s^2"},
                "correct_constants": {"gravity": "9.8 m/s^2"},
            },
            "root_cause": "Double negative sign in downward gravity vector",
            "expected_behavior": "Downward deceleration",
            "actual_behavior": "Upward acceleration",
        }
        submitted_fix = {"constants": {"gravity": "9.8 m/s^2"}}
        submitted_explanation = "The gravity constant had an inverted negative sign causing upward acceleration."

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "fix_correctness": 1.0,
                                    "understanding_score": 0.95,
                                    "misunderstanding_flag": False,
                                    "feedback_text": "Excellent fix and clear grasp of vector signs.",
                                }
                            )
                        }
                    }
                ]
            }
        )

        result = await verify_submission(
            artifact=artifact,
            submitted_fix=submitted_fix,
            submitted_explanation=submitted_explanation,
            grok_client=mock_client,
        )

        assert result.fix_correctness == 1.0
        assert result.understanding_score >= 0.90
        assert result.misunderstanding_flag is False

    @pytest.mark.asyncio
    async def test_lucky_guess_misconception_flagged(self) -> None:
        """Fix works (1.0), but explanation reveals a critical misconception (<0.5)."""
        artifact = {
            "domain_slug": "code",
            "artifact_payload": {
                "language": "python",
                "code": "def get_first(items):\n    return items[1]",
                "test_cases": [{"input": "[10, 20]", "expected_output": "10"}],
            },
            "root_cause": "Index 1 was accessed instead of 0 for the first element",
            "expected_behavior": "Return index 0",
            "actual_behavior": "Returns index 1",
        }
        submitted_fix = {"code": "def get_first(items):\n    return items[0]"}
        # Misconception: claiming Python lists are 1-indexed and 0 is a special memory offset
        submitted_explanation = "I changed it to 0 because 0 accesses the hidden metadata buffer in Python arrays."

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "fix_correctness": 1.0,
                                    "understanding_score": 0.15,
                                    "misunderstanding_flag": True,
                                    "feedback_text": "Your code fix passed, but your explanation contains a major misconception about Python indexing.",
                                }
                            )
                        }
                    }
                ]
            }
        )

        result = await verify_submission(
            artifact=artifact,
            submitted_fix=submitted_fix,
            submitted_explanation=submitted_explanation,
            grok_client=mock_client,
        )

        assert result.fix_correctness >= 0.8
        assert result.understanding_score < 0.5
        assert result.misunderstanding_flag is True
        assert "misconception" in result.feedback_text.lower() or "misunderstanding" in result.feedback_text.lower()

    @pytest.mark.asyncio
    async def test_semantic_story_evaluation(self) -> None:
        artifact = {
            "domain_slug": "story",
            "artifact_payload": {
                "text": "The key was melted in the forge. Later, David unlocked the door with that same key.",
                "inconsistency_type": "physical_continuity_error",
            },
            "root_cause": "Key cannot be used after being melted into liquid slag",
            "expected_behavior": "David uses a lockpick or secondary key",
            "actual_behavior": "Melted key is used intact",
        }
        submitted_fix = {
            "text": "The key was hidden in the cupboard. Later, David unlocked the door with that key."
        }
        submitted_explanation = "Prevented the key from being destroyed so David can realistically use it later."

        mock_client = MagicMock(spec=GrokClient)
        mock_client.chat = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "fix_correctness": 0.90,
                                    "understanding_score": 0.92,
                                    "misunderstanding_flag": False,
                                    "feedback_text": "Great job resolving the continuity paradox.",
                                }
                            )
                        }
                    }
                ]
            }
        )

        result = await verify_submission(
            artifact=artifact,
            submitted_fix=submitted_fix,
            submitted_explanation=submitted_explanation,
            grok_client=mock_client,
        )

        assert result.fix_correctness == 0.90
        assert result.understanding_score == 0.92
        assert result.misunderstanding_flag is False


# ── Test POST /verify-fix Endpoint ───────────────────────────────────────────


class TestVerifyFixEndpoint:
    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    @patch("api.verification.verify_submission")
    @patch("api.verification.get_supabase")
    @patch("api.verification.MasteryService")
    def test_verify_fix_endpoint_success(
        self,
        mock_mastery_cls: MagicMock,
        mock_get_supabase: MagicMock,
        mock_verify: AsyncMock,
        client: TestClient,
    ) -> None:
        from api.auth import get_current_user

        # Mock Auth override
        app.dependency_overrides[get_current_user] = lambda: {
            "sub": "user-1234",
            "email": "student@example.com",
        }

        # Mock Supabase
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
            "id": "artifact-123",
            "target_concept_id": "concept-456",
            "domains": {"name": "code"},
            "artifact_payload": {"code": "x = 1"},
            "root_cause": "Sample bug",
            "expected_behavior": "Expected",
            "actual_behavior": "Actual",
        }
        mock_db.table.return_value.insert.return_value.execute.return_value.data = [{"id": "attempt-789"}]

        # Mock Mastery Service
        mock_mastery_instance = MagicMock()
        mock_mastery_instance.update_mastery = AsyncMock(return_value={"mastery_score": 0.75})
        mock_mastery_cls.return_value = mock_mastery_instance

        # Mock Judge
        mock_verify.return_value = VerificationResult(
            fix_correctness=0.90,
            understanding_score=0.85,
            feedback_text="Great fix and explanation!",
            misunderstanding_flag=False,
        )

        response = client.post(
            "/verify-fix",
            json={
                "artifact_id": "artifact-123",
                "submitted_fix": {"code": "x = 2"},
                "submitted_explanation": "Changed x to 2 to meet requirements.",
            },
        )

        # Cleanup override
        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["fix_correctness"] == 0.90
        assert data["understanding_score"] == 0.85
        assert data["misunderstanding_flag"] is False
        assert data["feedback_text"] == "Great fix and explanation!"
        assert data["attempt_id"] == "attempt-789"
        assert data["mastery_updated"] is True

    @patch("api.verification.get_supabase")
    def test_verify_fix_endpoint_not_found(
        self,
        mock_get_supabase: MagicMock,
        client: TestClient,
    ) -> None:
        from api.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: {"sub": "user-1234"}

        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None

        response = client.post(
            "/verify-fix",
            json={
                "artifact_id": "nonexistent-id",
                "submitted_fix": {},
                "submitted_explanation": "Nothing.",
            },
        )

        app.dependency_overrides.pop(get_current_user, None)
        assert response.status_code == 404
