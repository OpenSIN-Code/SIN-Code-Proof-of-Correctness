# report.py

Serializers that turn a `Proof` into dict / JSON / Markdown.

## What it does

Three pure-function converters used by the CLI, MCP server, and tests
to produce different output formats from a `Proof`. No I/O, no
configuration — just transformation.

## Dependencies

- `proof.py` — `Proof`, `ProofStep`

## Public API

| Function | Returns | Use case |
|----------|---------|----------|
| `proof_to_dict(proof)` | `dict` | Programmatic consumption |
| `proof_to_json(proof, indent=2)` | `str` | Stash/print/log |
| `proof_to_markdown(proof)` | `str` | PR comments, reports |

## Markdown layout

The Markdown report includes a header block (function, strategy,
confidence, success), a "Properties Checked" bullet list, and a numbered
"Steps" list with verdict emoji (`✅ / ❌ / ❓ / ⏭️`) and details.

## Usage

```python
from sin_code_poc.report import proof_to_markdown
print(proof_to_markdown(proof))
```

## Known caveats

- The Markdown is hard-coded to English; localization is out of scope.
- `proof_to_json` uses `ensure_ascii=False` so non-ASCII content in
  `details` round-trips cleanly.
