Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; em-dash gate scope hole (gate auditing a gate). Revive on a witnessed new em-dash landing in the excluded validators, or a project-priority-profile change.)
Created: 2026-09-16

# Add an insertion-scoped em-dash check for edited Python validators

Workflow: backlog
Severity: Low
Class: hygiene validation gap
Source: witnessed 2026-09-16 during plan-review round r4 of docs/plans/2026-09-16-review-records-contract.md (docs/reviews/2026-09-16-plan-review-review-records-contract-r4.md, finding F2)

## Problem

`scripts/check-no-em-dash.sh` sweeps prose files by default and every file only under `CHECK_NO_EM_DASH_ALL=1`. The two large validators (`scripts/validate_review_staging.py`, 23 legacy em-dash lines; `scripts/summarize_review_stats.py`, 5) can never pass a whole-file sweep, so plans that edit them exclude them from em-dash gates entirely and a new em-dash inserted into those files ships green; only the authoring-time prose rule (and done Step 2.76's prose sweep, which also skips `.py`) covers them.

## Exact location

- `scripts/check-no-em-dash.sh`, file mode (no per-hunk or insertion-scoped mode)
- Consumers: plans Validation Commands that edit the two validators, done Step 2.76

## Suggested fix

Add a git-diff-based mode (for example `check-no-em-dash.sh added-lines [--base REF]`) that runs the U+2014 scan over added or changed lines only, so edited legacy files get insertion-scoped coverage without whole-file sweeps over frozen regions; plans then gate their own edits mechanically.

## Why not fixed now

It is a tooling enhancement, not a defect in current behavior; the exclusion is documented in the consuming plan's Validation Commands scope note, and new scripts are already covered whole by the all-files mode.

## Additional witness

Witnessed 2026-09-20 (Tasks 2-4 of the merge-landing-lock-grouping plan): the `touched` mode scans whole modified files, so it failed on 12 pre-existing em dashes (11 in `agents/skills/maintenance/SKILL.md`, 1 in `prompt-templates.md`, all present at HEAD and none introduced by the session); the plan's Validation Commands required the scan to exit 0, forcing punctuation-only normalization of pre-existing prose lines inside the batch's allowed file set (deviation-logged, not silent). The behavioral contract for such gate-driven rewrites is tracked separately in 2026-09-19-gate-driven-silent-prose-edits; the mechanical gap remains this item's insertion-scoped mode.

Witnessed 2026-09-22 (done for Task 2 of the agent-aware execute-plan contract plan): the `touched` mode failed again on a single pre-existing em dash (`projects/.ai-playbook/agent-runtime-layout.md` line 136, present at HEAD since 2026-08-30, outside the session's only added hunk). No plan Validation Commands required exit 0 this time, and the no-silent-rewrite pin now forbids unadjudicated normalization of untouched user prose, so the run committed its deliverables with the gate red and logged the deviation here instead of editing the line. The insertion-scoped mode remains the mechanical gap; each new session that touches a legacy prose file re-trips it until it ships.
