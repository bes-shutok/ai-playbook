# Plan: Validator pass r4-deferred residuals (5 items)

References (scope of record, full text in `docs/history/backlog/`):
- `docs/history/backlog/2026-09-04-validator-pass-r4-deferred-parser-warning-side-effect.md` (Task 1)
- `docs/history/backlog/2026-09-04-validator-pass-r4-deferred-stderr-capture-helper.md` (Task 2)
- `docs/history/backlog/2026-09-04-validator-pass-r4-deferred-severity-seed-symmetry.md` (Task 3)
- `docs/history/backlog/2026-09-04-validator-pass-r4-deferred-guidelines-typo.md` (Task 4)
- `docs/history/backlog/2026-09-05-vrs-exclusivity-message-oxford-and.md` (Task 5)
Source review: `docs/reviews/2026-09-02-validator-pass-code-review-r4.md` (F1, F2, F3, F5) and summarizer-hardening r2 execute-plan r6 F1.

## Terms

- **VRS**: `scripts/validate_review_staging.py`, the review-staging validator; its `--selftest` mode is its own test suite.
- **Unclosed-fence fallback**: the partial-recovery path in `parse_markdown_findings` (r6 F3) that re-scans from an unclosed fence opener with heading resets.
- **Warn callback**: the new optional `warn: Callable[[str], None] | None` parameter of `parse_markdown_findings`; `None` (the default) means fully silent.
- **`ValidationResult`**: the dataclass returned by `validate_staging_file`; its `warnings` list is printed as `WARN:` lines to stderr by `main()` (or embedded in `--json` output).
- **Source flag table**: `_SOURCE_FLAG_TABLE`, the single registration point for `--source-plan` / `--source-rfc` / `--source-doc`.

## Assumptions

- assume a `warn` callback parameter (silent by default) instead of changing the return type to a tuple; basis: the backlog item offers both shapes, the codebase already has a structural warning channel (`ValidationResult.add_warning`, printed by `main()`), and the callback keeps all 16 existing call sites compiling.
- assume the warning message text stays byte-identical to today's; basis: the fence-family selftests pin its substrings and the item asks to change the transport, not the wording.
- assume `_stderr_silenced()` from the backlog's suggested shape is NOT implemented; basis: all seven silence-only `redirect_stderr` wrappers die in Tasks 1 and 2 (verified: none of them reads its buffer), so a silenced-flavor helper would have zero callers (YAGNI, same principle as the r4 F2 finding that deferred this group). Only `_stderr_captured()` lands, with the four remaining capture-and-assert sites as callers.
- assume `from collections.abc import Callable` is the import style; basis: the file currently has no typing import and uses builtin generic syntax (`str | None`).
- assume `is_review_ready` keeps no `warn` plumbing and stays silent-by-default; basis: its one production caller (`scripts/plan_readiness.py`, the execute-plan/done readiness gate) passes no warn and needs no diagnostics, and its selftest fixtures are silenced by wrapper removal rather than diagnostics; this is an accepted observable-output change for selftest runs.

## Gist & Examples

Five small residuals deferred by the validator-pass r4 fix-risk stop, all in or around VRS, executed in the dependency order the backlog prescribes.

**1. Parser purity (contract change, deliberate).** Today `parse_markdown_findings` prints the unclosed-fence warning straight to `sys.stderr`, so every selftest parsing an unclosed-fence fixture must wrap the call in `redirect_stderr`, and callers cannot silence or inspect the warning selectively. The change: the parser grows an optional `warn` callback, default `None` (silent), and emits the warning through it instead of printing. The two production call sites (`validate_finding_conservation`, `validate_version1_payload` pattern-conservation block) pass `warn=result.add_warning`, so the warning reaches the user through the existing `WARN:`/JSON plumbing instead of a raw print. This consciously supersedes the 2026-09-02-validator-pass plan Assumption of a "warn-level stderr diagnostic"; it is a contract change, not a bug fix.

