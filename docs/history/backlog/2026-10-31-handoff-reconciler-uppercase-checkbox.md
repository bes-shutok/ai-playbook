# Backlog: Handle uppercase [X] checkbox markers in the handoff reconciler projection

Driving force: code-quality. `scripts/reconcile_execute_plan_handoff.py` checkbox regexes match only lowercase markers; a GFM-valid `- [X]` section reconciles successfully while storing a false projection (checkbox False, 0/0), satisfying the projection-incomplete gate with an empty projection. Normalize the marker class case-insensitively or refuse uppercase markers as an unsupported shape. Found by the Task 1 intermediate review (risk lens, 2026-10-31).
