# Plan: Bring the Required Test Suite Below Five Minutes

Backlog origin: docs/history/backlog/2026-11-08-test-suite-runtime-residual-optimization-path.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-test-suite-runtime-residual-optimization-path-p2afb000f-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list).
Executed: yes (492dc826ee5b6cf85dfdf04c4256050cad7cdc0d)
Authoring claim: 2026-11-08-test-suite-runtime-residual-optimization-path.md (session 01a1ba1b-31ac-7473-821f-835dde6e170e)

## Terms

- Required suite: every direct scripts/test_*.py suite under repository test guidance, re-derived at execution; the plan-authoring snapshot had 89 such files.
- Mixed runner policy: class-only suites use unittest discovery; function-only and mixed suites use pytest, per repository test guidance.
- Test script: one source suite file in the required inventory, with one aggregate outcome and a 60-second deadline covering discovery, every bounded shard, descendant cleanup/reaping, capture and in-memory source-result finalization.
- Suite shard: one complete unittest class, an isolated unittest method ID only when per-test setup/cleanup and filesystem, environment and child effects prove independence with no class fixtures or ordering dependency, or a pytest node ID from one source suite; assign every discovered ID once. Split classes only into independent classes preserving fixture, cleanup and ordering semantics; if none fits 60s, keep the residual open.
- Per-script limit: 60 seconds starting when the scheduler admits the source suite by acquiring its source slot and scheduling gate; it covers discovery, shard queueing and execution, descendant cleanup/reaping, capture and in-memory source-result finalization. Final aggregate JSON serialization and report-file writing count against the 300-second full-suite limit. Queue time before source admission also counts only against the 300-second suite limit. A Heavy trial command has a separate 60-second deadline from submission through queue, execution, cleanup and capture.
- Full-suite limit: a cumulative 300-second deadline from mise command launch through all queueing, suite execution, teardown and complete result/report writing; startup and capture count.
- Runner deadline: the cumulative deadline enforced inside the suite runner, set earlier than 300 seconds by a measured safety margin for mise startup, worst-case cleanup and report writing; the outer five-minute mise timeout is only the final guard.
- Retained signal: a distinct assertion proving a behavior or refusal; runtime work may merge tests only when every signal has a mapped surviving witness.
- Matched round: one run of each candidate on the same cases, inputs, environment and resource limits; candidate order is fixed before timing and rotated across three rounds.
- Run range: maximum minus minimum wall time across three matched rounds for one candidate.
- Candidate gain: baseline median wall time minus candidate median; it qualifies only when greater than the larger baseline/candidate run range.
- Trial disposition: retain only with complete parity, support and qualifying gain or operational evidence; reject only on complete evidence that a requirement fails; incomplete capped evidence or a timed profile or candidate round overlapping an unassigned long-lived test controller is inconclusive, preserves Python tests and routes any viable rerun through the no-candidate disposition.

- Scheduling class: per-run suite label based on mutable paths, locks, environment effects and process-tree effects; proven-independent suites may overlap, known conflicts are grouped or isolated, and unknown suites serialize.
- Node pilot: a bounded parity trial using Node's built-in test runner for selected behavior currently tested by Python.
- Pilot substitution: a retained candidate case replaces its exact mapped Python test ID in full-suite scheduling and is attributed to that source suite exactly once.
- Dev Quality Gates: an external curated tool catalogue with a recommendation and stated limits for each job; a research input, not a quality gate.
- mise: a project tool, version, environment and task manager; it runs tasks but does not check code or enforce quality standards.
- Trial process context: bounded process-tree PID/PPID snapshots attribute candidate commands and identify unrelated long-lived test controllers; an unassigned controller overlapping a timed profile or candidate round makes it inconclusive.
- Heavy trial: a bounded two-worktree experiment where Heavy holds a machine-wide semaphore slot only while its direct child (the Task 4 runner) lives; that runner cleans up descendant process groups captured from the live worker snapshot, and Heavy remains trial-only.
- Heavy control result: baseline peak active commands exceed Heavy slots; Heavy stays within its slots in all three pairs with the same pool and no bypass, its cleanup canary passes, and median aggregate time is no slower than baseline median plus the larger run range.
- Machinery admission protocol: the existing AGENTS.md rule that a lane-blocking addition needs a cited integrity incident, expected catch frequency, false-positive cost, sunset or review date, and a paying removal or simplification. New machinery starts warning-only or read-only; promotion requires a true catch and a pre-registered registry-removal row naming sunset and promotion criteria, and retires or demotes an existing blocker in the same change.
- Quality-gate issue: an evidenced slow, failing, missing or ineffective check, named with its owning gate and a reproducible example.

## Why

The 2026-11-07 report records a 1,748.107-second run of 88 suites, with seven above 60 seconds and `test_done_run_wrapper.py` at 692.935 seconds. The follow-up stopped without a qualifying language comparison and left the measured runtime work without a durable execution plan. This plan profiles the slow paths and targets the full required suite within 300 seconds, with each script capped at 60 seconds and all required test signals preserved.

## Gist & Examples

TLDR: Refactor and bound the required test suite, improving efficiency while preserving all regression signals.

**Before (at plan authoring):** The recorded 88-suite run took 1,748.107 seconds, with seven scripts above one minute. The plan-authoring snapshot contained 89 Python suite files, including test_maintenance_d17_continuation_scenarios.py. Long Git, shell and subprocess waits had not been fully attributed, and the prior execution did not test a non-Python implementation on the two historically longest paths.

