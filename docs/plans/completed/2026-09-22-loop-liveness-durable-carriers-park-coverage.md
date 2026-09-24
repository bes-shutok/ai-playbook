# Plan: loop liveness: durable carriers and park coverage

Backlog origins (scope of record): `docs/history/backlog/2026-09-21-loop-mode-durable-carrier.md`,
`docs/history/backlog/2026-09-21-successor-duty-primitive-absence-park-fallback.md`,
`docs/history/backlog/2026-09-21-watchdog-escalation-park-coverage.md`.

## Terms

- `loop_mode`: the standing loop directive field in the scheduler state file (object or null:
  mode, directive, set_at, note); landed by the state-durability execution (main 8719edff).
- `pending_rearm`: the re-arm intent record field (object or null); its paired payload copy
  derives the identity-bound filename per the field paragraph in SKILL.md's State file section.
- Park-path pairing rule: the intent record and the assembled payload copy are one paired
  write in the same targeted state edit, always before the corresponding memory note.
- Watchdog level-2 escalation: the watchdog payload's own re-arm create refusal route whose
  already-exists success verification failed (zcode.md "Watchdog backstop" bullet); distinct
  from level 1, the dispatching turn's arming refusal, which is a no-op by design.
- Sanctioned writer classes: the closed five-class list of state-file writers in SKILL.md;
  a state write without a named owner is a defect against the closedness invariant.
- Rearm kind: the `pending_rearm` payload filename form
  (`docs/tmp/future-plan-prompts-<date>-rearm.md`), owned by the field paragraph's derivation.

## Assumptions

- assume origins 1-2 substance is already landed by the state-durability execution (commit
  8719edff, archived as docs/plans/completed/2026-09-21-scheduler-maintenance-state-durability.md);
  basis: byte-level reads of the main surfaces (SKILL.md loop_mode field paragraph, Step 3
  enforcement, Step 0 self-heal, Step 6 carry-forward, pending_rearm paragraph; zcode.md recipe
  mode clause, loop-guard park, reduced-toolset note; prompt-templates.md deviation entries and
  blueprint paragraphs). Task 2 verifies each ask with grep evidence before any origin closes.
- assume the watchdog park targets only the level-2 escalation route; the level-1 arming
  refusal stays a no-op; basis: the origin's candidate fix text plus the current zcode.md level
  semantics.
- assume the watchdog's assembled payload copy is the recipe payload it attempted to create
  the parent from; basis: the same pairing semantics the child re-arm duty applies.
- assume no new state field and no schema version bump; basis: `pending_rearm` exists with its
  derivation and pairing rule; this plan adds a writer, not a field.
- assume the fix wording uses the derivation-reference form, never a bare dated path; basis:
  the r3 review-address precedent recorded in prompt-templates.md's deviation list ("Park-path
  copy identity by derivation reference").
- assume the deferred sibling docs/history/backlog/deferred/2026-09-21-loop-mode-nonenum-value-divergence.md
  stays deferred; basis: its revival condition (a witnessed invalid loop_mode value in state) is
  unmet, and the deferral sweep owns it.
Decision points requiring a grill: watchdog escalation fix option: option 1 (add the
pending_rearm park write and the writer-class membership) over option 2 (document the
escalation as deliberately note-only); source: the origin's own two-option candidate-fix menu
resolved by its driving force (the watchdog is the only out-of-lineage detector for a child
that dies before its re-arm, so a note-only escalation leaves that death unparked) plus the
standing pre-authorization; date: 2026-09-22; affected: Tasks 3-5

## Gist & Examples

