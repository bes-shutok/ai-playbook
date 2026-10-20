# Backlog: execution_claim.sh release refuses the active plan path once the archive rider has moved the plan

- **Filed:** 2026-10-21, execute-plan Phase 5 closeout of certification-seal-landing-survival (same-session analysis)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md (same script: `scripts/execution_claim.sh` operand and claim-path resolution)
- **Cluster:** docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md (same artifact class: the execution claim file's lifecycle ends)
- **Origin class:** observed execution friction
- **Class:** fix-class
- **Skill/step:** `scripts/execution_claim.sh` (`resolve_context`, the `plan operand not readable` tool error); `agents/skills/execute-plan/SKILL.md` Phase 5 (the claim removal by its owner)
- **Driving force:** simplicity (the closeout should release the claim it recorded without guessing a second path)

## Problem

The claim file records `plan: docs/history/plans/<file>.md` (the active path at take time). Phase 5 releases the claim after Phase 4's archive rider has already moved the plan to `docs/history/plans/completed/`, so `release <recorded plan path> --session <id>` dies with `plan operand not readable` (`OUTCOME: tool_error`) and the operator must re-invoke with the completed path. The gateway's own claim file is the stronger identity (slug plus session), yet the release arm keys on the operand's readability first.

## Expected

`release` resolves the claim by slug when the operand is absent (the recorded `plan:` line's slug, or the completed twin under the same basename), refusing only when no claim file matches the session; the Phase 5 wording names the recorded claim path as the release operand so no caller has to know about the archive move.

## Evidence

2026-10-21 closeout: `bash scripts/execution_claim.sh release docs/history/plans/2026-10-20-certification-seal-landing-survival.md --session zcode-maintenance-exec-20261021-1206-seal-resume` returned the tool error; the same call with `docs/history/plans/completed/...` released the claim.

## Why not fixed now

Single-surface script change with a fixture, but the witnessing session was an execution run under a stop-after-current-plan order; filed for the ad-hoc arm.

## Source

- Observed 2026-10-21 during the certification-seal-landing-survival Phase 5 claim release.
