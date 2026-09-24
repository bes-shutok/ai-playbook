# Plan: Guard-standdown self-healing loop recovery (mandatory out-of-band carrier)

Backlog origin: `docs/history/backlog/2026-09-25-guard-standdown-loop-dark-recovery.md`
Driving force: efficiency

## Terms

- loop guard: the dispatch-discipline guard that stands down automation primitives after an emission loop (repeated listings with a decided mutating call unsent).
- launchd resume carrier: the out-of-session carrier built from a launchd job running the CLI headless, whose job script exports the provider-config environment itself.
- parked intent: a `pending_rearm` or `pending_dispatch` entry recorded by a stand-down, paired with its payload copy.
- able-surface witness: the just-succeeded Bash state write that proves the standing-down session can still execute Bash-native work.
- in-turn recovery: discharging the parked intent and re-arming the carrier within the same turn that recorded the `turn_error`, under an explicit operator override or a later primitive-capable path.

## Assumptions

- This plan serializes after the landed prevention plan `docs/plans/2026-09-25-maintenance-rearm-emission-loop-prevention.md` (main 9ff41c7a, not yet executed at authoring time): of this plan's three edit anchors, the scoped-remedy tail is that plan's PRESCRIBED post-execution form (verified verbatim in its bytes today), while the launchd clause and the decision-first sentence are pre-existing live zcode.md text that the prevention plan does not touch; the Phase-0 drift task re-verifies all three in the live files before any edit. Basis: repo greps 2026-09-25 (remedy anchor 1 in the landed plan bytes; the other two anchors 1 each in live zcode.md).
- The launchd recipe's mechanics (env-complete job script, headless CLI invocation) are already specified in the overlay's "Launchd resume carrier" bullet; this plan changes its trigger from optional to mandatory on re-arm parks and pins the self-disable behavior; basis: the origin item's fix 1 wording and the existing recipe text.
- The failure cap's streak-reset change is a semantics clarification over the existing consecutive-count tripwire, not a schema change; basis: the origin item's fix 3 wording and the state schema's integer field.
- One-message decision+emission pairing binds the deciding turn's own emission shape; it does not constrain a LATER session executing a parked payload (that session's decision is its own); basis: the origin item's fix 2 wording and the park-discharge duty's separate decision path.
- If the prevention plan is deferred or abandoned rather than executed, this plan's Gate 0 fails closed indefinitely; the revisit arm is re-derivation: Task 0 then stops with a report naming the drift, and the anchors are re-derived from whatever form the prevention surfaces took, never silently edited around. Basis: the risk review's starvation finding and the serialize-after discipline.
- The retired rationale idiom surviving in the payload layer (the successor duty's park-first chaining sentence in prompt-templates.md) is an accepted residual: the payload layer's re-arm text is already an accepted residual of the prevention plan and this plan does not widen that surface; basis: the residual discipline recorded in the prevention plan's Assumptions.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Makes a loop-guard stand-down self-healing by making the launchd resume carrier mandatory whenever a stand-down parks a re-arm, tightening one-message decision+emission pairing, and codifying the in-turn recovery streak reset; an efficiency repair, because the 2026-09-25 11:12 guard trip left the loop dark for over two hours waiting for an operator even though prevention (main 9ff41c7a) had already landed.

Example of the gap being closed: on 2026-09-25 the carrier session tripped the loop guard, parked its re-arm, and went dark from 11:12 until the operator-override discharge at 13:56, when an operator override discharged the park by hand; under this plan the same stand-down's Bash state write also installs the launchd resume carrier, so the parked payload executes headless at the next window's start with no operator in the loop. Example of the streak change: the recovery turn reset `consecutive_turn_errors` to 0 manually; under this plan that reset is the written rule, so a healed loop does not cost the next turn's lanes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every inserted rule is verifiable by an occurrence-counted grep whose span occurs exactly once at its named surface, and every replaced stale phrase has a zero-count gate.
- consistency: the mandatory-carrier rule, the pairing rule, and the streak rule each live in the bullet that owns them, and the Phase-0 drift gate binds execution to the landed prevention plan's executed state.
- maintainability: no duplication of the launchd recipe mechanics; the remedy bullet references the recipe bullet by name.

**Done when:**
- All three origin fixes are present at their named surfaces and the full Validation Commands block exits 0 over the executed tree.
- The pins suite and the public-hygiene scan exit 0.
- The plan passes the readiness gate over the final bytes with zero blocking findings.

**Ship when:**
- The next guard trip, if any, ends with the parked payload executed by the launchd carrier and the loop re-armed with no operator touch; operational observation over subsequent loop turns. Evidence owner: the maintenance loop's own turn records and the launchd job log. Closure condition: one guard trip recovered end to end without operator action. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`

**Tests:**
- none new; the validation gates live in this plan's Validation Commands block and the existing pins suite.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/2026-09-25-maintenance-rearm-emission-loop-prevention.md` (landed, archived when executed); this plan serializes after it and never edits it.
- `scripts/check_maintenance_pins.sh`; run, not edited.
- `.ai-playbook/scheduler-state.json`; runtime state.
- `docs/history/backlog/*`; the origin item routes at completion.

## Validation Commands

Authoring-time RED evidence, recorded 2026-09-25 over the pre-edit tree: the three stale spans (the launchd bullet's optional wording, the decision-first discipline's unpaired form, the absence of the streak-reset rule) each verified at their expected pre-edit counts; every new-span gate reads 0; the pins suite exits 0; the launchd anchor and the decision-first anchor exist verbatim exactly once in zcode.md; the remedy anchor exists verbatim exactly once in the LANDED prevention plan's bytes (it enters zcode.md when that plan executes; Gate 0 of this block is the Phase-0 drift gate and fails closed until then). Executed readings (pre-edit tree): optional-carrier wording 1, unpaired decision-first 1 (both RED as designed); streak-reset span 0; both new spans 0; pins suite rc 0. The block's first failing gate on the pre-edit tree is Gate 0 (the prevention plan is not yet executed; serialize-after by design).

```bash
REPO="$(git rev-parse --show-toplevel)"
Z="$REPO/agents/skills/maintenance/zcode.md"
S="$REPO/agents/skills/maintenance/SKILL.md"
PREV="$REPO/docs/plans/2026-09-25-maintenance-rearm-emission-loop-prevention.md"
LANDFORM="$REPO/docs/plans/completed/2026-09-25-maintenance-rearm-emission-loop-prevention.md"
occ() { grep -oF "$1" "$2" | wc -l | tr -d ' '; }

# Gate 0 (task 0): Phase-0 drift gate; the prevention plan must be executed (archived) before this plan's edits run
if [ -f "$PREV" ]; then echo "GATE0 prevention plan not yet executed; serialize after it"; exit 1; fi
test -f "$LANDFORM" || { echo "GATE0 executed prevention plan not found in completed/"; exit 1; }
test "$(occ 'the just-succeeded state write is the able-surface witness for the continuation' "$Z")" -eq 1 || { echo "GATE0 remedy anchor missing from zcode.md; drift or partial execution"; exit 1; }
test "$(occ 'the FIRST automation primitive of the decided re-arm is the delete of that record' "$Z")" -eq 1 || { echo "GATE0 delete-first anchor missing; partial execution"; exit 1; }
test "$(occ 'stand down the automation-primitive surface for the session' "$Z")" -eq 1 || { echo "GATE0 scoped-remedy anchor missing; partial execution"; exit 1; }

# Gate 0b: pins suite over the edited surfaces
bash "$REPO/scripts/check_maintenance_pins.sh" || { echo "GATE0b pins-suite FAILED"; exit 1; }

# Gate 1 (task 1): mandatory launchd resume carrier at stand-down time
test "$(occ 'the sanctioned out-of-session carrier is a launchd job' "$Z")" -eq 0 || { echo "GATE1 optional-carrier wording still present"; exit 1; }
test "$(occ 'sanctioned resume-carrier fallback' "$Z")" -eq 0 || { echo "GATE1 suppression fallback wording still present"; exit 1; }
test "$(occ 'the mandatory resume-carrier rule is the launchd + headless-CLI recipe' "$Z")" -eq 1 || { echo "GATE1 mandatory-rule span missing"; exit 1; }
test "$(occ 'the mandatory out-of-session carrier is a launchd job' "$Z")" -eq 1 || { echo "GATE1 mandatory-carrier span missing"; exit 1; }
test "$(occ 'same Bash state write that parks the intent also installs the launchd resume carrier' "$Z")" -eq 1 || { echo "GATE1 install-at-standdown span missing"; exit 1; }
test "$(occ 'bootout-before-install, and sentinel self-disable pattern' "$Z")" -eq 1 || { echo "GATE1 watcher-pattern span missing"; exit 1; }
test "$(occ 'self-disables on a verified successful payload run' "$Z")" -eq 1 || { echo "GATE1 self-disable span missing"; exit 1; }
test "$(occ 'an install failure takes the rearm_note and memory-note escalation' "$Z")" -eq 1 || { echo "GATE1 install-failure span missing"; exit 1; }
test "$(occ 'records a missed-fire rearm_note at the next touch' "$Z")" -eq 1 || { echo "GATE1 missed-fire span missing"; exit 1; }

# Gate 2 (task 2): one-message decision+emission pairing
test "$(occ 'record the decision in the state file via a Bash edit BEFORE the first primitive call' "$Z")" -eq 0 || { echo "GATE2 unpaired decision-first wording still present"; exit 1; }
test "$(occ 'instead of losing the whole turn' "$Z")" -eq 0 || { echo "GATE2 replaced-sentence tail still present"; exit 1; }
test "$(occ 'first call, in the same assistant message that then emits the calls implementing the decided mutation' "$Z")" -eq 1 || { echo "GATE2 ordering span missing"; exit 1; }
test "$(occ 'no message boundary may separate the recorded decision from its emission' "$Z")" -eq 1 || { echo "GATE2 pairing span missing"; exit 1; }
test "$(occ 'the pending-record and record-taking rules' "$Z")" -eq 1 || { echo "GATE2 truncation-branch span missing"; exit 1; }

# Gate 3 (task 3): in-turn recovery streak reset
test "$(occ 'resets `consecutive_turn_errors` to 0 in the same targeted edit that records the recovery' "$S")" -eq 1 || { echo "GATE3 streak-reset span missing"; exit 1; }
test "$(occ "the turn's Step 6 write carries the reset forward" "$S")" -eq 1 || { echo "GATE3 step6-carry span missing"; exit 1; }
test "$(occ 'name the recovery edit' "$S")" -eq 1 || { echo "GATE3 writer-registration span missing"; exit 1; }

# Gate 4: preserved anchors from the executed prevention plan stay intact
test "$(occ 'the FIRST automation primitive of the decided re-arm is the delete of that record' "$Z")" -eq 1 || { echo "GATE4 prevention-plan delete-first span lost"; exit 1; }
test "$(occ 'stand down the automation-primitive surface for the session' "$Z")" -eq 1 || { echo "GATE4 prevention-plan scoped remedy lost"; exit 1; }

# Gate 5: hygiene over the whole repo, anchored to the repo root
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || { echo "GATE5 hygiene FAILED"; exit 1; }

echo "ALL VALIDATION GATES GREEN"
```

### Task 0: Phase-0 drift gate and serialization check

Files:
- none edited; gate verification only

- [x] Verify the prevention plan `docs/plans/2026-09-25-maintenance-rearm-emission-loop-prevention.md` has executed (archived under `docs/plans/completed/`); if it has not, stop this plan before any edit and report the serialization dependency; then run Gate 0's remedy-anchor check against the live `agents/skills/maintenance/zcode.md` and reconcile any drift between the executed bytes and the landed plan's prescribed forms before proceeding [class: REPOSITORY_TEST]

### Task 1: Mandatory launchd resume carrier at stand-down time (origin fix 1)

Files:
- `agents/skills/maintenance/zcode.md`

- [x] zcode.md "Launchd resume carrier" bullet: replace the clause `the sanctioned out-of-session carrier is a launchd job running the CLI headless` with, verbatim: `the mandatory out-of-session carrier is a launchd job running the CLI headless, installed by every parking session's own Bash state-write step (paired with the park record per the park-path pairing rule) and following the keyed-label, bootout-before-install, and sentinel self-disable pattern of scripts/execute_plan_resume_watcher.py` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md same bullet, appended after its env-complete job-script sentence, verbatim: `The fire time is the probe's reported reset_at_epoch plus 10 minutes (the arming margin); the install is verified by a read-back in the same sequence, an install failure takes the rearm_note and memory-note escalation with an operator report, the job self-disables on a verified successful payload run (a re-arm recognized per the HOST CAVEAT's verifiable-echo discipline), and a park still set past the carrier's fire window, or a carrier past its fire window whose park is discharged with no verified re-arm recorded, records a missed-fire rearm_note at the next touch.` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md emission-suppression clause, same dispatch-discipline bullet: replace `the sanctioned resume-carrier fallback is the launchd + headless-CLI recipe` with, verbatim: `the mandatory resume-carrier rule is the launchd + headless-CLI recipe` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md dispatch-discipline bullet, appended after the sentence ending `the state-file record being the stop it requires for the stood-down surface.`, verbatim: `The stand-down's same Bash state write that parks the intent also installs the launchd resume carrier per the Launchd resume carrier bullet, so a guard trip's default path no longer ends with the loop dark waiting for an external touch.` [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate1` run: Gates 0, 0b, and 1; expect both stale Gate 1 counts 0 (optional wording, suppression fallback) and all seven new Gate 1 spans 1 each; Gates 2 to 3 still RED until their tasks land [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance mandatory launchd resume carrier at guard stand-down` [class: IMPLEMENTATION_REQUIRED]

### Task 2: One-message decision+emission pairing (origin fix 2)

Files:
- `agents/skills/maintenance/zcode.md`

- [x] zcode.md decision-first discipline sentence: replace the whole sentence from `record the decision in the state file via a Bash edit BEFORE the first primitive call` through `instead of losing the whole turn.` with, verbatim: `record the decision in the state file via a Bash edit as the message's first call, in the same assistant message that then emits the calls implementing the decided mutation per the one-recorded-mutation carve-out, so no message boundary may separate the recorded decision from its emission; when the message nonetheless ends before full emission, the durable record carries the decision to the next turn through the pending-record and record-taking rules, and the boundary is recorded in the turn output.` [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate2` run: Gates 0, 0b, 1, and 2; expect both stale Gate 2 counts at 0, the three new Gate 2 spans at 1 each, and all earlier counts unchanged; Gate 3 still RED until task 3 lands (the full block exits 1 at Gate 3) [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance one-message decision and emission pairing` [class: IMPLEMENTATION_REQUIRED]

### Task 3: In-turn recovery streak reset (origin fix 3)

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] SKILL.md failure-cap section: in the Turn-level tripwire bullet (the bullet that names the schema counter `consecutive_turn_errors`), immediately after that bullet's final sentence, insert this text as a new sentence, verbatim: A turn whose turn_error is recovered in-turn (the parked intent discharged and the carrier re-armed by a create verified per the ENABLED recognition rule and ENABLED verification) resets `consecutive_turn_errors` to 0 in the same targeted edit that records the recovery, quotes the verification in the recovery note, and the turn's Step 6 write carries the reset forward; absent the verified re-arm, the streak stands. [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md sanctioned-writer enumeration: within the existing re-arm writer-class bullet, name the recovery edit (the same targeted edit that discharges the parked intent, re-arms the carrier, and resets the streak) among that class's targeted edits, preserving the enumeration's pinned class count [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate3` run: Gates 0, 0b, 1, 2, and 3; expect both Gate 3 spans at 1 and all earlier counts unchanged; at this point the entire Validation Commands block exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance in-turn recovery resets the turn-error streak` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Suite green and final certification inputs

Files:
- none new; verification over the tree tasks 1 to 3 produced

- [x] Run the full Validation Commands block; expect `ALL VALIDATION GATES GREEN` and exit 0, with the pins suite (Gate 0b) and hygiene (Gate 5) green over the edited tree [class: REPOSITORY_TEST]
- [x] Commit: `test: maintenance guard-standdown self-healing validation green` [class: IMPLEMENTATION_REQUIRED]

## Execution record

- Executed 2026-09-25 (in-session, user directive: execute plans in urgency order; worktree branch 2026-09-25-exec-guard-standdown, squash main this commit). Tasks 0-4 done; full Validation Commands block exit 0 (Gates 0-5, pins suite, hygiene).
- Origin `docs/history/backlog/2026-09-25-guard-standdown-loop-dark-recovery.md` closed and deleted per the 2eb72237 policy (disposition folded here). One deviation: Task 1's fire-time clause reworded to reference the cadence rule's 10-minute arming margin because the pins suite pins `reset_at_epoch plus 10 minutes` to a single occurrence in zcode.md.
