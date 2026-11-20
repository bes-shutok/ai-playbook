# Plan: Test Suite Runtime Reduction Follow-up

Language guidance: `projects/.ai-playbook/python_guidelines.md`

Backlog origin: `docs/history/backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md`
Driving force: efficiency
Plan review record: `.ai-playbook/reviews/2026-11-07-plan-review-test-suite-runtime-reduction-follow-up-r*.md`
Authoring claim: 2026-11-07-test-suite-runtime-reduction-follow-up.md (session 01a1b5e6-21f5-70b2-b228-3e9367e80bd1)
Executed: yes (f6c7363ab895f3c479468ff60a7d48c1f14ec52e)

## Terms

- **Complete suite:** The full required set of discovered script test suites; its inventory and outcomes stay comparable between measurements.
- **Regression signal:** A distinct behavior assertion that detects an unwanted result, including subprocess, Git, filesystem, lock, and failure-path behavior.
- **Fixture:** Test setup data and behavior that prepares a case, including its environment and temporary state.
- **Process-level parallelism:** Running independent suites or cases in separate operating-system processes with a measured worker and resource limit.
- **Language-specific overhead:** Python collection, interpreter, or process-startup time attributable to Python and plausibly reducible by another implementation. It is material only at 5% or more of comparable serial-suite time; costs inseparable from test work or measurement noise remain unproven.
- **Instrumentation overhead:** Extra time or resource use introduced by profiling or measurement tools.
- **Immutable input:** Reusable data that a test cannot change and that does not depend on repository, environment, manifest, or lock state.

## Why

The accepted complete-suite result improved by 44.10%, from 3,643.556 seconds to 2,036.658 seconds, while the 50% target remains unmet. The existing evidence shows that fixture isolation and removal of duplicate inherited executions worked, but it does not establish that the remaining cost is irreducible or that parallelism, reuse, caching, or a language change would help safely. The measured result is 214.880 seconds above the 1,821.778 seconds that would equal a 50% reduction from the original baseline.

## Gist & Examples

TLDR: Measure and prototype safe runtime options, extending efficiency beyond the accepted 44.10% reduction.

**Before (today):** Given a request to run the complete required suite, the serial run takes about 2,036.658 seconds in the accepted comparison. The isolated home/configuration fixtures and test-only lock timings reduced host-specific work, and the landing test mixin removed 114 repeated inherited executions while retaining all 65 unique methods. These changes saved time without replacing real process, Git, or lock behavior. A standalone home-isolation experiment was slower when it retained default wait/grace settings. The result is still short of the 50% target, and the other 86 suites' aggregate increased by 50.367 seconds; the available evidence does not prove that this increase was caused by a regression. Parallel execution, cache invalidation, startup reuse, and alternate-language cost remain unmeasured. Running fewer suites was rejected because it changes inventory instead of reducing the required work.

**After (this plan):** Given the same complete-suite trigger and a freshly re-derived inventory, the run records a comparable baseline, profiles residual costs, and measures bounded process workers and safe startup/reuse candidates. It tests an alternate-language prototype only when Python-specific work is a measured hotspot. If an experiment preserves regression signals and shows a worthwhile benefit, the final comparison quantifies it; otherwise the report identifies why the serial Python harness remains the measured best option.

**Edge cases:** If host contention or profiling overhead dominates a sample, label it uncertain and do not project it as a suite speedup. If parallel runs vary, leak state, exceed their resource bound, or lose failure detail, reject that path. If profiled Python-specific overhead is below 5% of comparable serial-suite time, or cannot be separated from test work or noise, do not build a Go/Rust prototype.

## Outcome

Produce a measured recommendation for reducing the time required to run the complete test suite while preserving its distinct regression signals.

- The remaining runtime contributors and limits of their measurement are documented.
- Process parallelism, startup reuse, caching, and a conditional language prototype have explicit evidence-based dispositions.
- A promising safe candidate has a comparable final measurement, or the report records a concrete stopping point.

Gate delta: only three complete-suite runs are authorized: one fresh baseline, exactly one required execute-plan Phase 2 validation (separately authorized 2026-11-08), and at most one final comparison if a candidate qualifies. Phase 2 does not qualify a candidate. No gate, validator, lock, ledger, ceremony, or blocking review layer is added.

## Assumptions

