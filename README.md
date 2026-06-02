# SIN-Code Proof of Correctness (POC)

> Lightweight, practical formal verification for AI-generated code — property-based testing driven by function signatures and natural-language intent.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

Part of the [SIN-Code](https://github.com/OpenSIN-Code) agent-engineering stack. Install all subsystems together via the [SIN-Code Bundle](https://github.com/OpenSIN-Code/SIN-Code-Bundle).

## Features

- **Property generator** — infers candidate invariants (idempotence, monotonicity, length-preservation, sorted output, reversibility, purity, …) from a function's signature and name
- **Runtime verifier** — executes properties with Hypothesis and reports `PASS` / `FAIL` / `SKIPPED` per property (no unsafe `eval`)
- **Multi-strategy engine** — auto-selects between symbolic (sympy), testing (hypothesis), and typecheck (mypy) strategies
- **Spec compiler** — turns declarative pre/post-conditions, or natural-language intent, into runnable property tests
- **MCP server** — expose proof generation and verification to AI agents via the Model Context Protocol

## Installation

```bash
pip install -e .
```

Optional MCP server support:
```bash
pip install -e ".[mcp]"
```

See [INSTALL.md](./INSTALL.md) for detailed setup instructions.

## Usage

### Library

```python
from sin_code_poc import ProofGenerator

# Auto-select best strategy
gen = ProofGenerator(strategy="auto")
proof = gen.generate("def add(x, y): return x + y")

print(proof.is_success())   # True
print(proof.confidence)     # 0.0–1.0
print(proof.strategy_used)  # "symbolic" or "testing"

# Inspect proof steps
for step in proof.steps:
    print(step.description, step.verdict)

# Verify a generated proof
assert gen.verify_proof(proof)
```

### Generate with specific properties

```python
proof = gen.generate(
    "def sort_items(items): return sorted(items)",
    properties="sorted, non-negative"
)
```

## Testing

```bash
pytest -q
```

## MCP Server

Run the MCP server for agent integration:

```bash
python -m sin_code_poc.mcp_server
```

Tools exposed:
- `verify_code(code, language="python")` — verify code correctness using formal proofs and property-based tests
- `generate_properties(code, language="python")` — generate property-based tests for given code

## Integration

POC is designed to work as part of the SIN-Code ecosystem:

- **SIN-Code Bundle** — orchestrates all subsystems from a single CLI (`sin`)
- **Verification Oracle** — feed proof results into the broader verification pipeline
- **Orchestration** — run proof generation as a task in a multi-agent workflow
- **Review Interface** — attach proof reports to code reviews

## Documentation

- [INSTALL.md](./INSTALL.md)
- [docs/USAGE.md](./docs/USAGE.md)
- [docs/CONFIGURATION.md](./docs/CONFIGURATION.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CHANGELOG.md](./CHANGELOG.md)

## License

MIT — see [LICENSE](./LICENSE).
