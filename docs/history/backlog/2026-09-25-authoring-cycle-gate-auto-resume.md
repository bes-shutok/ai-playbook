# Backlog: auto-resume after harness auto-compaction bypasses the user /compact cycle gate

Status: open
Workflow: backlog
Source: 2026-09-25 interactive authoring session. The session directive gates each next authoring cycle on "after plan is finished and /compact is run", but after the archive-policy plan closed out, the session's context ceiling triggered a harness auto-compaction and the resumed turn went straight into the next cycle's due checks; no user /compact ran. The user asked for the root cause and a prevention item.
Severity: Low
Priority: low
Consumer urgency: Any long-running one-at-a-time authoring or execution session that relies on /compact as the user's pacing control between cycles. From inside the resumed session, a harness auto-compaction and a user-run /compact are indistinguishable (both arrive as a summary-continuation), and the harness resume instruction ("pick up the last task as if the break never happened") actively points the resumed turn at the recorded next step.
Driving force: reliability

## Problem

Three facts combine into the bypass:

1. The assistant has no compaction primitive. /compact is a user-side command; the assistant can neither run it nor withhold it. When the context ceiling is hit, the harness compacts automatically.
2. No durable state distinguishes the two continuations. The prior session's handoff lived only in prose (decision_reason text and a final chat message saying "run /compact whenever you like, and I'll start authoring the next plan"), and prose in a chat message or a JSON note field is not a machine-checked gate. The resumed turn treated the auto-compaction as satisfying the compaction leg of the directive.
3. The harness continuation instruction tells the resumed session to resume directly and pick up the last task, and the recorded next step was "re-run due checks and start the next plan", so the resumed turn began that work (due-check reads only in the witnessed case; no claim, worktree, or plan bytes were created before the user interrupted).

Net effect: the user's intended pause point between one-at-a-time cycles silently disappears whenever the context ceiling happens to fall between cycles.

## Suggested fix

1. Durable cycle-gate marker: at every authoring (or execution) closeout, write a machine-readable field such as `authoring_cycle_gate: "awaiting-user-go"` into the scheduler state file. Clear it only on an explicit user directive in a later turn.
2. Resumed-turn rule in the maintenance skill (zcode payload): a continuation-summary resume with the gate armed performs due checks plus a readiness report only; it must not start authoring or execute the next plan until a real user message clears the gate.
3. Continuation classification where possible: the auto path's continuation header states the conversation "ran out of context"; a user-initiated /compact arrives as part of a user turn. Combined with the durable gate, the conservative default is: gate armed + no new user directive = report readiness and stop.

## Why not fixed now

The witnessed cycle was explicitly authorized by the user ("start next"), so a gate would not have changed this cycle's outcome. The mechanism spans the scheduler state schema and the maintenance skill payload text and deserves its own small plan with review.

Promote: one plan under `{plans_dir}` (for example maintenance-cycle-gate-auto-resume); on completion fold disposition into that completed plan, then delete this file.

capture hygiene: scan-public-hygiene --files pass (re-run after edits).