- assume the accepted 44.10% comparison is the historical reference, not a proof about a new host; basis: `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction.md` records host-load uncertainty and the operator's acceptance.
- assume execution re-derives the suite inventory, source revision, environment, and commands; basis: the baseline and final notes bind timings to exact inventory and host conditions.
- assume process-level parallelism is the first experiment and an alternate-language prototype requires evidence of material Python-specific overhead; basis: the operator-confirmed scope and the origin backlog's conditional arms.
- assume the plan delivers reversible experiments and a recommendation, not permanent harness or runner changes; basis: the user confirmed this scope on 2026-11-07, and the origin asks for a safe path recommendation before committing to a change.
- assume Gate delta defines the complete-suite run budget and authorization receipts; accepting 44.10% alone authorizes no run.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep the required complete-suite inventory and report all failures, errors, and skips; changed-suite selection is not a runtime improvement.
- Keep every experiment reversible and outside permanent harness files. Do not alter production workflow behavior, test-selection policy, or distinct regression signals.
- Follow Gate delta’s run budget; Phase 2 is required validation, not candidate qualification. Use focused checks for other experiments.
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

**Ship when:** [class: OPERATIONS_FOLLOW_UP] The execution manifest records the authorization receipts and results for the Gate delta run budget. Acceptance of 44.10% alone authorizes no run; no other complete-suite run is permitted.

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

From the repository root, validate after writing the report. Task 1 owns the baseline; execute-plan owns one Phase 2 suite after all tasks pass; Task 3 owns a final comparison only for a qualifying candidate. No other full-suite invocation is allowed.
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

- [x] Given the current execution tree, expects one complete-suite baseline over its re-derived inventory with revision, environment, command, elapsed time, and all outcomes recorded. [class: REPOSITORY_TEST]
- [x] Given residual hotspots, expects a profile to separate test work, Python collection/startup, subprocess, filesystem/Git setup, waits, host load, and instrumentation overhead. [class: REPOSITORY_TEST]
- [x] Given the prior comparison and fresh evidence, expects the report to explain what worked, what did not, and what remains unproven without overstating causality. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the accepted result, expects the report to retain 44.10% as an interim result and state that both original completion conditions remain unmet unless new evidence changes them. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `tests: record residual suite profile and benchmark baseline` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Measure process parallelism and safe startup reuse

Context surface: the plan's Terms and this task.

Files:
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md`

- [x] Given profile-selected independent suites or cases, expects a reversible process-level pilot with a predeclared worker/resource bound, complete result collection, and deterministic outcome ordering. [class: REPOSITORY_TEST]
- [x] Given a parallel candidate, expects at least three focused repetitions with matching outcomes, bounded resources, no cross-case state leakage, and complete failure propagation before it can be recommended. [class: REPOSITORY_TEST]
- [x] Given each candidate and its serial control, expects three matched focused runs; select at most one only when median gain exceeds the larger observed run-to-run range and outcome, coverage, isolation, and resource checks pass. [class: REPOSITORY_TEST]
- [x] Given a startup-reuse or cache candidate, expects changed inputs to invalidate reuse and each case's mutable repository, environment, manifest, and lock state to stay isolated; reject it if these checks fail. [class: REPOSITORY_TEST]
- [x] Given serial execution, parallelism, and reuse measurements, expects the report to compare time, resource contention, failure behavior, portability, and maintenance cost without changing suite selection. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `tests: record bounded parallel and reuse experiments` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Test the conditional language option and recommend a path

Context surface: the plan's Terms and this task.

Files:
- `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md`

- [x] Given Python-specific collection, interpreter, or startup cost at least 5% of comparable serial-suite time, expects a reversible representative prototype with parity, boundary, portability, setup, ownership, and maintenance costs measured; below 5%, or unseparated from test work/noise, expects no prototype and records why. [class: REPOSITORY_TEST]
- [x] Given a candidate meeting the Evaluation Criteria selection rule, expects one final complete-suite comparison on the same inventory and comparable settings; if none qualifies, records why no candidate merits that run. [class: REPOSITORY_TEST]
- [x] Given all measured and unmeasured options, expects one recommendation toward the remaining 50% gap or an evidence-backed stopping point that preserves every distinct regression signal. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `tests: recommend measured suite runtime path` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

The promoted origin `docs/history/backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md` is covered by this completed plan and is deleted in the same archive landing. Its request to preserve the accepted 44.10% interim result, explain what worked and what remained unproven, and investigate safe runtime options is carried into this plan. Execution recorded the 88-suite Phase 2 validation at 1,614.146 seconds with zero nonzero suites and a matching inventory. No measured candidate qualified for the final complete-suite comparison; process parallelism, safe reuse or caching, and a language prototype therefore remain unproven follow-up options for a separately authorized plan. The detailed evidence and optimization recommendations are in `docs/history/feature-notes/2026-11-07-test-suite-runtime-reduction-follow-up.md`.
