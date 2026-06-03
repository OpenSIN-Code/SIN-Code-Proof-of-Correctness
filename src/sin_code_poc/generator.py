"""Proof generator for SIN-Code POC.

Docs: generator.py.doc.md
"""
from __future__ import annotations

from typing import Any

from sin_code_poc.proof import Proof, ProofStep, Verdict
from sin_code_poc.properties import parse_property_spec
from sin_code_poc.strategies import StrategyRegistry, get_strategy, available_strategies
from sin_code_poc.strategies.symbolic import SymbolicStrategy
from sin_code_poc.strategies.testing import TestingStrategy
from sin_code_poc.strategies.typecheck import TypecheckStrategy
from sin_code_poc.verifier import Verifier


# Valid strategy names. Centralized so both the constructor and `_auto_generate`
# can validate without duplicating string literals.
_VALID_STRATEGIES = ("auto", "symbolic", "testing", "typecheck")

# Fallback order for `auto` mode. Symbolic first because it gives the strongest
# guarantees when it works; testing as the catch-all for non-arithmetic code.
_AUTO_FALLBACK_ORDER = ("symbolic", "testing")


# Register strategies at import time so a single import gives a usable registry.
_registry = StrategyRegistry()
_registry.register(SymbolicStrategy())
_registry.register(TestingStrategy())
_registry.register(TypecheckStrategy())


def _get_strategy(name: str) -> Any:
    """Look up a strategy by name (delegates to the module-level registry)."""
    return _registry.get(name)


def _available_strategies() -> list[str]:
    """List the names of all currently registered strategies."""
    return _registry.available()


class ProofGenerator:
    """Generate proofs of correctness for Python functions.

    Uses one of several strategies (`symbolic`, `testing`, `typecheck`) or
    auto-selects the best strategy based on the function. In `auto` mode
    the generator tries symbolic first, then falls back to testing.
    """

    def __init__(self, strategy: str = "auto"):
        """Initialize with a strategy.

        Args:
            strategy: One of `"auto"`, `"symbolic"`, `"testing"`, `"typecheck"`.

        Raises:
            ValueError: If `strategy` is not one of the allowed names.
        """
        if strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy!r}. Choose from: {', '.join(_VALID_STRATEGIES)}"
            )
        self.strategy = strategy

    def generate(self, function_code: str, properties: str = "") -> Proof:
        """Generate a proof of correctness for the given function.

        Args:
            function_code: Python source code string containing the function.
            properties: Comma-separated property names, or natural-language
                description of desired invariants. Empty string means all.

        Returns:
            A :class:`Proof` object with steps, strategy_used, and confidence.
        """
        parsed_props = parse_property_spec(properties)

        if self.strategy == "auto":
            proof = self._auto_generate(function_code, parsed_props)
        else:
            proof = self._explicit_generate(self.strategy, function_code, parsed_props)

        return proof

    def _explicit_generate(
        self, strategy_name: str, function_code: str, properties: list[str]
    ) -> Proof:
        """Run a single named strategy end-to-end and wrap it in a `Proof`.

        The "temp_proof with confidence=0.0" pattern is required because the
        `Verifier.confidence` is a function of (signature, properties, steps)
        and we want it to use the *actual* steps the strategy produced, not
        whatever the calling code chose to set.
        """
        strategy_impl = _get_strategy(strategy_name)
        steps = strategy_impl.generate(function_code, properties)
        sig = strategy_impl._build_signature(function_code)
        verifier = Verifier()
        temp_proof = Proof(
            function_signature=sig,
            properties_requested=tuple(properties),
            steps=tuple(steps),
            strategy_used=strategy_name,
            confidence=0.0,
        )
        return Proof(
            function_signature=sig,
            properties_requested=tuple(properties),
            steps=tuple(steps),
            strategy_used=strategy_name,
            confidence=verifier.confidence(temp_proof),
        )

    def _auto_generate(self, function_code: str, properties: list[str]) -> Proof:
        """Auto strategy: try symbolic first, then testing (typecheck excluded).

        The fallback order is fixed at import time; we never fall back to
        `typecheck` because its verdict is `UNKNOWN` for almost every property.
        """
        # Try symbolic first
        sym = SymbolicStrategy()
        steps = sym.generate(function_code, properties)
        sig = sym._build_signature(function_code)

        # Check if symbolic succeeded (no skipped translation step)
        # We probe the step list for the canonical "Translate to sympy"
        # description that SymbolicStrategy emits; this is the cleanest
        # way to detect "function is too complex for sympy".
        translation_skipped = any(
            s.description == "Translate to sympy" and s.verdict == Verdict.SKIPPED
            for s in steps
        )

        if not translation_skipped:
            # Symbolic worked, use it
            verifier = Verifier()
            temp_proof = Proof(
                function_signature=sig,
                properties_requested=tuple(properties),
                steps=tuple(steps),
                strategy_used="symbolic",
                confidence=0.0,
            )
            return Proof(
                function_signature=sig,
                properties_requested=tuple(properties),
                steps=tuple(steps),
                strategy_used="symbolic",
                confidence=verifier.confidence(temp_proof),
            )

        # Fall back to testing
        test = TestingStrategy()
        steps = test.generate(function_code, properties)
        sig = test._build_signature(function_code)
        verifier = Verifier()
        temp_proof = Proof(
            function_signature=sig,
            properties_requested=tuple(properties),
            steps=tuple(steps),
            strategy_used="testing",
            confidence=0.0,
        )
        return Proof(
            function_signature=sig,
            properties_requested=tuple(properties),
            steps=tuple(steps),
            strategy_used="testing",
            confidence=verifier.confidence(temp_proof),
        )

    def verify_proof(self, proof: Proof) -> bool:
        """Verify a generated proof.

        Args:
            proof: The proof to verify.

        Returns:
            True if the proof is valid and internally consistent.
        """
        verifier = Verifier()
        return verifier.verify(proof)
