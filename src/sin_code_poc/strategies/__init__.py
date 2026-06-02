"""Strategy base classes and registry for SIN-Code POC.

Docs: strategies/__init__.doc.md
"""
from __future__ import annotations

import ast
import inspect
from abc import ABC, abstractmethod
from typing import Callable

from sin_code_poc.proof import Proof, ProofStep, Verdict
from sin_code_poc.properties import PropertySpec, parse_property_spec


class Strategy(ABC):
    """Abstract base for all proof strategies."""

    name: str = ""

    @abstractmethod
    def generate(
        self, function_code: str, properties: list[str]
    ) -> list[ProofStep]:
        """Generate proof steps for the given function and properties."""

    def _extract_function_name(self, function_code: str) -> str:
        """Parse the function name from source code."""
        try:
            tree = ast.parse(function_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except SyntaxError:
            pass
        return "<unknown>"

    def _build_signature(self, function_code: str) -> str:
        """Build a normalized function signature string."""
        try:
            tree = ast.parse(function_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    if node.args.vararg:
                        args.append(f"*{node.args.vararg.arg}")
                    if node.args.kwarg:
                        args.append(f"**{node.args.kwarg.arg}")
                    return f"{node.name}({', '.join(args)})"
        except SyntaxError:
            pass
        return "<unknown>()"

    def _compile_function(self, function_code: str) -> Callable[..., object]:
        """Compile source code into a callable function object."""
        namespace: dict[str, object] = {}
        exec(compile(ast.parse(function_code), "<string>", "exec"), namespace)
        # Return the first function object found
        for value in namespace.values():
            if callable(value):
                return value
        raise ValueError("No callable found in provided code")


class StrategyRegistry:
    """Registry of available proof strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Strategy:
        if name not in self._strategies:
            raise KeyError(f"Unknown strategy: {name!r}")
        return self._strategies[name]

    def available(self) -> list[str]:
        return list(self._strategies)


# Global registry instance
_REGISTRY = StrategyRegistry()


def register_strategy(strategy: Strategy) -> None:
    _REGISTRY.register(strategy)


def get_strategy(name: str) -> Strategy:
    return _REGISTRY.get(name)


def available_strategies() -> list[str]:
    return _REGISTRY.available()
