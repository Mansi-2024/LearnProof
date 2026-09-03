"""Code domain handler with deterministic test-case validation and AST checking."""

from __future__ import annotations

import re
from typing import Any

from domains.base import DomainHandler, FixResult


class CodeHandler(DomainHandler):
    domain_slug = "code"

    def generate_prompt_context(self, artifact: dict[str, Any]) -> str:
        payload = artifact.get("artifact_payload", {})
        language = payload.get("language", "python")
        code = payload.get("code", "")
        test_cases = payload.get("test_cases", [])
        root_cause = artifact.get("root_cause", "")
        expected = artifact.get("expected_behavior", "")
        actual = artifact.get("actual_behavior", "")

        return (
            f"Domain: code ({language})\n"
            f"Code:\n```{language}\n{code}\n```\n"
            f"Test Cases: {test_cases}\n"
            f"Root cause: {root_cause}\n"
            f"Expected behaviour: {expected}\n"
            f"Actual behaviour: {actual}"
        )

    def validate_fix(
        self,
        artifact: dict[str, Any],
        submitted_fix: dict[str, Any],
        submitted_explanation: str,
    ) -> FixResult:
        """Validate code fix deterministically if test cases are provided."""
        submitted_code = submitted_fix.get("code") or submitted_fix.get("fixed_code") or ""
        payload = artifact.get("artifact_payload", {})
        language = payload.get("language", "python").lower()

        if not submitted_code.strip():
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback="No code was submitted in the fix.",
                details={"deterministic": True, "error": "empty_submission"},
            )

        # Basic Python syntax validation
        if language == "python":
            try:
                compile(submitted_code, "<submitted_code>", "exec")
            except SyntaxError as e:
                return FixResult(
                    is_correct=False,
                    correctness_score=0.0,
                    understanding_score=0.0,
                    feedback=f"Syntax Error in submitted code: {e.msg} at line {e.lineno}",
                    details={"deterministic": True, "syntax_error": str(e)},
                )

        # If language is Python and test cases can be checked
        test_cases = payload.get("test_cases", [])
        if not test_cases:
            # Fall back to Grok evaluation
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback="Requires semantic evaluation.",
                details={"deterministic": False, "requires_llm_judgment": True},
            )

        # Run safe evaluation of python function with test cases
        try:
            # Safe globals limiting dangerous builtins but containing defined functions
            safe_globals: dict[str, Any] = {
                "__builtins__": {
                    "range": range,
                    "len": len,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "abs": abs,
                    "int": int,
                    "float": float,
                    "str": str,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "bool": bool,
                    "print": lambda *args: None,
                    "RecursionError": RecursionError,
                }
            }
            exec(submitted_code, safe_globals)
        except Exception as exc:
            return FixResult(
                is_correct=False,
                correctness_score=0.0,
                understanding_score=0.0,
                feedback=f"Runtime error executing code: {exc}",
                details={"deterministic": True, "error": str(exc)},
            )

        # Find defined function name
        user_funcs = [
            k for k, v in safe_globals.items()
            if callable(v) and k != "__builtins__" and k not in safe_globals["__builtins__"]
        ]
        default_func = user_funcs[0] if user_funcs else None

        passed = 0
        total = len(test_cases)
        for tc in test_cases:
            inp = tc.get("input", "").strip()
            exp = str(tc.get("expected_output", "")).strip()
            if not inp:
                continue

            try:
                # If input is raw args like "[10, 20]" and not "get_first([10, 20])", wrap with func
                eval_expr = inp
                if default_func and not any(inp.startswith(f) for f in user_funcs):
                    eval_expr = f"{default_func}({inp})"
                result = eval(eval_expr, safe_globals)
                if str(result).strip() == exp:
                    passed += 1
            except Exception:
                pass



        score = float(passed / total) if total > 0 else 0.0
        return FixResult(
            is_correct=score >= 0.8,
            correctness_score=score,
            understanding_score=0.0,
            feedback=f"Passed syntax check and {passed}/{total} test assertions.",
            details={"deterministic": True, "tests_passed": passed, "total_tests": total},
        )


    def render_hint(
        self,
        artifact: dict[str, Any],
        attempt: dict[str, Any],
    ) -> str:
        root_cause = artifact.get("root_cause", "")
        return f"Hint: check the boundary conditions and state transitions near {root_cause[:40]}."
