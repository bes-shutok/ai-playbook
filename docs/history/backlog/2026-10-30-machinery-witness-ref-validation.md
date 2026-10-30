# Backlog: machinery inventory witness-ref validation is non-discriminating
Status: covered (docs/history/plans/2026-10-30-machinery-witness-ref-validation.md)

Driving force: code-quality (primary), coverage (secondary: a guard inventory claiming coverage it does not have masks drift - the defect class this family tracks)
Origin class: fence-class (extend an existing validator, not new machinery)
Origin: execute-plan phase2-baseline-repair Task 3 intermediate review (off-plan candidate, 2026-10-30)

Concern: `check_failures` in `scripts/machinery_inventory.py` only proves a `red-test` witness ref resolves to any tracked path; nothing verifies the ref is a test file or that it exercises the row's script. Mutation witness: pointing `script:base_reflog_audit.py`'s witness at `README.md` passes `--check` green. A factually false witness already exists at HEAD: `script:hooks_probe.py` cites `scripts/test_hooks_probe.py`, which never references `hooks_probe`.

Direction: extend the witness check so a `red-test` ref must be a `test_` path referencing the row's script stem; sweep existing rows for false witnesses while landing it.
