"""Report generation for SIN-Code POC.

Convert proof objects into dict, JSON, or Markdown representations.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from sin_code_poc.proof import Proof, ProofStep


def proof_to_dict(proof: Proof) -> dict[str, Any]:
    """Convert a proof to a plain dictionary."""
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
    """Convert a proof to a JSON string."""
    return json.dumps(proof_to_dict(proof), indent=indent, ensure_ascii=False)


def proof_to_markdown(proof: Proof) -> str:
    """Convert a proof to a Markdown report."""
    lines = [
        "# Proof of Correctness Report",
        "",
        f"**Function:** `{proof.function_signature}`",
        f"**Strategy:** `{proof.strategy_used}`",
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
        lines.append("- *(none specified)*")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    for i, step in enumerate(proof.steps, 1):
        emoji = {
            "passed": "✅",
            "failed": "❌",
            "unknown": "❓",
            "skipped": "⏭️",
        }.get(step.verdict.value, "❓")
        lines.append(f"{emoji} **Step {i}:** {step.description}")
        lines.append(f"   - Verdict: `{step.verdict.value}`")
        lines.append(f"   - Strategy: `{step.strategy}`")
        if step.details:
            lines.append(f"   - Details: {step.details}")
        lines.append("")
    return "\n".join(lines)
