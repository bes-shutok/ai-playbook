# Plan: execute-plan worker liveness: wedges, stalls, done-boundary commits

Backlog origins (docs/history/backlog/): 2026-09-20-execute-plan-blocked-claim-wedge-no-driver-recovery.md (a malformed checkpoint receipt latches the claim blocked with no driver-native recovery), 2026-09-20-execute-plan-implement-worker-stall-timeout-undefined.md (implement worker stall handling undefined), 2026-09-20-execute-plan-done-boundary-forces-commits-on-verification-only-tasks.md (the done boundary forces commits on verification-only tasks). Review artifacts for this plan live at docs/reviews/2026-09-20-plan-review-execute-plan-worker-liveness-r<N>.md (prefix-glob; rounds are not enumerated here).

Execution sequencing: the mechanics plan (docs/plans/completed/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md) edits the same driver, test, and contract files and may still be in flight; this plan executes only after that run lands, and Task 1 re-derives every pin against the then-current tree before any edit.

## Terms

- Malformed receipt: a worker-result envelope that fails the checkpoint envelope checks (missing `reason_code`, non-list or blank `evidence`, unknown status, non-integer `generation`, and siblings); normalizes to the closed outcome reason `malformed-result`.
- Receipt entrypoint: a driver method that accepts a worker or adapter result envelope: `record_worker_checkpoint` (checkpoint path), the adapter-return arms of the launch path (`_launch_claimed_task`), and the adapter-return arm of the member resume path (`_resume_member_window`).
- Latch: the durable write that moves the claim and its task into `blocked` with `resume_allowed: false` (`_apply_blocked` on the checkpoint path, `_persist_blocked_claim` on the launch and resume paths) plus the `worker-blocked` history event.
- No-commit justification: the done receipt shape whose `commit_identity` is the exact literal `none` (after stripping), accepted only when the driver proves the task's worktree clean.
- Baseline revision: the `baseline_revision` git revision on a claim or group record; consumed by the done boundary witnesses (`_git_commit_is_descendant`, `_git_diff_paths`) and handed to the next group member's claim by `_advance_group_locked`.
- Stall: an implement worker launch that produces neither a return nor the required artifacts within the 20-minute wall-clock bound.
- Checkbox-marker-only diff: a working-tree diff over one tracked Markdown file whose changed lines pair one-to-one (hunk headers ignored): each removed line and its added counterpart are identical after the `- [ ]` and `- [x]` markers, so only unchecked-to-checked marker flips of pre-existing checkbox lines satisfy the shape; the shape of the Step 1.3 checkbox flip on the plan file. The driver pins no plan path (the plan path reaches the driver only at the terminal and readiness operations), so the classification is content-based: tracked Markdown, outside the claim's allowed paths, paired-line identity.

## Assumptions

- assume malformed receipts become read-only refusals (validate-before-write) instead of adding `malformed-result` to `RESUMABLE_REASONS`; basis: the origin's prevention framing (a self-inflicted malformed receipt should not convert a healthy claim into a state only an out-of-contract manual edit can undo) and the frozen `runtime_capabilities.py` surface (the batch-2 phase-1 Task 6 pin keeps it unedited); the resumable-reasons widening is rejected.
- assume the no-commit justification is the `none` receipt shape, not pinning checkbox-flip commits as the per-task commit for verification-only tasks; basis: the origin names manufactured checkbox-flip commits as history pollution that conflates verification passed with content changed.
- assume HEAD substitutes for the `none` identity wherever a revision is consumed downstream (the group advance baseline hand-off); basis: `_advance_group_locked` stores the done identity as the next claim's `baseline_revision`, and the done boundary witnesses only accept real revisions.
- assume the `none` path proves state with the driver's own witnesses, not the receipt's caller-asserted `clean_state` boolean alone; basis: the driver verifies what it can verify.
- assume the none witness tolerates the Step 1.3 checkbox flip: Step 1.3 flips the plan-file checkboxes before the Step 1.4 done receipt, so the tree always carries that flip at done time for verification-only tasks; basis: review r1 F1 demonstrated the strict clean-tree witness makes the none receipt unreachable for exactly the tasks Gap 3 targets; the fold tolerates only checkbox-marker-only Markdown diffs outside the claim's allowed paths and refuses every other dirty entry, and adds the review r1 F2 honesty check (HEAD must equal a non-empty claim baseline). Review r2 F1 extends the same tolerated-entry classification to every dirty-tree consumer (the checkpoint scope witness, the real-identity done tail, and reconcile_startup's dirty gate), because the flip rides uncommitted across task boundaries; review r2 F3 tightens the shape to paired-line identity, so a content rewrite can never satisfy it. The classification stays content-based (no plan-path pin): the driver receives a plan path only at the terminal and readiness operations, and the flips ride uncommitted to the run's end-of-run plan-state handling rather than gaining a mid-run commit owner.
- assume the abort wedge probe's `commit_lookup` on a recorded task identity needs no fold for `none`: a task enters `commit-pending` only through `mark_commit_pending`, which the `none` path never calls (the done handoff advances the task straight to `checkpointed` in one atomic write); basis: the transition table and `_record_done_locked`'s completion write.
- assume execution of this plan is sequenced after the mechanics plan lands on the shared surfaces; basis: the authoring task prompt caution; Task 1 re-derives every pin before any edit.

