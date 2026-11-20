# Plan: Reduce test-suite runtime without losing regression coverage

Backlog origin: docs/history/backlog/2026-11-06-test-suite-runtime-reduction.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-test-suite-runtime-reduction[-p<identity-token>]-r*.md (highest round for this source-plan path is authoritative).
Executed: yes (3896d7f97db714007bef58276dcdce753d997a0c)
Authoring claim: 2026-11-06-test-suite-runtime-reduction.md (session 01a1b0ab-498e-7751-b65e-03a067c4a9bf)

Language guidance: [Python guidelines](../../../projects/.ai-playbook/python_guidelines.md).

## Terms

- Full suite: every script test suite discovered from the execution baseline's `scripts/test_*.py` inventory, with later additions and deliberate consolidations accounted for.
- Baseline: the unmodified execution tree, environment, test inventory, outcomes and measured elapsed time used for comparison.
- Wall time: elapsed time from starting the complete test command sequence until its final process exits, including setup and waiting.
- Regression signal: an assertion that distinguishes required behavior from a concrete incorrect outcome.
- Harness: the existing Python test setup and invocation helpers, including temporary repositories and subprocess management.
- Fixture: the isolated input files, environment and repository state prepared for a test.
- Parallel execution: running independent suites or cases concurrently with a bounded number of workers.
- `FixtureMixin`: the shared setup and invocation owner in the wrapper test module.
- `LandSquashHelperTest`: the base landing-helper test class.
- Benchmark reports: the baseline/options report created by Task 1 and the final comparison report created by Task 3, linked rather than repeatedly rewriting one new file.

## Why

The recorded complete run spent about 52 minutes in one wrapper suite and about seven minutes in the landing suite. Those measurements identify expensive suites but do not explain their internal costs. Reduce that repeated validation cost while keeping the behavior checks useful.

## Gist & Examples

TLDR: Profile and optimize the existing test harness, improving efficiency without losing unique regression coverage.

**Before (today):** An operator runs the complete script-test inventory to measure repository health. The recorded 83-suite run spent 3,142.6 seconds in the wrapper suite and 401.1 seconds in the landing suite. The sum of its suite timings is 5,386.1 seconds, which is not an independently measured end-to-end wall time; the current inventory must be measured afresh.

**After (this plan):** The same complete-suite benchmark has an explicit environment, source revision, inventory and outcome record. Profiling identifies where the existing harness spends time, and changes remove measured repeated work or safely overlap independent work. The comparison shows the complete-suite speedup and accounts for every changed regression signal rather than claiming success from fewer selected tests.

**Edge cases:** A test that deliberately exercises lock contention still exercises real contention. Shared mutable environment or repository state remains isolated. A failed, skipped, empty-collection or interrupted run cannot count as a successful faster run. Inventory drift is accounted for before comparing results; unexplained drift makes the comparison inconclusive.

## Outcome

Complete repository test runs take less time while retaining the checks that protect required behavior.

- Profiling distinguishes process startup, setup, filesystem and Git work, test bodies, waiting and contention.
- Existing tests and fixtures perform less repeated work without hiding defects or sharing mutable state accidentally.
- A reproducible comparison reports at least 50% less full-suite wall time, or the measured best result and evidence explaining the coverage or reliability limit.

Gate delta: none; no added refusal classes, hard gates, fences, protocol layers, schema fields, dispatch pauses or blocking review duties. Existing workflow validators and production safeguards are unchanged.

## Assumptions

- Assume efficiency is the primary force; basis: origin metadata and confirmed requirements.
- Assume comparisons use the complete discovered inventory and comparable environments with explicit failures, skips and inventory accounting; basis: origin acceptance and the historical 83/84-suite drift.
- Assume optimize the measured dominant cost first without assuming its cause; basis: suite timings do not attribute internal operations.
- Assume removals or merges need a coverage disposition and parallel paths need repeated isolation evidence; basis: origin acceptance and user-confirmed invariants.
- Assume all origin-listed options are evaluated, but implementation stays in the existing harness; basis: the confirmed scope choice. Profiling-only was the simpler alternative and was declined because this plan must deliver improvements.
- Assume ordinary validation stays focused; basis: the user authorized complete-suite runs solely for baseline and final comparison benchmarks, resolving the adjacent policy conflict for this plan only.
- Assume the origin is fix-class; basis: it removes expensive repeated work without adding blocking machinery.
- Scope ledger: authoring base `8cd877c40ba0115d66e4b0a10146a6cbc56e8876`; no pre-existing tracked or untracked dirt. Preserve ignored facts, review records and scratch under the captured closeout baseline. Task 2 owns harness setup and test changes; unrelated production scripts, skill contracts and test-selection policy are frozen. No suite file is deleted by default; remove or merge a case only with an explicit retained-signal mapping. No non-obvious branch-only changes require removal.

Decision points requiring a grill: user authorized bounded full-suite baseline/final benchmarks on 2026-11-06, affecting Tasks 1 and 3 and Validation Commands; user selected profiling plus existing-harness optimization and separate future port/runner work on 2026-11-06, affecting Task 2 and Review Scope; user confirmed the consolidated requirements on 2026-11-06.

