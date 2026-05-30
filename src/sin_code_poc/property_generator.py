"""Generiert Properties (formale Invarianten) für Python-Funktionen."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Property:
    name: str
    description: str
    hypothesis_strategy: str
    check_code: str  # Python-Code that returns bool


class PropertyGenerator:
    """Erkennt Funktionssignaturen und schlägt passende Properties vor."""

    BUILTIN_TEMPLATES = {
        "idempotent": Property(
            name="idempotent",
            description="Applying function twice yields same result as once: f(f(x)) == f(x)",
            hypothesis_strategy="from_type(T)",
            check_code="f(f(x)) == f(x)",
        ),
        "reversible": Property(
            name="reversible",
            description="Inverse exists: g(f(x)) == x",
            hypothesis_strategy="from_type(T)",
            check_code="g(f(x)) == x",
        ),
        "pure_no_side_effects": Property(
            name="pure",
            description="Same input always yields same output",
            hypothesis_strategy="from_type(T)",
            check_code="f(x) == f(x)",
        ),
        "monotonic": Property(
            name="monotonic",
            description="x <= y implies f(x) <= f(y)",
            hypothesis_strategy="integers()",
            check_code="(x <= y) == (f(x) <= f(y))",
        ),
        "boundary_non_negative": Property(
            name="non_negative_output",
            description="Output is always >= 0",
            hypothesis_strategy="from_type(T)",
            check_code="f(x) >= 0",
        ),
        "length_preserving": Property(
            name="length_preserving",
            description="len(output) == len(input)",
            hypothesis_strategy="lists(from_type(T))",
            check_code="len(f(x)) == len(x)",
        ),
        "sorted_output": Property(
            name="sorted_output",
            description="Output is sorted",
            hypothesis_strategy="lists(integers())",
            check_code="sorted(f(x)) == f(x)",
        ),
    }

    def suggest(self, signature: dict) -> list[Property]:
        """
        signature: dict with keys: name, return_type, params: list[dict], docstring
        """
        props: list[Property] = []
        ret = (signature.get("return_type") or "").lower()
        params = signature.get("params", [])
        doc = (signature.get("docstring") or "").lower()

        # Heuristics
        if ret in ("int", "float"):
            props.append(self.BUILTIN_TEMPLATES["boundary_non_negative"])
            if any(p.get("name") in ("x", "n") for p in params):
                props.append(self.BUILTIN_TEMPLATES["monotonic"])

        if ret in ("list", "tuple", "str"):
            props.append(self.BUILTIN_TEMPLATES["length_preserving"])

        if "sort" in signature.get("name", "").lower():
            props.append(self.BUILTIN_TEMPLATES["sorted_output"])

        if "encode" in signature.get("name", "").lower() or "decode" in signature.get("name", "").lower():
            props.append(self.BUILTIN_TEMPLATES["reversible"])

        if "normalize" in signature.get("name", "").lower() or "canonical" in signature.get("name", "").lower():
            props.append(self.BUILTIN_TEMPLATES["idempotent"])

        # Always include purity
        props.append(self.BUILTIN_TEMPLATES["pure_no_side_effects"])
        return props

    def render_hypothesis_test(self, func_name: str, properties: list[Property]) -> str:
        """Rendert einen lauffähigen hypothesis-Test."""
        lines = [
            "from hypothesis import given, strategies as st",
            "import hypothesis.strategies as _st",
            f"from your_module import {func_name}",
            "",
            f"f = {func_name}",
            "",
        ]
        for p in properties:
            lines.append(f"@given(x=st.{p.hypothesis_strategy})")
            lines.append(f"def test_{p.name}(x):")
            lines.append(f'    \"\"\"{p.description}\"\"\"')
            lines.append(f"    assert {p.check_code}")
            lines.append("")
        return "\n".join(lines)
