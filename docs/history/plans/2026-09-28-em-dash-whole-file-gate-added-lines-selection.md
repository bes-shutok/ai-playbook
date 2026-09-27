# Plan: Em-dash gate mode selection and maintenance skill de-em-dash

Backlog origin: docs/history/backlog/2026-09-27-em-dash-whole-file-mode-frozen-span-trip.md
Driving force: efficiency + simplicity
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-em-dash-whole-file-gate-added-lines-selection-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make the em-dash gates bind "no em dashes in edited text" instead of "no em dashes anywhere in a file that was edited", and clear the standing violations in the maintenance skill so whole-file gating works there again.

- An executor task that edits a file carrying known pre-existing committed em dashes passes its validation gate when its own added lines are clean, instead of structurally failing on lines its plan froze.
- The done skill's pre-commit em-dash gate passes unattended runs whose added lines are clean, reporting pre-existing violations in a machine-readable baseline line instead of stalling on the user-adjudication path.
- agents/skills/maintenance/SKILL.md carries zero em dashes, so the most frequently loop-edited skill file becomes whole-file-clean and its tasks stop tripping the gate.
- No pinned literal breaks: the maintenance pins suite exits 0 before and after the change.

## Terms

- **Whole-file modes**: the `file` and `touched` subcommands of `scripts/check-no-em-dash.sh`; each scans every prose line of the selected files and fails on any em dash (U+2014) anywhere in the file.
- **added-lines mode**: the `added-lines --base REF` subcommand; scans only the lines a git diff adds against the base ref, so it binds "the edit introduced no em dashes" regardless of pre-existing committed lines.
- **Pre-existing violation**: an em dash already committed on a line a task does not edit and cannot edit (frozen span, pinned writer-class line).
- **Pins suite**: `scripts/check_maintenance_pins.sh`, which count-gates exact literals in the maintenance skill family.

## Assumptions

- assume remedy (b) mode-selection guidance rather than remedy (a) script exempt-baseline affordance; basis: the origin item names both options; the authoring survey found twenty or more files carrying committed em dashes corpus-wide, so a per-violation exempt-baseline affordance would be standing mechanism with baseline-rot risk, while the shipped added-lines mode plus one written selection rule covers the general case; the repo priority profile ranks simplicity.
- assume the origin item's pending decision resolves to the de-em-dash pass, not to sanctioning the four lines as an exempt baseline; basis: all six dashes are mechanical appositive punctuation replaceable without meaning loss, and the pins suite carries no em-dash bytes, so no pinned literal spans a replaced dash (both checked at authoring against main 07885e0f).
- assume the done-gate fallback must be deterministic rather than judgment-based; basis: the done gate is standing unattended machinery whose current remedy path stops for user adjudication, which stalls unattended runs; the origin item witnessed the added-lines mode as the working remedy.
Decision points requiring a grill: remedy = guidance selection rule over script baseline affordance; source: origin item expected option (b) plus authoring corpus survey, 2026-09-28, Assumptions and Gist; the item's pending decision = de-em-dash pass over the four lines; source: origin item pending-decision second arm plus pins-suite em-dash survey, 2026-09-28, Task 1; done-gate fallback shape = deterministic two-step probe; source: standing unattended pre-authorization plus origin item observed remedy, 2026-09-28, Task 2

## Gist & Examples

TLDR: gate selection gains a written rule (added-lines for files with pre-existing violations) and the done gate gains a deterministic fallback, because whole-file modes made every editing task trip on lines its plan froze; the maintenance skill's six dashes are removed so the rule and the file agree.

**Before (today).** An execute-plan task must edit `agents/skills/maintenance/SKILL.md` (witnessed in the deferred-residual-dispositions run, 2026-09-27). The file carries committed em dashes on four lines inside spans the plan froze (some sit on pinned writer-class lines), so the task cannot remove them. The plan's Validation block runs the whole-file form `bash scripts/check-no-em-dash.sh touched`; it exits 1 reporting the pre-existing lines even though the task's added lines carry zero em dashes, and `added-lines` on the same file exits 0. The same structure bites the done skill's pre-commit em-dash gate: it runs the whole-file `touched` form over touched prose, its fix guidance sends pre-existing-line failures to the stop-and-adjudicate path, and an unattended run stalls.

