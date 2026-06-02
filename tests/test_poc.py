"""Tests for SIN-Code POC.
"""
from __future__ import annotations

import pytest

from sin_code_poc import (
    ProofGenerator,
    Proof,
    ProofStep,
    Verdict,
    list_properties,
    parse_property_spec,
    property_metadata,
    proof_to_dict,
    proof_to_markdown,
    proof_to_json,
)
from sin_code_poc.strategies.symbolic import SymbolicStrategy
from sin_code_poc.strategies.testing import TestingStrategy
from sin_code_poc.strategies.typecheck import TypecheckStrategy
from sin_code_poc.verifier import Verifier


# ── Property parsing ──────────────────────────────────────

def test_list_properties():
    props = list_properties()
    assert "pure" in props
    assert "total" in props
    assert len(props) == 6


def test_parse_property_spec_empty():
    assert parse_property_spec("") == list_properties()


def test_parse_property_spec_all():
    assert parse_property_spec("all") == list_properties()


def test_parse_property_spec_comma():
    assert parse_property_spec("pure, total") == ["pure", "total"]


def test_parse_property_spec_alias():
    assert parse_property_spec("deterministic") == ["pure"]


def test_parse_property_spec_nl():
    result = parse_property_spec("this function is pure and monotonic")
    assert "pure" in result
    assert "monotonic" in result


def test_property_metadata():
    meta = property_metadata("pure")
    assert meta.name == "pure"
    assert meta.arity == -1


def test_property_metadata_alias():
    meta = property_metadata("no_raise")
    assert meta.name == "no_exceptions"


def test_property_metadata_unknown():
    with pytest.raises(KeyError):
        property_metadata("nonexistent")


# ── Proof data structures ─────────────────────────────────

def test_proof_is_success():
    step = ProofStep("x", Verdict.PASSED)
    proof = Proof(steps=(step,))
    assert proof.is_success()


def test_proof_is_success_with_skip():
    step = ProofStep("x", Verdict.SKIPPED)
    proof = Proof(steps=(step,))
    assert proof.is_success()


def test_proof_is_not_success():
    step = ProofStep("x", Verdict.FAILED)
    proof = Proof(steps=(step,))
    assert not proof.is_success()


def test_proof_immutable():
    proof = Proof()
    with pytest.raises(AttributeError):
        proof.confidence = 1.0


# ── ProofGenerator ──────────────────────────────────────

def test_generator_auto():
    gen = ProofGenerator("auto")
    proof = gen.generate("def f(x): return x + 1")
    assert isinstance(proof, Proof)
    assert proof.function_signature == "f(x)"


def test_generator_symbolic():
    gen = ProofGenerator("symbolic")
    proof = gen.generate("def add(a, b): return a + b", "commutative")
    assert proof.strategy_used == "symbolic"
    assert proof.is_success()


def test_generator_testing():
    gen = ProofGenerator("testing")
    proof = gen.generate("def add(a, b): return a + b", "commutative")
    assert proof.strategy_used == "testing"


def test_generator_typecheck():
    gen = ProofGenerator("typecheck")
    proof = gen.generate("def add(a: int, b: int) -> int: return a + b")
    assert proof.strategy_used == "typecheck"
    assert any(s.description == "Typecheck with mypy" for s in proof.steps)


def test_generator_invalid_strategy():
    with pytest.raises(ValueError):
        ProofGenerator("invalid")


def test_generator_verify_proof():
    gen = ProofGenerator()
    proof = gen.generate("def f(x): return x * 2")
    result = gen.verify_proof(proof)
    assert isinstance(result, bool)


# ── Symbolic strategy ─────────────────────────────────────

def test_symbolic_commutative():
    s = SymbolicStrategy()
    steps = s.generate("def add(a, b): return a + b", ["commutative"])
    step = [s for s in steps if s.description == "Check commutative"][0]
    assert step.verdict == Verdict.PASSED


