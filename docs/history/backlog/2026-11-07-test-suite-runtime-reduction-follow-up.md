# Backlog: measure the remaining test-suite runtime reduction options

Status: open
Workflow: backlog
Priority: medium
Origin class: operator request (2026-11-07)
Class: fix-class
Driving force: efficiency
Cluster: docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md (same full-suite runtime family, distinct cause: this row measures how to reduce the cost of a required full suite; the sibling sets whether and when that suite runs)

## Problem

The completed test-harness optimization lowered the comparable complete-suite wall time by 44.10%, from 3,643.556 seconds to 2,036.658 seconds across the same 88-suite inventory. The operator accepts this result as an interim outcome so the current plan can close, while the original 50% target remains unmet. A separate measured follow-up is needed to determine whether remaining reduction is practical and which path preserves the suite's regression signals.

The two targeted suites improved substantially: `test_done_run_wrapper.py` fell from 2,330.721 to 789.908 seconds (66.1%), and `test_land_squash.py` fell from 228.124 to 111.672 seconds (51.0%). Across the other 86 suites, summed suite time increased by 50.367 seconds between these runs. The complete-suite result therefore validates the fixture changes but shows that those changes alone do not reach the target. It does not establish that the other 86 suites regressed causally or that the remaining options are harmful.

## Evidence

- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction.md` records the final 88-suite benchmark, exact outcomes, environmental caveats, suite deltas, and option dispositions. It reports 3,886 outcomes, seven failures, zero errors and one skip; all final failure identities were baseline-known, and one baseline failure did not reproduce.
- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction-baseline.md` records the baseline profile, focused experiments, and the limits of each attribution. The selected fixture changes isolate `HOME` and `XDG_CONFIG_HOME` and pin test-only lock timings while retaining real subprocess, Git, and lock behavior. A standalone home-isolation experiment was slower because it retained the default wait/grace behavior.
- The landing suite originally collected 179 cases but only 65 unique methods. The implementation moved shared setup/helpers into a mixin, retained all 65 methods and their behavior, and removed 114 repeated inherited executions with an explicit identity-to-witness map.
- The focused pair measurements improved 61.22% for the wrapper and 60.59% for landing. These are clear wins, but the aggregate complete-suite reduction remained below 50%.
- The final run overlapped a separate full test run near its tail; host load varied substantially during focused experiments. Treat the measured result as the accepted comparison for this execution, with host contention named as uncertainty rather than as an adjustment to the reported time.

## What worked

- Measuring fixture inputs and lock waits identified a safe, narrow improvement: provide isolated test-local home/config directories and shorter test-only lock clocks. This cut host-specific advisory/configuration work and avoidable waits without mocking production subprocess, Git, or lock boundaries.
- Consolidating fixture helpers into a non-test mixin removed duplicate inherited executions while preserving every unique method and its assertions. The method-to-retained-witness map makes the coverage disposition auditable.
- Focused before/after runs showed large improvements in both selected suites, and the single authorized final complete-suite run confirmed that the full inventory remained present with no new failure identity.

## What did not work or remains unproven

- The selected changes did not reach the 50% full-suite target. Their local gains do not establish that the residual time is irreducible; the other-suite aggregate and host contention warrant better attribution.
- Running only changed or selected suites is not a substitute for reducing the cost of the same required complete inventory. Keep selection-policy questions distinct; `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md` covers when suites run, not how to make this suite faster.
- Same-process thread parallelism is a poor first candidate because the suites mutate ambient environment and exercise locks. Process-based parallelism has not been measured; do not label it ineffective without a bounded pilot and isolation evidence.
- A Go or Rust port, or a replacement runner, has not been measured. The observed advisory and lock-wait costs are not inherently Python-specific, so a language switch is justified only if fresh profiling shows residual interpreter, collection, or process-launch overhead dominates a representative hotspot and a parity/maintenance comparison supports the port.
- Caching, persistent worker processes, and startup reuse were not validated. Mutable repositories, manifests, environment, and lock generations make invalidation and cross-case isolation part of any proposal.

## Work scope

Re-profile the residual complete-suite cost from a reproducible, comparable inventory and distinguish fixed test-body work from Python collection/startup, subprocess startup, filesystem/Git setup, waits, and host contention. Compare at least:

- bounded process-based parallel execution of independent suites or cases, including worker count, resource contention, failure propagation, deterministic outcomes, and repeated focused isolation runs;
- a representative Go or Rust prototype or runner comparison only if measured residual costs show language-specific overhead is material; include behavioral parity, boundary coverage, portability, build/install burden, ownership, and maintenance cost;
- narrower fixture/startup reuse or safe caching with explicit invalidation and per-case mutable-state isolation;
- retaining the serial Python harness with the current fixture improvements, including the cost and uncertainty of that choice.

Keep test-selection policy separate from complete-suite runtime. Do not remove unique regression signals, weaken production safeguards, add a gate/validator/lock, or claim an option is ineffective without measurement. Any parallel path must demonstrate bounded resources, complete failure accounting, deterministic outcomes, and at least three focused repeated isolation runs. Before implementation, propose a comparable follow-up benchmark protocol and obtain the full-suite authorization required for its baseline and final comparison.

## Acceptance criteria

- A current profile attributes the largest remaining contributors and reports instrumentation overhead and host-load limitations.
- The option comparison distinguishes measured results from unmeasured hypotheses and prices coverage, reliability, portability, build/setup, and maintenance costs.
- Any proposed language port has a representative prototype with semantic parity and a measured benefit on the residual hotspot; otherwise retain the current language and record why the port is not justified.
- Any selected parallel path passes at least three repeated focused runs with the same outcomes, bounded resource use, no state leakage, and complete failure propagation.
- The resulting recommendation either identifies a safe implementation path toward the remaining target gap or records the evidence-backed stopping point while preserving all unique regression signals.
- No full-suite benchmark is run until a follow-up plan or explicit operator direction authorizes its bounded baseline/final runs.

## Scope boundary

This follow-up begins from the already accepted 44.10% result and targets only the residual test-suite runtime. It does not reopen the completed fixture/mixin changes, change which repositories require full-suite validation, or authorize a language rewrite by itself.