**After (this plan):** The same complete, freshly inventoried suite runs under a five-minute total deadline, with each test script limited to about one minute. The longest Python test helpers use fewer repeated tool and process calls where the behavior remains covered. A bounded Node pilot compares equivalent cases on the two longest paths; if profiling still points to Python runtime or CPU cost, the plan considers one additional suitable language or tool. Only faster supported candidates replace mapped Python cases. A bounded runner overlaps only proven-independent suites and within-suite shards, with one aggregate timer and report per source script; it reports every pass, failure, error, skip, timeout, collected case and executed case. A two-worktree Heavy pilot proves shared pool identity, measures cross-session contention and queue delay, then records whether a separately admitted integration merits follow-up. A repository mise task provides a pinned, documented entrypoint around that runner; its wrapper time is measured and no speedup is credited for work done inside shell or Git.

**Example:** test_done_run_wrapper.py currently takes about 11.5 minutes. Its test fixtures are profiled with bounded samples, then refactored around the measured Git and subprocess costs. Each source script has one aggregate timer across its shards; a stuck shard is terminated and reported as a failure, and the complete result report is written by 300 seconds.

**Edge cases:** A timeout under contention is recorded as a failure, not a pass or skip. Suites that share host resources, lock paths or mutable environment state remain isolated or serialized. A port that is slower or not supported by the project's test environment is rejected with its evidence, while the Python coverage remains. A nonempty discovered suite reporting zero collected or executed cases is a runner failure even when its child exits successfully.

## Outcome

The full required test suite remains the performance target: every required script within 60 seconds and the complete invocation within 300 seconds, without losing any required test behavior. The user authorized a partial-delivery closeout if that target remains unmet, so implemented runner and tooling improvements can land while the runtime target stays explicitly open in the residual backlog.

- Every script in the re-derived required inventory finishes within 60 seconds, and the complete suite finishes within 300 seconds with cleanup and reporting included.
- Refactored helpers, bounded suite parallelism and evidence-backed within-suite sharding preserve every required behavior signal; the report accounts for every source suite, shard, outcome and per-script time.
- Node and Heavy receive bounded, matched trials with evidence-based dispositions; Heavy runs must overlap across worktrees and prove slot use, remains trial-only, and any integration proposal receives separate machinery admission review.
- The repository exposes a documented mise entrypoint and Dev Quality Gates lookup guidance; every concrete residual after a missed limit lands as an actionable backlog origin and ready prompt before archive. Partial delivery is permitted only under the recorded user authorization, after implementation, focused validation and review complete, and evidence records each runtime limit independently. Final execution closeout marks this plan executed, disposes its original covered origin through the existing lifecycle, and archives it as partial; the separate runtime-residual origin and ready prompt stay open with the next action. A not-run limit is never reported as a measured failure or a pass.

Gate delta: no CI, hook or agent-lane blocker is added. The plan adds a user-invoked mise task whose local runner reports timeout, missing-count and zero-collection failures, plus nonblocking tool-review guidance in existing instructions and skills. Heavy is trial-only; there is no persistent semaphore or wrapper in the required-suite command. A later blocking integration requires separate machinery admission evidence and a paying removal or simplification.

## Assumptions

- Assume all scripts/test_*.py suites are required until execution re-derives the live inventory; the plan-authoring snapshot counted 89, based on the report's 88-file inventory plus scripts/test_maintenance_d17_continuation_scenarios.py.
- Assume the existing class-only/function-only runner policy remains in force; basis: repository test guidance and the completed follow-up report.
- Assume real process, Git, filesystem and lock boundaries remain covered whenever they are the behavior under test; basis: the previous plan's preserved-signal requirements and the user's full-suite target.
- Assume process-level parallelism is bounded and selected from measured resource use; basis: the previous parallel pilot had unassigned controller contention.
- Assume no test case or assertion is removed for speed unless a retained test proves the same unique signal; basis: the user-confirmed complete-suite scope.
- Assume mise 2026.11.4 is installed from Homebrew on the current notebook and Node 26.13.0 is available; Go and Rust are absent. Recheck execution support. Keep the Python test virtual environment as the interpreter source; pin a candidate runtime only if its pilot remains in scope.
- Assume the previous 5% Python-specific-cost threshold no longer blocks a required alternative-language trial; basis: the user's explicit request to try a non-Python option on the longest scripts.
- Assume the repository has no mise configuration or CI workflow; basis: current root inventory. Add only a mise test task and documentation, with no new CI or hook gate.
- Assume Heavy is a contention-control candidate for simultaneous worktree sessions, not an intrinsic test-speed optimization; basis: its machine-wide semaphore behavior. This plan runs a bounded trial and records any case for a separate follow-up; it adds no persistent wrapper. An integration proposal must satisfy the existing Machinery admission protocol, including a qualifying incident witness, expected catch frequency, false-positive cost, sunset or review date, and a paying removal or simplification.
- Assume Dev Quality Gates is a current source for tool candidates, not a mandatory stack; execution rechecks its recommendation, limits, official tool documentation and existing repository tools before adoption.
- Assume the no-candidate outcome rule in docs/history/plans/2026-11-08-plan-execution-no-candidate-follow-up-disposition.md: retain explicit evidence-based rejections and route concrete viable residual work through an origin plus investigation/plan prompt before archive. Its PLAN-PROMPTS index entry was pruned at authoring. The separate test-suite-runtime-residual-optimization-path entry is this plan's direct performance input. This plan applies the outcome rule to runtime-limit misses. Only Task 6's Dev Quality Gates lookup edits in AGENTS.md, agents/skills/plans/SKILL.md and agents/skills/self-heal/SKILL.md are in scope; other plan/execute policy changes remain with their own backlog origin.

