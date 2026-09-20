# Plan: Loop-guard one-recorded-mutation carve-out (dark-loop prevention)

External gate: scheduler-maintenance-loop-quality-hygiene

Backlog origin (scope of record): `docs/history/backlog/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md` (priority high).

Coordination (binding): this plan edits the same `agents/skills/maintenance/zcode.md` dispatch-discipline bullet as the in-flight scheduler-leftovers hygiene plan (`docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md`, the emission-suppression fix). The gate slug above names that plan: while its plan file is absent from the open top-level survey the gate reads unsatisfied and the scheduler skips this plan, so the two never start blind to each other. Every task below is additive to that plan's prescribed additions in the shared bullet (the suppression rule sentences and the launchd resume-carrier bullet; the audit marker lives in the child classification markers bullet, not this one): no task rewrites or deletes them. The executing child's PRE-STEP re-certification and the union-merge precedent remain the collision backstop at landing.

External-gate strand triage (r1 F1, explicitly triaged, not fixed): the landed slug-form satisfaction rule (maintenance SKILL.md Step 1; normative definition in docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md) reads the gate SATISFIED while an open top-level plan or open backlog item other than the declaring plan carries the slug, and UNSATISFIED once the hygiene plan executes and archives (the completed/ subdirectory is outside the match set), with no self-heal. The line is kept anyway because the authoring prompt's coordination clause mandates it verbatim. Present state (updated at the r3 fold, 2026-09-21 evening): the hygiene plan's file landed on main (commit 82f5edff, the leftovers trio), so the gate reads SATISFIED today and this plan dispatches under the normal rules; the strand window is now only the timing case where this family is still open after the hygiene plan has executed and archived. The expected dispatch order still runs the family first (the family's basenames sort before the hygiene plan's, the execution lane serializes the executions), so a delayed family is the only exposure; the mechanism's designed fate for an unsatisfiable gate is D4's park proposal after 7 unchanged days, which forces the human decision instead of a silent loss. This triage is recorded in the authoring session's notes and final report; flipping the line to date form is a one-line human edit if Andrey prefers the date semantics.

Shared-surface inventory (r2 F3, corrected): the hygiene plan's Task 7 edits this same dispatch-discipline bullet (the suppression rule sentences) and its launchd resume-carrier bullet lands in the same region; its audit marker, however, edits the child classification markers bullet (a different bullet), not this one. The pins suite is a second shared surface: the hygiene plan's Task 6 edits the same suite this plan's Task 3 edits (its toolset-precheck block and audit-lane pins beside this plan's carve-out pins); both are additive pin blocks in different sections, and the union-merge precedent covers the file.

## Terms

- **Guard signature**: the selection-loop guard's trigger condition as the overlay's dispatch-discipline bullet states it today: a session notices itself repeating a read-only listing without advancing to the mutating step (two listings, no mutating step between them).
- **State-first decision write**: a durable record of the decided mutation in `.ai-playbook/scheduler-state.json` (a sanctioned targeted field edit) that preceded the first listing of the turn; the decision-first discipline the dispatch-discipline bullet already prescribes for multi-call dispatches.
- **Decision ownership**: the emitting session's qualifying relation to the recorded decision: the record is the session's own decision-first write, or the pending record the session takes as its own under the re-arm duty's record-taking rule.
- **Sole restorer**: the escalation-writing session that is the only actor able to restore the loop (no ENABLED recognition match and no live pending child at write time).
- **Dark loop**: the loop state where no scheduled actor exists to read an escalation and the parent is absent, so recovery waits on an interactive touch.

## Assumptions

