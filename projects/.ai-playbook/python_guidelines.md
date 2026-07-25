# Python Development Guidelines

Python-specific development patterns observed across projects.
Instruction files reference numbered clauses here rather than restating full text.

Language-agnostic agent workflow lessons live in `~/Projects/.ai-playbook/agent_workflow_guidelines.md`.

## 1. Test Tabular Data Construction

When constructing CSV, TSV, or fixed-width test data for any parser or reader test:

1.1. Verify column alignment immediately by printing the parsed row as a dict:
`print(dict(zip(header, row)))`. Do this as the first debug step, not after guessing.

1.2. Copy working test rows from existing tests and modify values only — never construct
tabular rows from scratch. Hand-counting delimiters is the single biggest source of wasted
debug iterations in parser tests.

1.3. When a test row fails, print the parsed dict first. Do NOT add or remove delimiters
blindly — find out where fields actually land.

1.4. Assert column counts explicitly in test setup: `assert len(row) == expected_count`.
This catches misalignment before it manifests as a wrong-value bug.

## 2. Post-Extraction Cleanup (Python)

See `agent_workflow_guidelines.md #4` for the general rule. Python-specific commands:

2.1. Run `ruff check <source_file> --select=F401,F811` on the source module before
committing. F401 catches unused imports left behind; F811 catches redefined functions
from incomplete removal.

2.2. Search for duplicate function definitions in the source file:
`grep -n "def <function_name>" <source_file>`.

## 3. Avoid `__getattr__` Delegation in Wrapper Dataclasses

Never use `__getattr__` to delegate attribute access from a wrapper to an inner object:

```python
# ❌ WRONG — __getattr__ delegation breaks type checkers
@dataclass
class AcquisitionContext:
    acq: CryptoAcquisition
    tx_key: str
    def __getattr__(self, name: str):  # type: Any
        return getattr(self.acq, name)  # mypy/pyright cannot resolve .date, .asset, etc.
```

Type checkers (`mypy`, `pyright`) cannot resolve delegated attributes through `__getattr__`,
turning every `wrapper.date` access into an unverifiable operation. Callers also have no IDE
completion for the proxied fields.

**Fix:** Add the extra fields directly to the domain entity or to a separate named parameter.
If the domain entity is immutable and processing metadata must be attached at a different
layer, use a `NamedTuple` or a plain `@dataclass` with all fields declared explicitly — never
delegate via `__getattr__`.

```python
# ✅ GOOD — all fields explicit, type-checker verified
@dataclass(frozen=True)
class CryptoAcquisition:
    date: str
    asset: str
    tx_key: str            # processing metadata co-located with domain data
    source_row_index: int
```

## 4. Monkeypatch Module-Level Path Constants in Unit Tests

When production code uses a module-level path constant resolved at import time:

```python
# production module
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DECISION_POINTS_DIR = _REPO_ROOT / "docs/config/decision_points"
```

Unit tests that exercise functions depending on that constant must monkeypatch the constant
itself, not place real files at the live path. Without patching, tests silently depend on a
real filesystem artifact; they fail with a cryptic `FileNotFoundError` on a fresh checkout
or when the file is moved, rather than with a meaningful test failure.

```python
# ✅ GOOD
def test_loads_flags(monkeypatch, tmp_path):
    (tmp_path / "2025.toml").write_text("[meta]\nfiscal_year = 2025\n[countries.PT]\nexclude_loan_repayment_gains = true\n")
    monkeypatch.setattr(config_module, "_DECISION_POINTS_DIR", tmp_path)
    result = config_module._load_decision_points_flags("PT", 2025, logger)
    assert result["exclude_loan_repayment_gains"] is True
```

This extends the `Path(__file__)` pattern in §4 to constants that are computed
once at module load — they are equally fragile and require the same monkeypatch isolation.

## 5. Resource-Release Flag Must Be Set After Successful Release Only

When a boolean flag signals that a resource was successfully released, only set it inside
the success branch — never unconditionally after a swallowed exception:

```python
# ❌ WRONG — flag set even when close() raised and was swallowed
try:
    resource.close()
except Exception as e:
    logger.error("close failed: %s", e)
released = True  # resource may still be open!

# ✅ CORRECT — flag only on confirmed release
try:
    resource.close()
    released = True
except Exception as e:
    logger.error("close failed: %s", e)
```

Setting the flag unconditionally after a swallowed close exception means downstream
`finally` blocks skip the cleanup path, creating a resource leak.

## 6. Module-Level Logger — Never Define `getLogger` Per-Call

Define the logger once at module level. Never call `logging.getLogger(__name__)` inside a
helper function body, even though the call is cached and thread-safe:

```python
# ❌ WRONG — redundant call on every invocation, especially costly in hot loops
def _process_row(row):
    logger = logging.getLogger(__name__)
    logger.warning("bad row: %s", row)

# ✅ CORRECT — module constant, defined once at import time
logger = logging.getLogger(__name__)

def _process_row(row):
    logger.warning("bad row: %s", row)
```

## 7. Encode In-Place Mutation Contracts in Function Names

When a helper's primary effect is mutating caller-owned collections (rather than returning a
value), encode that contract in the name — e.g. suffix with `_inplace`:

```python
# ❌ UNCLEAR — caller may assume the return value is the complete result
def _match_consumption_to_lots(pool, ...):
    ...  # also mutates pool, carryover_cost, partial_tx_keys

# ✅ CLEAR — mutation is auditable at the call site
def _consume_against_pool_inplace(pool, ...):
    ...  # caller knows pool is being modified
```

This prevents callers from treating the return value as the complete picture and missing
the side effects on the passed-in collections.

## 8. Dict Key Shape Must Match Between Build and Lookup Sites

When building a lookup dict with composite tuple keys, every lookup site must construct
the exact same key shape. A type annotation `dict[str | tuple[str, str], Decimal]` permits
both shapes but does not enforce consistency — a lookup using a plain `str` against a dict
built with `(str, str)` tuple keys will always miss, silently returning the default value
(e.g. zero).

```python
# ❌ BUG — dict built with (tx_key, platform) tuples, looked up with plain string
carryover = {(tx_key, platform): cost}          # build
result = carryover.get(acq.tx_key, Decimal(0))  # lookup always returns 0

# ✅ CORRECT — key shape is consistent
def _has_carryover_for_tx_key(d: dict, tx_key: str) -> bool:
    return any(isinstance(k, tuple) and k[0] == tx_key for k in d)
```

Mitigation: encapsulate key construction in a named helper so build and lookup share one
definition. Avoid union-typed keys (`dict[str | tuple, ...]`) as they create valid-looking
but semantically inconsistent lookups.

## 9. Don't Re-export Private Helpers from Package `__init__.py`

Underscore-prefixed functions are module-internal by convention. Re-exporting them from
`__init__.py` creates pseudo-public API for internals, forces callers to depend on the
package path rather than the actual module, and obscures where the code lives.

```python
# ❌ BAD — crypto_fifo/__init__.py exposes internals
from .parsing import _dedup_by_tx_key, _order_platforms_for_transfers  # private!

# ✅ CORRECT — callers import from the defining submodule directly
from myapp.submodule.parsing import _dedup_by_tx_key
```

Rule: `__init__.py` should only re-export symbols listed in `__all__`. Private helpers
must be imported directly from their defining submodule.

## 10. Pytest Test Method Names Must Start with `test_`

Pytest collects test functions and methods by name prefix only. Methods named after the
behaviour they describe (for example `finds_funding_fee_event_with_timestamp`,
`returns_empty_when_labels_missing`) without a `test_` prefix are silently skipped —
pytest reports `0 collected` and the RED phase never executes, so a GREEN implementation
can pass vacuously or a missing import can go undetected.

```python
# ❌ WRONG — pytest collects zero of these
class TestDerivativesThScanner:
    def finds_funding_fee_event_with_timestamp(self, tmp_path):
        ...

    def returns_empty_when_labels_missing(self):
        ...
```

```python
# ✅ CORRECT — every test method is prefixed
class TestDerivativesThScanner:
    def test_finds_funding_fee_event_with_timestamp(self, tmp_path):
        ...

    def test_returns_empty_when_labels_missing(self):
        ...
```