Decision points requiring a grill: user set the whole-suite limit to 300 seconds and each script limit to 60 seconds (2026-11-08; Why, Outcome, Evaluation Criteria, Tasks); user required a non-Python trial, narrower process/tool calls and bounded parallel runs (2026-11-08; Tasks, Review Scope, Validation Commands); user confirmed preservation of the complete suite and its behavior signals (2026-11-08; Tasks, Evaluation Criteria); user directed reuse of `plan-no-candidate-follow-up-disposition` for residual outcomes (2026-11-08; Task 5). User requested repository mise setup and Dev Quality Gates lookups for gate issues or new instruments (2026-11-08; Tasks 5-6); user recommended Heavy for coordinating simultaneous sessions across worktrees and requested its evaluation as a command-run optimization (2026-11-08; Task 5, Evaluation Criteria); user authorized partial-delivery archive while keeping the 60-second miss and 300-second not-run status separate (2026-11-10; Outcome, Done when, Task 5).

## Evaluation Criteria

**Quality dimensions:**

- Correctness: every suite in the live inventory runs under its required runner and retains its distinct assertions, failures, errors and skips; every nonempty suite reports positive collection and execution counts.
- Performance: no source test script or its aggregate shard group exceeds 60 seconds, and the complete mise invocation, including startup, queueing, cleanup and result writing, finishes within 300 seconds.
- Reliability: process cleanup, fixture isolation, lock ownership and failure propagation remain correct under suite and within-suite parallel execution; unknown suites or shard groups serialize, and Heavy baseline and enabled commands overlap, exercise slots, prove no bypass, and record cross-worktree pool identity and queue wait.
- Maintainability: the process-aware runner adds no library dependency; mise remains a task and version manager, not a test checker; the Python test virtual environment remains unchanged; candidate runtimes are pinned only when their trials justify use, and the temporary Heavy setup is removed before landing.
- Observability: the final report records source revision, inventory digest, suite and shard scheduling classes and start/end, runner, worker count, shard identities, collection/execution counts, per-script aggregate elapsed time, outcomes, host/runtime details, process attribution and uncertainty; Heavy reports queue/run times, pool identity, slot use, maximum active commands and host load as context.

**Done when:**

- Either the complete, re-derived required suite passes once within 300 seconds with every individual script within 60 seconds, or the user-authorized partial-delivery path is complete: implementation, focused validation and review pass; each limit has a separate evidence-based status; the residual backlog and ready prompt remain open with the next action; and normal execution closeout records `Executed: yes`, folds/deletes the original covered origin as required, and archives this plan as partial without claiming an unpassed limit.
- For full acceptance, account for every live suite and outcome; hide no missing result, zero-collection false green, new skip or lost signal. For partial archive, state that the full inventory was not run, report measured focused IDs separately and leave omitted full-run outcomes unverified.
- The Node pilot records retain, reject or inconclusive: retain or reject only after three complete matched rounds and parity/resource evidence; a 60-second script or 300-second campaign cap before completion is inconclusive, removes the Node pin, preserves Python tests and routes any viable rerun through the no-candidate disposition.
- The mise task entrypoint preserves the per-suite report, includes wrapper overhead in the 300-second budget, and passes the detached-descendant cleanup canary.
- Three matched two-worktree pairs launch the same commands concurrently in no-Heavy and Heavy conditions, with real overlap, baseline peak active commands above Heavy slots, Heavy peak active commands at or below slots in every pair, and enough submissions to exercise queueing. Baseline commands have a 60-second limit from process launch; Heavy commands have a 60-second limit from submission, including queue; the trial is capped at 300 seconds. Record start/end times, medians, ranges, queue/run times, pool identity, slots, maximum active commands and host load as context. Follow up only when Candidate gain qualifies or the Heavy control result holds. Overrun, non-overlap, bypass or separate pool is inconclusive. Remove temporary setup before landing; Heavy never wraps suite acceptance.
- The repository instructions and plan/recovery skills consult Dev Quality Gates for evidenced gate problems and new instrument proposals, with fit and limits recorded.
- Every candidate outcome is explicit; any concrete viable residual is committed as a backlog origin with a ready investigation/plan prompt before archive, using the existing no-candidate disposition pattern. Recording a residual alone does not satisfy Done when or authorize archive; when a limit is missed, the authorized partial path uses normal execution closeout for this plan's `Executed` field and original origin, while the separate residual origin and prompt remain open. Report each limit independently: a missed 60-second profile gates the 300-second run, which is then not run rather than measured as failed.
- The final feature note records the full per-script table when a full inventory run occurs; for partial archive, it records the prior table, focused-profile IDs/counts and raw samples separately, plus all remaining limits.

**Ship when:** none; this is a local test-harness and test-suite change.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Test harness and test code:**