- assume the guard signature stays the overlay's existing wording (two listings, no mutating step between them) and the carve-out adds no second signature; basis: the dispatch-discipline bullet's landed text, verified 2026-09-21.
- assume "recorded durably" means a state-file write through one of the sanctioned writer classes (for example the decision-first Bash state edit the bullet already prescribes); basis: the decision-first discipline paragraph and the State file section's sanctioned writer classes.
- assume the operator override is documentation-level (the overlay states it; no enforcement hook is added); basis: origin item 2 ("the overlay states explicitly"), which asks for the escape to be written down so a session offers it.
- assume the dark-case recovery carrier is an escalation-note format duty at the overlay level, not a new state field; basis: the origin's own pointer that the `pending_rearm` field is proposed by the sibling durable-carrier item, which is taken by the in-flight state-durability plan (scope boundary), so this plan prescribes only what the note must name.
- assume the byte-identical re-arm parity pin stays satisfied by applying the identical addition to both blueprint paragraphs in the same commit; basis: the pins suite's parity check (`paras[0] != paras[1]` fails the suite).
- assume the carve-out's decision-ownership rule is needed because the witnessed suppression case spans two sessions (the deciding turn records, a successor session may emit); basis: r1 F2's reading of the re-arm duty's record-taking rule; the strict same-session reading would void the blueprint references.

Decision points requiring a grill: carve-out scope (dispatch-discipline bullet plus recipe re-arm hygiene, not only one of them): resolved by the task prompt's standing pre-authorization, accept all recommended options without asking, 2026-09-21 authoring prompt; affected section: Task 1. Operator-override enforcement depth (prose-only, no hook): same standing pre-authorization receipt; affected section: Task 1. Dark-case carrier form (note-format duty, no new state field): same standing pre-authorization receipt plus the scope boundary recorded in Assumptions; affected section: Task 1. Decision-ownership rule (own record or the record taken as own): same standing pre-authorization receipt; affected section: Task 1 and Task 2. Drill depth (recorded walk-through of a fixture state, no live automation calls): same standing pre-authorization receipt; affected section: Task 4. External-gate strand (keep the mandated slug line with the triage paragraph above rather than flipping to date form): same standing pre-authorization receipt plus the binding coordination clause; affected section: Coordination.

## Gist & Examples

The maintenance loop's selection-loop guard is a circuit breaker with a flaw: after it fires, it forbids every automation-primitive call, including the one mutating call that would terminate the loop and restore liveness. In the common case (a parent present, a fresh retry two hours later) the cost is one wasted turn. In the re-arm case the actor IS the only restorer, so "safe stop" and "loop goes dark" are the same event, and no scheduled carrier exists to read the escalation note. That is not hypothetical: on 2026-09-21 the authoring-resume one-shot (automation-2fd9c94e) recorded its re-arm decision state-first, emitted four CronList calls instead of the decided CronCreate, honored the guard's stand-down, wrote the escalation note, and left the loop dark until an interactive touch - the second dark night in two days.

**Before (today)**: a session with a state-first recorded decision trips the guard and must stop touching automation primitives entirely. The decided mutation is never emitted; if the session was the sole restorer, the loop stays dark.

**After (this plan)**: the same session, holding the same state-first recorded decision (its own, or the pending record it takes as its own), may emit exactly ONE mutating call implementing that recorded decision, then stops touching automation primitives regardless of the call's outcome. A refusal after that single call takes the existing escalation paths unchanged. One recorded mutation is not a repeated listing, so the action-selection regress the guard bounds cannot reopen: the bound moves from "zero mutations after the signature" to "exactly the one recorded mutation, then stop". A decision that lived only in chat narration still qualifies for nothing - the state-first write is the carve-out's gate, which keeps the decision-first rule load-bearing.

Edge cases this design fixes:

- The operator override becomes written law: the guard binds unattended sessions protecting themselves from their own pathology; an explicit user instruction to proceed outranks it, and a session reporting a guard stand-down must offer the override instead of only reporting blocked.
- The dark case gets a mechanical handle: when the escalation note is written by the sole restorer, the note must name the recovery (the assembled payload copy path when one exists, the recipe pointer, the observed condition) so a rearm-on-touch session executes recovery instead of re-deriving it.

## Design Invariants (CR Guard)

