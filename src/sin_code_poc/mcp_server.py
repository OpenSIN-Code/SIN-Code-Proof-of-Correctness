"""MCP server for agent integration.

Docs: mcp_server.py.doc.md
"""
from __future__ import annotations

import json

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    # Soft import so the rest of the package remains usable without the MCP
    # dependency installed. `main()` raises a clear error at runtime instead.
    FastMCP = None

from .verifier import ProofVerifier
from .generator import PropertyGenerator


# Server identity reported to MCP clients in the initialize handshake.
_SERVER_NAME = "sin-code-poc"


def main():
    """Build the FastMCP server and start it on stdio (blocks).

    Raises:
        RuntimeError: If the optional `mcp` package is not installed.
    """
    if FastMCP is None:
        raise RuntimeError("mcp package not installed. Install with: pip install 'sin-code-poc[mcp]'")

    mcp = FastMCP(_SERVER_NAME)

    @mcp.tool()
    def verify_code(code: str, language: str = "python") -> str:
        """Verify code correctness using formal proofs and property-based tests.

        Args:
            code: Source code to verify (Python today; other languages may
                degrade gracefully depending on strategy support).
            language: Source language tag (default: `python`).

        Returns:
            JSON-encoded proof with verdict, confidence, and step trace.
        """
        verifier = ProofVerifier()
        return json.dumps(verifier.verify(code, language=language), indent=2)

    @mcp.tool()
    def generate_properties(code: str, language: str = "python") -> str:
        """Generate property-based tests for given code.

        Returns a JSON list of suggested property names from the built-in
        catalog (`pure`, `total`, `commutative`, ...).
        """
        generator = PropertyGenerator()
        return json.dumps(generator.generate(code, language=language), indent=2)

    mcp.run()


if __name__ == "__main__":
    main()
