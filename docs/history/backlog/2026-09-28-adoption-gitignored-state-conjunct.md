Status: open
Priority: low
Workflow: backlog
Class: correctness (the adoption predicate never checks the adopted worktree's pre-existing gitignored state)
Driving force: correctness

# Provisioned-worktree adoption never checks the adopted worktree's pre-existing gitignored state

**Exact location:** `agents/skills/execute-plan/SKILL.md`, the **Provisioned-worktree adoption** paragraph's conjunct list (branch, tracked dirt, foreign claim, and input-resolvability conjuncts; no gitignored-state conjunct) and the **Transfer-in implementation** it feeds (the noclobber facts copy `test -f .ai-playbook/facts.md || cp ...` and the unconditional reviews copy `cp -R "$PRIMARY/docs/reviews/." docs/reviews/`).

## Problem

The adoption predicate verifies branch, tracked dirt, foreign claims, and input resolvability, but never the adopted worktree's pre-existing gitignored state. Two concrete hazards survive: a stale or planted facts snapshot already sitting in the worktree passes the noclobber guard untouched (the guard copies only when the file is absent, so adoption silently runs on facts bytes the primary checkout does not back), and the unconditional reviews copy overwrites newer worktree-local docs with the primary's copies (a partially surviving prior run's newer staging docs are clobbered). The prose asserts a start-empty invariant ("A worktree's gitignored directories start empty, so nothing resolves until it is copied in") whose one real violation case is exactly adoption: a dispatch-provisioned worktree is the only worktree a run enters that it did not create fresh.

## Observed versus expected

- Observed: adoption's conjunct list ends at input resolvability; the transfer-in step then runs its noclobber and unconditional copies against whatever gitignored state the adopted worktree already carries.
- Expected: adoption verifies pre-existing gitignored state, and the start-empty invariant is stated as fresh-worktree-only so the prose and the adoption predicate agree.

## Suggested fix

Add an adoption conjunct: the adopted worktree's pre-existing gitignored state (facts file, reviews directory) must be absent or byte-identical to the primary checkout's sources, standing the run down on anything else; note in the canonical section that the start-empty invariant is a fresh-worktree-only statement, with adoption as the verified exception.

## Source reference

Review round r4 of docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r4.md (staged finding set, finding F13, risk Low, deferred by the round's staged set). Capture hygiene: scan-public-hygiene --files pass (see execution log review-r4-receiving-review.log.md). Why not fixed now: the conjunct touches the adoption predicate the pins suite keys on and the transfer-in recipe, a contract change beyond this round's narrowly-scoped edit set; deferred as durable backlog per receiving-review Backlog capture.

Dedup probe: searched the open backlog corpus for "adoption gitignored", "noclobber facts", "start-empty", "pre-existing gitignored state"; nearest item is the resume re-entry arm item filed the same round (worktree re-entry routing, not adoption predicate contents); no overlap.

Origin class: self-serving