- **Additive to the hygiene plan's region**: no prescribed edit rewrites or deletes the dispatch-discipline bullet text the hygiene plan adds (the suppression rule sentences and the launchd resume-carrier bullet; the audit marker lives in the child classification markers bullet, not this one); each insertion appends after the existing stand-down sentence and its additions.
- **The one-call bound is absolute**: after the single mutating call, the session stops touching automation primitives regardless of outcome; a chat-narrated decision never qualifies; the state-first write is the gate, and the emitting session must own the recorded decision.
- **Never-dark behavior preserved**: the carve-out only permits the terminating mutation before the existing stand-down; every escalation path (rearm_note, memory note, park) is unchanged.
- **Blueprint byte parity**: the two FIRST ACTION re-arm paragraphs stay byte-identical; the carve-out reference lands in both in the same commit.
- **No em-dashes in prescribed text**: the exact-needle greps in Validation Commands are the em-dash guard for the insertions (the needles themselves carry none, so a faithful insertion cannot introduce one); the edited files carry legacy em-dashes in frozen regions (measured 2026-09-21: one in the zcode.md Context measurement primitive's Compaction bullet, one in prompt-templates.md's deviation list), so no whole-file sweep is prescribed.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the carve-out requires all conjuncts (the guard signature AND a state-first decision write preceding the first listing AND decision ownership); the validation greps pin each new conjunct as its own dedicated needle, and the guard-signature restatement span carries its own gate.
- safety (never-dark): post-single-call refusals route to the existing escalation paths; a dedicated needle pins the escalation sentence, and the pins suite stays green at every task boundary.
- maintainability: every new span carries a count-gated pin with a concrete prescribed line; the blueprint reference is count-gated at exactly 2 (byte parity).
- coordination: the plan's edits never touch the hygiene plan's prescribed spans (additivity is reviewable against the Coordination paragraph).

**Done when:**

- All tasks checked; the Validation Commands block exits 0 on the post-Task tree.
- `bash scripts/check_maintenance_pins.sh` exits 0 including the new carve-out pins.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md` exits 0.
- The dark-loop drill has been walked and its outcome (exactly one mutation permitted, then stop) recorded in the execution task log (docs/tmp is transient by design; the durable witnesses are the Validation Commands run and the pins suite).

**Ship when:**

- The next real guard trip in an automation-born session holding a state-first recorded decision emits exactly one mutation and the loop re-arms; observed operationally by the loop, not by this repository's tests. Loop-owned; prose only. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`

**Tests:**

- `scripts/check_maintenance_pins.sh`

