# strategies/symbolic.py

**What:** Sympy-based symbolic execution strategy. Translates simple
arithmetic functions into symbolic expressions and verifies properties
via formal differentiation, substitution, and algebraic simplification.

**Dependencies:**
- `sympy>=1.12` — symbolic math engine
- `strategies/__init__.py` — base `Strategy` class
- `proof.py` — `ProofStep`, `Verdict`

**Key config:**
- Only supports `ast.BinOp` (+-*/), `ast.UnaryOp`, `ast.Call` to
  `math.sqrt/sin/cos/floor/ceil` and `abs`.
- Loops, conditionals, string operations, and external calls are
  **not** supported and will cause a `SKIPPED` step.

**Usage:**
```python
from sin_code_poc.strategies.symbolic import SymbolicStrategy
s = SymbolicStrategy()
steps = s.generate("def add(a, b): return a + b", ["commutative"])
```

**Caveats:**
- Division by a symbolic argument is flagged as a potential singularity.
- Derivative sign checks may return `UNKNOWN` when the sign depends on
  the parameter domain (e.g., `x**2` is not monotonic over all reals).
