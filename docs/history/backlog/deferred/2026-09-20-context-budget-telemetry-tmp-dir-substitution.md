# Backlog: telemetry-path tmp_dir substitution vs placeholder-free literals (review-loop + maintenance blueprints)

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; telemetry path split reachable only on facts.md-overriding installs. Revive on an overriding install is actually used here, or a project-priority-profile change.)
Workflow: backlog
Source: Task 3 Step 1.2b intermediate review of docs/plans/2026-09-19-context-budget-and-telemetry-long-running-skills.md (contract-docs lens, 2026-09-20; triaged valid off-plan candidate, deferred per the backlog-deferral default — the landed text matches the plan's prescribed literal verbatim, so this is a plan-level design residue, not an implementation error).
Severity: Low
Exact location: agents/skills/review-loop/SKILL.md round-boundary checkpoint paragraph (telemetry file `docs/tmp/review-loop/<branch-slug>/context.jsonl`); the same literal-vs-substitution question covers the Task 4 maintenance blueprint paths (`docs/tmp/execute-plan/<plan-slug>/context.jsonl`, `docs/tmp/authoring/<plan-slug>/context.jsonl` in agents/skills/maintenance/prompt-templates.md).
Why not fixed now: the plan's Tasks 3 and 4 deliberately prescribe placeholder-free literal paths (the pins suite pins the placeholder set exactly), and the execution must land the prescribed text verbatim; changing the wording is off-plan and would deviate from the certified landing text.
Driving force: simplicity

## Problem

Under a project whose `.ai-playbook/facts.md` overrides `{tmp_dir}`, a literal reading of the new telemetry duties logs per-run context telemetry to `docs/tmp/...` while the same project's execute-plan runs substitute the overridden prefix for their own paths — split telemetry locations in the archived corpus. Reachable only on overriding installs; default installs are unaffected. The execute-plan `Context budget checkpoints` policy already carries a `{tmp_dir}` substitution rule for its own paths (substitute the resolved `{tmp_dir}` for the `docs/tmp/` prefix when facts.md overrides the default) but does not state that the rule governs the per-skill telemetry paths named in review-loop and the maintenance blueprints.

Fix (single-point, covers all three sites): add one sentence to execute-plan's `Context budget checkpoints` Telemetry bullet stating the substitution rule governs all per-skill telemetry paths (review-loop's `docs/tmp/review-loop/<branch-slug>/context.jsonl` and the maintenance blueprints' two paths included, and the Phase 4 archive destination with its Phase 5 checklist wording (`docs/tmp/context-telemetry/<plan-slug>.jsonl`), which currently pin the literal default prefix with no substitution statement (Phase 3 r1 code review, 2026-09-20)).