## Standing constraints

- Preserve production workflow behavior, safety checks and ordinary project test-selection policy; optimizing tests never weakens the system under test.
- Use only baseline and final comparison runs for complete-suite benchmarks. Intermediate experiments and ordinary validation use the relevant focused tests. No extra full-suite run is added at task or review boundaries.
- Derive test and helper scope from the execution tree. Keep benchmark inputs and outcomes linked to exact revisions, commands, environment and inventory; collect failures and skips, never silently omit them.
- Retain real end-to-end coverage where the asserted behavior crosses process, Git, filesystem or lock boundaries. Reuse only proven immutable inputs; each case owns its mutable state and restores ambient environment changes.
- Evaluate removal/consolidation, fixture refactoring, bounded parallelism, startup reuse, caching, changed-scope selection and Go/Rust ports. Selection alone is no full-suite optimization; language ports and a replacement runner are evaluated follow-ups, not implementation in this plan.

## Evaluation Criteria

**Quality dimensions:**
- Performance: compare complete-suite wall time on the same stated environment and normalized inventory; report per-suite/per-test contributors and resource use with measurement overhead identified.
- Coverage: preserve each unique regression signal; every removed or merged case names its behavior, retained witness and why duplication or obsolescence is established.
- Reliability: preserve failure reporting, clean fixture teardown and isolation. Any selected parallel path passes at least three focused repeated runs with identical outcomes and no cross-case state leakage.
- Maintainability: every selected or rejected option records runtime evidence or uncertainty, coverage impact, flake risk, portability and maintenance cost. Unmeasured options are not described as proven ineffective.

**Done when:**
- The linked benchmark reports contain the reproducible baseline, dominant-cost profile, all option dispositions, implemented changes and final comparable result.
- Modified suites and causally affected regressions pass, and the final complete benchmark has no new failures, skips or unexplained lost signals relative to the baseline.
- Full-suite wall time falls by at least 50%, or the report states the measured best improvement and concrete evidence explaining why further in-scope reduction would unacceptably harm coverage or reliability. A missing experiment or mere lack of time is not that evidence. For this execution, completion of the Task 3 operator-accepted interim-disposition criteria permits plan closure.

**Ship when:**
- None: the repository work and benchmark evidence establish local completion; no deployment or external-owner condition applies.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope when valid.

**Production code:** none; production workflow changes are outside this plan.

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 2)
- `scripts/test_land_squash.py` (Task 2)

**Documentation:**
- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction-baseline.md` (Task 1) *(new)*
- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction.md` (Task 3) *(new)*
- `docs/history/backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md` (Task 3) *(new)*
- `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md` (Task 3)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 3)

**Plan-related extension:** implementation and review may change unlisted test helpers or test modules when evidence ties the change directly to measured runtime or a regression introduced by this plan. Execution records those expanded paths before work. Findings that complete a task, preserve changed wiring or close required documentation are in scope; weak or speculative links are rejected with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; ordinary suite-selection policy belongs to the adjacent policy backlog item.
- `scripts/done_run.sh` and `scripts/land_squash.sh`; production workflow semantics and guard changes are not test optimization.
- Go/Rust ports and replacement-runner implementation; evaluate and report their evidence requirements only.

## Validation Commands

Run from the repository root. Task 1 records the actual complete-suite command sequence and environment before optimization; Task 3 repeats the comparable complete inventory once after optimization. Use the repository-standard pytest collector, never unittest discovery for plain-function suites. These two measured runs prove final suite behavior; the commands below check discovery and text hygiene without inserting additional whole-suite validation at authoring or intermediate boundaries.

Authoring preflight on 2026-11-06: the block passed, collecting 429 tests in 0.15 seconds; hygiene and changed-line scans passed. The baseline and final report each have one creating task; the final report cites the earlier baseline as input. Shell syntax and acceptance byte caps passed; no literal-insertion or negative-grep simulation applies. Collection is not regression execution. The changed-line scan covers insertions in existing Python files; the new report is scanned whole when created. This validation preamble owns command purpose; measured execution results live in the benchmark report, not in plan review-state prose.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py scripts/test_land_squash.py --collect-only -q || exit 1
bash scripts/check-no-em-dash.sh added-lines -- scripts/test_done_run_wrapper.py scripts/test_land_squash.py || exit 1
PUBLIC_HYGIENE_REPO_ROOT="$REPO" bash scripts/scan-public-hygiene.sh --files scripts/test_done_run_wrapper.py scripts/test_land_squash.py || exit 1
bash scripts/check-no-em-dash.sh touched || exit 1
PUBLIC_HYGIENE_REPO_ROOT="$REPO" bash scripts/scan-public-hygiene.sh || exit 1
```

### Task 1: Establish the reproducible baseline and compare options

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction-baseline.md` *(new)*

