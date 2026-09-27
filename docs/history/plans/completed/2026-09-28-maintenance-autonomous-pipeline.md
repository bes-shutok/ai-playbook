# Plan: Maintenance autonomous pipeline

Backlog origin: docs/history/backlog/2026-09-28-maintenance-autonomous-pipeline.md; folded origin: docs/history/backlog/2026-09-28-authoring-lane-guard-precedence.md
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-maintenance-autonomous-pipeline-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make the maintenance loop run the authoring-to-execution pipeline itself, so the prompt queue, the backlog, and the landed plans keep processing across turns without a manually dispatched carrier for each stage.

- After an in-session authoring run lands its plan, the same turn hands that plan to the execution lane while quota, locks, and guards allow, instead of ending the turn at the authoring boundary.
- A scheduled authoring child's closeout verifies its re-armed carrier and repairs a failed or parked re-arm through the dispatch ladder, so a freshly landed plan never waits on a silently failed handback.
- The authoring lane takes distinct work beside a live peer: the occupancy guard distinguishes a same-target claim (which still holds the lane) from a distinct-target claim (which does not, when a standing directive to author is recorded), and the merge landing lock serializes the landings.
- Parked re-arm records are discharged by the next primitive-capable turn before it surveys, a completing stage that would leave the loop without a live carrier records the stranding and parks a successor payload, and the turn records and the weekly report carry throughput numbers (queue depth, plans authored and executed, stranded or parked stages) so the automation gain is measured.

## Assumptions

- assume the Step 3 rolling prompt log duties bullet stays the queue-consumption home and gains the continuation legs, rather than a new survey stage; basis: the duties bullet (added 2026-09-27) already reads the log top-down, prunes landed entries, and dispatches the top entry in-session.
- assume `loop_mode` (dual or authoring-only) and an explicit standing directive in the dispatching payload are the two durable sanction sources for the distinctness exception; basis: the State file `loop_mode` contract is the recorded standing direction, and the 2026-09-28 user override sanctions parallel authoring beside a live peer with target distinctness as the real gate.
- assume the account-level quota governor lands separately from this plan; this plan wires only the continue-loop consult against that origin's pressure classes and degrades to the existing probe reading until the governor's evaluator exists; basis: the sibling origin docs/history/backlog/2026-09-28-account-level-quota-governor.md is queued and its class contract is the scope of record.
- assume no new script, no new mechanical gate, and no new state-file key family beyond one new `turn_error` literal and the throughput tokens; basis: the 2026-09-28 machinery cost-benefit adjudication and the active-elimination doctrine (a keep or an addition cites its witness).
- assume the worktree-first standard (the canonical section landed 2026-09-28 in the execute-plan skill) stays the per-run isolation boundary and this plan adds no run-shape prose of its own; basis: the worktree-first standard-only-mode plan, landed main b36d5e2a.
- assume the successor-carrier arming duty reuses the zcode.md Recurring automation recipe and the Child dispatch ladder as-is, with no new recipe; basis: both surfaces already exist and the ladder already terminates in the park-with-payload rung.

Decision points requiring a grill: guard-precedence origin folded into this plan as Task 1: receipt: the origin's own Suggested fix names this plan as the fold target (docs/history/backlog/2026-09-28-authoring-lane-guard-precedence.md, filed 2026-09-28), affects Task 1; parallel authoring beside a distinct-target peer sanctioned: receipt: user direction 2026-09-28 (the same-day G1a parallel-authoring override plus the interactive correction of the 09:32 stand-down), affects Task 1 and Task 2; queue consumption continues through the existing rolling-log duties rather than a new stage: receipt: standing pre-authorization in the PLAN-PROMPTS.md entry maintenance-autonomous-pipeline (user direction, 2026-09-28), affects Task 2.

Scope extensions (grilled): none proposed.

## Gist & Examples

TLDR: the maintenance loop consumes the prompt queue, hands each landed plan to the execution lane, and recovers its own stalls, so routine processing runs without a manually dispatched carrier per stage; driving force: automation (machinery that runs the routine loop itself).

