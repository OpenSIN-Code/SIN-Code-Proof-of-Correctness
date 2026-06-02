# `mcp_server.py` — MCP Server for POC

What this file does: exposes proof-of-correctness tools to AI agents via the Model Context Protocol.

## Dependencies

- Imported by: CLI, external MCP hosts
- Imports: `verifier` (ProofVerifier), `generator` (PropertyGenerator)

## Tools

- `verify_code(code, language="python")` — verify code correctness using formal proofs and property-based tests
- `generate_properties(code, language="python")` — generate property-based tests for given code

## Usage

```bash
python -m sin_code_poc.mcp_server
```

Requires `pip install -e ".[mcp]"`.

## Notes

Uses `mcp.server.fastmcp.FastMCP` for tool registration.
