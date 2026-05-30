"""Kompiliert einfache Spezifikationen in testbare Properties."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Specification:
    function_name: str
    preconditions: list[str]
    postconditions: list[str]
    invariants: list[str]


class SpecCompiler:
    """Übersetzt deklarative Specs in Property-Tests."""

    def compile(self, spec: Specification) -> str:
        lines = [
            "from hypothesis import given, strategies as st, assume",
            f"from your_module import {spec.function_name}",
            "",
            "",
            "@given(x=st.integers())",
            f"def test_{spec.function_name}_spec(x):",
        ]
        for pre in spec.preconditions:
            lines.append(f"    assume({pre})")
        lines.append(f"    result = {spec.function_name}(x)")
        for post in spec.postconditions:
            safe = post.replace("result", "result").replace("x", "x")
            lines.append(f"    assert {safe}, f'postcondition failed: {post}'")
        return "\n".join(lines)

    def from_intent(self, intent: str, function_name: str) -> Specification:
        """Aus natürlicher Sprache (SOTA-Feature)."""
        intent = intent.lower()
        pre, post, inv = [], [], []
        if "positive" in intent or "non-negative" in intent:
            post.append("result >= 0")
        if "sorted" in intent:
            post.append("result == sorted(result)")
        if "non-empty input" in intent:
            pre.append("len(x) > 0")
        if "idempotent" in intent:
            post.append(f"{function_name}(result) == result")
        if not post:
            post.append("result is not None")
        return Specification(function_name=function_name,
                             preconditions=pre,
                             postconditions=post,
                             invariants=inv)
