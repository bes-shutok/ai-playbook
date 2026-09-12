# Execute-plan runtime r5 deferred findings: F5-F17 plus overflow items

Status: done
Disposition (2026-09-11): F9 verify-closed (Task 12 quotePath pin, 5 invocation-form matches, no re-fix); F14 closed by the Task 7 import-edge severance (the unused `MAX_EVIDENCE_BYTES` import removed by deletion); all other findings and overflow items closed by Tasks 1, 4, 6, 7, 9, 10, 11 of plan 2026-09-10-execute-plan-runtime-residuals.
Workflow: backlog
Source: docs/reviews/2026-09-09-branch-review-agent-agnostic-execute-plan-r5.md (final review round r5 of 5), findings F5-F17 (12 findings, Medium/Low, non-blocking or non-fix-family) plus the 5 recorded overflow items; deferred from the r5 receiving-review pass of docs/plans/2026-09-09-agent-agnostic-execute-plan.md

## Problem

1. **F5 (`architecture#static-attempt-identity`, Medium)**: the retry path records every failed attempt under the fixed key `{identity}#attempt-initial`, so with the default bounded budget of 2 the second consecutive error overwrites the first attempt's durable checkpoint record; reconciliation sees one attempt where two occurred.
2. **F6 (`architecture#owner-derivation-outside-lock`, Medium)**: `RuntimeDriver.__init__` reads `manifest.get("owner")` from an unlocked snapshot; concurrent first construction of two drivers on a fresh manifest yields divergent owner identities and the loser fails every owner fence for its lifetime.
3. **F7 (`security#manifest-lock-held-across-adapter-io`, Medium)**: `resume` invokes `adapter.resume(...)` (up to the 300s deadline) while holding the non-blocking flock, and the rewrite-retry path in `record_worker_checkpoint` launches the adapter inside the lock; concurrent driver processes get spurious blocked/stale-claim outcomes for the whole adapter window.
4. **F8 (`implementation#durable-receipt-rewrite-on-open`, Low)**: `_refresh_capability_receipts` runs in `__init__` and unconditionally overwrites the three receipt fields from the (possibly absent) profile, so a profile-less CLI invocation silently downgrades durable capability receipts to unsupported.
5. **F9 (`quality#git-path-quoting-witness-mismatch`, Low)**: fixed in this pass as part of F1/F4 (witness invocations now pass `-c core.quotePath=false`); retained here only as a cross-check that the fix lands in the post-cap verification round. Do not re-fix; verify and close.
6. **F10 (`testing#always-passes`, Low)**: the patched-socket and outside.txt assertions in `test_runtime_replay_is_hermetic_to_fixture_root` never intersect the code under test, so they cannot fail; only the authorize_action assertions guard anything.
7. **F11 (`testing#dangerous-negative-witness`, Low)**: `test_timeout_cleanup_treats_recycled_pid_identity_as_exited` passes `os.getpid()` as the recycled PID, so a regressed identity guard would SIGKILL the test runner instead of failing an assertion.
8. **F14 (`simplification#delete`, Low)**: `MAX_EVIDENCE_BYTES` is imported but never used in `scripts/execute_plan_runtime_codex.py`.
9. **F15 (`architecture#duplicated-contract-prose`, Low)**: the "Runtime-neutral execution contract" section of `agents/skills/execute-plan/SKILL.md` restates runtime-contract.md at length without linking it; every contract edit must hand-mirror both copies.
10. **F16 (`security#pid-identity-checked-after-sigkill`, Low)**: the timeout kill loop sends SIGKILL unconditionally and consults `_pid_identity_matches` only afterwards; a PID recycled inside the sub-second poll window is killed before the identity check runs.
11. **F17 (`security#forgeable-approval-receipt`, Low)**: `load_approval_receipt` validates only JSON shape and the literal `approval == "verified"`, with no binding to the host's real approval configuration and no permission requirement; any local process that can write a file can mint a verified receipt.
12. **Overflow items (5, all Low, verified)**:
    - `quality#dead-validation-helper-divergence` at `scripts/done-lock.sh:59`: `read_label` is dead code while the used arg loops diverge from it (missing `--label` value exits cryptically; empty label accepted).
    - `simplification#shrink` at `scripts/done-lock.sh:439`: `try_acquire` contains two near-identical ~18-line acquisition bodies; extract one helper.
    - `security#dead-code-sources-untrusted-session-file` at `scripts/done-lock.sh:375`: `load_lock_session` sources a repo-controlled file (arbitrary code execution if ever wired in); delete it, keep the no-sourcing invariant.
    - `simplification#delete` at `scripts/execute_plan_runtime.py:681` (record_done): dead commit-pending transition written then overwritten before any save; collapse to one update, leave commit-pending owned by `mark_commit_pending`.
    - `architecture#policy-query-storage-io` at `scripts/execute_plan_runtime.py:490`: `authorize_action` re-reads the manifest per action (N+1 storage I/O from a policy predicate); pass the already-read generation through.

## Location

- `scripts/execute_plan_runtime.py` (F5 ~line 590 retry record, F6 ~line 317 constructor, F7 ~line 862 resume/retry locking, F8 ~line 336 receipts, overflow dead transition ~line 681, overflow N+1 ~line 490)
- `scripts/runtime_capabilities.py` (F17 ~line 258 `load_approval_receipt`)
- `scripts/execute_plan_runtime_codex.py` (F14 ~line 16, F16 ~line 347)
- `scripts/test_execute_plan_runtime.py` (F10 ~line 993), `scripts/test_execute_plan_runtime_codex.py` (F11 ~line 174)
- `agents/skills/execute-plan/SKILL.md` (F15 ~line 44)
- `scripts/done-lock.sh` (overflow rows 1-3)

## Suggested fix

Per finding, as stated in the r5 staging doc comments: derive the attempt ordinal for F5 (or drop the attempt-suffixed entry in favor of the per-attempt history event); move owner resolution inside the locked `_refresh_capability_receipts` for F6; mirror the launch pattern (state transitions locked, adapter I/O unlocked) for F7; skip or merge the receipt write when no profile was supplied for F8; verify-and-close F9 against the landed quotePath fix; drive `continue_parent` across the patched-socket window or drop the decorative witnesses for F10; use a disposable child process for the recycled-PID test for F11; drop the dead import for F14; shrink the SKILL.md section to a summary plus an explicit read-first pointer to runtime-contract.md for F15; move (or duplicate) the identity check immediately before `os.kill(..., SIGKILL)` for F16; cross-check the referenced codex config policy, require owner-only permissions, and document the receipt as operator-attested for F17; apply the five overflow cleanups as stated.

## Severity

Medium (F5, F6, F7), Low (F8, F9, F10, F11, F14, F15, F16, F17, all five overflow items). None blocking after the F1-F4 fail-closed fixes landed in this pass; F9 is expected already fixed.

## Why not fixed now

Round cap reached: this was the final review round (5 of 5) of the execute-plan Phase 3 run, and the review budget is exhausted; per the orchestrator's fix scope, only the blocking findings (F1-F3) plus the F4 fail-open witness family were fixed inline with minimal additive diffs, and these fixes will not be re-reviewed within this run. Remaining findings are reserved for the post-cap verification round. Deferred by the r5 address-review sub-agent under execute-plan Phase 3 fix-risk triage.
