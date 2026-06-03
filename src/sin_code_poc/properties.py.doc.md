# properties.py

Built-in property catalog and the natural-language `properties` parser.

## What it does

Defines the six built-in invariants (`pure`, `total`, `monotonic`,
`commutative`, `idempotent`, `no_exceptions`) as `PropertySpec`
records, and provides `parse_property_spec` to interpret the
user-supplied `properties` string in `ProofGenerator.generate`.

## Dependencies

- (none — pure data + regex)

## Property registry

| Name | Arity | Category | Aliases |
|------|-------|----------|---------|
| `pure` | any | determinism | `deterministic`, `no_side_effects` |
| `total` | any | termination | `no_hang` |
| `monotonic` | unary | order | `increasing`, `non_decreasing` |
| `commutative` | binary | structure | `symmetric` |
| `idempotent` | unary | structure | `idemp` |
| `no_exceptions` | any | termination | `never_raises`, `no_raise` |

## Parser semantics (`parse_property_spec`)

- Empty / `"all"` / `"*"` / `"default"` → all registered properties.
- Comma/space/semicolon/pipe-separated list of names or aliases →
  matching canonical names, deduplicated, in registry order.
- Natural-language fragments matched against `_NL_PATTERNS`.
- Unknown tokens are silently dropped (the parser is intentionally
  tolerant of free-form user intent).

## Usage

```python
from sin_code_poc.properties import parse_property_spec, list_properties
parse_property_spec("")                          # all six
parse_property_spec("idempotent, never_raises")  # ['idempotent', 'no_exceptions']
parse_property_spec("should be deterministic")   # ['pure']
```

## Known caveats

- The arity `-1` sentinel means "any"; the testing strategy currently
  treats `-1` as unary — see `runtime_checkers` for the per-strategy
  interpretation.
- The NL patterns are case-insensitive and word-boundary anchored; an
  alias like `never_raises` matches both `never_raises` and `never raises`.
