# Backlog: cap-closure decode scoping states a declaration-only trigger while step 6's date-gated arms also need the decode

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: medium
Workflow: backlog
Class: certification machinery
Driving force: correctness

## Problem

Task 1 of the certification-machinery plan (as folded at r6) scopes the shared plan-bytes decode: "the probe call decodes and passes `plan_text` only when the declaration is present, and step 6 reuses the same decode along its existing date-gated arms instead of re-decoding". The only stated execution trigger is declaration presence, but step 6's date-gated decode arms fire independent of the declaration (scripts/plan_readiness.py:1299-1306, condition `trailer_gated or scope_gated or ownership_gated`). An implementation reading the first clause literally leaves the declaration-free, date-gated, undecodable-bytes path with an unbound variable (a new traceback path the sentence claims is avoided), and the sibling parenthetical "the undecodable-bytes reason fires only when the declaration routes the probe at the bytes" is false as a general claim. The preserved path also has no in-suite witness: every CapClosureReadinessTest arm is pinned below the fences except the one modern arm, which is declaration-present.

## Observed versus expected

- Observed: r7 risk worker finding (Medium, non-blocking); the union-of-triggers reading is implied but never stated.
- Expected: the decode sentence states the union explicitly (decode runs when the declaration is present OR any step 6-8 date guard fires; the original step-6 decode block is removed; the date-guard case returns the existing gated-checks cannot-read reason), the parenthetical is reworded to "when the declaration routes the probe at the bytes, and, as today, along the date-gated arms", and optionally a fifth guard arm (declaration-absent, gated date, undecodable bytes, expecting the cannot-read reason) pins the preserved path in-suite.

## Suggested fix

When the certification-machinery plan executes or in a follow-up plan, apply the wording fix to Task 1's decode sentence and add the fifth guard arm; if the plan has already landed, amend the validator's docstring comment to state the union trigger and add the unittest arm to scripts/test_plan_readiness.py.

## Environment

r7 execution-time re-cert round, 2026-09-27, execution worktree of the certification-machinery contract-collisions plan; deferred per the backlog-deferral default (clean round, zero blocking).
