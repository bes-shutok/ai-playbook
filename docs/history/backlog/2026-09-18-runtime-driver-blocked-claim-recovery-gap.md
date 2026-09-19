# Backlog: runtime driver offers no pre-lease recovery from a malformed checkpoint that latches a claim blocked

Status: open
Priority: high

Workflow: backlog
Source: learn Step 1.8 skill-usage capture, 2026-09-18 (execute-plan run of docs/plans/2026-09-16-learn-done-workflow-updates.md; staging docs under docs/reviews/2026-09-16-learn-done-workflow-updates-code-review-r1-r5).

## Observed vs expected

Observed: the orchestrator recorded a Task 1 checkpoint with an incomplete worker-result envelope (missing `reason_code`). The driver (`scripts/execute_plan_runtime.py`, `record_worker_checkpoint` / `normalize_result`) persisted the malformed result as a blocked receipt with `resume_allowed: false` on both the claim and the task. Every sanctioned recovery path then refused for the full `CLAIM_LEASE_SECONDS` (4h): `checkpoint` re-reads the live claim and fails owner/shape fencing, `resume` reports "no resumable blocked task" (resume_allowed false), and `reclaim` requires lease expiry. The work was already done and verified; the state machine wedged on one bookkeeping call. Recovery required recreating the session-private machine manifest from scratch and redoing the boundary sequence (honest but wasteful, and indistinguishable from tampering had peers been watching).

Expected: either (a) a malformed-result receipt from the claim's own owner is retryable in place (the result never launched anything; a corrected re-submission under the same token should be accepted), or (b) the CLI documents the exact worker-result envelope (keys `checkpoint_identity`, `status`, `reason_code`, `action_scope`, `generation`, `claim_token`, `evidence` list; where `generation` is the claim generation, not the workflow generation) so orchestrators following the skill text alone cannot produce the latch in the first place. Currently the envelope schema lives only in `runtime_capabilities.normalize_result` and the selftest.

## Suspected root area

`execute-plan` runtime-contract and `scripts/execute_plan_runtime.py` (`record_worker_checkpoint` retry/blocked accounting; CLI `--help` documents only flags, not the input schema).

## Environment context

Runtime: zcode agent session, one-shot shell calls; repo ai-playbook at main a4ffa82f; vendored copy equals repo copy (symlinked runtime). Date 2026-09-18.

## Completion evidence (for the fixing plan)

A test where a first checkpoint with a missing `reason_code` is followed by a corrected checkpoint under the same claim token succeeds without lease expiry (and without manifest recreation); or the CLI `--help`/runtime-contract carries a copy-paste checkpoint envelope example that passes a fresh run end-to-end.
