# Backlog: Honor maintenance authorization during plan authoring

- **Filed:** 2026-10-20
- **Status:** covered (docs/history/plans/2026-10-20-maintenance-plan-authoring-authorization.md)
- **Priority:** high
- **Consumer urgency:** Users who delegate plan selection and authoring to the maintenance workflow need it to resolve supported choices and continue without an interactive confirmation pause.
- **Origin class:** consumer-pet
- **Class:** fix-class
- **Cluster:** docs/history/backlog/2026-10-08-plan-simplicity-challenge.md (same plans Phase 1 confirmation boundary; that row covers unnecessary questions for high-confidence authoring choices)

## Problem

In an author-mode maintenance run, the standing user directive authorizes selecting and authoring eligible backlog plans, and the selected rolling-log entry supplies the scope and design alternatives. The maintenance skill says to decide and proceed without questions, but the plans skill's generic Phase 1 still asks the user to refine evaluation criteria and confirm the validated requirements. This run stopped at that confirmation even though the maintenance task was authorized and the candidate entry already specified its scope, rejected alternatives, and acceptance evidence.

The result is a conflict between the scheduler's standing authorization and the downstream authoring gate: a routine plan choice becomes a user interruption, and the maintenance lane fails to complete its selected work.

## Evidence

- `agents/skills/maintenance/SKILL.md`, opening paragraph: maintenance runs under standing pre-authorization and never blocks on questions.
- `agents/skills/plans/SKILL.md`, Phase 1 Steps 1.3–1.4: asks the user to refine criteria and requires explicit confirmation before writing.
- `agents/skills/maintenance/template-authoring.md`, authoring payload: invokes the plans skill for a selected backlog item but does not state how its confirmation gate consumes the maintenance authorization.
- `docs/history/plans/completed/2026-10-05-dirt-gate-new-file-refactor-and-required-operands.md`, Assumptions: a prior maintenance-authored plan treated the standing directive and validated records as satisfying Step 1.4, showing an existing precedent that is not stated as a reusable contract.
- Observed 2026-10-20 in an interactive maintenance author-mode turn: the assistant reported a ready candidate and requested confirmation instead of continuing under the user's maintenance instruction.
- Recurrence observed 2026-10-20: after the operator explicitly clarified that maintenance should choose the best-supported solution without asking, the assistant again treated its discretion as requiring a user decision. The source prompt and standing authorization were available, so this was an instruction-routing failure rather than missing requirements.

## Why the instructions were broken

The maintenance rule grants standing authorization and directs the agent to decide and proceed. The plans skill's general confirmation flow remains active unless it explicitly consumes that authorization. The agent followed the generic confirmation habit without checking whether the current task's source prompt and repository evidence already resolved the choice. That made a routine judgment look like an unresolved user decision and interrupted authorized work.

## Expected

Define the maintenance-to-plans authorization contract at the shared authoring boundary. For plans selected under a live maintenance directive, derive criteria and high-confidence assumptions from the backlog entry and repository evidence, choose the best-supported option, record the reasoning, and treat the standing directive as authorization to proceed without a confirmation question. Keep ordinary direct plan-authoring behavior intact: ask only when a material choice cannot be resolved from the request, the source records, or the project principles. In maintenance mode, exclude unsupported scope extensions and move to the next eligible item rather than asking the user or silently expanding scope.

Acceptance should show that a fully specified maintenance prompt proceeds through plan authoring without a question, a source-resolvable design choice is selected and recorded, an unsupported extension stays out of scope, and an ordinary interactive plan request still asks about a genuinely unresolved material decision.

## Scope

- Align the plans skill's confirmation and evaluation-criteria steps with maintenance's standing authorization.
- Ensure the maintenance authoring payload passes the authorization context needed by the plans skill.
- Preserve the ordinary interactive requirements-discovery path and the scope-extension boundary.
- Do not add a new approval flag, gate, validator, ledger, or review ceremony.

## Source

- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/plans/SKILL.md`
- `docs/history/plans/completed/2026-10-05-dirt-gate-new-file-refactor-and-required-operands.md`
- The 2026-10-20 maintenance author-mode interaction.
