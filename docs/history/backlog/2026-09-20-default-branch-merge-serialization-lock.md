# Backlog: default-branch merge serialization lock (authoring self-landing vs execution final squash)

Status: open
Origin: Andrey, 2026-09-20 (dispatch-prompt worktree-isolation discussion)

Two child kinds can now land commits onto the repository default branch, and nothing serializes them against each other:

- Execution children finish with their own "Finally squash merge to main" paragraph (execution blueprint, prompt-templates.md): gates, squash commit onto main, branch deletion.
- Authoring children are moving (2026-09-20 user-directed dispatch-prompt improvement) to ad-hoc-worktree isolation with a self-landing: after the done skill, one squash commit carrying only the task's files lands on the default branch (in whichever checkout holds it), then the worktree and authoring branch are deleted.

The done-lock serializes done sweeps but not final merges/landings, and `G3 (joint state)` only sees an in-progress merge/rebase or a held done-lock, not a landing in flight. Races to price: index/commit interleaving in the checkout that holds the default branch; an execution's tree-identical gate (`git diff <branch> main` empty) failing because an authoring landing moved main mid-gate; branch-deletion and worktree-removal races; hygiene/PII gate runs interleaving with someone else's staged state.

Requested work (plans + review process, not ad-hoc template edits): a maintenance-skill update, in one pass across SKILL.md, prompt-templates.md (both blueprints), and the zcode overlay, that defines a merge/landing lock held across the whole landing critical section (pre-commit gates, commit onto the default branch, branch deletion) by both child kinds, with the guards made aware of it (a `G3` arm or a new lane-guard arm so a scheduler turn neither dispatches into an in-flight landing nor stands down needlessly) and with both payloads acquiring the lock before landing and standing down or retrying on contention. Candidate mechanism: extend `scripts/done-lock.sh` with a distinct merge mode or add a sibling merge-lock script.

Design direction from Andrey (2026-09-20): keep the landing itself the last, minimal step. The worktree run prepares and verifies everything; the landing is just copying the changed files into the checkout that holds the default branch and making one pathspec-scoped commit there, so the lock's critical section stays as short as possible.

State note for the future plan: the 2026-09-20 ad-hoc edits to maintenance SKILL.md / prompt-templates.md / zcode.md (worktree-isolation blueprint rewrite plus the G1a/D2/overlay rewording) were REVERTED pending this item, so the blueprints still carry the pre-worktree joint-state riding model, while the standalone manual dispatch prompt carries the self-landing paragraph in its unserialized v1 form. The plan should reconcile blueprint, SKILL.md, overlay, and the standalone form with the lock in one pass. Per-execution worktree isolation stays rejected (2026-09-19 concurrency stance); this item serializes landings, it does not parallelize executions.
