# verifier.py

Independent re-checker for proofs produced by any strategy.

## What it does

`Verifier` is the "second opinion" of the pipeline. Given a `Proof`,
it determines whether the proof is internally consistent and computes
a confidence score in `[0.0, 1.0]`. Used by the auto-fallback in
`ProofGenerator` and exposed via the MCP server.

## Dependencies

- `proof.py` — `Proof`, `ProofStep`, `Verdict`

## Confidence rules

| Condition | Confidence |
|-----------|------------|
| No steps or only `SKIPPED` steps | `0.0` |
| Any step `FAILED` | `0.0` |
| All meaningful steps `PASSED` | `1.0` |
| Mix of `PASSED` and `UNKNOWN` | `0.5 × (passed / meaningful)` |

## Public API

| Method | Returns | Description |
|--------|---------|-------------|
| `verify(proof)` | `bool` | True iff there is at least one meaningful step and all of them passed |
| `verify_steps(proof)` | `list[ProofStep]` | Trace with a duplicate "Verify:" step after each original |
| `confidence(proof)` | `float` | Numeric confidence (see table above) |

## Usage

```python
from sin_code_poc import ProofGenerator
from sin_code_poc.verifier import Verifier
gen = ProofGenerator(strategy="auto")
proof = gen.generate("def f(x): return x\n", "pure")
print(Verifier().verify(proof), Verifier().confidence(proof))
```

## Known caveats

- `verify_steps` does not re-run any code; it just echoes the verdict
  with a `Verify:` prefix. Real re-execution would be strategy-specific.
- The confidence rubric is intentionally simple; do not tune it
  without updating the public docs.
