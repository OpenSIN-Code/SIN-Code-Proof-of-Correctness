import json
import sys
import importlib.util
from pathlib import Path

import typer

from .property_generator import PropertyGenerator
from .spec_compiler import SpecCompiler
from .runtime_verifier import RuntimeVerifier

app = typer.Typer(help="SIN-Code Proof of Correctness CLI")


@app.command()
def suggest(module_path: Path, function_name: str):
    """Suggest properties for a function."""
    spec = importlib.util.spec_from_file_location("m", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, function_name)
    rv = RuntimeVerifier()
    sig = rv.extract_signature(fn)
    pg = PropertyGenerator()
    props = pg.suggest(sig)
    typer.echo(pg.render_hypothesis_test(function_name, props))


@app.command()
def verify(module_path: Path, function_name: str, max_examples: int = 50):
    """Run runtime verification on a function."""
    spec = importlib.util.spec_from_file_location("m", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, function_name)
    rv = RuntimeVerifier(max_examples=max_examples)
    sig = rv.extract_signature(fn)
    pg = PropertyGenerator()
    props = {p.name: (lambda _fn, _x, c=p.check_code: eval(c, {"f": _fn, "x": _x})) for p in pg.suggest(sig)}
    results = rv.verify_function(fn, props)
    typer.echo(json.dumps(results, indent=2))


@app.command()
def from_intent(intent: str, function_name: str):
    """Compile a natural-language intent into a spec test."""
    sc = SpecCompiler()
    spec = sc.from_intent(intent, function_name)
    typer.echo(sc.compile(spec))


if __name__ == "__main__":
    app()
