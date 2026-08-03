# Project decisions

Architectural and workflow decisions for the ai-playbook instruction repository. Newest entries append at the bottom.

## ADR-0001: Immutable completed history and non-mirror context

Completed implementation plans, completed review digests, and non-mirror context under `docs/history/context/` (and legacy `docs/context/`) are immutable historical records of considerations at the time. Do not annotate or rewrite them to reinterpret process outcomes after the fact. Allowed edits only after explicit user confirmation for factual corruption (for example leaked secrets or broken paths). Confluence mirrors under `docs/history/context/confluence/` may refresh to match the wiki; that sync is not a license to revise completed plans or non-mirror context.

**Considered options:** leave only one prior completed plan untouched; annotate completed plans for honesty; freeze the entire context tree including Confluence mirrors.

**Consequences:** prevention work is forward-looking (skills and guidelines). Completed plans are context, not templates for copying rollout checklist shapes into new plans. New plans classify candidates as repository implementation, external prerequisites, or release gates. Only repository implementation becomes an executable plan task by default. A release-gate exception requires a current bound receipt (exact confirmation text or stable message reference, specific checklist item, target or environment, confirmation time or session), a meaningful `why executable now`, and observable `completion evidence` in the plan file. External prerequisites are never exception-admissible. `done` Confluence mirror sync remains valid. Future readers must not expect archives to be patched when process rules change.
