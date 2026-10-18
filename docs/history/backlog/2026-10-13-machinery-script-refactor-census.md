# Backlog: machinery scripts grew ad-hoc into god scripts — decomposition, dedup, and consistency program

- **Filed:** 2026-10-13, operator direction on the connected machinery theme ("scripts created for the machinery were updated ad-hoc and grew into big god scripts; review and refactor to remove duplications, inconsistency, simplify")
- **Status:** covered (docs/history/plans/2026-10-13-machinery-script-refactor-program.md)
- **Workflow:** backlog
- **Priority:** high (execution sequencing-gated behind the RED-on-main baseline repair — refactoring guard scripts over a red baseline repeats the audit's Part 4.6 violation)
- **Origin class:** self-serving
- **Class:** skill-architecture / refactor
- **Driving force:** reliability (hot-spot churn compounds review surface and drift risk)
- **Skill/step:** `scripts/` runtime corpus; the gates the maintenance loop executes per lane
- **Cluster:** docs/history/plans/2026-10-13-machinery-script-refactor-program.md (same defect class: script-internal duplication, already witnessed in the certification oracle; the 2026-09-19-plan-readiness-parser-dedup row this line first pointed at was deleted with the covering commit: the exec-lane landing commit for Task 2 of machinery-script-refactor-program, per the backlog completion rule)
- **Cluster:** docs/history/plans/2026-10-13-machinery-script-refactor-program.md (same defect class: script-internal duplication, already witnessed in the claim gateway; the 2026-10-07-claim-race-retry-duplication row this line first pointed at was deleted with the covering commit: the exec-lane landing commit for Task 3 of machinery-script-refactor-program, per the backlog completion rule)
- **Cluster:** docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md (the skill-text sibling of this theme; its module-extraction precedent is this row's method)
- **Cluster:** docs/history/plans/completed/2026-10-13-red-on-main-baseline-repair-and-auto-demote.md (the sequencing gate this row's execution waits behind; the origin row it covered was deleted with the covering landing per the backlog completion rule)

## Problem

The machinery's scripts were each born small and updated ad-hoc per incident, and the hot spots are now god scripts. Census at 2026-10-13 (wc -l over `scripts/*.py` and `scripts/*.sh`): 158,687 lines total (the 2026-10-09 audit measured ~84k runtime lines). Top offenders: `scripts/validate_review_staging.py` 18,110 lines / 252 functions (born 2026-07-17); `scripts/summarize_review_stats.py` 8,984 lines (born 2026-07-30); `scripts/plan_readiness.py` 7,973 lines / 89 defs (born 2026-09-06 — 8k lines in five weeks); `scripts/done_sweep_gates_lib.py` 7,650 lines / 153 defs / 21 argparse subcommands with an 11,209-line test (`scripts/test_done_sweep_gates_lib.py`) — born 2026-09-22, i.e. 7.6k production lines plus an 11.2k test in three weeks, with 31 commits in its first 30 days. `scripts/check_maintenance_pins.sh` is 3,287 lines of bash.

Duplication is already witnessed row-level inside two of these surfaces (the parser-dedup and claim-race cluster rows), so the pattern is established, not hypothetical. Consistency asymmetries at census: most gate scripts speak the outcome contract (`scripts/OUTCOME_CONTRACT.md`; e.g. validate_review_staging 102 OUTCOME refs, done_sweep_gates_lib 62, plan_readiness 35) while `scripts/quota_window_probe.py` carries none — the census must classify which of these are genuine inconsistencies and which are probe-shaped exemptions. Governance is asymmetric too: skill text is byte-budget-gated and duplication-reported (`scripts/skill_text_budget.py`, `scripts/skill_text_duplication.py`), while the script corpus — now larger than the skill text it serves — has neither; the audit's review machinery (family 1) sits inside the biggest offender, so every review round pays the monolith.

## Expected

Scripts read as single-purpose modules with one consistency posture: duplicated logic single-homed (the two witnessed dedup rows are the first work items), each surface speaking the outcome contract its consumers read, CLI and resolver conventions uniform, and the pins suite reconciled beside provenance at every move. The corpus stays at or below its current blocking surface — decomposition is removal-shaped; nothing here adds a gate.

## Fix shape

A census-first, incremental program mirroring the landed skill-text module split (`docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md`: byte-verbatim extraction, router/integrity pins re-aims beside provenance, twin deployment in the same run):

1. Inventory and hot-spot census: per-script invocation frequency and wall time (feeds from the script-runtime telemetry row), churn rate, duplication clusters, outcome-contract adoption map — one document, no behavior change.
2. Fold the two open dedup rows (`2026-09-19-plan-readiness-parser-dedup`, `2026-10-07-claim-race-retry-duplication`) as the first single-homing items.
3. Decompose the top offenders one module move at a time (validate_review_staging.py first — the audit's family 1 lives inside it), each move a scoped change with its pins reconciliation and its focused suite green.
4. One consistency pass over the census's asymmetry list (outcome contract, CLI conventions, the repo-local/deployed-twin resolver pattern), landing exempt-class decisions explicitly rather than by drift.

Sequencing: execute only after the RED-on-main baseline row's repair lands. Any new gate or budget mechanism the program proposes (for example extending the byte-budget gate to scripts) goes through the machinery admission protocol on its own evidence; this row proposes none.

## Rejected alternatives

- Big-bang rewrite of a god script in one change: rejected on the module-extraction row's own precedent — incremental per-module moves keep each intermediate boundary explicit and reviewable (`docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md`).
- Delete or replace guards wholesale to shrink the corpus: rejected because the gate-liveness ledger records true catches with owners; decomposition relocates, it does not remove, paying machinery (`scripts/gate_liveness_ledger.json`).
- Extend the byte-budget gate to scripts without an admission test: rejected because no witnessed incident shows script size itself blocked a lane — the witnessed costs are review rounds and churn, which decomposition addresses; a new blocker needs the four admission fields first (`AGENTS.md`, Machinery admission protocol).
- Leave as is and refactor per-incident: rejected because the birth-rate evidence shows per-incident updates are the growth mechanism (done_sweep_gates_lib: 7.6k lines in three weeks of incident patches).
