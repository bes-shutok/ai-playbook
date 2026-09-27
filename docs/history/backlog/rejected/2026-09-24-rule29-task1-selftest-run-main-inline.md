# Backlog: rule29 Task 1 selftest re-implements _selftest_run_main capture inline

- Status: rejected (2026-09-27; item itself proposes wontfix (interface-forced capture); style-only)
- Date: 2026-09-24
- Driving force: code-quality
- Origin: intermediate review of Task 1 (execute-plan run, worktree ai-playbook-exec-rule29, 2026-09-24); Low, non-blocking. Remedy reworded per Phase 3 design-simplicity lens (2026-09-24).

The new `_selftest_pre_round` family's local `run_main` re-implements `_selftest_run_main`'s four-line capture body (StringIO + redirect + main(argv)) inline instead of calling the shared helper. The inline capture is actually forced for the mutual_exclusion arm: `parser.error` writes into `_selftest_run_main`'s private StringIOs before `SystemExit` propagates, so delegating would lose the usage stderr the arm asserts on. Remedy: on the next natural touch, either drop this item as wontfix (the inline capture is interface-forced) or pin the local wrapper's behavioral equivalence to `_selftest_run_main` with a parity assertion instead of switching the call.