When transcribing test names from a plan or pseudocode that uses descriptive non-prefixed
names, prefix every method with `test_` at write time. After writing the first batch, run
`uv run pytest <path> --collect-only` (or just `uv run pytest <path> -v`) and confirm the
expected test count appears in the collection line before implementing.

## 11. Build Tabular Test Rows with `csv.DictWriter`, Not Hand-Aligned String Literals

When a test fixture needs a CSV with many columns (the Koinly TH export has 15+ columns),
do not write the rows as inline string literals. Long single-line CSV rows exceed line-length
linters (E501), are hard to modify when a column shifts, and invite column-count drift that
python_guidelines §1 was written to prevent.

```python
# ❌ BRITTLE — long literal, E501 violations, hard to modify
path.write_text(
    "Date,Type,Tag,Sending Wallet,Sent Amount,Sent Currency,Receiving Wallet,Received Amount,Received Currency,Description\n"
    "2025-01-24 20:00:00 UTC,crypto_withdrawal,Funding fee,ByBit,0.08838575,USDT,,,\n"
)
```

```python
# ✅ ROBUST — rows as dicts, header written once, csv handles quoting and alignment
def _write_th_csv(path, rows):
    with path.open("w", newline="") as f:
        f.write("Transaction report 2025\n\n")  # Koinly preamble
        fieldnames = ["Date", "Type", "Tag", "Sending Wallet", "Sent Amount",
                      "Sent Currency", "Receiving Wallet", "Received Amount",
                      "Received Currency", "Description"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
```

DictWriter guarantees every row matches the declared header (extra keys raise, missing
keys are written empty), eliminates alignment-by-hand, and keeps each test row readable as
a dict literal.

## 12. Verify Pipeline Stage Ordering With monkeypatch Spies, Not Full Mocks

When an integration test needs to assert that stage A runs before stage B before stage C in a multi-step pipeline (for example: validate → dedup → split), do not mock the stages themselves — that discards the real integration coverage and only proves the mocks were called in order. Instead, wrap each real stage with a thin monkeypatch spy that records the call order, then delegates to the original function.

```python
# ✅ Spy pattern — real stages run, call order is captured
def test_dedup_runs_after_validation_before_split(monkeypatch):
    call_order = []

    def _spy_validate(name, fn):
        def wrapper(*args, **kwargs):
            call_order.append(name)
            return fn(*args, **kwargs)
        return wrapper

    import tax_reporting.application.crypto_reporting as mod
    from tax_reporting.application.crypto.derivatives_dedup import apply_derivatives_dedup

    monkeypatch.setattr(
        mod, "_validate_capital_entries_have_valid_countries",
        _spy_validate("validate", mod._validate_capital_entries_have_valid_countries),
    )
    monkeypatch.setattr(
        mod, "apply_derivatives_dedup",
        _spy_validate("dedup", apply_derivatives_dedup),
    )
    monkeypatch.setattr(
        mod, "_split_ogr_index",
        _spy_validate("split", mod._split_ogr_index),
    )

    mod.load_koinly_crypto_report(...)  # real call with real fixture

    assert call_order.index("validate") < call_order.index("dedup") < call_order.index("split")
```

**Why spies, not mocks:** A mock replaces the stage with a stub that returns canned data. If a future refactor moves the dedup call to a different module or renames the stage, the mock still "passes" because it never invokes the real code. A spy wraps the real function, so the test fails loudly if the wiring moves or the real stage raises.

**When to use this pattern:**

- The pipeline has three or more stages and the ORDER is a correctness invariant (not just "does each stage run").
- You already have a fixture that exercises the full pipeline end-to-end.
- The stages are module-level functions (or methods on an injectable dependency) that `monkeypatch.setattr` can reach.

**When NOT to use it:**

- The order is enforced by the language (sequential statements in a single function) — a unit test of that function already covers it.
- The stages share mutable state that a spy would perturb (spy must be pure passthrough).

**Anti-pattern:** Mocking `apply_derivatives_dedup` with `MagicMock(return_value=[])`. The test asserts the mock was called, but the real dedup never runs. A bug that makes the real dedup raise on the fixture (which would surface as a pipeline failure in production) is invisible to the test.

