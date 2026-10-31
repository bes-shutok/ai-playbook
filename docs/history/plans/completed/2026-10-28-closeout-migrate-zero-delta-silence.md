# Plan: Closeout migrate zero-delta report

Backlog origin: docs/history/backlog/2026-10-28-closeout-migrate-zero-delta-silence.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-28-plan-review-closeout-migrate-zero-delta-silence-pde5a07f9-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-28-closeout-migrate-zero-delta-silence.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **Baseline**: the capture-time path and digest snapshot that `migrate` uses to find new or changed worktree artifacts.
- **Capture time**: the UTC time when the baseline capture starts walking its configured paths.
- **Legacy baseline**: a baseline written before it carried a capture time.
- **Migration manifest**: the JSON record written by `migrate` that records file-transfer outcomes and branch disposition.
- **Zero-delta migration**: a successful migration with no files copied, collision-renamed, or receipt-proven replaced.
- **Source artifact**: a file under one of the configured paths that the migration already walks in the run worktree.

## Why

`migrate` skips files whose current digest matches the baseline. If the baseline was captured after run artifacts were written, the helper can finish successfully with no artifact transfer while printing a clean zero. The output does not say when the baseline was captured, so the closeout owner cannot tell that the baseline may already include the run's work.

## Gist & Examples

TLDR: Report when a closeout baseline may already include run artifacts, improving carry visibility through efficiency.

Before, `Migrated 0 file(s)` gives no capture time or source mtime to distinguish a valid empty delta from a stale baseline that already includes run records.

After, a successful zero-delta migration prints a warning-only line with the baseline capture time and newest source artifact mtime, while keeping the existing copy result and exit status.

Edge cases: a baseline created before this change has no capture time and reports `unknown`; the baseline file itself is excluded from the mtime comparison because capture writes it after walking source paths.

## Outcome

A successful zero-delta closeout migration reports enough timing evidence to expose a baseline that may already include the run's artifacts.

- The closeout owner can see when the baseline was captured and the newest source artifact time.
- Older baseline files remain readable and continue through the same migration path.
- The warning does not change transfer behavior, migration manifest entries, or the success result.

Gate delta: add one UTC capture-time field to the baseline JSON and one warning-only zero-delta report; no refusal, hard gate, fence, protocol layer, scheduler state field, or dispatch pause is added, and no existing gate is removed or simplified. The warning addresses the witnessed `docs/history/backlog/2026-10-28-closeout-migrate-zero-delta-silence.md` incident, is expected on closeouts whose baseline postdates owned edits, may also appear on a legitimately empty delta, and remains non-blocking under the repository machinery admission protocol; review this warning after three closeouts, or propose a separate promotion plan after the next true catch.

## Assumptions

- Capture records its UTC timestamp before walking configured source paths; the timestamp describes the baseline operation rather than the later file write. Basis: `cmd_capture` walks the configured roots before writing the baseline.
- The mtime report uses the newest current source artifact under configured paths, including files absent from the baseline, and excludes the baseline file itself. Basis: `_cmd_migrate_transfer` walks all configured files; a missing baseline entry does not prevent a byte-identical target from being skipped.
- Baselines written before `captured_at` exists remain valid; their report uses `unknown` for that value rather than refusing the migration. Basis: the existing JSON format is read by `cmd_migrate` without a version gate.
- The warning is diagnostic only. The closeout still relies on its existing verified migration or manual-copy evidence before worktree removal. Basis: `agents/skills/done/SKILL.md` and the Worktree-first closeout contract.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the capture time and newest source mtime identify the evidence used by the zero-delta warning.
- Compatibility: older baselines remain accepted; copy, collision, replacement, migration manifest, and exit behavior stay unchanged.
- Observability: the warning clearly labels itself non-blocking and reports `unknown` or `none` when a timestamp cannot be derived.

**Done when:**
- A regression test reproduces a baseline captured after existing run records and observes the warning in a successful zero-delta migration.
- A legacy baseline without `captured_at` still migrates and reports an unknown capture time without changing the exit status.
- The closeout migration suite passes.

**Ship when:**
- None; this change only improves a local closeout diagnostic.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1)

**Tests:**
- The migration capture and zero-delta tests selected from repository evidence (Task 1)

**Plan-related extension:** implementation and review may change files not listed above when they complete this diagnostic and its tests, or correct a regression the change introduces.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; reason: the single-start baseline lifecycle and closeout dispatch remain unchanged.
- Closeout copy, replacement, removal, or shared-ledger policy; reason: the selected backlog item requests a warning-only report.

## Validation Commands

At execution, select and run the repository-owned class-style test suite or suites that cover baseline capture and migration reporting. Record the exact command and selected tests in the task log.

### Task 1: Report zero-delta timing evidence

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `cmd_capture` in `scripts/worktree_closeout_migrate.py`
- `_cmd_migrate_transfer` in `scripts/worktree_closeout_migrate.py`

Evidence:
- The captured JSON currently contains `dirs`, `files`, and `skipped`, without a capture timestamp.
- `_cmd_migrate_transfer` skips source files whose digest matches the baseline and prints the successful migration summary after persisting its migration manifest. It also skips a current source file absent from the baseline when the target is byte-identical, which can leave the successful transfer delta at zero.
- `docs/maintenance/development_lessons.md` lesson 288 records the 2026-10-28 zero-delta closeout witness and points to the warning-only backlog arm.

- [x] Given a new baseline capture, record a UTC `captured_at` value before the source walk. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a successful migration with no copied, renamed, or replaced files, report the baseline capture time and newest current source artifact mtime under configured paths, whether or not the artifact is baseline-listed, in one clearly warning-only line; if the baseline is legacy, report its capture time as unknown, and if no source artifact time is available, report none. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the baseline file is under a configured source root, exclude that file from newest-source-mtime calculation; the warning is printed only and is not itself a source artifact. [class: IMPLEMENTATION_REQUIRED]
- [x] Given either a legitimate empty delta or a baseline captured after existing run records, retain the same migration manifest, copy outcomes, and success exit status; do not auto-recapture or turn the warning into a gate. [class: IMPLEMENTATION_REQUIRED]
- [x] Add regression tests for capture-time ordering, both zero-delta cases, legacy `unknown`, missing-mtime `none`, baseline-file exclusion, and an un-baselined source file skipped as target-identical still contributing the newest mtime; then run the closeout migration suite. [class: REPOSITORY_TEST]
- [x] Commit: `fix: report zero-delta closeout timing` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- `ls docs/` showed only the existing history, maintenance, and temporary-documentation homes plus repository guidance. No new reference or workflow documentation is needed because the single-start baseline and closeout behavior do not change; the diagnostic lives in the helper's output.