The 2026-09-20/21 darkness window showed that the standing loop-mode directive survived only
as prose riding three surfaces, and that both re-arm recovery paths of that night lacked a
mechanically executable carrier. The state-durability execution (main 8719edff) landed the
durable carriers: the `loop_mode` field with its Step 3 enforcement, Step 0 self-heal, carry-forward
and recipe mode-appendix clause, and the `pending_rearm` intent record with the park-path
pairing rule wired into the child re-arm duty's escalation, the rearm loop guard's stand-down,
and the successor both-legs-fail branch. Those two backlog origins stayed open because the
durability plan's deviation entries registered the work as "not part of the backlog source
text"; this plan verifies the landed coverage row by row (Task 2) so both origins can close
honestly at archive.

One route was left unresolved by that execution's review r1 (finding F11, overflow): the
watchdog. The watchdog is the only out-of-lineage detector for a child that dies before its
re-arm. When the watchdog fires and its own re-arm create is refused with an already-exists
error whose ENABLED verification fails, the level-2 escalation writes only `rearm_note` plus
the `loop-parent-missing` memory note. A suppressed re-arm of exactly the actor the watchdog
exists to catch therefore never parks: the note is advisory, nothing reads it into a
mechanical action, and the loop stays dark until a human or a fresh interactive session
re-arms by hand. Concrete example: an execution child dies before its FIRST ACTION; the
watchdog fires, lists, sees no parent, attempts the create, and the create reports
already-exists against a record whose verification fails; today the escalation ends with
prose. After Task 4 the same escalation writes `pending_rearm` plus the assembled parent
payload copy under the rearm kind's identity-bound filename in the same targeted state edit,
before the memory note, so the next scheduler turn's Step 1 reader (whose reader arm already
exists) re-arms mechanically from the parked intent.

Task 4 also closes the sanctioned-writer open invariant the origin names: the `pending_rearm`
writers enumeration and the watchdog writer-class line gain the escalation park write, so the
write has a named owner. Task 3 lands the companion pins first and proves them RED against the
unmodified bytes; Task 4's prose flips them GREEN. The blueprint bodies in prompt-templates.md
are untouched, so the byte-identical re-arm parity pin stays green.

At the execution archive the three origins move to the backlog completed directory with
Status: done (the blueprint-owned archive step), which also resolves the two corpus-wide
straggler warnings these basenames currently earn from the archived durability plan's origins
block.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `bash scripts/check_maintenance_pins.sh` exits 0 including the three new
  needles; the escalation's park write mirrors the child duty's landed park shape (paired
  write in one targeted state edit, before the memory note, derivation-reference filename).
- closedness: the `pending_rearm` writer enumeration names the watchdog escalation and the
  watchdog writer-class line carries the park membership, so the closed writer-classes list
  stays closed.
- regression safety: no prompt-templates.md byte change (the re-arm parity pin holds); the
  level-1 no-op sentence and the recovery-clear span stay pinned and unchanged; the plan's
  own edit spans are unique in their files (simulated once, count 1 each).

**Done when:**
- All tasks checked; the pins suite exits 0 on the final bytes; `python3 scripts/plan_readiness.py`
  exits 0 on the final plan bytes; the Validation Commands block passes end to end.
- Task 2's verification rows all pass, or any failing row's missing piece was landed and
  recorded per that task's rule.
- At execution archive the three origins are dispositioned (moved with Status: done) and
  `python3 scripts/check_plan_origins_closed.py --plan <this-plan>` exits 0.

**Ship when:**
- The next live watchdog level-2 escalation parks the intent and a later Step 1 reader
  re-arms from the parked record (live-loop evidence outside this repository; prose only).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md` (Watchdog backstop bullet only; the rest of the file
  is frozen for this plan)
- `agents/skills/maintenance/SKILL.md` (the idle-time watchdog writer-class line, the
  `pending_rearm` field paragraph's Writers sentence, one new Revisions entry; the rest is
  frozen)
- `scripts/check_maintenance_pins.sh` (one new check group appended to each python heredoc;
  the rest is frozen)

**Tests:**
- none new; the pins suite is the verification surface for this plan and runs as a task gate.

**Plan-related extension**; implementation and review may change files not listed above.
Treat a finding as in scope when it is **causally related to this plan**: it implements or
completes a plan task, fixes a regression introduced by plan work, closes wiring or docs
implied by an explicit must-fix change, or contradicts a contract the plan changed. If the
link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md`; reason: blueprint bodies are deliberately
  unchanged (the watchdog is an overlay and SKILL.md surface, not a blueprint surface), and
  the byte-identical re-arm parity pin must stay green.
