# `symbolic.py` — Symbolic Strategy

What this file does: generates proofs using sympy symbolic execution.

## Dependencies

- Imported by: `generator.py`, `strategies/__init__.py`, tests

## Public API

- `SymbolicStrategy()` — symbolic proof strategy
- `generate(function_code, properties)` → list[ProofStep]

## Notes

Translates Python functions to sympy expressions. Falls back to testing if translation fails.
