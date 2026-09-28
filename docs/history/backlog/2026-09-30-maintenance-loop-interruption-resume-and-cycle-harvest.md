Status: open
Priority: high
Workflow: backlog
Class: automation
Driving force: reliability; secondary automation
Origin class: witnessed-incident (2026-09-30 an interactive session running a standing investigate/author interleave directive ended after completing an ad-hoc user task instead of resuming the loop; user direction: analyze why and file the fix)

# Standing-directive loops must survive interrupting tasks, classify their lane mandate, and harvest findings every cycle

## Problem

An interactive session ran a standing user directive ("keep investigate and authoring steps interchanging in the loop") through six completed cycles, then received an interrupting user task (analyze a collision, file backlog). It completed the task, posted the closing report, and ended the turn - and did not resume the loop. The user's follow-up ("why didn't you resume the original task") surfaced the failure. Root cause, both sides:

Skill side - the continuation machinery is landing-boundary-shaped and has an interruption-shaped hole:

- The interactive continuation rule (the execution lane's one home) makes a directive "live from its utterance until the directive is withdrawn" and forbids the closing report-and-stop shape while it stands - but only at the post-landing boundary, only in the execution lane.
- The in-session authoring chaining bullet chains an authoring landing into the execution decision, and the continue-loop condition covers lane decisions while its four legs hold - neither covers returning to a loop after an ad-hoc task that is itself neither an authoring nor an execution cycle.
- The `authoring_cycle_gate` resumed-turn rule biases to stop: a continuation-summary resume finding the gate armed reports readiness and stops, and only "a real user message" starts the next cycle. An interrupting task IS a real user message, but the rule never says its completion re-opens the loop - so the conservative default (stop) wins at exactly the boundary where the directive should resume.
- Learn is wired nowhere in the maintenance loop (zero integration points); investigate is wired only through the scheduler turn's rolling prompt log duties (one investigation per turn, when the log has no ready entry) - neither lane's interactive standing-directive loop harvests findings as a per-cycle duty.

Session side - three discipline gaps that the skill amendment should make structurally impossible:

- The session todo list was rewritten to only the interrupting task's items; the loop entry vanished from the session's own working plan, so the stop looked complete.
- The memory index recorded the standing directive, but as background context - nothing in the turn procedure says "after completing an ad-hoc task, re-read the standing-directive state before ending the turn", so latest-message-wins filled the silence.
- The session never armed `authoring_cycle_gate` at cycle closeouts although the directive text gates cycles on a user-side action (the operator's /compact), which the field paragraph prescribes for pacing-directive sessions; no durable state said "loop live, N cycles done, next: investigate/author", so every resumed context had to infer the loop from chat shape.

## Observed versus expected

- Observed: interrupting task completed; closing report; turn ended; loop dead until the user noticed and re-prompted (three consecutive meta-turns about loop behavior instead of loop work).
- Expected: the interrupting task completes and the session returns to the standing directive's loop in the same turn - classifying the directive's lane mandate from its initial text (authoring loop, execution loop, or interleave), running the next cycle's learn and investigate harvest, and continuing until a leg of the continue-loop condition fails or the user withdraws the directive.

## Proposal (minimal shape, for plan authoring to refine)

1. Interruption-resume rule (new, one home beside the interactive continuation bullet, generalized to both lanes): a live standing directive survives intervening ad-hoc user tasks; completing such a task returns the session to the directive's loop in the same turn, recording `resumed-standing-directive` with the task name in the turn record. The directive stays live until explicitly withdrawn (existing wording), and the closing report-and-stop shape must not fire at an interruption boundary while it stands - the turn's completeness becomes "task done AND loop resumed-or-leg-failed", not "task done".
2. Lane-mandate classification: the session classifies its loop mandate once from the directive's initial text and records it in the state file (authoring loop / execution loop / interleave with its fixed alternation); each subsequent cycle selection follows the recorded mandate through the existing continue-loop condition, guards, and quota leg, so a fresh or compacted context re-derives the loop instead of guessing it from chat.
3. Per-cycle harvest duty (both lanes): after each completed cycle (an authoring landing or an execution landing), before the next cycle's selection, the loop runs learn over the cycle's logs and outputs (lessons harvested, duplicates refused per the learn skill's own rules) and one investigate pass over any new findings witnessed during the cycle (new backlog items filed or existing ones updated). This makes the loop self-feeding: cycle N's findings become cycle N+1's candidates. Learn gains its first maintenance integration point; the investigate wiring generalizes beyond the scheduler turn's rolling-log duty.
4. Durable loop state: a pacing-directive session arms `authoring_cycle_gate` at every cycle closeout as the field paragraph already prescribes, and the state record carries the mandate and cycle count - so the resumed-turn rule's conservative stop lands the session in a state whose readiness report names the live loop and its next step, instead of a context-only inference.

## Rejected alternatives

- Treat every user message as a potential directive replacement (today's de-facto default): rejected; it makes standing directives one-shot and re-fires the failure every time the operator interrupts with analysis or bookkeeping.
- Arm the cycle gate at interruption boundaries so the session stops until an explicit "continue": rejected; the operator already ruled loops continue without stops, and the gate would convert every ad-hoc question into a loop stall.
- Run learn/investigate only at loop exit: rejected; findings harvested at exit are discovered too late to steer the next cycle, and an interrupted session never reaches exit.

## Witnesses

- The 2026-09-30 session: six interleave cycles landed (mains `fd204c78`, `4482c023`, `a9c65bb2`, `74fae7a1`, `0f4b7cf5`, rejection `d401e19a`), then the collision-analysis turn and the duplicate-authoring filing turn each ended the session instead of resuming; the user asked "why didn't you resume the original task" and directed this filing.
- Skill text: the interactive continuation bullet (execution lane, one home), the in-session authoring chaining bullet, the continue-loop condition, the `authoring_cycle_gate` resumed-turn rule, and the rolling prompt log duties' investigate clause are the only continuation/harvest machinery; learn has no maintenance integration point.
