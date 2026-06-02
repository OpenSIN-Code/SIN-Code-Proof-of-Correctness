"""Property catalog and parsing for SIN-Code POC.

Defines the six built-in invariants (``pure``, ``total``, ``monotonic``,
``commutative``, ``idempotent``, ``no_exceptions``) and helpers to parse
the user-supplied ``properties`` string in :py:meth:`ProofGenerator.generate`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class PropertySpec:
    """Metadata describing a single invariant.

    Attributes:
        name: Canonical property name (lowercase, snake_case).
        description: Human-readable description of the invariant.
        arity: Required parameter count for the target function
            (``1`` for unary, ``2`` for binary, ``-1`` for any arity).
        category: Logical category — ``"determinism"``, ``"termination"``,
            ``"order"``, or ``"structure"``.
    """

    name: str
    description: str
    arity: int
    category: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


PROPERTY_REGISTRY: dict[str, PropertySpec] = {
    "pure": PropertySpec(
        name="pure",
        description="Function has no side effects; same input always yields same output.",
        arity=-1,
        category="determinism",
        aliases=("deterministic", "no_side_effects"),
    ),
    "total": PropertySpec(
        name="total",
        description="Function returns a value for every input in its domain.",
        arity=-1,
        category="termination",
        aliases=("no_hang",),
    ),
    "monotonic": PropertySpec(
        name="monotonic",
        description="Output is non-decreasing with respect to input ordering.",
        arity=1,
        category="order",
        aliases=("increasing", "non_decreasing"),
    ),
    "commutative": PropertySpec(
        name="commutative",
        description="f(a, b) == f(b, a) for all inputs.",
        arity=2,
        category="structure",
        aliases=("symmetric",),
    ),
    "idempotent": PropertySpec(
        name="idempotent",
        description="f(f(x)) == f(x) for all inputs.",
        arity=1,
        category="structure",
        aliases=("idemp",),
    ),
    "no_exceptions": PropertySpec(
        name="no_exceptions",
        description="Function never raises an exception on valid inputs.",
        arity=-1,
        category="termination",
        aliases=("never_raises", "no_raise"),
    ),
}


def list_properties() -> list[str]:
    """Return the canonical names of all registered properties."""
    return list(PROPERTY_REGISTRY)


def property_metadata(name: str) -> PropertySpec:
    """Look up a :class:`PropertySpec` by canonical name or alias.

    Raises:
        KeyError: If the name is not in the registry and matches no alias.
    """
    key = name.lower().strip()
    if key in PROPERTY_REGISTRY:
        return PROPERTY_REGISTRY[key]
    for spec in PROPERTY_REGISTRY.values():
        if key in spec.aliases:
            return spec
    raise KeyError(f"Unknown property: {name!r}")


_NL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(idempotent|idemp)\b", re.I), "idempotent"),
    (re.compile(r"\b(commut|symmetric|symmetric)\b", re.I), "commutative"),
    (re.compile(r"\b(monoton|increasing|non[_ -]?decreasing)\b", re.I), "monotonic"),
    (re.compile(r"\b(pure|deterministic|no[_ -]side[_ -]effects?)\b", re.I), "pure"),
    (re.compile(r"\b(total|complete|always[_ -]?returns?)\b", re.I), "total"),
    (re.compile(r"\b(no[_ -]?(exception|raise|error|throw)|never[_ -]?raises?)\b", re.I), "no_exceptions"),
]


def parse_property_spec(spec: str) -> list[str]:
    """Parse the ``properties`` argument of :py:meth:`ProofGenerator.generate`.

    Accepts:

    * an empty string or ``"all"`` → every registered property;
    * a comma- or whitespace-separated list of property names/aliases →
      the matching canonical names, in registry order;
    * a natural-language sentence → properties matched by keyword.

    Unknown tokens are silently dropped to make the parser tolerant of
    user-supplied intent strings.
    """
    if not spec or not spec.strip():
        return list_properties()
    text = spec.strip().lower()
    if text in {"all", "*", "default"}:
        return list_properties()

    explicit: list[str] = []
    for token in re.split(r"[\s,;|]+", text):
        token = token.strip()
        if not token:
            continue
        if token in PROPERTY_REGISTRY:
            if token not in explicit:
                explicit.append(token)
            continue
        matched = False
        for spec_ in PROPERTY_REGISTRY.values():
            if token in spec_.aliases:
                if spec_.name not in explicit:
                    explicit.append(spec_.name)
                matched = True
                break
        # natural-language fragments are handled below

    if explicit:
        return _ordered(explicit)

    nl_hits: list[str] = []
    for pattern, canonical in _NL_PATTERNS:
        if pattern.search(text) and canonical not in nl_hits:
            nl_hits.append(canonical)
    return _ordered(nl_hits) if nl_hits else list_properties()


def _ordered(names: list[str]) -> list[str]:
    order = {n: i for i, n in enumerate(PROPERTY_REGISTRY)}
    return sorted(names, key=lambda n: order.get(n, 1_000_000))


CheckerFn = Callable[[Callable[..., object], object], bool]


@dataclass
class _RuntimeChecker:
    """A simple property checker that takes a callable + a single example.

    Used by the testing strategy to evaluate invariants at runtime
    without invoking the full Hypothesis machinery on every property.
    """

    name: str
    arity: int
    check: CheckerFn


def runtime_checkers() -> dict[str, _RuntimeChecker]:
    """Return runtime checkers for the six registered properties.

    Each checker accepts ``(fn, x)`` where ``x`` matches the property's
    ``arity`` (a single value for unary properties, a tuple for binary).
    """

    def _passes(fn, x):
        try:
            fn(x)
            return True
        except Exception:
            return False

    def _no_raise(fn, x):
        try:
            fn(x)
            return True
        except Exception:
            return False

    def _deterministic(fn, x):
        try:
            return fn(x) == fn(x)
        except Exception:
            return False

    def _monotonic(fn, x):
        a, b = x
        if a <= b:
            try:
                return fn(a) <= fn(b)
            except Exception:
                return False
        return True

    def _commutative(fn, x):
        a, b = x
        try:
            return fn(a, b) == fn(b, a)
        except Exception:
            return False

    def _idempotent(fn, x):
        try:
            once = fn(x)
            twice = fn(once)
            return once == twice
        except Exception:
            return False

    return {
        "pure": _RuntimeChecker("pure", 1, _deterministic),
        "total": _RuntimeChecker("total", 1, _passes),
        "no_exceptions": _RuntimeChecker("no_exceptions", 1, _no_raise),
        "monotonic": _RuntimeChecker("monotonic", 1, _monotonic),
        "commutative": _RuntimeChecker("commutative", 2, _commutative),
        "idempotent": _RuntimeChecker("idempotent", 1, _idempotent),
    }
