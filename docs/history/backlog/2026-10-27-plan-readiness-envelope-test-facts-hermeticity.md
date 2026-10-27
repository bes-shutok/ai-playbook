# Backlog: make the plan-readiness envelope test hermetic to the gitignored facts file

- **Filed:** 2026-10-27, learn Step 1.9 over the interactive exec max-2 run (a focused-panel worker witnessed the red test inside an ad-hoc worktree; reproduced from a scratch worktree the same day)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-panel witness (learn Step 1.9 project issue)
- **Class:** test reliability
- **Driving force:** code-quality
- **Skill/step:** `scripts/test_plan_readiness.py`, class `ReadinessSingleFileUnchangedTest`, test `test_landed_plan_pre_round_refuses_on_envelope`
Cluster: docs/history/backlog/2026-10-23-gate-ledger-cli-tests-hermetic-environment.md (same defect class - a suite test not hermetic to its checkout environment - different surface and mechanism: that row's child process inherits host environment variables, this row's subprocess reads the checkout's gitignored facts file)
Cluster: docs/history/backlog/2026-10-27-done-setup-facts-provisioning-fresh-worktree.md (same gitignored-facts defect class, different surface and consumer: this row's scope is the readiness suite's test class, that row's is the done boundary setup's own resolution in the ad-hoc worktree flow)

## Observed

`ReadinessSingleFileUnchangedTest.test_landed_plan_pre_round_refuses_on_envelope` invokes the real `scripts/plan_readiness.py --pre-round` as a subprocess against the real repository root. The script resolves `plans_dir`/`reviews_dir` from the checkout's `.ai-playbook/facts.md`, which is gitignored. In the primary checkout (facts file present) the test passes; in any fresh worktree or CI-style checkout (facts file absent) the script fails earlier with `readiness FAILED: cannot resolve plans_dir/reviews_dir from the facts TOML block` instead of the pinned `readiness PRE-ROUND FAILED:` prefix, so the test reports red for an environment reason, not a code reason. Reproduced 2026-10-27 in a scratch worktree at both d7e163df6 and c63064b52 (fails in the worktree, passes at the same tip in the primary checkout), so the dependence is the checkout, not a commit regression. About ten sibling classes in the same file already build a temp root with their own `.ai-playbook/facts.md` written into it; this class is the one that escapes that pattern.

## Expected

The suite is hermetic: the envelope test runs green in any checkout of the repository, with or without the gitignored facts file, and its pinned refusal assertions exercise the pre-round gate rather than the facts-resolution failure path.

## Suggested fix

Move the class to the temp-root fixture pattern its siblings use: a per-test temp root carrying a minimal facts TOML block (plans_dir and reviews_dir keys), the landed completed plan fixture, and its reviews home, with the subprocess pointed at that root, so the pinned refusal assertions bite the real gate surface. Single-surface scripted fix in `scripts/test_plan_readiness.py`; no production script change.

## Witness

- Reproduction: scratch worktree at d7e163df6 and at c63064b52 - the test fails in the worktree (`cannot resolve plans_dir/reviews_dir from the facts TOML block`) and passes at the identical tip in the primary checkout.
- Panel witness: the pick-1 focused-panel correctness worker flagged the same failure inside the run's ad-hoc worktree and correctly classified it as not branch debt.
- Suite state at the tip: full `test_plan_readiness.py` green in the primary checkout (173 passed + 58 subtests).
