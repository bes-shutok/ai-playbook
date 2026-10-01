# Plan: Docs-branch progress-only overlay and receipt-backed checklist reconciliation

Backlog origin (scope of record): `docs/history/backlog/2026-09-29-docs-branch-certified-plan-progress.md`
Driving force: reliability; secondary automation
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-docs-branch-progress-overlay-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Mechanically proven task progress stops blocking the per-task done path at both gates the origin names, while substantive plan edits keep failing closed.

- The docs-branch certified-plan guard accepts a progress-only overlay: when the branch bytes match the latest certified digest and the incoming plan differs from the branch copy ONLY in checkbox marker tokens, every differing line pair being an unchecked-to-checked flip (`[ ]` to `[x]`, case-insensitive) on two otherwise byte-identical lines of equal line count, the guard emits a named acceptance line naming the plan, the flip count, and the certified digest, and the overlay proceeds; any other byte difference (text, structure, a checked-to-unchecked regression, bullet or spacing changes) still refuses as a certified downgrade.
- Execute-plan preflight reconciles a checkpointed task's unchecked plan checkboxes against recorded evidence before declaring plan-manifest disagreement: an unchecked parent-owned `Commit:` item closes only when the task's recorded checkpoint or done receipt names a commit identity; an unchecked verification/TDD item closes only when the task's recorded receipt carries matching verification evidence; an unobserved TDD RED step closes only through an explicit bounded disposition recorded beside the check (never silently); every remaining unchecked line refuses with a per-line disposition list naming the task, the plan digest, and each line's reason.

Gate delta: one acceptance arm added to the guard's certified-downgrade surface (progress-only overlays, narrowly normalized) and the preflight agreement check extended by a receipt-backed reconciliation pass (new per-line disposition granularity with three bounded acceptance shapes); no refusal surface is removed, and unexplained open items, missing receipts, and substantive drift keep refusing exactly as today; the guard's warn-and-proceed behavior on digests that match neither side is unchanged.

## Terms

- Progress-only overlay: an incoming plan whose only differences from the branch copy are unchecked-to-checked flip pairs on checkbox lines, under the pairing rule below.
- Pairing rule: the two plans are compared line by line; line counts must be equal; each line pair must be byte-identical except that the bracketed marker token may differ, and a differing pair is accepted only when the branch side carries the unchecked marker `[ ]` and the incoming side a checked marker `[x]` or `[X]`. Checkbox-line membership covers checked and unchecked GFM task-list markers (first non-whitespace token `- [ ]`, `- [x]`, `- [X]` with any of the `-`, `*`, `+` bullets); normalization touches only the bracketed token, never the bullet character, spacing, post-marker text, non-checkbox lines, inline code spans, or line structure.
- Parent-owned `Commit:` item: a checklist line whose text begins `Commit:` (the parent obligations family the seeding boundary already tracks in `parent_commit`/`parent_obligations`).
- Bounded RED disposition: the explicit record that a TDD RED step was attempted but its evidence is unavailable, carried in the preflight check output (never written into the plan).
- Receipt-backed reconciliation: classification of each unchecked line against the manifest's recorded receipts for that task (checkpoints, done receipts, commit evidence), not against prose claims.

## Assumptions

- The guard's refusal arm (branch bytes match the certified digest, incoming bytes do not) is the only place the progress arm lands: the `branch_ok and not incoming_ok` branch in `cmd_guard` (`scripts/docs_branch_plan_guard.py`, read today) is where the normalized-equality test inserts, so upgrade and warn paths are untouched.
- The preflight agreement condition is the `plan-manifest disagreement` failure inside `_readiness_decision` (`scripts/execute_plan_runtime.py`, the `unchecked = _unchecked_checkbox_lines(section)` site, read today); the reconciliation pass extends exactly that condition, and the readiness operation's closed decision set is unchanged.
- The receipt field names the reconciliation reads (checkpoint result commit evidence, done receipt `commit_identity`, verification evidence entries) are traced at implementation start from the manifest writer sites and recorded in the task log before their validation is wired, the same trace-first discipline the runtime hardening pair plan used; the plan pins the acceptance shapes, not unverified field names.
- The guard implements its own small pairing predicate, duplicated locally with a mirror comment naming `execute_plan_runtime._unchecked_checkbox_pairs` as the shape of record for the unchecked-marker half; no import edge into `execute_plan_runtime` is added (the runtime module is very large and its helper recognizes unchecked markers only, while the pairing rule needs checked markers too). Three callers consume the preflight agreement conditions the reconciliation reshapes: `_preflight_check_body` (preflight), the readiness operation, and the recover-run-identity admission, which reads the conditions as evidence strings; the reconciliation changes which conditions fire, never how callers parse them.

