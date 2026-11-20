# Backlog: Fix the shared span-rule claim in the handoff reconciler docstring

Driving force: docs (source-of-truth drift). `scripts/reconcile_execute_plan_handoff.py` claims it uses "the shared plan_task_span span rule" but restates the span extraction inline; the receipt's scope binding rests on two unlinked implementations. Either import the span extraction from `scripts/plan_task_span.py` or reword the docstring to "same rule, restated here". Found by the Task 1 intermediate review (contract-docs lens, 2026-10-31).
