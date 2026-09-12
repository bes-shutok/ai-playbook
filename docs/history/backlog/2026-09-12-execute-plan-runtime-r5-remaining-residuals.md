# Backlog: Execute-plan runtime residuals — r5 remaining residuals (2026-09-12)

Status: open
Origin: Phase 3 round-5 clean review of the execute-plan runtime residuals branch (staging doc `docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r5.md`; loop exit residuals, backlog-captured per receiving-review, no post-clean folds).

All findings are non-blocking against the certified tree (110+30 suites green). Listed by severity with fix directions from the review.

## Medium

1. **Success-path abort-fence asymmetry** (risk + correctness, merged): `_checkpoint_success_commit`, `_record_done_locked`, and `_reconcile_commit_locked` never consult `workflow_state`; a late success receipt/done handoff for a different live claim persists after an explicit abort, contradicting the "never persist" comments. Fix: add the abort fence at the three success sites, or document claim-scoped completion as intended and soften the comments plus reconcile `mark_commit_pending`'s global fence.
2. **Commit-pending unrecoverable wedge**: a commit-pending claim whose commit never landed (crash between `mark_commit_pending` and `git commit`) has no runtime exit: startup skips it, `continue_parent` refuses, `record_done` blocks on commit-not-found, and the r4 progression guard removed `abort()` as the kill switch. Fix directions: verify commit existence at `mark_commit_pending`, an operator-scoped reset operation, or allow abort for commit-pending claims with provably missing commits.
3. **Missing witness for the terminal-task refinement arm**: a non-success receipt arriving for a checkpointed/complete task with a live claim surfaces the raw actionable receipt (intentional, commented) — no test pins it; a reverting mutation passes the suite. Suggested witness in the r5 review log.

## Low

4. `include_terminal=False` mode of `_claim_progressed_past_receipt` has no production caller; fold into the base set and trim the test matrix.
5. The F-r4-9 pre-loop startup gate duplicates the claim loop's two filters; build one `examined` list and iterate it.
6. `_record_activation_receipt` checks token/generation before abort while `_mark_claim_launched` orders the same conditions oppositely; hoist the abort check for consistent reason codes.
7. The contract's receipt-rejection taxonomy names three cross-check classes; the code emits four (config-not-valid-TOML unlisted). Amend the sentence.
8. The `abort()` progression-guard comment omits `commit-pending` from its status list (sibling comment lists it correctly).
9. The seeding-boundary contract sentence overclaims non-empty `allowed_paths` enforcement at `create` (empty scopes seed fine and fail at envelope authorization). Reword, or enforce non-emptiness at create.

Out-of-lens observation (record, not a finding): `mark_commit_pending` permits a stale commit-pending write on an already-done-pending task.
