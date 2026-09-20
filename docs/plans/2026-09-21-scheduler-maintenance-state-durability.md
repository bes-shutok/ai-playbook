# Plan: Scheduler/maintenance state durability (loop-mode carrier, re-arm/successor park fallback)

Backlog origins (scope of record): `docs/history/backlog/2026-09-21-loop-mode-durable-carrier.md`,
`docs/history/backlog/2026-09-21-successor-duty-primitive-absence-park-fallback.md`.

Covered elsewhere (dispositioned here, NOT implemented in this plan; each is an origin the grouping of
record names for the state-durability cluster): `2026-09-19-subagent-session-record-persistence-races.md`,
`2026-09-19-recycling-update-flip-refuted-delete-plus-create.md`, `2026-09-19-host-caveat-durability-claim-scope.md`,
`2026-09-19-transcription-cross-check-before-write.md`, `2026-09-19-hook-outcome-audit-visibility.md`,
`2026-09-19-model-selection-persist-foreign-key.md`, `2026-09-19-execute-plan-live-session-check-runtime-ambiguity.md`.
All seven are implemented by `docs/plans/2026-09-19-scheduler-ops-lanes-durability.md` (executed on branch
`2026-09-19-scheduler-ops-lanes-durability`, pending merge at authoring time).

Sequencing of record (supersedes the r1 draft's header External gate, whose slug-form polarity the r1
review measured as inverted): this plan must not run in parallel with the durability plan because they
edit the same SKILL.md state-schema, Step 6 carry-forward, and blueprint surfaces. Two mechanisms carry
the constraint, in order: (1) the landing records a dependency-chain memory note marking this plan
dependency-blocked by `2026-09-19-scheduler-ops-lanes-durability`, which the survey's dependency skip
honors and which self-heals (the plan becomes dispatchable) exactly when the blocker is no longer an open
plan anywhere under the resolved plans_dir; (2) Task 1's first checklist item is an edit-nothing
stand-down precondition that verifies the same fact at execution time and takes the sanctioned
stand-down path (no failure credit) if the blocker is still open.

Plan review: docs/reviews/2026-09-21-plan-review-scheduler-maintenance-state-durability-r*.md (latest ready round)

## Terms

- **loop_mode**: additive top-level scheduler-state field carrying a standing loop directive: `{"mode": "authoring-only|dual|execution-only", "directive": "<user wording>", "set_at": "<iso>", "note": "<carrier instructions>"}` or `null`.
- **Mode appendix**: the paragraph appended to the recurring parent's prompt that carries the directive; sourced from `loop_mode.directive` at parent creation and self-heal time.
- **pending_rearm**: additive top-level scheduler-state field `{"decided_at": "<iso>", "source": "<writer>", "note": "<short reason>"}` or `null`; the re-arm intent record a child or guard writes when it decided a parent re-arm but cannot execute it.
- **Park path**: the sanctioned recovery write pairing a state intent record (`pending_dispatch` or `pending_rearm`) with the assembled payload copy under `docs/tmp/future-plan-prompts-<date>.md`, so any later reader can dispatch mechanically.
- **Primitive precheck (child-side)**: the successor-dispatch and re-arm duties' assertion that the session owns the automation primitives the decided leg needs before selecting that leg (the child-side twin of the overlay's ladder precheck).
- **Verifiable echo**: an update-primitive call counts as landed only when the echoed record is verifiably the intended form; otherwise the caller takes delete-plus-create (the post-refutation recycling discipline).

## Assumptions

- assume the peer durability execution lands on main before this plan executes; basis: the sequencing-of-record mechanisms above (dependency-chain memory mark with self-heal, plus the Task 1 stand-down precondition), and the durable-carrier origin's own sequencing constraint.
- assume residual same-file drift at execution time is handled by the PRE-STEP re-certification (re-baseline edit targets against the current tree); basis: execution blueprint PRE-STEP contract.
- assume no new facts key is needed; basis: both fields live in the existing scheduler state file, the sanctioned durable carrier named by both origins.