**Partially-in-scope files:** in `zcode.md`, only the dispatch-discipline bullet (the appended sentence groups, each after the existing stand-down sentence and additive to the hygiene plan's prescribed additions) and the re-arm hygiene paragraph's tail (the escalation-note recovery duty sentence) are open; every other section is frozen. In `prompt-templates.md`, only the tail of the Loop guard sentence inside each of the two FIRST ACTION re-arm paragraphs is open; the paragraphs stay byte-identical to each other and no other line of either blueprint may change. In the pins suite, only the new carve-out pin lines and the freeze-literal origin notes are open.

**Plan-related extension;** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract this plan changed.

**Out of scope; reject unless plan-related:**

- `agents/skills/maintenance/SKILL.md`; reason: this plan deliberately stays at the overlay and payload layer (the dark-case duty is overlay-level; the State file region belongs to the in-flight state-durability plan).
- The budget-gate sections of `agents/skills/plans/SKILL.md` and `agents/skills/execute-plan/SKILL.md`; reason: owned by the sibling resume-fallbacks plan of this family.
- Pre-existing em-dashes in the edited files (measured 2026-09-21: one in the zcode.md Context measurement primitive's Compaction bullet, one in prompt-templates.md's deviation list); reason: frozen or peer-contested regions; the insertions are covered by the exact-needle greps.

## Validation Commands

First executed at authoring time against the pre-task tree (2026-09-21, pre-fold bytes): every text-presence gate was RED with gate 1 first and the pins gate green, exactly as this section requires of the pre-task tree; re-run at every task boundary as the per-task Run lines state. The post-fold gate set below must be RED on the pre-task tree in the same pattern (gates 1 through 15 fail, gate 16 green) and flip GREEN exactly when Tasks 1 through 3 land.

```bash
REPO="$(git rev-parse --show-toplevel)"
Z="$REPO/agents/skills/maintenance/zcode.md"
P="$REPO/agents/skills/maintenance/prompt-templates.md"
PIN="$REPO/scripts/check_maintenance_pins.sh"
fail=0
# 1. Carve-out anchor: exactly once in the overlay (the blueprint reference is lowercase and cannot alias it)
n=$(grep -oF 'One-recorded-mutation carve-out' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: carve-out anchor count $n != 1 in zcode.md"; fail=1; }
# 2. The single-call bound span: exactly once in the overlay
n=$(grep -oF 'exactly ONE mutating call implementing that recorded decision' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: single-call bound span count $n != 1 in zcode.md"; fail=1; }
# 3. The advancing-dispatch scoping clause (the carve-out governs only the stand-down moment)
n=$(grep -oF 'never curtails an advancing dispatch' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: advancing-dispatch scoping count $n != 1 in zcode.md"; fail=1; }
# 4. The escalation-routing sentence (post-single-call refusals keep the existing paths)
n=$(grep -oF 'any refusal after that single call takes the existing escalation paths' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: escalation-routing count $n != 1 in zcode.md"; fail=1; }
# 5. The stop-bound tail (stop after the one call regardless of outcome)
n=$(grep -oF "must stop touching automation primitives immediately after it regardless of the call's outcome" "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: stop-bound tail count $n != 1 in zcode.md"; fail=1; }
# 7. The bound's unit clause (decided mutations, not primitive calls; the re-arm recipe's delete-plus-create is one mutation)
n=$(grep -oF 'The bound counts decided mutations, not primitive calls' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: bound unit clause count $n != 1 in zcode.md"; fail=1; }
# 8. The guard-signature restatement span (the carve-out's own wording of the signature conjunct)
n=$(grep -oF "the loop's signature appeared (two listings, no mutating step between them)" "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: guard-signature restatement count $n != 1 in zcode.md"; fail=1; }
# 8. The state-first gate conjunct (count-gated: absent or duplicated both fail)
n=$(grep -oF 'a state-first write that preceded the first listing' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: state-first gate span count $n != 1 in zcode.md"; fail=1; }
# 9. The narration exclusion conjunct (count-gated: absent or duplicated both fail)
n=$(grep -oF 'a decision recorded only in chat narration does not qualify' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: narration-exclusion span count $n != 1 in zcode.md"; fail=1; }
# 10. The decision-ownership conjunct (overlay copy)
n=$(grep -oF 'or the pending record it takes as its own' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: decision-ownership span count $n != 1 in zcode.md"; fail=1; }
# 11. The operator-override escape sentence
n=$(grep -oF 'an explicit user instruction to proceed outranks them' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: operator-override span count $n != 1 in zcode.md"; fail=1; }
# 12. The single-call decision-write mandate (the carve-out's motivating path)
n=$(grep -oF 'records its decided re-arm in the state file before its first primitive call' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: single-call decision-write mandate count $n != 1 in zcode.md"; fail=1; }
# 13. The escalation-note recovery duty
n=$(grep -oF 'must name the mechanical recovery' "$Z" | wc -l | tr -d ' ')
[ "$n" -eq 1 ] || { echo "FAIL: escalation-note recovery duty count $n != 1 in zcode.md"; fail=1; }
# 14. Blueprint carve-out references: exactly 2 (one per FIRST ACTION paragraph; byte parity)
n=$(grep -oF "the overlay's one-recorded-mutation carve-out" "$P" | wc -l | tr -d ' ')
[ "$n" -eq 2 ] || { echo "FAIL: blueprint carve-out reference count $n != 2 in prompt-templates.md (byte parity)"; fail=1; }
# 14. Blueprint ownership clause: exactly 2 (byte parity)
n=$(grep -oF 'and this session owns that record' "$P" | wc -l | tr -d ' ')
[ "$n" -eq 2 ] || { echo "FAIL: blueprint ownership clause count $n != 2 in prompt-templates.md (byte parity)"; fail=1; }
# 16. Pins suite green (existing pins plus the Task 3 carve-out pins)
bash "$PIN" || { echo "FAIL: maintenance pins do not hold"; fail=1; }
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: Overlay carve-out, operator override, and escalation-note recovery duty

Files:
- `agents/skills/maintenance/zcode.md`

- [ ] Dispatch-discipline bullet, immediately after the existing stand-down sentence ("...record a `turn_error` naming the deferred target, leave the parent armed, and end the turn.") and additive to the hygiene plan's prescribed additions, append the carve-out sentences with these exact spans: the anchor `One-recorded-mutation carve-out` (with the dated origin and the automation-2fd9c94e witness), the scoping clause `never curtails an advancing dispatch` (the carve-out governs the stand-down moment, the session that has stopped retrying and is standing down through a Bash state write; the operative multi-call dispatch whose calls implement the recorded decision step by step - the decision-first discipline's delete-plus-create included, its rollback create included - is not a selection loop and keeps its full path), the conjuncts (`the loop's signature appeared (two listings, no mutating step between them)` AND `a state-first write that preceded the first listing` AND the ownership clause `or the pending record it takes as its own`), the narration exclusion (`a decision recorded only in chat narration does not qualify`), the bound (`may then emit exactly ONE mutating call implementing that recorded decision, and must stop touching automation primitives immediately after it regardless of the call's outcome`) with its unit clause `The bound counts decided mutations, not primitive calls` (the one decided mutation is emitted per the recipe's operative shape, and a parent re-arm's shape is the recipe's delete-plus-create: deleting the session's own lingered spawner record is part of that create's recipe, not a second decided mutation), and the escalation routing (`any refusal after that single call takes the existing escalation paths (rearm_note, memory note, park) with no further primitive calls`) [class: IMPLEMENTATION_REQUIRED]
- [ ] Same bullet, as its final sentence, append the operator override: the guard and its carve-out bind unattended sessions protecting themselves from their own pathology; `an explicit user instruction to proceed outranks them`, and a session reporting a guard stand-down to its user must offer the override instead of only reporting blocked [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-arm hygiene paragraph (the recipe section), as its final sentence, append the escalation-note recovery duty: when a rearm_note or a loop-parent-missing memory note is written by a session that was the sole restorer (no ENABLED recognition match and no live pending child at write time), the note `must name the mechanical recovery` so a rearm-on-touch session executes it instead of re-deriving it: the assembled payload copy path when one exists (the `docs/tmp/future-plan-prompts-<date>.md` form), the recipe pointer ("re-arm per agents/skills/maintenance/zcode.md, Recurring automation recipe"), and the sole-restorer condition observed at write time; the same sentence mandates the recording half of the carve-out's gate on the single-call path: a rearm-on-touch session `records its decided re-arm in the state file before its first primitive call` (the decision-first discipline extended to single-call re-arm dispatches), so the carve-out can qualify on exactly the path it was designed for [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on Validation Commands gates 1 through 13 and 16; gates 14 and 15 stay RED at this boundary (the blueprint references land in Task 2): expect exit 1 listing exactly the two blueprint-parity lines [class: REPOSITORY_TEST]
- [ ] Commit: `feat: loop-guard one-recorded-mutation carve-out and operator override in the overlay` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Blueprint re-arm duty carve-out references (byte parity)

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [ ] In BOTH FIRST ACTION re-arm paragraphs, immediately after the existing sentence `Loop guard: if you have listed twice without a mutating step between listings, write the "rearm_note" field via a Bash state edit naming the loop and stop touching automation primitives.`, append the identical sentence: `Carve-out: when the decided mutation was recorded state-first before the first listing and this session owns that record (its own decision-first write, or the pending record it takes as its own under this duty's record-taking rule), the overlay's one-recorded-mutation carve-out (agents/skills/maintenance/zcode.md, "Dispatch discipline and loop stand-down") permits exactly ONE mutating call implementing that recorded decision before this guard's stop applies regardless of the call's outcome.`; the two paragraphs must remain byte-identical (the parity pin), and no other line of either blueprint may change [class: IMPLEMENTATION_REQUIRED]
- [ ] Same commit: append the deviation-list entry registering the carve-out reference sentence (dated 2026-09-21, this plan; not part of the backlog source text), mirroring the file's convention for blueprint additions; the entry paraphrases and must not quote the pinned spans (a verbatim quote would drift the count gates) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the full Validation Commands block (all gates green at this boundary; the pins gate holds because the Task 3 pins do not exist yet and no existing pin trips) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: re-arm duty loop-guard carve-out references (byte parity)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Pins for the carve-out spans

Files:
- `scripts/check_maintenance_pins.sh`

- [ ] Add the carve-out pin lines in the zcode.md pin section, using the suite's standalone count-check shape (`fail=1` on mismatch), one line per obligation, each a dedicated count check that fails when THAT obligation is absent or duplicated: [class: REPOSITORY_TEST]

```bash
[ "$(grep -oF 'One-recorded-mutation carve-out' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: carve-out anchor count"; fail=1; }
[ "$(grep -oF 'exactly ONE mutating call implementing that recorded decision' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: single-call bound count"; fail=1; }
[ "$(grep -oF 'never curtails an advancing dispatch' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: advancing-dispatch scoping count"; fail=1; }
[ "$(grep -oF 'The bound counts decided mutations, not primitive calls' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: bound unit clause count"; fail=1; }
[ "$(grep -oF 'any refusal after that single call takes the existing escalation paths' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: escalation-routing count"; fail=1; }
[ "$(grep -oF "must stop touching automation primitives immediately after it regardless of the call's outcome" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: stop-bound tail count"; fail=1; }
[ "$(grep -oF "the loop's signature appeared (two listings, no mutating step between them)" "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: guard-signature restatement count"; fail=1; }
[ "$(grep -oF 'a state-first write that preceded the first listing' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: state-first gate count"; fail=1; }
[ "$(grep -oF 'a decision recorded only in chat narration does not qualify' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: narration-exclusion count"; fail=1; }
[ "$(grep -oF 'or the pending record it takes as its own' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: decision-ownership count"; fail=1; }
[ "$(grep -oF 'an explicit user instruction to proceed outranks them' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: operator-override count"; fail=1; }
[ "$(grep -oF 'records its decided re-arm in the state file before its first primitive call' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: single-call decision-write mandate count"; fail=1; }
[ "$(grep -oF 'must name the mechanical recovery' "$Z" | wc -l | tr -d ' ')" -eq 1 ] || { echo "PIN FAIL: escalation-note recovery duty count"; fail=1; }
```

- [ ] Add the blueprint-parity pin in the prompt-templates section, same shape: the reference count equals 2 and the ownership-clause count equals 2 (`grep -oF "the overlay's one-recorded-mutation carve-out" "$P"` and `grep -oF 'and this session owns that record' "$P"`) [class: REPOSITORY_TEST]
- [ ] Append the freeze-literal origin notes per the suite header's protocol (the carve-out spans' superseding origin is this plan); simulate each new pin's failure direction once against a temp copy with the span deleted and record the flips in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 on the post-Task-1-and-2 tree [class: REPOSITORY_TEST]
- [ ] Commit: `test: pins for the one-recorded-mutation carve-out spans` [class: IMPLEMENTATION_REQUIRED]
### Task 4: Dark-loop drill and final validation

- [ ] Dark-loop drill: in a temp directory, build a fixture state file carrying a decision recorded state-first (a `pending_dispatch`-style targeted record written before any listing) and walk the post-Task overlay decision text against it twice: the STAND-DOWN walk (the guard signature appears on the second listing, the session owns the recorded decision, the carve-out permits exactly one mutating call implementing the recorded decision, the session stops after it regardless of outcome, and a refusal after that call routes to rearm_note plus the loop-parent-missing note naming the mechanical recovery) and the ADVANCING-DISPATCH walk (the operative delete-plus-create whose calls implement the recorded decision runs its full path - both calls and the rollback create stay available, the scoping clause never curtails it) plus the AUTOMATION-BORN RE-ARM walk (the stand-down session whose decided mutation is the parent re-arm emits the recipe's delete-plus-create as ONE decided mutation - the lingered-spawner deletion plus the create both stay available under the unit clause); record the three walked outcomes in the execution task log; no live automation call is made; no commit (nothing repo-visible changes; the durable witnesses are the two checks below) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: full Validation Commands block, exit 0 [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md` exits 0 [class: REPOSITORY_TEST]
