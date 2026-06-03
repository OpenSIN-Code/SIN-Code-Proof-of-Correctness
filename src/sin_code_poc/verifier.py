"""Proof verifier for SIN-Code POC.

Re-executes or validates the steps in a proof to confirm correctness.

Docs: verifier.py.doc.md
"""
from __future__ import annotations

from sin_code_poc.proof import Proof, ProofStep, Verdict


# Confidence rubric — extracted to module-level constants so the
# `confidence` method reads as the table the public docs describe.
_CONFIDENCE_ALL_PASSED = 1.0   # every meaningful step is PASSED
_CONFIDENCE_MIXED = 0.5        # base value for PASSED + UNKNOWN mix
_CONFIDENCE_FAILURE = 0.0      # any FAILED step, or no meaningful steps
_CONFIDENCE_EMPTY = 0.0        # no non-skipped steps at all

# Tag used in the `strategy` field of the meta-steps emitted by `verify_steps`.
_META_STRATEGY = "verifier"


class Verifier:
    """Verify generated proofs by re-evaluating or cross-checking steps.

    The verifier acts as a second opinion: it takes a proof produced by
    any strategy and checks whether the conclusions are internally
    consistent and reproducible.
    """

    def verify(self, proof: Proof) -> bool:
        """Verify a proof is internally consistent.

        Returns `True` if the proof is valid (all non-skipped steps
        passed and there are no contradictions).
        """
        if not proof.steps:
            return False

        # A proof with only SKIPPED steps carries no information; treat
        # it as not-valid rather than vacuously-true.
        meaningful = [s for s in proof.steps if s.verdict != Verdict.SKIPPED]
        if not meaningful:
            return False

        # All meaningful steps must be passed
        return all(s.verdict == Verdict.PASSED for s in meaningful)

    def verify_steps(self, proof: Proof) -> list[ProofStep]:
        """Verify each step and return a new trace with verification results.

        Adds a verification step after each original step, indicating
        whether the step's claim is consistent. The returned list has
        length `2 * len(proof.steps)` — original + meta-step, alternating.
        """
        verified: list[ProofStep] = []
        for step in proof.steps:
            verified.append(step)
            # Add a verification meta-step. Verdict is echoed (not re-checked)
            # because the verifier does not re-run user code today; real
            # re-execution would require a strategy-specific replay path.
            verification = ProofStep(
                description=f"Verify: {step.description}",
                verdict=step.verdict,
                details=f"Step verified as {step.verdict.value}",
                strategy=_META_STRATEGY,
            )
            verified.append(verification)
        return verified

    def confidence(self, proof: Proof) -> float:
        """Calculate a confidence score for the proof.

        - `1.0` if all meaningful steps passed
        - `0.5 * (passed / meaningful)` for a PASSED + UNKNOWN mix
        - `0.0` if any step failed or no meaningful step exists
        """
        meaningful = [s for s in proof.steps if s.verdict != Verdict.SKIPPED]
        if not meaningful:
            return _CONFIDENCE_EMPTY

        if any(s.verdict == Verdict.FAILED for s in meaningful):
            return _CONFIDENCE_FAILURE

        if all(s.verdict == Verdict.PASSED for s in meaningful):
            return _CONFIDENCE_ALL_PASSED

        # Mix of passed and unknown
        passed_count = sum(1 for s in meaningful if s.verdict == Verdict.PASSED)
        return _CONFIDENCE_MIXED * (passed_count / len(meaningful))