- scripts/test_done_run_wrapper.py (Task 1)
- scripts/test_worktree_closeout_migrate.py (Task 1)
- scripts/test_release_skill_selftest.py (Task 1)
- scripts/test_done_sweep_gates_lib.py (Task 1)
- scripts/test_corrections_record.py (Task 2)
- scripts/test_execution_claim.py (Task 2)
- scripts/test_land_squash.py (Task 2)
- scripts/test_suite_node_pilot.mjs (Task 3)
- scripts/run_required_test_suite.py (Task 4)
- scripts/test_required_test_suite.py (Task 4)

**Documentation and origin:**

- mise runtime candidate and task configuration: mise.toml, conditional mise.lock, README.md and AGENTS.md (Tasks 3 and 5)
- quality-tool investigation guidance: AGENTS.md, agents/skills/plans/SKILL.md and agents/skills/self-heal/SKILL.md (Task 6)
- docs/history/feature-notes/2026-11-08-test-suite-fast-feedback-refactor.md (Task 5)
- docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv (Task 5)
- docs/history/feature-notes/2026-11-08-test-suite-fast-feedback-runner-report.md (Task 5)
- docs/history/backlog/2026-11-08-test-suite-runtime-residual-optimization-path.md (Task 5)
- docs/history/backlog/ (Task 5); conditional new dated residual origin if either limit is missed
- docs/history/backlog/PLAN-PROMPTS.md (Task 5)

**Plan-related extension:** review or execution may adjust supporting test helpers or fixtures when they directly implement these refactors or preserve a named signal. Production behavior and unrelated plan/execute workflow text are outside this plan; Task 6's Dev Quality Gates lookup edits in AGENTS.md and the named plans and self-heal skills are explicitly in scope.

**Out of scope; reject unless plan-related:**

- Test selection reductions, caching test results, or changing production workflow behavior.
- Installing an unmeasured language runtime, unrelated quality tools, creating CI workflows or Git hooks, or adopting every Dev Quality Gates category. Task 3 may select one additional runtime such as Rust only when profiling identifies material Python runtime/CPU cost. A persistent Heavy pin, semaphore or wrapper is outside this plan; Task 5 uses Heavy only as a temporary trial and the acceptance command runs without it.
- The separate execution-policy changes described by plan-no-candidate-follow-up-disposition; this plan reuses its no-candidate outcome rule only.
- Replacing the Python test virtual environment as part of mise setup; each alternative-language pilot has its own measured parity decision.

## Validation Commands

Run from the repository root. Always run the focused runner-contract command and both text/hygiene scans over every scoped non-Markdown file. Run full mise acceptance only after the exact 145-ID profile passes within 60 seconds. Record a failed exact profile as a 60-second miss and gate the 300-second run as not run; after a passing profile, report the 60-second and full-suite 300-second outcomes independently. Resolve pinned tools before timed acceptance and start the 300-second clock at mise launch.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
unset PYTHONHOME PYTHONPATH || exit 1
export AI_PLAYBOOK_TEST_VENV="$HOME/.agents/venvs/ai-playbook-test/bin"
export PATH="$AI_PLAYBOOK_TEST_VENV:$PATH"
python3 scripts/run_required_test_suite.py --suite scripts/test_required_test_suite.py --workers 1 --per-script-timeout 60 --suite-timeout 60 --json-report docs/tmp/test-suite-fast-feedback-runner-tests.json || exit 1
bash scripts/check-no-em-dash.sh file scripts/test_done_run_wrapper.py scripts/test_worktree_closeout_migrate.py scripts/test_release_skill_selftest.py scripts/test_done_sweep_gates_lib.py scripts/test_corrections_record.py scripts/test_execution_claim.py scripts/test_land_squash.py scripts/run_required_test_suite.py scripts/test_required_test_suite.py scripts/test_authoring_continuation_ownership.py scripts/test_authoring_raced_pick_continuation.py scripts/test_invocation_telemetry.py docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv mise.toml || exit 1
bash scripts/scan-public-hygiene.sh --files scripts/test_done_run_wrapper.py scripts/test_worktree_closeout_migrate.py scripts/test_release_skill_selftest.py scripts/test_done_sweep_gates_lib.py scripts/test_corrections_record.py scripts/test_execution_claim.py scripts/test_land_squash.py scripts/run_required_test_suite.py scripts/test_required_test_suite.py scripts/test_authoring_continuation_ownership.py scripts/test_authoring_raced_pick_continuation.py scripts/test_invocation_telemetry.py docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv mise.toml || exit 1
if [[ -f mise.lock ]]; then
  bash scripts/check-no-em-dash.sh file mise.lock || exit 1
  bash scripts/scan-public-hygiene.sh --files mise.lock || exit 1
