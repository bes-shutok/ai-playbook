# Plan: Maintenance turn self-scheduling cadence (quota-aligned turn chain)

External gate: scheduler-maintenance-loop-quality-hygiene

Backlog origin (scope of record): `docs/history/backlog/2026-09-21-maintenance-turn-self-scheduling-cadence.md` (user direction, 2026-09-21 evening: the fixed every-2-hours scheduling "shouldn't be fixed and should be decided by the maintenance itself and probably only scheduled if it sees that 5h limit is closing to resume in next 5h window").

Coordination (binding):

- The gate slug names the hygiene plan (`docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md`, landed on main as an open plan via 82f5edff); per the landed satisfaction rule the gate reads satisfied while that plan is open, and unsatisfied after it archives (the strand window and the D4 park backstop are triaged in the carve-out plan's Coordination section, same family). Every task below is additive to that plan's prescribed dispatch-discipline additions.
- Sequenced after `docs/plans/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md` (basename order plus the execution lane's sequential executions): that plan's carve-out sentences inside the shared re-arm paragraphs predate this plan's edits; every task below is additive to them and must not remove them.
- Additive to the state-durability plan (`docs/plans/2026-09-21-scheduler-maintenance-state-durability.md`, landed on main via 82f5edff, not yet executed; the `loop_mode` field, the `pending_rearm` park path): this plan's `next_turn_at` field name is distinct and collides with nothing; where both plans touch the Step 6 carry-forward enumeration or the re-arm paragraphs, the later executor applies its addition to the current bytes (union-merge precedent; the PRE-STEP re-certification is the backstop). Form-specific note: that plan's Step 0 mode-appendix self-heal and its re-arm legs consume this plan's rewritten recipe, so after both land those legs select the carrier form per the cadence rule recorded there (this plan owns the recipe; the durability plan owns the mode appendix it appends to whichever form the rule selects).

## Terms

- **Loop carrier**: the armed automation that fires scheduler turns. Two legal forms per the cadence rule: the **chain record** (a one-shot carrying the scheduler prompt template, armed for the next window's start) and the **recurring fallback** (the fixed-cadence recurring parent of today's recipe).
- **Cadence rule**: the decision that selects the carrier form and its fire time, owned by the overlay's recipe section.
- **Window start**: the next quota reset plus the arming margin (10 minutes).
- **Turn-start carrier re-arm duty**: the turn's opening liveness duty: the turn re-arms the carrier state-first before any survey or dispatch, with the creation form per the cadence rule. It replaces the fixed parent's always-armed property with an armed-at-turn-start property, so a turn that dies later in its steps still leaves the carrier armed.
- **Carrier consumption**: on a clocked-dispatch turn, the dispatch ladder's operative delete-plus-create consumes the just-armed carrier record and hands liveness to the child, whose re-arm duty restores the carrier as its FIRST ACTION (the existing record-oscillation model; there is no separate surrender case).
- **HOST CAVEAT**: the durable recycling-update rule already recorded in both re-arm duties: an echoed record that is not verifiably the intended form is a refusal routed to delete-plus-create.

## Assumptions

- assume "decided by the maintenance itself" means the scheduler turn owns the next-turn decision, not a static configuration value; basis: the origin's user direction, quoted in the backlog item.
- assume "only scheduled if it sees that 5h limit is closing to resume in next 5h window" is satisfied by the uniform one-survey-per-window rule: the carrier is armed for the next window's start, a mid-window turn never multiplies surveys, and a conditional no-schedule branch is rejected because nothing else would wake the loop when new work lands, stranding it dark; basis: this is the recommended reading recorded in the backlog item's fix item 3, accepted under the task prompt's standing pre-authorization.
- assume the worst-case reaction latency rise (from about 2 hours to about 5 hours) is priced deliberately for the quota savings; basis: the same user direction ("resume in next 5h window").
- assume the 2-hour cadence-period constants in the staleness rails stay untouched and no rail needs redefining: an armed chain record is an ENABLED recognition match, so the Step 0 listing-derived clears set `parent_absent_since` back to cleared on any touch during the gap, the listing never records an absence at all while the carrier is armed, and Task 3's human-check exemption amendment (an appended clause, never a rewrite of the existing exemption text) covers the id-first reads; basis: the recognition rule keys on title plus prompt opening plus repository root, never on `recurring`, verified against SKILL.md Step 0 and the State file section on 2026-09-21.
- assume the arming leg is delete-plus-create only: the session's own spawner record at turn start is a COMPLETED one-shot (the chain record fired to spawn the session) or the live recurring fallback record, and the one reshape shape that would apply to a completed record is the overlay's UNVERIFIED completed-record re-enable, while the observed-working retime record (2026-09-15) applied to a LIVE one-shot; basis: the overlay's Scheduling primitives and "Automation primitive verification" sections; no reshape leg is prescribed.
- assume the recognition rule survives unchanged because the chain record carries the same title and prompt template; basis: the recognition rule keys on title plus prompt opening plus repository root, never on `recurring`.
- assume arming at turn START (not turn end) is the crash-immune ordering: r2 F1 traced that a turn dying before a turn-end arming leaves the chain dark with no automated detector; arming before the survey closes that window for every death after the duty completes, and the residual pre-duty window (a death in the seconds before the duty completes) is the same exposure every child dispatch already has today, covered by the existing escalation paths; basis: r2 F1's trace and the child blueprints' existing re-arm-first precedent.
- assume the ladder's conflict arm needs the own-carrier exception: r3 F1 traced that the just-armed chain record (non-recurring, ENABLED, future `nextRunAt`) exactly matches the dispatch ladder's `armed-child-record-conflict` stand-down condition, so the letter of the operative path would stand down every clocked dispatch; the exception (the record this session's own Turn-start duty armed this turn, witnessed by the duty's targeted state edit) is narrow and mechanical; basis: r3 F1's trace against the ladder's operative step 2 text, verified 2026-09-21.
Decision points requiring a grill: carrier model (self-rescheduling one-shot chain with a recurring fallback, over re-cronning or turn-level no-op gating): resolved by the task prompt's standing pre-authorization, accept all recommended options without asking, 2026-09-21 authoring prompt; affected section: Gist & Examples and Task 1. Uniform one-survey-per-window rule over conditional scheduling: same standing pre-authorization receipt; affected section: Gist & Examples. Arming margin (10 minutes past reset): same standing pre-authorization receipt; affected section: Task 1. Turn-start arming over turn-end arming (crash immunity; the ladder consumption model instead of a surrender case): same standing pre-authorization receipt; affected section: Task 1. The ladder's own-carrier exception (consuming the carrier this session armed is the duty's hand-off, not a conflict): same standing pre-authorization receipt; affected section: Task 1. State representation (additive `next_turn_at` field written by the turn duty and the child re-arm path, no children[] kind extension): same standing pre-authorization receipt; affected section: Tasks 2 and 3. Delete-plus-create as the only arming leg (no reshape leg; the completed-record shape is unverified): same standing pre-authorization receipt; affected section: Task 1. Live-record migration step (retitle or re-form the already-armed parent at execution time): same standing pre-authorization receipt; affected section: Task 1.

## Gist & Examples

**Before (today)**: the loop is a fixed recurring parent on cron `15 */2 * * *`. At 04:15 inside an exhausted quota window it wakes, surveys, defers every dispatch (the quota leg defers past the reset), records, and dies until 06:15; roughly half of the twelve daily firings land in exhausted windows and spend budget without being able to dispatch. The reset boundary drifts (roughly 5 hours from first use), so no fixed cron can track it.

**After (this plan)**: every scheduler turn OPENS by re-arming the loop carrier state-first, exactly like the child payloads do, with the creation form per the cadence rule: a one-shot carrying the same scheduler prompt template, timed by the quota probe to the next window's start (`reset_at_epoch` plus 10 minutes) - except when the probe is unusable, where the recurring fallback is created per today's recipe. The turn then surveys, decides, and dispatches as today; on a clocked-dispatch turn the ladder consumes the just-armed carrier record (its operative delete-plus-create) and the child's FIRST ACTION re-arm restores the carrier, which is the record-oscillation model the loop already runs. Work mid-window is handled by children and their own successor chaining, not by extra surveys. No path ends with the loop dark: either the carrier is armed, or a clocked child owns the baton and re-arms per the cadence rule.

Worked example. A chain one-shot fires at 09:08 into a fresh window. The turn's opening duty runs at 09:08: it deletes the session's own spawner record (the fired chain one-shot, completed and still binding) and creates the next carrier for the next window's start (probe usable, next reset about 14:05, target 14:15), recording the carrier id into `parent_automation_id` and 14:15 into `next_turn_at` in one targeted edit. It then surveys (09:09), finds the execution lane held by an in-flight child, dispatches an authoring child through the idle-time primitive (09:10), writes state (09:12), and ends. The 14:15 carrier fires into a fresh window. A window with no dispatchable work costs exactly one turn, not six.

Worked example, clocked dispatch (carrier consumption). A turn opens at 09:08 and arms the carrier for 14:15, then selects an execution child at Step 5: the ladder's operative delete-plus-create deletes the armed carrier record (the session's own, whatever form the listing shows) and creates the child, rebinding the session's create cap. The child's FIRST ACTION re-arms the carrier per the cadence rule (14:15 again). Liveness passed from the turn to the child with no new machinery - the same oscillation the loop performs today.

Crash case. The turn dies at 09:30 mid-report (provider stop, store race): the carrier armed at 09:08 is already in place and fires at 14:15; nothing is lost except the dead turn's remaining work. Under today's fixed parent the same crash also leaves the parent armed - the redesign preserves that property instead of regressing it (r2 F1).

Failure walk. The probe reports unknown at turn start: the duty creates the recurring fallback per the recipe (after the own-spawner deletion; a create refusal indicating an ENABLED recognition match already exists counts as success only after the ENABLED verification). The arming create is cap-refused with no own lingered record to delete (an armed child from an earlier turn holds the binding): the duty takes the existing escalation only after the recurring fallback create is also attempted and refused - `no arming path may end with the loop dark` - and the escalation note names the mechanical recovery per the carve-out plan's duty.

## Design Invariants (CR Guard)

- **Never-dark**: every turn opens with the carrier re-arm, and every turn end holds liveness one of two ways - the armed carrier, or a clocked child dispatched this turn whose re-arm duty restores the carrier per the cadence rule; the recurring fallback create is attempted before any escalation; the escalation paths themselves are unchanged.
- **Crash immunity preserved**: the carrier is armed before the survey, so a turn death after the duty completes leaves the carrier armed - the property today's always-armed fixed parent provides; the residual pre-duty window (a death in the seconds before the duty completes) is the same exposure every child dispatch already has today, with the same automatic detection (none; the staleness rails are the backstop).
- **Recognition invariance**: the chain record carries the recipe's title and prompt template; the recognition rule, the duplicate-parent tripwire's span shape, the widened arm's recorded-parent exclusion, and both re-arm duties' recognition matches work without modification.
- **One carrier per repository**: at most one ENABLED recognition match at any time; the duty's delete-plus-create keeps the single-record model, and the recorded id is updated in the same edit.
- **The 2-hour cadence-period constants are untouched**: no staleness rail is redefined; the armed chain is covered by the Step 0 listing-derived clears and the amended human-check exemption.
- **Additive to prior plans**: the carve-out sentences and the hygiene plan's prescribed additions are never rewritten or deleted.
- **No em-dashes in prescribed text**: the exact-needle greps guard the insertions; the edited files carry legacy em-dashes in frozen regions (measured 2026-09-21: one in the zcode.md Context measurement primitive's Compaction bullet, one in prompt-templates.md's deviation list), so no whole-file sweep is prescribed.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the cadence rule selects the chain form exactly when the probe is usable and the fallback otherwise; dedicated needles pin the branches, the margin, and the duty's state-first ordering.
- liveness (never-dark and crash-immune): dedicated needles pin the fallback-before-escalation sentence and the duty-before-survey ordering; the drills walk the usable, unusable, and carrier-consumption paths and record that liveness holds on every path.
- safety (no duplicate carriers): the duty reuses the witnessed delete-plus-create mechanics and the child duty's own state-first steps; the recognition invariance is pinned by the unchanged recognition-span counts in the pins suite.
- maintainability: every new span carries a count-gated pin added in the SAME task as the text it pins (the pins suite is green at every task boundary); the blueprint parenthetical is count-gated at exactly 2 (byte parity); superseded literals are frozen absent with recorded origins.

**Done when:**

- All tasks checked; the Validation Commands block exits 0 on the post-task tree.
- `bash scripts/check_maintenance_pins.sh` exits 0 including the reconciled title pin and the new cadence pins.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-21-maintenance-turn-self-scheduling-cadence.md` exits 0.
- The arming drills have been walked on both probe fixtures plus the carrier-consumption path and the three outcomes recorded in the execution task log (docs/tmp is transient by design; the durable witnesses are the two checks below).

**Ship when:**

- A full window with no dispatchable work costs one scheduler turn, observed over at least two quota windows of loop telemetry (state files), not by this repository's tests. Loop-owned; prose only. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

**Tests:**

- `scripts/check_maintenance_pins.sh`

**Partially-in-scope files:** in `zcode.md`, only the Scheduling primitives section's first bullet, the recipe section's Title and Cadence bullets, the new Turn-start carrier re-arm duty bullet, the watchdog bullet's re-arm verb phrase, and the dispatch ladder's step 2 conflict-arm sentence are open. In `agents/skills/maintenance/SKILL.md`, only Step 0's new lead bullet, the State file JSON block's single added line, the carry-forward enumeration, the scheduler-turn writer-classes list, the `parent_automation_id` and the new `next_turn_at` field paragraphs, the human-check sentence's appended exemption clause, the `parent_absent_since` paragraph's closing sentence, and the Revisions ledger entry are open. In `prompt-templates.md`, only step (1)'s form parenthetical inside each of the two FIRST ACTION re-arm paragraphs is open; the paragraphs stay byte-identical to each other. In the pins suite, only the reconciled title and cadence pins, the new cadence pins added per task, and the freeze-literal origin notes are open. Everything else is frozen.

**Plan-related extension;** findings are in scope when causally related to this plan.

**Out of scope; reject unless plan-related:**

- The blueprint bodies beyond the named parenthetical; reason: the payloads' re-arm escalation and chaining text is owned by prior plans and the byte-parity pin.
- The dispatch-discipline bullet; reason: owned by the hygiene plan (suppression additions) and the carve-out plan (carve-out sentences); this plan only reads both as frozen context.
- `scripts/quota_window_probe.py`; reason: the in-flight quota-aware sibling owns it.
- Pre-existing em-dashes in the edited files (measured 2026-09-21: one in the zcode.md Context measurement primitive's Compaction bullet, one in prompt-templates.md's deviation list); reason: frozen regions; the insertions are covered by the exact-needle greps.

## Validation Commands

First executed at authoring time against the pre-task tree (2026-09-21, post-rebase bytes, r4 fold): gates 1 through 7 and 9 through 14 are RED (the duty, rule, wiring, and amendment text does not exist yet; gate 9's expect-absent fires because the superseded title literal is still present), and gates 8, 15, 16, and 17 are GREEN (the fallback-cadence literal and the placeholder count are pre-Task constants, the origin item exists, the pins suite holds). The FIRST failing gate is gate 1, exit 1. The gates flip exactly when Tasks 1 through 3 land.

```bash
REPO="$(git rev-parse --show-toplevel)"
Z="$REPO/agents/skills/maintenance/zcode.md"
S="$REPO/agents/skills/maintenance/SKILL.md"
P="$REPO/agents/skills/maintenance/prompt-templates.md"
PIN="$REPO/scripts/check_maintenance_pins.sh"
fail=0
for f in "$Z" "$S" "$P" "$PIN"; do
  [ -f "$f" ] || { echo "FAIL: missing $f"; fail=1; }
done
expect_absent() { # expect_absent <file> <pattern>: rc 0 = present (fail), rc >= 2 = grep error (fail), rc 1 = pass
  out="$(grep -oF -- "$2" "$1" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden span present in $1: $2"; fail=1
  elif [ "$rc" -ge 2 ]; then echo "FAIL: grep error on $1 while checking absence"; fail=1; fi
}
count() { grep -oF -- "$2" "$1" 2>/dev/null | wc -l | tr -d ' '; }
# 1. Loop-carrier bullet replaces the recurring-parent bullet
n=$(count "$Z" 'Loop carrier: the armed automation that fires scheduler turns')
[ "$n" -eq 1 ] || { echo "FAIL: loop-carrier bullet needle count $n != 1"; fail=1; }
# 2. The cadence rule's chain branch
n=$(count "$Z" "the carrier is a one-shot carrying this recipe's title and prompt template")
[ "$n" -eq 1 ] || { echo "FAIL: cadence-rule chain span count $n != 1"; fail=1; }
# 3. The arming margin
n=$(count "$Z" 'reset_at_epoch plus 10 minutes')
[ "$n" -eq 1 ] || { echo "FAIL: arming margin span count $n != 1"; fail=1; }
# 4. Never-dark: the fallback before escalation
n=$(count "$Z" 'attempt the recurring fallback create per the recipe before escalating')
[ "$n" -eq 1 ] || { echo "FAIL: never-dark span count $n != 1"; fail=1; }
# 5. The Turn-start carrier re-arm duty bullet (zcode) and its state-first reference
n=$(count "$Z" 'Turn-start carrier re-arm duty')
[ "$n" -eq 1 ] || { echo "FAIL: turn-start duty anchor count $n != 1 in zcode.md"; fail=1; }
n=$(count "$Z" 'the same state-first re-arm duty the child blueprints carry as their FIRST ACTION')
[ "$n" -eq 1 ] || { echo "FAIL: state-first reference span count $n != 1"; fail=1; }
# 6. The own-spawner deletion covers both spawner forms
n=$(count "$Z" 'or the live recurring fallback record this session spawned from')
[ "$n" -eq 1 ] || { echo "FAIL: spawner-form span count $n != 1"; fail=1; }
# 7. The ladder's own-carrier exception (the consumption hand-off; worded so it does not embed gate 5's needle)
n=$(count "$Z" "unless it is the carrier this session's turn-start duty armed this turn")
[ "$n" -eq 1 ] || { echo "FAIL: ladder exception span count $n != 1"; fail=1; }
# 8. The fallback cadence literal survives exactly once (the never-dark fallback)
n=$(count "$Z" '15 */2 * * *')
[ "$n" -eq 1 ] || { echo "FAIL: fallback cadence literal count $n != 1"; fail=1; }
# 9. Title superseded: new literal once, old literal absent
n=$(count "$Z" 'Title: `Maintenance scheduler turn`')
[ "$n" -eq 1 ] || { echo "FAIL: new title literal count $n != 1"; fail=1; }
expect_absent "$Z" 'Maintenance scheduler turn (every 2 hours)'
# 10. Blueprint form parenthetical: exactly 2 (byte parity)
n=$(count "$P" "in the form the recipe's cadence rule selects")
[ "$n" -eq 2 ] || { echo "FAIL: blueprint parenthetical count $n != 2 (byte parity)"; fail=1; }
# 11. Blueprint next_turn_at writer: exactly 2 (byte parity)
n=$(count "$P" 'record the armed carrier'"'"'s fire time into "next_turn_at"')
[ "$n" -eq 2 ] || { echo "FAIL: blueprint next_turn_at writer count $n != 2 (byte parity)"; fail=1; }
# 12. Watchdog re-arm verb follows the cadence rule
n=$(count "$Z" "re-arms the carrier per the recipe's cadence rule")
[ "$n" -eq 1 ] || { echo "FAIL: watchdog cadence wording count $n != 1"; fail=1; }
# 13. SKILL.md wiring: Step 0 duty, schema line, human-check exemption, carrier wording
n=$(count "$S" "the runtime overlay's Turn-start carrier re-arm duty")
[ "$n" -eq 1 ] || { echo "FAIL: Step 0 arming bullet missing"; fail=1; }
n=$(count "$S" '"next_turn_at": null,')
[ "$n" -eq 1 ] || { echo "FAIL: next_turn_at schema line count $n != 1"; fail=1; }
n=$(count "$S" 'in the future and the recorded `parent_automation_id` is ENABLED')
[ "$n" -eq 1 ] || { echo "FAIL: human-check chain exemption missing"; fail=1; }
n=$(count "$S" "the loop carrier automation's id")
[ "$n" -eq 1 ] || { echo "FAIL: parent_automation_id carrier wording missing"; fail=1; }
# 14. The ledger entry names this plan
n=$(count "$S" 'maintenance-turn-self-scheduling-cadence')
[ "$n" -eq 1 ] || { echo "FAIL: Revisions ledger entry missing"; fail=1; }
# 15. Blueprint placeholder integrity: the Task 2 replacement preserves the file's {REPO_ROOT} count
n=$(count "$P" '{REPO_ROOT}')
[ "$n" -eq 6 ] || { echo "FAIL: REPO_ROOT placeholder count $n != 6 (the count measured on the pre-Task-2 tree, 2026-09-21; the parenthetical replacement preserves it)"; fail=1; }
# 16. The backlog origin exists and stays open until completion
test -f "$REPO/docs/history/backlog/2026-09-21-maintenance-turn-self-scheduling-cadence.md" || { echo "FAIL: backlog origin missing"; fail=1; }
# 17. Pins suite green (reconciled title pin plus new cadence pins included)
bash "$PIN" || { echo "FAIL: maintenance pins do not hold"; fail=1; }
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: Overlay cadence rule, title, Turn-start carrier re-arm duty, and their pins

Files:
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Scheduling primitives, first bullet: replace the "Recurring parent" bullet with the loop-carrier bullet (exact span `Loop carrier: the armed automation that fires scheduler turns`; the two forms named per the cadence rule; one carrier per repository) [class: IMPLEMENTATION_REQUIRED]
- [ ] Recipe section, Title bullet: `- Title: \`Maintenance scheduler turn\`` (the superseded cadence parenthetical is deleted; the recognition title becomes form-independent; the superseding origin is this plan) [class: IMPLEMENTATION_REQUIRED]
- [ ] Recipe section, Cadence bullet: replace the fixed-cadence bullet with the cadence rule (exact spans `the carrier is a one-shot carrying this recipe's title and prompt template` on the probe-usable branch, `reset_at_epoch plus 10 minutes` as the window-start margin, and the never-dark fallback branch keeping `15 */2 * * *` as the recurring fallback cadence with the exact span `no arming path may end with the loop dark`) [class: IMPLEMENTATION_REQUIRED]
- [ ] Recipe section, new bullet after Re-arm hygiene: the Turn-start carrier re-arm duty, opening with the exact span `the same state-first re-arm duty the child blueprints carry as their FIRST ACTION` (the duty in agents/skills/maintenance/prompt-templates.md: consult the state file first, list at most once only when the state cannot decide, delete your own spawner record `whatever its form (a lingered completed one-shot, or the live recurring fallback record this session spawned from)` before a cap-refused create, and treat an already-exists refusal as success only after the ENABLED verification), with the creation form per the cadence rule and the duty's final targeted edit recording the fresh carrier id into `parent_automation_id` and the armed fire time into `next_turn_at` (null when nothing could be armed); the duty runs `attempt the recurring fallback create per the recipe before escalating` on any non-success path; and the consumption sentence: when this turn later dispatches a clocked child, the dispatch ladder's operative delete-plus-create consumes the just-armed carrier record and the child's re-arm duty restores the carrier per the cadence rule as its FIRST ACTION (the existing record-oscillation model; no separate turn-end duty exists) [class: IMPLEMENTATION_REQUIRED]
- [ ] Watchdog bullet: replace "re-creates the parent per the recipe" with the exact span `re-arms the carrier per the recipe's cadence rule` (one occurrence; the level-1/level-2 refusal semantics are unchanged) [class: IMPLEMENTATION_REQUIRED]
- [ ] Child dispatch ladder, step 2 conflict arm: extend the armed-child-record-conflict sentence with the own-carrier exception (exact span `unless it is the carrier this session's turn-start duty armed this turn`): a non-recurring ENABLED record with a future `nextRunAt` that is the carrier this session's duty armed this turn (the duty's targeted state edit is on record) is consumed by the operative delete-plus-create as that duty's designed hand-off; any other actor's live child still takes the `armed-child-record-conflict` stand-down unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Live-record migration (execution-time step, recorded in the task log): when an ENABLED automation matching the tripwire span shape (the old scheduler prompt opening plus the resolved repository root) but not the new recognition title exists, retime and retitle it per the cadence rule with one update-primitive call under the HOST CAVEAT (an unverifiable echo routes to delete-plus-create); record the migration in decision_reason; the duplicate-parent tripwire is the backstop if the migration is skipped [class: IMPLEMENTATION_REQUIRED]
- [ ] Same commit, pins suite (same-edit reconciliation per the freeze-literal protocol): swap the title pin to `Title: \`Maintenance scheduler turn\`` and freeze the old literal absent from zcode.md (expect_absent) with the freeze-literal origin note recording this plan as the superseding origin, AND update the python block's title-count assertion (its `z.count("Maintenance scheduler turn (every 2 hours)")` check) to the new literal in the same edit; rescope the cadence pin description to the fallback cadence (`15 */2 * * *`, exactly once); add count-gated pins for the new zcode spans (the loop-carrier bullet, the cadence-rule chain branch, the arming margin, the never-dark span, the turn-start duty anchor, the state-first reference, the spawner-form span, the ladder-exception span, the watchdog wording); simulate each changed or new pin's failure direction once against a mutated temp copy and record the flips in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN on Validation Commands gates 1 through 9, 12, and 17 and on `bash scripts/check_maintenance_pins.sh` (the suite is green at this boundary with the reconciled pins); gates 10 and 11 stay RED (blueprint pending), gates 13 and 14 stay RED (SKILL.md pending): expect the validation block exit 1 listing exactly those lines [class: REPOSITORY_TEST]
- [ ] Commit: `feat: quota-aligned cadence rule, turn-start carrier re-arm, and pin reconciliation in the overlay` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Blueprint re-arm duties point at the cadence rule (byte parity)

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [ ] In BOTH FIRST ACTION re-arm paragraphs, replace the full form parenthetical `(its title, its cadence cron, recurring true, enabled true, its prompt template with {REPO_ROOT} filled)` (byte-exact; verified 2026-09-21) with `(its title and prompt template, in the form the recipe's cadence rule selects: the chained one-shot at the next window's start when the probe is usable, otherwise the recurring fallback; enabled true, its prompt template with {REPO_ROOT} filled)`; the replacement preserves the `{REPO_ROOT}` placeholder (gate 15's count), the two paragraphs remain byte-identical (the parity pin), the HOST CAVEAT sentence inside each paragraph must not change, and no other line of either blueprint may change [class: IMPLEMENTATION_REQUIRED]
- [ ] In BOTH FIRST ACTION re-arm paragraphs, step (3)'s closing `then update "parent_automation_id" as a targeted field edit` becomes `then update "parent_automation_id" and record the armed carrier's fire time into "next_turn_at" as one targeted field edit` (identical in both paragraphs, byte parity holds; this gives the child-re-arm path its `next_turn_at` writer, so the field never goes stale during routine past-reset gaps) [class: IMPLEMENTATION_REQUIRED]
- [ ] Same commit, pins suite: add the blueprint parenthetical pin (count equals 2, byte parity) and the next_turn_at writer pin (the span `record the armed carrier's fire time into "next_turn_at"` count equals 2), each with its freeze-literal origin note; simulate each pin's failure direction once against a temp copy and record the flips in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN on Validation Commands gates 10, 11, and 15 and on `bash scripts/check_maintenance_pins.sh`; gates 13 and 14 stay RED (SKILL.md pending): expect the validation block exit 1 listing exactly those lines [class: REPOSITORY_TEST]
- [ ] Commit: `feat: re-arm duties select the carrier form per the cadence rule (byte parity)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: SKILL.md wiring, state representation, and their pins

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Step 0, new lead bullet before the rearm-on-touch bullet: turn-start carrier re-arm runs `the runtime overlay's Turn-start carrier re-arm duty` before the survey; a turn arriving to classified darkness arms per the same cadence rule, superseding the rearm-on-touch check's re-arm leg for the turn itself (the check's listing-derived bookkeeping edits and its child-duty exemption are unchanged) [class: IMPLEMENTATION_REQUIRED]
- [ ] State file schema JSON: add `"next_turn_at": null,` directly after the `parent_absent_since` line (additive under schema 4, no version bump) [class: IMPLEMENTATION_REQUIRED]
- [ ] State file prose: add the `next_turn_at` field paragraph (the armed carrier's fire time, written by the Turn-start carrier re-arm duty AND by the child re-arm duty's final targeted edit, both named so the child-re-arm path's writer is sanctioned; carried forward by the Step 6 rewrite, null when nothing was armed); add `next_turn_at` to the Step 6 carry-forward enumeration; add the arming edits to the scheduler-turn writer-classes list [class: IMPLEMENTATION_REQUIRED]
- [ ] `parent_automation_id` field paragraph: reword to `the loop carrier automation's id` (the chained one-shot or the recurring fallback record; the form is the cadence rule's); the exclusion, fallback, and self-heal pointer sentence is unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Human check sentence: APPEND to the exemption list (never rewrite the existing exemption text) the armed chain clause with the exact span `in the future and the recorded \`parent_automation_id\` is ENABLED`; `parent_absent_since` paragraph: add the closing sentence naming the armed chain record `the expected inter-turn state, not darkness` [class: IMPLEMENTATION_REQUIRED]
- [ ] Revisions ledger: add the 2026-09-21 entry naming this plan and the cadence change (the schema stays 4, additive-field precedent) [class: IMPLEMENTATION_REQUIRED]
- [ ] Same commit, pins suite: add count-gated pins for the SKILL.md spans (the Step 0 duty bullet, the schema line, the human-check exemption, the carrier wording, and the ledger span) with their freeze-literal origin notes; simulate each pin's failure direction once against a mutated temp copy and record the flips in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN on Validation Commands gates 13 and 14 and the full block (all gates green at this boundary) and on `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [ ] Commit: `feat: wire the turn-start carrier re-arm into the scheduler skill and state` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Arming drills and final validation

- [ ] Arming drill, usable-probe fixture: with a fixture probe report (usable window, `reset_at_epoch` about 90 minutes out) and a fixture completed spawner record, walk the Turn-start carrier re-arm duty against a temp copy of the overlay text, and record in the execution task log: the spawner record deleted first, exactly one carrier created at reset plus 10 minutes carrying the recipe title and prompt template with `recurring: false`, `parent_automation_id` and `next_turn_at` recorded in one edit; no live automation call is made [class: REPOSITORY_TEST]
- [ ] Arming drill, carrier-consumption path: with the same fixture plus a simulated clocked dispatch, walk the ladder's delete-plus-create against the just-armed carrier and the child duty's FIRST ACTION re-arm, and record that liveness passes from the turn to the child with no gap and no escalation [class: REPOSITORY_TEST]
- [ ] Arming drill, unusable-probe fixture: with a status-unknown fixture report, record that the recurring fallback is created instead and no chain record exists [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: full Validation Commands block, exit 0 [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-21-maintenance-turn-self-scheduling-cadence.md` exits 0 [class: REPOSITORY_TEST]
