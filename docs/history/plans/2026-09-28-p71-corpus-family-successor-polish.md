# Plan: Corpus-family successor polish

Backlog origins (scope of record):
- docs/history/backlog/2026-09-27-review-agents-corpus-family-phase3-deferred-findings.md
- docs/history/backlog/2026-09-27-review-agents-corpus-family-task1-deferred-review-nits.md
- docs/history/backlog/2026-09-27-review-agents-corpus-family-task3-deferred-review-nits.md
- docs/history/backlog/2026-09-27-review-agents-corpus-family-task4-deferred-review-nit.md

Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-p71-corpus-family-successor-polish-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The corpus-family's deferred review findings land as rigor and wording fixes instead of staying deferred: the door-registry selftest can no longer false-pass on moved clauses, the corpus wording matches its landed reality, and the archived plan's validation pins stay truthful.

- Declaration tests in the doors selftest attribute required-action spans to the door's own section, so a clause relocated across a section boundary fails the test instead of passing it.
- Exact counts and verbatim headings are pinned (declaration-test count 12, the relocatable-inventory heading), and the panel-signal test asserts compound spans plus the two cross-pointer door ids.
- The review-agents corpus wording carries no stale temporal qualifier, the consistency pointer names its code-review behavior, and the severity cap carries an explicit calibration-promotion exception.
- The archived corpus-family plan's Validation block reflects the true counts and the reworded corpus text under this plan's recorded successor license.

## Terms

- Door-section attribution: a declaration-test assertion that extracts the text from the door pattern's own section boundary (the nearest preceding heading of any level before the `Pattern:` declaration, through the next heading of any level), and requires the asserted span to occur inside that extraction, not merely in a fixed character window.
- Compound-span assert: a single assertion matching two spans in document order within one extracted region, so a pairing cannot survive being attached to the wrong trigger branch.
- Successor license: the recorded permission for this plan to edit the archived corpus-family plan's Validation block (the origins' own count-pin and heading-pin fixes name exactly that touch).
- Owning pin update: the archived plan's Validation Commands grep that pins a corpus phrase is re-literalized in the task immediately following the corpus reword, so the corpus and its pin never disagree across a landing.

## Assumptions

- assume the declaration-test count is exactly 12 on today's tree and the archived block's `-ge 11` pin plus its "three landed plus eight new" comment are both stale; basis: the task4 origin's arithmetic (base 4 landed + 8 new) and the task1 origin's comment-drift row.
- assume the archived plan's Validation block lines are the only archived bytes this plan touches; basis: the origins' recorded license names the count-pin fix and the heading pin, and the severity-row reword's owning pins live in the same block.
- assume the severity-cap contradiction resolves by appending an explicit calibration-promotion exception to the cap sentence rather than re-narrowing the span: the recorded span-narrowing residual's pins live in the same archived block and the exception is the smaller coherent edit; basis: the phase3 origin's fix line offering both, with the narrower arm selected under the origin prompt's standing pre-authorization.
- assume the `concurrency#claim-generation` id resolves by declaring a `Pattern:` id in `agents/skills/review-agents/concurrency.md` for the existing un-numbered claim-generation guidance rather than dropping the id from the applied-ids list; basis: the phase3 origin's fix line preferring declaration (a navigating worker keeps the fence check).
- assume F1's docs-branch provenance, F2's extras-copy stance clause, the scan-scope notes, and the packaged-parity boundary-wording redundancy stay recorded dispositions without edits; basis: each origin's own trigger reserves those surfaces for their next natural touch, and this plan touches none of them.

