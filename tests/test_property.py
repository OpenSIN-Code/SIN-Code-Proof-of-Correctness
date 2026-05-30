from sin_code_poc.property_generator import PropertyGenerator
from sin_code_poc.spec_compiler import SpecCompiler


def test_suggest_sort():
    pg = PropertyGenerator()
    props = pg.suggest({"name": "sort_list", "return_type": "list", "params": [{"name": "x"}], "docstring": ""})
    names = {p.name for p in props}
    assert "sorted_output" in names


def test_spec_compiler():
    sc = SpecCompiler()
    spec = sc.from_intent("returns non-negative integer", "compute")
    assert any("result >= 0" in p for p in spec.postconditions)