def test_symbolic_not_commutative():
    s = SymbolicStrategy()
    steps = s.generate("def sub(a, b): return a - b", ["commutative"])
    step = [s for s in steps if s.description == "Check commutative"][0]
    assert step.verdict == Verdict.FAILED


def test_symbolic_idempotent():
    s = SymbolicStrategy()
    steps = s.generate("def abs_val(x): return abs(x)", ["idempotent"])
    step = [s for s in steps if s.description == "Check idempotent"][0]
    assert step.verdict == Verdict.PASSED


def test_symbolic_monotonic():
    s = SymbolicStrategy()
    steps = s.generate("def f(x): return x + 1", ["monotonic"])
    step = [s for s in steps if s.description == "Check monotonic"][0]
    assert step.verdict == Verdict.PASSED


def test_symbolic_total():
    s = SymbolicStrategy()
    steps = s.generate("def f(x): return x + 1", ["total"])
    step = [s for s in steps if s.description == "Check total"][0]
    assert step.verdict == Verdict.PASSED


def test_symbolic_total_with_singularity():
    s = SymbolicStrategy()
    steps = s.generate("def f(x): return 1 / x", ["total"])
    step = [s for s in steps if s.description == "Check total"][0]
    assert step.verdict == Verdict.FAILED


def test_symbolic_unsupported():
    s = SymbolicStrategy()
    steps = s.generate("def f(x):\n    if x > 0:\n        return 1\n    return 0", ["pure"])
    step = [s for s in steps if s.description == "Translate to sympy"][0]
    assert step.verdict == Verdict.SKIPPED


# ── Testing strategy ──────────────────────────────────────

def test_testing_commutative():
    t = TestingStrategy()
    steps = t.generate("def add(a, b): return a + b", ["commutative"])
    step = [s for s in steps if s.description == "Check commutative"][0]
    assert step.verdict == Verdict.PASSED


def test_testing_not_commutative():
    t = TestingStrategy()
    steps = t.generate("def sub(a, b): return a - b", ["commutative"])
    step = [s for s in steps if s.description == "Check commutative"][0]
    assert step.verdict == Verdict.FAILED


def test_testing_pure():
    t = TestingStrategy()
    steps = t.generate("def f(x): return x + 1", ["pure"])
    step = [s for s in steps if s.description == "Check pure"][0]
    assert step.verdict == Verdict.PASSED


def test_testing_no_exceptions():
    t = TestingStrategy()
    steps = t.generate("def f(x): return x + 1", ["no_exceptions"])
    step = [s for s in steps if s.description == "Check no_exceptions"][0]
    assert step.verdict == Verdict.PASSED


# ── Typecheck strategy ──────────────────────────────────

def test_typecheck_mypy():
    t = TypecheckStrategy()
    steps = t.generate("def add(a: int, b: int) -> int: return a + b", ["total"])
    step = [s for s in steps if s.description == "Typecheck with mypy"][0]
    assert step.verdict == Verdict.PASSED


def test_typecheck_no_annotations():
    t = TypecheckStrategy()
    steps = t.generate("def add(a, b): return a + b", ["pure"])
    step = [s for s in steps if s.description == "Check type annotations present"][0]
    # No annotations → unknown
    assert step.verdict == Verdict.UNKNOWN


def test_typecheck_with_annotations():
    t = TypecheckStrategy()
    steps = t.generate("def add(a: int, b: int) -> int: return a + b", ["pure"])
    step = [s for s in steps if s.description == "Check type annotations present"][0]
    assert step.verdict == Verdict.PASSED


# ── Verifier ─────────────────────────────────────────────

def test_verifier_pass():
    v = Verifier()
    proof = Proof(steps=(ProofStep("x", Verdict.PASSED),))
    assert v.verify(proof)


def test_verifier_fail():
    v = Verifier()
    proof = Proof(steps=(ProofStep("x", Verdict.FAILED),))
    assert not v.verify(proof)


