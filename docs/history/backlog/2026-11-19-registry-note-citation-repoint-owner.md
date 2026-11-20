# Backlog: registry note-internal citation re-point owner

Driving force: code-quality (witnessed by the Task 3 intermediate review r1, 2026-11-19, run known-red-gates-consumed-baseline, commit ef8ce891a; log `docs/tmp/execute-plan/known-red-gates-consumed-baseline/review-task3-r1.log.md` in the run worktree, mirrored at the reviews home at Phase 3).

A machinery registry entry note's incident-field citation of a backlog row's living path has no named re-point owner at that row's completion fold, and `machinery_inventory.py --check` does not validate note-internal citations. The cited `duty:carrier-liveness-zero-turn` precedent's own note citation already dangles today, so the new row conforms to its precedent. Fix is repo-wide registry hygiene: a re-point duty for note-internal row citations at completion folds plus optional `--check` validation, priced against the machinery admission protocol's growth rules.

Cluster: machinery-registry-hygiene