**Before (today):** the loop's per-turn pieces exist but nothing chains them. The rolling-log monitor authors the top queue entry in-session and stops at the authoring boundary; a scheduled authoring child re-arms the carrier as its payload's FIRST ACTION, so the loop itself is not dark after the child, but nothing verifies that re-arm at closeout, and when it parks or refuses the freshly landed plan waits silently for a carrier that never comes; the in-session path stops at the authoring boundary, so the latency to execution is a full carrier interval even when the same session could continue; recovery of a parked record waits for a payload that names the duty, not for the loop itself; and the 09:32 incident on 2026-09-28 shows the occupancy guard standing the authoring lane down on a live peer's claim without checking whether the candidate target was distinct, idling the lane for hours under a standing user directive to keep authoring.

**After (this plan):** one turn can author the top queue entry, land it, and execute it, then continue to the next target while quota, locks, and guards allow, with every stop reason recorded. A child whose FIRST ACTION re-arm failed has that failure caught and repaired at closeout, inside the re-arm duty's own grant. A peer authoring a different plan no longer idles this lane, and a taken top entry no longer hides a distinct untaken entry behind it. Concrete example: the 09:32 turn, replayed under this plan, would have found the em-dash peer's claim distinct from the top queue entry, authored the entry in-session beside the peer, landed through the merge lock, and continued to the execution decision on the fresh plan in the same turn.

**Edge cases that shaped the design:** a same-target claim still holds the lane, because duplicate work on one target is the failure the occupancy guard exists to prevent; a reduced-toolset session (automation listing only) cannot discharge parked records and leaves them parked, the sanctioned terminal that a later primitive-capable turn reverses; a continue-loop stop at quota exhaustion with a reset time rides the existing pause semantics rather than inventing a new wait mechanism; and the stranding detector counts both an armed carrier arriving within one cadence and a reset-window carrier armed by the recipe's cadence rule (whose fire time can sit past one cadence after a quota pause) as explanations, so a healthy loop never trips it.

## Evaluation Criteria

**Quality dimensions:**
- witness discipline: every added or rewritten rule cites its witness (a recorded incident, a user decision, or an origin line); no rule exists on assertion alone
- correctness: the rewritten occupancy rule preserves same-target exclusion and the audit and re-triage exclusivity sentences in meaning; the continuation preference slots behind the execution_queue head rule, never ahead of it
- runtime neutrality: the edited shared skill bodies pass the shared-body forbidden-term gate
- maintainability: the pins suite stays green; every pin whose pinned span a task rewords is re-keyed in the same edit

**Done when:**
- the distinctness and standing-directive precedence rules exist exactly once in `agents/skills/maintenance/SKILL.md` (the G1a lane rule), with the discovery arm and the rolling-log duties referencing them rather than restating them
- the continuation rules exist: the D1 fresh-plan preference, the in-session chaining after a landed authoring run, the successor-arming closeout duty in the authoring child payload, and the monitor chaining leg
- the continue-loop condition exists once with its quota-pressure consult and degradation arm, and every stop records its reason
- the Step 0 discharge precedence, the Step 6 stranding detection with its `turn_error: completion-stranded` literal, and the dispatch ladder's named reduced-toolset terminal rung exist
- the queue-depth token and the weekly throughput block exist with their durable sources named
- the pins suite, the shared-body runtime-neutrality gate, the no-em-dash scan over added lines, and the public hygiene scan all exit 0, and `scripts/plan_readiness.py` exits 0 on the final plan bytes

**Ship when:**
- consumer repositories that vendor these skills pick the updated bodies up on their next sync (prose only; no deploy step in this repository)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (Step 0 discharge precedence; Step 2 G1a lane rule and discovery arm; Step 3 D1 preference, in-session chaining, continue-loop condition, rolling-log duties sync; Step 6 stranding detection; Step 7 throughput block)
- `agents/skills/maintenance/zcode.md` (Child dispatch ladder terminal rung; recipe cross-reference from the succession duty)
- `agents/skills/maintenance/prompt-templates.md` (authoring child closeout succession duty; scheduler payload standing-directive sentence)
- `scripts/check_maintenance_pins.sh` (pin re-keys riding the rewording)