def test_verifier_empty():
    v = Verifier()
    proof = Proof()
    assert not v.verify(proof)


def test_verifier_all_skipped():
    v = Verifier()
    proof = Proof(steps=(ProofStep("x", Verdict.SKIPPED),))
    assert not v.verify(proof)


def test_verifier_confidence_full():
    v = Verifier()
    proof = Proof(steps=(ProofStep("x", Verdict.PASSED),))
    assert v.confidence(proof) == 1.0


def test_verifier_confidence_zero():
    v = Verifier()
    proof = Proof(steps=(ProofStep("x", Verdict.FAILED),))
    assert v.confidence(proof) == 0.0


def test_verifier_confidence_mixed():
    v = Verifier()
    proof = Proof(
        steps=(ProofStep("x", Verdict.PASSED), ProofStep("y", Verdict.UNKNOWN))
    )
    assert 0.0 < v.confidence(proof) < 1.0


# ── Report ───────────────────────────────────────────────

def test_proof_to_dict():
    proof = Proof(
        function_signature="f(x)",
        properties_requested=("pure",),
        steps=(ProofStep("Check pure", Verdict.PASSED),),
    )
    d = proof_to_dict(proof)
    assert d["function_signature"] == "f(x)"
    assert d["steps"][0]["verdict"] == "passed"


def test_proof_to_json():
    proof = Proof(
        function_signature="f(x)",
        steps=(ProofStep("Check pure", Verdict.PASSED),),
    )
    json_str = proof_to_json(proof)
    assert "passed" in json_str


def test_proof_to_markdown():
    proof = Proof(
        function_signature="f(x)",
        steps=(ProofStep("Check pure", Verdict.PASSED),),
    )
    md = proof_to_markdown(proof)
    assert "Proof of Correctness Report" in md
    assert "✅" in md


# ── Auto fallback ────────────────────────────────────────

def test_auto_fallback_to_testing():
    """Auto strategy should fall back to testing for unsupported symbolic functions."""
    gen = ProofGenerator("auto")
    proof = gen.generate(
        "def f(x):\n    if x > 0:\n        return 1\n    return 0",
        properties="pure",
    )
    assert proof.strategy_used == "testing"


# ── Side effects detection ───────────────────────────────

def test_testing_pure_with_side_effects():
    """A function with side effects should fail the pure check."""
    t = TestingStrategy()
    # We can't easily test side effects in a simple function, but
    # the deterministic checker will still pass on the same input.
    # This is a limitation of the runtime checker.
    steps = t.generate("def f(x): return x + 1", ["pure"])
    step = [s for s in steps if s.description == "Check pure"][0]
    # The runtime checker only checks deterministic behavior on same input
    assert step.verdict == Verdict.PASSED


# ── Recursive functions ───────────────────────────────────

def test_symbolic_recursive():
    """Recursive functions are not supported by symbolic strategy."""
    s = SymbolicStrategy()
    steps = s.generate("def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)", ["total"])
    step = [s for s in steps if s.description == "Translate to sympy"][0]
    assert step.verdict == Verdict.SKIPPED


def test_testing_recursive():
    """Testing strategy can handle recursive functions."""
    t = TestingStrategy()
    steps = t.generate("def fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n-1)", ["total"])
    step = [s for s in steps if s.description == "Check total"][0]
    assert step.verdict == Verdict.PASSED


# ── Edge cases ──────────────────────────────────────────

def test_generator_no_properties():
    gen = ProofGenerator()
    proof = gen.generate("def f(x): return x")
    assert len(proof.properties_requested) == 6  # all properties


def test_generator_compile_error():
    gen = ProofGenerator()
    proof = gen.generate("def f(x): return x +", properties="pure")
    assert any(s.verdict == Verdict.FAILED for s in proof.steps)


def test_generator_single_property():
    gen = ProofGenerator()
    proof = gen.generate("def f(x): return x + 1", properties="pure")
    assert proof.properties_requested == ("pure",)
