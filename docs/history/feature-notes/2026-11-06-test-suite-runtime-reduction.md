# Test-suite runtime final comparison

## Result

The final serial run took **2,036.658 seconds (33 minutes 56.7 seconds)** across all 88 discovered script suites. Against the 3,643.556 second baseline, this is a measured reduction of **1,606.897 seconds (44.10%)**. The run preserved the full suite inventory and exposed no new failing test identities. It did not reach the plan's 50% target.

The alternative completion condition is also **not established**: available evidence does not show that further in-scope runtime reduction would unacceptably harm coverage or reliability. All 114 removed landing executions were exact inherited duplicates with retained witnesses, but the remaining optimization options were not proven harmful. Do not claim that 50% was achieved.

### Operator acceptance receipt

- **Confirmation:** The operator wrote, “Accept 44.10% for now.”
- **Confirmation date and scope:** 2026-11-07; this one-run acceptance applies to this plan’s final 88-suite full comparison and to closing this execution after the requested follow-up and investigation.
- **Why executable now:** The final benchmark is complete, and the operator-requested detailed follow-up item and its investigation entry are recorded and validated. No remaining full-suite experiment is needed to honor this one-run disposition.
- **Completion evidence:** [follow-up backlog item](../backlog/2026-11-07-test-suite-runtime-reduction-follow-up.md) and [investigation entry](../backlog/PLAN-PROMPTS.md#test-suite-runtime-reduction-follow-up); the investigation validator reported 10 entries, 35 dispositions and zero violations.
- **Disposition:** The 50% target remains unmet, and the alternative harm condition is not established. The report and archived plan must preserve both conditions as unmet; the interim acceptance does not meet either condition.

## Reproduction and environment

- Baseline revision: `1933ba5f4c5b4a75a6a1948da34238ede9aa8782`; final revision: `58b1a58eadbd345930d51e52fd04994ade24080d`.
- Both runs used Python 3.14.10, pytest 9.1.1, macOS 26.6.2 arm64, and 12 logical CPUs. No dependency installation occurred.
- Both used the sorted `scripts/test_*.py` inventory, one independent pytest process per suite, serial execution, and continued after failures. Every suite used `python3 -m pytest <suite> -q --durations=0 --junitxml=<output>/<suite>.xml`, with the test venv prepended to `PATH` and `/usr/bin/time -l` around each command.
- One monotonic timer covered the complete sequence from immediately before the first suite command through final result persistence. Inventory, interpreter and environment discovery occurred before that timer. Per-suite timings include pytest and child process startup, fixture setup, waiting, JUnit output, and logging. No profiler was enabled in either complete run; the same lightweight per-suite resource and JUnit instrumentation was used.
- Baseline load average was 15.995 / 15.202 / 13.628 at start and 8.795 / 10.403 / 10.902 at finish. Final load average was 6.457 / 6.673 / 8.912 at start and 13.631 / 10.729 / 9.406 at finish. During the last final suite, another full inventory pytest process was active in a different worktree. It did not share this checkout, but it adds host-load uncertainty. These are single runs on a shared host, not a controlled repeat or confidence interval.

Raw per-suite commands, timestamps, source hashes, JUnit XML, resource output and analysis are in `.ai-playbook/metrics/test-suite-runtime-reduction/final/`. Baseline evidence is in `.ai-playbook/metrics/test-suite-runtime-reduction/baseline/` and is summarized in the linked [baseline report](2026-11-06-test-suite-runtime-reduction-baseline.md).

## Inventory and outcomes

The baseline and final inventories both contain 88 suites. There are no added or missing suites. Eighty-six suite files have identical SHA-256 values; the only changed test files are `scripts/test_done_run_wrapper.py` and `scripts/test_land_squash.py`.

| Measure | Baseline | Final | Difference |
|---|---:|---:|---:|
| Complete sequence wall time | 3,643.556s | 2,036.658s | 44.10% lower |
| Suites completed | 88 | 88 | 0 |
| Collected outcomes including subtests | 4,000 | 3,886 | 114 fewer |
| Failures | 8 | 7 | 1 fewer |
| Errors | 0 | 0 | 0 |
| Skips | 1 | 1 | 0 |

The 114 fewer outcomes are exactly the duplicate inherited executions removed from the landing suite. The complete 57-row [inheritance map](../../../.ai-playbook/metrics/test-suite-runtime-reduction/baseline/landing-inheritance-map.json) maps both removed subclass identities for each base test to its retained witness. All 65 unique landing methods remain. No other suite or test was removed.

The baseline failures were five cases in `test_invocation_telemetry.py`, one in `test_learn_router_dispatch.py`, one in `test_machinery_inventory.py`, and one in `test_quota_governor.py`. The final run has the same first seven failing case identities and no new failing identity. The prior quota-governor failure did not reproduce. The single skip remained in `test_docs_branch_sync.py`. These pre-existing failures and the skip remain visible in the raw JUnit records; none was filtered.

## Runtime contributors

| Suite | Baseline | Final | Reduction |
|---|---:|---:|---:|
| `test_done_run_wrapper.py` | 2,330.721s | 789.908s | 66.1% |
| `test_land_squash.py` | 228.124s | 111.672s | 51.0% |
| Both optimized suites | 2,558.845s | 901.580s | 64.8% |
| Other 86 suites, summed | 1,084.711s | 1,135.078s | 50.367s higher |

The wrapper completed with 263 tests and 2 passing subtests. The focused pytest duration was 847.05s and the enclosing shell's `real` time was 847.41s; the complete-suite wrapper time of 789.908s is one full-run observation. The landing suite completed with 65 tests, compared with 179 baseline collected outcomes; the 114 reduction consists only of exact duplicate inheritance. Per-suite resource captures are retained beside each stdout and stderr log. Across all final suites, child user CPU summed to 604.63 seconds and system CPU to 679.12 seconds; the largest per-suite maximum resident set was 131,547,136 bytes. CPU sums and per-process resident maxima are not elapsed wall time or a whole-run memory peak.

## Change and coverage disposition

`FixtureMixin.runner_env()` now gives each wrapper case its own temporary `HOME` and `XDG_CONFIG_HOME`, and pins test-only done-lock poll/wait/grace values. Production defaults are unchanged, explicit per-case clock overrides remain active, and real lock contention, subprocess, Git and filesystem assertions remain in place. Focused characterization and post-change runs passed: wrapper 263 tests plus 2 subtests, 2,185.63s to 847.05s; landing 179 collected outcomes to 65 unique methods, 278.19s to 109.63s. The focused timings are not complete-suite measurements.

The landing fixture helpers now live in `_LandSquashFixtureMixin`. The three test classes use that setup directly, so the two subclasses no longer execute 57 inherited test bodies each. Every case still owns and cleans its own `TemporaryDirectory`. The retained base tests are byte-identical behavior witnesses for all 114 removed duplicate IDs; no unique subclass test was removed.

No caching or parallel path was selected. No shared mutable fixture data was introduced. The complete-run comparison is not evidence that unmeasured options are ineffective.

## Option decisions and remaining limits

| Option | Final disposition | Evidence and limit |
|---|---|---|
| Fixture isolation and test-only clock pins | Selected | Focused characterization preserved real refusal, lock and no-write assertions; full wrapper run passed with all 265 outcomes. Production behavior did not change. |
| Remove exact inherited landing repetitions | Selected | The map proves 114 duplicate executions and retains all 65 unique methods and witnesses. No other collection suppression was used. |
| Bounded parallelism | Not selected | Ambient environment and lock tests make same-process concurrency unsafe without redesign. A process-based path would need bounded resource and failure accounting plus at least three focused isolation repetitions; none was measured. |
| Process or startup reuse | Not selected | Real shell/Python boundaries are regression signals. Reuse semantics, lifecycle ownership, portability and maintenance cost were not measured. |
| Caching | Not selected | Mutable repositories, manifests and lock generations remain case-local. No cache invalidation or mutation-isolation evidence was produced. |
| Changed-scope selection | Rejected as a complete-suite optimization | It would omit suites and change the measured inventory, rather than reduce the cost of the full inventory. Ordinary validation selection remains unchanged. |
| Go/Rust port or replacement runner | Follow-up only | Outside this implementation. No parity, portability or maintenance evidence was collected. |

The focused work removed the measured repeated host probes and lock waits in the wrapper and exact duplicate collection in the landing suite. These changes saved 1,657.265 seconds across those two suites. However, the whole run improved by only 44.10%, and the other suites together took 50.367 seconds longer than baseline. There is no evidence here that further fixture changes, reuse or parallelism would necessarily damage coverage, nor evidence that they can safely supply the additional 214.880 seconds needed to reach 50%. The current evidence therefore supports reporting the measured best result, not the alternative completion claim.

## Reproduction details

For each sorted suite, the exact final argument array and working directory are recorded in `final/suite-results.jsonl`; each suite's resource output and pytest summary are in matching `.stderr.log` and `.stdout.log` files, and JUnit is in the matching `.xml`. `final/metadata.json` records interpreter, environment, source revision, suite hashes and inventory comparison; `final/summary.json` records the monotonic sequence time and start/finish load averages. `final/analysis.json` contains aggregated outcomes, failure identities, resources and comparison arithmetic.

The benchmark completed and all 88 rows, XML files and the sequence summary were persisted. The temporary driver's final console-summary line then raised a `TypeError` because `flush=True` was passed to `json.dumps`; this happened after all suites and aggregates had finished and did not alter test outcomes or saved evidence. No suite was rerun.