- `docs/history/backlog/**` origin files; reason: moved at the execution archive by the
  blueprint-owned origins-closure duty, never edited by a task.
- the in-flight cadence execution's surfaces and regions (turn-start carrier re-arm,
  `next_turn_at`, cadence rule, loop-carrier forms); reason: owned by
  docs/plans/2026-09-21-maintenance-turn-self-scheduling-cadence.md while it executes.

## Validation Commands

```bash
# Pins: full suite, exit 0 required; includes the three watchdog-park needles Task 3 adds.
bash scripts/check_maintenance_pins.sh

# Plan readiness on the final bytes (certification oracle; exit 0 required).
python3 scripts/plan_readiness.py docs/plans/2026-09-22-loop-liveness-durable-carriers-park-coverage.md

# Origins closure at closeout, before the archive commit (exit 0 required).
python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-22-loop-liveness-durable-carriers-park-coverage.md

# The three landed spans exist exactly once in their owning regions (fail-closed;
# the fragments are apostrophe-free so single-quoting is safe; the region
# extractions are fail-closed on their anchors, so a reworded file cannot pass vacuously).
python3 - <<'EOF'
import sys
s = open("agents/skills/maintenance/SKILL.md").read()
z = open("agents/skills/maintenance/zcode.md").read()
zline = [l for l in z.split("\n") if l.startswith("- Watchdog backstop:")]
if len(zline) != 1:
    sys.exit("watchdog bullet anchor not unique")
if "escalation plus the watchdog park write" not in zline[0]:
    sys.exit("watchdog escalation park span missing")
sline = [l for l in s.split("\n") if l.startswith("  - The idle-time watchdog (")]
if len(sline) != 1:
    sys.exit("watchdog writer-class anchor not unique")
if "parks `pending_rearm` with its paired payload copy" not in sline[0]:
    sys.exit("watchdog writer-class park membership missing")
prline = [l for l in s.split("\n") if l.startswith("`pending_rearm` is the re-arm intent record")]
if len(prline) != 1:
    sys.exit("pending_rearm paragraph anchor not unique")
if "and the idle-time watchdog escalation (a refused re-arm" not in prline[0]:
    sys.exit("pending_rearm writer enumeration missing")
print("landed spans ok")
EOF
```

### Task 1: drift re-cert and residual re-verification (pre-step)

Files: none (read-only; records its findings in the run log)

- [x] Re-read the three origin files at the backlog top level and confirm the watchdog item's [class: REPOSITORY_TEST]
  gap text still matches current bytes: `grep -cF "the already-exists case routes to the child duty's escalation (record" agents/skills/maintenance/zcode.md` expects 1, and
  `grep -cF "escalation plus the watchdog park write" agents/skills/maintenance/zcode.md` expects 0 (the residual is unlanded)
- [x] Re-check adjacent in-flight forces against this plan's base commit (the base sha is the [class: REPOSITORY_TEST]
  authoring branch's base at execution start): run
  `git log --oneline <base-sha>..HEAD -- agents/skills/maintenance/ scripts/check_maintenance_pins.sh`
  and inspect every landing. When the cadence execution or another plan landed and touched the
  Watchdog backstop bullet, re-anchor Task 4's edit spans on the current bytes (the level-2
  escalation parenthetical is the stable anchor in both the pre-cadence and post-cadence forms
  of the bullet) and re-run `python3 scripts/plan_readiness.py` on this plan; when a landed
  change already added the watchdog escalation park, stop this plan as already-satisfied and
  record that in the run log
