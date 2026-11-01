# Backlog: preserve maintenance cycle-gate behavior with durable scenarios
Cluster: docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md (same D-17 continuation surface; runtime behavior versus scenario coverage)

- **Filed:** 2026-10-31 during the maintenance-autopilot-continuation Phase 3 review
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** self-serving
- **Class:** fix-class (the current run used temporary phrase assertions as a manual substitute for a durable behavior witness)
- **Driving force:** testability
- **Source:** `.ai-playbook/reviews/2026-10-31-maintenance-autopilot-continuation-code-review-r1.md`, finding F2 (Low, non-blocking); capture hygiene: `scan-public-hygiene --files` pass
Cluster: docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md (same D-17 continuation surface; separate runtime-specific continuation mechanism); docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md (same D-17 continuation surface; separate runtime-specific continuation mechanism)
- **Why not fixed now:** The finding is formal-hardening under this repository's personal priority profile; the execution plan's accepted scope covers the shared continuation policy, and adding a durable scenario harness is a separate testability task. Deferred by the execution run under `receiving-review`'s formal-hardening route.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `maintenance cycle gate`, `cycle-gate scenario`, `D-17 test`, `maintenance skill scenario`, and `durable behavior witness`; the nearest result was rejected item `docs/history/backlog/rejected/2026-09-25-authoring-cycle-gate-auto-resume.md`, which concerns an obsolete auto-resume request, not regression coverage for the current D-17 gate. No open item covers this test gap.

## Problem

The D-17 cycle-gate behavior has no durable scenario witness. The maintenance instruction text and this execution's temporary phrase assertions cover the intended autopilot and user-paced outcomes, but the full script suite does not exercise the gate with realistic contexts. A later instruction edit could keep the expected phrases while restoring the context-only stop, and the suite would stay green. The review verified the gap against the changed maintenance skill and the full 3066-pass repository suite; no current wrong behavior was demonstrated.

## Location

`agents/skills/maintenance/SKILL.md`, Cycle gate section, especially the D-17 disposition at line 14.

## Suggested fix

Add a durable, non-blocking scenario check with distinct outcomes:

- Autopilot mandate plus a gate armed only for context management clears the stale gate and continues to the next lane decision without prompting.
- Explicit user-paced directive keeps the readiness report and stops until a real user directive clears the gate.

Use the repository's existing skill-test conventions if available; do not invent a runtime API or add a dispatch-blocking validator.

## Acceptance criteria

- Both scenarios run from realistic maintenance context and assert the resulting continuation or readiness-stop behavior, not just policy phrases.
- The autopilot scenario fails if the gate remains armed or the run stops before the next lane decision.
- The user-paced scenario fails if the gate clears or the run continues without a real user directive.
- The check remains warning-only or test-suite-only and adds no new blocking machinery.