**Tests:**
- none *(the plan adds no test files; the verification obligations run existing gates: the maintenance pins suite, the shared-body runtime-neutrality test, the no-em-dash scan, the public hygiene scan, and the readiness validator)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. References to the rewritten rules from `agents/skills/maintenance/SKILL.md` sibling sections (the quota-aware lane decisions bullet, the audit and re-triage contention bullets) are in scope where the rewrite would leave them dangling. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-plan/SKILL.md`, `agents/skills/review-loop/SKILL.md`, `agents/skills/receiving-review/SKILL.md`; reason: review exit conditions and caps belong to the review-loop-exit-condition-metrics item
- `scripts/quota_window_probe.py` and any new governor evaluator script; reason: the pressure evaluator belongs to the account-level-quota-governor item; this plan only consults its class contract with a degradation arm
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/execute-plan/runtime-contract.md`; reason: the worktree-first standard and worker-lifecycle layers just landed or are owned elsewhere; no run-shape change here
- the interactive execute-then-continue policy origins (docs/history/backlog/2026-09-27-next-execute-after-landing-interactive-default.md and docs/history/backlog/2026-09-27-compact-between-execution-runs-mechanism.md); reason: this plan owns the autonomous loop only; the interactive ask policy is the queued p68 item
- `scripts/tool_runtime_stats.py`; reason: the measurement miner's own tail is the queued p62 item; this plan only appends a derived block through the existing Step 7 rider

## Validation Commands

Validation preamble (authoring-time execution record, per the plans skill's rule 29 and rule 19 duties): the block below was executed against the pre-implementation tree in the authoring worktree, re-executed after each review fold batch. Because the block is fail-fast, the gates were executed individually to record each one's outcome. G1 through G5 are presence probes over spans this plan adds, so each FIRED RED on the current bytes (span absent; for G2 the prompt-templates half of the probe already passes today, the SKILL.md half is the RED leg), and each probe was verified in the opposite direction against a temp copy of the target file carrying the simulated post-edit state, where the full set passes, so both directions are exercised; the G1 leg set was redesigned twice on review evidence (the r2 reconciliation after the first state-file-arm extraction proved unbounded, r2 F2; the r3 reconciliation adding per-site legs for every fold-batch edit site after the unanchored duties anchor matched two spans, r3 F2) and the final nine-leg set was re-verified in both directions: RED on the current bytes for every leg, GREEN on the simulated post-edit copy, with every region leg's extraction proven non-empty and line-anchored on the real bullet literals (regions of 2, 1, 1, 1, and 1 lines measured). G6 (pins suite) exited 0, the baseline the pin tasks must restore; G7 (runtime neutrality) exited 0 via the unittest fallback (pytest absent in this environment); G8 (em-dash added-lines against main) exited 0; G9 (hygiene) exited 0; G10 (readiness pre-round) exited 0 on the drafted bytes, after one environment fix that touched no plan bytes (the gitignored facts document was not yet transferred into the authoring worktree, so the validator could not resolve the directory keys; the worktree-first recipe's transfer-in step covers this). Simulate the swapped shape before trusting any order-sensitive gate.

