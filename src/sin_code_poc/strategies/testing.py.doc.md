# testing.py

Property-based testing strategy using `hypothesis`.

## What it does

Compiles the user's function and runs each requested property as a
Hypothesis-driven test. Hypothesis generates random inputs in
`[-1000, 1000]` (or pairs thereof) and reports the first counterexample
if the property fails.

## Dependencies

- `hypothesis` — property-based testing framework
- `proof.py` — `ProofStep`, `Verdict`
- `properties.py` — `runtime_checkers` (per-property check functions)
- `strategies/__init__.py` — `Strategy` base class

## Public API

| Symbol | Purpose |
|--------|---------|
| `TestingStrategy` | Strategy class (`name = "testing"`) |
| `generate(code, properties)` | Produce proof steps |
| `_check_property(prop, fn, checkers)` | Per-property step |
| `_run_unary(fn, check)` | Hypothesis run for unary properties |
| `_run_binary(fn, check)` | Hypothesis run for binary properties |

## Tunable constants

| Constant | Value | Why |
|----------|-------|-----|
| `max_examples` (int) | 100 | Upper bound on integer examples per check |
| `max_examples` (float) | 50 | Smaller — floats are slower to compare |
| integer range | `[-1000, 1000]` | Catches overflow at the edge of int32 |
| float range | `[-1000, 1000]`, no NaN/Inf | Avoids `nan != nan` semantics breaking tests |

## Known caveats

- `_run_unary` runs BOTH an integer pass and a float pass. A failure
  in the integer pass is preferred; a float failure is only kept if
  the integer pass was clean.
- Uses `suppress_health_check=[HealthCheck.too_slow]` so user code that
  is slow per-iteration does not abort the whole run.
- A property that needs >2 arguments is unsupported by this strategy.