Decision points requiring a grill: malformed-receipt recovery design: standing pre-authorization in the 2026-09-20 authoring task prompt (accept all recommended options) accepts direction (a) validate-before-write over direction (b) resumable-reasons widening; affects Assumptions and Tasks 2 and 3; 2026-09-20; no-commit shape: the same standing pre-authorization accepts the `none` receipt over pinning checkbox-flip commits; affects Assumptions and Tasks 4 through 6; 2026-09-20; stall-protocol home: the same standing pre-authorization accepts mirroring the Step 3.1 timeout semantics into Step 1.2; affects Assumptions and Task 6; 2026-09-20; none-witness dirt tolerance: the same standing pre-authorization accepts tolerating checkbox-marker-only Markdown diffs outside the claim's allowed paths together with the HEAD-equals-baseline honesty check; affects Assumptions and Tasks 4 through 6; 2026-09-20; tolerance owner set and shape: the same standing pre-authorization accepts the content-based classifier (no plan-path pin, paired-line identity) taught to all four dirty-tree consumers with the flips riding to end-of-run handling; affects Assumptions and Tasks 4 through 6; 2026-09-20

## Gist & Examples

Three worker-liveness gaps, one per origin, all on the execute-plan runtime driver, its tests, and the worker contract/skill.

Gap 1: a malformed checkpoint receipt latches the claim blocked. Today a checkpoint envelope missing `reason_code` normalizes to the blocked `malformed-result` outcome and `_record_checkpoint_locked` feeds it to the same retry-or-blocked flow as a real worker failure: the claim and task latch `blocked` with `resume_allowed: false`. From there `resume` answers "no resumable blocked task" (`malformed-result` is not in `RESUMABLE_REASONS`), `reclaim` refuses until the 4-hour lease expires, and the only documented exit is a hand edit of the driver-owned manifest. The same shape exists on the launch and member-resume receipt entrypoints. Fix: a malformed envelope is refused read-only at every receipt entrypoint, before the fence and before any state write. The caller gets the same blocked `malformed-result` outcome; the manifest is untouched; the corrected re-submission succeeds immediately under the same live claim token and generation. Well-formed receipts (including real worker failures) keep the existing fence, retry, and latch semantics unchanged.

Gap 2: implement workers have no stall protocol. Step 3.1 gives review panels a 20-minute artifact timeout with focused relaunch and bounded parent-inline recovery, but Step 1.2's exit criteria assume the implement worker returns; a worker killed by a harness inactivity timeout leaves the orchestrator improvising dead waits, with no rule saying when inline recovery is legitimate. Fix: Step 1.2 carries the same operational timeout semantics with implement-specific artifacts (non-empty implement log plus task-local validation evidence), one focused relaunch, then explicitly authorized parent-inline recovery with the same log-evidence obligations as a worker.

Gap 3: the done boundary forces commits on verification-only tasks. The done receipt requires a `commit_identity` matching a HEAD-reachable commit; tasks that are read-only verification gates (drift gates, final sweeps) carry no `Commit:` line and have nothing to commit, so observed runs manufactured checkbox-flip commits to pass the boundary. Fix: the receipt accepts the documented no-commit justification (`commit_identity` exactly `none`); the driver proves the clean worktree itself with its existing worktree witness, records `none` as the completion identity, and hands the group advance the current HEAD revision as the next claim's baseline. Example: a drift-gate task whose validation command exits 0 records `commit_identity: "none"` and completes; the Step 1.3 checkbox flip on the plan file rides uncommitted, tolerated at every dirty-tree consumer (the none witness, the next task's checkpoint scope check, a later real-commit done's clean tail, and resume reconciliation), so the next task's checkpoint, its done, and any resume re-entry proceed normally, and its claim bases on HEAD exactly as if a real commit had landed.

