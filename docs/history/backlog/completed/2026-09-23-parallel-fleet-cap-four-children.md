# Parallel fleet cap: up to 4 concurrent children (worktree-isolated, merge-lock landings)

Status: done (executed via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md)
Priority group: 1 (efficiency)
Class: real
Date: 2026-09-23

## Origin

User directive, 2026-09-23 ~23:20 local (maintenance turn): "we can have several executions and authoring up to 4 sessions in parallel (from main on a separate worktree and the squash merging to main) depending on the quota and the cost of tokens in current time of day. So we may change the rule and start now."

The maintenance skill currently pins strictly-sequential executions (one `G1e` child at a time) and one authoring child (`G1a`). The directive replaces the single-child lane model with a **fleet cap of 4 concurrent children** for this repository, of mixed kinds (execution and authoring), each running:

- in its own ad-hoc worktree branched off the default branch (never switching the primary checkout's branch, never touching the primary checkout's working tree; the only exception is a child that legitimately needs the primary checkout, which then counts double toward collision discipline);
- landing via the existing merge-landing-lock critical section (repo-scoped lock already serializes squash landings);
- gated by the quota leg as-is (runtime-fit, peak-pricing deferral, rate-pressure) — the cost gate the directive names.

## What must change (authoring scope)

1. `SKILL.md` Step 2/3: `G1e`/`G1a` become fleet-count guards (count live peer execution sessions via the discovery arm + recorded pending children + armed child automations, capped at 4 repo-wide) instead of per-lane single-occupancy; D1/D2 dispatch until the fleet cap is reached.
2. `zcode.md` overlay: child dispatch ladder gains the parallel-dispatch reality (a session's own automation-born cap still limits it to one clocked create + one idle task; additional fleet slots are filled by fresh scheduler turns or child successor chaining, which must count the fleet before chaining — the idle-fleet-#2 payload already carries this fleet-count conjunct).
3. `prompt-templates.md`: both blueprints gain the PARALLEL-RUN DISCIPLINE sentence (worktree-off-main, facts copy, merge-lock landing) — already carried ad hoc by the 2026-09-23 fleet dispatches.
4. Pins suite + validation: update lane-occupancy pins; the armed-child guard scope note (prompt-templates deviation list, "recorded for a future policy change that arms clocked authoring children") becomes live policy.
5. Failure cap: progress/outcome checks already key on children[] entries, not lane singleton-ness; verify the fast re-dispatch and stand-down carve-out work with N concurrent entries per lane.

## First witnesses (2026-09-23)

- Clocked fleet child `automation-1e745234` (p37-context-budget) armed 23:30 local with the PARALLEL-RUN DISCIPLINE sentence; idle fleet child for p37-rate-pressure refused (idle-time quota exhausted — the audit's 11-refusal finding); live peer execution session on the primary checkout counted as fleet member 1.

## Acceptance

- Scheduler turn dispatches to a full fleet of 4 across turns without duplicate-target dispatches or primary-checkout collisions.
- Two executions land on main the same night via the merge lock without gate erosion (PII/hygiene/peer-byte/dirt-regression all still enforced per landing).
- Pins suite and validation green after the skill amendment lands.