Before:
```
stderr: warning: unclosed code fence in the Findings section (opener at
line 11 of the Findings section); ...
```
After:
```
result.warnings carries the warning once per parsing pass of the Findings
section: a direct parse yields exactly one entry; a current-v1 staging-doc
validation parses twice (pattern conservation and finding conservation),
so result.warnings holds two entries
main() non-JSON output: WARN: warning: unclosed code fence ...   (per entry)
main() --json output:   "warnings": ["warning: unclosed code fence ...", ...]
```
The recovery behavior is unchanged: both findings still parse, the later blocking pending finding still blocks readiness.

**2. Stderr-capture helper.** With the parser silent, the `buf = io.StringIO(); with contextlib.redirect_stderr(buf):` prelude survives only at four selftest sites that capture `main()`'s own stderr output (empty-flag loud exit, stale-digest Case B, source-kind mismatch Case D, exclusivity Case E). A `_stderr_captured()` contextmanager replaces those four preludes; the seven silence-only wrappers around parse/validate calls are deleted outright across Tasks 1 and 2 (six remain by Task 2; the parser no longer prints, so there is nothing to silence).

**3. Severity-seed symmetry.** The non-fallback `apply_events` call passes the local `current_severity` while the fallback call passes literal `None`; the local is initialized `None` and never reassigned, so both calls now pass literal `None` and the local (plus the explanatory comment) is deleted. Behavior identical.

**4. Guidelines typo.** Guideline 10 ("Pytest Test Method Names Must Start with `test_`") of `projects/.ai-playbook/python_guidelines.md` reads "silently skipped ;" with a stray space before the semicolon; drop the space. (The backlog item says "guideline 12"; the actual heading is `## 10`, verified at authoring time. The edit target is the unique text, not the number.)

