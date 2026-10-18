# Backlog: operand-free dirt-gate command displays in the maintenance templates

- **Filed:** 2026-10-05, review residual (r1 F5 of docs/history/plans/2026-10-05-dirt-gate-new-file-refactor-and-required-operands.md; the covering plan fixed the done-skill display site and records this row as the residual's home)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (r1, Low, seam-and-scope#adjacent-same-shape-unlisted)
- **Class:** fix-class (documentation span)
- **Cluster:** docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md (shares the dirt-regression-gate surface; named kept-open outside that row's demotion program as a display defect, not posture)
- **Driving force:** reliability

Cluster: docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md (shared surface: both display sites sit in prompt-templates.md, whose changelog extraction and template split relocate lines; this row's fixes re-anchor after those land)

## Problem

`agents/skills/maintenance/prompt-templates.md` displays the dirt regression gate command without its required path operands at two sites (lines 62 and 325): `scripts/dirt_regression_gate.py --base <merge-base-sha>` over the working tree's modified files. The helper requires one or more `paths` arguments, so a literal use exits with `the following arguments are required: paths` and `OUTCOME: tool_error` (exit 3), the identical hazard the done-skill row `2026-10-05-done-dirt-regression-cli-path-usage.md` witnessed on its own display site (fixed by the covering plan). The sites sit on the maintenance merge-duty and audit-recipe boundaries, outside that row's Skill/step span, so the covering plan recorded them as a residual instead of editing them.

## Expected

Both display sites show the operand-carrying form (`--base "$BASE" -- "$path1" "$path2"`, one path operand per modified file from the working-tree scan) and state that a `--base`-only invocation is a command-construction usage error, mirroring the covering plan's done-skill wording; the merge-bound landing prose keeps its derivation and outcome handling.

## Why not fixed now

Outside the covering plan's Review Scope (origin row 2's Skill/step line names only the done skill); the two sites are reachable only from maintenance-lane landing prose, so the exposure is narrower than the done-skill site, and the residual is recorded rather than scope-crept.

## Source

- Review r1 finding F5, docs/reviews/2026-10-05-plan-review-dirt-gate-new-file-refactor-and-required-operands-r1.md; display sites verified in live bytes at lines 62 and 324-325.
