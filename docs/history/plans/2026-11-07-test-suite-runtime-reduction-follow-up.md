# Plan: Test Suite Runtime Reduction Follow-up

Language guidance: `projects/.ai-playbook/python_guidelines.md`

Backlog origin: `docs/history/backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md`
Driving force: efficiency
Plan review record: `.ai-playbook/reviews/2026-11-07-plan-review-test-suite-runtime-reduction-follow-up-r*.md`
Authoring claim: 2026-11-07-test-suite-runtime-reduction-follow-up.md (session 01a1b5e6-21f5-70b2-b228-3e9367e80bd1)
Executed: no

## Terms

- **Complete suite:** The full required set of discovered script test suites; its inventory and outcomes stay comparable between measurements.
- **Regression signal:** A distinct behavior assertion that detects an unwanted result, including subprocess, Git, filesystem, lock, and failure-path behavior.
- **Fixture:** Test setup data and behavior that prepares a case, including its environment and temporary state.
- **Process-level parallelism:** Running independent suites or cases in separate operating-system processes with a measured worker and resource limit.
- **Language-specific overhead:** Time attributable to Python collection, interpreter work, or Python process startup that a different implementation could plausibly reduce.
- **Instrumentation overhead:** Extra time or resource use introduced by profiling or measurement tools.
- **Immutable input:** Reusable data that a test cannot change and that does not depend on repository, environment, manifest, or lock state.

## Why

The accepted complete-suite result improved by 44.10%, from 3,643.556 seconds to 2,036.658 seconds, while the 50% target remains unmet. The existing evidence shows that fixture isolation and removal of duplicate inherited executions worked, but it does not establish that the remaining cost is irreducible or that parallelism, reuse, caching, or a language change would help safely. The measured result is 214.880 seconds above the 1,821.778 seconds that would equal a 50% reduction from the original baseline.

## Gist & Examples

TLDR: Measure and prototype safe runtime options, extending efficiency beyond the accepted 44.10% reduction.

**Before (today):** Given a request to run the complete required suite, the serial run takes about 2,036.658 seconds in the accepted comparison. The isolated home/configuration fixtures and test-only lock timings reduced host-specific work, and the landing test mixin removed 114 repeated inherited executions while retaining all 65 unique methods. These changes saved time without replacing real process, Git, or lock behavior. A standalone home-isolation experiment was slower when it retained default wait/grace settings. The result is still short of the 50% target, and the other 86 suites' aggregate increased by 50.367 seconds; the available evidence does not prove that this increase was caused by a regression. Parallel execution, cache invalidation, startup reuse, and alternate-language cost remain unmeasured. Running fewer suites was rejected because it changes inventory instead of reducing the required work.

**After (this plan):** Given the same complete-suite trigger and a freshly re-derived inventory, the run records a comparable baseline, profiles residual costs, and measures bounded process workers and safe startup/reuse candidates. It tests an alternate-language prototype only when Python-specific work is a measured hotspot. If an experiment preserves regression signals and shows a worthwhile benefit, the final comparison quantifies it; otherwise the report identifies why the serial Python harness remains the measured best option.

**Edge cases:** If host contention or profiling overhead dominates a sample, label it uncertain and do not project it as a suite speedup. If parallel runs vary, leak state, exceed their resource bound, or lose failure detail, reject that path. If Python-specific overhead is not material, do not build a Go/Rust prototype.

## Outcome

Produce a measured recommendation for reducing the time required to run the complete test suite while preserving its distinct regression signals.

- The remaining runtime contributors and limits of their measurement are documented.
- Process parallelism, startup reuse, caching, and a conditional language prototype have explicit evidence-based dispositions.
- A promising safe candidate has a comparable final measurement, or the report records a concrete stopping point.

Gate delta: adds one dispatch-pausing external prerequisite: operator authorization for the bounded complete-suite baseline and conditional final comparison; no repository gate, validator, lock, ledger, required ceremony, or blocking review layer is added.

