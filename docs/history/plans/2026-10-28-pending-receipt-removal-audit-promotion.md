# Plan: Promote the Pending Receipt Removal Audit

Backlog origin: docs/history/backlog/2026-10-28-pending-receipt-removal-warning-promotion.md
Driving force: code-quality
Plan review record: the staging series `.ai-playbook/reviews/2026-10-28-plan-review-pending-receipt-removal-audit-promotion-p1002c343-r*.md` (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1.25h
Authoring claim: docs/tmp/authoring-claims/2026-10-28-pending-receipt-removal-warning-promotion.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **Receipt line:** one complete `PLAN-PROMPTS-PRUNE:` or `EXEC-PROMPTS-PRUNE:` ledger line in the canonical prompt log.
- **Landing repair mode:** the explicit audit option used by plan landing and plan authoring closeout to restore deleted receipt lines automatically before continuing.
- **Repair reconciliation:** matching one exact pending receipt addition to the corresponding committed deletion so a verified repair passes the audit rerun.
- **Survey mode:** the existing report-only maintenance audit invocation; it does not edit the prompt log or block maintenance.

## Why

The prune audit currently misses receipt lines removed by pending edits and by committed changes, allowing certified landings to silently lose ledger history. Two production losses were repaired the same day, and an automatic, exact repair path can prevent the next landing from stopping for routine recovery.

## Gist & Examples

TLDR: Flag receipt-line deletions and restore their exact bytes during landing, preserving the append-only ledger while keeping surveys read-only.

Before, deleting a foreign receipt in a staged change or a committed freeze could pass the audit. A landing then needed a manual forensic repair. After, the landing audit restores only the missing receipt lines from trusted Git history, reconciles each restoration against its exact committed deletion, checks the repaired result, and continues when it passes. For example, the two same-day loss shapes can be repaired without choosing among alternatives or waiting for an operator. If an exact source cannot be established or repeated concurrent edits prevent a safe write, the audit reports the specific failure and stops; read-only surveys, unrelated log changes, and existing scan/tool-error behavior keep their current outcomes.

## Outcome

Plan landings retain every receipt line and continue automatically after an exact repair.

- A deleted receipt line is detected in pending changes and committed history.
- Landing closeout restores only missing receipt bytes, verifies the repaired audit, and proceeds without operator input when successful.
- Maintenance surveys remain read-only and unrelated changes do not acquire new blocking behavior.

Gate delta: promote exact receipt-line deletion from a pending warning and an unclassified committed change to one flagged audit class, and add an explicit landing-only repair path; remove the pending warning-only handling for this class. The new refusal is limited to an exact repair that cannot be sourced, safely applied after one fresh-read retry, or verified; a repeated concurrent edit is part of that same repair failure, not a separate blocker. It is priced by the witnessed three production instances in thirteen days (the two same-day repairs `b4c137a30` and `42610a0a2`, plus the founding witness recorded in the origin); automatic repair removes the ordinary operator-stop cost. The current guard liveness ledger is 29 catches to 48 incidents (29:48). Existing entry-removal flags remain. No other refusal class, hard gate, fence, protocol layer, schema field, dispatch condition, or blocking review duty changes; no existing blocker is removed because the operator approved net growth after the true catch.

## Assumptions

- Landing closeout may amend only the canonical prompt log's receipt-line bytes in the index and worktree; this preserves unrelated staged and unstaged edits while making a successful repair ready for the existing landing commit. Basis: the user authorized the flagged class and specifically asked that routine recovery avoid stopping work.
- Exact receipt lines can be recovered from the relevant Git image that precedes their deletion; the audit reconciles one pending exact re-add with one committed removal by line identity and multiplicity. If history does not establish a unique exact source, the repair fails with a named report instead of fabricating a line. Basis: the two repair commits restore byte-identical lines from Git history.
- A repair verifies the latest index and worktree images before writing. On a concurrent change it rereads both images and retries once; if they keep changing, it leaves unrelated bytes untouched and reports that safe repair could not finish. Basis: the user requires recovery to avoid overwriting concurrent work while keeping ordinary repairs automatic.
- The maintenance survey remains read-only, report-only, and non-blocking. Only landing-closeout callers opt into repair. Basis: avoiding new survey mutations or blockers was an explicit user constraint.
- The user approved the audit promotion after the true catch and requires the plan to minimize its costs through automatic recovery. This is a recorded approval for this narrow change, not authorization to broaden other audit classes.

Decision points requiring a grill: none remain.

## Standing constraints

- Repair receipt lines only; do not rewrite, stage, or reorder unrelated prompt-log content.
- Reconcile committed deletions only with the same exact receipt line and occurrence count; unmatched deletions remain flagged.
- Before applying changes, verify the index and worktree images; after one changed-image retry, leave the repair unapplied and report the conflict if the images keep moving. If a paired write fails partway, roll back only the inserted receipt bytes and verify both images retain their pre-repair content and concurrent edits.
- Preserve existing warning, tool-error, and unrelated prune-audit outcomes.
- Automatic repair is idempotent and reruns the same audit before landing continues.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every receipt-line deletion in pending changes or the committed range is detected, and later exact re-additions are recognized.
- Recovery: a uniquely sourced deletion is restored automatically in the index and worktree, the audit is rerun, and closeout proceeds only after a passing result.
- Scope: survey calls remain read-only; unrelated edits and existing read/tool-error paths retain their current behavior.

**Done when:** focused tests cover both loss layers, exact automatic repair, idempotence, later re-addition, unmatched-deletion failure, duplicate-occurrence accounting, persistent-conflict reporting, paired-write rollback, preservation of unrelated staged and unstaged bytes, and the unchanged outcomes for unrelated cases; pinned caller contracts distinguish landing repair from read-only survey.

**Ship when:** the plan is reviewed and certified ready for execution.

## Documentation Impact Assessment

The workflow instructions that invoke the landing audit must name the automatic repair mode. The durable `PLAN-PROMPTS.md` Prune rule and both landing callers must opt into repair; the maintenance survey in `agents/skills/maintenance/decisions.md` keeps its default, report-only, never-blocking behavior. Update the existing pins alongside the wording so the split stays enforced. The incident details and repair witnesses already live in the backlog origin and `development_lessons.md`; no additional incident dossier is needed.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py` (Task 1)
- `scripts/check_maintenance_pins.sh` (Task 2)

**Tests:**
- `scripts/test_check_prompt_log_origins.py` (Task 1)

**Workflow documentation:**
- `agents/skills/plans/SKILL.md` (Task 2)
- `agents/skills/maintenance/template-authoring.md` (Task 2)
- `agents/skills/maintenance/decisions.md` (Task 2) *(review-only)*
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Other audit classifications, unrelated maintenance dispatch rules, and general Git repair machinery; this plan only changes receipt-line detection and landing recovery.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_check_prompt_log_origins.py'
python3 scripts/check_prompt_log_origins.py --selftest
```

### Task 1: Detect and automatically repair deleted receipt lines

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`

Primary class anchors:
- `pending_receipt_removal_warnings` in `scripts/check_prompt_log_origins.py`
- `walk_audit_commits` in `scripts/check_prompt_log_origins.py`
- `prune_audit` in `scripts/check_prompt_log_origins.py`

- [ ] Pending and committed audit paths flag deleted receipt lines; one exact pending re-add reconciles one matching committed deletion by line identity and multiplicity, while unmatched deletions remain flagged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Landing repair restores only uniquely sourced receipt bytes, preserves unrelated staged and unstaged bytes, reconciles committed history, reruns the audit, and reports success only when the rerun passes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Before writing, repair verifies current index and worktree images; after one fresh-read retry, a continued concurrent change leaves unrelated bytes intact and produces a specific repair-conflict report. [class: IMPLEMENTATION_REQUIRED]
- [ ] If the paired index/worktree write fails partway, repair removes only its own receipt insertion and verifies both images retain their pre-repair content, including concurrent unrelated edits. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a committed deletion, expect automatic restoration and immediate rerun to pass; given a matching committed deletion plus an unrelated deletion, expect only the matching occurrence reconciled, the unmatched receipt named in the audit output, and the audit rerun to fail. [class: REPOSITORY_TEST]
- [ ] Given two identical committed receipt deletions and one pending restoration, expect exactly one occurrence reconciled, the second named in the audit output, and the rerun to fail. [class: REPOSITORY_TEST]
- [ ] Given a concurrent unrelated edit that settles during the fresh-read retry, expect it to survive with the restored receipt; given another change after that retry, expect a specific conflict report and both images unchanged. Given a failure between index and worktree updates, expect rollback to leave both images unchanged. [class: REPOSITORY_TEST]
- [ ] Given the default audit invocation, expect its report and index/worktree bytes to remain unchanged. [class: REPOSITORY_TEST]
- [ ] Given the same missing receipt is audited twice, the second repair makes no further change; given ambiguous or unavailable source bytes, the audit names the unrecoverable line and does not invent or alter it. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the behavior's failing check (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `fix: automatically repair deleted prune receipts` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Keep landing and survey invocation scopes distinct

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/decisions.md`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Plan landing, authoring-closeout, and the durable Prune rule invoke automatic repair and continue after exact repair verifies; they name the specific unrecoverable condition. [class: IMPLEMENTATION_REQUIRED]
- [ ] Maintenance survey remains on the default read-only, report-only, never-blocking invocation. [class: IMPLEMENTATION_REQUIRED]
- [ ] Invocation pins fail if landing or survey callers are swapped, or if the survey opts into repair. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the behavior's failing check (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `docs: wire automatic receipt repair into landing closeout` [class: IMPLEMENTATION_REQUIRED]
