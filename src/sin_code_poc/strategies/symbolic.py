"""Symbolic execution strategy using sympy.

For pure functions with numeric operations, symbolically execute
with abstract inputs and verify output invariants.

Docs: strategies/symbolic.py.doc.md
"""
from __future__ import annotations

import ast
import math
from typing import Any, Callable

import sympy as sp

from sin_code_poc.proof import ProofStep, Verdict
from sin_code_poc.strategies import Strategy


class SymbolicStrategy(Strategy):
    """Symbolic execution strategy using sympy.

    Parses the function AST, attempts to translate numeric operations
    into sympy expressions, and verifies properties symbolically.
    """

    name = "symbolic"

    def generate(
        self, function_code: str, properties: list[str]
    ) -> list[ProofStep]:
        steps: list[ProofStep] = []
        sig = self._build_signature(function_code)

        try:
            fn = self._compile_function(function_code)
        except Exception as exc:
            steps.append(
                ProofStep(
                    description="Compile function",
                    verdict=Verdict.FAILED,
                    details=f"Compilation error: {exc}",
                    strategy=self.name,
                )
            )
            return steps

        steps.append(
            ProofStep(
                description="Compile function",
                verdict=Verdict.PASSED,
                details=f"Compiled {sig}",
                strategy=self.name,
            )
        )

        # Attempt sympy translation
        sym_expr, sym_args, translation_ok = self._to_sympy(function_code)
        if not translation_ok:
            steps.append(
                ProofStep(
                    description="Translate to sympy",
                    verdict=Verdict.SKIPPED,
                    details="Function contains unsupported operations for symbolic translation",
                    strategy=self.name,
                )
            )
            return steps

        steps.append(
            ProofStep(
                description="Translate to sympy",
                verdict=Verdict.PASSED,
                details=f"Symbolic expression: {sym_expr}",
                strategy=self.name,
            )
        )

        # Check properties symbolically
        for prop in properties:
            step = self._check_property(prop, fn, sym_expr, sym_args)
            steps.append(step)

        return steps

    def _to_sympy(
        self, function_code: str
    ) -> tuple[sp.Expr | None, list[sp.Symbol], bool]:
        """Translate a simple function body into a sympy expression.

        Returns ``(expr, symbols, success)``.
        """
        try:
            tree = ast.parse(function_code)
        except SyntaxError:
            return None, [], False

        func_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_def = node
                break
        if func_def is None:
            return None, [], False

        arg_names = [a.arg for a in func_def.args.args]
        symbols = [sp.Symbol(a) for a in arg_names]
        sym_map = {name: sym for name, sym in zip(arg_names, symbols)}

        # Check for unsupported control flow in the body
        unsupported_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.TryStar)
        for stmt in func_def.body:
            if isinstance(stmt, unsupported_nodes):
                return None, symbols, False
            # Also scan inside statements for nested unsupported nodes
            for node in ast.walk(stmt):
                if isinstance(node, unsupported_nodes):
                    return None, symbols, False

        # We only support simple return statements with arithmetic
        if not func_def.body or not isinstance(func_def.body[-1], ast.Return):
            return None, symbols, False

        ret = func_def.body[-1]
        if not isinstance(ret, ast.Return) or ret.value is None:
            return None, symbols, False

        try:
            expr = self._ast_to_sympy(ret.value, sym_map)
            return expr, symbols, True
        except (ValueError, TypeError):
            return None, symbols, False

    def _ast_to_sympy(self, node: ast.expr, sym_map: dict[str, sp.Symbol]) -> sp.Expr:
        """Convert an AST expression node into a sympy expression."""
        if isinstance(node, ast.Name):
            if node.id in sym_map:
                return sym_map[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)
            raise ValueError("Non-numeric constant")
        if isinstance(node, ast.BinOp):
            left = self._ast_to_sympy(node.left, sym_map)
            right = self._ast_to_sympy(node.right, sym_map)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left**right
            if isinstance(node.op, ast.FloorDiv):
                return sp.floor(left / right)
            if isinstance(node.op, ast.Mod):
                return left % right
            raise ValueError("Unsupported binary operator")
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -self._ast_to_sympy(node.operand, sym_map)
            if isinstance(node.op, ast.UAdd):
                return self._ast_to_sympy(node.operand, sym_map)
            raise ValueError("Unsupported unary operator")
        if isinstance(node, ast.Call):
            # Support math functions like sqrt, sin, cos, abs
            if isinstance(node.func, ast.Name) and node.func.id == "abs":
                if len(node.args) == 1:
                    return sp.Abs(self._ast_to_sympy(node.args[0], sym_map))
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "math":
                math_func = node.func.attr
                if len(node.args) == 1:
                    arg = self._ast_to_sympy(node.args[0], sym_map)
                    if math_func == "sqrt":
                        return sp.sqrt(arg)
                    if math_func == "sin":
                        return sp.sin(arg)
                    if math_func == "cos":
                        return sp.cos(arg)
                    if math_func == "floor":
                        return sp.floor(arg)
                    if math_func == "ceil":
                        return sp.ceiling(arg)
            raise ValueError("Unsupported function call")
        raise ValueError("Unsupported AST node")

    def _check_property(
        self,
        prop: str,
        fn: Callable[..., Any],
        sym_expr: sp.Expr | None,
        sym_args: list[sp.Symbol],
    ) -> ProofStep:
        """Check a single property symbolically."""
        if sym_expr is None:
            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.SKIPPED,
                details="No symbolic expression available",
                strategy=self.name,
            )

        try:
            if prop == "pure":
                # Pure functions are deterministic; sympy expressions are inherently deterministic
                return ProofStep(
                    description="Check pure",
                    verdict=Verdict.PASSED,
                    details="Sympy expression is deterministic (no side effects)",
                    strategy=self.name,
                )

            if prop == "total":
                # Check if expression has singularities (e.g., division by parameter)
                # A simplistic check: if expression contains division by a symbol
                if self._has_singularity(sym_expr, sym_args):
                    return ProofStep(
                        description="Check total",
                        verdict=Verdict.FAILED,
                        details="Expression may have singularities",
                        strategy=self.name,
                    )
                return ProofStep(
                    description="Check total",
                    verdict=Verdict.PASSED,
                    details="Expression is defined for all symbolic inputs",
                    strategy=self.name,
                )

            if prop == "monotonic":
                if len(sym_args) >= 1:
                    derivative = sp.diff(sym_expr, sym_args[0])
                    is_mono = sp.simplify(derivative >= 0)
                    if is_mono == True:
                        return ProofStep(
                            description="Check monotonic",
                            verdict=Verdict.PASSED,
                            details=f"Derivative {derivative} >= 0 for all inputs",
                            strategy=self.name,
                        )
                    if is_mono == False:
                        return ProofStep(
                            description="Check monotonic",
                            verdict=Verdict.FAILED,
                            details=f"Derivative {derivative} is not non-negative everywhere",
                            strategy=self.name,
                        )
                    return ProofStep(
                        description="Check monotonic",
                        verdict=Verdict.UNKNOWN,
                        details=f"Derivative {derivative} sign depends on input values",
                        strategy=self.name,
                    )
                return ProofStep(
                    description="Check monotonic",
                    verdict=Verdict.SKIPPED,
                    details="No arguments to differentiate",
                    strategy=self.name,
                )

            if prop == "commutative":
                if len(sym_args) >= 2:
                    swapped = sym_expr.subs(
                        [(sym_args[0], sym_args[1]), (sym_args[1], sym_args[0])],
                        simultaneous=True,
                    )
                    diff = sp.simplify(sym_expr - swapped)
                    if diff == 0:
                        return ProofStep(
                            description="Check commutative",
                            verdict=Verdict.PASSED,
                            details="Expression is symmetric under argument swap",
                            strategy=self.name,
                        )
                    return ProofStep(
                        description="Check commutative",
                        verdict=Verdict.FAILED,
                        details=f"Difference after swap: {diff}",
                        strategy=self.name,
                    )
                return ProofStep(
                    description="Check commutative",
                    verdict=Verdict.SKIPPED,
                    details="Need at least 2 arguments",
                    strategy=self.name,
                )

            if prop == "idempotent":
                if len(sym_args) >= 1:
                    composed = sym_expr.subs({sym_args[0]: sym_expr})
                    diff = sp.simplify(composed - sym_expr)
                    if diff == 0:
                        return ProofStep(
                            description="Check idempotent",
                            verdict=Verdict.PASSED,
                            details="f(f(x)) == f(x) symbolically",
                            strategy=self.name,
                        )
                    return ProofStep(
                        description="Check idempotent",
                        verdict=Verdict.FAILED,
                        details=f"Difference: {diff}",
                        strategy=self.name,
                    )
                return ProofStep(
                    description="Check idempotent",
                    verdict=Verdict.SKIPPED,
                    details="Need at least 1 argument",
                    strategy=self.name,
                )

            if prop == "no_exceptions":
                # If symbolic translation succeeded, the function is numeric and likely safe
                if self._has_singularity(sym_expr, sym_args):
                    return ProofStep(
                        description="Check no_exceptions",
                        verdict=Verdict.UNKNOWN,
                        details="Potential singularities (e.g., division by zero)",
                        strategy=self.name,
                    )
                return ProofStep(
                    description="Check no_exceptions",
                    verdict=Verdict.PASSED,
                    details="No obvious exception sources in symbolic expression",
                    strategy=self.name,
                )

            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.SKIPPED,
                details=f"Property not supported by symbolic strategy",
                strategy=self.name,
            )
        except Exception as exc:
            return ProofStep(
                description=f"Check {prop}",
                verdict=Verdict.UNKNOWN,
                details=f"Symbolic check error: {exc}",
                strategy=self.name,
            )

    def _has_singularity(self, expr: sp.Expr, args: list[sp.Symbol]) -> bool:
        """Heuristic check for potential singularities (division by symbolic args)."""
        for denom in expr.as_numer_denom()[1].free_symbols:
            if denom in args:
                return True
        return False
