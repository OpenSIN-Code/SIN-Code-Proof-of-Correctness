# __init__.py

Package entry point for `sin_code_poc`.

## What it does

Re-exports the public API (`ProofGenerator`, `Proof`, `ProofStep`,
`Verdict`, the property catalog helpers, and the report serializers)
and pins `__version__`.

## Public exports

| Symbol | Source |
|--------|--------|
| `ProofGenerator` | `generator.py` |
| `Proof`, `ProofStep`, `Verdict` | `proof.py` |
| `PROPERTY_REGISTRY`, `list_properties`, `parse_property_spec`, `property_metadata` | `properties.py` |
| `proof_to_dict`, `proof_to_markdown`, `proof_to_json` | `report.py` |
| `__version__` | this module |

## Usage

```python
from sin_code_poc import ProofGenerator
proof = ProofGenerator(strategy="auto").generate("def f(x): return x\n")
```

## Known caveats

- `__all__` is the source of truth for `from sin_code_poc import *`;
  any new public symbol must be added to both the import list and
  `__all__`.
- The `Docs: generator.py.doc.md` reference is intentional — the
  package is thin and the generator is the main entry point.