Decision points requiring a grill: `pending_rearm` is a separate additive top-level field rather than a `pending_dispatch` kind; standing pre-authorization (scheduling ask, 2026-09-21); affects State file section and Step 1 reader. The mode-appendix self-heal requires a verifiable echo and falls back to delete-plus-create rather than trusting a bare update; standing pre-authorization (scheduling ask, 2026-09-21); affects Step 0. The r1 draft's slug-form External gate was replaced by the dependency-mark plus stand-down pair after the r1 review measured its polarity as inverted; standing pre-authorization (scheduling ask, 2026-09-21); affects the header sequencing-of-record block and Task 1.

## Gist & Examples

What changes: the maintenance loop's standing mode directive and its failed re-arm/successor intents stop
living in prose only. Two additive fields join the scheduler state file, the parent-creation and re-arm
paths source a mode appendix from that state, and the child duties gain primitive prechecks plus park
paths, so a loop that goes dark leaves a mechanically executable record instead of a note only.

**Before (today):** the operator tells the loop "authoring lane only, one plan at a time". The directive
rides three prose surfaces: the parent automation's prompt, scheduler-state decision_reason strings, and
agent memory notes. The parent dies overnight; a re-arm actor rebuilds the parent "exactly per the recipe";
the recipe has no mode slot, so the restored parent is pure dual-lane and the next tick may dispatch an
execution child against the standing directive with nothing but an unread memory note in its way
(witnessed 2026-09-20/21: the loop produced zero plans overnight). Separately, an execution child finishes
a clean closeout on a toolset that carries neither `CronUpdate` nor `CronDelete`/`CronCreate`; its
successor duty has two legs, both need missing primitives, both fail, and the duty ends with a
`successor-chain-failed` memory note only. The loop stays dark until a fresh interactive session happens
to run the recipe by hand the next morning (witnessed 2026-09-21, automation-636eef07).

**After (this plan):** the same directive is recorded as `loop_mode` in `.ai-playbook/scheduler-state.json`.
Step 3 reads it before the lane decisions: under `authoring-only`, D1 and D4 resolve to D3 with the mode
named in decision_reason, so a pure-prompt turn still honors the directive. When a listing shows the armed
parent's prompt lacks the appendix a non-dual mode requires, the Step 0 self-heal repairs it with a
verifiable echo (falling back to delete-plus-create per the post-refutation discipline). Every re-arm and
successor duty that decides a create first asserts it owns the primitives that leg needs, routes to the
next leg or the park path on absence, and when all legs fail writes `pending_rearm` (or `pending_dispatch`
for a successor target) plus the assembled payload under `docs/tmp/future-plan-prompts-<date>.md` in one
targeted state edit before any memory note. The next scheduler turn's Step 1 reader dispatches the parked
intent mechanically: a parked `pending_dispatch` re-enters the existing reader path; a parked
`pending_rearm` re-arms the parent per the recipe (appendix included) and clears itself.

