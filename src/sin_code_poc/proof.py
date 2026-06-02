"""Proof data structures for SIN-Code POC.

Defines ``Proof`` (immutable result) and ``ProofStep`` — the two
dataclasses that flow between :pyclass:`ProofGenerator`,
the strategy implementations, :pyclass:`Verifier`, and
:pymod:`report`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    """Enumeration of possible verification outcomes."""

    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ProofStep:
    """One step in the proof trace.

    Attributes:
        description: Human-readable description of what was checked.
        verdict: Outcome of this step (passed, failed, unknown, skipped).
        details: Supplementary information — concrete values, failure
            causes, or diagnostic messages.
        strategy: Name of the strategy that produced this step.
    """

    description: str
    verdict: Verdict = Verdict.UNKNOWN
    details: str = ""
    strategy: str = ""


@dataclass(frozen=True)
class Proof:
    """Immutable proof-of-correctness result.

    Attributes:
        function_signature: Normalized representation of the function's
            signature (``"f(x, y)"`` style).
        properties_requested: Normalized list of invariant names that
            were asked to check.
        steps: Ordered trace of individual checks performed.
        strategy_used: Name of the primary strategy that generated
            this proof (``"symbolic"``, ``"testing"``, ``"typecheck"``,
            or ``"auto"``).
        confidence: Numeric confidence in the proof outcome.
            ``1.0`` means fully verified; values below ``1.0`` reflect
            limited coverage (sampling, heuristic checks, etc.).
    """

    function_signature: str = ""
    properties_requested: tuple[str, ...] = field(default_factory=tuple)
    steps: tuple[ProofStep, ...] = field(default_factory=tuple)
    strategy_used: str = "auto"
    confidence: float = 0.0

    def is_success(self) -> bool:
        """Return ``True`` when every non-skipped step passed."""
        return all(
            s.verdict in (Verdict.PASSED, Verdict.SKIPPED) for s in self.steps
        )
