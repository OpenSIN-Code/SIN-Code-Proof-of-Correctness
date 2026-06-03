"""Property-based testing strategy using Hypothesis.

Generates test cases that try to break invariants and provides
counterexamples if invariants fail.

Docs: testing.py.doc.md
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


# Hypothesis budgets. Tuned to keep test time short while still
# surfacing common bugs; raise these together for stronger coverage.
_INT_MAX_EXAMPLES = 100        # per property
_FLOAT_MAX_EXAMPLES = 50       # smaller — float comparisons are slower
_INPUT_MIN = -1000
_INPUT_MAX = 1000

# Suppress `too_slow` because user code under test may legitimately
# be slow per-iteration (e.g. recursive functions).
_HEALTH_OVERRIDES = [HealthCheck.too_slow]


class TestingStrategy(Strategy):
    """Property-based testing strategy using Hypothesis.

    Generates test cases that try to break invariants and provides
    counterexamples if invariants fail.

    Per property: run an integer pass (deterministic, fast), then a
    float pass (catches numeric edge cases the integer pass misses).
    A failure on the integer pass is preferred over a float failure.
    """

    name = "testing"

    def generate(
        self, function_code: str, properties: list[str]
    ) -> list[ProofStep]:
        """Run the strategy: compile → check each property via Hypothesis.

        Returns a list of `ProofStep` records. The first step is the
        compile check; per-property steps follow.
        """
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
        """Run a property check via Hypothesis.

        Returns PASSED, FAILED, UNKNOWN, or SKIPPED:
        - SKIPPED: property has no runtime checker.
        - FAILED: a counterexample was found.
        - UNKNOWN: Hypothesis itself raised (e.g. function too slow).
        """
        if prop not in checkers:
            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.SKIPPED,
                details="No runtime checker available",
                strategy=self.name,
            )

        checker = checkers[prop]
        try:
            # Arity dispatch. `-1` (any) falls back to unary; multi-arg
            # properties >2 are not currently supported by this strategy.
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
        """Run a unary property check with Hypothesis.

        Performs an integer pass and a float pass. The integer pass
        runs first because it is faster and often more diagnostic;
        float pass failures are only kept if the integer pass was clean.
        """
        examples = []
        counterexample = None

        @settings(max_examples=_INT_MAX_EXAMPLES, suppress_health_check=_HEALTH_OVERRIDES)
        @given(st.integers(min_value=_INPUT_MIN, max_value=_INPUT_MAX))
        def test_int(x):
            examples.append(x)
            if not check(fn, x):
                note(f"Counterexample: {x}")
                raise AssertionError(f"Counterexample: {x}")

        try:
            test_int()
        except AssertionError as exc:
            counterexample = str(exc)

        # Also test with floats. `allow_nan=False` + `allow_infinity=False`
        # prevents NaN/Inf from breaking comparison-based properties
        # (`nan != nan` would make every pure/deterministic check fail).
        @settings(max_examples=_FLOAT_MAX_EXAMPLES, suppress_health_check=_HEALTH_OVERRIDES)
        @given(st.floats(allow_nan=False, allow_infinity=False, min_value=_INPUT_MIN, max_value=_INPUT_MAX))
        def test_float(x):
            examples.append(x)
            if not check(fn, x):
                note(f"Counterexample: {x}")
                raise AssertionError(f"Counterexample: {x}")

        try:
            test_float()
        except AssertionError as exc:
            # Integer pass already produced a counterexample — keep it.
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
        """Run a binary property check with Hypothesis.

        Uses an integer-pair strategy only — float-pair testing is
        expensive and rarely catches bugs that the integer pair
        strategy misses for the properties we currently support
        (commutative in particular).
        """
        examples = []
        counterexample = None

        @settings(max_examples=_INT_MAX_EXAMPLES, suppress_health_check=_HEALTH_OVERRIDES)
        @given(
            st.integers(min_value=_INPUT_MIN, max_value=_INPUT_MAX),
            st.integers(min_value=_INPUT_MIN, max_value=_INPUT_MAX),
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
