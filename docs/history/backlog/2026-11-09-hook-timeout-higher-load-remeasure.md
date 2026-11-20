Status: open
Workflow: backlog
Priority: low
Origin class: plan follow-up (regime-not-reached disposition of plan docs/history/plans/2026-11-09-hook-timeout-recurrence-diagnostic.md)
Class: fix-class (bounded diagnostic; no behavior change)
Driving force: efficiency
Added: 2026-11-09
Cluster: docs/history/backlog/2026-11-05-hook-timeout-recurrence-diagnostic.md

# Re-measure the skill-gate consult path at a synthetic load that reaches the incident regime

## Problem

The 2026-11-09 consult-path measurement run (plan
docs/history/plans/2026-11-09-hook-timeout-recurrence-diagnostic.md) injected
its maximum sanctioned load — 11 workers, exactly the ceiling of physical cores
12 minus 1 — and still never approached the host timeout: the worse run's
all-sample loaded max was 2.223 s (block), below the 5.0 s incident-regime
threshold (half the 10 s per-hook host timeout). The regime-not-reached
condition suppresses the stage verdict, so no dominant stage was named and the
plan's pre-registered narrowing list was never consulted; the disposition
landed as the note arm's regime-not-reached record (record line: the
"Consult-path load measurement — incident regime NOT reached (2026-11-09; note
arm)" entry in `agents/hooks/skill-gate/README.md`, "Build-time verifications
(outcomes)" section). A synthetic run that never approaches the host timeout
cannot price or narrow the origin row's incident — six witnessed hook timeouts
in one afternoon (2026-11-04 telemetry, harvested 2026-11-05) — so this row
carries the origin row's acceptance bar forward and requests a higher-load
re-measurement before the recurrence is left unexplained.

## Observed vs expected

Observed: at the sanctioned load ceiling the consult path measures p95/max
1.464 s / 2.033 s (allow) and 1.865 s / 2.223 s (block), with the emission-off
block p95 at 0.823 s beside the emission-on 1.865 s — comfortable headroom
against the 10 s budget, and no stage verdict drawable.

Expected: a re-measurement whose load configuration actually approaches or
reaches the incident regime, so the pinned per-class dominance rule can draw a
stage verdict and a disposition arm (narrow or price) can fire on measured
evidence — or a demonstration at the raised configuration that the consult
path still cannot approach the host timeout, which would convert the historical
frequency into a bounded, witnessed acceptance.

## Suggested fix and options considered

- **Recommended: raise the load past the worker ceiling.** The ceiling
  (physical cores - 1) is a host-safety bound for load injection, not the
  incident's operating point: the witnessed timeouts happened in real
  parallel-session windows where other sessions, builds, and standing security
  agents stack on top of the harness load. Options: oversubscribe workers
  beyond physical cores (still sandboxed and bounded), or run at the ceiling
  with a declared ambient-load generator co-running, or both; the harness
  (`scripts/profile_skill_gate_consult.py`, run context fields and the
  incident-regime check) already records whatever configuration is used.
  Regenerate with
  `python3 scripts/profile_skill_gate_consult.py load --out <output-dir> --kind loaded --repeat 0 --workers <N> --iterations <M> && python3 scripts/profile_skill_gate_consult.py analyze --out <output-dir>`.
- Re-run the identical 11-worker configuration: rejected, the regime verdict
  cannot change on the same operating point.
- Narrow a stage without a drawn verdict: rejected, the plan's narrowing list
  is pre-registered to fire only on a dominant stage, and inventing a target
  from non-dominant shares would breach that contract.

Decision semantics, refusal classes, and the pins (the 5 s resolver bound and
the 10 s host timeout) stay frozen through any re-measurement.

## Severity and source

Low. Source: plan execution Task 3, regime-not-reached arm, 2026-11-09
(worktree 2026-11-09-hook-consult-profiling).

## Dedup probe

Searched open backlog items for hook timeout / consult-path / skill-gate load:
only the origin row (covered-pending-execution) and its plan matched; no row
covers a higher-load re-measurement.
