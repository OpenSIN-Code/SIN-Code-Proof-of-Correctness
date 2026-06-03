"""SIN-Code Proof of Correctness (POC).

Multi-strategy proof-of-correctness for Python functions. Combines
symbolic execution (sympy), property-based testing (hypothesis), and
static type checking (mypy) to verify common invariants.

Docs: __init__.py.doc.md
"""

from sin_code_poc.proof import Proof, ProofStep, Verdict
from sin_code_poc.generator import ProofGenerator
from sin_code_poc.properties import (
    PROPERTY_REGISTRY,
    list_properties,
    parse_property_spec,
    property_metadata,
)
from sin_code_poc.report import proof_to_dict, proof_to_markdown, proof_to_json

__version__ = "0.1.0"

__all__ = [
    "ProofGenerator",
    "Proof",
    "ProofStep",
    "Verdict",
    "PROPERTY_REGISTRY",
    "list_properties",
    "parse_property_spec",
    "property_metadata",
    "proof_to_dict",
    "proof_to_markdown",
    "proof_to_json",
    "__version__",
]
