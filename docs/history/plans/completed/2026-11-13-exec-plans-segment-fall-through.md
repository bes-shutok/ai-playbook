# Plan: bind plans-scoped exec payloads to the segment-first fall-through

Backlog origin: docs/history/backlog/2026-11-13-empty-exec-candidate-cross-lane-stop-gap.md
Design input (rolling log entry, never a Backlog origin): PLAN-PROMPTS entry `exec-plans-segment-fall-through`
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-exec-plans-segment-fall-through-p18054159-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (24976387e04e9f142d129f717a411437be33e39c)
Authoring claim: exec-plans-segment-fall-through.md (session sess_3242752c-b859-41b3-8a1b-d9d76b8203cd)

## Terms

- plans segment: the slice of the exec lane's urgency-ordered candidate set surviving D1's inputs, skip classes, and holds for this session; a plan held by the agent-type affinity hold or another blocking hold is not dispatchable by this session and does not keep the segment non-empty.
- lower segments: the ready unfrozen EXEC-PROMPTS entries and the directly ad-hoc-eligible open items that follow the plans segment in the merged ordering.
- `exec-plans-segment-exhausted`: the `decision_reason` token recorded when a plans-scoped exec payload's plans segment resolves empty and the selection falls through to the lower segments.
- starvation switch: the Starvation switch paragraph in the Loop modes section (`agents/skills/maintenance/SKILL.md`) that lifts a bound mode's exclusion when that mode's own lane runs empty, recording `mode-starved-bypass:<lane>` and running the other lane's own machinery (for the switched authoring lane, D2's selection rules) under the standing caps.
- plans-scoped exec payload: an exec ask whose own wording scopes the run to plans, whatever its surface form (the witnessed payloads carry no leading count); operator one-shots included. The clause keys on the ask's wording scope, never on the `exec N plan(s)` template's literal shape.
- both-lanes-empty terminal: the sanctioned stand-down that fires only when the plans segment and the lower segments all resolve empty AND the switched authoring lane is starved per the starvation switch's own predicates in the Starvation switch paragraph of the Loop modes section (D2's selection rules, the rolling-log readiness, and the investigate leg's set - not D2's selection alone); the switch consult composes after the segment fall-through and runs before any terminal exit.

## Why

Two same-day witnessed stand-downs (the 01:51 and 03:00 WET one-shots of 2026-11-13) ended the loop dark with quota abundant, the authoring lane unoccupied, and hundreds of open backlog rows, because a plans-scoped exec payload read its own wording as excluding the lower segments entirely. The fall-through mechanism already exists in the Exec-mode selection rule; the missing piece is one clause binding scoped payloads to it plus the terminal-vocabulary condition.

## Gist & Examples

TLDR: one clause in the Exec-mode selection rule bullet makes a plans-scoped exec payload fall through when its plans segment is empty, sequences the starvation-switch consult before any terminal exit, and fires the sanctioned stand-down only when the switched lane is starved per the switch's own predicates; driving force automation (the loop keeps working without operator re-prompts).

