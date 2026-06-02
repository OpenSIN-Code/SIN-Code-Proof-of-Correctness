# `report.py` — Proof Report Formatter

What this file does: converts `Proof` objects into dict, markdown, and JSON for human-readable output.

## Dependencies

- Imported by: `__init__.py`, tests, CLI
- Imports: `proof` (Proof, ProofStep, Verdict)

## Public API

- `proof_to_dict(proof)` → dict
- `proof_to_markdown(proof)` → markdown string
- `proof_to_json(proof)` → JSON string

## Usage

```python
from sin_code_poc import ProofGenerator, proof_to_markdown
gen = ProofGenerator()
proof = gen.generate("def add(x, y): return x + y")
print(proof_to_markdown(proof))
```

## Notes

Markdown output includes a table of proof steps with verdict badges.
