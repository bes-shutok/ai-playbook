# Backlog: a worktree task boundary gets a plan-readiness child tool error after task checkboxes change

- **Filed:** 2026-10-18, execute-plan Task 1 done boundary
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed execution-boundary blocker
- **Class:** fix-class
- **Driving force:** reliability + simplicity
- **Skill/step:** `agents/skills/done/SKILL.md` Step 3 landing sweep; `scripts/done_sweep_gates_lib.py` `derive_plan_readiness_candidates` and `gate_plan_readiness`
- **Related backlog:** `docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md` (the stale plan-review digest after checkbox updates is shared; this row owns the additional composed-gate tool-error and exemption mismatch)

## Problem

The 2026-10-18 Task 1 boundary stopped before committing an otherwise implemented and validated task. The task completion checkboxes changed the plan bytes after review r11, so a direct `scripts/plan_readiness.py` consult correctly reported the review sidecar's `source_digest` stale. The composed done sweep reported `tool_error=1` for that plan because its child exited 1 without a final `OUTCOME` line and exposed only a traceback header. The operator record also notes that direct candidate derivation exempted the plan with a fresh `workflow_state: active` execute-plan manifest, while the composed sweep still selected it. The execution manifest was later parked as `blocked`; no gate or validator was edited.

The gate's origin is the done Step 1.5 plan-readiness check, introduced in `fe61c8471` with a 24-hour active-execute-plan manifest exemption. The exemption is meant to avoid re-gating a live plan while preserving review-digest checks for ordinary plan deliverables. A later plan explicitly kept that exemption after review rounds found it compatible with checkbox-drift and resume handling (`docs/history/plans/completed/2026-09-04-done-deliverables-log-dedupe-and-anchors.md`, invariant 8). The current witness leaves two questions unresolved: why the composed invocation did not match the direct active-manifest derivation, and why its validator child emitted no final outcome.

## Expected

The same run inputs should produce the same plan-readiness candidate and exemption decision in direct derivation and the composed done sweep. A candidate validator crash should preserve enough concrete diagnostic output to identify the exception and must not be confused with a modeled stale-review failure. A task boundary should resume through the documented fresh-review path when plan bytes changed; it must not bypass review-digest binding.

## Evidence

- Plan and task: `docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md`, Task 1; plan digest at the parked boundary: `db2d2f98e470414419e04c5e6763183d152900d5109eb3776e48184420c21963`.
- Done-boundary result recorded in `docs/tmp/execute-plan/2026-10-17-archive-ceremony-review-evidence-mismatch/task-1-review.log.md`: `plan-readiness` had `passed=0`, `exempted=0`, `tool_error=1`; the child had no final `OUTCOME` line. The same log records the direct active-manifest derivation mismatch.
- Direct validator result in the task worktree: `readiness FAILED: sidecar source_digest is stale (plan bytes changed after review r11)` followed by `OUTCOME: fail`.
- The current gate still derives the active-manifest exemption in `_manifest_exempts` and runs `plan_readiness.py` as a child in `gate_plan_readiness` (`scripts/done_sweep_gates_lib.py`). Its exemption logic dates to `fe61c8471`; the later preservation decision is recorded in the completed plan linked above.
- Related witness: `docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md` already identifies fresh review after checkbox edits as the safe response to stale plan digests; this row tracks the additional composed-gate inconsistency and child crash, not the ordinary stale-digest refusal.

## Origin assessment and recommended direction

Keep the review-digest integrity check: this session reproduced a real stale sidecar after plan bytes changed, and the existing digest-handoff backlog already records fresh review as the supported response. Do not remove the plan-readiness gate based on this one failure. First re-derive the candidate and manifest inputs through the composed runner, capture the validator's complete child error, and compare that path with the direct derivation. If the mismatch is confirmed, simplify the active-plan exemption to one ownership-scoped derivation path while retaining the digest check for plans that remain candidates. Remove the exemption only if the originating incident and current consumers show it has no independent protective value.

Alternatives: removing all readiness validation is rejected because it would admit the stale review digest witnessed here; keeping the current behavior without diagnosing the disagreement is rejected because it stranded the task and collapsed the child error to an incomplete traceback; a fresh plan review followed by one bounded boundary retry is the current continuation path, not a durable fix. This item adds no gate, validator, lock, ledger, or required ceremony.

## Dedup probe

Searched open backlog items for plan-readiness, stale review digests, and done-boundary failures. The 2026-10-10 plan-digest handoff row owns the general checkbox-to-review digest mismatch and already prescribes fresh review. It does not record the 2026-10-18 composed-gate exemption disagreement or child `tool_error`, so this row is a distinct failure mode with a shared related origin.