- [x] When the peer reconciliation branch (the lineage without the quality-gates landing, [class: REPOSITORY_TEST]
  holding the primary checkout as of authoring) has landed on the base, re-verify the
  origins-closure tooling still exists before relying on Task 5:
  `test -f scripts/check_plan_origins_closed.py`

### Task 2: origins 1-2 landed-coverage verification rows

Files: none (read-only; every row is grep evidence against the current bytes). A failing row
means that origin is NOT fully landed: land the missing minimal piece with Task 4's edit
discipline and record it in Task 4's Revisions entry before closing that origin; never close
a failing origin.

Origin 1 (loop-mode durable carrier), all against the current bytes:

- [x] `grep -cF '`loop_mode` is the standing loop directive' agents/skills/maintenance/SKILL.md` [class: REPOSITORY_TEST]
  expects 1 (the field paragraph with the mode/directive/set_at/note shape and the withdrawal
  trace)
- [x] `grep -cF 'plus `loop_mode` and `pending_rearm`' agents/skills/maintenance/SKILL.md` [class: REPOSITORY_TEST]
  expects 1 (the Step 6 carry-forward list names both fields)
- [x] `grep -cF 'Loop-mode enforcement runs before D1, D4, and D2' agents/skills/maintenance/SKILL.md` [class: REPOSITORY_TEST]
  expects 1 (the Step 3 enforcement sentence)
- [x] `grep -cF 'Self-heal arm (added 2026-09-21, scheduler/maintenance state durability plan Task 2' agents/skills/maintenance/SKILL.md` [class: REPOSITORY_TEST]
  expects 1 (the Step 0 self-heal arm)