Relationship to batch-2 phase 1: its Task 6 documented the checkpoint caller envelope and pinned in-place recovery from a latched malformed receipt. This plan removes the latch itself; the corrected-recovery pin stays, rewritten for the no-mutation semantics.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the full driver unittest suite passes; every new witness asserts the discriminating state (manifest comparisons for no-mutation pins, not outcome-shape alone)
- fail-closed bias: every new refusal path returns a closed outcome and writes nothing; positive witnesses pin the unchanged paths (well-formed failures still latch; operational launch failures still persist; real-commit refusals unchanged)
- contract-docs alignment: driver, contract, and skill describe the same semantics; each prescribed prose span appears exactly once at its home
- minimality: frozen regions untouched per the Review Scope freezes

**Done when:**

- `( cd scripts && python3 -m unittest test_execute_plan_runtime )` exits 0
- `python3 scripts/plan_readiness.py docs/plans/2026-09-20-execute-plan-worker-liveness.md` exits 0
- the hygiene scan and the em-dash gate over the authored files exit 0
- every Validation Commands pin holds at its post-task count
- the plan digest matches the final certification round's sidecar `source_digest`

**Ship when:**

- the executing session runs on a driver where the mechanics plan has landed; sequencing and peer-session coordination on the shared surfaces is human-owned and stays prose here.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `scripts/execute_plan_runtime.py` (partially in scope: `_record_checkpoint_locked`, `_worktree_scope_violation`, `_launch_claimed_task`, `_resume_member_window`, `_record_done_locked`, `_done_boundary_block`, `_advance_group_locked`, the startup reconciliation completion-recovery probe and its consumer, `_is_ambient_noise_entry`, and reconcile_startup's dirty-worktree gate; all other methods are frozen; reject any review finding that touches frozen methods and track real frozen-region bugs as separate backlog notes)

**Tests:**

- `scripts/test_execute_plan_runtime.py` (partially in scope: `CheckpointRecoveryTest`, the three `ExecutePlanRuntimeTest` launch/resume pins named by Tasks 2 and 3, and the new `CheckpointMalformedNoMutationTest` and `DoneBoundaryNoCommitTest` classes; unrelated tests frozen)

**Documentation/contract:**

- `agents/skills/execute-plan/runtime-contract.md` (partially in scope: the Checkpoint caller envelope malformed-receipt paragraph, the Transition table `done-pending` row, the new Done handoff receipt subsection; all other sections frozen)
- `agents/skills/execute-plan/SKILL.md` (partially in scope: the Step 1.2 timeout block and failure paragraph, the Sub-Agent Launch Rules Timeout bullet, the Step 1.4 pass paragraph and verification gate items 2 and 3, and Hard Gates item 4; all other sections frozen)

**Plan-related extension;** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `scripts/runtime_capabilities.py`; reason: `RESUMABLE_REASONS` is unchanged by design (direction (b) rejected) and the module is frozen.
- `agents/skills/execute-plan/subagent-prompts.md`; reason: verified its Done template already returns an explicit justified nothing to commit; recording the none receipt is the orchestrator's Step 1.4 duty.
- `docs/history/backlog/**`; reason: origin items move to `completed/` at plan completion per the lifecycle and are never edited by tasks.
- `docs/reviews/**`; reason: review artifacts, produced by the review loop, never edited by tasks.
- `README.md`; reason: verified to carry no sentences consuming the changed surfaces.
- `docs/plans/completed/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md`; reason: peer-owned executing plan, referenced read-only.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# Full hermetic driver suite (unittest, run from scripts/ so the flat imports resolve)
( cd "$REPO/scripts" && python3 -m unittest test_execute_plan_runtime ) || { echo "driver suite failed"; exit 1; }

# Mechanical readiness gate on this plan
( cd "$REPO" && python3 scripts/plan_readiness.py docs/plans/2026-09-20-execute-plan-worker-liveness.md ) || { echo "readiness gate failed"; exit 1; }

# Public hygiene scan (anchored; scanner resolves its root from cwd)
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || { echo "hygiene scan failed"; exit 1; }

# Em-dash policy over the authored prose files (plan, contract, skill)
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/plans/2026-09-20-execute-plan-worker-liveness.md agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/SKILL.md ) || { echo "em-dash gate failed"; exit 1; }