**Edge cases:** a stale `pending_rearm` whose parent is verifiably armed is cleared without re-arming. A
child whose reshape leg lacks `CronUpdate` routes to delete-plus-create WITHOUT a listing first (the
overlay's primitive-absence arm pattern). The recipe's mode clause is inert under `dual` or a null field,
so today's behavior is preserved when no directive is standing.

## Design Invariants (CR Guard)

- Delete-plus-create is the operative recycling path on this host; the parent-to-child flip is REFUTED
  live (zcode.md "Automation primitive verification"). Any new update-primitive use (the self-heal) must
  require a verifiable echo and fall back to delete-plus-create; never reintroduce an ungated flip.
- Additive state fields never bump the schema version (schema 4, additive-no-bump precedent:
  `park_proposals`, `rate_limited_events`); the Step 6 carry-forward list must name every new field or
  the next whole-document rewrite drops it.
- SKILL.md stays runtime-agnostic: primitive names (`CronCreate`, `OffPeakCreate`, ...) appear only in
  zcode.md and the blueprint payloads, never in SKILL.md.
- Blueprint bodies keep their pinned placeholder sets and exactly-once anchor literals; every blueprint
  change registers a dated deviation-list entry in prompt-templates.md (the file's protocol).
- Sanctioned-writer closedness: new state writes join the State file's writer-classes enumeration
  explicitly; no unsanctioned writer class is created. Both new fields' writers appear in the list.
- The loop never pushes to origin and never blocks on questions (SKILL.md Invariants, unchanged).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the field paragraphs, reader arms, and enforcement sentences state the exact resolution
  semantics (`authoring-only` resolves D1 and D4 to D3; `execution-only` resolves D2 to D3; `dual` and
  `null` are inert); a reviewer can trace each behavior to one owning paragraph.
- consistency: every SKILL.md change has a dated Revisions entry; every blueprint change has a
  deviation-list entry; the State file JSON schema block, the carry-forward list, and the writer-classes
  list all name both new fields and their writers.
- testability: pins assert each new operative contract (distinctive multi-word needles, per-file
  occurrence counts where multi-site); flip-probes are simulated and recorded.
- simplicity: no new script, no new primitive, no new writer class beyond the named additions.

**Done when:**
- All tasks checked; `bash scripts/check_maintenance_pins.sh` exits 0 including the new pins.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-21-scheduler-maintenance-state-durability.md` exits 0.
- The latest review round reports ready=yes with zero unresolved blocking findings on the final digest.

**Ship when:**
- The dependency-blocked mark self-heals (the peer durability plan has archived) and the loop dispatches
  this plan normally. Human/loop-owned; prose only. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`

**Tests:**
- `scripts/check_maintenance_pins.sh`

**Plan-related extension;** findings are in scope when causally related to this plan (wiring or docs
implied by the must-fix changes, contradictions of the contracts this plan changes, pins that must move
because a pinned span moved). If the link is weak or speculative, drop as out of scope with a one-line
reason.

**Partially-in-scope files:** in `agents/skills/maintenance/SKILL.md`, only the State file section (field
paragraphs, JSON schema block, carry-forward sentence, writer-classes list), Steps 0, 1, and 3, and the
Revisions ledger are open; the failure-cap, quota-leg, and park-proposal sections are frozen (reject
findings that rewrite them). In `agents/skills/maintenance/zcode.md`, only the Recurring automation
recipe section and the Child dispatch ladder section are open; the Session compaction bullet is frozen.
In `prompt-templates.md`, only the re-arm duty paragraph, the successor-dispatch paragraph, the deviation
list, and the fenced blueprint bodies at the named insertions are open.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-19-*` durability-cluster items; reason: owned by the peer plan (see Covered elsewhere).
- `scripts/quota_window_probe.py`, `scripts/execute_plan_runtime.py`; reason: no contract change here touches them.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
S="$REPO/agents/skills/maintenance/SKILL.md"
Z="$REPO/agents/skills/maintenance/zcode.md"
P="$REPO/agents/skills/maintenance/prompt-templates.md"
PIN="$REPO/scripts/check_maintenance_pins.sh"
EMDASH="$(printf '\342\200\224')"
fail=0

# 1. loop_mode contract: schema block, field paragraph opener, carry-forward, enforcement, self-heal, reader arm
grep -qF '"loop_mode": null' "$S" || { echo "FAIL: loop_mode schema literal missing"; fail=1; }
grep -qF 'is the standing loop directive' "$S" || { echo "FAIL: loop_mode field paragraph missing"; fail=1; }
grep -qF 'carry forward the values' "$S" || { echo "FAIL: carry-forward sentence missing"; fail=1; }
grep -qF '"mode": "authoring-only|dual|execution-only"' "$S" || { echo "FAIL: mode enum missing"; fail=1; }
grep -qF 'authoring-only resolves D1 and D4 to D3' "$S" || { echo "FAIL: authoring-only enforcement missing"; fail=1; }
grep -qF 'execution-only resolves D2 to D3' "$S" || { echo "FAIL: execution-only enforcement missing"; fail=1; }
grep -qF 'verifiable echo' "$S" || { echo "FAIL: self-heal echo contract missing"; fail=1; }
# 2. pending_rearm contract: schema, field paragraph opener, reader arm, park pairing
grep -qF '"pending_rearm": null' "$S" || { echo "FAIL: pending_rearm schema missing"; fail=1; }
grep -qF 'is the re-arm intent record' "$S" || { echo "FAIL: pending_rearm paragraph missing"; fail=1; }
grep -qF 'future-plan-prompts-' "$S" || { echo "FAIL: park payload path missing from SKILL.md"; fail=1; }
# 3. recipe mode clause + toolset note (overlay); needles are prescribed verbatim in the tasks
grep -qF 'mode appendix sourced from state' "$Z" || { echo "FAIL: recipe mode clause missing"; fail=1; }
grep -qF 'reduced toolset' "$Z" || { echo "FAIL: toolset note missing"; fail=1; }
# 4. blueprint precheck + park + appendix sourcing (payload bodies; counts per prescription)
n=$(grep -oF 'assert the session actually owns' "$P" | wc -l | tr -d ' ')
[ "$n" -ge 2 ] || { echo "FAIL: precheck count $n < 2 in prompt-templates.md"; fail=1; }
grep -qF 'pending_rearm' "$P" || { echo "FAIL: blueprint park duty missing"; fail=1; }
n=$(grep -oF 'mode appendix sourced from state' "$P" | wc -l | tr -d ' ')
[ "$n" -ge 3 ] || { echo "FAIL: appendix sourcing count $n < 3 in prompt-templates.md"; fail=1; }
# 5. pins suite green (includes this plan's new pins)
bash "$PIN" || { echo "FAIL: maintenance pins do not hold"; fail=1; }
# 6. em-dash ban, portable pattern, scoped per plans rule 28: whole-file only for prompt-templates.md
#    (whose single legacy dash, deviation-list line 26, Task 3 fixes); SKILL.md and zcode.md carry legacy
#    em dashes in frozen regions (measured 2026-09-21: zcode.md line 71) and are covered by the exact
#    greps above, which the inserted lines must match verbatim.
for f in "$P"; do
  if grep -q "$EMDASH" "$f"; then echo "FAIL: em dash in $f"; fail=1; fi
done
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: loop_mode field, carry-forward, Step 3 enforcement (SKILL.md)

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] Precondition stand-down (runs before any edit): verify `docs/plans/2026-09-19-scheduler-ops-lanes-durability.md` is no longer at the plans top level; if it is still open, perform the plan-prescribed edit-nothing stand-down (write `.ai-playbook/last-stand-down.json` with keys `{"plan": <this plan path>, "reason": "peer-durability-plan-still-open", "date": <today>}` as the last action before reporting; an ad-hoc-worktree run writes it into the primary checkout) and do nothing else; the failure cap's stand-down carve-out accrues no credit [class: IMPLEMENTATION_REQUIRED]
- [ ] State file section: add the `loop_mode` field paragraph after `pending_dispatch`'s, opening with the exact span `is the standing loop directive` (backtick the field name only): additive schema-4 field, object or null, `{"mode": "authoring-only|dual|execution-only", "directive": "<user wording>", "set_at": "<iso>", "note": "<carrier instructions>"}`; `dual` and `null` are inert (today's behavior); writers: a turn or session carrying an explicit user directive, via targeted field edit; the same writer replaces the field when the directive changes or is withdrawn [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `"loop_mode": null,` to the JSON schema block between `"pending_dispatch"` and `"park_proposals"` [class: IMPLEMENTATION_REQUIRED]
- [ ] Carry-forward sentence: add `loop_mode` and (Task 4's) `pending_rearm` to the enumerated carry-forward list; the sentence keeps its existing opening span `carry forward the values` [class: IMPLEMENTATION_REQUIRED]
- [ ] Writer-classes list: comprehensive sweep so the closed list stays closed: every new state write this plan introduces gets a named owner: the `loop_mode` write/replace (a turn or session carrying an explicit user directive); the `pending_rearm` park write (the child re-arm FIRST ACTION class); the successor-dispatch class gains the both-legs-fail `pending_dispatch` park write and its payload-copy duty; the scheduler-turn class's Step 1 reader-edits enumeration gains the `pending_rearm` clear-on-dispatch and clear-on-armed-verification; and Task 2's self-heal refused-fallback `rearm_note` record joins the `rearm_note` field paragraph's writer enumeration; no unnamed write remains [class: IMPLEMENTATION_REQUIRED]
- [ ] Step 3: add the enforcement sentence before D1, containing the exact spans `authoring-only resolves D1 and D4 to D3` and `execution-only resolves D2 to D3` (keep these spans outside inline-code): the per-lane decision reads `loop_mode` before D1/D4/D2; a non-dual mode resolves the excluded lanes to D3 with the mode recorded in that lane's decision_reason; `dual` and `null` are inert [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the dated Revisions ledger entry naming this plan [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the Task 1 needles of the Validation Commands block scoped to what exists so far (stage-scoped per plans rule 16: only needles whose text this task prescribed) [class: REPOSITORY_TEST]

### Task 2: Recipe mode-appendix clause and Step 0 self-heal

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`

- [ ] zcode.md Recurring automation recipe: add the mode-appendix clause, whose operative sentence contains the exact span `mode appendix sourced from state`: when the state file's `loop_mode` is non-dual and non-null, the parent prompt template appends the mode paragraph built from the field's directive and mode, and "exactly per the recipe" includes the appendix; inert otherwise [class: IMPLEMENTATION_REQUIRED]
- [ ] SKILL.md Step 0: add the self-heal arm to the rearm-on-touch check: when a listing-derived observation shows an ENABLED recognition match whose prompt lacks the mode appendix that a non-dual `loop_mode` requires, repair with one update-primitive call changing nothing else; the repair counts as landed only on a verifiable echo (recurring true, enabled true, future nextRunAt, prompt carrying the appendix); on a garbled or non-verifiable echo, delete the record and create the parent per the recipe (appendix included), then update `parent_automation_id`; a refused fallback re-create records the refusal via a targeted state edit (`rearm_note`, joining the `rearm_note` field paragraph's writer enumeration per Task 1's sweep) and lets the existing `parent_absent_since` and staleness detectors carry recovery, mirroring the dispatch ladder's fallback refusal handling [class: IMPLEMENTATION_REQUIRED]
- [ ] Revisions ledger entry for the Step 0 addition (same pass as Task 1's entry protocol) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the recipe-clause needle (`mode appendix sourced from state` in zcode.md) and the self-heal needle (`verifiable echo` in SKILL.md) [class: REPOSITORY_TEST]

### Task 3: Blueprint legs source the mode appendix from state

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [ ] Re-arm duty paragraph (both blueprints): in the create/recycle steps, add the sentence containing the exact span `mode appendix sourced from state`: the parent is created or repaired with the recipe's mode appendix sourced from `loop_mode` (read the state file first; the recipe clause owns the shape); keep the paragraph's anchor literals intact [class: IMPLEMENTATION_REQUIRED]
- [ ] Successor-dispatch paragraph: the both-legs-fail parent re-create leg carries the same `mode appendix sourced from state` sentence (three occurrences total across the file) [class: IMPLEMENTATION_REQUIRED]
- [ ] Deviation list: register both changes as dated entries (not part of the backlog source text; the recipe clause is the single shape source); in the same pass, fix the legacy em dash on deviation-list line 26 (the stand-down report duty entry, inside this plan's open deviation-list region) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: pins suite still exits 0 (placeholder sets and anchor literals unharmed) and the appendix-sourcing count is at least 3 [class: REPOSITORY_TEST]

### Task 4: pending_rearm field, park paths, and the Step 1 reader arm

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`

- [ ] SKILL.md State file section: add the `pending_rearm` field paragraph, opening with the exact span `is the re-arm intent record` (backtick the field name only): object or null; `{"decided_at", "source", "note"}`; writers are the child re-arm duty's escalation and the rearm loop guard's stand-down, each paired with the assembled payload copy under `docs/tmp/future-plan-prompts-<date>.md` in the same targeted state edit and BEFORE the corresponding memory note; the successor both-legs-fail branch is NOT a pending_rearm writer (it parks `pending_dispatch`, its own existing field); cleared by the Step 1 reader on a successful mechanical re-arm, or when a listing verifies the parent already armed; add `"pending_rearm": null,` to the JSON schema block; extend the writer-classes list so the closed list stays closed: the child re-arm FIRST ACTION class gains the `pending_rearm` park write, and the successor-dispatch writer class (the completing execution child's class) gains the both-legs-fail `pending_dispatch` park write and its payload-copy duty [class: IMPLEMENTATION_REQUIRED]
- [ ] SKILL.md Step 1: add the pending_rearm reader arm, containing the exact span `pending_rearm` and the pairing path: when set, decide state-first; when the recipe re-arm conditions hold, re-arm per the recipe (mode appendix included per `loop_mode`), update `parent_automation_id`, and clear `pending_rearm` in the same targeted edit; when a listing shows the parent verifiably armed, clear the stale intent without re-arming; both clears join the scheduler-turn class's Step 1 reader-edits enumeration (Task 1's sweep) [class: IMPLEMENTATION_REQUIRED]
- [ ] prompt-templates.md, successor-dispatch paragraph both-legs-fail branch: before writing `successor-chain-failed`, write `pending_dispatch` (kind execute, the D1-selected successor target) plus the payload copy under `docs/tmp/future-plan-prompts-<date>.md` in the same targeted state edit; the memory note follows, it no longer stands alone [class: IMPLEMENTATION_REQUIRED]
- [ ] prompt-templates.md, re-arm duty escalation and loop guard: on a refused or suppressed re-arm, write `pending_rearm` plus the assembled parent payload copy (same pairing rule) before the `loop-parent-missing` note; decision-first recording: when the duty decides the create/adopt and any listing remains to be done, record the intent in the state file before or with that listing [class: IMPLEMENTATION_REQUIRED]
- [ ] Deviation-list entries for both blueprint changes [class: IMPLEMENTATION_REQUIRED]
- [ ] zcode.md Child dispatch ladder, Cron-tool boundary bullet: add the toolset sentence containing the exact span `reduced toolset`: automation-born children may inherit a reduced toolset (witnessed 2026-09-21: an execution child carried only the listing and idle primitives, no mutation primitives), so payload duties precheck before leg selection [class: IMPLEMENTATION_REQUIRED]
- [ ] Revisions ledger entry covering the reader arm and writer-class extension [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the pending_rearm and park needles; run → expect GREEN on the `reduced toolset` needle [class: REPOSITORY_TEST]

### Task 5: Child-side primitive precheck in successor and re-arm duties

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [ ] Successor-dispatch paragraph: before the reshape leg, add the sentence containing the exact span `assert the session actually owns`: the session asserts it actually owns the primitive that leg needs (the update primitive for reshape; delete plus create for the fallback); on absence route to the next leg or the park path WITHOUT burning listings on statically absent primitives (mirror the overlay's ladder-precheck semantics) [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-arm duty paragraph: the same `assert the session actually owns` sentence before its step 1 reshape and its step 3 create/recycle legs, routing to the escalation (now the park path from Task 4) on absence [class: IMPLEMENTATION_REQUIRED]
- [ ] Deviation-list entry for the precheck (the child-side twin of the ladder precheck, origin: successor-duty park-fallback item) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the precheck needle occurs at least twice in prompt-templates.md (once per blueprint) [class: REPOSITORY_TEST]

### Task 6: Pins suite updates and flip-probe simulation

Files:
- `scripts/check_maintenance_pins.sh`

- [ ] Add pins: the `loop_mode` schema-block literal and the `is the standing loop directive` paragraph needle in SKILL.md; the `authoring-only` and `execution-only` enforcement needles; the `verifiable echo` self-heal needle; the `pending_rearm` schema literal and the `is the re-arm intent record` paragraph needle; the Step 1 reader-arm needle (`pending_rearm` in the Step 1 region); the recipe mode-clause needle and the `reduced toolset` needle in zcode.md; the blueprint precheck count (>= 2) and appendix-sourcing count (>= 3) in prompt-templates.md; each pin follows the suite's existing need()/count helpers [class: REPOSITORY_TEST]
- [ ] Simulate each new pin's failure direction once against a mutated copy of the target file (delete the guarded sentence in a temp copy, run the pin logic, record that it fails) and record the flip-probe outcome in the commit message body [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 on the post-Task-1..5 tree [class: REPOSITORY_TEST]

### Task 7: Final validation

- [ ] Run → expect GREEN: the full Validation Commands block from a clean shell, exit 0 [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-21-scheduler-maintenance-state-durability.md` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: durable loop-mode carrier and re-arm/successor park fallback for the maintenance loop` [class: REPOSITORY_TEST]