Before: "exec plans, max 1" payload finds zero open plans, records an exit token (the witnessed sessions wrote `loop-exit:candidate-set-empty`, a non-enumerated token outside D-18's closed five-class vocabulary - the drift this plan treats), and ends the session while the execution lane's lower segments or the authoring lane still hold work. After: the same payload records `exec-plans-segment-exhausted`, falls through to the lower segments under the existing per-turn caps; when both segments are empty, the starvation switch runs the authoring lane's own machinery before any terminal exit, and the session ends dark only when that lane is starved per the switch's own predicates (D2's selection rules, the rolling-log readiness, and the investigate leg's set), recording the sanctioned `loop-exit:queue-empty` per D-18 (`docs/maintenance/operator-directives.md`).

## Outcome

A plans-scoped exec session can no longer stop dark while the execution lane still holds dispatchable non-plan work.

- The selection rule's existing fall-through clause applies explicitly to plans-scoped payloads (operator one-shots included).
- The terminal exit condition is stated in the same bullet with its recorded token, preconditioned on the starvation-switch consult, removing the interpretation drift the witnesses showed.
- The two reversal paths sequence rather than compete: the segment fall-through stays intra-lane (its own token `exec-plans-segment-exhausted`); the starvation switch composes after it with its own predicate (the exec lane's candidate set empty) and its own token (`mode-starved-bypass:<lane>`), and never fires while any segment holds work.
- The origin row's both-lanes boundary ("no tasks", not "no open plans") is implemented by the switch-consult precondition; the closing-report exit token surfaces through the existing `loop-exit:` recording duty at that terminal.

Gate delta: prose-only clause addition to one existing bullet; no new refusal class, gate, fence, protocol layer, or schema field; the standing per-turn caps, quota leg, admission consult, and starvation-switch semantics are unchanged and are explicitly named as the fell-through work's binding caps (the fell-through work is ordinary in-lane selection; the starvation switch never fired for it). Removed machinery: none.

## Assumptions

- The clause is additive to the existing `exec-plans-segment-first` sentence in the Exec-mode selection rule bullet (`agents/skills/maintenance/decisions.md`), not a rewrite of the merged-urgency default for unqualified exec.
- The closing-report/D-18 exit vocabulary needs no separate file edit: the both-lanes-empty terminal names its condition and the starvation-switch consult in the same bullet, records the existing sanctioned `loop-exit:queue-empty` class (D-18's closed enumeration, `docs/maintenance/operator-directives.md`), and never mints a new exit token; the witnessed `loop-exit:candidate-set-empty` is annotated as the non-enumerated drift artifact being treated. This implements the origin row's both-lanes terminal boundary through the consult precondition rather than a second exit token.
- The byte-budget advisory cap on `agents/skills/maintenance/decisions.md` (already over the advisory cap and within a few hundred bytes of the blocking single-read ceiling) binds this change to a same-change equivalent-bytes payment with the Task 1 bounded fallback as the sanctioned exit; the blocking ceiling is verified at execution from the gate's own constants, never from this plan's numbers.

Decision points requiring a grill: none remain.

## Standing constraints

- Skill text anti-growth rules (repository guidelines): this change prices its decisions.md growth with an equivalent-bytes deletion in the same change.
- Tool-agnostic wording: the clause describes behavior by intent, never a runtime or tool name.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a plans-scoped payload with an empty plans segment selects from the lower segments under the recorded `exec-plans-segment-exhausted` token; the terminal fires only when both segments are empty.
- consistency: the clause's wording sequences the two reversal paths (intra-lane fall-through, then the starvation switch's cross-lane reversal with its own predicate and token), never asserting an equivalence between them, with the standing caps named as binding.

**Done when:**
- `agents/skills/maintenance/decisions.md` carries the clause and the terminal condition; `bash scripts/check_maintenance_pins.sh` exits 0.
- `python3 scripts/skill_text_budget.py --check` reports `0 ceiling breach(es) (blocking)` and decisions.md's advisory PILOT OVER line does not grow relative to the pre-change bytes (99723 at r0; the same-change payment holds the delta non-positive).
- The public hygiene scan exits 0.

**Ship when:**
- the change is landed on the confirmed base branch and the state file records the run's completion.

## Review Scope

**Explicit must-fix:** none beyond the paths below.

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1)

**Tests:**
- none (prose-only change; the pins suite is the regression witness)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/SKILL.md`; reason: the starvation switch paragraph is read as-is, only reconciled by wording in decisions.md.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: segment fall-through clause, terminal vocabulary, and byte payment

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/decisions.md`

Primary class anchors:
- `check_maintenance_pins.sh` in `scripts/check_maintenance_pins.sh`

- [x] The Exec-mode selection rule bullet gains one clause binding plans-scoped exec payloads (operator one-shots included) to the existing segment-first fall-through: when the plans segment resolves empty, the selection falls through to the lower segments, recording `exec-plans-segment-exhausted` beside the sentence's existing `exec-plans-segment-first` recording (the 5h-wall arm in the Occupied-lane chaining bullet keeps its existing shape) [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the witnessed shape (a plans-scoped payload, zero open plans, ready lower segments, quota not exhausted, no lane-stop flag), expects the session to select from the lower segments under the standing per-turn caps and record `exec-plans-segment-exhausted`, never to record `loop-exit:candidate-set-empty` while lower segments hold work [class: REPOSITORY_TEST]
- [x] Terminal vocabulary: the clause conditions the terminal stand-down on a starvation-switch consult: when both segments resolve empty, the switch's reversal (`mode-starved-bypass:<lane>`, standing caps binding) runs before any terminal exit, and the stand-down fires only when the switched lane is starved per the switch's own predicates, recording `loop-exit:queue-empty` per D-18 [class: IMPLEMENTATION_REQUIRED]
- [x] The clause references the switch, never restates or re-owns it [class: IMPLEMENTATION_REQUIRED]
- [x] Reconciliation sentence: the clause states the two reversal paths as a sequence, not an identity - the segment fall-through is intra-lane (token `exec-plans-segment-exhausted`); the starvation switch composes after it with its own predicate (the exec lane's candidate set empty) and its own token, and never fires while any segment holds work [class: IMPLEMENTATION_REQUIRED]
- [x] Byte payment: the same change holds the file's post-change byte count at or below its pre-change count, deleting the equivalent bytes elsewhere in `agents/skills/maintenance/decisions.md`; the payment span is chosen at execution from the file's own redundancy (prefer grep-provably duplicative spans, re-derive against current disk bytes, avoid every pins-quoted literal and pins-counted token) and quoted in the commit message for post-hoc reviewability [class: IMPLEMENTATION_REQUIRED]
- [x] Byte-payment bounded fallback: if no equivalent-bytes span is verifiable against current disk bytes and free of pins-quoted spans, first compress the added clause's own wording to hold the delta at or below zero; if still positive, stop before commit, leave no partial edit, and file a backlog row carrying the evaluated spans for the operator [class: IMPLEMENTATION_REQUIRED]
- [x] Ceiling headroom note: the file sits near the budget gate's blocking single-read ceiling (~277 bytes of headroom), so net positive growth beyond that headroom is a blocking-gate event, not only an advisory ratchet row; the same-change payment holds the delta at or below zero regardless [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect the pins suite to pass: `bash scripts/check_maintenance_pins.sh` exit 0 (the change touches no recognition literal) [class: REPOSITORY_TEST]
- [x] Run -> expect pass: `python3 scripts/skill_text_budget.py --check` reports `0 ceiling breach(es) (blocking)` [class: REPOSITORY_TEST]
- [x] Byte-delta assert: `wc -c agents/skills/maintenance/decisions.md` before and after the edit; the post-change count is at or below the pre-change count (assert the delta before commit; the payment margin is load-bearing) [class: REPOSITORY_TEST]
- [x] Run -> expect pass, from the worktree root: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exit 0 (the scan root defaults to the cwd, so an unpinned cwd yields a false green) [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: exec selection falls through on empty plans segment` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-13-empty-exec-candidate-cross-lane-stop-gap.md: covered by this plan's executed Task 1 (the Exec-mode selection rule fall-through clause landed in commit 2bb10c9b9); the row's remaining context lives in this completed twin. Follow-up wording hygiene from the execution review's deferred findings is tracked in docs/history/backlog/2026-11-13-exec-fall-through-phase3-deferred-wording.md.
