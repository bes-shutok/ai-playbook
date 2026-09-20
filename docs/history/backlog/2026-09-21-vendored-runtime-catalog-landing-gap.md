# Backlog: runtime-catalog edits made mid-execution strand the vendored repo copy

Status: open
Priority: high
Workflow: backlog
Source: session question (2026-09-21) on the context-budget execution closeout: the review-plan iteration-discipline rule 5 forced a catalog fix (a new testing-catalog section) into the runtime registry during execution; the edit was deliberately outside the plan's Files scope and its vendored repo twin later appeared as uncommitted, byte-identical dirt on the integration branch that nobody on the exec side owned.
Severity: Low (process; the runtime copy is authoritative so no agent sees stale behavior, but the repo twin drifts or arrives as orphan dirt)
Exact location: the review-plan skill's Iteration Discipline rule 5 (catalog gap -> update the skill first) and the skills-repo vendored-asset sync rules; the gap is the missing landing-path clause between them.
Why not fixed now: the rule addition belongs to the owning skill's text and the runtime/vendored split makes it a cross-surface edit; captured during done with the execution closed.
Driving force: simplicity

## Problem

When an execution session edits the runtime skill registry under review-plan rule 5, the repo's vendored copy has no defined landing path: the session correctly does not widen its done commits, so the change either strands in the runtime tree only (repo/runtime drift until the next manual sync) or arrives as uncommitted working-tree dirt attributed to no session.

Fix: add one clause to rule 5 (or the vendored-sync rules): when rule 5 forces a runtime-catalog edit during an execution, the session must either (a) land the vendored copy in the same run when the file is in the plan's scope, or (b) file a vendored-sync backlog item naming the changed files, so the twin is a tracked handoff instead of orphan dirt.
