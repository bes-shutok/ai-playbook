# Backlog: preserve maintenance cycle-gate behavior with durable scenarios
Cluster: docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md (same D-17 continuation surface; runtime behavior versus scenario coverage)

- **Filed:** 2026-10-31 during the maintenance-autopilot-continuation Phase 3 review
- **Status:** covered-pending-execution (docs/history/plans/2026-11-07-maintenance-d17-false-terminal-stop.md)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Consumer projects that run the maintenance skill need this fix because an unattended run can stop while eligible authoring or execution work remains; the skills-repo personal priority profile must not park or defer it as formal-hardening for the skills repo alone.
- **Origin class:** self-serving
- **Class:** fix-class (the maintenance run stopped despite eligible work and treated an unsupported blocker as terminal)
- **Driving force:** automation
- **Source:** `.ai-playbook/reviews/2026-10-31-maintenance-autopilot-continuation-code-review-r1.md`, finding F2 (Low, non-blocking), plus the 2026-11-07 Codex maintenance run that ended after an unsupported no-op/blocker disposition while dispatchable work remained; capture hygiene: `scan-public-hygiene --files` pass
Cluster: docs/history/plans/completed/2026-11-02-maintenance-codex-continuation.md (same D-17 continuation surface; completed Codex continuation work); docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md (same D-17 continuation surface; separate runtime-specific continuation mechanism)
- **Why not fixed now:** This capture records a maintenance-skill workflow defect; changing the skill and adding a durable scenario belongs in a later authoring pick. The current task is limited to analysis and backlog capture.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `maintenance cycle gate`, `cycle-gate scenario`, `D-17 test`, `maintenance skill scenario`, `durable behavior witness`, and `stop with eligible work`; this existing item is the closest match and already owns durable D-17 continuation scenarios. The Codex quota-reset row covers runtime wake behavior, and the ZCode row covers fresh-session dispatch; neither covers a same-session false terminal stop after a blocker/no-op disposition. Folded the new witness and regression case into this scenario item rather than creating another file.

## Problem

The D-17 continuation behavior has no durable scenario witness. The maintenance instructions require Codex to continue in the same session while eligible work remains, and they require one self-heal consultation before treating a routine blocker as unrecoverable. In a Codex maintenance run on 2026-11-07, the run nevertheless ended after recording no-op/blocker outcomes while authoring and execution work remained; the asserted blocker was not established through the required recovery consultation. The current instructions already state the intended behavior, so this is a demonstrated workflow-application failure as well as the previously identified scenario-coverage gap. A later instruction edit could preserve the expected phrases while still allowing the false terminal stop, and the suite would stay green.

## Location

`agents/skills/maintenance/SKILL.md`, Cycle gate and final-report sections; `agents/skills/maintenance/decisions.md`, Blocker recovery and continue-loop condition.

## Suggested fix

Add durable, non-blocking scenarios with distinct outcomes:

- Autopilot mandate plus a gate armed only for context management clears the stale gate and continues to the next lane decision without prompting.
- Explicit user-paced directive keeps the readiness report and stops until a real user directive clears the gate.
- A routine blocker or no-op disposition does not end a D-17 run while another eligible pick remains; the deciding turn consults self-heal once for a non-user-only blocker, then resumes normal lane decisions when the existing guards permit.

Use the repository's existing skill-test conventions if available; do not invent a runtime API or add a dispatch-blocking validator.

## Acceptance criteria

- Both scenarios run from realistic maintenance context and assert the resulting continuation or readiness-stop behavior, not just policy phrases.
- The autopilot scenario fails if the gate remains armed or the run stops before the next lane decision.
- The user-paced scenario fails if the gate clears or the run continues without a real user directive.
- The false-terminal-stop scenario fails if the run ends with an eligible pick and no sanctioned stopping condition, or if a routine blocker reaches a stop without its one self-heal consultation.
- The check remains warning-only or test-suite-only and adds no new blocking machinery.