fi
```

Only after the exact 145-ID profile passes, resolve and install mise tools and run the full acceptance command once. If the exact profile misses 60 seconds, record the 300-second acceptance as not run; do not report a 300-second failure without running it:

```bash
if [ -f mise.lock ]; then mise install --locked || exit 1; fi
AI_PLAYBOOK_TEST_VENV="$HOME/.agents/venvs/ai-playbook-test/bin" TEST_SUITE_WORKERS=8 PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" PYTHONHOME="/tmp/ai-playbook-invalid-python-home" PYTHONPATH="/tmp/ai-playbook-invalid-python-path" mise run --timeout 5m --report-file docs/tmp/mise-required-test-suite.json test:required
```

### Task 1: Profile and refactor the four longest Python suites

Context surface: the plan's Terms, this task and Standing constraints when present; referenced, never restated.

Files:

- scripts/test_done_run_wrapper.py
- scripts/test_worktree_closeout_migrate.py
- scripts/test_release_skill_selftest.py
- scripts/test_done_sweep_gates_lib.py

Primary class anchors:

- FixtureMixin in scripts/test_done_run_wrapper.py
- WorktreeCloseoutTest in scripts/test_worktree_closeout_migrate.py
- ReleaseSkillSelftest in scripts/test_release_skill_selftest.py
- DoneSweepGatesLibOutcomeTest in scripts/test_done_sweep_gates_lib.py

Evidence: the follow-up report measured these four longest suites at 692.935, 131.799, 124.015 and 108.449 seconds. It names repeated shell/Git/subprocess waits as a major cost and requests child-process attribution for the wrapper path. The previous pilot recorded 1-minute host load from 8.864 to 21.524 and an unclassified long-lived Python process coincident with unrelated suite runs (docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md#L160-L175). The prior overlap motivates balanced candidate order and retaining run ranges; host load is reported as context, not an eligibility gate.

- [x] Given bounded profiles of the four longest suites, expects wall/CPU, Git and process-tree timings plus bounded before/after PID/PPID snapshots attributing commands and identifying unrelated long-lived test controllers. An unassigned controller overlapping a timed profile makes it inconclusive. Host load and Heavy waits are context only. Cap each script at 60s and campaign at 300s. [class: IMPLEMENTATION_REQUIRED]
- [x] Given measured repeated setup or tool calls, expects batching, narrowing, or a supported direct tool/API to reduce measured work without changing behavior; mutable repositories, environments and locks stay isolated. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a suite over 60s, use only Terms-eligible shards. Split classes only into groups that preserve fixture, cleanup and ordering behavior; if no safe split meets 60s, record the residual and use the authorized partial path only when its criteria pass. Run every test ID exactly once. [class: IMPLEMENTATION_REQUIRED]
- [x] Given any removed or consolidated test, expects a one-to-one map for every distinct behavior signal to a surviving discriminating assertion; elapsed time alone never justifies deletion. [class: REPOSITORY_TEST]
- [x] Given date-sensitive fixtures, expects one frozen or injected date for fixture data and the child process, with an assertion they observe the same date. [class: REPOSITORY_TEST]
- [x] Given each changed test path, expects focused validation to use the current class/function runner policy and a 60-second process bound. [class: REPOSITORY_TEST]
- [x] Commit: tests: reduce runtime in the heaviest closeout suites [class: IMPLEMENTATION_REQUIRED]

### Task 2: Refactor the remaining over-minute Python suites

Context surface: the plan's Terms, this task and Standing constraints when present; referenced, never restated.

Files:

- scripts/test_corrections_record.py
- scripts/test_execution_claim.py
- scripts/test_land_squash.py

Primary class anchors:

- RecordSchemaTest in scripts/test_corrections_record.py
- TestExecutionClaim in scripts/test_execution_claim.py
- LandSquashHelperTest in scripts/test_land_squash.py

Evidence: the next three historically slow suites measured 108.243, 93.452 and 88.400 seconds. Current profiles attribute 48.906 seconds to 47 `execution_claim.sh` calls in the first 36 tests, and 43.774 seconds to 110 `land_squash.sh` and `done-lock.sh` calls. Capped serial runs stopped at 48/94 and 44/65 by 55 seconds. No faster compatible shell tool is installed. Corrections-record passed all 92 tests in 49.778 seconds once. Use the existing suite-shard contract to retain the CLI behavior and meet the source deadline with safe within-source parallelism.

- [x] Given bounded profiles of these three suites, expects per-suite and child-process samples sufficient to identify expensive setup, Git work and waits; cap each source at 60s and the profile campaign at 300s. [class: IMPLEMENTATION_REQUIRED]
- [x] Given measured hotspots, expects test-only setup/tool work to decrease without changing production behavior or weakening isolation; preserve the required CLI exit, output and cleanup signals. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the CLI-heavy execution-claim and land-squash classes, expects Terms-eligible complete class shards in the same source files, an exact old-to-new test-ID map, and each ID collected and executed exactly once. Preserve fixture setup/cleanup and ordering; prove filesystem, environment, lock and child-process isolation before overlapping shards. [class: REPOSITORY_TEST]
- [x] Given each selected class shard, expects a complete standard-runner pass within 60s with full failure/error/skip output. Task 4 owns the aggregate 60s deadline and report for each source; a serial watchdog result is never a pass. [class: REPOSITORY_TEST]
- [x] Commit: tests: trim repeated setup in remaining slow suites [class: IMPLEMENTATION_REQUIRED]

### Task 3: Compare alternative-language implementations on the longest test paths

Context surface: the plan's Terms and this task; referenced, never restated.

Files:

- mise.toml *(new)* (candidate runtime pin; Task 5 adds the required-suite task)
- mise.lock *(new)* (when a runtime is pinned)
- scripts/test_suite_node_pilot.mjs *(new)* (delete if rejected)
- scripts/test_done_run_wrapper.py
- scripts/test_worktree_closeout_migrate.py

Primary class anchors:

- FixtureMixin in scripts/test_done_run_wrapper.py
- WorktreeCloseoutTest in scripts/test_worktree_closeout_migrate.py

Evidence: Node and mise are installed in the authoring environment. This task sets up only the measured candidate runtime before comparing equivalent behavior and process/Git work; Task 5 later adds the required-suite entrypoint. If Node is not faster and profiles still attribute material cost to Python execution itself, evaluate one additional suitable runtime such as Rust through mise; if costs remain shell/Git/subprocess waits, compare narrower or direct tools instead.

- [x] Given high-cost cases in the two longest suites, expects mise to pin Node and a built-in test pilot to invoke the same production commands, map each case one-to-one to exact Python test IDs/assertions, and match inputs and side effects. [class: REPOSITORY_TEST]
- [x] Given three matched Python/Node rounds, expects identical cases, inputs, environment and limits in Python/Node, Node/Python, Python/Node order. Capture wall time, parity and process/Git counts with process context; unassigned controller overlap makes the round inconclusive. Host load and Heavy waits are context only; cap scripts at 60s and campaign at 300s. [class: REPOSITORY_TEST]
- [x] For Python/Node, gain=median(Python wall)-median(Node wall); retain Node only if gain>max(range_Python,range_Node), each range=max-min across the three rounds, and parity/resource checks pass. [class: REPOSITORY_TEST]
- [x] Given complete Node evidence and runtime support, keeps Node only when parity/resource checks pass and Candidate gain qualifies; complete evidence of failure is a rejection. Incomplete capped evidence is inconclusive, removes the Node pin, preserves Python tests and routes any viable rerun through the no-candidate disposition. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Node is rejected and profiling shows material Python runtime/CPU cost, expects one additional runtime to compare the same mapped cases in three orders: Python/candidate, candidate/Python, Python/candidate. Match inputs, environment and limits; require parity for all retained signals. Keep it only when Candidate gain qualifies; reject on parity/gain failure and mark inconclusive when 60s per script or 300s total cannot produce complete evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a shell/Git/subprocess wait hotspot, expects a direct/narrow trial of that operation, preserving assertions and required process/Git/filesystem/lock effects. Run three matched rounds ordered baseline/candidate, candidate/baseline, baseline/candidate; match inputs, environment and limits. Keep only if parity passes and Candidate gain qualifies; reject on failure or mark inconclusive if 60s per script or 300s total prevents evidence. No language speedup is credited. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a candidate is retained, expects the full-suite runner to replace only its mapped Python IDs and report each candidate case once under its original suite; rejected or inconclusive trials leave Python inventory intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an alternative-runner rejection, expects all Python cases and assertions to remain intact and an evidence-backed rejection; Task 5 handles any residual disposition after the final full-suite outcome. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: tests: compare alternative-language pilots on slow test paths [class: IMPLEMENTATION_REQUIRED]

### Task 4: Add the bounded parallel suite runner and focused validation

Context surface: the plan's Terms and this task; referenced, never restated.

Files:

- scripts/run_required_test_suite.py *(new)*
- scripts/test_required_test_suite.py *(new)*

Primary class anchors:

- RequiredTestSuiteRunner in scripts/run_required_test_suite.py, which owns inventory discovery, suite and shard scheduling, per-script and cumulative runner deadlines, process cleanup, test collection accounting and one aggregate result per source script.

- [x] Given a source suite, expects its 60s clock to start after scheduler admission acquires the source slot and scheduling gate, and to cover discovery, shard queueing/execution, cleanup, capture and in-memory source-result finalization; aggregate JSON serialization and report-file writing count against 300s. [class: REPOSITORY_TEST]
- [x] Given scheduling, classify mutable paths, locks, environment and child effects; unknown/conflicting work serializes. Use Terms-eligible selectors; report each shard ID, source suite, scheduling class, queue/run/start/end/duration, collected/executed counts and outcome. [class: IMPLEMENTATION_REQUIRED]
- [x] Given any Python child, expects the configured test venv; pin `AI_PLAYBOOK_TEST_VENV`/`PATH` and clear or pin `PYTHONPATH`/`PYTHONHOME`. [class: REPOSITORY_TEST]
- [x] Given hostile inherited `AI_PLAYBOOK_TEST_VENV`, `PATH`, `PYTHONPATH` or `PYTHONHOME`, expects an integration test to prove the child interpreter, imports and helpers resolve from the configured venv. [class: REPOSITORY_TEST]
- [x] Given inherited pytest selection/plugin variables, expects the runner to pin or clear `PYTEST_ADDOPTS`, `PYTEST_PLUGINS` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD`. Neutralize or reject hostile deselection; execute a known case and never report a filtered subset complete. [class: REPOSITORY_TEST]
- [x] Given a focused selector, expects only named suites under the same script bound and marks the report partial. Full runs omit it and re-derive inventory. [class: REPOSITORY_TEST]
- [x] Given profiles, sample the highest-cost remaining suite or shard group per scheduling class; record paths and digests. Compare k only on overlapping samples; full inventory is acceptance. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the Task 4 sample, run matched rounds 1/4/16, 4/16/1 and 16/1/4 under identical inputs, environment and limits; apply the 60s source and 300s campaign caps. This initial profile chose 16; Task 5 later superseded it with the operator cap of 8. [class: REPOSITORY_TEST]
- [x] For initial candidates k in {4,16}, retain only when median gain exceeds max run range and resource checks pass; incomplete evidence defaults to one worker. Task 5 supersedes the 16-worker choice with cap 8. [class: REPOSITORY_TEST]
- [x] Given a source suite, enforce 60s after scheduler admission (source slot and gate acquired) through discovery, shard queueing/execution, capture, descendant cleanup and in-memory source-result finalization; aggregate JSON writing stays under the 300s suite limit. Each shard has a 60s launch-to-capture ceiling. Pre-admission queue counts only toward 300s. Heavy's limit starts at submission, including queue. Overruns fail; start TERM/KILL early enough to report. [class: REPOSITORY_TEST]
- [x] Given class-only, method-sharded, pytest and substitution fixtures, expects correct selectors/argv and one-to-one IDs; omitted, duplicated, zero-case or count-missing work fails even on child exit zero. [class: REPOSITORY_TEST]
- [x] Given a configured cumulative runner deadline below 300 seconds, expects cleanup and complete result/report writing before that deadline; Task 5 sets its value from measured mise startup, cleanup and report-writing margin. [class: REPOSITORY_TEST]
- [x] Given a TERM-ignoring child, drive production timeout/reap with a one-second test deadline. Assert timeout, complete report, no survivor in captured process groups, fail-closed uncertainty and 60s production default. [class: REPOSITORY_TEST]
- [x] Given synthetic suites, expects queue-wait and cumulative-deadline accounting, inventory drift, failure/error/skip propagation, lock or file conflicts, and serial scheduling for unknown suites. [class: REPOSITORY_TEST]
- [x] Given SIGINT/TERM, stop admissions, reap process groups captured from worker PPID snapshots within the cleanup bound, report active/unstarted suites cancelled and exit nonzero. A captured survivor or uncertain cleanup fails; reparented descendants remain an open investigation. [class: REPOSITORY_TEST]
- [x] Commit: tests: add the bounded required-suite runner [class: IMPLEMENTATION_REQUIRED]

