# Backlog: invoke self-heal before caller decides remedy is unknown

- **Filed:** 2026-10-29, operator correction during learn capture
- **Status:** covered (docs/history/plans/2026-10-29-self-heal-before-unknown-remedy.md)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** consumer projects using these shared skills need the recovery handoff; the skills-repository priority profile must not defer the fix as self-serving hardening.
- **Origin class:** self-serving
- **Class:** fix-class
- **Severity:** Medium
- **Driving force:** efficiency (primary) + reliability (secondary)
- **Skill/step:** `agents/skills/done/SKILL.md`, Recoverable stop handoff; `agents/skills/plans/SKILL.md`, Recoverable workflow stops
- **Runtime:** local agent session; repository-owned skill files, not a vendored runtime copy
- **Dedup probe:** searched open backlog names and findings for `unknown remedy`, `recoverability trigger`, `self-heal before stop`, `plans self-heal`, and `closeout handoff`. The nearest open rows cover report retention, run-manifest binding, and separate review or authorization issues; none covers a caller requiring a recovery remedy to be known before invoking self-heal. The completed `2026-10-27-self-heal-before-workflow-stop` plan added the handoffs but retains this trigger gap.

## Problem

The `plans` and `done` handoff rules invoke self-heal only after the caller already recognizes a failure as recoverable; `done` additionally requires the cause and authorized remedy to be determinable. This asks the caller to establish that recovery exists before invoking the skill whose job is to search for an authorized recovery. In the observed closeout, `gate-removal` reported missing verified report destinations. The assistant asked the operator for a backup location before searching the available local recovery sources. After the operator invoked self-heal, the original records were recovered and restored, and the same gate passed. The earlier plan added explicit `plans` and `done` handoffs, so the missing detail is the trigger before recoverability is known, not the existence of an integration point.

## Exact location

- `agents/skills/plans/SKILL.md`, Recoverable workflow stops.
- `agents/skills/done/SKILL.md`, Recoverable stop handoff.

## Expected

For a non-user-only failure or refusal that is about to make the workflow stop or ask the user, the owner invokes self-heal once before deciding whether recovery exists, even when the cause or remedy is uncertain. Self-heal may recover the run, preserve a required user decision, or report that no authorized path exists. In the final `plans` closeout, require `done` to return its disposition; if a closeout refusal arrives without one, `plans` invokes self-heal before forwarding it. Do not repeat a disposition or relax existing retry, ownership, fail-closed, or completion gates.

## Suspected root area

The consumer trigger classifies recoverability before invoking the diagnostic recovery skill. The plan-to-done handoff also carries a refusal without requiring evidence that `done` already made a self-heal disposition.

## Suggested direction

Keep the existing handoff and change its trigger: invoke self-heal before treating an uncertain failure or refusal as unrecoverable. In the `plans` closeout, carry `done`'s recorded disposition and invoke self-heal only when `done` returns a refusal without one. Preserve explicit user-only stops, named fail-closed remedies, retry limits, ownership checks, and completion evidence. Add no gate, state, ledger, or recovery allowance.

## Evidence

- `docs/history/plans/completed/2026-10-27-self-heal-before-workflow-stop.md` records the current `plans` and `done` handoffs and defines a recoverable stop as one whose cause and authorized remedy are already determinable.
- The current session's first response to the missing report destinations asked the user for a backup source. After the user invoked self-heal, local snapshots yielded the originals and `gate-removal` passed; `docs/history/backlog/2026-10-29-done-gate-report-retention.md` records the report-loss facet.
- The later plan closeout repeated the request for a backup location before a second user-directed self-heal search, confirming that the trigger gap remained after the earlier plan landed.

## Why not fixed now

This turn is the Learn and Investigate closeout. The follow-up changes the shared invocation contract across two skills, so it is routed through its own focused authoring and review rather than added during this capture.

## Source

Current-session operator correction after Learn's earlier pass treated the underlying report-retention issue as covering the distinct missed self-heal invocation.
