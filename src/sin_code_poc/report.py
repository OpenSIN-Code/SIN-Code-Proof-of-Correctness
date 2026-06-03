"""Report generation for SIN-Code POC.

Convert proof objects into dict, JSON, or Markdown representations.

Docs: report.py.doc.md
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from sin_code_poc.proof import Proof, ProofStep


# Emoji map for the Markdown verdict bullets. Kept in module scope so the
# Unicode literals are easy to find/replace (e.g. for terminal-only logs).
_VERDICT_EMOJI = {
    "passed": "✅",
    "failed": "❌",
    "unknown": "❓",
    "skipped": "⏭️",
}
_DEFAULT_EMOJI = "❓"


def proof_to_dict(proof: Proof) -> dict[str, Any]:
    """Convert a proof to a plain dictionary.

    Note: `properties_requested` is materialized from a tuple to a list
    because most JSON consumers expect mutable sequences. The verdict
    enum is converted to its string value (not the enum name) so the
    output is `passed`, not `Verdict.PASSED`.
    """
    return {
        "function_signature": proof.function_signature,
        "properties_requested": list(proof.properties_requested),
        "strategy_used": proof.strategy_used,
        "confidence": proof.confidence,
        "success": proof.is_success(),
        "steps": [
            {
                "description": step.description,
                "verdict": step.verdict.value,
                "details": step.details,
                "strategy": step.strategy,
            }
            for step in proof.steps
        ],
    }


def proof_to_json(proof: Proof, indent: int = 2) -> str:
    r"""Convert a proof to a JSON string.

    `ensure_ascii=False` so non-ASCII content in `details` (e.g. error
    messages from non-English tools) round-trips through `json.loads`
    without `\uXXXX` escapes.
    """
    return json.dumps(proof_to_dict(proof), indent=indent, ensure_ascii=False)


def proof_to_markdown(proof: Proof) -> str:
    """Convert a proof to a Markdown report.

    Layout: header block (function, strategy, confidence, success) →
    "Properties Checked" bullet list → numbered "Steps" list with verdict
    emoji. Each step is followed by an indented sub-bullet for verdict,
    strategy, and (if present) details.
    """
    lines = [
        "# Proof of Correctness Report",
        "",
        f"**Function:** `{proof.function_signature}`",
        f"**Strategy:** `{proof.strategy_used}`",
        # Confidence is rendered with two decimals to keep the table width stable.
        f"**Confidence:** {proof.confidence:.2f}",
        f"**Success:** {proof.is_success()}",
        "",
        "## Properties Checked",
        "",
    ]
    if proof.properties_requested:
        for prop in proof.properties_requested:
            lines.append(f"- {prop}")
    else:
        # Empty property list means "everything"; surface that explicitly
        # rather than printing a misleading bullet.
        lines.append("- *(none specified)*")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    for i, step in enumerate(proof.steps, 1):
        emoji = _VERDICT_EMOJI.get(step.verdict.value, _DEFAULT_EMOJI)
        lines.append(f"{emoji} **Step {i}:** {step.description}")
        lines.append(f"   - Verdict: `{step.verdict.value}`")
        lines.append(f"   - Strategy: `{step.strategy}`")
        if step.details:
            lines.append(f"   - Details: {step.details}")
        lines.append("")
    return "\n".join(lines)