### Task 5: Set up mise, evaluate Heavy and own final acceptance

Context surface: the plan's Terms and Tasks 3-4; referenced, never restated.

Files:

- mise.toml
- mise.lock (when tools are configured)
- README.md
- AGENTS.md
- scripts/run_required_test_suite.py
- scripts/test_required_test_suite.py
- docs/history/feature-notes/2026-11-08-test-suite-fast-feedback-refactor.md *(new)*
- docs/history/feature-notes/2026-11-08-test-suite-fast-feedback-runner-report.md *(new)*
- docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv *(new; operator-requested diagnostic artifact)*
- docs/history/backlog/2026-11-08-test-suite-runtime-residual-optimization-path.md
- docs/history/backlog/2026-11-08-heavy-slot-active-command-terminology.md
- docs/history/backlog/ (conditional new dated residual origin if either limit is missed)
- docs/history/backlog/PLAN-PROMPTS.md

Evidence: Dev Quality Gates describes mise as a pinned toolchain and task manager, not a checker. Official mise documentation supports task and run timeouts, bounded jobs, shared-resource locks and JSON task reports. A task timeout covers each command entry separately, so each bounded task must run one command. On Unix mise uses SIGTERM followed by SIGKILL five seconds later; the project runner owns process-tree cleanup and the final complete run. The repository had no mise configuration at plan start; Task 3 adds only a measured candidate runtime and this task adds the required-suite task. mise 2026.11.4 is installed from Homebrew on the current notebook. Heavy documents machine-wide file-lock semaphore slots shared by checkouts, queue/run JSONL metrics, an unfair wait queue and CI bypass; the temporary trial must prove both worktrees share the same pool identity on a local filesystem.

