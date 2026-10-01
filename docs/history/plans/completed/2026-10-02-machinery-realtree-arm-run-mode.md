# Plan: Machinery enforcing suite — real-tree arm run mode

- **Date:** 2026-10-02
- **Workflow:** plans
- **Origin class:** self-serving
- **Class:** fix-class
- **Priority:** low

Backlog origin: docs/history/backlog/2026-10-02-machinery-realtree-arm-unreachable.md

## Review Scope

Paths this plan touches:

- `scripts/test_machinery_inventory.py`

One file only. The registry (`scripts/machinery_registry.json`), the checker (`scripts/machinery_inventory.py`), and every consumer pinning the suite's 14-test count are unchanged surfaces read as witnesses. The suite's fixture arm (the 14 tests) keeps its current default-run behavior byte-for-byte. One consumer mode must stay genuinely unchanged: unittest DISCOVERY invocations (for example the machinery-elimination-pass plan's `python3 -m unittest discover -s scripts -p "test_machinery_inventory.py"`) import the whole module and already discover `RealTreeCheck` today — red under current drift before this plan lands. The Task 1 (a) hook is pattern-aware precisely so discovery keeps that behavior (fixture arm plus `RealTreeCheck`, red under today's drift, green once the upkeep execution lands); a naive fixture-only hook would silently flip discovery red-to-green here and strip the arm from discovery coverage.

## Terminology and core concepts

- **The dead arm**: `class RealTreeCheck` sits AFTER the `unittest.main()` call in `scripts/test_machinery_inventory.py` (main at line 219, class at line 222), so the documented invocation `python3 scripts/test_machinery_inventory.py` defines only the fixture tests, runs them, and exits before the class definition is reached — the arm the class docstring calls "the Enforcing arm of the standing regrowth guard" never executes in that mode.
- **The two run modes this plan establishes**: the default invocation stays fixture-only (14 tests, unchanged); `python3 scripts/test_machinery_inventory.py --real-tree` runs ONLY the RealTreeCheck arm against the live tracked tree.
- **The live drift**: `python3 scripts/machinery_inventory.py --check` currently reports 15 failures (8 unregistered scripts, 7 dead witnesses) — the registration drift the machinery-inventory-upkeep plan owns and its execution has not yet repaired. Any default-run inclusion of the real-tree arm would therefore turn the suite red on today's main, redden every plan validation block that runs the suite, and collide with the peer execution mid-flight.

### Task 1: make the real-tree arm reachable and deliberately scoped

Files:
- `scripts/test_machinery_inventory.py`

- [ ] Move `class RealTreeCheck` above the `if __name__ == "__main__":` block so the class is defined before any run mode dispatches [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the run-mode dispatch with both branches explicit, because neither is free after the class move: unittest.main() with default settings loads EVERY TestCase subclass in module scope, so (a) add a module-level `load_tests(loader, tests, pattern)` hook (re-derive the fixture class name from the file) that is pattern-aware: when `pattern` is set (a unittest DISCOVERY invocation) it returns the fixture arm plus `RealTreeCheck`, preserving discovery's today-semantics exactly, and when unset (the documented default invocation) it returns only the fixture arm, pinning that branch to exactly today's 14 tests, and (b) when the flag is present, strip it from argv AND pass `RealTreeCheck` as the sole selected test name (`unittest.main(argv=[sys.argv[0], "RealTreeCheck"])`) — a strip alone would run the whole module suite. The flag-absent invocation's observable behavior stays byte-identical to today's only through the (a) pin [class: IMPLEMENTATION_REQUIRED]
- [ ] Correct the `RealTreeCheck` docstring: it keeps the enforcing-arm claim but names its invocation (`--real-tree`) and states the default run is fixture-only by deliberate contract, with default-run inclusion deferred — the deferral decision is recorded BY THIS PLAN, here and in the ledger of its own landing receipt, because the machinery-inventory-upkeep plan's landed bytes declare the suite read-only ("no test edits planned") and carry no such record; this plan is the sole owner of the file and of the decision [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect OK, 14 tests: `python3 scripts/test_machinery_inventory.py` (the default run's count and set are unchanged, so the machinery-inventory-upkeep plan's "OK (14 tests)" pin stays valid) [class: REPOSITORY_TEST]
- [ ] Run → in a repository checkout, expect the arm executes and exits nonzero on today's tree, naming the drift rows: `python3 scripts/test_machinery_inventory.py --real-tree` (nonzero is the EXPECTED state while the upkeep execution has not landed; outside a repository checkout the arm skips with exit 0 — the third witness state, legitimate, record which one you saw; this checkbox documents the red, it does not fail the plan) [class: REPOSITORY_TEST]

### Task 2: validation

Files: none (verification only)

- [ ] Run → expect exit 0: the hygiene scan [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0 per round record: `python3 scripts/validate_review_staging.py --hard <round-md-path> --source-plan <round-bytes-file>` for each authored round record [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0: `python3 scripts/plan_readiness.py` on the final bytes [class: REPOSITORY_TEST]

## Assumptions

- The change is dispatch-and-docstring only: no registry edits, no checker changes, no new files, no consumer updates — the default run's 14-test count survives untouched THROUGH the `load_tests` pin, not for free: without it, the class move alone would put `RealTreeCheck` in default discovery and the default run would be 15 tests failing on today's drift. The pin's pattern-aware arm is equally load-bearing: a fixture-only hook would silently change discovery semantics (red-to-green flip under today's drift), which is a consumer-visible behavior change this plan forbids.
- The real-tree arm's expected-red state on today's main is a documented intermediate, not a defect of this plan: the drift is the machinery-inventory-upkeep plan's execution scope, and once that lands the same invocation flips green with no further change here.
- The `--real-tree` arm has three legitimate witness states, all recordable without failing the plan: nonzero with drift rows (today's tree, drift unexecuted), zero green (after the upkeep execution lands), and zero SKIPPED (invoked outside a repository checkout — the arm's own skipTest path). The executor records which one it witnessed.

Decision points requiring a grill: whether the real-tree arm joins the default run now or stays split behind the flag (resolved: split — the live 15-failure drift is unexecuted peer scope, so default inclusion would redden every consumer's validation block mid-flight; the split makes the arm reachable today and leaves default inclusion as a deliberate follow-up owned by the upkeep execution); whether the split is an in-module flag or a separate entry point (resolved: in-module dispatch before `unittest.main()` with argv stripping — one file, unittest's own CLI preserved, no new surface for the machinery registry to track).