# Contract: the read-only malformed refusal stated exactly once at its home
c="$(grep -cF "fails closed as a read-only refusal" "$REPO/agents/skills/execute-plan/runtime-contract.md")"; test "$c" -eq 1 || { echo "contract read-only pin count: $c"; exit 1; }

# Contract: the none receipt definition stated exactly once
c="$(grep -cF 'exact literal `none`' "$REPO/agents/skills/execute-plan/runtime-contract.md")"; test "$c" -eq 1 || { echo "contract none pin count: $c"; exit 1; }

# Contract: the checkbox-marker-only flip tolerance stated exactly once
c="$(grep -cF 'checkbox-marker-only' "$REPO/agents/skills/execute-plan/runtime-contract.md")"; test "$c" -eq 1 || { echo "contract flip tolerance pin count: $c"; exit 1; }

# Skill: Step 1.2 carries its own implement timeout block (region-scoped to Step 1.2)
n="$(awk '/^### Step 1.2:/,/^### Step 1.2b:/' "$REPO/agents/skills/execute-plan/SKILL.md" | grep -cF '**Timeout (operational):**')"; test "$n" -eq 1 || { echo "step 1.2 timeout pin count: $n"; exit 1; }

# Skill: Step 1.4 carries the none receipt duty (region-scoped; the Hard Gate 4 amendment repeats the phrase by design)
n="$(awk '/^### Step 1.4:/,/^### Step 1.5:/' "$REPO/agents/skills/execute-plan/SKILL.md" | grep -cF 'Done handoff receipt subsection')"; test "$n" -eq 1 || { echo "step 1.4 none pointer count: $n"; exit 1; }
c="$(grep -cF 'never manufacture a checkbox-flip commit' "$REPO/agents/skills/execute-plan/SKILL.md")"; test "$c" -eq 1 || { echo "step 1.4 no-manufacture pin count: $c"; exit 1; }

# Skill: Hard Gate 4 carries the none-receipt arm exactly once
c="$(grep -cF 'verify a commit at HEAD or a recorded none receipt' "$REPO/agents/skills/execute-plan/SKILL.md")"; test "$c" -eq 1 || { echo "skill gate 4 pin count: $c"; exit 1; }

