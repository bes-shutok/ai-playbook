# Producer telemetry test order-flake (cross-file)

Driving force: code-quality

`scripts/test_produce_exec_review_record.py::ProduceExecReviewRecordTest::test_validator_telemetry_stays_under_the_temp_metrics_home` fails (`metrics_log.is_file()` False) when the suite runs combined after `scripts/test_step31_record_validation_gate.py`, passes standalone and in isolation. Reproduces identically at main@46fe276b5 without the seam changes (witness: 2026-11-07 exec run for docs/history/plans/2026-11-07-producer-code-family-record-arm.md, Phase 2 probe), so it is not caused by that plan. Likely cross-file env/state pollution (temp metrics home or cwd interference). Fix: isolate the env dependence or fix the pollution source.
