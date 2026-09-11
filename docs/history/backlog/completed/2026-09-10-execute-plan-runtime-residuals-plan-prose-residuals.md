# Execute-plan runtime residuals plan: prose and spec residuals from the authoring certification round

Status: done
Workflow: backlog
Source: docs/reviews/2026-09-10-plan-review-execute-plan-runtime-residuals-r8.md (certification round r8, ready=yes, zero blocking; findings F1-F5 plus one overflow item deferred non-blocking)

## Problem

Residuals in the plan text `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (fold before or during its execution, or as an errata pass if the plan completes first):

1. **F1 (`quality#anchor-keying-over-broad`, Medium)**: Task 2's anchor keying (repo-hash + plan-slug) claims "parallel sessions never share an anchor", but two sessions on the SAME plan slug share the anchor file, and the cross-talk witness only exercises different slugs, so it cannot discriminate; the failure mode is fail-closed (a spurious policy-anchor-mismatch dead-end), not a security hole. Sharpen the keying (for example adding a run identity to the key) and strengthen the witness.
2. **F2 (`consistency#count-contradiction`, Low)**: Task 3 says "eight behaviors"/"eight fixes" but its GREEN gate says "seven new witnesses" (the startup-noise witness made it eight; the GREEN line was not updated).
3. **F3 (`testing#fixture-update-incomplete`, Low)**: Task 5's `expected-runtime-ids.json` update bullet covers only the canonical-id expectation; `verify_activation` also compares per-profile fields, so a literal update fails the task's own activation witnesses. The bullet must scope the update to the full compared shape.
4. **F4 (`implementation#coupled-write-site`, Low)**: Task 4's "skip the receipt write when no profile was supplied" is coupled to the only site that persists the derived manifest owner; the task should state the owner-persistence behavior is preserved when skipping.
5. **F5 (`compatibility#in-flight-lock-format`, Low)**: Task 9 rewrites the done-lock session-file field name with no disposition for in-flight locks written in the old shape; add a migration note (old-shape locks are stale-cleaned by the operator path or accepted once).
6. **Overflow (`consistency#sweep-scope-wording`, Low)**: Task 5's wording implies the Validation `runtime-adapter:codex` sweep covers the inventory too, but it greps only `scripts/runtime_capabilities.py`; align the wording or extend the sweep.

## Location

- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (Tasks 2, 3, 4, 5, 9; Validation Notes).

## Suggested fix

Per finding as stated above; all are plan-text edits except F1, which may also add one witness and a key-derivation line to Task 2.

## Severity

Medium (F1), Low (rest). Plan-text precision only; the plan is executable as certified (r8 ready=yes, zero blocking).

## Why not fixed now

The review loop exited at its reconciliation bound: r8 is the single fresh certification round allowed after the mandatory reconcile fold, and it reported ready=yes with zero blocking. Folding these would change the digest and require a ninth round past the bound. Recorded per the backlog-capture rule.

Disposition: folded pre-execution via the rider plan; the six residuals landed as rider Tasks 1-2, and the fold target's re-certification completed 2026-09-11 (r18 ready=yes, zero blocking) after the 2026-09-11 threat-model decision moved the anchor mechanism to the deferred backlog (F1's keying text superseded by that deferral).
