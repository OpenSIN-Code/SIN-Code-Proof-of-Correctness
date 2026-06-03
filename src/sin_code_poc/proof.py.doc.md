# proof.py

Immutable data structures for proof-of-correctness results.

## What it does

Defines `Verdict` (enum), `ProofStep` (one check), and `Proof`
(aggregated result). These flow through every strategy, the verifier,
and the report serializers. Everything is `@dataclass(frozen=True)` so
proofs are hashable and safe to share between threads.

## Public API

| Symbol | Purpose |
|--------|---------|
| `Verdict` | `passed` / `failed` / `unknown` / `skipped` |
| `ProofStep` | Single check: description, verdict, details, strategy |
| `Proof` | Full proof with signature, properties, steps, strategy, confidence |
| `Proof.is_success()` | True iff all non-skipped steps passed |

## Usage

```python
from sin_code_poc.proof import Proof, ProofStep, Verdict
p = Proof(
    function_signature="add(x, y)",
    properties_requested=("commutative",),
    steps=(ProofStep("Check commutative", Verdict.PASSED, "swap yields same value", "symbolic"),),
    strategy_used="symbolic",
    confidence=1.0,
)
assert p.is_success()
```

## Known caveats

- Adding a field to `Proof` is a breaking change for any consumer
  using `dataclasses.asdict` or pickle-based caching.
- The `is_success` definition treats `SKIPPED` as success — a proof
  with *only* skipped steps is *not* success (that case is rejected
  by `Verifier.verify`).
