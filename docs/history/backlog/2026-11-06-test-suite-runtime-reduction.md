# Backlog: reduce repository test-suite runtime while preserving coverage

Status: covered-pending-execution (docs/history/plans/2026-11-06-test-suite-runtime-reduction.md)
Workflow: backlog
Priority: high
Origin class: operator request (2026-11-06)
Class: fix-class
Driving force: efficiency
Cluster: docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md (related suite-runtime family; that item sets which validation runs and when, this item reduces the runtime of the selected test suite itself)

## Problem

The repository's script test suite has expensive cases that make validation runs take a long time. In the 2026-11-06 complete 83-suite run, `scripts/test_done_run_wrapper.py` took 3,142.6 seconds (52m23s) for 224 tests and 2 subtests; `scripts/test_land_squash.py` took 401.1 seconds (6m41s) for 179 tests. A refreshed run after `main` advanced was stopped at the operator's request during the wrapper suite after 1,256 seconds and 123 passing tests; that interruption is not a test failure.

The existing `execute-plan-project-test-policy-scope` item covers whether and when project-wide validation is required. It does not profile or optimize the test suite itself. Keep those causes separate: changing suite policy alone does not reduce the runtime when the full suite is required, while optimizing the suite does not decide which projects or plan boundaries should run it.

## Evidence

- `docs/tmp/execute-plan/certification-gates-full-violation-reporting/phase2-self-heal-rerun/suite-index.md` records the per-suite timings for the 83-suite run, including the wrapper and land-squash results above. Its SHA-256 at capture was `3ce9383f38a2f61074f5fd7ed35a8786ab71e24055b2492b59b984d7a699e883`.
- After `main` advanced, the repository inventory contained 84 `scripts/test_*.py` suites. The refreshed suite run was interrupted by the operator during suite 24; see the session's `phase2-refreshed-rerun/suite-index.md` for the partial timing and result. No failure is inferred from that interruption.
- The standard command per script suite is `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_<name>.py -q` (repository test guidance).

## Work scope

Measure the complete test suite and identify the sources of wall-clock cost, including repeated process startup, fixture setup, filesystem and Git operations, serial execution, and tests that no longer protect a unique behavior. Compare, without presupposing the result:

- Remove or consolidate tests only when their unique regression signal is redundant or obsolete and the retained suite still protects the required behavior.
- Refactor slow tests and shared fixtures to reduce repeated setup and subprocess work while keeping each test's assertions meaningful and isolated.
- Run independent tests in parallel where resource contention, shared state, ordering, and flake risk can be bounded and measured.
- Port measured hotspots to Go or Rust when profiling shows a material runtime benefit and parity, maintainability, and ongoing ownership costs are acceptable.
- Consider other evidence-backed options, such as test selection for changed scope, caching, or a faster harness; do not treat a narrower validation policy as a substitute for optimizing the full suite where that suite remains required.

## Acceptance criteria

- Record a reproducible baseline for total wall time and per-suite/per-test contributors on a stated environment, including the largest slowdowns and their resource profile.
- Evaluate all work-scope options against that baseline and document their runtime impact, coverage impact, flake risk, and maintenance cost; the final decision may reject an option when evidence shows it is not worthwhile.
- Reduce full-suite wall time by at least 50% from the reproducible baseline, or return with a measured best result and explicit evidence explaining why the remaining reduction is infeasible without unacceptable loss of coverage or reliability.
- Preserve the unique regression signals for retained behavior. Any removed or merged test has an explicit coverage disposition; any parallelized path has repeat-run evidence for determinism and isolation; any language port has behavioral parity evidence and a measured speedup.
- Keep test selection and required validation policy aligned with `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md`; do not introduce a new blocking gate or validator as part of the optimization without a separate witnessed incident and machinery-admission case.
