# Backlog: Task 1 intermediate-review hardening nits (lock-span plan)

Status: open
Priority: low
Origin class: self-serving
Quarantine: 2026-10-16
Consumer urgency: none
Cluster: docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md

Driving force: correctness (measurement fidelity, fixture isolation)

## Findings (Step 1.2b intermediate review, Task 1, 2026-10-11)
1. Held-span asymmetry: the migrate arm starts its held-span clock before the acquire (worktree_closeout_migrate.py `_merge_lock_wait_acquire` call site), so `merge-lock: held <N>s` includes the bounded wait; the sync arm starts after acquire. Fix: start the clock after a successful acquire.
2. Hermeticity asymmetry: the docs-branch suite's `lock_env_pins` pins three vars but does not pop inherited `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN`/`DONE_LOCK_*` the way the migrate suite does; a host shell carrying old done-skill exports could pollute fixtures. Fix: pop the migrate suite's inventory inside `lock_env_pins`.

## Fix shape
Two one-line hardening changes in the named files; suites stay green.
3. Budget caps gap (Task 4 intermediate review, Medium): `scripts/skill_text_budget_caps.json` still caps the done router at the old monolith budget and has no rows for the 10 new modules; each `--check` run prints 10 CAPS GAP advisories. Fix: one `--ratchet` run plus tightening the router row.
4. Liveness ledger evidence pointer (Task 4 intermediate review, Low): `scripts/gate_liveness_ledger.json` post-landing-staging override row cites `agents/skills/done/SKILL.md` as evidence; the sanction text now lives in `sweep-gates-pre-commit.md`. One-line re-aim.
5. Budget caps per-module rows (Task 5 intermediate review, Low): `scripts/skill_text_budget_caps.json` learn row (and the done row from finding 3) still caps the now-small router; per-module cap rows are the precedent-consistent remedy (fold with finding 3's ratchet run).
6. generalize skill pointer tightening (Task 5 intermediate review, Low): `agents/skills/generalize/SKILL.md` points at `../learn/SKILL.md` for the Generalization pass, whose heading now lives in `learn/step-1-extract.md`; still resolves via router dispatch, but a module-path pointer would prevent a dead-end lookup.
7. Recurring ad-hoc-worktree force-removal (run witness, 2026-10-11): this execute-plan run's worktree was force-removed twice mid-task by an external process (a peer lane sweep is the suspected actor; the plan premortem names the class), the second removal striking between a worker's commit and the parent's done-boundary command so the boundary briefly landed on main and was rewound (evidence: docs/tmp/done-session/revert-set-evidence-cbfa562b-wrong-landing.patch in the primary). Fix shape: the sweep's worktree-removal arm must refuse worktrees whose branch carries an active execution claim, not only active checkouts.
