# AI playbook

Ubiquitous language for agent workflow and planning in this repository.

## Language

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
