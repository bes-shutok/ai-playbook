# Execute-plan runtime r6 verification findings: ignored-path witness blindness (accepted limitation), done-boundary symlink escape, witness usability

Status: done
Disposition (2026-09-11): F1 deferred by the 2026-09-11 threat-model decision to docs/history/backlog/2026-09-11-deferred-malicious-worker-hardening.md (Task 2 added only the honest-drift launch record); overflow items closed by the Task 8 directory-path rejection and seeding-producer documentation; F2-F13 closed by Tasks 1, 3, 7, 11 of plan 2026-09-10-execute-plan-runtime-residuals.
Workflow: backlog
Source: docs/reviews/2026-09-10-branch-review-agent-agnostic-execute-plan-r6.md (verification round r6 of docs/plans/2026-09-09-agent-agnostic-execute-plan.md, archived at merge)

## Problem

Findings from the r6 verification panel, all valid, none fixed in the run (round budget; F1 is a design change for its own plan):

1. **F1 (`security#ignored-path-witness-blindness`, High, deferred as accepted limitation)**: both scope witnesses run `git status --porcelain --untracked-files=all` without `--ignored`, so gitignored paths are invisible; the driver's own manifest lives under gitignored `docs/tmp/`, so a deliberately malicious same-user worker could edit its policy state (widen `allowed_paths`, erase `baseline_revision`) and pass both witnesses while committing out of scope. **Why deferred, not fixed at merge**: the proper fix is structural (anchor policy state outside the witnessed tree, e.g. `~/.execute-plan/<repo-hash>/`, or verify an out-of-tree policy digest at both boundaries), which is a design change for a dedicated plan. The fence defends against same-user drift, and a same-user adversary already holds every local anchor (repo, hooks, manifest); blast radius is bounded to this workstation because main is unpushed and every push is an explicit human action. A partial drift-audit option: `--ignored=matching` with driver-owned-path exclusion (the manifest itself must be excluded from the union since the driver writes it constantly).
2. **F2 (`security#done-boundary-symlink-escape`, Medium)**: the done boundary compares committed path names only; a committed symlink at an in-scope path pointing outside the repo passes. Fix: apply the checkpoint-side escape check to committed paths (reject blob mode 120000 at allowed paths via `git ls-tree`).
3. **F3 (`quality#untracked-noise-overblocks-scope-witness`, Medium, usability priority)**: ambient untracked noise (.DS_Store, editor swaps) dead-ends the workflow non-resumably. Fix options: make the untracked branch resumable (`cleanup-required`), compare file mtime against claim launch timestamp, or a documented ignore-list.
4. **F4 (`architecture#fail-open-witness-carveout`, Medium)**: absent `baseline_revision` disables both witnesses (seeded-test convenience); fail closed for launched claims and pin a sentinel baseline in test seeds.
5. **F5 (`architecture#wrong-direction-adapter-import`, Medium)**: codex adapter imports `bounded_evidence`/`MAX_EVIDENCE_*` from the driver; move those helpers into `runtime_capabilities.py` to sever the adapter→driver edge (supersedes the unused-import half of r5 F14).
6. **F6 (`quality#retry-clamp-floor-escapes-zero-budget`, Low)**: `max(1, int(retry_budget))` grants one retry to a `retry_budget = 0` profile; use `max(0, ...)` plus a `none` retry mode.
7. **F8 (`testing#porcelain-parse-escape`, Low)**: the witness parser strips quotes but does not C-unescape; switch to `git status --porcelain -z` or a proper C-unquote.
8. **F9 (`security#path-escape-check-fails-open`, Low)**: `_path_escapes_repo` returns False on OSError; fail closed (True) or propagate to `unavailable`.
9. **F10 (`security#reconcile-path-skips-done-verification`, Low)**: factor the done-boundary verification out of `record_done` and call it from `reconcile_commit_before_checkpoint`.
10. **F11 (`testing#always-passes`, Low)**: hermeticity-test network/filesystem witnesses still do not drive the code under test; drive `continue_parent` across the patched window or drop them.
11. **F12 (`architecture#god-method-checkpoint-recorder`, Low)**: split `record_worker_checkpoint` (retry/blocked handling vs success-path commit) before landing the r5 deferred F5/F7 fixes.
12. **F13 (`simplification#shrink-done-boundary-outcome-shape`, Low)**: extract `_done_boundary_block`/`_complete_and_claim` helpers used by `record_done` and `reconcile_commit_before_checkpoint`.

Overflow (below staging bar, same backlog scope): directory-valued allowed paths never prefix-match (block tasks under an allowed directory; implement prefix matching or reject with an actionable error); empty-scope fail-closed gate lacks a documented seeding producer for per-task `allowed_paths` (document in runtime-contract.md alongside the deferred r4 F15 seeding operation).

## Location

- `scripts/execute_plan_runtime.py` (witness ~997-1100, done boundary ~692-714, checkpoint recorder ~567-657, reconcile ~1130-1151)
- `scripts/runtime_capabilities.py` (retry clamp ~347-355)
- `scripts/execute_plan_runtime_codex.py` (import line 16)
- `scripts/test_execute_plan_runtime.py` (hermeticity test ~993)
- `agents/skills/execute-plan/runtime-contract.md` (document any behavior changes)

## Suggested fix

Dedicated hardening plan for the runtime: out-of-worktree policy anchor (or policy digest) as the headline item, then the witness usability + fail-closed smalls (F2-F4, F6, F8-F10) and the structural cleans (F5, F11-F13) in one pass, then a fresh review round.

## Severity

High (F1, accepted limitation with bounded blast radius: same-user adversary outside the file-based fence's threat model; main unpushed, pushes are explicit human actions), Medium (F2-F5), Low (rest).

## Why not fixed now

Round budget exhausted (r6 was the user-authorized verification round); F1's fix is a design change inappropriate as a merge-time patch; the rest are small but each would re-open the fix-review cycle on fresh code. All recorded for the dedicated hardening plan.
