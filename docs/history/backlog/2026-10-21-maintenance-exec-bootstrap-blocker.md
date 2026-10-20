# Backlog: maintenance exec can enter work without a recoverable checkout bootstrap

- **Filed:** 2026-10-21, after `maintenance exec` could not start its requested backlog item in a fresh worktree
- **Status:** covered (docs/history/plans/2026-10-21-maintenance-exec-bootstrap-lapse-disposition.md)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** session-witnessed workflow blocker
- **Class:** investigate-class
- **Skill/step:** `agents/skills/maintenance/SKILL.md` exec dispatch and `agents/skills/execute-plan/SKILL.md` Worktree-first standard transfer-in
- **Driving force:** continuity (the requested task could not reach its first edit because required checkout inputs and closeout state were not prepared)

## Problem

The `maintenance exec` request for `2026-10-21-requested-test-scope-incomplete.md` started in a fresh worktree without the gitignored `.ai-playbook/facts.md` and other required transfer-in inputs. The first done setup therefore failed. A retry in the primary checkout then exposed two unfinished manifests for dead worktree roots; after their supported dead-root dispositions, setup advanced but refused to write a manifest because the primary review staging directory had 3,191 unrelated candidates that had not been classified as foreign. The supported `--foreign-review-from` path allowed setup to pass without changing those review files. Setup still reports a separate older dead-root manifest as a non-blocking warning.

The immediate recovery used existing mechanisms: close only dead-root manifests after their deliverable witnesses pass, explicitly classify unrelated review candidates as foreign, and transfer the facts file and reviews directory before setting up a fresh worktree. The bootstrap contract should make those steps discoverable and ordered before the first gate, and should distinguish blockers from warning-only inherited state. Do not add a new gate or broaden the review candidate classification silently.

## Expected

An `exec` run reaches its first setup with the required gitignored inputs copied from the primary checkout, follows the supported interrupted-manifest disposition path when a dead-root record blocks setup, and classifies existing review staging candidates through the runner's supported bulk input. Report any remaining warning without treating it as a fresh-run blocker. Keep the primary checkout's unrelated dirt untouched.

## Origin disposition

The independent test-scope item was completed locally by `99e8fb44a2aacaccc2b2fbb01b40555e33cbcf2c`. This row concerns maintenance/worktree setup and remains a separate open investigation.

## Investigation prompt

Trace the `maintenance exec` dispatch from the ready `EXEC-PROMPTS.md` item through worktree creation, transfer-in, done setup, and manifest writing. Compare the failed managed-worktree attempt with the successful primary-checkout setup and the documented Worktree-first transfer-in path. Identify the smallest existing contract or invocation gap that omitted `.ai-playbook/facts.md` and the other required inputs, and determine whether the 3,191-candidate bulk classification should be a caller responsibility or a documented setup step. Review related dead-root disposition guidance and backlog coverage; recommend whether to remove, simplify, or retain any origin workflow text. Prefer wiring existing supported steps over adding machinery. Record the resolution in the maintenance/worktree workflow and add a focused regression check for a fresh checkout with gitignored inputs absent and unrelated review candidates present.
