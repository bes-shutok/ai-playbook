# Backlog: fix the Validation Commands preamble's target-repository root wording

- **Filed:** 2026-11-05, review round r2 certification-residual capture for docs/history/plans/2026-11-05-stacked-pr-review-size-policy.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review certification residual (this plan's r2)
- **Class:** fix-class
- **Skill/step:** plan Validation Commands block preamble
- **Dedup probe:** searched open backlog and this plan's review series for validation working-directory anchors and target-repository wording. The r1 finding (unanchored cwd-dependent validation) produced the preamble in commit 5ee0a783a; no row covers the anchor's term collision.

## Problem

The r2 fold added the preamble "# Run every command from the target repository root." to the Validation Commands block, but the plan's Terms define the target repository as the policy-bearing consumer repository whose facts configuration carries the PR-size policy; the three validation commands (scan-public-hygiene.sh, check_maintenance_pins.sh, machinery_inventory.py) exist only in the repository this plan edits (the shared-skills checkout). Following the preamble literally runs the commands in a checkout that lacks the scripts, and the failure surfaces as missing-file errors rather than the intended anchored run.

## Expected

The preamble names the root the commands actually require, for example "Run every command from this repository's root (the checkout whose skills this plan edits)", with no collision with the plan's defined target-repository term.
