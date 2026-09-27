# Next-execute-after-landing: interactive single-plan asks stop at one plan by default

- **Filed:** 2026-09-27
- **Origin:** operator analysis request after the churn-prevention execution turn (main 351f704f)
- **Status:** open
- **Priority:** low

## Problem

The operator's ask was "when finished, start executing <plan X>". The turn executed X end to end (worktree, review, land, archive, memory, state file) and then stopped, leaving the remaining open plans unworked. Two causes, one by design and one a real gap:

1. **By design:** the ask named exactly one plan, and every layer of the repo's discipline treats an execution ask as single-plan unless stated otherwise: the automation payloads say "pick the single highest-priority open plan", the compact-between-runs design (backlog 2026-09-27-compact-between-execution-runs-mechanism.md) wants each plan to run in a fresh context, and executing a second plan in the same session would violate that intent. Stopping after landing X was the correct reading of the ask as written.
2. **The gap:** there is no standing rule anywhere (maintenance skill, execute-plan skill, or a user-level directive) that says what an interactive session should do after landing a plan when the queue is non-empty. The discharge-parked-intents default (landed via P54) covers only *parked* dispatch intents recorded in the scheduler state; a fresh operator ask that lands a plan creates no such intent, so nothing carries "continue with the next plan" forward. Result: an interactive one-plan ask drains nothing beyond itself, while an automation payload with the same subject would also have stopped — "one by one" only ever worked across separate scheduled dispatches, never within a turn.

## Fix shape

- Pick one explicit policy and write it down:
  - (a) an interactive execution ask defaults to one plan, and the closing report lists the next-highest open plan + a ready-to-send continuation ask (cheap, no surprise consumption); or
  - (b) an interactive execution ask continues down the queue one-by-one until quota, a gate, or an empty queue, honoring the fresh-context caveat from the compact-mechanism backlog (each subsequent plan runs uncompacted in the same session).
- Whichever is chosen, add it to the maintenance skill's execution-lane section and (if (b)) to the execute-plan completion step, so a landing turn knows its own post-landing duty without re-deriving intent each time.
- The two backlog items pair: this one decides *whether* to continue; 2026-09-27-compact-between-execution-runs-mechanism.md decides *how* a continuing run gets a fresh context.

## Witness

- 2026-09-27 churn-prevention turn: plan executed and landed 351f704f; remaining open plans (review-agents corpus family, origin-class, release-skill) untouched; no pending_dispatch or parked intent recorded, so no mechanism resumed the queue.
