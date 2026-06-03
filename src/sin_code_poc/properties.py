"""Property catalog and parsing for SIN-Code POC.

Defines the six built-in invariants (`pure`, `total`, `monotonic`,
`commutative`, `idempotent`, `no_exceptions`) and helpers to parse
the user-supplied `properties` string in `ProofGenerator.generate`.

Docs: properties.py.doc.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


# Sentinel arity used by PropertySpec to mean "any number of arguments".
_ARITY_ANY = -1

# Tokens that, if seen in a property spec, mean "use every registered property".
_ALL_TOKENS = {"all", "*", "default"}

# Fallback bucket for unknown tokens in parse_property_spec. Big enough
# to push unknown names past any registered name in `_ordered`.
_UNKNOWN_ORDER = 1_000_000


@dataclass(frozen=True)
class PropertySpec:
    """Metadata describing a single invariant.

    Attributes:
        name: Canonical property name (lowercase, snake_case).
        description: Human-readable description of the invariant.
        arity: Required parameter count for the target function
            (`1` for unary, `2` for binary, `_ARITY_ANY` for any arity).
        category: Logical category — `"determinism"`, `"termination"`,
            `"order"`, or `"structure"`.
        aliases: Alternative names a user might pass to the parser.
    """

    name: str
    description: str
    arity: int
    category: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


# ── Property catalog ───────────────────────────────────────────────────
# Each entry is the single source of truth for the property; tests and
# the report serializer both read from this dict.
PROPERTY_REGISTRY: dict[str, PropertySpec] = {
    "pure": PropertySpec(
        name="pure",
        description="Function has no side effects; same input always yields same output.",
        arity=_ARITY_ANY,
        category="determinism",
        aliases=("deterministic", "no_side_effects"),
    ),
    "total": PropertySpec(
        name="total",
        description="Function returns a value for every input in its domain.",
        arity=_ARITY_ANY,
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
        arity=_ARITY_ANY,
        category="termination",
        aliases=("never_raises", "no_raise"),
    ),
}


def list_properties() -> list[str]:
    """Return the canonical names of all registered properties (in registry order)."""
    return list(PROPERTY_REGISTRY)


def property_metadata(name: str) -> PropertySpec:
    """Look up a `PropertySpec` by canonical name or alias.

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


# Natural-language patterns used as a fallback when no explicit token matched.
# Ordered most-specific-first so idempotent/commutative win over generic "pure".
_NL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(idempotent|idemp)\b", re.I), "idempotent"),
    (re.compile(r"\b(commut|symmetric|symmetric)\b", re.I), "commutative"),
    (re.compile(r"\b(monoton|increasing|non[_ -]?decreasing)\b", re.I), "monotonic"),
    (re.compile(r"\b(pure|deterministic|no[_ -]side[_ -]effects?)\b", re.I), "pure"),
    (re.compile(r"\b(total|complete|always[_ -]?returns?)\b", re.I), "total"),
    (re.compile(r"\b(no[_ -]?(exception|raise|error|throw)|never[_ -]?raises?)\b", re.I), "no_exceptions"),
]


def parse_property_spec(spec: str) -> list[str]:
    """Parse the `properties` argument of `ProofGenerator.generate`.

    Accepts:

    * an empty string or `"all"` → every registered property;
    * a comma- or whitespace-separated list of property names/aliases →
      the matching canonical names, in registry order;
    * a natural-language sentence → properties matched by keyword.

    Unknown tokens are silently dropped to make the parser tolerant of
    user-supplied intent strings.
    """
    if not spec or not spec.strip():
        return list_properties()
    text = spec.strip().lower()
    if text in _ALL_TOKENS:
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
        # Alias lookup. We don't break out of the outer loop even after a match
        # because the next token may resolve to a different property; the
        # dedup `if spec_.name not in explicit` guard keeps the result stable.
        for spec_ in PROPERTY_REGISTRY.values():
            if token in spec_.aliases:
                if spec_.name not in explicit:
                    explicit.append(spec_.name)
                break
        # natural-language fragments are handled below

    if explicit:
        return _ordered(explicit)

    # No explicit token matched → try the natural-language patterns.
    nl_hits: list[str] = []
    for pattern, canonical in _NL_PATTERNS:
        if pattern.search(text) and canonical not in nl_hits:
            nl_hits.append(canonical)
    return _ordered(nl_hits) if nl_hits else list_properties()


def _ordered(names: list[str]) -> list[str]:
    """Sort a list of property names into registry declaration order.

    Unknown names sort to the end (after `_UNKNOWN_ORDER`) so they're easy
    to spot in logs without breaking deterministic ordering.
    """
    order = {n: i for i, n in enumerate(PROPERTY_REGISTRY)}
    return sorted(names, key=lambda n: order.get(n, _UNKNOWN_ORDER))


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

    Each checker accepts `(fn, x)` where `x` matches the property's
    `arity` (a single value for unary properties, a tuple for binary).
    """

    # ── Per-property checkers ──────────────────────────────────────────
    # Each is a closure over the function-under-test and the input.

    def _passes(fn, x):
        """Property: function returns (no assertion about value)."""
        try:
            fn(x)
            return True
        except Exception:
            return False

    def _no_raise(fn, x):
        """Property: function doesn't raise. Equivalent to `_passes` today;
        kept as a separate function so future refinement (e.g. allowlist
        of specific exception types) can target `no_exceptions` alone.
        """
        try:
            fn(x)
            return True
        except Exception:
            return False

    def _deterministic(fn, x):
        """Property: pure — same input gives same output across calls."""
        try:
            return fn(x) == fn(x)
        except Exception:
            return False

    def _monotonic(fn, x):
        """Property: monotonic — for `a <= b`, `fn(a) <= fn(b)`.

        When the input order is reversed we short-circuit True because
        the property is symmetric in the comparison direction.
        """
        a, b = x
        if a <= b:
            try:
                return fn(a) <= fn(b)
            except Exception:
                return False
        return True

    def _commutative(fn, x):
        """Property: commutative — `fn(a, b) == fn(b, a)`."""
        a, b = x
        try:
            return fn(a, b) == fn(b, a)
        except Exception:
            return False

    def _idempotent(fn, x):
        """Property: idempotent — `fn(fn(x)) == fn(x)`."""
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