**After (this plan).** The plans skill's Validation authoring rules state the selection rule: whole-file modes are for files the plan leaves whole-file clean; a file whose committed bytes carry known pre-existing violations in frozen spans is gated with `added-lines --base REF` over the prescribed insertions. The done gate keeps `touched` as its primary probe and gains a deterministic fallback: untracked hits fail (new prose must be clean), tracked hits cross-check `added-lines --base HEAD`, clean added lines pass with the pre-existing hits reported as `pre-existing (known-violation baseline): <path>:<line>` rows (one row per hitting file, the first violating line, matching the whole-file probe's reporting shape), dirty added lines still fail. And the maintenance skill's six appositive dashes are reworded to colon or comma punctuation, so the loop's most-edited file stops carrying the standing violation at all.

**Edge cases.** The added-lines mode scans tracked diff lines only, so an untracked new prose file is invisible to it; the fallback therefore fails untracked hits outright (a new file has no pre-existing lines, so whole-file cleanliness is the honest property for it). The added-lines default base is HEAD, which gates working-tree insertions at commit time; re-gating other runs' already-committed history stays out of scope, while this plan's G6 run passes an explicit merge-base, the sanctioned one-shot exception that scans exactly this run's own committed insertions. The corpus carries em dashes in twenty or more other files (agterm, doc-hierarchy, tdd-guide, the maintenance runtime overlay, and others); their future edits select added-lines through the new rule, and a corpus-wide de-em-dash pass remains a separate decision this plan deliberately does not take.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the done-gate fallback passes exactly when the run's added lines are clean and every whole-file hit is a tracked pre-existing line; untracked-prose hits and dirty added-line hits still fail (four canaries prove all three directions plus the no-short-circuit combination).
- compatibility: the maintenance pins suite exits 0 before and after the reword; no pinned literal changes.
- maintainability: one written selection rule and one deterministic fallback; no baseline file, no new script surface, no new flag.

**Done when:**
- `bash scripts/check-no-em-dash.sh file agents/skills/maintenance/SKILL.md` exits 0.
- The four canary tests exist and pass, and the full lib suite passes via the test venv.
- The done skill's gate clause and fix bullet name the fallback and the baseline-report marker.
- The plans skill's rules 28 and 29 carry the selection rule.
- All Validation Commands below exit 0.