```bash
REPO="$(git rev-parse --show-toplevel)"
S="$REPO/agents/skills/maintenance/SKILL.md"
Z="$REPO/agents/skills/maintenance/zcode.md"
P="$REPO/agents/skills/maintenance/prompt-templates.md"

# G1: the distinctness rule's home sentence exists exactly once, every G1a arm and
# every consumer site carries it, and the audit and re-triage exclusivity spans
# survive (presence, counting, and preservation probes; RED until Task 1). Every
# region leg anchors on a real line-start literal and ends at the next bullet
# anchor, so each leg witnesses its own edit site and cannot pass via a
# different span.
test "$(grep -cF 'does not hold the lane when the targets are distinct' "$S")" -eq 1 \
  || { echo "FAIL G1: rule home sentence missing or restated"; exit 1; }
grep -q 'One authoring child still never runs alongside another' "$S" \
  && { echo "FAIL G1: unqualified single-occupancy sentence still present"; exit 1; }
awk '/^- `G1a \(authoring lane\)`/{f=1} /^- Fleet cap/{f=0} f' "$S" | grep -q 'target-distinctness' \
  || { echo "FAIL G1: G1a lane region lacks the rule reference"; exit 1; }
awk '/^  - Discovery arm \(authoring-side\)/{f=1} /^- Fleet cap/{f=0} f' "$S" | grep -q 'target-distinctness' \
  || { echo "FAIL G1: discovery arm lacks the rule reference"; exit 1; }
awk '/^- `D2 \(author\)`/{f=1} /^- Execution-lane carrier-selection ordering/{f=0} f' "$S" | grep -q 'target-distinctness' \
  || { echo "FAIL G1: D2 does not reference the rule"; exit 1; }
awk '/^- `D1 \(execute\)`/{f=1} /^- `D4 \(propose park\)`/{f=0} f' "$S" | grep -q 'freshly landed plan' \
  || { echo "FAIL G1: D1 lacks the fresh-plan continuation"; exit 1; }
awk '/^- Rolling prompt log duties/{f=1} /^- Quota-aware lane decisions/{f=0} f' "$S" | grep -q 'target-distinctness' \
  || { echo "FAIL G1: rolling-log duties do not reference the rule"; exit 1; }
grep -q 'an audit child never runs alongside an authoring child or another audit child' "$S" \
  || { echo "FAIL G1: audit-child exclusivity span lost"; exit 1; }
grep -q 'never runs alongside an authoring child, another re-triage child, or an audit child' "$S" \
  || { echo "FAIL G1: re-triage-child exclusivity span lost"; exit 1; }

# G2: the continuation wiring exists (presence probes; RED until Task 2)
grep -q 'freshly landed plan' "$S" && grep -q 'successor' "$P" \
  || { echo "FAIL G2: continuation rules missing"; exit 1; }

# G3: the Step 0 discharge precedence exists (presence probe; RED until Task 4)
grep -q 'discharges parked' "$S" || { echo "FAIL G3: discharge precedence missing"; exit 1; }

# G4: the stranding detection exists with its literal (presence probe; RED until Task 4)
grep -q 'completion-stranded' "$S" || { echo "FAIL G4: stranding detection missing"; exit 1; }

# G5: the throughput instrumentation exists (presence probe; RED until Task 5)
grep -q 'queue-depth' "$S" && grep -q 'Throughput' "$S" \
  || { echo "FAIL G5: throughput instrumentation missing"; exit 1; }

# G6: the maintenance pins suite is green after the re-keys
bash "$REPO/scripts/check_maintenance_pins.sh" >/dev/null \
  || { echo "FAIL G6: pins suite red after edit"; exit 1; }

# G7: the edited shared skill bodies stay runtime-neutral (pytest when the
# environment has it; the unittest fallback mirrors the interpreter note in
# the worktree-first plan)
python3 -m pytest "$REPO/scripts/test_execute_plan_runtime.py" -k shared_skill_bodies -q 2>/dev/null \
  || PYTHONPATH="$REPO/scripts" python3 -m unittest -k shared_skill_bodies scripts.test_execute_plan_runtime \
  || { echo "FAIL G7: shared skill body carries a forbidden term"; exit 1; }

# G8: no em-dash in the run's added lines (default-branch integration project: base is main)
BASE_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')"
[ -n "$BASE_BRANCH" ] || BASE_BRANCH=main
bash "$REPO/scripts/check-no-em-dash.sh" added-lines --base "$BASE_BRANCH" \
  || { echo "FAIL G8: em-dash in added lines"; exit 1; }

# G9: public hygiene scan over the repository
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" \
  || { echo "FAIL G9: hygiene scan hit"; exit 1; }

# G10: readiness validator over the final plan bytes
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-28-maintenance-autonomous-pipeline.md ) \
  || { echo "FAIL G10: readiness pre-round structural gate"; exit 1; }
```