Operator update (2026-11-10): supersede Task 4's initial 16-worker selection and cap future runner and matched-campaign concurrency at eight workers. The exact 145-ID diagnostic completed all cases at eight in 83.568 seconds without per-test timeouts; earlier 16-worker capped profiles stalled before collection. This resource-conscious cap does not satisfy the 60-second source limit. The per-test duration CSV and remaining Git/checkout optimization work are recorded in the residual backlog; the 300-second full acceptance remains not run until a future exact profile passes 60 seconds. The successful-exit cleanup canary proves cleanup for a detached child still present in the worker's process snapshot; reparented grandchildren remain an open investigation recorded in the residual backlog.

Sources: [Dev Quality Gates](https://github.com/mokevnin/dev-quality-gates), [adoption guide](https://github.com/mokevnin/dev-quality-gates/blob/main/docs/adopt.md), [mise task configuration](https://mise.jdx.dev/tasks/task-configuration), [mise task execution](https://mise.jdx.dev/tasks/running-tasks.html), [mise locks](https://mise.jdx.dev/dev-tools/mise-lock.html), and [Heavy README](https://github.com/mokevnin/heavy).

- [x] Given hostile interpreter/import variables and PATH without the venv bin, expects `test:required` to pin `AI_PLAYBOOK_TEST_VENV`/`PATH`, clear `PYTHONHOME`/`PYTHONPATH`, report worker count and interpreter/import roots; README.md and AGENTS.md document the command and both limits. [class: REPOSITORY_TEST]
- [x] Given Task 3 candidate results, expects only a measured, supported runtime to remain pinned; rejected runtimes and lock entries are removed. Heavy uses temporary mise setup or supported local install. [class: IMPLEMENTATION_REQUIRED]
- [x] Given two worktrees, expects three matched, overlapping baseline/Heavy pairs with identical inputs/env/limits; baseline exceeds Heavy slots, Heavy stays within slots and queues in each pair; each command <=60s and campaign <=300s. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each Heavy run, expects one shared local HEAVY_DIR, pool and slot count with acquisition logs; CI/nested bypass is absent, and bypassed, unproven, non-overlapping or separate-pool runs are inconclusive. [class: IMPLEMENTATION_REQUIRED]
- [x] Given matched controls and Heavy runs, qualifies follow-up only if Candidate gain or the Heavy control result holds, including a passing cleanup canary; host load is context. Incomplete evidence is inconclusive; complete nonqualifying evidence is rejected. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Heavy timeout/signal with a TERM-ignoring child and waiting contender, reap captured groups before exit; Heavy holds its slot until exit. Start 60s at submission; early release, overrun, captured survivor or uncertain cleanup fails the canary. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a passing worker leaves a detached child visible in the cleanup snapshot, reap it before pass; uncertain cleanup or a captured survivor fails the shard. Reparented descendants remain in the lifecycle backlog. [class: REPOSITORY_TEST]
- [x] Given any Heavy result, removes trial setup before landing; favorable evidence creates a separate Machinery-admission origin/prompt, incomplete evidence a rerun prompt, and failed evidence a rejection. Heavy never wraps suite acceptance. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each timeout-bounded mise task, expects exactly one command; tool installation and lock resolution finish before timing. [class: REPOSITORY_TEST]
- [x] Given identical focused inputs, records direct-runner/mise timing and parity; credit only wrapper overhead to mise, not internal shell/Git savings. [class: REPOSITORY_TEST]
- [x] Given full acceptance is pursued, the mise timeout/signal canary stops scheduling, reaps captured groups, writes a complete report and exits nonzero; for the authorized partial path, records this canary as unverified in the existing residual backlog and keeps full acceptance blocked. [class: REPOSITORY_TEST]
- [x] Given the exact 145-ID profile passes within 60 seconds, expects one full mise run over the re-derived inventory and separate 60/300-second outcomes; when it misses, records the 60-second miss and 300-second acceptance as not run. [class: REPOSITORY_TEST]
- [x] Given user-authorized partial delivery after a miss, report 60s and 300s separately in the feature note/backlog, keep the residual prompt open, and close out `Executed`, origin disposition and partial archive. [class: IMPLEMENTATION_REQUIRED]
- [x] Given either limit miss, commit a dated backlog origin and ready prompt before archive, covering slow suites, measurements, blockers and next comparisons. Reuse plan-no-candidate-follow-up-disposition; a feature note alone cannot close a miss. [class: IMPLEMENTATION_REQUIRED]
- [x] Given both limits pass, expects explicit no-follow-up only when evidence leaves no concrete viable candidate; the partial path records concrete residuals and does not claim both limits passed. [class: IMPLEMENTATION_REQUIRED]
- [x] Given final results, write the durable report at docs/history/feature-notes/2026-11-08-test-suite-fast-feedback-runner-report.md with digests, environment, runner/workers, IDs, classes, times, outcomes, samples, decisions and uncertainty; the feature note links it. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: tooling: add the mise test-suite entrypoint [class: IMPLEMENTATION_REQUIRED]

### Task 6: Add Dev Quality Gates lookup guidance

Context surface: the plan's Terms, this task and the existing Machinery admission protocol; referenced, never restated.

Files:

- AGENTS.md
- agents/skills/plans/SKILL.md
- agents/skills/self-heal/SKILL.md

Primary anchors:

- Machinery admission protocol in AGENTS.md
- Plan Quality Gate in agents/skills/plans/SKILL.md
- Recovery steps in agents/skills/self-heal/SKILL.md

Evidence: the Dev Quality Gates README identifies one recommended tool per job and records limits. Its adoption guide says to keep a current tool that already performs the job, inspect each recommendation's limitations, and skip irrelevant categories. The plans skill scopes proposed tooling; self-heal handles observed gate failures.

- [x] Given a slow, failing, missing or ineffective quality gate, expects the repository guidance and self-heal workflow to consult the Dev Quality Gates catalogue and adoption guide as candidate sources, then verify the current official docs and repository-specific fit. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a proposed new test, analysis or quality instrument, expects the plan workflow to compare the candidate with existing tools, record its limits and enforcement behavior, and state an evidence-based adopt or reject disposition. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a catalogue category that is absent or a candidate that does not fit, expects an explicit skip reason without installing an unrelated tool or changing an existing standard. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the existing Machinery admission protocol, Plan Quality Gate and Recovery steps, expects compact updates in those homes, equivalent-byte deletion whenever operative text grows, and realistic examples validating the lookup behavior. [class: REPOSITORY_TEST]
- [x] Commit: skills: consult Dev Quality Gates for tooling decisions [class: IMPLEMENTATION_REQUIRED]
## Disposition of migrated backlog items
- `docs/history/backlog/2026-11-08-test-suite-runtime-residual-optimization-path.md`: partial execution is recorded in this archived plan; the origin file is deleted in this completion pass. The remaining full-suite acceptance and process-containment investigations stay open in `docs/history/backlog/2026-11-09-required-test-suite-five-minute-residual.md`.
