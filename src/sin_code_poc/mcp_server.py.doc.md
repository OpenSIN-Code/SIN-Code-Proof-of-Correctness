# mcp_server.py

FastMCP server exposing the proof-of-correctness pipeline as MCP tools.

## What it does

Wraps `ProofVerifier` and `PropertyGenerator` in a `FastMCP` server so
agents (opencode, claude-code) can call them over stdio. Two tools are
exposed: `verify_code` and `generate_properties`.

## Dependencies

- `verifier.py` — `ProofVerifier` (cross-checking proof steps)
- `generator.py` — `PropertyGenerator` (auto-suggest invariants)
- `mcp.server.fastmcp.FastMCP` — optional; the import is soft so the
  package remains usable without the MCP dependency.

## Tools

| Tool | Returns | Description |
|------|---------|-------------|
| `verify_code(code, language="python")` | JSON | Run multi-strategy verification and return the proof as JSON |
| `generate_properties(code, language="python")` | JSON | Auto-suggest invariants a user might want to check |

## Usage

```bash
python -m sin_code_poc.mcp_server
```

In opencode.json configure the MCP server; the tools become available
to agents.

## Known caveats

- Requires `pip install 'sin-code-poc[mcp]'` (or equivalent) for the
  `mcp` package; otherwise `main()` raises a clear `RuntimeError`.
- The server re-creates the verifier/generator per call — no caching.