## Assumptions

- assume the accepted 44.10% comparison is the historical reference, not a proof about a new host; basis: `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction.md` records host-load uncertainty and the operator's acceptance.
- assume execution re-derives the suite inventory, source revision, environment, and commands; basis: the baseline and final notes bind timings to exact inventory and host conditions.
- assume process-level parallelism is the first experiment and an alternate-language prototype requires evidence of material Python-specific overhead; basis: the operator-confirmed scope and the origin backlog's conditional arms.
- assume the plan delivers reversible experiments and a recommendation, not permanent harness or runner changes; basis: the user confirmed this scope on 2026-11-07, and the origin asks for a safe path recommendation before committing to a change.
- assume at most one complete-suite baseline and one final candidate comparison are run; basis: the prior run's accepted boundary and this follow-up's bounded comparison scope.
- assume no complete-suite benchmark in this follow-up is authorized by the earlier 44.10% acceptance; basis: the origin backlog requires authorization for this follow-up's baseline and final comparison.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep the required complete-suite inventory and report all failures, errors, and skips; changed-suite selection is not a runtime improvement.
- Keep every experiment reversible and outside permanent harness files. Do not alter production workflow behavior, test-selection policy, or distinct regression signals.
- Run no more than one complete-suite baseline and one final candidate comparison. Use focused checks for other experiments.
- Do not call an option effective or ineffective unless the experiment measures it; state uncertainty and profiling overhead explicitly.
- Treat concurrency as process-based, resource-bounded work. Same-process threads are not a pilot candidate for tests that mutate ambient environment or exercise locks.

## Evaluation Criteria

**Quality dimensions:**
- Performance: comparable complete-suite wall time, residual contributor attribution, worker resource use, and measurement overhead; report host contention and uncertainty.
- Candidate selection: compare three matched serial-control runs with three runs per candidate; advance at most one candidate only when its median focused wall time improves by more than the larger observed run-to-run range, all outcomes and regression signals are preserved, and the predeclared resource bound is met. If several qualify, choose the largest median gain within the resource bound; if none qualify, skip the final complete-suite run.
- Coverage: complete inventory and outcomes remain accounted for; every removed, merged, or skipped signal has a retained behavior witness and evidence that it is redundant or obsolete.
- Reliability: parallel experiments are deterministic, bounded, fully failure-accounted, isolated, and leave no shared or ambient state behind; a recommended path passes at least three focused repetitions.
- Maintainability and portability: compare dependencies, setup/build effort, ownership, invalidation rules, supported environments, and maintenance cost against the serial Python harness.

**Done when:**
- A report records the fresh baseline, residual profile, instrumentation and host limits, experiment outcomes, and measured versus unmeasured options.
- Any recommended parallel candidate passes three focused repeated runs with the same outcomes, bounded resources, no state leakage, and complete failure propagation.
- A final complete-suite comparison is recorded for a candidate selected by the profile, or the evidence explains why no candidate merits that run and identifies the stopping point.
- The report recommends a safe implementation path toward the remaining 50% gap or explains why further in-scope reduction costs more in coverage, reliability, portability, or maintenance than its measured benefit.

**Ship when:** [class: OPERATIONS_FOLLOW_UP] The operator owns providing explicit authorization for this plan's bounded protocol and its two complete-suite targets (one fresh baseline and, only if a candidate qualifies, one final comparison) before either invocation. Closure evidence is the exact authorization receipt recorded in the execution log. Acceptance of the earlier 44.10% result does not authorize these follow-up runs. Until that receipt exists, tasks requiring a complete-suite invocation are not executable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope when valid.

**Production code:** none; experiments do not land production changes.

**Tests:** none; test sources are read and copied for reversible experiments but are not modified by this plan.

