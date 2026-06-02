# `__init__.py` — Strategies Package

What this file does: package-level exports for proof strategies.

## Dependencies

- Imported by: `generator.py`, tests

## Exports

- `StrategyRegistry` — registry for strategy implementations
- `get_strategy(name)` — retrieve a strategy by name
- `available_strategies()` — list registered strategy names

## Notes

Strategies are registered at import time in `generator.py`.
