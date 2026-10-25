# Backlog: task-primary worktree archive refusal strands an already-landed checkout

- **Filed:** 2026-10-25, self-heal after task-primary archive refusal
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** task-owned worktree cleanup blocked by app ownership
- **Class:** managed worktree terminal ownership gap
- **Driving force:** operator time + reliability
- **Related backlog:** `docs/history/backlog/2026-10-13-codex-task-resource-cleanup.md` (general task-resource ownership; its completed investigation did not resolve task-primary archive refusal)

## Problem

After this task's changes and ignored review artifacts were landed or migrated to the primary checkout, the closeout gate reported the exact source worktree removable. The app's `archive_worktree` operation refused because that checkout was the task's primary checkout. Attaching the actual main checkout as a replacement also refused because it is not an app-managed worktree. The session stopped before checking whether a supported ownership transition could make the exact landed checkout archivable. The obstacle is at the app-managed task ownership boundary, not the repository's transfer or landedness checks.

## Evidence

- The closeout gate's existing task-specific output authorized removal only after artifact migration and exact-tree accounting; `agents/skills/done/SKILL.md` names app-managed archival as the supported removal route and forbids raw managed-worktree deletion.
- The app tool refused to archive the attached task-primary checkout and refused to attach the unmanaged main checkout; both refusals occurred in this session after the landed work and artifact migration.
- In follow-up, the backlog and closeout commits were made directly in the main checkout while this task remained attached to a managed worktree. This confirms repository work can continue in main without rebinding the app task. The available app operations expose managed-worktree creation, attachment, archive, and restore, but no task-primary rebind or detach operation; attaching main still fails because it is unmanaged.
- `docs/history/plans/completed/2026-10-13-codex-task-resource-cleanup.md` and `docs/history/plans/completed/2026-10-15-codex-task-resource-cleanup-evidence-recovery.md` investigated task-resource ownership but did not test this exact post-landing primary-checkout refusal or an ownership handoff.
- `docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md` and `docs/history/plans/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md` cover project-run closeout follow-through; the current gate passed, so the unresolved boundary is the app's primary-checkout restriction.

## Expected

When an exact task-owned worktree is fully landed, clean, and artifact-verified, the owning task can complete a supported ownership transition and archive it, or report a precise platform limitation with a viable continuation path. The app must continue protecting a checkout while it is the task's active primary workspace.

## Suggested direction

Investigate whether the app supports rebinding a task to the unmanaged main checkout or detaching its primary-worktree ownership. Repository work can already continue through an explicit main-checkout path; creating a replacement managed worktree only moves the primary-checkout restriction and leaves another task checkout. Compare any app-supported rebind/detach operation with retaining the current protection and reporting the platform limitation. Do not raw-remove a managed checkout or weaken the refusal based only on landedness.

## Alternatives

- **Remove the primary-checkout refusal:** not yet justified; the refusal protects the active task workspace from deletion, and this incident does not establish that the app can safely switch its execution context first (current tool refusal in this session).
- **Keep the refusal and add an ownership transition:** preferred for investigation because the archive API already accepts exact managed worktrees after they cease to be primary; verify whether the available create/attach flow supplies that transition before proposing code or policy changes (`agents/skills/execute-plan/worktree-first.md`).
- **Use project closeout or raw Git worktree removal:** rejected because project closeout gates do not transfer ownership of this app-managed attachment, and the done contract explicitly forbids raw managed-worktree deletion (`agents/skills/done/SKILL.md`).

## Machinery assessment

No new gate, hook, or ledger is proposed. The incident is one witnessed refusal; the false-positive cost of weakening a primary-workspace protection is loss of the active checkout. First test the existing ownership transition and simplify any unnecessary handoff if supported.

## Recovery witness

Creating a clean managed replacement at the landed primary-checkout commit changed the active task attachment sufficiently for the app archive operation to archive the original task-primary worktree. After verifying the archived path was absent, no Git registration still named the run branch, and its ref still matched the gate's previously proven OID, the branch was removed with an expected-OID compare. The original worktree and branch are gone. A replacement managed checkout remains the active task workspace; the app still does not support attaching the unmanaged primary checkout directly, so the broader ownership transition and terminal cleanup contract remain unresolved.
