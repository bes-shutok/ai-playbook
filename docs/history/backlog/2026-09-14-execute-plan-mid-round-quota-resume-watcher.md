# Backlog: wave-boundary budget probes and a standing mid-round resume watcher

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-14
Class: budget-gate coverage gap (execute-plan and plans mirror)
Origin: execute-plan run of docs/plans/2026-09-13-budget-gate-quota-fixes.md. The r1 review panel completed 00:47 local on 2026-09-14 with roughly two hours of quota window remaining, outside the 20-minute pause threshold, so the boundary-only budget gate returned continue. The session died when the window expired mid-round, in the gate-free stretch between panel completion and the address-pass launch. The session manifest records no `budget_pause` and no resume automation was scheduled; the run sat idle ~12.8 hours until manually resumed at 13:34. This is precisely the "work dies with the session and nothing reschedules" failure the budget gate exists to prevent, and the gate's boundary-only design cannot see it.

## Problem

1. Phase 3 has gate-free stretches: panel launch, synthesis, address launch. Window death there kills the session with no pause record and no scheduled resume.
2. A continue decision only checks minutes-before-reset; it ignores the expected duration of the next worker wave. A two-hour window feeding a two-and-a-half-hour round is a predicted death that today's thresholds call "continue".
3. Even when death is not preventable, nothing schedules the resume: the pause protocol's automation-scheduling step runs only on a pause decision.

## Proposed change

Two layers, both anchored in the canonical Budget gate section of `agents/skills/execute-plan/SKILL.md` (the plans skill mirrors it):

1. **Wave-boundary probes.** Run the probe before every Phase 3 worker-wave launch: Step 3.1 panel launch and Step 3.3 address launch, not only the Step 1.5/3.5 boundaries. Record every outcome in the session manifest. On pause: the existing pause protocol, unchanged.
2. **Standing resume watcher.** At every budget-gate boundary whose decision is continue, schedule a one-shot resume automation at the binding window's reset time plus one minute, self-disarming and idempotent. Its prompt re-enters execute-plan on the plan path, verifies against the session manifest whether the run progressed after the scheduling point (fresh commit, moved HEAD, or refreshed `updated:` timestamp) and STANDS DOWN if the run progressed, a peer session resumed it, or the plan is archived; otherwise it applies the Step 0.5 resume rules (digest resume-exemption check, epoch-matched guard-flag and fired-marker clearing) and continues the loop. Each later boundary replaces the pending watcher; clean exit or archive cancels it.

This converts a mid-round death from "idle until a human notices" to "idle at most until reset plus one minute".

## Non-goals

No mid-worker interruption; workers still run to completion or die with the session. The backstop hook keeps enforcing armed flags only. Pause thresholds and the weekly secondary report-only rule are unchanged (secondary still schedules nothing).

## Acceptance criteria

1. The manifest records a probe outcome at every Phase 3 wave boundary.
2. A continue decision always leaves either no pending watcher (run exiting) or exactly one scheduled resume with stand-down rules; later boundaries replace, never stack, watchers.
3. A simulated mid-round death resumes automatically at reset plus one minute and passes the Step 0.5 resume path without re-certification (staging docs survive on disk; only the killed wave relaunches).
4. Stand-down checks (progressed, peer-resumed, archived) verified by test or fixture run.
5. Weekly secondary binding stays report-only.

## Why not fixed now

The origin run was executing the plan that ships the current gate, so its gate contract was frozen mid-run; the watcher is a protocol change to the canonical home shared with the plans skill and needs its own review cycle.

## When to act

Before the next long execute-plan run (multi-task or likely multi-round). Pairs naturally with 2026-09-14-execute-plan-parallel-review-address-workers.md in one wall-clock plan.

Related: 2026-09-14-review-runner-bounded-timeout-fallback.md (a worker timing out inside a round and the whole session dying to quota expiry are distinct failure classes needing distinct mechanisms); agents/hooks/budget-guard/ (the enforcement layer for armed flags).