Decision points requiring a grill: severity-cap resolution via the cap exception clause (author selection between the origin's two recorded arms under the origin prompt's standing pre-authorization, 2026-09-28; Task 2); claim-generation id resolution via corpus declaration (author selection between the origin's two recorded arms under the same pre-authorization, 2026-09-28; Task 2); the archived-block edits ride this plan's successor license (recorded in the phase3 and task4 origins' fix lines, 2026-09-27; Task 3).

## Gist & Examples

TLDR: the doors selftest gains section-attribution, compound spans, exact counts, and heading pins; the corpus wording drops its stale qualifier and gains the pointer qualification, cap exception, and declared claim-generation id; the archived plan's pins are re-literals to match, for code-quality.

Today a clause moved from a door bullet into a neighbor keeps the selftest green (mechanically demonstrated on two doors), and a mid-execution tree missing one declaration test would pass the `-ge 11` pin. After this plan every assertion attributes to the door's own section and every count is exact.

Examples:

- A future editor moves "unless the plan explicitly documents the wider set" out of the typed-catalog door's section into a different door's section: the section-attributed assert fails where the old window assert passed.
- A worker navigating by `concurrency#claim-generation` finds a declared `Pattern:` id in concurrency.md instead of un-numbered prose.

## Evaluation Criteria

**Quality dimensions:**

- attribution: no declaration assert passes on text outside the door's own section (mutation-proven by moving one span across a section boundary in a scratch clone and watching the suite fail).
- exactness: every count pin is exact (12), no stale `-ge` bounds remain in the touched surfaces.
- corpus consistency: the reworded phrases carry their owning pin updates in the task immediately following the reword; no stale qualifier survives anywhere in the corpus.
- archived-bytes discipline: Task 3 touches only the recorded Validation-block lines (count comment, count pin, heading pin, severity-row pin literals) and nothing else in the archived file.

**Done when:**

- the doors suite passes with section-attributed asserts, compound-span panel-signal asserts, the two door-id pins, the exact count 12, and the heading pin.
- `check_review_agent_portability.py` exits 0.
- the corpus rewords, the cap exception, and the concurrency declaration are in place with wrap-tolerant absence of the stale phrases.
- the archived Validation block pins the true count, the heading, and the reworded severity-row phrase.
- the Validation Commands block passes end to end.

**Ship when:**

- the next natural touch of the packaged-parity boundary sentence folds the recorded redundancy simplification (human-owned sequencing; recorded disposition).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/test_review_agent_doors.py`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/concurrency.md`
- `docs/history/backlog/2026-09-27-review-agents-corpus-family-task3-deferred-review-nits.md` *(the recorded headroom-figure correction)*
- `docs/history/plans/completed/2026-09-26-review-agents-corpus-family.md` *(archived Validation block; successor license recorded in the origins)*

**Tests:**

- none as separate files; `scripts/test_review_agent_doors.py` (listed above) is the corpus's selftest and carries this plan's new assertions

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- the other review-agents lens files (documentation.md and concurrency.md only are edited); reason: no origin finding names them.
- the docs-branch provenance claim, extras-copy stance clause, hygiene/em-dash scan scopes, and the packaged-parity boundary sentence; reason: recorded dispositions whose triggers this plan does not fire.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. The doors suite passes with the new rigor (Tasks 1; mutation probe is Task 1's RED arm).
( cd "$REPO" && python3 scripts/test_review_agent_doors.py ) || { echo "FAIL: doors suite failed"; exit 1; }

# 2. Portability gate over the edited corpus files (AGENTS.md mandate).
( cd "$REPO" && python3 scripts/check_review_agent_portability.py ) || { echo "FAIL: portability checker failed"; exit 1; }

# 3. Exact counts and pins landed in the selftest (Task 1; only the pattern_section leg
# is red on today's tree and witnesses Task 1; the count and door-id legs are
# regression guards, green today because both ids are already pinned).
test "$(grep -c 'def test_.*_declared' "$REPO/scripts/test_review_agent_doors.py")" -eq 12 || { echo "FAIL: declaration test count is not 12"; exit 1; }
grep -qF "### Relocatable identifier inventory gate" "$REPO/agents/skills/review-agents/documentation.md" || { echo "FAIL: heading pin target missing"; exit 1; }
grep -qF "architecture#dual-surface-policy-parity" "$REPO/scripts/test_review_agent_doors.py" || { echo "FAIL: door id pin missing"; exit 1; }
grep -qF "testing#cross-surface-policy-witness" "$REPO/scripts/test_review_agent_doors.py" || { echo "FAIL: door id pin missing"; exit 1; }
grep -qF "def test_panel_signal_names_both_doors" "$REPO/scripts/test_review_agent_doors.py" || { echo "FAIL: panel-signal test missing"; exit 1; }
grep -qF "pattern_section" "$REPO/scripts/test_review_agent_doors.py" || { echo "FAIL: section attribution helper missing"; exit 1; }

# 4. Corpus wording: new phrases in, stale phrases out (wrap-tolerant; Task 2).
DM="$REPO/agents/skills/review-agents/documentation.md"
CM="$REPO/agents/skills/review-agents/concurrency.md"
grep -qF "the severity-calibration Category defaults row" "$DM" || { echo "FAIL: reworded row reference missing"; exit 1; }
if tr '\n' ' ' < "$DM" | tr -s ' ' | grep -qF "the new severity-calibration row"; then echo "FAIL: stale temporal qualifier still present"; exit 1; fi
grep -qF "in code reviews the sweep still stages each stale statement" "$DM" || { echo "FAIL: pointer qualification missing"; exit 1; }
grep -qF "calibration-promotion exception" "$DM" || { echo "FAIL: cap exception missing"; exit 1; }
test "$(grep -c 'Pattern: `concurrency#claim-generation`' "$CM")" -eq 1 || { echo "FAIL: claim-generation id not declared exactly once"; exit 1; }

# 5. The archived Validation block pins the truth (Task 3; successor license). The
# stale-phrase negation is scoped to the Validation Commands block: the archived file
# carries immutable occurrences of the phrase outside that block (task and coverage
# prose), which the license forbids touching.
AP="$REPO/docs/history/plans/completed/2026-09-26-review-agents-corpus-family.md"
BLOCK="$(awk '/^## Validation Commands$/{f=1} f&&/^```bash$/{b=1;next} f&&/^```$/{exit} b' "$AP")"
test -n "$BLOCK" || { echo "FAIL: archived validation block not extracted"; exit 1; }
grep -qF "four landed plus eight new" "$AP" || { echo "FAIL: count comment not corrected"; exit 1; }
grep -qF -- "-eq 12" "$AP" || { echo "FAIL: exact count pin missing in archived block"; exit 1; }
grep -qF "### Relocatable identifier inventory gate" "$AP" || { echo "FAIL: heading pin missing in archived block"; exit 1; }
grep -qF "the severity-calibration Category defaults row" "$AP" || { echo "FAIL: severity-row pin not re-literalized"; exit 1; }
src_rc=0
printf '%s' "$BLOCK" | grep -qF "the new severity-calibration row" || src_rc=$?
test "$src_rc" -le 1 || { echo "FAIL: block scan tool error (rc=$src_rc)"; exit 1; }
test "$src_rc" -eq 1 || { echo "FAIL: stale phrase still pinned inside the archived validation block"; exit 1; }

# 6. Em-dash cleanliness, scoped to what this plan creates and adds (rule 28). BASE is
# persisted to a run-notes file by Task 1's first item before any task commit, and is
# read back here so a fresh shell cannot run with the variable unset.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-p71-corpus-family-successor-polish.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
BASEFILE="$REPO/docs/tmp/p71-corpus-polish-base.sha"
test -s "$BASEFILE" || { echo "FAIL: BASE file missing (Task 1 first item)"; exit 1; }
BASE="$(cat "$BASEFILE")"
case "$BASE" in *[!0-9a-f]*) echo "FAIL: BASE file corrupted"; exit 1;; esac
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE" ) || { echo "FAIL: em-dash in added lines"; exit 1; }
```

### Task 1: Doors selftest rigor

Files:

- `scripts/test_review_agent_doors.py`

- [ ] Persist the base revision for validation command 6: write `git rev-parse HEAD` to `docs/tmp/p71-corpus-polish-base.sha` (one lowercase hex line), executed before any task commit of this run. [class: REPOSITORY_TEST]
- [ ] Add section attribution to the declaration-test helper: a `pattern_section(text, pattern_id)` extraction bounded by headings of any level (the nearest preceding line matching `^#{2,6} ` before the `Pattern:` declaration, through the next such heading; whitespace-normalized), and convert every declaration test's span assertions to call the section helper for their targets (the lens files carry `## ` sections, not `### `, so the anchor must not hardcode a level); delete the character-window helper from the declaration tests' use; its three remaining call sites in the two fixture-characterization tests keep the helper unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `test_panel_signal_names_both_doors`, replace the four independent full-text span asserts with two compound-span asserts over the extracted paired-surface policy section of `agents/skills/review-agents/review-panel-selection.md` (the section containing the migration-renumber and dual-entry policy bullets; extract once, assert both trigger-plus-pairing orders inside it), and add `assertIn` pins for `architecture#dual-surface-policy-parity` and `testing#cross-surface-policy-witness`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the verbatim heading pin: an assert that `agents/skills/review-agents/documentation.md` contains the exact line `### Relocatable identifier inventory gate`. [class: REPOSITORY_TEST]
- [ ] `python3 scripts/test_review_agent_doors.py`; given a scratch clone of one lens file with one required-action span moved across a section boundary into a different door's section (the only move class the section attribution must catch that the old window assert also passed), expects the suite to exit non-zero (the attribution regression catcher; run the probe once and record the failing test id), then restore the tree. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: validation command 1 (suite, including the new asserts) and command 3 (exact counts and pins) [class: REPOSITORY_TEST]
- [ ] Commit: `doors: section-attributed declaration asserts with exact counts and heading pin` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Corpus wording and seams

Files:

- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/concurrency.md`
- `docs/history/backlog/2026-09-27-review-agents-corpus-family-task3-deferred-review-nits.md`

- [ ] In `agents/skills/review-agents/documentation.md`, reword both `the new severity-calibration row` occurrences to `the severity-calibration Category defaults row`; qualify the stale-semantics consistency pointer with the code-review behavior (`in code reviews the sweep still stages each stale statement`); and append the calibration-promotion exception to the Do-not-assign cap sentence (prose findings stage Low except the relocatable-inventory class and the severity-calibration promotion rows, which follow their recorded promotion columns). [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/review-agents/concurrency.md`, declare the claim-generation guidance as a door pattern: add the `Pattern: `concurrency#claim-generation`` declaration line with its existing fence text as the pattern body, so the deep-read applied-ids list's id resolves. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `docs/history/backlog/2026-09-27-review-agents-corpus-family-task3-deferred-review-nits.md`, correct the declaration-window headroom figure from ~132 chars to the measured 122 chars, and mark the task3 nit row discharged by this plan. [class: IMPLEMENTATION_REQUIRED]
- [ ] Record in the run log the dispositions with no edit: the record-drift row (the archived plan's residual list keeps its pending wording; this disposition record is the successor editor's note), the boundary-wording redundancy (folds into the sentence's next natural touch), the scan-scope notes (standing shared-scanner property, content clean today), and the door-id applied-ids list (resolved by Task 2's declaration). [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: validation command 2 (portability) and command 4 (corpus wording) [class: REPOSITORY_TEST]
- [ ] Commit: `review-agents: corpus wording seams with the claim-generation declaration` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Archived Validation block under the successor license

Files:

- `docs/history/plans/completed/2026-09-26-review-agents-corpus-family.md`

- [ ] In the archived plan's Validation Commands block only: correct the count comment to `four landed plus eight new`, change the declaration-test pin from `-ge 11` to `-eq 12`, add the verbatim heading pin line (`grep -qF '### Relocatable identifier inventory gate' agents/skills/review-agents/documentation.md`), and re-literal the severity-row pin from `stages Medium operability drift per the new severity-calibration row` to the reworded phrase from Task 2. Touch no other line of the archived file. License: this plan is the recorded successor item named by the origins' count-pin and heading-pin fixes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 5 (archived block pins) and command 1 (the suite still passes; nothing in the corpus moved in this task) [class: REPOSITORY_TEST]
- [ ] Commit: `docs: archived corpus-family validation block under the successor license` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Full block

Files:

- none (verification-only task)

- [ ] Run → expect GREEN: the full Validation Commands block (rule 21 interim expectation: every command passes at this point). [class: REPOSITORY_TEST]
