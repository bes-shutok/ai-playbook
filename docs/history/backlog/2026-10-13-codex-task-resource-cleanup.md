# Backlog: Codex task-owned branches and worktree remnants lack a terminal cleanup owner

- **Filed:** 2026-10-13, operator-directed local cleanup
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed local branch and worktree residue
- **Class:** Codex task resource lifecycle gap
- **Driving force:** operator time + reliability
- **Skill/step:** Codex task/worktree lifecycle; local Git branch and worktree cleanup
- **Related backlog:** `docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md` (project-owned execution worktree transfer and closeout is a separate owner boundary)

## Problem

A local inventory found completed `codex/*` refs that were already contained in the local base but remained after their task work had ended, along with empty or marker-only worktree-root directories. The user had to request cleanup. Other registered checkouts still contained uncommitted work or commits outside the local base, so deleting every Codex-named resource would risk losing work. The current workflow does not make clear who owns terminal cleanup for task-created local resources, or how to distinguish safe residue from preserved work.

## Evidence

- On 2026-10-13, four local `codex/*` refs already ancestral to the local base and seven empty or marker-only worktree-root directories were removed. Of the six registered non-primary worktrees in the initial inventory, two clean worktrees whose tips were already in the local base were removed after re-derivation; three of the four remaining worktrees have uncommitted changes and commits outside the local base, and the clean fourth has commits outside the local base.
- A prior Codex worktree review found that a completed plan had replaced the branch's only unmerged plan with a completed version on the local base; removal happened only after a separate user request (`docs/history/plans/completed/2026-10-01-codex-model-guard-runtime-alignment.md`).
- Re-witnessed in a later session: `create_worktree` completed, `archive_worktree` returned queued, and the artifact listing reported the worktree archived. The checkout was gone, but its parent directory remained with only the zero-byte `.codex-worktree-name` marker. After verifying the parent held no other entries, the session removed the marker and used non-recursive `rmdir`; no branch, checkout, or user data was removed. This identifies the residue as the named parent container left after archive, rather than a live Git worktree.
- Project closeout does name a cleanup owner for its own execution worktrees, but its transfer and removal gates are scoped to that run (`agents/skills/execute-plan/SKILL.md`, Phase 5; `agents/skills/done/SKILL.md`, worktree transfer-out and removal). The residue sweep also recognizes a narrower task-worktree shape (`scripts/worktree_closeout_migrate.py`).
- The machinery blocker audit rates worktree lifecycle and recovery as a recurring blocker family and warns that additional cleanup ceremony has a cost (`docs/maintenance/machinery-blocker-audit-2026-10-09.md`).

## Expected

A completed Codex task has one clear owner for deciding whether its exact local worktree and branch are removable. Cleanup preserves any dirty or unmerged work, removes only resources whose ownership and landed state are verified, and reports resources retained for review. Empty setup remnants should not persist after their creation attempt has ended.

## Suggested direction

Trace the current Codex task/worktree lifecycle and the local mechanisms that create, retain, or remove task resources. Establish whether cleanup is intentionally delegated to the operator, omitted from task completion, or unavailable for resources outside a managed-artifact attachment. Reuse an existing owner or supported closeout path if one exists. When a successful archive leaves only its exact empty name-parent marker, let that operation's owner remove the marker and parent with non-recursive cleanup; preserve and report any parent that contains other entries. Do not add a background sweeper, global Git hook, ledger, or mandatory cleanup ceremony unless a witnessed failure proves that simpler ownership cannot work and the machinery admission protocol is met.

## Alternatives

- **Delete every branch or directory with a Codex-looking name:** rejected because the 2026-10-13 inventory included registered worktrees with uncommitted changes or commits not contained in the local base; names do not prove that their content is disposable (`docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`).
- **Keep all Codex task resources indefinitely:** rejected because four already-landed local refs and seven empty or marker-only directories required a separate operator cleanup on 2026-10-13 (`docs/history/plans/completed/2026-10-01-codex-model-guard-runtime-alignment.md`).
- **Add a global cleanup hook or recurring inventory ledger:** rejected because task ownership and safe landing cannot be inferred from names, while the existing project-specific closeout is narrower and the machinery audit prices extra ceremony (`docs/maintenance/machinery-blocker-audit-2026-10-09.md`).
- **Extend project `done` closeout to own all Codex-created resources:** rejected pending evidence that those resources belong to the project's execution run; the existing contract gates transfer and removal for a specific run worktree (`agents/skills/done/SKILL.md`).

## Machinery assessment

No new gate, hook, or ledger is admitted by this backlog. The observed local inventory establishes a cleanup miss but not a recurring catch rate for a proposed automatic mechanism; the false-positive cost of removing active or unmerged work is high. Reassess only after tracing the current lifecycle and applying the machinery admission protocol.
