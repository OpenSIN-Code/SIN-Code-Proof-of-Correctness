# generator.py

Top-level `ProofGenerator` orchestrating the three proof strategies.

## What it does

Picks a strategy (`auto` / `symbolic` / `testing` / `typecheck`) and
runs it against a user-supplied function. In `auto` mode it falls back
from symbolic to testing if the function isn't pure-arithmetic, and
produces a `Proof` object that includes the strategy used and a
confidence score from the `Verifier`.

## Dependencies

- `proof.py` — `Proof`, `ProofStep`, `Verdict`
- `properties.py` — `parse_property_spec` (string → property list)
- `strategies/` — `SymbolicStrategy`, `TestingStrategy`, `TypecheckStrategy`
- `verifier.py` — `Verifier` (confidence scoring)

## Strategy selection (`auto` mode)

1. Try **symbolic** — only works for pure-arithmetic functions.
2. If translation was skipped, fall back to **testing**.
3. The `typecheck` strategy is not in the auto-fallback chain because
   it is strictly weaker than the other two for our property catalog.

## Usage

```python
from sin_code_poc import ProofGenerator
gen = ProofGenerator(strategy="auto")
proof = gen.generate("def add(x, y):\n    return x + y\n", "commutative")
print(proof.confidence, proof.is_success())
```

## Known caveats

- `auto` does not fall back to `typecheck`; pick it explicitly if needed.
- The `_auto_generate` fallback path always uses `testing`, never `typecheck`.
- The `strategy` field is set verbatim on the proof (no normalization).
