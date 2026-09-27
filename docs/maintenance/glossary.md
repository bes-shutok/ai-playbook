# AI playbook

Ubiquitous language for agent workflow and planning in this repository.

## Language

**Single-operator setup**:
An agent work environment where one person controls the local machine, project checkouts, and configured tools.
_Avoid_: shared-agent workstation

**Rejected plan or backlog item**:
A proposed change explicitly decided against; retain its record under the repository's rejected archive instead of deleting it.
_Avoid_: completed item

**Executable plan task**:
A checklist item the default executor can finish now from the target repo and local tooling, without a blocked shared environment or another team's deploy.
_Avoid_: release gate (as a checkbox), rollout step, staging verification task

**Repository implementation**:
Work in the target repository that the default executor can complete and verify now with available local tooling. It becomes an executable plan task by default.
_Avoid_: external prerequisite, release gate

**External prerequisite**:
Work owned outside the current repo or ticket that must exist before a Ship-when condition can be met (another service, ticket, or team).
_Avoid_: implementation task, local verify

**Release gate**:
A Ship-when condition that needs deployed, cross-team, or human-owned evidence. It may appear in plan prose; it must not become a checklist item unless the user confirms an exception. An admitted exception must record a bound receipt (exact confirmation text or stable message reference, specific checklist item, target or environment, confirmation time or session), a meaningful `why executable now`, and observable `completion evidence` in the plan file. External prerequisites are never exception-admissible.
_Avoid_: Done-when check, executable plan task

**Done when**:
The executable success criteria for the implementation phase (local quality dimensions and repo-verifiable checks).
_Avoid_: Ship when, release complete

**Ship when**:
Narrative release dependencies that remain after the implementation phase. No checkboxes; optional Jira tracking only after the user confirms ticket creation.
_Avoid_: Done when, plan archive meaning production-ready

**Completed history artifact**:
A finished plan under `{plans_completed_dir}`, a completed review digest, or non-mirror docs under `docs/history/context/` (and legacy `docs/context/`). Treat as immutable historical context of considerations at the time.
_Avoid_: living guideline, editable draft

**Confluence mirror**:
A wiki snapshot under `docs/history/context/confluence/` that may refresh to match the external page. Not a process-outcome reinterpretation of a completed plan.
_Avoid_: completed history artifact (for immutability rules)

**Review iteration cap**:
The total count of review rounds in one execute-plan Phase 3 loop, counting full-panel and focused rounds alike, stated as the `max_review_rounds` budget (default 5) in the execute-plan Review end condition table. Counting, stop, and standing-instruction semantics are owned by execute-plan Step 3.5.
_Avoid_: full-panel cap (counts only all-five-worker rounds), `max_full_panel_rounds`

**Sibling-doc restatement**:
A living document that restates a cross-cutting rule whose canonical home already states it correctly. During execute-plan Phase 3 addressing, a peer on a shipped doc surface converts to a pointer on the canonical home in the same pass; only a non-shipped or legacy peer defers as one pointer-cleanup backlog item instead of being fixed as a new finding that extends the loop (see `receiving-review`).
_Avoid_: independent contract bug, per-surface docs drift

**Duplicate unit witness**:
A test finding that demands an assertion for a production-path invariant another test demonstrably pins (the pinning test is named and fails when the invariant is violated; for example call order asserted on one unit, now demanded of a sibling unit). During execute-plan Phase 3 addressing, it is deferred to backlog as one family-completeness item instead of being fixed round after round. A pin that cannot be reproduced as a failure under a violated-invariant mutation disqualifies the class and reverts the finding to the fix-everything default (see `receiving-review`).
_Avoid_: per-test always-passes fix

**Ownership registry**:
One central Layer 2 file (path resolved via facts keys, e.g. `docs/maintenance/document-registry.md`) mapping stable document identity to the current living SOT, archived history artifacts, and aliases. Updated only within lifecycle transitions (plan completion, backlog archival, RFC closure); never edited in place via stub files. Decided 2026-09-08 (ADR trail for backlog `2026-09-08-document-ownership-and-archive-lifecycle`).
_Avoid_: per-doc frontmatter as the registry, "# Moved to" stub redirect

**Document identity**:
A stable capability or concept identifier naming what a document owns, independent of any ticket, branch, or implementation task. Tickets and session ids may appear as provenance, never as the durable key.
_Avoid_: ticket-id-keyed doc name, branch-scoped identity

**Living SOT**:
The one document or wire/schema source that owns the current normative rule for an idea. May change freely while its owning work is active; on completion or supersession the rule's home becomes a completed history artifact plus a successor entry in the ownership registry.
_Avoid_: historical artifact (for a living doc), frozen context (a completed history artifact under `docs/history/context/`, not a separate state)

**Release (run)**:
One invocation of the `release` skill: squash the unpushed `main` commits into a few feature commits, write a dated `CHANGELOG.md` entry, and publish to the remote after the safety and privacy gates. A publishing action owned by the release workflow, not a plans-domain checkpoint; the plans-domain `Release gate` term keeps its own meaning.
_Avoid_: release gate
