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
