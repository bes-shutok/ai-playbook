# Plan: Warn on Pending Prompt-Log Receipt Removals

Backlog origin: docs/history/backlog/completed/2026-10-20-prompt-log-pending-prune-audit-warning.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-warn-pending-prompt-log-receipt-removals-r*.md
Authoring claim: docs/tmp/authoring-claims/2026-10-20-prompt-log-pending-prune-audit-warning.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)
Execution budget: 1.5h total, largest task 1.5h

## Terms

- **Rolling prompt log:** either tracked dispatch log, `PLAN-PROMPTS.md` or `EXEC-PROMPTS.md`.
- **Receipt line:** a ledger line in a rolling prompt log that records a completed prune and its witness.
- **Pending receipt removal:** a receipt line deletion present in the Git index or working tree but not yet in a commit.
- **Warning-only:** a finding that reports evidence without changing the audit exit status, modifying files, or adding a stop.

## Why

The committed-history audit cannot see receipt lines removed while a change is still in the index or working tree. The backlog records a neighboring landing receipt disappearing before commit without an early signal.

## Gist & Examples

TLDR: Report pending receipt-line removals through the existing audit, improving code quality by surfacing them before commit without changing its decisions.

Before: `--prune-audit` sees committed log changes, so a receipt removed in the index or working tree has no report yet.

After: The same audit reports the removed receipt's slug, log, change layer, and HEAD witness while preserving the existing committed-history result.

## Outcome

The existing prune audit reports pending receipt-line deletions before they are committed.

- Staged and unstaged deletions are distinguishable and identify the affected log and receipt slug.
- Pending findings remain warning-only and do not change the current exit or `OUTCOME` result.
- The audit stays read-only, keeps committed removal classification intact, and adds no state or second audit path.

Gate delta: no runtime gates, refusal classes, hard gates, fences, protocols, schema fields, or blocking review duties are added or removed; no existing checks are retired. Extend the existing nonblocking audit report over pending changes and add no separate invocation or state. The extension removes reliance on a person noticing pending receipt loss by eye; no new machinery is introduced.

## Assumptions

- assume the existing `--prune-audit` invocation remains the single entry point; basis: `scripts/check_prompt_log_origins.py` already audits both rolling logs, and its maintenance and landing callers invoke it.
- assume the pending scan compares the index to `HEAD` and the working tree to the index separately so each warning identifies its change layer; basis: the backlog requires staged and unstaged coverage, and the separate comparisons provide the smallest direct attribution.
- assume existing receipt lines are preserved by the rolling-log write rules and have no authorized deletion class; basis: the log rules require pre-existing receipts to stay byte-for-byte and in order. A deleted receipt line therefore receives a warning without adding a new authorization system.
- assume a pending-scan read failure emits an explicit warning but does not change the existing committed audit's exit or outcome; basis: the backlog and machinery admission protocol require this extension to remain warning-only.
- assume the sibling plan `docs/history/plans/2026-10-23-prune-audit-incommit-receipt-witness-arm.md` owns the shared Git-environment isolation for its checker tests, and this plan uses that landed fixture pattern without adding a second helper; basis: the sibling plan's task and the shared checker test harness.
- assume the scope is limited to the selected backlog item, while committed in-commit receipt classification remains in the sibling plan; basis: the sibling plan's explicit out-of-scope boundary.

Decision points requiring a grill: Keep the pending scan inside the existing audit, compare index and worktree layers separately, and fail open with a warning on pending-scan errors; basis: existing callers, current audit ownership, and the origin's warning-only requirement; simpler alternatives rejected: a second flag or invocation duplicates the audit surface, a combined diff loses layer attribution, and a new refusal or tool-error path could block the existing landing audit.

## Standing constraints

- Keep all pending-change reads non-mutating; never edit either rolling log or persist audit state.
- Pending findings and pending-scan errors remain warning-only. Existing committed-history classifications and their exit behavior remain unchanged.
- Reuse the sanitized test subprocess environment established by the sibling in-commit audit plan; do not add a parallel fixture helper.

## Evaluation Criteria

**Quality dimensions:**
- Detection: receipt deletions in the index and worktree are reported with the correct log, slug, layer, and HEAD identity.
- Compatibility: committed-history classifications, exit status, and `OUTCOME` behavior are unchanged by pending findings.
- Simplicity: one existing invocation handles both logs; no new state, flag, or blocking machinery is added.

**Done when:**
- Regression checks cover staged and unstaged receipt removals in both rolling logs, clean and receipt-addition cases, and pending-scan failure behavior.
- The pending scan is read-only and warning-only, and existing committed-history checks retain their results.
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-23-warn-pending-prompt-log-receipt-removals.md` passes.

**Ship when:** None; implementation and verification are repository-local.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py`

**Tests:**
- Regression cases for pending index and worktree receipt removals, selected from repository evidence when execution begins.

**Plan-related extension:** implementation and review may change files not listed above only when a finding is causally required by this plan's warning-only contract or regression checks.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/2026-10-23-prune-audit-incommit-receipt-witness-arm.md`; reason: it owns committed in-commit receipt classification, which this plan explicitly preserves.
- `agents/skills/maintenance/decisions.md` and `agents/skills/plans/SKILL.md`; reason: both already invoke the existing audit and need no new workflow step.
- `scripts/machinery_registry.json`; reason: the existing checker remains the same registered script and this plan adds no blocking machinery or state.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-23-warn-pending-prompt-log-receipt-removals.md
```

### Task 1: Report pending receipt deletions through the existing prune audit

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/check_prompt_log_origins.py`

Primary class anchors:
- `prune_audit` in `scripts/check_prompt_log_origins.py`

Evidence:
- The existing audit walks committed log changes and already reports warning-only findings in its summary.
- Both rolling logs are enumerated by one invocation when the audited path is either rolling log.
- The backlog requires pending staged and unstaged receipt-removal detection without changing the exit result or log bytes.

- [ ] Given a receipt line removed from a rolling log in the index, expects a warning identifying its slug, log path, `index` layer, and the audited `HEAD` identity; the existing audit exit and `OUTCOME` remain determined by committed-history findings only. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a receipt line removed from a rolling log only in the working tree, expects the same evidence with the `worktree` layer; a receipt in the sibling log never attributes a deletion to the other log. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a clean log, an added receipt, or an unrelated line edit, expects no pending-removal warning. [class: REPOSITORY_TEST]
- [ ] Given a pending-scan Git read failure, expects an explicit warning and the unchanged committed-audit exit and `OUTCOME`; no pending-only failure becomes a stop or tool-error result. [class: IMPLEMENTATION_REQUIRED]
- [ ] Regression checks exercise staged and unstaged deletions in both logs, the clean and addition controls, the read-failure case, and preservation of the existing committed-removal classifications. [class: REPOSITORY_TEST]
- [ ] Keep the pending scan read-only, preserve existing committed-history classifications, and do not add a CLI flag, second audit invocation, persistent state, or blocking gate. [class: IMPLEMENTATION_REQUIRED]
- [ ] Reuse the sibling plan's sanitized test subprocess environment after it lands; add no second test-environment helper. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: warn on pending prompt-log receipt removals`. [class: IMPLEMENTATION_REQUIRED]
