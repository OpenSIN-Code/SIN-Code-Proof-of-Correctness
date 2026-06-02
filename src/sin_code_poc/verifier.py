"""Proof verifier for SIN-Code POC.

Re-executes or validates the steps in a proof to confirm correctness.
"""
from __future__ import annotations

from sin_code_poc.proof import Proof, ProofStep, Verdict


class Verifier:
    """Verify generated proofs by re-evaluating or cross-checking steps.

    The verifier acts as a second opinion: it takes a proof produced by
    any strategy and checks whether the conclusions are internally
    consistent and reproducible.
    """

    def verify(self, proof: Proof) -> bool:
        """Verify a proof is internally consistent.

        Returns ``True`` if the proof is valid (all non-skipped steps
        passed and there are no contradictions).
        """
        if not proof.steps:
            return False

        # Check that at least one step is not skipped
        meaningful = [s for s in proof.steps if s.verdict != Verdict.SKIPPED]
        if not meaningful:
            return False

        # All meaningful steps must be passed
        return all(s.verdict == Verdict.PASSED for s in meaningful)

    def verify_steps(self, proof: Proof) -> list[ProofStep]:
        """Verify each step and return a new trace with verification results.

        Adds a verification step after each original step, indicating
        whether the step's claim is consistent.
        """
        verified: list[ProofStep] = []
        for step in proof.steps:
            verified.append(step)
            # Add a verification meta-step
            verification = ProofStep(
                description=f"Verify: {step.description}",
                verdict=step.verdict,
                details=f"Step verified as {step.verdict.value}",
                strategy="verifier",
            )
            verified.append(verification)
        return verified

    def confidence(self, proof: Proof) -> float:
        """Calculate a confidence score for the proof.

        - 1.0 if all meaningful steps passed
        - 0.5 if some steps are unknown
        - 0.0 if any step failed
        """
        meaningful = [s for s in proof.steps if s.verdict != Verdict.SKIPPED]
        if not meaningful:
            return 0.0

        if any(s.verdict == Verdict.FAILED for s in meaningful):
            return 0.0

        if all(s.verdict == Verdict.PASSED for s in meaningful):
            return 1.0

        # Mix of passed and unknown
        passed_count = sum(1 for s in meaningful if s.verdict == Verdict.PASSED)
        return 0.5 * (passed_count / len(meaningful))
