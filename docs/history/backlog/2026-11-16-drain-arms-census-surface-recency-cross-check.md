# Backlog: the drain-arms census duty's surface resolution binds enumeration recency, not newest-closeout identity

- **Filed:** 2026-11-16, plan review r2 of docs-tmp-drain-arms-promotion-loop (certification-residual capture, findings F2 and F3)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** certification-residual capture from a plan review delta round
- **Skill/step:** the executed `Docs-tmp drain-arms census arm` bullet in `agents/skills/maintenance/survey-arms.md` (the plan docs/history/plans/2026-11-15-docs-tmp-drain-arms-promotion-loop.md's Task 1)
- **Dedup probe:** searched the open backlog for drain-arms census, report_surface, and surface-recency concerns (2026-11-16): no row owns the resolution rule's recency binding; the plan's own origin row owns the missing duty, not this adjudication edge.
- **Cluster:** docs/history/plans/2026-11-15-docs-tmp-drain-arms-promotion-loop.md (the census duty this row refines)

## Observed versus expected

Observed: the landed plan's resolution rule selects the newest full enumeration by the run-id timestamp in its name, but never cross-checks that enumeration against the newest closeout's identity. A newest closeout whose report lines fell at or under the emission sample bound leaves no durable enumeration, so the newest surviving file is an EARLIER closeout's report; the duty as pinned adjudicates those stale rows and can report the operator flip review from a cycle that never saw the newest closeout's data. The rule also gives per-class ordering keys (run-id timestamp for scoped names, file mtime for the bare unscoped name) but no cross-class precedence for a mixed population.

Expected: before adjudicating, the duty cross-checks the resolved `report_surface`'s run id against the newest done closeout's run id (the census record's `run_id` leg) and records a report-absent cycle when they disagree or when the newest closeout has no durable enumeration; the mixed scoped/bare population resolves by one stated precedence.

## Evidence

- Plan review r2 (2026-11-16, record .ai-playbook/reviews/2026-11-16-plan-review-docs-tmp-drain-arms-promotion-loop-pfa144802-r2.md) findings F2 (Medium, non-blocking) and F3 (Low, non-blocking), verified against `scripts/done_sweep_gates_lib.py`'s bounded emission (`SAMPLE_LIMIT = 10`) and `_gate_report_run_scope`'s bare-name fallback.
- Window-immune and citation-held earlier enumerations survive in `docs/tmp/done-session/gate-reports/` (the retention plan's keep-side protections), so the stale-adjacent-file state is reachable in normal operation.

## Suggested correction

When the census arm's first execution lands (the plan's own execution lane), fold one cross-check clause into the arm text: the resolved surface's run id must match the newest closeout's run id, else record report-absent; state one cross-class precedence for mixed populations.