**Ship when:**
- None as a release gate; all criteria are repository-verifiable. Runtime-home copies of `done_sweep_gates_lib.py` propagate to other checkouts through the existing vendored sync and release flow (operations follow-up, prose only; no plan task).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (only the six dash spans on the four lines named in Task 1; all other lines in this file are frozen; reject any review finding that touches them)
- `scripts/done_sweep_gates_lib.py` (only the `gate_em_dash_scan` function; all other functions are frozen)
- `agents/skills/done/SKILL.md` (only the em-dash-scan clause of the gates-order paragraph and the em-dash-scan fix-guidance bullet; all other lines are frozen)
- `agents/skills/plans/SKILL.md` (only the rule 28 body and the rule 29 opening sentence; all other rules and lines are frozen)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(new canaries plus the fixture helpers they need; existing tests are frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/zcode.md` and every other em-dash-carrying file in the corpus; reason: the origin item scopes the de-em-dash pass to `agents/skills/maintenance/SKILL.md`, and the guidance amendment already routes their future edits to added-lines; a corpus-wide pass is a separate decision.
- `scripts/check-no-em-dash.sh`; reason: the scanner's modes already behave as this plan requires; only their selection changes.
- Any exempt-baseline affordance in the scanner; reason: rejected at authoring (see Assumptions).

## Validation Commands

Stage note: G1 and G2 are baseline-proofed at authoring against main 07885e0f (G1 RED-today: exit 1 reporting the first hit line only, the scanner reports one hit per file; G2 exit 0). G1 flips GREEN exactly at Task 1's commit; G3 through G5 flip GREEN at Tasks 2 and 3. Every grep gate aborts non-zero on a miss; the em-dash scanner's own exit contract (0 clean, 1 hit) is the zero-match assertion. The dash byte never appears in this plan's bytes: the greps construct it at run time, and the plan file is excluded from sweeps (its fragments are checker literals, not stale references).

```bash
# G1 (after Task 1): the maintenance skill is whole-file clean.
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/SKILL.md

# G2 (after Task 1): the pins suite still exits 0.
bash scripts/check_maintenance_pins.sh

# G3 (after Task 2): done-gate prose carries the deterministic fallback (dedicated pins).
grep -qF "added-lines --base HEAD" agents/skills/done/SKILL.md || { echo "G3 fail: done gate fallback missing"; exit 1; }
grep -qF "pre-existing (known-violation baseline)" agents/skills/done/SKILL.md || { echo "G3b fail: baseline report wording missing"; exit 1; }

# G4 (after Task 3): plans-skill selection rule present (dedicated pins).
grep -qF "known pre-existing violations in frozen spans" agents/skills/plans/SKILL.md || { echo "G4 fail: selection rule missing"; exit 1; }
grep -qF "authoring-time self-check" agents/skills/plans/SKILL.md || { echo "G4b fail: rule 29 sentence missing"; exit 1; }

# G5 (after Task 2): canaries exist and the lib suite is green.
for canary in test_em_dash_fallback_preexisting_tracked_passes test_em_dash_fallback_untracked_still_fails test_em_dash_fallback_dirty_added_lines_still_fails test_em_dash_fallback_mixed_hits_fail_untracked; do grep -qF "$canary" scripts/test_done_sweep_gates_lib.py || { echo "G5 fail: $canary missing"; exit 1; }; done
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_done_sweep_gates_lib.py -q

# G6 (whole diff): the run introduced no em dashes anywhere.
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
```

### Task 1: De-em-dash the maintenance skill body

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] Run `bash scripts/check-no-em-dash.sh file agents/skills/maintenance/SKILL.md` → expect RED: exit 1 reporting the first hit line only (the whole-file modes report one hit per file, exiting at the first em-dash line; measured at authoring: `agents/skills/maintenance/SKILL.md:64`); the six-dash population across four lines (the lines carrying `parked-dependency liveness arm`, `Progress for an execution child`, `successor-dispatch children-append`, and `parked_dependencies is the ordered array`) is authoring context from grep, not the expected gate output; baseline recorded at authoring 2026-09-28 against main 07885e0f [class: REPOSITORY_TEST]
- [ ] Replace each appositive em dash (space, U+2014, space) with the named punctuation, changing no other byte of the line: in the parked-dependency liveness arm line, the dash after "with the plan otherwise dispatchable" becomes a colon and the dash after "evaluated FIRST and win over the aging states" becomes a colon; in the Progress-for-an-execution-child line, the dash after "never a checkbox count against the serialized plan" becomes a colon; in the successor-dispatch children-append line, the dash after "parked-dependency entry edits" becomes a colon and the dash after "refused_tip`)" becomes a comma; in the parked_dependencies field-paragraph line, the dash after "plus four optional keys" becomes a colon. Each replacement keeps the tail text after the dash byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the file scan again → expect GREEN: exit 0 [class: REPOSITORY_TEST]
- [ ] Run `bash scripts/check_maintenance_pins.sh` → expect exit 0 (authoring baseline exit 0; the suite carries no em-dash bytes, so no pinned literal spans a replaced dash) [class: REPOSITORY_TEST]
- [ ] Commit: `skills: remove six appositive em dashes from maintenance skill` [class: IMPLEMENTATION_REQUIRED]

### Task 2: done gate falls back to added-lines on pre-existing violations

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

