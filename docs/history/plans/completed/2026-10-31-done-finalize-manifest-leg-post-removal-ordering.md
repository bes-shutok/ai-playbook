# Plan: Align Done Finalize Identity-Mismatch Guidance

Backlog origin: docs/history/backlog/2026-10-31-done-finalize-manifest-leg-refuses-after-worktree-removal.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-31-plan-review-done-finalize-manifest-leg-post-removal-ordering-p4f3e3086-r*.md
Authoring claim: 2026-10-31-done-finalize-manifest-leg-refuses-after-worktree-removal.md (session 01a19102-3396-7662-b283-1fe0117de2f0)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- Identity mismatch: a run manifest whose schema or repository identity does not match the repository finalizing it.
- Post-removal finalization: calling the finalizer after its run worktree has already been removed.

## Why

The manifest finalizer correctly refuses a wrong schema or repository identity, but its refusal can look like corrupt manifest data. When the done lock remains held, the wrapper may then recommend rerunning the incomplete finalization, even though a post-removal identity refusal cannot succeed from the primary checkout. Aligning both messages will reduce repeat diagnosis and prevent futile retries.

## Gist & Examples

TLDR: Align the manifest refusal and wrapper retry guidance, reducing diagnosis time through efficiency.

**Before:** The manifest helper reports the expected schema and repository fingerprint without explaining the post-removal disposition. If a lock remains held, the wrapper can then advise a full retry because the manifest is incomplete.

**After:** The helper retains its identity details and explains the post-removal disposition and future ordering rule. The wrapper preserves its lock-release attempts but does not recommend a full finalize retry after this identity refusal.

**Edge cases:** Keep the identity check and non-zero refusal unchanged; leave the manifest byte-identical on every mismatch. The guidance is conditional, so a genuinely wrong schema or foreign repository still reads as an identity refusal.

## Outcome

An operator can identify the post-removal failure and follow a consistent disposition across the helper and wrapper: report the failed finalization, release locks through the existing release steps, and do not rerun finalization from the primary checkout. Future closeouts finalize before worktree removal.

- Wrong-schema and foreign-root mismatches retain their current non-zero refusal and identity details.
- The helper refusal explains that when the run worktree has already been removed, the failed finalization step must be reported and the existing lock-release steps allowed to run; do not rerun finalization from the primary checkout. It also states that future closeouts must run the done runner's `finalize` subcommand before worktree removal and cites lesson #326.
- Both mismatch cases leave their manifest bytes unchanged.

Gate delta: runtime gates, refusal classes, fences, protocol layers, schema fields, and dispatch conditions added or removed: none; the wrapper only changes its failure guidance after the existing identity refusal.

## Assumptions

- assume adjusting only the helper and wrapper failure messages is the smallest viable fix; basis: both state surfaces already identify the mismatch and lock status, so no new identity lookup or lock behavior is needed.
- assume the primary-mirror completion arm stays out of scope; basis: the prompt records no incident beyond an honest reported failure, while that arm would add root-confirmation machinery.

Decision points requiring a grill: none remain.
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**
- Diagnostic accuracy: the refusal identifies the post-removal recovery order without presenting it as the cause of every mismatch.
- State integrity: mismatch refusal remains non-zero and leaves each input manifest byte-identical.

**Done when:**
- The mismatch test requires both wrong-schema and foreign-root cases to state the post-removal disposition, future finalize-before-removal order, and lesson citation.
- The mismatch test continues to assert non-zero refusal and byte preservation for both cases.
- The wrapper test confirms an identity refusal with the done lock still held after release attempts does not recommend a full finalize retry.
- The wrapper test confirms other incomplete manifests retain full-retry advice and completed manifests retain release-only advice.
- The held-lock cases use controlled clock and lock-state inputs, independent of wall-clock delays.
- The focused done-sweep-gates and done-run-wrapper test suites pass.

**Ship when:**
- No external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 1) - refusal message in `_cmd_finalize_manifest`; all other methods are frozen
- `scripts/done_run.sh` (Task 2) - retry guidance in `cmd_finalize`; lock-release actions and other wrapper behavior are frozen

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1) - `test_legacy_manifest_rejected_with_named_mismatch`; all other tests are frozen
- `scripts/test_done_run_wrapper.py` (Task 2) - finalize wrapper output for identity refusal with a held lock; all other tests are frozen

**Plan-related extension:** implementation and review may change files not listed above only when causally related to the task or a changed contract.

**Out of scope; reject unless plan-related:**
- The identity comparison, schema contract, manifest write behavior, and lock-release algorithms; the plan changes diagnostic wording only.
- Completing finalization from mirrored primary-checkout state; no incident supports adding the required root-confirmation machinery.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
```

### Task 1: Explain the post-removal refusal disposition

Context surface: the plan's Terms, this task, and the backlog origin.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_cmd_finalize_manifest` in `scripts/done_sweep_gates_lib.py`, which owns the manifest identity-mismatch refusal.

- [x] When finalization follows worktree removal, explain that the failed finalization step must be reported and not rerun from the primary checkout; state that future closeouts must finalize before worktree removal and cite lesson #326. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the current identity details and non-zero refusal; leave each mismatched manifest byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Require both wrong-schema and foreign-root cases to include the post-removal disposition, future finalize-before-removal order, and lesson citation in `test_legacy_manifest_rejected_with_named_mismatch`. [class: IMPLEMENTATION_REQUIRED]
- [x] Continue asserting a non-zero refusal and byte-identical manifests for both mismatch cases. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused done-sweep-gates test suite and confirm it passes. [class: REPOSITORY_TEST]

### Task 2: Suppress contradictory full-retry advice

Context surface: the identity-refusal result from Task 1 and the done wrapper's held-lock/incomplete-manifest message.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_finalize` in `scripts/done_run.sh`, which owns finalization output and lock-release reporting.
- `DoneRunFinalizeTest` in `scripts/test_done_run_wrapper.py`, which owns wrapper-level finalize scenarios.

- [x] Preserve the non-zero identity-refusal result and all existing lock-release attempts. If a lock remains held, report its state without advising a full finalize retry. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep existing full-retry advice for other incomplete-manifest causes and release-only advice for completed manifests. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a wrapper test for identity refusal while the done lock remains held after release attempts; require the refusal and held done-lock state, with no full finalize retry recommendation. [class: IMPLEMENTATION_REQUIRED]
- [x] Add contrasting held-lock cases for another incomplete manifest and a completed manifest; require full-retry advice for the former and release-only advice for the latter. [class: IMPLEMENTATION_REQUIRED]
- [x] Make held-lock assertions use controlled clock and lock-state inputs so expected guidance does not depend on wall-clock delay or fixture timestamps. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused done-run-wrapper test suite and confirm it passes. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- Origin row docs/history/backlog/2026-10-31-done-finalize-manifest-leg-refuses-after-worktree-removal.md: covered by this plan (landed commit recorded in the landing message); option (a) delivered — the finalizer refusal and the wrapper held-lock guidance now name the post-removal disposition and the finalize-before-worktree-removal ordering rule citing lesson #326; option (b) (primary-mirror completion arm) explicitly out of scope per the plan's Assumptions. The row is deleted in the same landing change per the covered-origin rule; the completed plan twin is its durable home.
- Panel residuals (FM_OUT local declaration; identity-arm unknown-completion miss path, wording tension, unpinned guard) captured as open rows docs/history/backlog/2026-10-31-done-run-fmout-local-declaration.md and docs/history/backlog/2026-10-31-done-finalize-identity-arm-residuals.md — deliberately not covered; they are deferred hardening outside the plan's diagnostic-wording scope.
