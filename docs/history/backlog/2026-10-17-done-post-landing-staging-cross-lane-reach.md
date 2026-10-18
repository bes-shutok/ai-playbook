# Backlog: post-landing-staging gate inspects the primary checkout index even for worktree-resident runs

- **Filed:** 2026-10-17, exit row of the placement-closing-doctrine-enforcement review loop (r2 overflow candidate, correctness-completeness)
- **Status:** covered (docs/history/plans/completed/2026-10-16-worktree-done-boundary-gate-roster-split.md, landed 3eafe0b3d 2026-10-17 11:29; this row's three witnesses, 2026-10-16 16:21-16:42 task boundaries, all predate the fix, and the landed per-task roster skip delivers this row's Expected: per-task boundaries no longer inspect the primary index, the final closeout keeps today's strict shape)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** witnessed three times during the placement-closing-doctrine-enforcement execution (2026-10-16)
- **Class:** cross-lane serialization
- **Driving force:** reliability
- **Skill/step:** `scripts/done_sweep_gates_lib.py` `gate_post_landing_staging`; `agents/skills/done/SKILL.md` Step 3

## Problem

The per-task done boundary's post-landing-staging gate resolves the primary checkout and inspects its index even when the run itself is worktree-resident. A peer session staging files in the primary checkout therefore blocks a worktree lane's own boundary: the gate refuses on unowned staged residue it attributes to the run's closeout, though the run's own landing surface is its worktree. Witnessed three times in this run (Tasks 1-3 boundaries), each resolved by an operator-directed recorded override-proceed or by waiting for the peer to clear.

## Expected

A worktree-resident run's boundary should scope the primary-index inspection to what the run actually lands through the primary (the declared-stage channel and manifest-owned paths), or skip the primary-index residue classes that cannot belong to a worktree lane, so cross-lane peer staging stops blocking foreign lanes. A primary-resident run keeps today's strict shape.

## Suggested direction

Key the gate's residue-class strictness on the resolved placement (the facts document's `worktree_policy` the gate already reads): under the worktrees resolution, demote the unowned-staged class over the primary index to a warning naming the peer lane; under the primary resolution, keep the refusal. Probe the placement-awareness arm the gate already carries (its docstring records the `primary`/`primary-execution` widening) before adding any machinery; the change lands warning-only first per the machinery admission protocol.

## Alternatives

- Keep the refusal and always require operator overrides: rejected because it converts a peer-lane timing collision into a standing manual step, witnessed three times in one run (`.ai-playbook/reviews/2026-10-17-placement-closing-doctrine-enforcement-code-review-r2.md`, overflow O1).
- Exempt the primary index entirely for worktree runs: rejected because the declared-stage channel legitimately routes paths through the primary and keeps its ownership check (`scripts/done_sweep_gates_lib.py`, `gate_post_landing_staging` placement contract).

## Evidence

- The gate docstring's placement contract and its repo-keyed resolution: `scripts/done_sweep_gates_lib.py` (`gate_post_landing_staging`).
- The run manifest's done_fast_path rows for tasks 1-3 record the refusals and the recorded override-proceed posture (session logs, `docs/tmp/execute-plan/2026-10-16-placement-closing-doctrine-enforcement/manifest.md`).
