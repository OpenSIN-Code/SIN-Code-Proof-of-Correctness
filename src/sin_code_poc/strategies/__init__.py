"""Strategy base classes and registry for SIN-Code POC.

Docs: __init__.py.doc.md
"""
from __future__ import annotations

import ast
import inspect
from abc import ABC, abstractmethod
from typing import Callable

from sin_code_poc.proof import Proof, ProofStep, Verdict
from sin_code_poc.properties import PropertySpec, parse_property_spec


# ── AST helpers (used by all three concrete strategies) ──────────────


class Strategy(ABC):
    """Abstract base for all proof strategies.

    Subclasses must set `name` (a unique short identifier used by
    `StrategyRegistry` and as the `strategy` field on emitted steps)
    and implement `generate()`.
    """

    name: str = ""

    @abstractmethod
    def generate(
        self, function_code: str, properties: list[str]
    ) -> list[ProofStep]:
        """Generate proof steps for the given function and properties.

        Args:
            function_code: Python source code string of the function under test.
            properties: Normalized list of property names to check (see
                `parse_property_spec` for the normalization rules).

        Returns:
            A list of `ProofStep` records describing each check the
            strategy performed.
        """

    def _extract_function_name(self, function_code: str) -> str:
        """Parse the function name from source code.

        Returns the name of the first `ast.FunctionDef` found in the
        module. Returns `<unknown>` if the source doesn't parse.
        """
        try:
            tree = ast.parse(function_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except SyntaxError:
            pass
        return "<unknown>"

    def _build_signature(self, function_code: str) -> str:
        """Build a normalized function signature string.

        Includes positional, `*args`, and `**kwargs` parameters in that
        order. Returns `<unknown>()` if the source doesn't parse.
        """
        try:
            tree = ast.parse(function_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    # Prefix the * and ** markers so the signature round-trips
                    # through downstream tooling that doesn't re-parse it.
                    if node.args.vararg:
                        args.append(f"*{node.args.vararg.arg}")
                    if node.args.kwarg:
                        args.append(f"**{node.args.kwarg.arg}")
                    return f"{node.name}({', '.join(args)})"
        except SyntaxError:
            pass
        return "<unknown>()"

    def _compile_function(self, function_code: str) -> Callable[..., object]:
        """Compile source code into a callable function object.

        Executes the source in an empty namespace and returns the first
        callable value found. This is intentionally permissive — it
        allows the source to define helper functions alongside the main
        one, but the caller is responsible for ensuring the source is
        trusted (it is `exec`'d).

        Raises:
            ValueError: If no callable is defined in the source.
        """
        namespace: dict[str, object] = {}
        exec(compile(ast.parse(function_code), "<string>", "exec"), namespace)
        # Return the first function object found
        for value in namespace.values():
            if callable(value):
                return value
        raise ValueError("No callable found in provided code")


# ── Strategy registry ────────────────────────────────────────────────


class StrategyRegistry:
    """Registry of available proof strategies.

    The registry keys on `Strategy.name`; a name collision overwrites
    the previous entry. Use a single `StrategyRegistry` per
    application-scoped lookup, or use the module-level convenience
    functions below.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        """Register a strategy under `strategy.name`. Overwrites on collision."""
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Strategy:
        """Look up a strategy by name.

        Raises:
            KeyError: If `name` was never registered.
        """
        if name not in self._strategies:
            raise KeyError(f"Unknown strategy: {name!r}")
        return self._strategies[name]

    def available(self) -> list[str]:
        """Return the names of all currently registered strategies."""
        return list(self._strategies)


# Global registry instance
_REGISTRY = StrategyRegistry()


def register_strategy(strategy: Strategy) -> None:
    """Module-level convenience wrapper around `_REGISTRY.register`."""
    _REGISTRY.register(strategy)


def get_strategy(name: str) -> Strategy:
    """Module-level convenience wrapper around `_REGISTRY.get`."""
    return _REGISTRY.get(name)


def available_strategies() -> list[str]:
    """Module-level convenience wrapper around `_REGISTRY.available`."""
    return _REGISTRY.available()
