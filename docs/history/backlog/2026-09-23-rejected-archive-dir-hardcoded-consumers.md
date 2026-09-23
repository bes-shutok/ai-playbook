# Rejected archive location is a hard-coded convention in five consumers

Status: open
Workflow: backlog

## Problem statement

The `rejected` archive subdirectory is derived independently in five consumers — `check_plan_origins_closed.py` (`REJECTED_DIR_NAME`), `docs_branch_backlog_dedupe.py` (`ARCHIVE_DIRS`), `docs_branch_plan_guard.py` (`ARCHIVED_PLAN_DIR_NAMES`), `done_sweep_gates_lib.py` (plans dir + `"rejected"`), and `plan_readiness.py` (positional part check) — while the completed dirs come from `facts.md` configuration. A repo with a customized plans layout gets rejected recognition only at the conventional location (`docs/plans/rejected/`, `docs/history/backlog/rejected/`); a sixth spelling could drift from the first five. The doc-registry validator's write gate (post-r1-F1 fix) adds two more hard-coded spellings of the same convention.

Evidence: grep each named constant/consumer; the READMEs in both archive dirs document the location as a convention, not a configured path.

## Location

- `scripts/check_plan_origins_closed.py` (`REJECTED_DIR_NAME`)
- `scripts/docs_branch_backlog_dedupe.py` (`ARCHIVE_DIRS`)
- `scripts/docs_branch_plan_guard.py` (`ARCHIVED_PLAN_DIR_NAMES`)
- `scripts/done_sweep_gates_lib.py` (rejected-prune derivation)
- `scripts/plan_readiness.py` (rejected path-part check)

## Suggested fix

Leave as-is today (yagni-consistent: the plans skill already calls the location "conventional"). If a sixth consumer appears, hoist one shared helper or a facts key (for example `plans_rejected_dir`) so the spellings cannot drift; fold the validator's two constants into the same helper at the same time.

## Severity and source reference

Low. Source: code review round r1 finding F5 (design-simplicity worker), `docs/reviews/2026-09-23-code-review-ai-harness-friction-audit-r1.md`. Capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

Non-blocking Low finding triaged to backlog capture by the r1 address-phase instruction. The scattered literals mirror the pre-existing convention for archive naming; no repo on this host customizes the plans layout, so the drift risk is theoretical today.

Driving force: simplicity, secondary: maintainability
