# SIN-Code Proof of Correctness (POC)

Forces agents to write formal specifications before code. Auto-TLA+ / Lean for the real world.

## Features
- Property suggestion from function signatures
- Hypothesis test generation
- Runtime verification with configurable example counts
- Natural-language intent compilation
- Static signature extraction via AST

## Install
```bash
pip install -e .
```

## Usage
```bash
poc suggest my_module.py my_function        # suggest properties
poc verify my_module.py my_function         # run verification
poc from-intent "returns sorted list" sort  # compile intent to spec
```

## Architecture
- `PropertyGenerator`: Suggests properties based on heuristics
- `SpecCompiler`: Translates specifications to test code
- `RuntimeVerifier`: Executes hypothesis tests and reports violations
