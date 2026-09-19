# Plan: maintenance loop residuals: occupancy, anchors, rearm wording

Backlog origins (scope of record, six items under `docs/history/backlog/`):
`2026-09-17-maintenance-lane-occupancy-repo-scoping.md`,
`2026-09-17-maintenance-preservation-pins-discriminating-guard.md`,
`2026-09-17-maintenance-intra-payload-ordering-anchors.md`,
`2026-09-17-step0-rearm-trigger-state-first-wording.md`,
`2026-09-17-maintenance-darkness-detection-concurrent-done-race.md`,
`2026-09-17-maintenance-r5-doc-consistency-residuals.md`.
Group ledger: `docs/tmp/future-plan-prompts-2026-09-16.md`, section "P12".

## Terms

- **Lane guards (`G1e` / `G1a`)**: the Step 2 execution/authoring lane guards in `agents/skills/maintenance/SKILL.md` (below: SKILL.md).
- **Widened arm**: the catch-all arm inside `G1e`/`G1a` that classifies every remaining automation listing record; `G1a` applies the same classification symmetrically, so one text edit covers both lanes.
- **Pins suite**: `scripts/check_maintenance_pins.sh`; the mechanical invariant gate for the maintenance corpus. Exit 0 = all pins hold.
- **Negative pin**: an `expect_absent`-style check in the pins suite: rc 0 (pattern found) = fail, rc 1 (absent) = pass, rc >= 2 (grep error) = fail.
- **Rearm-on-touch**: the SKILL.md Step 0 check a touching session runs (plus the done-skill pointer line that defers to it).
- **State-first**: consult `.ai-playbook/scheduler-state.json` before any automation listing; list only after the mutation decision requires it.
- **Archived liveness plan**: `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md` (historical record of the executed liveness plan; annotation-only edits here).
- **The r5 item**: `2026-09-17-maintenance-r5-doc-consistency-residuals.md`; its numbered entries 1-20 are quoted by number below.

## Assumptions

