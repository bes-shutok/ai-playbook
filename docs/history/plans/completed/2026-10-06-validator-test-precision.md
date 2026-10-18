# Plan: collapse the select_slug test helper into select_in

Backlog origin: docs/history/backlog/2026-09-20-select-slug-test-helper-dedup.md
Driving force: simplicity
Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-validator-test-precision-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-validator-test-precision.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- select helper family: the three helpers in `scripts/test_review_record_selection.py` that invoke the CLI `select` command and return `(code, payload, err)`: `select_in`, `select`, and `select_slug`.
- pair-grammar cases: the tests that address record families other than `demo` by passing an explicit slug through the helper family.
- collapsed signature: the post-collapse parameter line `self, directory: Path, digest: str, *extra: str, slug: str = "demo"`, the span the Validation Commands pin at exactly 1.
- grammar pass: an edit pass that extends the helper family for a new record-grammar shape (the drift witness in Why).
- pins suite: `scripts/check_maintenance_pins.sh`, whose rows are the maintenance-pin rows the Assumptions cite.

## Why

The test file carries two near-identical helpers for the same CLI call, and the duplication already invited drift once: a grammar pass extended `select_slug` and left `select_in` behind. A defaulted parameter keeps one helper.

## Outcome

One select helper family: `select_in` owns the slug as a defaulted keyword parameter, `select` stays the demo-defaulting wrapper, and the separate `select_slug` helper is gone.

- The next grammar-pass contributor extends one helper instead of guessing between two.
- All 54 tests stay green with an unchanged case count and unchanged selection behavior.

Gate delta: none.

## Assumptions

- assume the collapse is behavior-preserving for every caller; basis: the two helper bodies are identical except that `select_slug` passes its slug parameter where `select_in` hardcodes `"demo"`, and the helper family is file-private (no references outside `scripts/test_review_record_selection.py` and no maintenance-pin rows name it).
- assume the suite stays at 54 cases; basis: counted and run green at main `f706f875` on 2026-10-06 (`grep -c "def test_"` = 54, `python3 scripts/test_review_record_selection.py` exits 0); if execution observes a different count, the re-pin is a plan correction and the pinned number is never edited to chase the count.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the review-record selection test suite collapses its duplicate `select_slug` helper into a slug-parameterized `select_in`, so the next contributor extends one helper instead of two (simplicity).

**Before (today):** `scripts/test_review_record_selection.py` defines `select_in` (hardcoded `"demo"` slug) and `select_slug` (slug as the second positional parameter) with identical bodies; 16 call sites target `select_slug`, 5 target `select_in`.

**After (this plan):** `select_in` takes `slug: str = "demo"` as a keyword-only parameter after `*extra`; `select_slug` is deleted; the 16 call sites pass the slug as a keyword; the two-line comment explaining the parameter moves to `select_in`; `select` and every existing call keep their behavior.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the suite passes at 54 tests with no case added, removed, or renamed; the pair-grammar cases still select by their explicit slugs.
- regression safety: the pins suite stays green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: only `scripts/test_review_record_selection.py` changes; no production file, gate, or schema surface is touched.

**Done when:**
- `( cd "$REPO" && python3 scripts/test_review_record_selection.py )` exits 0 with the suite at 54 tests.
- `def select_slug` occurs 0 times and the collapsed signature occurs exactly once in `scripts/test_review_record_selection.py`.

**Ship when:**
- The next test-file edit extends one select helper instead of two; it follows from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none (the change is test-only)

