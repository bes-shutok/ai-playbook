# plan-readiness consumer-ordering + docs residuals

Backlog origin: execution residual of docs/history/plans/2026-11-06-plan-readiness-planned-path-lifecycle.md (exec review r1, ready=yes zero blocking, digest 9ecf0c6a).

Driving force: correctness

- Clause (b) consumer-before-owner orders by document position, so unpadded-filename directory assembly can judge cross-task checklist references by assembly order rather than heading ordinal; clause (c) got ordinal ordering in the executed plan, clause (b) did not (pre-existing, left untouched by scope).
- The plans skill Files-grammar bullet documents only the bare `*(deleted)*` form; the elaboration form (`*(deleted; see Task 2)*`) lives in the validator docstring and plan Terms only.
- Clause (c) recomputes `_plan_task_sections` for ordinals instead of reusing the section titles in hand (pure function, provably aligned; simplification candidate).