# Driver: malformed interception reads exactly four sites (checkpoint, launch raw arm, launch validated arm, resume validated arm); RED-today count is 2
c="$(grep -cF 'reason_code") == "malformed-result"' "$REPO/scripts/execute_plan_runtime.py")"; test "$c" -eq 4 || { echo "malformed interception count: $c"; exit 1; }
```

### Task 1: Phase 0 drift gate (re-derive every pin before any edit)

Files:

- (read-only gate; no file edits)

- [x] Re-derive every quoted span, identifier, count, and anchor in this plan against the current tree (`_record_checkpoint_locked`'s validate-then-fence order, `_launch_claimed_task`'s persist arms, `_resume_member_window`'s validated arm, `_record_done_locked`'s gate sequence and `commit_lookup` refusal, `_done_boundary_block`'s drift guard and clean-worktree tail, `_advance_group_locked`'s baseline hand-off sites, the startup reconciliation completion-recovery probe, `CheckpointRecoveryTest` and the three launch/resume pin names, the contract's malformed-receipt paragraph and `done-pending` row, the SKILL Step 1.2 failure paragraph and Step 3.1 Timeout wording, the `RESUMABLE_REASONS` closed set); where any pin moved, update this plan in the same task before any code edit [class: REPOSITORY_TEST]
- [x] Sequencing and stand-down check: confirm the mechanics plan run has landed on the shared surfaces and `git status --porcelain` shows none of the driver, test, contract, or SKILL files dirty from a peer session; if any is dirty or the mechanics run is still in flight, stop and report instead of editing [class: REPOSITORY_TEST]

### Task 2: Malformed checkpoint receipts never mutate state (origin: blocked-claim wedge)

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] Rewrite `CheckpointRecoveryTest#test_corrected_checkpoint_after_malformed_receipt_recovers`; given the seeded launched claim with launch record and a first checkpoint envelope missing `reason_code`, expects the blocked `malformed-result` outcome returned while the manifest stays unchanged (claim state `launched`, task status unchanged, no `blocked_receipt`, no `worker-blocked` history event, no checkpoint record), then the corrected envelope under the same token and generation expects success and `done-pending` as today; rewrite the class docstring: the latched-wedge precondition no longer exists [class: REPOSITORY_TEST]
- [x] `CheckpointMalformedNoMutationTest#test_malformed_checkpoint_with_stale_fence_refuses_read_only`; given a seeded claim whose generation differs from the manifest generation and a malformed envelope, expects the same read-only `malformed-result` refusal (not `owner-mismatch`, no mutation); basis: the interception precedes the fence [class: REPOSITORY_TEST]
- [x] `CheckpointMalformedNoMutationTest#test_well_formed_failure_receipt_still_latches`; given a well-formed envelope with a failure status and reason `runtime-error` on the live claim, expects the existing behavior unchanged: claim and task latch `blocked` with `resume_allowed: true`; guards against over-broad interception [class: REPOSITORY_TEST]
- [x] Run → expect RED: the rewritten recovery pin and the new class fail against the current latch behavior [class: REPOSITORY_TEST]
- [x] In `_record_checkpoint_locked`, immediately after `result = self.validate_adapter_result(raw)`, return `result` unchanged when `result.get("reason_code") == "malformed-result"`: a malformed envelope refuses read-only before the fence, before any claim lookup, latch, history append, or checkpoint record write; well-formed receipts keep the existing fence and retry-or-blocked flow [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime )` [class: REPOSITORY_TEST]
- [x] Commit: `fix: refuse malformed checkpoint receipts without mutating claim state` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Malformed launch and resume receipts never persist blocked claims (origin: blocked-claim wedge)

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] Rewrite `ExecutePlanRuntimeTest#test_claimed_launch_persists_malformed_scalar_as_blocked` as `test_claimed_launch_refuses_malformed_scalar_without_mutation`; given the malformed scalar adapter result on a fresh claim, expects the blocked malformed outcome returned while the claim stays `claimed`, the task stays `pending`, and no `worker-blocked` history event exists [class: REPOSITORY_TEST]
- [x] Rewrite `ExecutePlanRuntimeTest#test_claimed_launch_persists_malformed_mapping_as_blocked` as `test_claimed_launch_refuses_malformed_mapping_without_mutation`; given the malformed mapping adapter result on a fresh claim, expects the same no-mutation refusal [class: REPOSITORY_TEST]
- [x] Rewrite `ExecutePlanRuntimeTest#test_resume_non_mapping_is_persisted_as_blocked` as `test_resume_non_mapping_refuses_without_mutation`; given the non-mapping resume result, expects the blocked malformed outcome returned while the manifest is unchanged [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_operational_launch_failure_still_persists_blocked`; given an adapter that raises `TimeoutError` (the arm that manufactures the blocked outcome with explicit `resume_allowed: true`; do not build the fixture from a raw mapping, whose persisted `resume_allowed` defaults to false), expects the existing persisted blocked claim with `resume_allowed: true`; guards the persist arm against over-broad removal [class: REPOSITORY_TEST]
- [x] Run → expect RED: the three rewritten pins fail against the current persist behavior [class: REPOSITORY_TEST]
- [x] In `_launch_claimed_task`, add a read-only arm before the blocked-persist arm: when the raw adapter outcome carries `reason_code == "malformed-result"`, return it without `_persist_blocked_claim`; keep the persist arm for `runtime-policy-unavailable`, `runtime-error`, and `timeout`; when `validate_adapter_result` returns `malformed-result` for an envelope-shaped failure, return the validated outcome without persisting [class: IMPLEMENTATION_REQUIRED]
- [x] In `_resume_member_window`, return the validated outcome unchanged when its reason is `malformed-result` instead of calling `_persist_blocked_claim` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime )` [class: REPOSITORY_TEST]
- [x] Commit: `fix: refuse malformed launch and resume receipts without persisting blocked claims` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Done boundary accepts the none no-commit justification (origin: done-boundary commits)

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `DoneBoundaryNoCommitTest` setUp: hermetic git fixture mirroring the `ExecutePlanRuntimeTest` git pattern (neutralized global/system config, identity set repo-locally, an initial fixture commit) plus a committed minimal plan Markdown file, with a driver builder accepting a `commit_lookup` stub and seeding each claim's `baseline_revision` to the fixture HEAD captured at seed time [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_identity_clean_worktree_completes`; given a seeded done-pending task with fenced claim, `baseline_revision` equal to the fixture HEAD, and a done receipt whose `commit_identity` is `none`, checkbox true, clean_state true, non-empty log evidence, and a `commit_lookup` stub that fails the test if called, expects success `completed` with the exact evidence line "no-commit justification, checkbox, clean-state, and log evidence recorded", task `checkpointed` with `commit_identity` `none`, the `done-commit` history event recording `none`, and no commit lookup invoked [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_identity_tolerates_plan_checkbox_flip`; given the committed plan Markdown with one `- [ ]` line flipped to `- [x]` uncommitted before the done receipt, expects success `completed` with the same outcome shape as the clean case; pins the Step 1.3 flip tolerance [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_identity_refuses_untracked_dirt`; given an untracked file created in the fixture before the done receipt, expects blocked `commit-pending` with evidence naming the clean-state requirement, task still `done-pending`, claim still open [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_identity_refuses_tracked_content_dirt`; given a committed fixture file edited with non-checkbox content before the done receipt, expects the same blocked `commit-pending` refusal [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_identity_refuses_in_scope_dirt`; given a dirty file listed in the seeded claim's `allowed_paths`, expects the same refusal even when its diff is checkbox-marker-only [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_identity_refuses_when_head_moved_past_baseline`; given one extra commit added after the claim's `baseline_revision` was seeded, expects blocked `commit-pending` with evidence naming the moved HEAD; pins the honesty check that keeps a committing worker from masquerading as verification-only [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_real_commit_path_unchanged`; given a real identity with a `commit_lookup` stub returning False, expects the existing blocked `commit-pending` commit-not-found refusal; regression witness that the `none` branch did not swallow the lookup path [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_group_advance_none_hands_off_head_baseline`; given a two-member batch group fixture where member one completes with the `none` receipt, expects the advanced next member claim's `baseline_revision`, the `member_attempts` record's `baseline_revision` and `initialized_from`, and the returned resume action's `baseline_revision` all to equal the fixture's HEAD revision captured before the done [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_reconcile_accepts_recorded_none_identity`; given a checkpointed task recording `none` with done log evidence and its claim left launched (hand-corruption seeding; unreachable through the atomic done flow), expects the startup reconciliation completion recovery to complete without a git lookup refusal [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_completion_then_next_checkpoint_succeeds`; given a none-completed task with the plan flip riding uncommitted and a seeded next-task claim receiving a valid checkpoint envelope, expects checkpoint success with no `contract-violation` latch and no blocked claim [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_none_completion_then_real_commit_done_succeeds`; given a none-completed task with the flip riding and a following real-commit task's done receipt carrying a findable identity, expects the clean-worktree tail to tolerate the riding flip and the done to complete [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_reconcile_after_none_completion_not_blocked`; given a none-completed task with the flip riding and the next task's claim seeded launched (launch record present, task in flight), expects `reconcile_startup` to return neither `dirty-worktree` nor `cleanup-required` [class: REPOSITORY_TEST]
- [x] `DoneBoundaryNoCommitTest#test_flip_shaped_content_rewrite_refuses`; given a tracked out-of-scope Markdown diff that deletes real checklist lines and inserts fabricated checked lines (paired-line identity violated), expects the none receipt refused as `commit-pending`; pins the r2 F3 hardening [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new pins fail against the current commit-required boundary [class: REPOSITORY_TEST]
- [x] In `_record_done_locked`, branch on the stripped `commit_identity` literal `none` after the existing evidence gate, abort fence, and member fence: skip `commit_lookup`, and store `none` as the completion's `commit_identity` and in the `done-commit` history event, with the success evidence line "no-commit justification, checkbox, clean-state, and log evidence recorded" at the none return sites; keep the existing lookup refusal and evidence line for every other identity [class: IMPLEMENTATION_REQUIRED]
- [x] Extract one dirty-entry classifier helper (the `_git_worktree_dirty()` / `_git_worktree_entries()` read, the `except (OSError, RuntimeError)` arm, and the tolerated-versus-refused classification): a dirty entry inside the claim's `allowed_paths` refuses; a tracked Markdown entry outside them is tolerated only when its working-tree diff is checkbox-marker-only with paired-line identity (see Terms; the Step 1.3 flip is the sanctioned case); every other dirty entry refuses. In `_done_boundary_block`, run the `none` branch through it after the drift check, then, when the claim carries a non-empty `baseline_revision`, require the driver's HEAD revision to equal it and refuse as `commit-pending` when it moved; return `None` before the baseline guard and commit witnesses. Real identities keep the full witness chain and reuse the same classifier at the existing clean-worktree tail [class: IMPLEMENTATION_REQUIRED]
- [x] In `_worktree_scope_violation`, classify a changed path outside `allowed_paths` through the same helper: a checkbox-marker-only Markdown diff is tolerated (not `unexpected`) so the next task's checkpoint after a none completion does not persist a non-resumable `contract-violation`; in-scope changes keep the existing violation semantics [class: IMPLEMENTATION_REQUIRED]
- [x] In `reconcile_startup`'s dirty-worktree gate, exclude the tolerated entries (tracked Markdown, outside allowed paths, paired-line checkbox-marker-only flips) from the gate's dirty set before both the hoisted and per-claim arms, rather than routing them through the ambient-noise allowlist (the ambient arms are conditioned on launch-record absence and cannot carry the exemption for a launched claim), so `continue` and resume re-entry after a none completion does not hard-block on the riding flip [class: IMPLEMENTATION_REQUIRED]
- [x] In `_advance_group_locked`, compute the advance revision once before the hand-off sites: the driver's HEAD revision when the done identity is `none` (empty HEAD expects a blocked `commit-pending` outcome naming the unavailable HEAD) and the identity otherwise; use it at every `str(commit_identity)` site in the advance block (the next claim's `baseline_revision`, the `member_attempts` `baseline_revision` and `initialized_from`, and the returned resume action's `baseline_revision`) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the startup reconciliation completion recovery (the probe that reads `task.get("commit_identity")` and its consumer) to accept a recorded `none` identity with done log evidence as a valid completion without the git lookup [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime )` [class: REPOSITORY_TEST]
- [x] Commit: `feat: accept the none no-commit justification at the done boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Contract folds: read-only malformed refusal and the none receipt (origins: blocked-claim wedge, done-boundary commits)

Files:

- `agents/skills/execute-plan/runtime-contract.md`

- [x] In the Checkpoint caller envelope subsection, replace the paragraph beginning "Every field except `claim_token` is checked by" and ending "re-submission does not recover it." with: "Every field except `claim_token` is checked by `runtime_capabilities.normalize_result`; `claim_token` never reaches normalization and exists only for the driver's fence. A malformed receipt (the envelope missing or failing any check) fails closed as a read-only refusal: the normalization refusal surfaces as a blocked `malformed-result` outcome carrying the caller's checkpoint identity and the manifest generation, and the driver returns it before the claim fence, before any latch, history append, or checkpoint record write. The claim and task keep their pre-receipt state, so a malformed receipt never converts a healthy claim into a blocked state; recovery is the corrected re-submission itself, under the same live claim token and the claim's generation, with no lease expiry, claim replacement, launch-record precondition, or manifest recreation. When the envelope is well formed, the existing fence and recovery semantics apply unchanged, including the drift guard that refuses a corrected receipt on a post-launch claim without a launch record as the resumable `stale-claim` outcome by design (anti-tamper)." Keep the copy-paste JSON example that follows unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] In the Transition table, amend the `done-pending` row's last column to: "Do not launch the next task until commit (or the documented no-commit justification), checkbox, clean state, and log evidence exist." [class: IMPLEMENTATION_REQUIRED]
- [x] Add a `### Done handoff receipt` subsection immediately after the Checkpoint caller envelope subsection (before `### Readiness decision`) with: "The done handoff receipt normally carries a `commit_identity` matching a HEAD-reachable commit, verified by the driver's commit lookup and the done boundary witnesses. A task whose plan section carries no `Commit:` line (a read-only verification gate with nothing to commit) records the no-commit justification instead: `commit_identity` set to the exact literal `none` after stripping. The driver never consults the commit lookup for `none`; it proves the state itself: a dirty entry inside the claim's allowed paths refuses as `commit-pending`, a dirty entry outside them is tolerated only when its working-tree diff over that tracked Markdown file is checkbox-marker-only with paired-line identity (the Step 1.3 flip on the executing plan file is the sanctioned case; a content rewrite never satisfies the shape), every other dirty entry refuses as `commit-pending` with the clean-state evidence, and when the claim carries a baseline revision the driver requires HEAD to equal it, so a worker that committed changes cannot report `none` past its baseline. The same tolerated-entry classification applies at the checkpoint scope witness, the real-identity done tail, and the resume reconciliation dirty gate, so the riding flip never wedges the next receipt; the flips ride uncommitted and land with the run's end-of-run plan-state handling. The none completion records `none` as the task's completion identity and in the `done-commit` history event, and hands the group advance the current HEAD revision as the next claim's baseline. Checkbox-flip commits manufactured to satisfy the boundary are not part of the contract." [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the three contract pins in Validation Commands (each prescribed span present exactly once) [class: REPOSITORY_TEST]
- [x] Commit: `docs: align the runtime contract with read-only malformed refusals and the none receipt` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Skill folds: Step 1.2 implement stall protocol and Step 1.4 none receipt (origins: implement worker stall, done-boundary commits)

Files:

- `agents/skills/execute-plan/SKILL.md`

- [x] In Step 1.2, replace "If the sub-agent reports failure or tests do not pass:" with "If the sub-agent reports failure, never returns (a stall under the Timeout clause below), or tests do not pass:" [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 1.2, after the failure-recovery paragraph, add: "**Timeout (operational):** wall-clock from the Step 1.2 launch. If **20 minutes** elapse without both (a) a non-empty `<IMPLEMENT_LOG_PATH>` and (b) the task's task-local validation evidence in the returned result, treat the launch as a stall: stop the worker, verify no side effects (`git status` scoped to the task's `Files:` list, plus the session manifest lock file), preserve or append `<IMPLEMENT_LOG_PATH>`, and relaunch the Implement Task template once. Under a Step 1.2 batch launch the artifacts are the active member's implement log and member checkpoint cadence. After a second stall, bounded parent-inline recovery is explicitly authorized: the parent performs the task inline, writes `<IMPLEMENT_LOG_PATH>` itself, and satisfies the same exit criteria and log-evidence obligations as a worker. Escalate only when the recovery budget or another hard gate is reached." [class: IMPLEMENTATION_REQUIRED]
- [x] In the Sub-Agent Launch Rules Timeout bullet, after "automatically use the defined focused relaunch or bounded inline recovery path without asking for confirmation" insert "; for implement, the defined path is Step 1.2's Timeout protocol" [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 1.4, after "Pass the plan's commit line when present (e.g. `Commit: feat: ...`)," insert "and when the task section carries no `Commit:` line, expect the done workflow's justified `nothing to commit` and record the driver done receipt with `commit_identity` `none` per the runtime contract's Done handoff receipt subsection; never manufacture a checkbox-flip commit to satisfy the boundary (the none witness tolerates the Step 1.3 flip itself)" [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 1.4's verification gate, replace item 3 with: "when the done sub-agent returned a commit SHA, `git log -1 --oneline` in the repo shows that commit at HEAD (or the user-visible branch tip moved); when the none receipt was recorded, no commit check applies" [class: IMPLEMENTATION_REQUIRED]
- [x] In Hard Gates item 4, replace "verify a commit at HEAD before starting the next task" with "verify a commit at HEAD or a recorded none receipt per the runtime contract's Done handoff receipt subsection before starting the next task" [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the four skill pins in Validation Commands (each prescribed span present exactly once, including the Hard Gate 4 none-receipt arm) [class: REPOSITORY_TEST]
- [x] Commit: `docs: define the implement-worker stall protocol and the none done receipt in the skill` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Final validation sweep

Files:

- (read-only sweep; no file edits; this task is itself verification-only, so its own done receipt uses the `none` justification this plan implements)

- [x] Run the full Validation Commands block; expect exit 0 on every check [class: REPOSITORY_TEST]
- [x] Verify the plan digest: `shasum -a 256 docs/plans/2026-09-20-execute-plan-worker-liveness.md` matches the final certification round's sidecar `source_digest` [class: REPOSITORY_TEST]
