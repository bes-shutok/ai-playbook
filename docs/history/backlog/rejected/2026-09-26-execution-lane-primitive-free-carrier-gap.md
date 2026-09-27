# Execution lane has no primitive-free carrier: reduced-toolset turns park a ready queue while quota sits abundant

- **Date filed:** 2026-09-26
- **Status:** rejected (2026-09-28; scheduler-lane machinery polish; the automation lattice it hardens is pruned by the 2026-09-28 scheduler simplification direction; no witnessed user-facing failure)
- **Priority:** high
- **Class:** real (agent-workflow liveness)
- **Origin:** 2026-09-26 04:0x scheduler-turn analysis (this repo)

## Symptom

The 2026-09-26 04:0x automation-born scheduler turn ended with the execution lane parked despite: the execution queue head being a certified, digest-intact, ready plan (`docs/plans/2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md`), an abundant quota window (3.0% used, 286 minutes to reset), and no competing lane. `pending_dispatch.reason`: "turn toolset lacks CronCreate (reduced automation-born toolset); execution lane never routed in-session or idle". The loop carrier was simultaneously dark (re-arm also parked, `precheck-absent-leg`), so the queue idled until an external touch. Similar dark-idle witnesses from sibling maintenance sessions on 2026-09-25: queue-drain plan landed with the carrier NOT armed (memory: "loop DARK re-arm parked"), and a parked branch dependency silently froze the lane (serialization-stall item, since filed).

## Root cause

The maintenance skill deliberately confines the execution lane to child-dispatch carriers. `agents/skills/maintenance/SKILL.md` (D2, quota-aware carrier selection): "The rule binds the authoring carrier alone: **the execution lane is never routed in-session** (its routing unchanged)". The ladder precheck (`agents/skills/maintenance/zcode.md`, "Ladder precheck") grants the primitive-free carve-out to in-session *authoring* only ("needs no mutating primitives at all"); the execution lane's only carriers are a clocked child (needs `CronCreate`, plus `CronDelete` when automation-born) or an idle-time child (needs `OffPeakCreate`). An automation-born turn inheriting the reduced toolset (no mutation primitives at all, witnessed 2026-09-21 and again 2026-09-26) therefore has **zero lawful execution carriers** and must park: by design, not by turn error. The park is correct under current rules; the rules are the defect. The authoring lane solved this same problem on 2026-09-20 with the in-session dispatch mode (`(in-session)` children[] entries, full gates still applied); the execution lane never received the equivalent.

Related but distinct stop causes already tracked elsewhere: per-plan confirmation pauses (fixed by the executed queue-drain plan, `docs/plans/completed/2026-09-25-execution-lane-queue-drain-continuation.md`) and mid-execution-turn context exhaustion (`2026-09-25-execution-sessions-compact-at-task-boundaries.md`). This item covers only the missing carrier.

## Fix direction (for the authoring turn to shape; options, not a decision)

1. **In-session execution dispatch mode** (mirror of authoring's): allow the deciding turn to run the execute-plan chain itself when (a) both child-dispatch primitives are absent after the precheck, and (b) the quota probe shows an abundant window (same thresholds as D2), recording an `(in-session)` execution children[] entry with `dispatch_plan_sha` and the same completion evidence (plan archived). P57's per-execution worktree isolation removed the old reason executions were child-only (shared-checkout contention).
2. **Idle-leg fallback for parked dispatch**: when the clocked leg's primitive is absent but `OffPeakCreate` exists, route the parked `pending_dispatch` through the idle lane instead of parking bare.
3. **Park must arm the resume carrier**: a `pending_dispatch` park currently leaves the loop dark when the re-arm leg also lacks primitives; pair the park with the launchd resume-carrier path already used by the loop-guard stand-down, so a parked queue is never carrier-less.

## Acceptance sketch

- A reduced-toolset turn with a ready queue head and an abundant quota window records an executed-or-idle-dispatched outcome, not a bare park; a regression test/pin covers the carrier-selection ordering (clocked → idle → in-session → park-with-carrier).
- The `pending_dispatch` park paragraph in SKILL.md/`zcode.md` cross-references whichever fallback legs are adopted, and the state schema needs no bump beyond reusing the existing `(in-session)`/`(idle)` marker conventions.