- [x] Given the unmodified execution tree, expects the complete discovered suite benchmark to record source revision, command sequence, environment, inventory, end-to-end wall time, suite/test contributors, resource use, failures and skips. [class: REPOSITORY_TEST]
- [x] Given expensive suites, expects attributed setup, process-start, Git/filesystem, test-body, waiting and contention costs; separate instrumented profiling overhead from the comparable baseline. [class: REPOSITORY_TEST]
- [x] Write the baseline and option comparison in `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction-baseline.md`: given each listed approach, expects measured evidence or an explicit unmeasured disposition, coverage impact, flake risk, portability and maintenance cost. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the profile, expects selected existing-harness changes to target demonstrated costs; reject selection-only speedups and document why ports or a replacement runner remain follow-up work. [class: IMPLEMENTATION_REQUIRED]
- [x] Given baseline failures, skips or interruption, expects accurate separate outcomes and no false passing baseline; retain evidence and continue only with comparisons whose uncertainty is explicitly reported. [class: REPOSITORY_TEST]
- [x] Commit: `tests: record full-suite runtime baseline and optimization choices` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Remove measured costs from the existing harness

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_run_wrapper.py`
- `scripts/test_land_squash.py`

Primary class anchors:
- `FixtureMixin` in `scripts/test_done_run_wrapper.py`, shared wrapper setup and invocation.
- `LandSquashHelperTest` in `scripts/test_land_squash.py`, landing test setup and behavior checks.

- [x] Run → expect GREEN characterization before refactoring: given each selected hotspot and its protected behavior, expects the existing assertions to distinguish the correct result from the relevant incorrect outcome. [class: REPOSITORY_TEST]
- [x] Given a measured repeated setup or subprocess cost, expects the optimized existing harness to do less work while retaining real boundary coverage, isolated mutable state and equivalent failure assertions. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a removed or merged case, expects a recorded mapping to a retained discriminating witness, or evidence the old behavior is obsolete; elapsed time alone never licenses removal. [class: IMPLEMENTATION_REQUIRED]
- [x] Given selected caching or setup reuse, expects changed inputs to invalidate reused data and one case's mutation not to alter another case's result; keep the original isolation path if reuse cannot meet this witness. [class: REPOSITORY_TEST]
- [x] Given selected parallel paths, expects bounded workers and at least three focused repeated runs with identical outcomes, isolated state and complete failure propagation; retain serial behavior when the measured reliability or contention cost outweighs savings. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN after refactoring: given the modified suites and causally affected tests, expects retained behavior assertions and cleanup checks to pass; measure focused speedups without another complete-suite run. [class: REPOSITORY_TEST]
- [x] Commit: `tests: reduce measured harness overhead without losing regression signals` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Verify complete-suite improvement and publish the result

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction.md` *(new)*
- `docs/history/backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md` (Task 3) *(new)*
- `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md` (Task 3)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 3)

- [x] Given the optimized tree, expects one final complete-suite benchmark using comparable baseline settings and inventory accounting; retain outcomes and resource measurements, separate setup effects and instrumentation overhead. [class: REPOSITORY_TEST]
- [x] Given the baseline and final measurements, expects the benchmark report to state the wall-time reduction and uncertainty, changed coverage dispositions, failures/skips, repeat-run evidence for parallel paths and final option decisions. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the final measurement, expects the report to state whether reduction reached 50% and to account for behavior coverage in the measured result. [class: REPOSITORY_TEST]
- [x] Given less than 50% reduction without explicit one-run operator acceptance, expects measured best results and concrete coverage or reliability limits; [class: IMPLEMENTATION_REQUIRED]
- [x] Given one-run operator acceptance, expects a receipt quoting and binding the confirmation to this plan's final result and run; report and archive keep both original conditions unmet and link the validated follow-up and investigation with why executable now. [class: REPOSITORY_TEST]
- [x] Given the operator-directed interim disposition, expects the remaining process-parallelism, Go/Rust runner, and fixture/startup options to be preserved in an open follow-up backlog item with detailed measured versus unmeasured findings and a validated investigation entry. [class: IMPLEMENTATION_REQUIRED]
- [x] Given new failures, added skips, unexplained inventory loss or incompatible environments, expects an inconclusive comparison with named evidence, never a successful speedup claim or premature completion. [class: REPOSITORY_TEST]
- [x] Run the Validation Commands and any focused checks selected for expanded task scope; given changed helper/doc surfaces, expects no stale references, leaked fixture state or new hygiene violations. [class: REPOSITORY_TEST]
- [x] Commit: `tests: document verified full-suite runtime improvement` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- The origin `docs/history/backlog/2026-11-06-test-suite-runtime-reduction.md` was covered by this execution. Its status was flipped to `covered` against the pre-squash branch tip and the origin is deleted in this archive commit. The distinct test-policy item remains open.
- The final benchmark measured a 44.102% reduction, below the 50% target. The alternative coverage or reliability limit was not established. The operator said, “Accept 44.10% for now,” for this execution only. Both original success conditions remain unmet.
- Follow-up work remains open at `docs/history/backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md`, with investigation recorded in `docs/history/backlog/PLAN-PROMPTS.md`. It is actionable now because the completed profiles identify the remaining measurement work, with process parallelism first and Go/Rust prototypes conditional on profiling evidence.
