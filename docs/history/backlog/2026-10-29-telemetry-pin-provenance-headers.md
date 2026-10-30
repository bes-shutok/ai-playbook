# Backlog: telemetry pin provenance headers over-claim capture base

Driving force: docs (primary), maintainability (secondary)
Origin: execute-plan phase2-baseline-repair Task 1 intermediate review (off-plan candidate, 2026-10-29)

Concern: module-level and Task 3 closeout pin provenance headers in `scripts/test_invocation_telemetry.py` state literals were captured at historical bases (c2cfc02a9, d88657273), but the 2026-10-29 re-baseline re-captured several literals at the current CLI; only scattered inline comments disclose the re-capture, so a provenance audit from headers alone misreads original vs re-captured pins.

Direction: carry re-baseline status in the pin provenance headers so provenance is derivable from the headers a pin auditor reads first.