**Documentation:**
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md` (Task 1) *(new)*
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md` (Task 2)
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md` (Task 3)

**Plan-related extension:** review may include temporary experiment inputs and notes only when they directly support this plan's measurements. Any permanent harness, test, runner, or configuration change is outside this plan and requires a later decision based on this report.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md`; it controls when and which suites run, not the cost of the required complete suite.
- `scripts/done_run.sh` and `scripts/land_squash.sh`; production workflow behavior is not being changed.

## Validation Commands

Run from the repository root after the report is written. The bounded complete-suite baseline and final comparison are owned by Tasks 1 and 3; do not add full-suite invocations at other task or review boundaries.
Validation preamble: on 2026-11-07, plan readiness pre-round, the plan-file em-dash scan, and the repository public-hygiene scan all passed at authoring time. No test suite or benchmark was run while authoring this plan.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
python3 scripts/plan_readiness.py docs/history/plans/2026-11-07-test-suite-runtime-reduction-follow-up.md --pre-round || exit 1
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-11-07-test-suite-runtime-reduction-follow-up.md || exit 1
PUBLIC_HYGIENE_REPO_ROOT="$REPO" bash scripts/scan-public-hygiene.sh || exit 1
```

### Task 1: Re-establish the complete-suite baseline and profile residual cost

Context surface: the plan's Terms and this task.

Files:
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md` *(new)*

- [ ] Given the current execution tree, expects one complete-suite baseline over its re-derived inventory with revision, environment, command, elapsed time, and all outcomes recorded. [class: REPOSITORY_TEST]
- [ ] Given residual hotspots, expects a profile to separate test work, Python collection/startup, subprocess, filesystem/Git setup, waits, host load, and instrumentation overhead. [class: REPOSITORY_TEST]
- [ ] Given the prior comparison and fresh evidence, expects the report to explain what worked, what did not, and what remains unproven without overstating causality. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the accepted result, expects the report to retain 44.10% as an interim result and state that both original completion conditions remain unmet unless new evidence changes them. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `tests: record residual suite profile and benchmark baseline` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Measure process parallelism and safe startup reuse

Context surface: the plan's Terms and this task.

Files:
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md`

- [ ] Given profile-selected independent suites or cases, expects a reversible process-level pilot with a predeclared worker/resource bound, complete result collection, and deterministic outcome ordering. [class: REPOSITORY_TEST]
- [ ] Given a parallel candidate, expects at least three focused repetitions with matching outcomes, bounded resources, no cross-case state leakage, and complete failure propagation before it can be recommended. [class: REPOSITORY_TEST]
- [ ] Given each candidate and its serial control, expects three matched focused runs; select at most one only when median gain exceeds the larger observed run-to-run range and outcome, coverage, isolation, and resource checks pass. [class: REPOSITORY_TEST]
- [ ] Given a startup-reuse or cache candidate, expects changed inputs to invalidate reuse and each case's mutable repository, environment, manifest, and lock state to stay isolated; reject it if these checks fail. [class: REPOSITORY_TEST]
- [ ] Given serial execution, parallelism, and reuse measurements, expects the report to compare time, resource contention, failure behavior, portability, and maintenance cost without changing suite selection. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `tests: record bounded parallel and reuse experiments` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Test the conditional language option and recommend a path

Context surface: the plan's Terms and this task.

Files:
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md`

- [ ] Given material Python-specific collection, startup, or interpreter cost, expects a reversible prototype for one representative hotspot with semantic parity, boundary coverage, portability, build/setup effort, ownership, and maintenance cost measured. [class: REPOSITORY_TEST]
- [ ] Given no material Python-specific cost, expects the report to decline a Go/Rust prototype with the profile evidence that makes it unjustified. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a candidate meeting the Evaluation Criteria selection rule, expects one final complete-suite comparison on the same inventory and comparable settings; if none qualifies, records why no candidate merits that run. [class: REPOSITORY_TEST]
- [ ] Given all measured and unmeasured options, expects one recommendation toward the remaining 50% gap or an evidence-backed stopping point that preserves every distinct regression signal. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `tests: recommend measured suite runtime path` [class: IMPLEMENTATION_REQUIRED]
