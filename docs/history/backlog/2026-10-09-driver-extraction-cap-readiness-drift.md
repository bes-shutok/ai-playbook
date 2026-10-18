# Backlog: driver extraction cap refuses Phase 0 over a checklist class label the readiness oracle does not measure

- **Filed:** 2026-10-10, execute-plan Phase 1 of plan 2026-10-09-review-loop-round-budget (Task 5)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** readiness-versus-driver extraction contract drift
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Phase 0 driver checklist; `scripts/plan_readiness.py` criterion measurement
- **Cluster:** docs/history/plans/completed/2026-10-10-contract-single-sourcing.md (the contract single-sourcing family)

## Observed vs expected

Observed: the execute-plan driver refused Phase 0 manifest seeding because a plan criterion measured 4556 bytes against the 4096-byte aggregate-per-criterion cap, while the readiness oracle (scripts/plan_readiness.py) the certification loop relies on does not measure the same extraction-cap surface. The two gates disagree about what "fits the extraction contract" means: a plan can be certified ready by the oracle and still be refused at the driver boundary (the 4556-byte refusal witnessed in the origin row), and the split remedy (six over-length criteria split at the seeding boundary) had to be discovered by hand.

Expected: the driver's extraction cap and the readiness oracle measure the same predicate, or the drift is named and owned in one place: the readiness oracle carries the driver-side extraction-cap check (or the driver reads the oracle's criterion measurement), so a certified-ready plan passes the Phase 0 boundary without a manual split discovery.

## Suggested direction

Fold the driver's per-criterion byte-cap check into scripts/plan_readiness.py's structural checks (or into a shared helper both the driver and the oracle import), with the driver refusal naming the same reason codes the oracle emits; add a fixture pair (over-cap criterion refused by both surfaces, at-cap criterion accepted by both) to the boundary-fixture regression.

## Evidence

- 2026-10-10 execution session (sess_2ab595f1): Phase 0 create refused with a 4556-byte criterion; remedy was a manual six-criteria split, recorded as a manifest-only deviation, and the split itself drifted r7 and forced a fresh full review panel (r8) before execution could proceed.