- A line the reconciliation closes (and a RED disposition) stays unchecked in the plan bytes: this plan fixes continuation and the docs-branch overlay only. The terminal/archive gate's refusal of any unchecked plan line is the pre-existing next boundary for receipt-closed plans and is deliberately out of scope here; the executor records it in the task log so the follow-up is visible.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: checkbox-only plan progress overlays pass the docs-branch certified guard, and preflight closes a checkpointed task's unchecked boxes only from recorded receipts with named per-line dispositions; force: reliability.

Today a consumer Task 5 done handoff wedges twice: the guard refuses the progressed plan as a certified downgrade (the certified digest no longer matches the incoming bytes), and even with the overlay question solved, preflight refuses continuation because the task's `Run → expect RED` and `Commit:` lines are unchecked despite a checkpoint receipt naming the successful commit and task-local verification. Marking those lines complete by hand would claim evidence that does not exist. After this plan the progress-only overlay passes with a named acceptance line, and preflight either closes each line from recorded evidence or refuses with the exact per-line reason and the bounded RED disposition escape.

## Evaluation Criteria

**Quality dimensions:**
- Fail-closed preservation: substantive edits, mixed edits (checkbox plus text), unexplained open acceptance items, stale digests, and missing receipts still refuse at both gates.
- Mechanically proven progress only: every acceptance cites its evidence (normalized-digest equality at the guard; receipt fields at preflight), never prose.
- Surface fidelity: the tests drive the actual `guard` subcommand and the actual preflight operation, not helper abstractions.

**Done when:**
- Every Validation Commands line exits 0 and both suites pass.

