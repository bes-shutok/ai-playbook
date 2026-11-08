# Backlog: authoring selection runs no duplicate-origin coverage probe before the claim

Status: open
Workflow: backlog
Priority: high
Origin class: self-serving
Class: fix-class
Cluster: docs/history/backlog/2026-11-08-coverage-gate-deliberately-open-scope-row.md (same duplicate-origin coverage gate surface; that row owns the other half of the late-and-false refusal pair)
Driving force: efficiency

## Problem

Skill and step: `agents/skills/maintenance/template-authoring.md` (the AUTHORING CLAIM collision disposition and the pre-landing duplicate-origin coverage gate paragraph) and `agents/skills/plans/SKILL.md` (Phase 0 and the Landing closeout coverage gate). The duplicate-origin coverage gate (`scripts/check_plan_origins_closed.py --check-coverage`) runs only before the landing. The collision disposition before authoring checks claims only (lesson #393), not other plans' coverage of the picked origin row.

Observed (2026-11-08, ZCode one-shot author run, repo copy): an entry was picked, frozen, authored, and certified through four review rounds. The landing coverage gate then refused because a completed sibling plan already listed the origin row in its scope-of-record block. The conflict existed on disk before the claim was written; one gate invocation at pick time (the plan's would-be origin line against the primary plans directory) would have shown it before any review spend. Recovery needed an operator-directed self-heal (de1f7ae54; landing 4909ab7e7).

Expected: the authoring selection, or Phase 0 before the first plan-file write, probes the picked origin for covering citers with the same read-only gate logic. A hit routes to the collision disposition (stand down, adopt, first-landed-wins, or the citer re-home when the citer's own dispositions keep the row open, lesson #427) before authoring starts.

## Suggested change

Smallest first: one sentence in the authoring template's collision disposition and the plans Phase 0 entry naming the read-only coverage probe at pick time. The gate's existing CLI already serves it (a scratch declaring file carrying only the `Backlog origin:` line), so no new gate, validator, or ceremony is added. If the scratch-file operand proves awkward, a `--probe-origin <row path>` read-only mode is the next step, admitted under the Machinery admission protocol.

Dedup probe: searched open backlog for coverage gate, check-coverage, duplicate-origin, pick time, and Phase 0. `docs/history/backlog/2026-11-08-coverage-gate-deliberately-open-scope-row.md` owns the gate's false-conflict class (a different failure mode: what the gate counts, not when it runs). `docs/history/backlog/2026-11-04-authoring-claim-discovery-filename-convention.md` is covered and owned claim discovery only.
