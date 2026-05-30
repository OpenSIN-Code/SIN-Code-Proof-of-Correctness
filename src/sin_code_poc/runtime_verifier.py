"""Runtime-Verifikation für bereits generierten Code."""
from __future__ import annotations

import ast
import inspect
from typing import Callable, Any


class RuntimeVerifier:
    """Führt Properties zur Laufzeit aus und meldet Verletzungen."""

    def __init__(self, max_examples: int = 100):
        self.max_examples = max_examples

    def verify_function(self, fn: Callable, properties: dict[str, Callable[[Any], bool]]) -> dict:
        from hypothesis import given, strategies as st, settings, HealthCheck
        results = {}
        for name, check in properties.items():
            try:
                import hypothesis.strategies as _st
                # Try integers as default strategy
                @given(x=st.integers(min_value=-1000, max_value=1000))
                @settings(max_examples=min(self.max_examples, 20), suppress_health_check=[HealthCheck.too_slow])
                def _test(x, _check=check):
                    assert _check(fn, x)
                _test()
                results[name] = "PASS"
            except AssertionError:
                results[name] = "FAIL"
            except Exception as e:
                results[name] = f"ERROR: {type(e).__name__}"
        return results

    @staticmethod
    def extract_signature(fn: Callable) -> dict:
        src = inspect.getsource(fn)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = []
                for arg in node.args.args:
                    params.append({"name": arg.arg, "annotation": ast.unparse(arg.annotation) if arg.annotation else None})
                ret = ast.unparse(node.returns) if node.returns else None
                docstring = ast.get_docstring(node)
                return {"name": node.name, "params": params, "return_type": ret, "docstring": docstring}
        return {}