### Task 1: Authoring-lane target distinctness and standing-directive precedence

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Rewrite the authoring-vs-authoring clause of the G1a lane rule (the sentence beginning "One authoring child still never runs alongside another") into the target-distinctness rule: an authoring occupant holds the lane when its claim target matches the candidate target, and does not hold the lane when the targets are distinct and a standing directive to author is recorded (`loop_mode` dual or authoring-only, or an explicit standing directive in the dispatching payload); the audit-child and re-triage-child exclusivity sentences keep their meaning unchanged; the rule names the 2026-09-28 09:32 stand-down incident as its witness and states that a standing user directive outranks a lane-occupancy stand-down. [class: IMPLEMENTATION_REQUIRED]
- [x] Subject every G1a arm to the rule through the lane bullet's inheritance sentence: the G1a lane-rule bullet (the one opening "the same arms as `G1e`, evaluated only against authoring children") gains the carve-out so an authoring child's hold under the state-file, armed, fired, and widened arms releases when the recorded or listed child's target is distinct from the candidate target and the standing-directive sanction exists; the occupant's target resolves through a three-rung ladder, because a scheduled peer has no claim file before its session starts: the pending `children[]` entry keyed on the plan or item slug first (the pre-fire witness, present from dispatch time), then the claim file by target-keyed matching, then the listed prompt's target-bearing span; a record none of the three explains occupies, the not-visible fail-safe unchanged; the execution-side semantics of the shared arms stay untouched; the audit-child and re-triage-child holds stay unconditional, byte-for-byte in meaning. [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the exception in the G1a discovery arm: a foreign claim (item matching no pending entry) occupies the lane only when its item target matches the candidate target or no standing directive sanction exists; the claim file's item slug and the live worktree branch names are the witness set for the distinctness read; stale-claim semantics stay unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Sync the two references that read the lane-free precondition (the rolling prompt log duties bullet's dispatch clause and the D2 guard-resolution sentence) to reference the distinctness rule by name instead of restating an occupancy test, so the rule has one home; the rolling-log dispatch clause gains the next-distinct-entry scan: when the top surviving entry's target matches a live claim under the distinctness rule, the turn evaluates the next surviving entry for a distinct target before holding the lane, so a taken top entry never hides a distinct untaken entry behind it. [class: IMPLEMENTATION_REQUIRED]
- [x] Add pins over the new rule's home sentence, the arms carve-out, and the preserved audit-child and re-triage-child exclusivity spans in `scripts/check_maintenance_pins.sh` (no pin covers the authoring-vs-authoring clause or the preserved exclusivity sentences today; the existing G1a-region pins keep their spans because this plan does not reword them: the `G1a guard present` heading pin, the region-scoped discovery-arm extraction pins, and the P57 fleet-member sequencing pin whose span sits on a sentence Task 1 does not touch; the Invariants "per-lane cap wording" pin likewise needs no change) and run the pins suite, expect GREEN before leaving the task. [class: REPOSITORY_TEST]

### Task 2: Authoring-to-execution continuation

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

- [x] Add the D1 fresh-plan preference: behind the execution_queue head rule, when the state's latest authoring completion (a scheduled child's evidenced completion, or an in-session authoring run landed this turn) produced an open dispatchable plan, D1 selects that plan ahead of the memory dependency-chain ordering, still through the guards, the certification oracle, the quota leg, and the landing gate; the preference is recorded in `decision_reason` when it fires. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the in-session chaining rule: after an in-session authoring run lands its plan (a backlog-item authoring or a rolling-log entry authoring), the same turn re-runs the execution-lane decision on the freshly landed plan under the continue-loop condition, recording the standard `(in-session)` execution child entry; the monitor's duties text gains the chaining leg instead of ending at the authoring boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Restate the authoring child template's closeout duties in `agents/skills/maintenance/prompt-templates.md` as a closeout verification-and-repair of the successor carrier, operating entirely within the payload's existing FIRST ACTION re-arm grant so the chaining guard sentence stays true unamended: at closeout the child verifies the carrier its FIRST ACTION re-arm armed (the recognition match recorded in the state file); when the re-arm parked or refused (a `pending_rearm` record or no recognition match), the closeout repairs it through the Recurring automation recipe and the Child dispatch ladder's park-with-payload rung, which on an automation-born session the lineage cap refuses the create and the park rung is the sanctioned terminal; when the carrier is armed, the duty records the armed carrier id and does nothing else, so a landed plan never waits on a silently failed handback and no redundant successor payload is parked beside a live carrier. [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep the Step 3 decision text for any sentence or clause whose only reading is that the turn stops after its authoring dispatch, and re-point each hit to the continue-loop condition; where no explicit sentence exists (the stopping shape may be emergent rather than written), the sweep records that finding in the task evidence, the chaining rule now governing the shape by construction. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the G2 continuation probe legs after the sweep and expect GREEN (the D1-preference and rolling-log legs witness the landed continuation text), recording the run in the task evidence. [class: REPOSITORY_TEST]

### Task 3: Continue-loop condition with quota-pressure consult

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Define the continue-loop condition once in the Step 3 decision section, referenced by name from Task 2's sites: the loop continues while (a) quota pressure permits, (b) the merge landing lock and the done lock are free, (c) the Step 2 guards pass, and (d) a dispatchable target exists; every stop records its reason in `decision_reason`, and the condition names its witnesses (the 09:32 dark gap and the 2026-09-28 user direction to keep processing). [class: IMPLEMENTATION_REQUIRED]
- [x] Write the condition's quota leg as a consult of the account-level governor's pressure classes per the sibling origin (abundant and tightening continue, constrained defers with the standing interactive reserve, exhausted waits for reset), with the degradation arm: until the governor's evaluator exists, the existing probe reading with its landed thresholds and pause decisions governs the same leg. [class: IMPLEMENTATION_REQUIRED]
- [x] Record the supersession sentence beside the condition: the same-day scheduler-lattice-pruning proposal is superseded by the pipeline direction per the user reversal of 2026-09-28, so no reader reverts the loop to the pruning shape. [class: IMPLEMENTATION_REQUIRED]

### Task 4: Stall-class recovery

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add the Step 0 re-arm discharge precedence as a timing amendment of the existing park-discharge machinery, not a second discharge duty: at Step 0, before the survey, a turn whose prechecked toolset carries the create primitives discharges a parked `pending_rearm` record (read the payload copy from disk, perform the recorded arm, verify survival, then delete the payload copy); the sentence names the duty plainly (the turn discharges parked re-arm records before it surveys) so the gate literal lands. The `pending_dispatch` half is NOT moved: dispatch discharge stays owned by the existing Step 1 parked-intent discharge duty with its fresh-survey validation arms (target presence, gate classification, loop-mode, rate pressure, the landing gate) applying unchanged, and the Step 0 text cross-references that duty instead of duplicating it; the discharge writes join the sanctioned state-writer enumeration the existing duty's writes use. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Step 6 completion-stranding detection: after the state write, when dispatchable work remains (an open certified plan, a non-empty execution queue, or a ready prompt-log entry) and no live carrier explains the next turn, the turn records `turn_error: completion-stranded` and parks the successor payload per the park-with-carrier rule. The explanation predicate is wide enough to never trip on a healthy loop: an armed carrier whose recorded fire time falls within one cadence counts, AND a reset-window carrier armed by the recipe's cadence rule for a later quota window counts as well (its fire time can sit past one cadence after a quota-pause stop), and the detector consults the continue-loop stop's recorded quota-pause reason and suppresses the trip while such a reset-window carrier is armed. [class: IMPLEMENTATION_REQUIRED]
- [x] Consolidate the reduced-toolset terminal in the zcode.md Child dispatch ladder as a named rung: a session whose automation toolset is the listing primitive only parks the decided action with its payload copy and stops touching the primitives, and the rung names the Step 0 discharge precedence as the recovery path a later primitive-capable turn owns. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the owning pins over any reworded span in `scripts/check_maintenance_pins.sh` in the same edit and run the pins suite, expect GREEN before leaving the task. [class: REPOSITORY_TEST]

### Task 5: Throughput instrumentation

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Add the per-turn queue-depth token to the survey output duties: the turn records `queue-depth=log:<n>,uncovered:<n>,plans:<n>` (ready prompt-log entries, plan-uncovered open backlog items, open top-level plans) in the `decision_reason` summary strings, the survey's existing persistent record home, with no state-schema change. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Step 7 weekly rider's report section with a throughput block appended to the same digest-log section the rider already writes (aggregates only, no new script, no new file), opening with the literal heading "Throughput": per period, the count of `children[]` entries by kind and evidenced outcome (authoring completions, execution completions), stated as a lower bound over the state file's retention window (the `children` array keeps the last 20 entries, and the block names that bound so no reader takes the number as a true period total); the count of entries whose outcome records a `turn_error` or a parked recovery, the plan's durable-source-driven proxy for the origin's "manual interventions required" measure (recorded here as the proxy decision); and the current queue depth (log entries, plan-uncovered open items, open plans), which reads live state and has no retention bound. [class: IMPLEMENTATION_REQUIRED]

### Task 6: Corpus verification and commit

Files:
- none *(verification task; touches only the files above)*

- [x] Run the full Validation Commands block; expect exit 0 with every gate green. [class: REPOSITORY_TEST]
- [x] Commit: `skills: wire the maintenance loop to run the pipeline itself` [class: IMPLEMENTATION_REQUIRED]
