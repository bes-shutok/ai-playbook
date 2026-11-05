# Backlog: dispatch admission outstanding-manifest recovery

Added: 2026-11-05, self-heal after a maintenance dispatch admission refusal

Status: open
Priority: medium
Class: fix-class
Origin class: consumer-pet
Scope: `scripts/dispatch_admission.py` and the maintenance/execute-plan handoff
Cluster: docs/history/backlog/2026-11-04-dispatch-admission-candidate-side-conservatism.md

Witness: maintenance turn 2026-11-05; `dispatch_admission.py` refused the top plan prompt because an outstanding execution run had no done-setup manifest. The active run has a claim, plan, session manifest, runtime state, and live-session evidence, but no run-specific done-setup JSON with owned-path fields at the consulted homes.

The first maintenance turn stopped after the conservative refusal without completing the required self-heal source check. The follow-up confirmed the refusal is the missing-source arm, not an intersection finding: the execute-plan `manifest.md` is not the JSON done-setup manifest accepted by `dispatch_admission.py`, and `runtime_state.json` carries no owned-path set. The existing admission plan explicitly treats this absence as intersecting. Because the run remains live, an inferred or fabricated manifest would not establish its complete future edit surface; no safe input currently lets the gate prove disjointness.

Investigate the smallest durable source that keeps exact target-disjointness available throughout an active run. Compare retaining a run-owned setup manifest across task boundaries with deriving a complete owned set from the claim, plan `Files:` lists, and current worktree dirt. Preserve the conservative refusal whenever the full set cannot be established; do not synthesize a manifest from a partial snapshot or weaken the admission check.