## 13. Pass Pervasive Configuration as a Typed Value Object, Not via `contextvars` or a Module Cache

When a value like the reporting jurisdiction, tenant, or locale must reach several functions in a single-threaded synchronous pipeline, pass it as an explicit parameter carrying a **typed value object** (a frozen dataclass whose relevant field is required and validated at load). Do not reach for `contextvars.ContextVar` or a module-level cached singleton just because the value feels "pervasive."

```python
# ✅ GOOD - explicit DI of the typed value object
@dataclass(frozen=True)
class TaxJurisdictionConfig:
    country: str          # required, no default; validated fail-fast at config load
    fiscal_year: int
    ...

def write_crypto_supplementary_sheet(
    workbook, crypto_tax_report, tax_jurisdiction: TaxJurisdictionConfig,
) -> None:
    if tax_jurisdiction.country != "PT":
        return  # omit the PT-only reference section
    ...

# single call site already holds the object in scope:
write_crypto_supplementary_sheet(workbook, report, config.tax_jurisdiction)
```

```python
# ❌ WRONG - hidden global state for a value that only threads one or two hops
import contextvars
_CURRENT_JURISDICTION: contextvars.ContextVar[TaxJurisdictionConfig | None] = (
    contextvars.ContextVar("jurisdiction", default=None)
)

def write_crypto_supplementary_sheet(workbook, crypto_tax_report) -> None:
    jurisdiction = _CURRENT_JURISDICTION.get()  # untyped-ish, implicit, None-able
    if jurisdiction is None:                     # a "default to forget" the type cannot catch
        ...
```

