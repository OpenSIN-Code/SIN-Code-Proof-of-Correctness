# Installation — `sin-code-poc`

## Requirements

- Python **3.11+**
- `pip` (or `uv`/`pipx`)
- Git (for repository-aware features)

## Install from source (recommended during preview)

```bash
git clone https://github.com/OpenSIN-Code/SIN-Code-Proof-of-Correctness.git
cd SIN-Code-Proof-of-Correctness
pip install -e .
```

This installs the importable package `sin_code_poc`.

## Install into an isolated environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

## Optional: MCP server support

The MCP server requires the optional `mcp` dependency:

```bash
pip install -e ".[mcp]"
```

## Verify the installation

```bash
pytest -q
python -c "from sin_code_poc import ProofGenerator; print('OK')"
```

## Uninstall

```bash
pip uninstall sin-code-poc
```
