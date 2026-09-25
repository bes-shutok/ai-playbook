# Plan: plan_readiness.py polish direct-fix batch

Backlog origin (scope of record):
- `docs/history/backlog/2026-09-06-plan-readiness-selftest-write-clean-state-privacy-rename.md`
- `docs/history/backlog/2026-09-06-plan-readiness-verdict-token-comment-eligibility-wording.md`

## Assumptions

- assume `write_clean_state` is selftest-only with no callers outside `scripts/plan_readiness.py`; basis: repo grep on 2026-09-07 found 39 occurrences (1 definition at line 645 + 38 call sites; 43 occurrences in the current tree after 3056efe), all inside that file; the only other mentions are historical completed-plan docs (`docs/plans/completed/`), which are immutable history, not live callers.
- assume the rename needs no compatibility alias; basis: same grep evidence (no live external caller).
- assume the baseline selftest is green today: `python3 scripts/plan_readiness.py --selftest` prints `ALL PASS` with rc 0; 90 `PASS:` lines at authoring time, 117 as of 2026-09-08 (commit 3056efe added the decision-points trailer-gate checks post-authoring); basis: executed 2026-09-07 before authoring, re-executed 2026-09-08.
- assume the executable sweep gate wording is authoritative over the stale comment: `scripts/plan_readiness.py` (line 407 at authoring; 561 in the current tree) enforces "eligible only when total is positive and covered equals total" and `agents/hooks/plan-readiness/README.md` line 100 documents "a positive total with covered equal to total"; basis: read both sources 2026-09-07.

## Gist & Examples

This plan lands two small, independent polish fixes in `scripts/plan_readiness.py`, both captured as backlog items by the 2026-09-06 plan-readiness-polish execution and deferred there because the then-executing plan pinned the old text.

**Fix 1 (comment wording).** The module comment above `VERDICT_TOKEN_RE` (line 68) still says the legacy-grammar deletion is "eligible only once ``--sweep`` coverage reports covered equal to total". That drops the positive-total clause the gate actually enforces: the sweep counter (line 407 at authoring; 561 in the current tree) requires "total is positive and covered equals total", and the README's drift-check section says "a positive total with covered equal to total". A reader of the comment alone could believe a 0/0 sweep unlocks the deletion, when the gate rejects it.

- **Before (today):** comment at line 68 reads `# (eligible only once ``--sweep`` coverage reports covered equal to total).`
- **After (this plan):** the same comment reads `# (eligible only once ``--sweep`` coverage reports a positive total with covered equal to total).`

**Fix 2 (privacy rename).** Module-level selftest helpers are underscore-prefixed (`_clean_reviews_dir`, `_review_markdown`, `_clear_sidecar`, all `_selftest_*` functions), but `write_clean_state` (definition at line 645 at authoring; 799 in the current tree) is exported without the underscore despite being a selftest fixture writer called only by `_selftest_*` runners. Readers may assume it is public module API.

- **Before (today):** `grep -cE '(^|[^_[:alnum:]])write_clean_state' scripts/plan_readiness.py` returns 39 (definition plus 38 call sites).
- **After (this plan):** every occurrence is `_write_clean_state`; the unprefixed form has zero matches in the file.

Both fixes are non-behavioral: Fix 1 is comment-only; Fix 2 is a mechanical name change with no signature or semantics change. The existing selftest (90 checks at authoring time, 117 as of 2026-09-08) is the characterization net for Fix 2: it must stay green (rc 0, `ALL PASS`) across the rename.

## Evaluation Criteria

**Quality dimensions:**
- correctness: selftest stays green (rc 0, `ALL PASS`; 117 `PASS:` lines as of 2026-09-08) after both fixes.
- consistency: the `VERDICT_TOKEN_RE` comment matches the executable gate (line 407) and the README drift-check wording.
- maintainability: no unprefixed `write_clean_state` reference remains in `scripts/plan_readiness.py`; the helper reads as module-private like its sibling selftest helpers.

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` exits rc 0 with an `ALL PASS` line (117 `PASS:` lines as of 2026-09-08; authoring-time count was 90).
- `grep -E '(^|[^_[:alnum:]])write_clean_state' scripts/plan_readiness.py` has zero matches (Validation Commands asserts this fail-closed).
- `grep -F 'coverage reports covered equal to total' scripts/plan_readiness.py` has zero matches and the positive-total wording is present.

**Ship when:**
- Both backlog items are archived to `docs/history/backlog/completed/` with `Status: done` during plan completion (repository-owned follow-through, no external dependency).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (frozen except: the comment line above `VERDICT_TOKEN_RE` at line 68, the `write_clean_state` definition and its 38 call sites; all other content is frozen; reject any finding that touches frozen regions)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/plan-readiness/README.md`; already carries the corrected wording (line 100); this plan does not edit it.
- `docs/plans/completed/2026-09-05-plan-readiness-migration.md`; historical plan prose references `write_clean_state` by the old name; completed history is immutable, not a caller.
- Both `docs/history/backlog/2026-09-06-plan-readiness-*.md` items; archived verbatim at completion, not edited.

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)"