**5. Mutual-exclusivity message terminal "and".** The r5 F4 table-derived rewrite dropped the Oxford "and". Restore it, still derived from `_SOURCE_FLAG_TABLE` (probe-verified byte-identical to the pre-c341e07 wording):
```
before: --source-plan, --source-rfc, --source-doc are mutually exclusive
after:  --source-plan, --source-rfc, and --source-doc are mutually exclusive
```

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/validate_review_staging.py --selftest` exits 0 after every task; the fence family (unclosed, tilde, silent-misparse, fallback-preserves-fenced-example, phantom-unclosed, same-group) still passes with unchanged recovery expectations.
- purity: `inspect.getsource(parse_markdown_findings)` contains neither `print(` nor `sys.stderr`, and the runtime purity probe (unclosed-fence fixture parsed with stderr captured) yields empty stderr and exactly one structural warning.
- consistency: both `apply_events` call sites pass literal `None` for the severity seed; the exclusivity error text contains the terminal "and" and is still derived from `_SOURCE_FLAG_TABLE` (no flag name hardcoded).
- hygiene: `scripts/check-no-em-dash.sh file <changed files>` exits 0.

**Done when:**
- All five backlog items' fixes are merged into the working tree with one commit per task, selftest green at every task boundary.
- The final Validation Commands block exits 0 in full.

**Ship when:**
- Not applicable; repository-local tooling with no deploy surface. (The backlog items move to `docs/history/backlog/completed/` at plan completion, per the plans lifecycle; that is not an implementation task.)

## Design Invariants (CR Guard)

- **The parser must stay pure.** No `print`, no `sys.stderr` write, no logging inside `parse_markdown_findings`; the warning flows only through the `warn` callback. A reviewer finding stderr output re-added inside the parser is a contract regression, not a style nit.
- **The warning text is byte-identical** to today's (transport changed, wording not). The phrase "not recovered" and the "line N of the Findings section" indexing basis stay pinned by selftests.
- **Recovery semantics frozen.** The r6 F3 partial fallback (both findings parse, post-opener metadata bullets not recovered) must not drift while the warning migrates; the fence-family checks are the guard.
- **`_SOURCE_FLAG_TABLE` stays the single registration point.** The exclusivity message (and its selftest expectation) must derive the flag list from the table; hardcoding the three flag names in the message text reintroduces the second sync point r5 F4 removed.
- **No `_stderr_silenced()` helper.** It has zero live callers after Task 1; adding it back is dead code.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py`
- `projects/.ai-playbook/python_guidelines.md`

**Tests:**
- The selftest suite lives inside `scripts/validate_review_staging.py` (same file as production code); there is no separate test file.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/2026-09-05-scope-control-family.md`; reason: untracked file from a peer session, not created or referenced by this plan.
- `docs/history/backlog/*.md` (other than the five referenced items at completion time); reason: the backlog corpus is frozen history for this plan; items move to `completed/` only in the plan-completion pass, not by implementation tasks.
- Runtime copies of VRS outside the repo (e.g. `~/.ai-playbook/scripts/validate_review_staging.py` symlink target is this file; no separate deployment step exists in this plan).

## Validation Commands

```bash
set -euo pipefail
python3 scripts/validate_review_staging.py --selftest

if grep -q " ;" projects/.ai-playbook/python_guidelines.md; then
  echo "FAIL: space-before-semicolon still present in python_guidelines.md"
  exit 1
fi

python3 - <<'PY'
import contextlib, importlib.util, inspect, io, sys
spec = importlib.util.spec_from_file_location(
    "vrs", "scripts/validate_review_staging.py"
)
vrs = importlib.util.module_from_spec(spec)
sys.modules["vrs"] = vrs
spec.loader.exec_module(vrs)

# 1. The parser carries no printing side effect.
src = inspect.getsource(vrs.parse_markdown_findings)
assert "print(" not in src, "FAIL: parse_markdown_findings still prints"
assert "sys.stderr" not in src, "FAIL: parser still writes stderr"

# 2. Purity probe: unclosed-fence fixture parses silently and surfaces the
#    fallback through the warn callback (fixture mirrors the selftest shape).
f1 = vrs._current_finding(id=1)
f2 = vrs._current_finding(id=2, severity="High", blocking=True)
md = vrs._current_findings_markdown([f1, f2]).replace(
    "#### Comment",
    "#### Comment\nAn unclosed fence example follows:\n```python\nx = 1\n",
    1,
)
warns = []
err = io.StringIO()
with contextlib.redirect_stderr(err):
    parsed = vrs.parse_markdown_findings(md, warn=warns.append)
assert err.getvalue() == "", "FAIL: parser printed to stderr"
assert len(warns) == 1, "FAIL: expected 1 structural warning, got %r" % warns
assert "unclosed code fence" in warns[0], "FAIL: wrong warning text"
assert sorted(f["id"] for f in parsed) == [1, 2], "FAIL: recovery drifted"

# 3. Mutual-exclusivity message carries the terminal "and".
err = io.StringIO()
with contextlib.redirect_stderr(err):
    try:
        vrs.main(
            ["--hard", "no.md", "--source-plan", "a.md",
             "--source-rfc", "b.md"]
        )
        raise AssertionError("FAIL: exclusivity violation did not exit")
    except SystemExit as exc:
        assert exc.code == 2, "FAIL: rc %r" % exc.code
flags = [f for f, _d, _k in vrs._SOURCE_FLAG_TABLE]
expected = (
    ", ".join(flags[:-1]) + ", and " + flags[-1]
    + " are mutually exclusive"
)
assert expected in err.getvalue(), (
    "FAIL: message missing terminal and: %r" % err.getvalue()
)
print("validation probes OK")
PY
```

Authoring-time RED-today record (2026-09-05, against the pre-plan tree): the purity probe raised `TypeError: parse_markdown_findings() got an unexpected keyword argument 'warn'` and the parser source contained both `print(` and `sys.stderr`; the exclusivity probe exited rc 2 with the message lacking ", and " (expected text absent); the typo grep matched line 199 of `projects/.ai-playbook/python_guidelines.md`. Every gate above therefore fires today and flips green only when its task lands.

### Task 1: Surface the unclosed-fence fallback via a warn callback (item 1)

Files:
- `scripts/validate_review_staging.py`

- [x] Rewrite the fence-scanner round 2 warning check (anchor `# unclosed-fence-warning`, the block currently capturing `warn_buf` before `parsed_warn`): replace the `redirect_stderr` wrapper with `warns: list[str] = []` and `parse_markdown_findings(unclosed_md, warn=warns.append)`; keep the `classify_fence_lines` defang guard and the existing id-2 `blocking: true` pin. Check given an unclosed-fence fixture with opener at section line 11, expects exactly one collected warning containing "line 11 of the Findings section" and "not recovered", parsed ids still `[1, 2]`, and finding id 2 keeping `blocking is True` (anchor `(# unclosed-fence-warning)` preserved)
- [x] Extend the `unclosed_val` block (currently wrapping `validate_staging_file` in `unclosed_val_buf`, buffer unread): drop the wrapper, keep the result object, add a check given a staging doc with an unclosed fence validated hard, expects `ok` true AND `result.warnings` containing at least one entry with "unclosed code fence". Gate on "at least one", not an exact count: the entry count depends on how many parsing passes the fixture's payload triggers (one for a legacy payload without `schema_version`, two for a current-v1 payload). The single-warning-per-parse contract is pinned by the direct-parse `warn` check above, not here. The dropped wrapper previously co-pinned the blocking/readiness assertions; those stay covered by the adjacent untouched fence checks (ids and readiness pins)
- [x] Run → expect RED: `python3 scripts/validate_review_staging.py --selftest` fails (today: `TypeError: ... unexpected keyword argument 'warn'`; the old stderr-asserting check must be fully removed in the same edit, not left to double-fail)
- [x] Add `from collections.abc import Callable` to the imports; change the signature to `def parse_markdown_findings(content: str, warn: Callable[[str], None] | None = None) -> list[dict]:`; replace the `print(..., file=sys.stderr)` block in the fallback branch with `if warn is not None: warn(<same message text, byte-identical>)`; update the docstring's contract sentence to state the parser is side-effect free and surfaces the fallback through `warn`; reword the block comment above the migrated warning check (the one currently reading "the parser emits exactly ONE stderr warning per parse_markdown_findings call naming ...") to describe structural emission instead: the parser passes exactly ONE warning per parsing pass of the Findings section to the `warn` callback, naming the same 1-based opener line and non-recovery scope
- [x] Wire production callers: in `validate_finding_conservation` change `md_findings = parse_markdown_findings(content)` to `parse_markdown_findings(content, warn=result.add_warning)`; in `validate_version1_payload`'s pattern-conservation comprehension, add `warn=result.add_warning` the same way
- [x] Run → expect GREEN: selftest exits 0 (the remaining silence-only wrappers are still in place and harmless at this point)
- [x] Commit: `validator: surface unclosed-fence fallback via warn callback (pure parser)`

### Task 2: `_stderr_captured()` helper, collapse the wrapper boilerplate (item 2)

Files:
- `scripts/validate_review_staging.py`

- [x] Add beside `_check_empty_flag_loud_exit`:
```python
@contextlib.contextmanager
def _stderr_captured() -> Iterator[io.StringIO]:
    """Capture stderr for selftests that assert on main()'s output.

    Silence-only wrappers are gone since the parser stopped printing
    (warn callback); only capture-and-assert sites remain.
    """
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        yield buf
```
plus the matching `from collections.abc import Iterator` import (matching Task 1's `collections.abc` import home; keep one import home)
- [x] Migrate the four capture-and-assert sites to `with _stderr_captured() as <existing buffer variable>:` keeping each site's current variable name (`buf` in the empty-flag check and Case B, `buf2` in Case D, `buf3` in Case E, so later checks referencing `buf3` keep compiling): the empty-flag loud-exit check, Case B (stale digest), Case D (source_kind mismatch; the code's own comment label, not Case C), Case E (mutual exclusivity); dedent bodies; buffer reads unchanged
- [x] Delete the six remaining silence-only wrappers (buffer never read; a seventh, `unclosed_val_buf`, already died in Task 1): `unclosed_buf`, `tilde_unclosed_buf`, `silent_unclosed_buf`, `fallback_buf`, `phantom_unclosed_buf`, `sg_buf`; dedent the wrapped parse/validate/is_review_ready calls
- [x] Run → expect GREEN: selftest exits 0; `grep -c "contextlib.redirect_stderr" scripts/validate_review_staging.py` prints exactly 1 (the helper body; the bare `import contextlib` line does not match this pattern, and zero call-site preludes remain)
- [x] Commit: `validator: add _stderr_captured helper, drop silence-only stderr wrappers`

### Task 3: Severity-seed symmetry between the two apply_events calls (item 3)

Files:
- `scripts/validate_review_staging.py`

- [x] In `parse_markdown_findings`, change the non-fallback call `apply_events(events, scanned, None, current_severity, False)` to pass literal `None`; delete the `current_severity: str | None = None` local; trim the "Severity seed is None here (r3 F3)" comment to state both call sites seed from literal `None` because state is re-derived inside `apply_events` (the fallback pass seeds its reset pass from `cur_severity`, which is different state and stays)
- [x] Characterization (no new test): the fence family and readiness checks already run both branches; run → expect GREEN: selftest exits 0 with zero diff in parsed outputs
- [x] Commit: `validator: pass literal None severity seed in both apply_events calls`

### Task 4: Guidelines typo, space before semicolon (item 4)

Files:
- `projects/.ai-playbook/python_guidelines.md`

- [x] Guideline 10 (heading `## 10. Pytest Test Method Names Must Start with test_`, the "silently skipped ;" sentence): change "silently skipped ;" to "silently skipped;" (one byte removed; verified present at authoring time on line 199; the number 12 in the backlog item is wrong, target the unique text)
- [x] Run → expect GREEN: selftest unaffected; `! grep -q " ;" projects/.ai-playbook/python_guidelines.md` now passes
- [x] Commit: `guidelines: drop stray space before semicolon in guideline 10`

### Task 5: Restore the terminal "and" in the mutual-exclusivity message (item 5)

Files:
- `scripts/validate_review_staging.py`

- [x] RED first: in Case E, add a table-derived expectation and a dedicated check:
```python
        _flags = [f for f, _d, _k in _SOURCE_FLAG_TABLE]
        _expected_text = (
            ", ".join(_flags[:-1]) + ", and " + _flags[-1]
            + " are mutually exclusive"
        )
        check(
            "mutual-exclusivity message keeps the terminal and, table-derived",
            rc_both == 2 and _expected_text in buf3.getvalue(),
        )
```
Run → expect RED: selftest fails on the new check (probe-verified at authoring time: rc 2 but the message lacks ", and ")
- [x] GREEN: in `main()`, replace the `parser.error(f"{', '.join(flag for flag, _d, _k in _SOURCE_FLAG_TABLE)} are mutually exclusive")` body with:
```python
        flags = [f for f, _d, _k in _SOURCE_FLAG_TABLE]
        parser.error(
            f"{', '.join(flags[:-1])}, and {flags[-1]} "
            "are mutually exclusive"
        )
```
(keep the F4 table-derived comment, add one line noting the terminal "and" is restored per the 2026-09-05 backlog item and the wording is byte-identical to pre-c341e07)
- [x] Run → expect GREEN: selftest exits 0
- [x] Commit: `validator: restore terminal and in mutual-exclusivity message (table-derived)`

### Task 6: Final validation

Files:
- none (validation only)

- [x] Run the full `## Validation Commands` block from the repo root → expect all gates green, exit 0
- [x] Run `scripts/check-no-em-dash.sh file scripts/validate_review_staging.py projects/.ai-playbook/python_guidelines.md` → expect exit 0
- [x] Commit: none (no-op task; nothing to commit if all green)

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-04-validator-pass-r4-deferred-parser-warning-side-effect.md: disposition folded into 2026-09-05-validator-pass-r4-deferred-residuals.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-validator-pass-r4-deferred-severity-seed-symmetry.md: disposition folded into 2026-09-05-validator-pass-r4-deferred-residuals.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-validator-pass-r4-deferred-stderr-capture-helper.md: disposition folded into 2026-09-05-validator-pass-r4-deferred-residuals.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-04-validator-pass-r4-deferred-guidelines-typo.md: disposition folded into 2026-09-05-validator-pass-r4-deferred-residuals.md (2026-09-25); per-item file deleted.
