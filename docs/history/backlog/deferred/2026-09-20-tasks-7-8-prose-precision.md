# Backlog: Tasks 7-8 prose precision residuals

Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; prose precision. Revive on the sentences are next touched, or a project-priority-profile change.)

- Status: open
- Origin: Tasks 7-8 intermediate review (r1 F1, F2) of 2026-09-20-merge-landing-lock-grouping; verdict backlogged-candidates
- Driving force: two freshly landed sentences are mildly imprecise against the surfaces they describe, so future readers may over- or under-generalize the sweep scope and the sync abort set.

## Items

1. execute-plan SKILL.md exit-path paragraph uses the literal `docs/tmp/` where the `{tmp_dir}` placeholder would stay correct if facts.md customizes tmp_dir; normalize to the placeholder like the rest of the paragraph.
2. docs-branch SKILL.md `Failure semantics (sync):` paragraph names the two plan-mandated exit-1 aborts but the fence also contains "invalid docs/* branches" and "Refusing unsafe shadow path" aborts; consider enumerating them for completeness.