- [ ] Write all four canaries with fixture em-dash bytes constructed at run time via the Python source escape `"\u2014"` (a literal U+2014 byte must never appear in test source, so Task 2's added lines stay clean under G6's added-lines gate, which scans every extension) [class: IMPLEMENTATION_REQUIRED]
- [ ] RED canary `test_em_dash_fallback_preexisting_tracked_passes`; given a fixture repo whose tracked prose file carries one committed em dash on an unchanged line while the working tree adds one clean line to that file, expects the em-dash-scan gate returns rc 0 with a message carrying the full row shape `pre-existing (known-violation baseline): <path>:<line>` for the fixture path and line [class: REPOSITORY_TEST]
- [ ] RED canary `test_em_dash_fallback_untracked_still_fails`; given the same fixture shape but the dirty prose path is untracked, expects rc 1 naming that path with the reason marker `new prose must be whole-file clean` [class: REPOSITORY_TEST]
- [ ] RED canary `test_em_dash_fallback_dirty_added_lines_still_fails`; given a tracked file whose working tree adds a line carrying an em dash, expects rc 1 naming that path with the reason marker `added-lines` [class: REPOSITORY_TEST]
- [ ] RED canary `test_em_dash_fallback_mixed_hits_fail_untracked`; given a fixture repo holding one tracked file with a committed dash on an unchanged line (clean added lines) plus one untracked prose file carrying a dash, expects rc 1 naming the untracked path with the reason marker `new prose must be whole-file clean`; the tracked pre-existing file must not short-circuit the untracked failure [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_done_sweep_gates_lib.py -q -k em_dash_fallback` (all four canaries fail today: today's failure message is the touched tail rows, which carries none of the three markers; suite baseline 75 passed on main 07885e0f via the same command without -k) [class: REPOSITORY_TEST]
- [ ] Implement the fallback in `gate_em_dash_scan`: after a non-zero `touched` run, partition the reported paths into untracked (`git ls-files --others --exclude-standard`) and tracked; the partition input is the touched probe's COMPLETE stdout (every reported row of the same invocation, re-run or captured before the rc check), never the failure message's last-10-rows tail (`tail_rows[-10:]` in the current lib), so runs with more than ten hitting files cannot silently pass dirty added lines; for each tracked path run `bash <check-no-em-dash.sh> added-lines --base HEAD -- <path>`; a clean result marks the hit pre-existing (collect one `pre-existing (known-violation baseline): <path>:<line>` row per hitting tracked file, the touched probe reporting the first violating line per file, and return rc 0 with the rows in the message); any untracked hit returns rc 1 carrying the marker `new prose must be whole-file clean` with the path, and any dirty added-lines result returns rc 1 carrying the marker `added-lines` with the path [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the -k selection passes and the full lib suite stays green [class: REPOSITORY_TEST]
- [ ] Amend the done skill: the em-dash-scan clause of the gates-order paragraph gains exactly the sentence `on failure the gate falls back to added-lines --base HEAD per tracked path, reporting the first pre-existing line per hitting file as pre-existing (known-violation baseline): <path>:<line> (one row per hitting file, matching the whole-file probe's reporting shape); untracked hits and dirty added lines still fail`, and the em-dash-scan fix-guidance bullet gains exactly `enumerated pre-existing tracked hits pass with the baseline report; the stop-and-adjudicate path applies to added-lines failures and untracked-path hits` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G3's two greps over agents/skills/done/SKILL.md → expect both found (interim check before the commit, not first at Task 4) [class: REPOSITORY_TEST]
- [ ] Commit: `done: em-dash gate falls back to added-lines for pre-existing violations` [class: IMPLEMENTATION_REQUIRED]

### Task 3: plans skill names the mode-selection rule

Files:
- `agents/skills/plans/SKILL.md`

- [ ] In Validation Commands authoring rule 28, append one sentence after its final sentence: whole-file modes are for files the plan leaves whole-file clean; when a validation gate must bind a file whose committed bytes carry known pre-existing violations in frozen spans (the maintenance skill before Task 1 is the standing example), the gate selects `added-lines --base REF` over the prescribed insertions [class: IMPLEMENTATION_REQUIRED]
- [ ] In rule 29, inside the opening parenthesis after the real-subcommand-form clause, append one sentence: at authoring time the plan bytes are the touched set (a new file), so `touched` is the authoring-time self-check; an executor-facing Validation block gating an edited file with known pre-existing committed violations selects added-lines per rule 28 [class: IMPLEMENTATION_REQUIRED]
- [ ] Verification greps, fail-closed and dedicated: rule 28 carries the span `known pre-existing violations in frozen spans`; rule 29 carries the span `authoring-time self-check` [class: REPOSITORY_TEST]
- [ ] Commit: `plans: name the em-dash gate mode-selection rule` [class: IMPLEMENTATION_REQUIRED]

### Task 4: final validation

- [ ] Run the full Validation Commands block from the repo root → expect every gate green; record the output in the task log [class: REPOSITORY_TEST]
