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


# Register strategies at import time
_registry = StrategyRegistry()
_registry.register(SymbolicStrategy())
_registry.register(TestingStrategy())
_registry.register(TypecheckStrategy())


def _get_strategy(name: str) -> Any:
    return _registry.get(name)


def _available_strategies() -> list[str]:
    return _registry.available()


class ProofGenerator:
    """Generate proofs of correctness for Python functions.

    Uses one of several strategies (symbolic, testing, typecheck) or
    auto-selects the best strategy based on the function.
    """

    def __init__(self, strategy: str = "auto"):
        """Initialize with a strategy.

        Args:
            strategy: One of ``"auto"``, ``"symbolic"``, ``"testing"``,
                ``"typecheck"``.
        """
        if strategy not in ("auto", "symbolic", "testing", "typecheck"):
            raise ValueError(
                f"Unknown strategy: {strategy!r}. Choose from: auto, symbolic, testing, typecheck"
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
            strategy_impl = _get_strategy(self.strategy)
            steps = strategy_impl.generate(function_code, parsed_props)
            sig = strategy_impl._build_signature(function_code)
            verifier = Verifier()
            proof = Proof(
                function_signature=sig,
                properties_requested=tuple(parsed_props),
                steps=tuple(steps),
                strategy_used=self.strategy,
                confidence=verifier.confidence(
                    Proof(
                        function_signature=sig,
                        properties_requested=tuple(parsed_props),
                        steps=tuple(steps),
                        strategy_used=self.strategy,
                        confidence=0.0,
                    )
                ),
            )

        return proof

    def _auto_generate(self, function_code: str, properties: list[str]) -> Proof:
        """Auto strategy: try symbolic first, then testing, then typecheck."""
        # Try symbolic first
        sym = SymbolicStrategy()
        steps = sym.generate(function_code, properties)
        sig = sym._build_signature(function_code)

        # Check if symbolic succeeded (no skipped translation step)
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
