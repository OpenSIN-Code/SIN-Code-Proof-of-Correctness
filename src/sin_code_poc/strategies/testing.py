"""Property-based testing strategy using Hypothesis.

Generates test cases that try to break invariants and provides
counterexamples if invariants fail.
"""
from __future__ import annotations

import ast
import math
from typing import Any, Callable

from hypothesis import given, settings, HealthCheck, note
from hypothesis import strategies as st
from hypothesis.errors import HypothesisException

from sin_code_poc.proof import ProofStep, Verdict
from sin_code_poc.strategies import Strategy
from sin_code_poc.properties import runtime_checkers


class TestingStrategy(Strategy):
    """Property-based testing strategy using Hypothesis.

    Generates test cases that try to break invariants and provides
    counterexamples if invariants fail.
    """

    name = "testing"

    def generate(
        self, function_code: str, properties: list[str]
    ) -> list[ProofStep]:
        steps: list[ProofStep] = []
        sig = self._build_signature(function_code)

        try:
            fn = self._compile_function(function_code)
        except Exception as exc:
            steps.append(
                ProofStep(
                    description="Compile function",
                    verdict=Verdict.FAILED,
                    details=f"Compilation error: {exc}",
                    strategy=self.name,
                )
            )
            return steps

        steps.append(
            ProofStep(
                description="Compile function",
                verdict=Verdict.PASSED,
                details=f"Compiled {sig}",
                strategy=self.name,
            )
        )

        checkers = runtime_checkers()
        for prop in properties:
            step = self._check_property(prop, fn, checkers)
            steps.append(step)

        return steps

    def _check_property(
        self,
        prop: str,
        fn: Callable[..., Any],
        checkers: dict[str, Any],
    ) -> ProofStep:
        """Run a property check via Hypothesis."""
        if prop not in checkers:
            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.SKIPPED,
                details="No runtime checker available",
                strategy=self.name,
            )

        checker = checkers[prop]
        try:
            if checker.arity == 1:
                result = self._run_unary(fn, checker.check)
            elif checker.arity == 2:
                result = self._run_binary(fn, checker.check)
            else:
                result = self._run_unary(fn, checker.check)

            if result["passed"]:
                return ProofStep(
                    description=f"Check {prop}",
                    verdict=Verdict.PASSED,
                    details=f"Hypothesis tested {result['examples']} examples",
                    strategy=self.name,
                )
            else:
                return ProofStep(
                    description=f"Check {prop}",
                    verdict=Verdict.FAILED,
                    details=f"Counterexample found: {result['counterexample']}",
                    strategy=self.name,
                )
        except HypothesisException as exc:
            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.UNKNOWN,
                details=f"Hypothesis error: {exc}",
                strategy=self.name,
            )
        except Exception as exc:
            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.UNKNOWN,
                details=f"Testing error: {exc}",
                strategy=self.name,
            )

    def _run_unary(
        self, fn: Callable[..., Any], check: Callable[[Any, Any], bool]
    ) -> dict[str, Any]:
        """Run a unary property check with Hypothesis."""
        examples = []
        counterexample = None

        @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
        @given(st.integers(min_value=-1000, max_value=1000))
        def test_int(x):
            examples.append(x)
            if not check(fn, x):
                note(f"Counterexample: {x}")
                raise AssertionError(f"Counterexample: {x}")

        try:
            test_int()
        except AssertionError as exc:
            counterexample = str(exc)

        # Also test with floats
        @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
        @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000))
        def test_float(x):
            examples.append(x)
            if not check(fn, x):
                note(f"Counterexample: {x}")
                raise AssertionError(f"Counterexample: {x}")

        try:
            test_float()
        except AssertionError as exc:
            if counterexample is None:
                counterexample = str(exc)

        return {
            "passed": counterexample is None,
            "examples": len(examples),
            "counterexample": counterexample,
        }

    def _run_binary(
        self, fn: Callable[..., Any], check: Callable[[Any, Any], bool]
    ) -> dict[str, Any]:
        """Run a binary property check with Hypothesis."""
        examples = []
        counterexample = None

        @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
        @given(
            st.integers(min_value=-1000, max_value=1000),
            st.integers(min_value=-1000, max_value=1000),
        )
        def test_int(a, b):
            examples.append((a, b))
            if not check(fn, (a, b)):
                raise AssertionError(f"Counterexample: ({a}, {b})")

        try:
            test_int()
        except AssertionError as exc:
            counterexample = str(exc)

        return {
            "passed": counterexample is None,
            "examples": len(examples),
            "counterexample": counterexample,
        }