**Ship when:**
- The next consumer per-task done handoff with a checkbox-only update completes without a fresh certification (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/docs_branch_plan_guard.py`
- `agents/skills/docs-branch/SKILL.md` (certified-plan ordering contract wording only)
- `scripts/execute_plan_runtime.py` (the preflight agreement condition and its helpers only)

**Tests:**
- `scripts/test_docs_branch_plan_guard.py`
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the reviewed-scope recovery operation and its fencing; reason: the origin explicitly scopes this item to the progress-only complement, not claim fencing or scope drift.
- the seeding boundary's agreement semantics for pending tasks; reason: unchecked boxes on pending tasks agree with the manifest today and stay that way.

## Validation Commands

```bash
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_docs_branch_plan_guard.py -q || { echo FAIL: guard suite; exit 1; }
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_docs_branch_plan_guard.py -k progress_overlay -q || { echo FAIL: guard progress pins; exit 1; }
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k checklist_reconciliation -q || { echo FAIL: preflight reconciliation pins; exit 1; }
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime 2>&1 | tail -1 | grep -q "^OK" || { echo FAIL: runtime suite; exit 1; }
grep -q "progress-only overlay" scripts/docs_branch_plan_guard.py || { echo FAIL: guard acceptance token; exit 1; }
grep -q "receipt-backed reconciliation" scripts/execute_plan_runtime.py || { echo FAIL: preflight reconciliation token; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/docs_branch_plan_guard.py scripts/execute_plan_runtime.py agents/skills/docs-branch/SKILL.md docs/history/plans/2026-10-01-docs-branch-progress-overlay.md || { echo FAIL: em-dash; exit 1; }
```

### Task 1: guard accepts a progress-only checklist overlay

Files:
- `scripts/docs_branch_plan_guard.py`
- `scripts/test_docs_branch_plan_guard.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_docs_branch_plan_guard.py -k progress_overlay -q`; covers the new pins

- [x] Run → expect RED: `grep -c "progress-only overlay" scripts/docs_branch_plan_guard.py` prints 0 (grep exits 1) [class: REPOSITORY_TEST]
- [x] Add the suite pins FIRST (they fail on the missing arm), then implement: add a local pairing predicate (mirror comment naming `_unchecked_checkbox_pairs` as the unchecked-marker shape of record; no import from `execute_plan_runtime`) and insert the progress arm in `cmd_guard`'s certified-downgrade branch: pairing rule per Terms, print the named acceptance line `progress-only overlay accepted for <plan> (<N> unchecked-to-checked flip(s); branch matches certified digest <digest>)` and count the plan as accepted instead of refused; any non-conforming byte difference keeps the existing refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Suite pins drive the real `guard` subcommand via the file's existing subprocess helper, each named with the `progress_overlay` substring so the Evidence selector collects the family: `test_progress_overlay_accepts_marker_flip` (unchecked-to-checked flip passes with the acceptance line; one flip targets the uppercase `[X]` form to pin the case-fold), `test_progress_overlay_refuses_text_in_checkbox_line` (a text edit inside a checkbox line refuses), `test_progress_overlay_refuses_substantive_edit`, `test_progress_overlay_refuses_progress_regression` (checked-to-unchecked refuses), `test_progress_overlay_refuses_mixed_edit` (checkbox plus text refuses), and `test_progress_overlay_inert_without_certified_sidecar` (no sidecar: warn path unchanged), and `test_progress_overlay_inert_when_branch_digest_stale` (branch bytes no longer match the certified digest: the progress arm stays inert and today's warn-and-proceed behavior holds) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command; the full guard suite green [class: REPOSITORY_TEST]
- [x] Commit: `guard: accept progress-only checklist overlays at the certified boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 2: docs-branch ordering contract wording

Files:
- `agents/skills/docs-branch/SKILL.md`

Evidence:
- `grep -c "progress-only" agents/skills/docs-branch/SKILL.md` returns at least 1

- [x] Extend BOTH contract sites in `agents/skills/docs-branch/SKILL.md`: the certified-plan ordering paragraph (the Rules section) gains the progress-only overlay arm (what it accepts: unchecked-to-checked flip pairs under the pairing rule on a branch that matches the certified digest; what it still refuses: any other byte difference; the acceptance prints as a named line), and the failure-semantics paragraph (the sync failure semantics section) gains one deferring sentence so its absolute refusal wording cannot contradict the new arm [class: IMPLEMENTATION_REQUIRED]
- [x] Scrub the pre-existing em-dashes in `agents/skills/docs-branch/SKILL.md` (the file already carries U+2014 characters, so the file-scoped em-dash gate cannot exit 0 until they are rewritten as prose) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command; `bash scripts/check-no-em-dash.sh file agents/skills/docs-branch/SKILL.md` exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs-branch: document the progress-only overlay arm` [class: IMPLEMENTATION_REQUIRED]

### Task 3: preflight reconciles unchecked boxes against recorded receipts

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k checklist_reconciliation -q`; covers the new pins

- [x] Run → expect RED: `grep -c "receipt-backed reconciliation" scripts/execute_plan_runtime.py` prints 0 (grep exits 1) [class: REPOSITORY_TEST]
- [x] First, trace the receipt field names at the manifest writer sites (checkpoint receipts, done receipts, commit evidence, verification evidence entries) and record the found names in the task log before wiring their validation [class: REPOSITORY_TEST]
- [x] Reorder note for the executor: add the pin suite item below FIRST (the pins fail on the missing helper), then implement this item [class: REPOSITORY_TEST]
- [x] In the agreement condition inside `_readiness_decision`, before failing on `_unchecked_checkbox_lines(section)`: classify each unchecked line through a receipt-backed reconciliation helper that reads ONLY in-memory manifest state (no git invocations per line); a `Commit:` item closes only when a receipt recorded for the task's CURRENT attempt and claim generation names a commit identity (receipts from earlier attempts or generations are stale: task reset and reclaim paths do not clear checkpoints or verification evidence, so recency matching is the refusal guard; the commit checkpoints and done-commit records carry no attempt or generation of their own, so recency keys off the task's claim record `token`/`generation` while the trace-first step pins the exact fields found); a verification/TDD item closes only when current-attempt recorded verification evidence matches the item's command or criteria reference; a TDD RED step whose evidence is unavailable closes only through the explicit bounded RED disposition recorded in the preflight check output; every other unchecked line fails the condition with a per-line disposition list naming the task, the plan digest, and each line's reason (absent evidence, stale-attempt evidence, or mismatched identity), under the token `receipt-backed reconciliation` [class: IMPLEMENTATION_REQUIRED]
- [x] Add suite pins through the real preflight operation, each named with the `checklist_reconciliation` substring so the Evidence selector collects the family: `test_checklist_reconciliation_closes_commit_line_from_receipt`, `test_checklist_reconciliation_closes_verification_item_from_receipt`, `test_checklist_reconciliation_red_step_requires_bounded_disposition`, `test_checklist_reconciliation_refuses_unexplained_acceptance_item`, `test_checklist_reconciliation_refuses_mismatched_commit`, `test_checklist_reconciliation_names_refused_lines`, and `test_checklist_reconciliation_fully_checked_section_unchanged` [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Evidence command; full runtime suite green [class: REPOSITORY_TEST]
- [x] Commit: `runtime: preflight reconciles unchecked checklist lines against recorded receipts` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers both suites, the selector pins, the acceptance tokens, and the em-dash gate

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
