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

## Additional witness: completed run leaves two live checkouts (2026-09-30)

The CRM-<ID> run currently has the primary `sporty-crm-profile` checkout on `CRM-<ID>-fact-reconcile-worker-rebased` and an attached Codex worktree on `codex/crm-<id>-criteria-compact`. The worktree has an uncommitted update to `docs/history/plans/CRM-<ID>-fact-reconcile-worker.md`; the primary checkout has separate uncommitted implementation/configuration changes. A second detached worktree, `execute-plan-scope-recovery`, is rooted at the unrelated `origin/master` tip and is not the CRM-<ID> source branch. The Codex artifact list is empty, while Git confirms the `codex/crm-<id>-criteria-compact` branch is still linked to its worktree.

This exposes a handoff/closeout gap adjacent to the post-squash stale-ref case: an execution can be active in a worktree and later proceed in the primary checkout, without a visible run-level disposition saying whether the original worktree is still canonical, has unique untransferred edits, or can be retired. Chat summaries identify active sessions only imperfectly, so a cleanup decision needs evidence from run ownership plus the actual checkout state rather than branch age or task title. Do not remove either CRM-<ID> location while these distinct uncommitted changes remain. The detached scope-recovery worktree also needs an explicit owner/status lookup before cleanup; its origin/master tip alone does not prove it is abandoned.

Extend the expected closeout behavior to reconcile all checkouts for the exact run after a handoff or landing: identify the canonical run checkout and branch; enumerate other attached, detached, and archived worktrees; compare their tracked and untracked state and commits against the canonical destination; transfer or explicitly disposition unique edits; verify no active run manifest, task, or process owns the checkout; then archive/remove only the proven redundant worktree and its exact branch ref. Report retained worktrees, detached recovery artifacts, and platform-preserved snapshots with their owner and reason. A blocked ownership or transfer check retains the checkout and names the evidence still needed.

## Follow-up disposition: CRM-<ID> worktrees (2026-09-30)

The detached `execute-plan-scope-recovery` worktree was clean and at `2a92820e`, an ancestor of `CRM-<ID>-fact-reconcile-worker-rebased` (`6a58695d`). No active thread in the available Codex task list used that checkout. It was removed with `git worktree remove`; the CRM-<ID> branch retains the commit history. The `codex/crm-<id>-criteria-compact` worktree belongs to the active **Execute CRM-<ID> plan** session (thread `01a0ee06-6e8c-73a2-b606-2821a70415c0`). Its `docs/history/plans/CRM-<ID>-fact-reconcile-worker.md` has uncommitted edits and that plan file is absent from the primary checkout, so the worktree and branch are retained until the unique plan changes are transferred or explicitly dispositioned. This confirms cleanup must be per-checkout and evidence-based: a merged clean detached checkout can be removed, while a still-owned checkout with unique edits cannot.
