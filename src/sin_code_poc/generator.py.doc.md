# generator.py

**What:** Core orchestrator that picks a proof strategy, runs it,
and returns an immutable `Proof` object.

**Dependencies:**
- `proof.py` — dataclasses (`Proof`, `ProofStep`, `Verdict`)
- `strategies/symbolic.py` — sympy-based execution
- `strategies/testing.py` — Hypothesis-based testing
- `strategies/typecheck.py` — mypy integration
- `properties.py` — property parsing and runtime checkers
- `verifier.py` — confidence scoring and step validation

**Key config:**
- `strategy` in `{'auto', 'symbolic', 'testing', 'typecheck'}`

**Usage:**
```python
from sin_code_poc import ProofGenerator
gen = ProofGenerator(strategy="auto")
proof = gen.generate("def f(x): return x + 1", properties="pure, total")
assert proof.is_success()
```

**Caveats:**
- `auto` tries symbolic first; if the function contains unsupported
  AST nodes (loops, conditionals, external calls), it falls back to
  `testing`.
- `typecheck` alone is rarely sufficient for full verification; use
  it as a supplementary check.
