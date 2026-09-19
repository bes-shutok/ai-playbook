# Backlog: untested fail-closed refusal arms in the staged terminal predicate

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-18
Class: execute-plan driver test coverage, fail-closed refusal arms

## Problem

Several refusal arms of the driver's staged terminal predicate have no test
witness: the missing facts key arm of the destination clause, the
invalid-JSON sidecar arm, the unknown-stage refusal, and the shape-guard arm
(malformed plan_path/commit/checklist input). The arms exist in code and are
fail-closed, but a future refactor could silently weaken any of them and the
suite stays green.

Witnessed since this list was written (review round 4, commit 74fe9006): the
open-claims refusal and the pending-done-handoff refusal, covered by
`test_refuses_open_claim_record` and `test_refuses_pending_done_handoff`;
the two entries were removed from the unwitnessed list above.

## Location

- `scripts/execute_plan_runtime.py`: `_pre_archive_gate` (claim, handoff,
  destination key, sidecar JSON, shape arms) and `mark_terminal` (unknown
  stage).
- `scripts/test_execute_plan_runtime.py`: `ArchiveGatePreArchiveTest` and
  `TerminalFinalStageTest`.

## Suggested direction

Add one refusal fixture per arm to the existing test classes, asserting the
blocked `done-pending` status, the arm-naming evidence fragment, and the
byte-identical manifest, following the subTest pattern of
`test_refuses_missing_or_unclean_review_sidecar`.

## Severity and source

Low; staging doc
`docs/reviews/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety-code-review-r1.md`,
round 1, finding T-3.

## Why not fixed now

Deferred by the address-pass disposition of execute-plan review round 1
(non-blocking coverage expansion beyond the round's fix budget); recorded
here as the durable item.

## Addendum (review round 3, 2026-09-18)

Round 3 (finding T3-1) records three more unwitnessed arms of the same
pre-archive predicate: the missing destination directory arm (the resolved
`plans_completed_dir` does not exist on disk), the destination-escape arm
(the resolved destination escapes the repository root), and the sidecar
unsafe-path arm (a `review_sidecar` that fails the fail-closed safe-path
policy). Same disposition and same suggested direction: one refusal fixture
per arm, asserting the blocked `done-pending` status, the arm-naming
evidence fragment, and the byte-identical manifest.

Source: round 3 finding T3-1,
`docs/reviews/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety-code-review-r3.md`.
