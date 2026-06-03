# typecheck.py

Static type-checking strategy that shells out to `mypy`.

## What it does

Writes the user's function to a temp file, runs `mypy` on it, and
emits one `ProofStep` per property reflecting the type system's view.
Useful as a "type perspective" complement to the runtime strategies.

## Dependencies

- `mypy` — invoked as `python -m mypy` (not the package import)
- `proof.py` — `ProofStep`, `Verdict`
- `strategies/__init__.py` — `Strategy` base class

## Public API

| Symbol | Purpose |
|--------|---------|
| `TypecheckStrategy` | The strategy class (`name = "typecheck"`) |
| `TypecheckStrategy.generate(code, properties)` | Produce proof steps |
| `_has_type_annotations(code)` | AST helper |
| `_check_property_type_perspective(prop, mypy_passed, has_annotations)` | Per-property step |

## What it reports

- A `Typecheck with mypy` step (`PASSED` if mypy exit 0, else `FAILED`)
- A `Check type annotations present` step (`PASSED`/`UNKNOWN`)
- A per-property step. Most properties return `UNKNOWN` because Python's
  type system cannot express things like commutativity or monotonicity.

## Known caveats

- Runs mypy as a subprocess (30s timeout). Slow functions of mypy
  are not pre-warmed.
- `python -m mypy` requires mypy to be importable in the current venv.
- The `pure` / `no_exceptions` / `commutative` / `monotonic` /
  `idempotent` properties are *always* `UNKNOWN` from this strategy —
  the type system simply cannot prove them.