**Tests:**
- `scripts/test_review_record_selection.py` (the select helper family and its 21 call sites)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the uppercase-opener readiness machinery in `scripts/plan_readiness.py`; reason: the entry's sibling task landed ad-hoc in commit 19ac10b5 with its origin row covered, and this plan's scope is the select-slug dedup only.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match: the collapsed signature 0; the preserved spans matched: `def select_slug` 1, `self.select_slug` 16 call sites, `self.select_in(` 5, the comment 1, the suite 54 green); the rule 22 mechanical audit verified every pinned span occurs in its owning prescribed snippet (rule 36 mirrors included: the signature and comment spans each appear once as a checker literal and once as their prescription) and `bash -n` accepted the Validation Commands block; the em-dash touched scan and the hygiene scan both exited 0. Round-start state for r1: authoring worktree ai-playbook-wt-vtp, branch 2026-10-06-validator-test-precision, plan bytes at the draft commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && test -f scripts/test_review_record_selection.py )
( cd "$REPO" && python3 scripts/test_review_record_selection.py )
( cd "$REPO" && test "$(grep -oF 'def select_slug' scripts/test_review_record_selection.py | wc -l)" -eq 0 )
( cd "$REPO" && test "$(grep -oF 'self.select_slug' scripts/test_review_record_selection.py | wc -l)" -eq 0 )
( cd "$REPO" && test "$(grep -oF 'self, directory: Path, digest: str, *extra: str, slug: str = "demo"' scripts/test_review_record_selection.py | wc -l)" -eq 1 )
( cd "$REPO" && test "$(grep -oF 'self.select_in(' scripts/test_review_record_selection.py | wc -l)" -eq 21 )
( cd "$REPO" && test "$(grep -cF 'The pair-grammar cases address families other than' scripts/test_review_record_selection.py)" -eq 1 )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: collapse select_slug into a slug-parameterized select_in

Context surface: the plan's Terms and this task.

Files:
- `scripts/test_review_record_selection.py` (the select helper family and its 16 `select_slug` call sites)

Evidence:
- `( cd "$REPO" && python3 scripts/test_review_record_selection.py )`; covers the same-case-count criterion: the suite passes at 54 tests before and after the rewrite
- the span checks in `## Validation Commands`; covers the helper-family criterion: zero `select_slug` occurrences, one collapsed signature, one relocated comment, and 21 `self.select_in(` call occurrences

- [x] In `scripts/test_review_record_selection.py`, rewrite `select_in`'s signature to take the slug as a keyword-only defaulted parameter after `*extra` (the parameter line becomes `self, directory: Path, digest: str, *extra: str, slug: str = "demo"`) and replace the hardcoded `"demo"` argument in its `run_cli` call with `slug` [class: IMPLEMENTATION_REQUIRED]
- [x] Move the two-line comment that explains the parameter (from the line starting `# The pair-grammar cases address families other than` through the line ending `hardcoded fixture value.`) from `select_slug`'s body to directly above `select_in`'s signature [class: IMPLEMENTATION_REQUIRED]
- [x] Delete the `select_slug` helper (its `def` line and its body; the comment was relocated in the prior step) [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite all 16 `self.select_slug` call sites to `self.select_in(...)` calls that pass the digest in the second positional slot and the former slug argument as the `slug=` keyword, preserving each site's one-line or multi-line shape and its surrounding assertions byte-for-byte [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_review_record_selection.py )` passes all 54 tests; every span check in `## Validation Commands` holds (`def select_slug` and `self.select_slug` at 0, the collapsed signature and the relocated comment at exactly 1, `self.select_in(` at 21) [class: REPOSITORY_TEST]
- [x] Commit: `refactor: collapse select_slug into a slug-parameterized select_in` [class: IMPLEMENTATION_REQUIRED]


## Disposition

Executed 2026-10-06 in-session under the operator directive "start execution right away" (worktree wt-vtp, branch plan-vtp-exec).

- Task 1: select_in rewritten with the keyword-only defaulted slug parameter after *extra; the two-line comment relocated above select_in's signature; select_slug deleted; all 16 call sites rewritten to self.select_in(..., slug=...) with the digest in the second positional slot, extras order preserved, and zero assertion lines touched; 15 of 16 sites kept their original shape and the one collapsed site re-wrapped after the exec review noted it.
- Suite 54/54 before and after; every Validation-Commands span check holds (select_slug 0/0, collapsed signature 1, self.select_in( 21, comment 1); pins 0, em-dash 0, hygiene 0, pre-round pass.
- Exec review rN (numbered past the authoring series): ready=yes, zero blocking, one cosmetic non-blocking note folded (the multi-line shape restore); record 2026-10-06-plan-review-validator-test-precision-exec (md+sidecar).
- Origin row folded in the landing change per the deletion doctrine.
