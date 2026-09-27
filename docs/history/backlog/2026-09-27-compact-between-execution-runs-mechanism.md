# Compact-between-execution-runs mechanism is unimplementable as worded

- **Filed:** 2026-09-27
- **Origin:** operator analysis request after the P65 one-by-one execution run (automation-9912debc, squash b3971208)
- **Status:** open
- **Priority:** medium

## Problem

The one-by-one execution payload says "after each plan's execution completes, run /compact before starting the next plan, so each run starts compacted." Two independent reasons made this impossible in the witnessed run:

1. **`/compact` is not callable from inside a session.** It is a host CLI command available to the interactive user (or a slash command dispatched into a fresh turn). An agent executing a plan mid-run has no tool that triggers compaction; the harness compacts automatically only when the context window fills. The P65 run in fact ended by *running out of context* and being continued by a summary — the exact outcome the instruction was trying to prevent.
2. **No continuation mechanism existed even if compaction had worked.** The one-shot fired once; the payload said "pick the single highest-priority open plan" (singular) and "if the queue is empty, report that and stop." Nothing re-armed a follow-up dispatch, and `CronCreate` is refused inside an automation-bound session (automation-lane cap, re-confirmed 2026-09-15), so the run could not schedule its own successor. Executing a second plan in the same uncompacted session would have violated the compact-between-runs intent even harder.

Net effect: "one by one with /compact between runs" degenerated to "one plan per automation dispatch, with the dispatch itself being the compaction boundary" — which is the correct mental model, but nothing in the payload or the maintenance skill states it.

## Fix shape

- Reword the one-by-one payload template: replace "run /compact before starting the next plan" with "end the run after each plan; each scheduled dispatch starts in a fresh, compacted context" — the dispatch boundary *is* the compaction boundary.
- If multi-plan sequential execution per dispatch is wanted, say so explicitly ("execute up to N plans in this run") and accept no compaction between them, or move the sequencing to a recurring parent that fires per plan.
- Optionally add a note to the maintenance skill's execution-lane section: `/compact` is operator-only; agent runs achieve a fresh context by ending, not by compacting.
- Consider a payload-guard in future scheduled-work authoring: never instruct a session to invoke host CLI slash commands.

## Witness

- automation-9912debc run 2026-09-26 23:07 local: P65 executed, context exhausted mid-closeout, session continued via summary; no second plan attempted.
- 2026-09-27 interactive runs (origin-class plan, then run-start-marker plan): the operator explicitly directed "continue with executions one by one" in-session, yet the executing session still stopped after one landed plan per turn and reported the queue, because the one-plan-per-dispatch boundary is the only stopping rule the maintenance skill states. In an interactive session with an explicit continuation directive this is pure lost throughput: context was nowhere near exhausted, all gates were green, and the next plan was known. The skill needs a rule that an explicit operator directive to continue sequentially overrides the per-dispatch boundary until the operator stops the session or the context genuinely runs low - and that the closing "report and stop" shape must not fire while a continuation directive is live.

## Fix shape (updated 2026-09-27)

- Reword the one-by-one payload template: replace "run /compact before starting the next plan" with "end the run after each plan; each scheduled dispatch starts in a fresh, compacted context" — the dispatch boundary *is* the compaction boundary.
- If multi-plan sequential execution per dispatch is wanted, say so explicitly ("execute up to N plans in this run") and accept no compaction between them, or move the sequencing to a recurring parent that fires per plan.
- Optionally add a note to the maintenance skill's execution-lane section: `/compact` is operator-only; agent runs achieve a fresh context by ending, not by compacting.
- Consider a payload-guard in future scheduled-work authoring: never instruct a session to invoke host CLI slash commands.
- NEW: add an interactive-continuation rule to the maintenance skill's execution lane — when the operator's live directive says to continue executing plans sequentially in-session, the session proceeds to the next digest-intact open plan immediately after landing the previous one (re-running the readiness gate and scheduler-state check per plan), ending only when the directive is withdrawn, the queue is empty, or the context window genuinely runs low; the per-dispatch boundary applies only to automation-born sessions.