- assume the archived liveness plan's canonical path is `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md` and every origin reference to `docs/plans/2026-09-16-maintenance-scheduler-liveness.md` resolves there; basis: on-disk find 2026-09-18 (the plan archived after its execution; top-level `docs/plans/` no longer holds it).
- assume origin 5 (darkness-detection concurrent-done race) is still accepted-by-design; basis: verified 2026-09-18 that the duplicate-parent tripwire (SKILL.md Step 2) and the Step 1 memory-note read-back adoption are present in the current text, that no launchd-based re-arm heartbeat for the maintenance loop exists on the maintenance surfaces (SKILL.md, zcode.md, prompt-templates.md, done SKILL.md, and the state-file writers; the repo's launchd-based execute-plan resume watcher, `scripts/execute_plan_resume_watcher.py`, is an authoring/execution resume carrier, not a darkness detector), and that no corpus note withdraws the acceptance; the group ledger requires this verification before folding the origin.
- assume the r5 item's 20 entries fold as: entry 15 distributed to the three origin items named inside it (finding-text restatements in Tasks 2, 3, and 4), entry 17 into Task 2, entries 18 and 19 into Task 3, and the remaining sixteen into Task 5; basis: the item's "each entry is independently foldable" note and this plan's disposition table.
- assume the pins suite remains the only mechanical test surface this plan touches (no new test files); basis: the scope lines of origins 2 and 3.
- assume schema-3 state-file semantics are untouched; the plan edits prose consistency and pins only; basis: the ledger note that schema v3 is a fresh surface with a cheap drift check, plus the pins suite's own schema-block parser (the drift check).
- assume scratch-copy RED proofs (copy a target file, inject the simulated regression, run the suite, expect the named pin to fail) are execution-time evidence recorded in task output and commit messages, never committed artifacts; basis: the fix sketches of origins 2 and 3 ("verify the new pins are RED against a scratch copy ... and GREEN on the current tree before committing").

Decision points requiring a grill: none remain.

## Gist & Examples

The liveness execution (squash a4ffa82f) left six residual classes. This plan folds all six:

1. **Repo-scope the lane-occupancy classification (origin 1, High)**: the widened arm classifies every remaining automation with no repository containment, so on a multi-repo host a foreign repository's 2h parent falls into "anything else occupies both lanes" and every repo's turns record endless D3 no-ops: silent fleet-wide dispatch starvation. Fix: one containment clause (mirror the recognition matchers), an audit of the execution-marker match, discriminating pins.
2. **Discriminating negative pins for born-GREEN preservation pins (origin 2, Low)**: two preservation pins require only spans that pre-date the r4 scoping fixes, so a regression reverting the surrounding sentence to its unscoped form keeps the suite green. Fix: `expect_absent` pins against the exact pre-r4 wordings extracted from git history.
3. **Ordering and confinement anchors (origin 3, Low)**: `SUCCESSOR DISPATCH` and the resume rule are pinned for presence and count only, so moving them past a gate they must precede, or grafting the execution-only carve-out span into the authoring blueprint, stays green. Fix: region-scoped positional pins and region-confinement assertions in the suite's python block.
4. **State-first Step 0 trigger (origin 4, Low)**: the rearm-on-touch check opens listing-first ("when the automation listing shows no ENABLED parent"), inverting the state-first design principle and paying one listing per touch. The wording is pinned in three coupled places, so the fix lands in one pass: SKILL.md sentence, suite discriminating pin plus negative pin, archived-plan deviation registration and gate-needle flip. Also folds r5 entry 17 (the zcode.md hygiene-bullet surface) and entry 15's step0 part.
5. **Darkness-detection acceptance re-affirmed, not implemented (origin 5, Low)**: verified still accepted-by-design; the plan adds a dated corpus note with the verification evidence and restates the R-5 finding text inline. No heartbeat, no lock machinery.
6. **r5 documentation-consistency sweep (origin 6)**: entries 1-14, 16, and 20 folded across SKILL.md, zcode.md, prompt-templates.md, and the archived plan, each with its anchor; entries 15, 17, 18, and 19 are folded by Tasks 2-3-4 as dispositioned above.

Concrete effect examples: after Task 1, a foreign repository's parent automation no longer occupies this repository's lanes; after Task 3, a regression that moves `SUCCESSOR DISPATCH` past the FINAL STEP line fails the suite instead of compiling a payload that chains before compacting; after Task 4, a touching session with a recorded armed parent performs zero listings where the old wording forced one.

## Design Invariants (CR Guard)

- The archived liveness plan stays a historical record: only the dated deviation note, the Validation gate 2 needle flip, and the stale-quote annotations land there; no prose rewrite of its task text.
- SKILL.md stays runtime-agnostic: no automation-primitive names may enter it (the pins suite's existing runtime-agnostic check must keep passing).
- The state file's schema-3 semantics do not change; no task edits the schema block.
- The darkness-detection race is not implemented; only its acceptance is re-affirmed with dated evidence.
- The two lanes stay independent; executions stay strictly sequential; this plan changes no lane-cap wording.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `bash scripts/check_maintenance_pins.sh` exits 0 on the executed tree, and every validation command below exits green.
- discrimination: every new negative, ordering, and confinement pin is proven RED against a scratch copy simulating exactly its regression (pre-r4 span restored, successor anchor moved past the FINAL STEP line, carve-out span grafted into the authoring blueprint, listing-first sentence restored, done-skill pointer line moved below the Step 0 heading, or the State-file schema block replaced by a later-section foreign block) and GREEN on the executed tree, with the observed outputs recorded in the task evidence.
- docs consistency: all 20 r5 entries are folded or explicitly dispositioned; the disposition table above maps every entry number to a task.

**Done when:**
- The pins suite exits 0 with the new pins present and the old needles absent.
- The Validation Commands block exits 0 end to end.
- The public-hygiene scan (facts key `public_hygiene_scan_script`) exits 0.

**Ship when:**
- Nothing external: all evidence is repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md` (annotation and gate-needle edits only; all other prose frozen)

**Tests:**
- `scripts/check_maintenance_pins.sh` (doubles as the mechanical test suite; the python blocks are the test bodies)

**Read-only pin target (no edits prescribed):**
- `agents/skills/done/SKILL.md` (Task 3 adds an ordering pin that reads it; the done-skill pointer line is prescribed unchanged)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The six origin backlog items are in scope for exactly the dated notes, finding-text restatements, and scope-line extensions their tasks prescribe, and for triage folds; the three whose paths appear in task Files lists are inventoried here explicitly:
- `docs/history/backlog/2026-09-17-step0-rearm-trigger-state-first-wording.md` (Task 2)
- `docs/history/backlog/2026-09-17-maintenance-preservation-pins-discriminating-guard.md` (Task 3)
- `docs/history/backlog/2026-09-17-maintenance-darkness-detection-concurrent-done-race.md` (Task 4)
The plan document itself (`docs/plans/2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording.md`) is in scope for triage folds.

**Freeze notes:** SKILL.md, zcode.md, and prompt-templates.md are open only in the spans their tasks name (plus folds of review findings on those spans); all other pre-existing prose in those files is frozen; a valid finding on frozen prose goes to a durable backlog item, not an in-plan fix. The pins suite is open in the sections its tasks touch (SKILL.md structure pins, the rearm-on-touch pin, the prompt-templates python block, the header comment); all other pins are frozen.

**Out of scope; reject unless plan-related:**
- `.ai-playbook/scheduler-state.json`; reason: gitignored runtime state, no task edits it.
- `agents/skills/done/SKILL.md` edits; reason: the pointer line is prescribed unchanged (read-only pin target above).
- Backlog items other than the six origins; reason: this plan covers the six named origins only.
- `docs/tmp/` buffers; reason: session scratch.

## Triage notes (execution)

- 2026-09-19 (code review r1, F1 + contract-F1): the zcode.md REFUTED-flip verdict rewrite rode commit 0c91ceff out-of-plan; no P12 task names that span, and the commit-scope contamination is recorded here rather than repaired by history rewrite. The dispatch-ladder step 2 rewrite to delete-plus-create (with its interim pointer in step 2) is owned by the open backlog item `docs/history/backlog/2026-09-19-recycling-update-flip-refuted-delete-plus-create.md`; the ladder prose stays frozen for this plan otherwise.
- 2026-09-19 (code review r1, contract-F2 plan-side slip): the directional error in the archived liveness plan's Deviation line ("the Task 4 quote above" for a quote sitting below the line) originates in this plan's Task 2 prescription, which dictated the Deviation sentence verbatim; the archived-plan copy was corrected in place (annotation-tier edit), and this note records the plan-side origin.
- 2026-09-19 (code review r2, CC-2 + R2-RISK-1, five r1 remedy deviations beyond the checked-off exact-span/verbatim prescriptions, one entry per deviation, each pointing at its owning durable record):
  1. Task 1's SKILL.md replacement span gained the not-visible fail-safe carve-out ("a prompt not visible in full is not classifiable and counts as a potential child per the not-visible fail-safe (the lane is treated as busy)") beyond the plan's prescribed exact new span; this is the r1 RISK-3 remedy, owned by lesson #387 rule (3), whose containment-trade residual names the not-visible fail-safe among the surviving coverage paths.
  2. Task 2's cannot-decide list gained the staleness escape conjunct ("a file whose own last write is older than one cadence period ...") beyond the prescribed exact opening; r1 RISK-1 remedy, owned by the step0 backlog item's "Note (2026-09-19, code review r1 RISK-1)" in `docs/history/backlog/2026-09-17-step0-rearm-trigger-state-first-wording.md`.
  3. Task 2's "everything from `The check runs on every touch` onward stays verbatim" prescription was violated by the listing-derived bookkeeping reconciliation clause inserted into the same bullet (the three bookkeeping edits apply only when the listing ran); same r1 RISK-1 remedy, same owning note.
  4. r5 entry 14's prompt-templates.md `per plan Task 2` reference was repointed to `docs/plans/completed/2026-09-13-maintenance-scheduler-skill.md` instead of the archived liveness plan the entry named; the git trace showed the 2026-09-13 plan's Task 2 prescribes the field-line annotations while the liveness plan's Task 2 is zcode.md ladder work; owned by lesson #390 (its witness records this dated deviation).
  5. r5 entry 16's tripwire single-sourcing kept the tripwire's own title-less span shape with the title conjunct explicitly not required, instead of pointing at the full Step 0 recognition rule; r1 RISK-2 remedy, owned by lesson #391.
- 2026-09-19 (code review r2, CC-1 plan-side slip): the plan's Task 5 entry-7 prescription itself supplied `armed-child-record-conflict` as the `rearm_note` definition's example; the corpus binds that string exclusively to `turn_error` (zcode.md's armed-child stand-down), so the landed SKILL.md parenthetical was reworded in the r2 address pass so it cannot read as a `rearm_note` value, and this note records the plan-side origin.
- 2026-09-19 (code review r2, TEST-R2-1, executed RED/GREEN evidence for the new pins; full outputs in the task implement logs under `docs/tmp/execute-plan/maintenance-loop-residuals-occupancy-anchors-rearm-wording/`, ephemeral; this entry is the durable summary):

  | Proof | Scratch regression injected | Observed failing output |
  |---|---|---|
  | Task 1 RED | pre-Task-1 unscoped widened-arm span restored in SKILL.md | `widened-arm classification repo-scoped`; `superseded unscoped widened-arm classification wording must be absent from SKILL.md` (exit 1) |
  | Task 2 RED | listing-first Step 0 sentence restored in SKILL.md | `step 0 rearm-on-touch check`; `superseded listing-first rearm-on-touch trigger must be absent from SKILL.md` (exit 1) |
  | Task 3 RED 1 | pre-r4 unscoped carve-out restored in zcode.md | `superseded unscoped ambiguous-outcome carve-out must be absent from zcode.md` (exit 1) |
  | Task 3 RED 2 | pre-r4 unscoped success clause restored in prompt-templates.md | `superseded unscoped success-via-existing clause must be absent from prompt-templates.md` (exit 1) |
  | Task 3 RED 3 | successor paragraph moved after the FINAL STEP line | `execution payload ordering drifted (squash merge < SUCCESSOR DISPATCH < FINAL STEP)` (exit 1) |
  | Task 3 RED 4 | execution-only carve-out span grafted into the authoring blueprint | `execution-only span left the execution inner block: beyond the re-arm duty below and the single successor-dispatch duty below` (exit 1; the presence-only pin stayed green) |
  | Task 3 RED 5 | done-skill pointer moved below the Step 0 heading | `done-skill rearm-on-touch pointer must precede the Step 0 heading` (exit 1) |
  | Task 3 schema A/B | State file json block replaced by prose + full-shape block under a later heading | Phase A (unbounded region): all hold, exit 0 (vacuous pass witnessed); Phase B (bounded region): `state schema json block missing`, exit 1 |
  | Task 6 sweep | none (observation) | validation block exit 0 `validation: all hold`; section-3 sweep rcs both observed 1 (both superseded wordings absent); no missing-file line for the done-skill target; runtime-agnostic check passed |
  | r1 address RED | recognition-rule match re-injected into the tripwire | `tripwire span shape excludes the title conjunct` (exit 1) |
  | r1 address RED | pre-Task-1 uncontained execution-child marker span restored in zcode.md | `execution-child marker repo containment`; `superseded uncontained execution-child marker wording must be absent from zcode.md` (exit 1) |
  | r1 address RED | listing-gate sentence emitted before the consult inside Step 0, positive needle kept verbatim | `step 0 must consult the state file before the listing (state-first placement)` (exit 1; the positive step-0 pin survived) |

  Every scratch regression failed exactly its named pin or assertion and only that one; every GREEN run on the edited tree exited 0 (`maintenance pins: all hold`).

## Validation Commands

```bash
set -u
fail=0
note() { echo "VALIDATION FAIL: $1"; fail=1; }

# 1. Primary gate: the pins suite, all pins hold on the executed tree.
bash scripts/check_maintenance_pins.sh || note "maintenance pins suite failed"

# 2. New positive needles, fail-closed, per file.
grep -qF 'classify its prompt only when the prompt contains the resolved repository root' agents/skills/maintenance/SKILL.md \
  || note "widened-arm repo-scoped needle missing"
grep -qF 'rearm-on-touch check: consult the scheduler state file first' agents/skills/maintenance/SKILL.md \
  || note "state-first step0 needle missing"
grep -qF 'and the resolved repository root (the relative plans-dir substring alone' agents/skills/maintenance/zcode.md \
  || note "execution-marker containment needle missing"
grep -qF 'Deviation (2026-09-18, P12)' docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md \
  || note "archived-plan deviation note missing"
grep -qF 'rearm-on-touch check: consult the scheduler state file first' docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md \
  || note "archived-plan gate needle not flipped"
grep -qF 'Historical note (2026-09-18, P12)' docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md \
  || note "archived-plan stale-quote annotation missing"

# 3. Superseded wordings stay absent; grep rc 0 = regression, rc >= 2 = tool error, only rc 1 passes.
for probe in "when the automation listing shows no ENABLED parent agents/skills/maintenance/SKILL.md" \
             "spacing window, classify its prompt: agents/skills/maintenance/SKILL.md"; do
  pat="${probe% *}"; f="${probe##* }"
  rc=0; grep -qF "$pat" "$f" || rc=$?
  if [ "$rc" -eq 0 ]; then note "superseded wording returned in $f: $pat"; fi
  if [ "$rc" -ge 2 ]; then note "grep error on $f while checking absence"; fi
done

# 4. Em-dash sweep over the actively edited files; all four measured clean at authoring (2026-09-18).
for f in agents/skills/maintenance/SKILL.md agents/skills/maintenance/zcode.md \
         agents/skills/maintenance/prompt-templates.md scripts/check_maintenance_pins.sh; do
  rc=0; rg -q "$(printf '\u2014')" "$f" || rc=$?
  if [ "$rc" -eq 0 ]; then note "em dash found in $f"; fi
  if [ "$rc" -ge 2 ]; then note "rg error on $f"; fi
done

# 5. Public-hygiene scan, anchored at the repo root.
HYGIENE="$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
if [ ! -f "$HYGIENE" ]; then note "hygiene scan script missing at $HYGIENE";
else ( cd "$(git rev-parse --show-toplevel)" && bash "$HYGIENE" ) >/dev/null 2>&1 || note "hygiene scan failed"; fi

if [ "$fail" -eq 1 ]; then exit 1; fi
echo "validation: all hold"
```

### Task 1: Repo-scope the lane-occupancy classification (origin 1)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] In SKILL.md's `G1e` widened arm, replace the opening of classification step (3) so classification applies only to repository-contained prompts (the exact new span, replacing `for each remaining automation whose fire or last-run time falls inside the spacing window, classify its prompt:` and keeping the existing classification outcomes verbatim after it): `for each remaining automation whose fire or last-run time falls inside the spacing window, classify its prompt only when the prompt contains the resolved repository root (the same containment the recognition matchers and the duplicate-parent tripwire require); a prompt without that containment occupies nothing, because a foreign repository's plan work is not this repository's lane occupant. Among contained prompts:` [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the `G1a` guard needs no parallel edit: its widened-arm text applies the lane-classification rule symmetrically, so the single edit covers both lanes; record the verifying quote in the task evidence [class: IMPLEMENTATION_REQUIRED]
- [x] In zcode.md's child-classification markers, extend the execution-child bullet to require containment (exact new span, replacing `plus a path under the resolved \`plans_dir\` (SKILL.md Configuration; default \`docs/plans/\`).`): `plus a path under the resolved \`plans_dir\` and the resolved repository root (the relative plans-dir substring alone also matches foreign repositories' prompts; the SKILL.md widened-arm containment gate applies before classification; SKILL.md Configuration; default \`docs/plans/\`).` [class: IMPLEMENTATION_REQUIRED]
- [x] Add two pins to the suite's SKILL.md structure section (RED first): a positive pin on the needle `classify its prompt only when the prompt contains the resolved repository root`, and a negative pin `expect_absent` on the superseded span `spacing window, classify its prompt:` (unique today: measured one occurrence in SKILL.md at authoring) [class: REPOSITORY_TEST]
- [x] Record the containment trade's accepted residual as one dated sentence in zcode.md's idle-attribution area: containment-scoped classification is accepted because blueprint-dispatched children always carry the filled repository root; an uncontained manually dispatched child is caught by none of the marker-gated arms (armed, fired) nor by the state-file arm (which covers only recorded children), so its surviving coverage is the discovery arm's live-session check, the not-visible fail-safe, and the treated-as-foreign disposition; and a listing that hides or truncates prompt text stays under the existing fail-safe (a prompt not visible to classification counts as a potential child and treats the lane as busy) [class: IMPLEMENTATION_REQUIRED]
- [x] RED proof: run the suite against a scratch copy of the tree where SKILL.md still carries the old span; expect both new pins to fail (positive needle missing, negative span present); record the output [class: REPOSITORY_TEST]
- [x] GREEN proof: run `bash scripts/check_maintenance_pins.sh` on the edited tree; expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: repo-scope the widened-arm lane classification (P12 origin 1)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: State-first Step 0 rearm-on-touch trigger (origin 4; r5 entries 15 part, 17)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`
- `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md`
- `docs/history/backlog/2026-09-17-step0-rearm-trigger-state-first-wording.md`

- [x] Rewrite the SKILL.md Step 0 trigger to state-first (exact new opening, replacing `rearm-on-touch check: when the automation listing shows no ENABLED parent for this repository (an automation whose title and repo-filled prompt opening match the recognition rule), consult the State file semantics`; everything from the following sentence `The check runs on every touch` onward stays verbatim): `rearm-on-touch check: consult the scheduler state file first (its recorded \`parent_automation_id\`, the pending \`children[]\` entries, and \`parent_absent_since\`), and run the automation listing only when the state file cannot decide (no recorded id, no live pending child explaining an absence, or a darkness classification that needs listing confirmation); when the listing shows no ENABLED parent for this repository (an automation whose title and repo-filled prompt opening match the recognition rule), consult the State file semantics` [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the rewritten bullet keeps the three unconditional bookkeeping edits, the Step 0 adoption guards, the runtime-without-listing inertness clause, and the child-duty exemption verbatim (nothing after the replaced opening changes); record the verifying diff in the task evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Confirm the zcode.md re-arm hygiene bullet now reads true without edits (it says the state-first shape governs the re-arm decision of the turn's Step 0; after this task that sentence is accurate, closing r5 entry 17's conflict); record the verifying quote [class: IMPLEMENTATION_REQUIRED]
- [x] Update the suite's rearm-on-touch pin (currently `pin "step 0 rearm-on-touch check" grep -qF 'rearm-on-touch check: when the automation listing shows no ENABLED parent'`) to the new needle `rearm-on-touch check: consult the scheduler state file first`, and add the negative pin `expect_absent` on the superseded span `when the automation listing shows no ENABLED parent` (unique today: measured one occurrence in SKILL.md at authoring) so the listing-first wording cannot silently return [class: REPOSITORY_TEST]
- [x] In the archived liveness plan, flip its Validation gate 2 needle (the `expect_pin "rearm-on-touch check: when the automation listing shows no ENABLED parent"` command) to the same new needle, and add directly under its Task 4 heading the dated line: `Deviation (2026-09-18, P12): the Step 0 trigger was rewritten to state-first wording (backlog 2026-09-17-step0-rearm-trigger-state-first-wording); the Task 4 quote above is historical, and this plan's gate needle was flipped to the new sentence's discriminating needle in the same commit so this plan's gate block and the pins suite never disagree.` The Task 4 quote text itself stays untouched [class: IMPLEMENTATION_REQUIRED]
- [x] In the step0 backlog item, extend the Scope line with the zcode.md hygiene-bullet surface (r5 entry 17), and add a dated note restating the DS-4 finding text inline (r5 entry 15's step0 part): the finding's consequence (one listing per touching session before the state file is consulted; the state-first invariant inverted for the touch surface) and its origin (liveness r1, deferred by the triage because three coupled surfaces had to move in one pass) [class: IMPLEMENTATION_REQUIRED]
- [x] RED proof: run the suite against a scratch copy of the tree where SKILL.md still carries the listing-first sentence; expect the updated positive pin to fail and the new negative pin to fail; record the output [class: REPOSITORY_TEST]
- [x] GREEN proof: run the suite on the edited tree; expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: state-first Step 0 rearm-on-touch trigger across coupled surfaces (P12 origin 4)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Discriminating, ordering, and confinement pins (origins 2-3; r5 entries 15 part, 18-19)

Files:
- `scripts/check_maintenance_pins.sh`
- `agents/skills/done/SKILL.md` (read-only pin target)
- `docs/history/backlog/2026-09-17-maintenance-preservation-pins-discriminating-guard.md`

- [x] Extract the two pre-r4 unscoped wordings from git history (origin 2 step 1): the versions of `agents/skills/maintenance/zcode.md` and `agents/skills/maintenance/prompt-templates.md` immediately before the liveness squash (`git show "a4ffa82f^:<path>"`), and choose per file one minimal span that contains the unscoped clause (the ambiguous-outcome carve-around `treat the child as dispatched` without the cap-shaped/listing-verified scoping; the success clause `counts as success only after one more listing confirms` without the failed-confirmation escalation route and without repo containment) and cannot appear in the current scoped text; record both exact spans in the task evidence [class: REPOSITORY_TEST]
- [x] Add one rc-aware negative pin per extracted span (origin 2 step 2), mirroring the `expect_absent` pattern already used for the superseded re-arm wording; verify each new pin RED against a scratch copy carrying the pre-r4 text (inject the extracted span, expect exactly that pin to fail) and GREEN on the current tree, before committing (origin 2 step 3) [class: REPOSITORY_TEST]
- [x] Add region-scoped ordering pins to the suite's prompt-templates python block (origin 3): within the execution inner block (between the dispatch-slice tags), assert `index("Finally squash merge to main") < index("SUCCESSOR DISPATCH") < index("FINAL STEP")`; assert `index("once the gate exits 0") < index("this is a resume run")` in the same inner block; and in `agents/skills/done/SKILL.md` assert `index("Before Step 0, in a repository that resolves the maintenance skill") < index("## Step 0")`, each with a fail-closed anchor check on the predecessor string so a broken extractor cannot pass vacuously [class: REPOSITORY_TEST]
- [x] Add confinement assertions to the same python block (origin 3 scope note): split prompt-templates.md on the blueprint headings (`## Authoring child`, `## Execution child`) and the dispatch-slice tags; assert the carve-out span `beyond the re-arm duty below and the single successor-dispatch duty below` appears only inside the execution inner block, and `this is a resume run` appears only inside the execution inner block and after the PRE-STEP end (the ordering pin's index check supplies the position half) [class: REPOSITORY_TEST]
- [x] RED proofs: in scratch copies, move the successor paragraph after the FINAL STEP line (ordering pin fails), graft the carve-out span into the authoring blueprint (confinement assertion fails), and move the done-skill pointer line below the Step 0 heading (done-skill ordering pin fails); record all three outputs [class: REPOSITORY_TEST]
- [x] Bound the schema-block regex at its end (r5 entry 18): change the search region from `s.split("## State file", 1)[1]` to `s.split("## State file", 1)[1].split("\n## ", 1)[0]` so a later section's json block can never satisfy the schema pins [class: REPOSITORY_TEST]
- [x] RED proof for the region bound: in a scratch copy of SKILL.md, replace the State file section's own json block with prose and place a full-shape schema-3 json block (every key the schema pins check) under a later `## ` heading; run the suite with the pre-change unbounded region and expect the schema pins to pass vacuously on the foreign block, then with the bounded region and expect the schema-block pin to fail; record both outputs [class: REPOSITORY_TEST]
- [x] Replace the suite's stale header comment `(review r1/r2 fix rounds)` (r5 entry 19) so the header no longer dates the pin families; keep the existing family enumeration lines below it [class: IMPLEMENTATION_REQUIRED]
- [x] In the preservation-pins backlog item, add a dated note restating the T-3 finding text inline (r5 entry 15's preservation part): the two born-GREEN pins by name, the presence-only guarantee consequence, and the origin (liveness r1, deferred by the triage; the rc-aware negative-pin mechanism existed from the r1 address pass) [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN proof: run the full suite on the edited tree; expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: discriminating, ordering, and confinement pins for the loop corpus (P12 origins 2-3)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Darkness-detection acceptance re-affirmed, not implemented (origin 5; r5 entry 15 part)

Files:
- `docs/history/backlog/2026-09-17-maintenance-darkness-detection-concurrent-done-race.md`

- [x] Re-verify the acceptance before folding (ledger instruction): the duplicate-parent tripwire with its `duplicate-parent-candidate` turn error is present in SKILL.md Step 2; the Step 1 memory-note read-back that adopts a live ENABLED recognition match is present; no launchd-based re-arm heartbeat or dedicated re-arm lock exists on the maintenance loop's surfaces (SKILL.md, zcode.md, prompt-templates.md, done SKILL.md, and the state-file writers; the repo's execute-plan resume watcher is an authoring/execution resume carrier, not a darkness detector, and is out of scope for this probe); record all three verification probes and their outputs in the task evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Add a dated corpus note to the item re-affirming accepted-by-design as of 2026-09-18 with those three probes as evidence, and restating the R-5 finding text inline (r5 entry 15's darkness part): the concurrent-done double-create window, the fail-safe aftermath (tripwire flags both lane guards, human collapses duplicates), and the rejected alternative (the launchd heartbeat deferred by the liveness plan's decision grill) [class: IMPLEMENTATION_REQUIRED]
- [x] Confirm the four corpus members (the original race plus the r2/r3/r4 notes) each still carry their accepted-family mitigation shape unchanged; record the confirming quotes [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `backlog: re-affirm darkness-detection accepted-by-design with dated evidence (P12 origin 5)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: r5 documentation-consistency sweep (origin 6; entries 1-14, 16, 20)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md`

Each entry below quotes the r5 item's numbering; every edit stays inside the span the entry names (freeze note above). Entries 15, 17, 18, and 19 are not here: they landed in Tasks 2-4.

- [x] Entry 1 (functional-adjacent): add the touch-session `rearm_note` clear on an armed-again listing to both the canonical clearer list in the `rearm_note` field paragraph and the rearm-on-touch writer class in the State file writer-classes bullet (SKILL.md State file section) [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 2: in the execution payload's successor paragraph, replace the two-clause span `the note is surfaced by the next touch session's or human read-back of the memory index, and by the next scheduler turn's survey read-back only when the loop has been re-armed by some actor` (exactly both clauses; the span ends before the final clause `which then re-runs the normal D1 decision for the target`, which stays intact) with `the note is surfaced by a human read-back of the memory index, and by the next scheduler turn's Step 1 survey read-back only when the loop has been re-armed by some actor` (the operative mechanism: touch sessions classify darkness and re-arm; they do not read the memory index) [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 3: add a third dated verdict line to zcode.md's Automation primitive verification section for the completed-record enabled-re-enable reshape shape (`enabled` false to true on a lingered completed record with `recurring` kept false), marked not yet verified live, and extend the recording-rule sentence to cover reshape shapes alongside flip directions [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 4: add a dated note to prompt-templates.md's deviations list recording that the re-arm duty's armed-child guard matches only plan-execution payloads, so armed clocked authoring payloads are invisible to it; note this is currently policy-unreachable (one authoring child at a time, dispatched idle-time without a clock) and is recorded for a future policy change; the pinned payload paragraphs are not edited [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 5: in zcode.md's dispatch ladder step 2, drop `the listing shows` from `or one naming no record the listing shows, has no update target` so the zero-listing primary path no longer reads listing-first [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 6: extend the archived plan's stale-quote annotation (entry 20 below) to cover the witness-table row 3 claim (`decision_reason records the release`), naming where the duty actually landed (SKILL.md's early authoring outcome check in Failure detection) [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 7: add the sanctioned `parent_automation_id` writes to the child and watchdog writer-class bullets (the child recipe re-arm's targeted update; the watchdog recovery's update), and broaden the `rearm_note` field paragraph's definition to cover dispatch-direction conflicts (for example `armed-child-record-conflict`), not only re-arm refusals [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 8: define `hand-off` at its first writer-class use in SKILL.md (the dispatch ladder's listing-confirm leg that hands the single record to the decided child) instead of leaving the term undefined [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 9: reword the carry-forward tail in the State file scoping note so `pending_dispatch` is no longer described as written by non-Step-6 actors (it is turn-owned; the tail should say `pending_dispatch` / `parent_absent_since` are written outside Step 6 by the turn's own earlier steps or by touch sessions), and cover the archived-plan side of the entry in the entry 20 annotation [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 10: add the missing `tmp_dir` row to SKILL.md's Configuration table (scratch directory for session manifests and validation blocks; fallback `docs/tmp/`) [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 11: verify-and-attribute, do not double-record: SKILL.md's Revisions already carries the entry `2026-09-15 (same day, review r3 fix round)` covering all six SKILL.md-facing liveness-r3 deltas (the ladder's ambiguous-create carve-out becoming operative, the watchdog's child-duty guards and cause-free own-create refusal, the six-hour idle lane horizon, the `loop-parent-missing` reader branch, the full-span recognition pin, the verified-success confirmation wording; the entry text landed with the liveness squash a4ffa82f); confirm the entry's attribution to the liveness plan, annotating in place only if it under-specifies which plan the round belongs to, so the ledger records the round exactly once [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 12: repair prompt-templates.md's deviation ledger: add the dated entries for the r2/r4-hardening paragraph amendments (armed-child guard repo containment, chain-nothing parenthetical, truthful dark-path wording), stop counting the closed punctuation entry as an open deviation, and fix the tail-fix bullet's superseded claim (the fenced body now ends with the compaction step, not the stranding note) [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 13: replace the unanchored `the same day` provenance in SKILL.md's Step 5 floor rule with a pointer at the Revisions ledger [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 14: reword the provenance pointers that cite gitignored review logs or unnamed plans: zcode.md's three `(r4 item N)` mentions (items 7, 4, and 6 across the ladder and watchdog bullets) and prompt-templates.md's `per plan Task 2` become durable references to the archived liveness plan by path [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 16: single-source the recognition rule in SKILL.md: define it once at its Step 0 first use (ENABLED automation whose title matches the recipe title, whose prompt begins with the scheduler prompt template's opening line, and whose prompt contains the resolved repository root; literals live in the runtime overlay's recipe, pinned by the suite), and make the Step 1 and duplicate-parent tripwire mentions point at that definition instead of restating three different shapes [class: IMPLEMENTATION_REQUIRED]
- [x] Entry 20: add one dated historical annotation to the archived liveness plan, opening with the exact needle `Historical note (2026-09-18, P12)` (the Validation block greps this needle), covering its five stale checkbox/invariant quotes plus the entry 6 and entry 9 plan-side residuals: the quotes are stale versus the landed r3/r4 fixes, the landed skill files are authoritative, and the plan is a historical record; place it near the plan header so a reader meets it before the task text [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: fold the r5 documentation-consistency residuals (P12 origin 6)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Full validation sweep

- [x] Run the complete Validation Commands block from the repository root; expect exit 0 with `validation: all hold` [class: REPOSITORY_TEST]
- [x] Record the observed rc of each section-3 sweep as 1 (the superseded wordings absent after Tasks 1 and 2), witnessing the sweeps' discriminating behavior rather than assuming it [class: REPOSITORY_TEST]
- [x] Confirm the pins suite output names no missing-file error for the read-only done-skill pin target, and that the suite's runtime-agnostic SKILL.md check still passes after Tasks 1, 2, and 5 [class: REPOSITORY_TEST]
- [x] Commit (only if any validation-driven fix left an uncommitted edit): `maintenance: P12 validation sweep fixes` [class: IMPLEMENTATION_REQUIRED]