# 1. Characterization: full selftest stays green across both fixes.
python3 scripts/plan_readiness.py --selftest > /tmp/pr_selftest.out 2>&1
rc=$?
test "$rc" -eq 0 || { echo "FAIL: selftest rc=$rc"; exit 1; }
PASS_COUNT="$(grep -c '^PASS:' /tmp/pr_selftest.out)"
# Floor-of-green: the PASS count grows as main adds checks (90 at authoring,
# 117 since 3056efe); rc 0 and the ALL PASS line above are the authoritative signals.
test "$PASS_COUNT" -ge 90 || { echo "FAIL: expected at least 90 PASS, got $PASS_COUNT"; exit 1; }
grep -q '^ALL PASS' /tmp/pr_selftest.out || { echo "FAIL: ALL PASS line missing"; exit 1; }

# 2. Fix 2 negative sweep: no unprefixed write_clean_state remains.
#    (Fires today: grep -cE returns 39 against the pre-fix tree, verified 2026-09-07.)
#    The [^_[:alnum:]] boundary keeps _write_clean_state matches out of the sweep.
if grep -nE '(^|[^_[:alnum:]])write_clean_state' scripts/plan_readiness.py; then
  echo "FAIL: unprefixed write_clean_state remains"; exit 1
fi
grep -qE '(^|[^_[:alnum:]])_write_clean_state' scripts/plan_readiness.py \
  || { echo "FAIL: _write_clean_state definition missing"; exit 1; }

# 3. Fix 1 comment contract: stale wording gone, positive-total wording present.
#    (Stale sweep fires today: grep -cF returns 1 against the pre-fix tree, verified 2026-09-07.)
if grep -F 'coverage reports covered equal to total' scripts/plan_readiness.py; then
  echo "FAIL: stale eligibility wording remains"; exit 1
fi
grep -qF 'a positive total with covered equal to total' scripts/plan_readiness.py \
  || { echo "FAIL: positive-total wording missing"; exit 1; }
```

### Task 1: Align VERDICT_TOKEN_RE eligibility comment with the sweep gate

Files:
- `scripts/plan_readiness.py`

- [x] Edit the comment line above `VERDICT_TOKEN_RE` (line 68) from `# (eligible only once ``--sweep`` coverage reports covered equal to total).` to `# (eligible only once ``--sweep`` coverage reports a positive total with covered equal to total).`; comment-only, no other line changes
- [x] Run Validation Commands checks 1 and 3 only at this interim point (check 2 is unsatisfiable until Task 2 lands: its forbidden sweep still fires with 39 unprefixed hits); expect check 1 green (`ALL PASS`, rc 0) and check 3 green (stale wording zero matches, positive-total wording present)
- [x] Commit: `scripts: align VERDICT_TOKEN_RE eligibility comment with sweep gate` — provenance note (2026-09-08): the standalone commits (07ef2f2, 2fff601) were made on the execution session branch but that branch never landed on main as ancestors; both fixes reached main folded inside squash commit 3056efe, which is the authoritative delivery record.

### Task 2: Rename selftest helper write_clean_state to _write_clean_state

Files:
- `scripts/plan_readiness.py`

- [x] Rename `write_clean_state` to `_write_clean_state` at the definition (line 645 at authoring; 799 in the current tree) and all call sites (38 at authoring, lines 721 through 1815; 42 in the current tree, lines 876 through 2363 after 3056efe's additions); signature, parameters, semantics, and return tuple unchanged
- [x] Run the full Validation Commands block; expect all checks green: selftest `ALL PASS` rc 0, unprefixed sweep zero matches, `_write_clean_state` present, stale comment wording zero matches, positive-total wording present
- [x] Commit: `scripts: rename selftest helper write_clean_state to _write_clean_state` — same provenance note as Task 1: content delivered to main via squash commit 3056efe; the standalone branch commits are unreachable.
