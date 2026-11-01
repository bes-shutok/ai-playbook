# Backlog: distinguish successful branch-only closeout from unknown-ref recovery

- Filed: 2026-10-29
- Status: open
Cluster: docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md (shared `gate-removal` closeout surface; the empty-diff no-op route remains distinct); docs/history/backlog/2026-10-31-gate-removal-inherited-manifest-rows.md (same gate-removal surface; that row owns manifest-row scoping across runs, this row owns the branch-only terminal state); docs/history/backlog/2026-11-01-adhoc-planless-worktree-closeout-arm.md (same gate-removal surface; that row owns the plan-less ad-hoc invocation gap, this row owns the branch-only terminal state)
- Priority: high
- Consumer urgency: Consumer repositories that use branch-only closeout need retained gate reports through `unknown-ref` recovery and a reliable completion signal before pruning; the skills-repository personal priority profile must not park this shared workflow defect as formal-hardening.
- Skill-step: `scripts/worktree_closeout_migrate.py` `cmd_gate_removal` and `scripts/done_sweep_gates_lib.py` `_run_gate_on_twin`
- Class: fix-class
- Origin class: self-serving
- Driving force: simplicity
- Severity and source: Medium, blocking review finding `implementation#missing-state-transition`, `.ai-playbook/reviews/2026-10-29-plan-review-done-gate-report-retention-p91c56b4b-r11.md`; corroborated by `.ai-playbook/reviews/2026-10-29-plan-reconciliation-done-gate-report-retention-r11.md`.
- Dedup probe: searched open backlog filenames and bodies for `branch-only`, `unknown-ref`, `terminal state`, `completion receipt`, and closeout report retention. The nearest item is `2026-10-29-done-gate-report-retention.md`, now narrowed to worktree-mode retention; `2026-10-21-gate-removal-task2-review-deferred.md` covers report wording and fixtures, not the branch-only completion transition. No existing open item covers this remaining state distinction.

## Problem

`gate-removal --branch` can return `OUTCOME: pass` to authorize operator removal, but it performs no removal and persists no terminal completion state. The done-sweep retention lookup calls `gate-removal --worktree`; branch-only `unknown-ref` recovery therefore has no matching sweep observation. If retention is extended to branch-only and the branch ref later disappears, the existing manifest cannot distinguish successful closeout from an unresolved recovery attempt. This leaves no bounded rule that both preserves reports through recovery and prunes them after success.

## Expected

Given branch-only closeout returns `unknown-ref`, preserve each verified referenced report while the operator resolves the ref and retries. Given successful branch-only closeout, provide an observable durable completion signal tied to the recorded branch and expected OID so a later sweep can prune only after success. Preserve the existing missing-destination refusal and bounded age cleanup for unrelated reports.

## Suggested investigation and direction

Trace existing done-session, migration-manifest, and closeout lifecycle records for a completion signal that can be reused. Compare that with the smallest receipt added to the existing closeout manifest; do not create a second registry or ledger. Any new retention state or blocking behavior must name its incident, expected catch frequency, false-positive cost, sunset/review date, and removal or simplification per the machinery-admission rules before implementation is planned.

## Why not fixed now

The active maintenance-selected plan is being narrowed to worktree-mode recovery because its declared scope excludes new retention schema and the current manifest has no branch-only terminal state. The r11 finding is not solved by that plan and remains a separate design item.
