# Backlog: dispatch admission outstanding-manifest recovery

Added: 2026-11-05, self-heal after a maintenance dispatch admission refusal

Status: covered-pending-execution (docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md)
Priority: medium
Class: fix-class
Origin class: consumer-pet
Scope: `scripts/dispatch_admission.py` and the maintenance/execute-plan handoff
Cluster: docs/history/backlog/2026-11-04-dispatch-admission-candidate-side-conservatism.md

Witness: maintenance turn 2026-11-05; `dispatch_admission.py` refused the top plan prompt because an outstanding execution run had no done-setup manifest. The active run has a claim, plan, session manifest, runtime state, and live-session evidence, but no run-specific done-setup JSON with owned-path fields at the consulted homes.

The first maintenance turn stopped after the conservative refusal without completing the required self-heal source check. The follow-up confirmed the refusal is the missing-source arm, not an intersection finding: the execute-plan `manifest.md` is not the JSON done-setup manifest accepted by `dispatch_admission.py`, and `runtime_state.json` carries no owned-path set. The existing admission plan explicitly treats this absence as intersecting. Because the run remains live, an inferred or fabricated manifest would not establish its complete future edit surface; no safe input currently lets the gate prove disjointness.

Investigate the smallest durable source that keeps exact target-disjointness available throughout an active run. Compare retaining a run-owned setup manifest across task boundaries with deriving a complete owned set from the claim, plan `Files:` lists, and current worktree dirt. Preserve the conservative refusal whenever the full set cannot be established; do not synthesize a manifest from a partial snapshot or weaken the admission check.

Harvest append (2026-11-06, cross-session harvest over the prior 24h): the conservative arm stood down two more one-shot maintenance carriers overnight on the same missing-source refusal. The 01:46 WET carrier recorded 0/1 with two live peer executions running manifest-less (their certification and closeout-migrate branches unlanded), and the 06:47 WET carrier recorded 0/1 with the certification peer branch still unlanded, the conservative consult blocking all four queued candidates; both parked dispatches were refreshed rather than satisfied. The manifest-less window closed only when the peer execution landed (cd385e428, 08:16 WET). Witnessed cost across the night: two full maintenance windows produced zero picks while the underlying runs were healthy and mid-flight, which prices this row's recovery-source investigation (the derived owned set from claim, plan Files lists, and worktree dirt, preserving the conservative refusal when the set cannot be established) as the live remedy, not a cleanup nicety.
