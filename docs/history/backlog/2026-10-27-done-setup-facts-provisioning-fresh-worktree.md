# Backlog: done setup in a fresh ad-hoc worktree fails on the gitignored facts block with no named remedy

- **Filed:** 2026-10-27
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** `docs/history/backlog/2026-10-27-plan-readiness-envelope-test-facts-hermeticity.md` (same defect class - a surface reading the checkout's gitignored `.ai-playbook/facts.md` that fails in any fresh worktree where the file is absent - different surface and consumer: that row's scope is the readiness suite's test class, this row's is the done boundary setup's own facts resolution in the ad-hoc worktree flow)
- **Skill/step:** `scripts/done_sweep_gates_lib.py` `_resolve_dir` (the fail-closed facts-key resolution whose ValueError rides the `config error:` handlers that `done_run.sh` setup surfaces); the ad-hoc worktree provisioning flow in `agents/skills/execute-plan/worktree-first.md` (the Transfer-in implementation copies facts, reviews, and review-certs for plan runs; the ad-hoc (no-plan) flow has no fence leg that provisions the facts file)
- **Class:** fix-class
- **Origin class:** session witness (ad-hoc exec run start mechanics)

## Finding

A fresh ad-hoc worktree has no gitignored home at all, so its first `done_run.sh setup` fails the manifest writer with `config error: cannot resolve plans_dir from .ai-playbook/facts.md (the facts block is the single source for repo paths; complete the facts block before running the gates)` - an instruction that reads as a repo misconfiguration but is in fact the routine fresh-worktree shape. The output does say to complete the facts block, but not that the file is machine-local by design (never rides the branch) nor the concrete remedy; the working fix (copy the primary checkout's facts block into the worktree, `mkdir -p .ai-playbook` first because even the parent directory is absent) lives only in session experience, and the transfer-in fence that would provision the file is scoped to plan runs. Witnessed twice in one session (2026-10-27, both ad-hoc picks of the 20:00 exec run; the first remedy attempt also failed by skipping the missing parent directory, recorded as project lesson 278).

## Expected

Either the setup failure output names the concrete remedy (copy the primary checkout's facts block; create the parent first), or the ad-hoc worktree flow provisions the facts file the way the plan-run fence does, so a fresh worktree's first setup passes without a diagnosis round.

## Suggested direction

Bounded arms: (1) widen the `_resolve_dir` ValueError's remedy text to name the copy-from-primary step and the missing parent directory, or (2) give the ad-hoc worktree provisioning path the same facts-provisioning leg the plan-run fence has. Prefer (1) as the smaller arm; (2) touches the worktree-first standard's fence text and prices a prose change against a one-line error message. No new gate, validator, or machinery.

## Evidence

- Witnessed 2026-10-27: both picks' first setup outputs (the facts-resolution tool error), the failed bare-copy attempt, and the passing post-provision re-runs.
- A fresh worktree created for this row's filing session confirms the empty-home shape (no `.ai-playbook` directory until provisioned).
