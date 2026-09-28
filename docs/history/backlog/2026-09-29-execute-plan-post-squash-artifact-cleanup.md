# Execute-plan closeout leaves stale run branches after squash landing

- **Filed:** 2026-09-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** hygiene
- **Driving force:** reliability; simplicity
- **Origin class:** witnessed-incident
- **Source:** ai-playbook execute-plan follow-up session, 2026-09-29. The reviewed authoring worktree was archived after its plan was squash-landed on `main` (`f0d851a2`). The plan was later executed and completed on `main` (`41a4dc2b`), but `codex/execute-plan-preflight-followup` remained as a branch ref without a linked worktree. The app's archived-worktree record retained a recoverable snapshot, which explains why archiving did not remove the branch. A separate `codex/execute-plan-scope-recovery` branch still has a live worktree and is active, so it must be preserved.

## Problem

The execute-plan worktree-first standard already says to delete a run's worktree and branch after artifact transfer is verified. In practice, managed worktree archival was treated as full cleanup. Archival preserves a recoverable snapshot and the source branch ref; it does not prove the source branch is still needed or remove it. The branch left behind after its reviewed work had landed and the plan had completed.

A related open item, `docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md`, covers redundant worktrees and says to delete a branch after ancestry proves its commits reachable from the destination. That condition does not cover a squash landing, which intentionally creates a new destination commit instead of preserving source-commit ancestry. This item covers that missing closeout case and the run's other disposable artifacts.

## Expected behavior

- Closeout retains one exact run identity linking its source branch, worktree, landing destination, and run-owned artifacts.
- After landing, closeout verifies the intended changes are present on the destination even when squash means source commits are not ancestors. It also verifies that required review and other durable artifacts were transferred before any cleanup.
- Once those checks pass and no live task or process uses the run, clean up only that run's source branch and disposable artifacts. Preserve durable plan history and review evidence. Preserve an archived recovery snapshot when the platform requires it, and report it as intentionally retained rather than claiming complete removal.
- A failed landing, artifact transfer, or liveness check retains the source branch and worktree for recovery. Active sibling branches and unrelated worktrees are never selected by a prefix-wide cleanup.
- Closeout records the exact removed and retained run artifacts, including any archived snapshot that has no supported deletion operation.

## Possibility space

- **Recommended: add a post-squash closeout arm to the existing worktree lifecycle.** Prove the landed content and artifact transfer for the exact run, then remove its branch and disposable run artifacts while preserving durable outputs and any platform-owned recovery snapshot.
- **Delete every `codex/*` branch after a landing:** rejected; it would remove active work such as the live scope-recovery branch.
- **Require source commits to be ancestors before branch deletion:** rejected as the only proof; it cannot succeed after a squash landing.
- **Treat archive as complete cleanup:** rejected; the archived worktree and branch remained after the plan completed, leaving stale refs without a disposition.
- **Use blanket `git clean` or delete the archived snapshot by filesystem path:** rejected; either can remove another run's work or bypass the platform's recovery and ownership rules.

## Dedup probe

Read `docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md` in full. It addresses duplicate run worktrees, landing choice, archive refusal, and branch removal when ancestry proves the commit is reachable. Its witness is distinct and its ancestry-only branch-removal condition leaves the squash case open. Nearby worktree closeout items cover pre-teardown artifact migration and manifest recovery, not removal of stale source refs after a successful squash landing.

## Suggested fix

Extend the existing execute-plan closeout rather than adding a second cleanup framework. Capture exact run-owned refs and artifacts; after a squash landing, verify the destination against the run's landed change set and verify each durable artifact at its destination; then reconcile the exact source ref and disposable run outputs. Keep the app-managed archived snapshot when it is the supported recoverability record, but make that retained state visible. Add witnesses for a successful squash, an ordinary ancestry-preserving landing, a live sibling branch, a failed artifact migration, durable review retention, and a platform-retained archive.

## Evidence and scope boundary

Current refs show `codex/execute-plan-preflight-followup` has no linked worktree and belongs to the archived authoring worktree. The reviewed work was landed by `f0d851a2`, and the plan implementation later landed by `41a4dc2b`. `codex/execute-plan-scope-recovery` has a linked worktree and remains active. This capture requests a future closeout improvement; it does not authorize deleting either branch or changing current archived artifacts.