- [x] `grep -cF 'Mode appendix (added 2026-09-21, scheduler/maintenance state durability plan Task 2)' agents/skills/maintenance/zcode.md` [class: REPOSITORY_TEST]
  expects 1 (the recipe's mode-appendix clause)
- [x] `grep -cF 'mode appendix sourced from state' agents/skills/maintenance/prompt-templates.md` [class: REPOSITORY_TEST]
  expects 3 (the sourcing sentence in both re-arm duty paragraphs and the successor paragraph)

Origin 2 (successor-duty precheck and park fallback), all against the current bytes:

- [x] `grep -cF 'assert the session actually owns the primitives the chosen leg needs' agents/skills/maintenance/prompt-templates.md` [class: REPOSITORY_TEST]
  expects 2 (the child-side precheck in both re-arm duty paragraphs) and
  `grep -cF 'assert the session actually owns the primitive that leg needs' agents/skills/maintenance/prompt-templates.md`
  expects 1 (the successor paragraph's precheck)
- [x] `grep -cF 'write "pending_dispatch" (kind execute' agents/skills/maintenance/prompt-templates.md` [class: REPOSITORY_TEST]
  expects 1 (the both-legs-fail park, pairing rule and before-the-memory-note ordering)
- [x] `grep -cF 'when a decided re-arm is left unexecuted (a suppressed re-arm), write `pending_rearm`' agents/skills/maintenance/zcode.md` [class: REPOSITORY_TEST]
  expects 1 (the rearm-on-touch loop guard's stand-down park)
- [x] `grep -cF 'Decision-first recording: when this duty has decided to re-arm' agents/skills/maintenance/prompt-templates.md` [class: REPOSITORY_TEST]
  expects 2 (decision-first recording in both blueprints)
- [x] `grep -cF 'Reduced toolset inheritance (witnessed 2026-09-21)' agents/skills/maintenance/zcode.md` [class: REPOSITORY_TEST]
  expects 1 (the reduced-toolset drift note beside the Cron-tool boundary bullet)

### Task 3: companion pins first, expect RED

Files:
- `scripts/check_maintenance_pins.sh`

Append one check group to each python heredoc, mirroring the existing region-scoped style.
In the first heredoc (the one invoked with `python3 - "$S"`, whose content variable is `s`),
directly after the existing r5 F2 writer-class membership checks:

```python
# loop liveness durable carriers and park coverage plan: the watchdog
# escalation park coverage hole (state-durability review r1 F11). Writer-side
# needles, region-scoped per class line and per field paragraph line so the
# closed enumerations cannot drop the watchdog and stay green; the class-line
# membership reuses the watchdog_class extraction of the r5 F2 block above.
if not watchdog_class or "parks `pending_rearm` with its paired payload copy" not in watchdog_class:
    print("PIN FAIL: watchdog writer class lacks the escalation park write membership"); sys.exit(1)
pr_line = ""
for line in s.split("\n"):
    if line.startswith("`pending_rearm` is the re-arm intent record"):
        pr_line = line
        break
if not pr_line or "and the idle-time watchdog escalation (a refused re-arm" not in pr_line:
    print("PIN FAIL: pending_rearm paragraph lacks the watchdog escalation writer"); sys.exit(1)
```

In the second heredoc (the one invoked with `python3 - "$P" "$Z" "$D"`, whose zcode content
variable is `z`), directly after the existing watchdog recovery-clear span check, reusing the
`watchdog_line` variable that check defines:

```python
# loop liveness durable carriers and park coverage plan: the bullet's level-2
# escalation carries the park write (region-scoped to the one bullet line the
# block above already extracts, so a stray copy elsewhere cannot satisfy it).
if not watchdog_line or "escalation plus the watchdog park write" not in watchdog_line:
    print("PIN FAIL: watchdog bullet lacks the level-2 escalation park write span"); sys.exit(1)
```

- [x] Run `bash scripts/check_maintenance_pins.sh` → expect RED with exit non-zero and exactly [class: REPOSITORY_TEST]
  one PIN FAIL line: "watchdog writer class lacks the escalation park write membership" (the
  first new check of the first heredoc; the python heredoc exits at its first failing check and
  the suite aborts at the first heredoc whose rc is non-zero, so the other two new needles'
  failures are not observable in this run; every pre-existing pin that ran before the new block
  is green)
- [x] Prove the remaining two needles individually RED with fragment-absence greps (the needles' [class: REPOSITORY_TEST]
  python logic is exercised at GREEN by the suite and the Validation Commands block):
  `grep -cF "and the idle-time watchdog escalation (a refused re-arm" agents/skills/maintenance/SKILL.md` expects 0, and
  `grep -cF "escalation plus the watchdog park write" agents/skills/maintenance/zcode.md` expects 0
- [x] Commit: `test: add RED pins for the watchdog escalation park coverage` [class: REPOSITORY_TEST]

### Task 4: land the watchdog escalation park

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`

Four exact edits, each against the current bytes (re-anchor per Task 1 when the cadence
execution landed):

1. zcode.md, Watchdog backstop bullet, level-2 escalation parenthetical. Replace
   "the already-exists case routes to the child duty's escalation (record `rearm_note`, write
   the repo-keyed `loop-parent-missing` memory note, continue) instead of silently succeeding"
   with: "the already-exists case routes to the child duty's escalation plus the watchdog park
   write (record `rearm_note`, write `pending_rearm` plus the assembled parent payload
   copy under the rearm kind's identity-bound payload filename (derived per the `pending_rearm`
   field paragraph) in the same targeted state edit (the park-path pairing rule: intent record
   and payload copy are one paired write, always before the memory note), then write the
   repo-keyed `loop-parent-missing` memory note, continue) instead of silently succeeding".
   The level-1 no-op sentence and the recovery-clear wording stay byte-identical.
2. SKILL.md, the idle-time watchdog writer-class line. Replace "(it writes `rearm_note` on its
   level-2 escalation, clears it on recovery," with "(it writes `rearm_note` on its level-2
   escalation, parks `pending_rearm` with its paired payload copy per the park-path pairing
   rule in that same escalation's targeted state edit, clears it on recovery,".
3. SKILL.md, the `pending_rearm` field paragraph's Writers sentence. Replace "Writers: the
   child re-arm duty's escalation on a refused re-arm and the rearm loop guard's stand-down on
   a suppressed re-arm, each paired" with "Writers: the child re-arm duty's escalation on a
   refused re-arm, the rearm loop guard's stand-down on a suppressed re-arm, and the idle-time
   watchdog escalation (a refused re-arm whose already-exists verification failed), each
   paired". The Clearers sentence is unchanged (the watchdog recovery re-arm clear is already
   enumerated there).
4. SKILL.md, one new Revisions entry at the top of the Revisions section:
   "- 2026-09-22 (loop liveness: durable carriers and park coverage,
   `docs/plans/2026-09-22-loop-liveness-durable-carriers-park-coverage.md`): the idle-time
   watchdog's level-2 escalation joined the `pending_rearm` writer enumeration and the watchdog
   writer class (the escalation parks the re-arm intent with its paired payload copy per the
   park-path pairing rule in the same targeted state edit as its `rearm_note` record, before
   the `loop-parent-missing` memory note), closing the watchdog-escalation park-coverage hole
   (state-durability review r1 F11; origin
   `2026-09-21-watchdog-escalation-park-coverage.md`). Companion pins registered in the pins
   suite; no blueprint body changed, so no deviation entry." (The entry paraphrases the class
   line's pinned fragment deliberately: the Task 4 count gate on that fragment must observe
   exactly one occurrence, the writer-class line itself.)

- [x] Apply edits 1-4 exactly; `git diff --stat` shows exactly the two files [class: IMPLEMENTATION_REQUIRED]
- [x] `grep -cF "escalation plus the watchdog park write" agents/skills/maintenance/zcode.md` expects 1 [class: IMPLEMENTATION_REQUIRED]
- [x] `grep -c 'parks `pending_rearm` with its paired payload copy' agents/skills/maintenance/SKILL.md` [class: IMPLEMENTATION_REQUIRED]
  expects 1 (the writer-class line; the Revisions entry paraphrases without the pinned fragment;
  the pattern is single-quoted so the backticks stay literal to grep)
- [x] `grep -c "and the idle-time watchdog escalation (a refused re-arm" agents/skills/maintenance/SKILL.md` [class: IMPLEMENTATION_REQUIRED]
  expects 1
- [x] Level-1 no-op and recovery-clear regression guards: [class: REPOSITORY_TEST]
  `grep -cF 'and any other refusal keeps the level 1 no-op semantics' agents/skills/maintenance/zcode.md` expects 1, and
  `grep -cF 'and clears `pending_rearm` in that same recovery edit' agents/skills/maintenance/SKILL.md` expects 1
- [x] Commit: `feat: watchdog level-2 escalation parks pending_rearm with its payload copy` [class: IMPLEMENTATION_REQUIRED]

### Task 5: pins GREEN, validation block, readiness

Files: none (gates only)

- [x] Run `bash scripts/check_maintenance_pins.sh` → expect GREEN: exit 0, the three Task 3 [class: REPOSITORY_TEST]
  needles now holding, no pre-existing pin regressed
- [x] Run the full `## Validation Commands` block → expect GREEN end to end; the origins-closure [class: REPOSITORY_TEST]
  command runs last at its closeout position and this plan's own three origins satisfy it only
  after the archive step's moves, so run it in two stages: before the archive it is expected to
  report the open origins (informational), and the archive step's own gate run must exit 0
- [x] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-22-loop-liveness-durable-carriers-park-coverage.md` [class: REPOSITORY_TEST]
  → expect exit 0 on the final plan bytes

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-21-watchdog-escalation-park-coverage.md: disposition folded into 2026-09-22-loop-liveness-durable-carriers-park-coverage.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-21-loop-mode-durable-carrier.md: disposition folded into 2026-09-22-loop-liveness-durable-carriers-park-coverage.md (2026-09-25); per-item file deleted.