**Why a typed value object, not `contextvars`:** The frozen dataclass with a required `country` field makes an unset value *impossible to construct*; validation runs once, fail-fast, at config load, so the parameter TYPE is the guarantee that the value is set. There is no `None` default and no sentinel to misuse. `contextvars` is the recommended tool only for truly cross-cutting context that spans many indifferent layers AND crosses async/thread boundaries (request ID, trace context, current user). For a synchronous CLI where the value threads one or two hops to functions called from a single site, `contextvars` adds hidden global state, loses type-checker/IDE support, and forces every test to set and reset a context (leakage risk between tests) to avoid threading two parameters. ([Python `contextvars` docs](https://docs.python.org/3/library/contextvars.html); if you do use it, the `ContextVar` must be created at module top level, never inside a function.)

**Why not a module-level cache / `functools.lru_cache` accessor:** A `get_jurisdiction()` singleton is hidden mutable global state duplicated from what the `Config` object already carries. It is a testing hazard (tests must reset it) and obscures the dependency at the call site. If the value already lives on a config object loaded at startup, thread that object.

**Choosing the narrowest cohesive type:** Pass the value object the consumer actually needs, not the whole root config. `TaxJurisdictionConfig` (cohesive, carries `.country` plus the flags the consumer uses) is correct; passing the entire `Config` couples the consumer to exchange rates and security settings it does not need, and passing a bare `country: str` discards the cohesion and the type-level presence guarantee.

**When `contextvars` IS the right choice:**

- A web/async workload where the value is request-scoped and must not leak across concurrent tasks.
- The value would otherwise be threaded through many functions that do not otherwise use it (signature pollution across indifferent layers), not just one or two call sites.

**Anti-pattern 1:** Defaulting an optional `country: str | None = None` parameter and falling back to a PT/synthetic value when `None`. A caller that forgets to thread it silently produces PT output on a non-PT run. Make the value object required; let the type checker and the frozen-dataclass contract enforce presence.

**Anti-pattern 2:** Introducing `contextvars` in a batch CLI "for future flexibility" before there is a second async caller. The hidden state and per-test context boilerplate are a net loss over an explicit parameter; add `contextvars` only when the async/pervasiveness need is real.

## 14. Pair `pytest.raises` with `match=` (Ruff PT011)

`pytest.raises(ExceptionType)` with no `match=` argument passes for ANY instance of
that exception type, not just the one the test intends. Ruff's `PT011` rule flags bare
`pytest.raises(...)` for this reason: a test that asserts only the type can stay GREEN
when a completely different code path raises the same exception type, masking the
behaviour the test was supposed to pin.

**Principle:** Family A (Equivalence-class coverage). The bare-type assertion pins only
one cell of the equivalence class "any `ExceptionType` raised anywhere in the body".
The test must pin the specific cell, the message substring unique to the intended
raise site.

Always pair `pytest.raises` with a `match=<regex>` argument whose substring is
produced by the intended raise site (the unknown value passed to the constructor,
the field name in the validation error, the configuration key, etc.):

```python
# WRONG - PT011; passes for any ValueError from anywhere in the body
with pytest.raises(ValueError):
    Treatment("nonsense")

# CORRECT - match pins the constructor call site (the literal value appears
# in Python's default enum error message)
with pytest.raises(ValueError, match="nonsense"):
    Treatment("nonsense")
```

When the raise site produces a domain-specific message (configuration error, validation
error, file processing error), prefer a substring of THAT message over the input value
itself; that anchors the assertion to the intended raise site even when Python's
default error text changes.

Applies to every Python test that uses `pytest.raises`. Add the `match=` argument at
RED time; never defer it as "polish" after GREEN.

## 15. Patch ALL Lookups in a Short-Circuit Disjunction When Asserting "None Fired"

When a test asserts that a code path "does not call" a set of helper lookups, and the
production predicate that selects those lookups is a short-circuit `or` (or `and`) over
two or more of them — for example `is_known = asset in popular_tokens() or
contains_popular_token(asset)`, where the test wants to assert NEITHER fires — you MUST
monkeypatch EVERY lookup in the disjunction, not just the first. Patching only the first
lookup leaves the second (and third, etc.) UNPINNED: the test's "none fired" assertion
can pass only because the first spy short-circuited the `or` before reaching the real
second call, so a future refactor that moves the unpatched lookup to fire unconditionally
(or before the short-circuit) would keep the test GREEN while breaking the avoidance
invariant the test was written to pin.

**Principle:** Family H (Verify the real thing, not the abstraction). The "none of the
lookups fired" assertion is only as strong as the set of lookups the spy actually covers.
An unpatched lookup is a hole in the coverage the assertion cannot see. Compounded by
Family G (Data-loss observability): the regression is silent — no exception, no warning,
just a lookup that runs and a test that still says "0 calls."

```python
# WRONG - only the first lookup is spied; the short-circuit or hides whether
# _contains_popular_token would have fired on the real call path
monkeypatch.setattr(cr, "_get_popular_crypto_tokens", spy_popular)
# _contains_popular_token is UNPATCHED - a future refactor that moves it above
# the short-circuit runs the REAL function and the test still sees popular=0

# CORRECT - patch ALL lookups in the disjunction (plus any sibling predicate
# the code path also consults, e.g. contains_non_latin_characters for is_suspicious)
monkeypatch.setattr(cr, "_get_popular_crypto_tokens", spy_popular)
monkeypatch.setattr(cr, "_contains_popular_token", spy_contains_popular)
monkeypatch.setattr(cr, "contains_non_latin_characters", spy_non_latin)
assert call_counts == {"popular": 0, "contains_popular": 0, "non_latin": 0}
```

**How to enumerate the full set:** Read the production predicate literally and list
every function call on its RHS. A short-circuit `a or b or c` has three; a
`is_known_token` defined as `asset in popular() or contains_popular(asset)` has two.
If the guarded block ALSO calls an independent predicate (for example a separate
`is_suspicious = contains_non_latin_characters(asset)` consulted in the same block),
patch that too when the invariant is "this whole block did not run."

**Distinguishing from rule #12 (pipeline-stage ordering spies):** #12 patches real
stages to assert ORDERING (A before B before C) while still running them; the spies
wrap and delegate so the real stages execute. This rule patches lookups to assert
NON-INVOCATION (zero calls each); the spies replace and do NOT delegate, because the
invariant is "the avoidance path fired, so the lookups were never reached." #12 is for
"did the right stages run in the right order"; this rule is for "did the short-circuit
prevent the lookups from running at all."

Applies to any "lookup avoidance" or "short-circuit gate" test where the production
predicate is a compound boolean over multiple helper calls.
