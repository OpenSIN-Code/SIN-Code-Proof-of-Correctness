"""Type checking strategy using mypy.

Verifies type signatures prevent certain classes of errors.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any

from sin_code_poc.proof import ProofStep, Verdict
from sin_code_poc.strategies import Strategy


class TypecheckStrategy(Strategy):
    """Type checking strategy using mypy.

    Verifies type signatures prevent certain classes of errors.
    """

    name = "typecheck"

    def generate(
        self, function_code: str, properties: list[str]
    ) -> list[ProofStep]:
        steps: list[ProofStep] = []
        sig = self._build_signature(function_code)

        # Create a temporary file with the function
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(function_code)
            temp_path = f.name

        try:
            # Run mypy
            result = subprocess.run(
                ["python", "-m", "mypy", "--ignore-missing-imports", "--no-error-summary", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            mypy_passed = result.returncode == 0
            mypy_output = result.stdout.strip()
        except Exception as exc:
            mypy_passed = False
            mypy_output = f"mypy execution error: {exc}"
        finally:
            os.unlink(temp_path)

        steps.append(
            ProofStep(
                description="Typecheck with mypy",
                verdict=Verdict.PASSED if mypy_passed else Verdict.FAILED,
                details=mypy_output if mypy_output else "No type errors",
                strategy=self.name,
            )
        )

        # Check for type annotations in the function
        has_annotations = self._has_type_annotations(function_code)
        steps.append(
            ProofStep(
                description="Check type annotations present",
                verdict=Verdict.PASSED if has_annotations else Verdict.UNKNOWN,
                details="Function has type annotations" if has_annotations else "No type annotations found",
                strategy=self.name,
            )
        )

        # For each property, provide a type-check perspective
        for prop in properties:
            step = self._check_property_type_perspective(prop, mypy_passed, has_annotations)
            steps.append(step)

        return steps

    def _has_type_annotations(self, function_code: str) -> bool:
        """Check if the function has any type annotations."""
        import ast
        try:
            tree = ast.parse(function_code)
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check argument annotations
                for arg in node.args.args:
                    if arg.annotation is not None:
                        return True
                # Check return annotation
                if node.returns is not None:
                    return True
        return False

    def _check_property_type_perspective(
        self, prop: str, mypy_passed: bool, has_annotations: bool
    ) -> ProofStep:
        """Provide a type-check perspective on a property."""
        if prop == "pure":
            # Type annotations don't guarantee purity, but no IO types help
            return ProofStep(
                description="Check pure (type perspective)",
                verdict=Verdict.UNKNOWN,
                details="Type system cannot verify purity; use symbolic or testing strategy",
                strategy=self.name,
            )

        if prop == "total":
            # Type annotations can help catch missing returns
            if mypy_passed:
                return ProofStep(
                    description="Check total (type perspective)",
                    verdict=Verdict.PASSED,
                    details="mypy found no missing return paths",
                    strategy=self.name,
                )
            return ProofStep(
                description="Check total (type perspective)",
                verdict=Verdict.UNKNOWN,
                details="mypy found issues; review for missing returns",
                strategy=self.name,
            )

        if prop == "no_exceptions":
            # Type annotations for specific exceptions are not standard
            return ProofStep(
                description="Check no_exceptions (type perspective)",
                verdict=Verdict.UNKNOWN,
                details="Type system cannot verify exception safety; use testing strategy",
                strategy=self.name,
            )

        if prop == "monotonic":
            return ProofStep(
                description="Check monotonic (type perspective)",
                verdict=Verdict.UNKNOWN,
                details="Order properties are not expressible in Python's type system",
                strategy=self.name,
            )

        if prop == "commutative":
            return ProofStep(
                description="Check commutative (type perspective)",
                verdict=Verdict.UNKNOWN,
                details="Commutativity is not expressible in Python's type system",
                strategy=self.name,
            )

        if prop == "idempotent":
            return ProofStep(
                description="Check idempotent (type perspective)",
                verdict=Verdict.UNKNOWN,
                details="Idempotence is not expressible in Python's type system",
                strategy=self.name,
            )

        return ProofStep(
            description=f"Check {prop} (type perspective)",
            verdict=Verdict.SKIPPED,
            details="Property not supported by typecheck strategy",
            strategy=self.name,
        )
