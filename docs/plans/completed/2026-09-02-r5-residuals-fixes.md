# Plan: phase3-residue-pass r5 residuals fixes

Backlog: docs/history/backlog/2026-09-02-phase3-residue-pass-r5-residuals.md (promotes all 5 findings)
Source: docs/reviews/2026-09-02-plan-review-phase3-residue-pass-r5.md

## Assumptions

- assume all work lands on branch `2026-09-02-phase3-residue-pass` (no separate branch); basis: this plan amends `docs/plans/2026-09-02-phase3-residue-pass.md`, which lives on and is certified for that unmerged branch, and the run is pre-authorized ("accepting all suggestions").
- assume backlog item 3 (re-entry cap) is implemented by amending the residue-pass plan's **prescribed Task 2f** counting-paragraph text, not by editing `agents/skills/execute-plan/SKILL.md` directly; basis: residue-pass Task 2f wholesale-replaces that paragraph on execution, so a direct skill edit would be clobbered (single source of truth).
- assume the rule-numbering collision (foreign rule 24 "Task-coupling sweep", added at 761a5c2) is resolved by renumbering it to 25 **now, in this plan**, rather than re-pinning residue-pass Task 1; basis: this preserves the certified byte-precise Task 1 prescription (`22. **Witnesses` → `23.`, `23. **Generate` → `24.`) and its `^24\. ` count == 1 pin.

## Gist & Examples

Five non-blocking residuals from the r5 certification round of the phase3-residue-pass plan, plus one new collision found at execution-prep time:

1. **Preamble misclassification (Low):** the authoring-time proof classes the Task 2g routing-anchor count as RED-today, but the anchor `Class membership in the two backlog-by-default classes` already occurs exactly once on disk, so that guard is green today and never flips. Reclassify it as a green-today count guard. Additionally, the rule 25 guard added by this plan is a green-today regression guard; both reclassifications and a new rule 25 guard land in the Validation preamble.
2. **Cap-row forward reference (Low):** the prescribed Step 3.5 cap-row cell (residue-pass Task 2d) says "then the short session note described in this row is written" before the otherwise-branch of the same cell defines what that note contains. Replace the forward reference with the inline definition.
3. **Uncounted re-entry loop (Medium, pre-existing debt):** verification-gate or timeout re-entries that re-check or re-synthesize without re-running workers advance neither `review_round` nor `re_entry_count`, so a pathologically failing gate can loop with no cap ask. Fix in the prescribed Task 2f counting paragraphs: uncounted re-entries increment `re_entry_count`, counted re-entries never reset it, and reaching 3 within a round stops for a user ask that a standing continue does not lift (re-folded after code-review r2; see the Task 5 superseded note).
4. **Cap-row single-ask not restated (Low):** the prescribed cell says "take the Fix-risk direction per Hard Gate 23" without restating that Hard Gate 23 is a stop-and-ask; drift in `receiving-review` would silently drop the cap-row ask. Append "(a stop-and-ask)" locally and pin it.
5. **Review Scope heading (Low):** `docs/maintenance/glossary.md` is listed under **Production code (skill contract text)** in the residue-pass plan's Review Scope; it belongs under **Documentation**.
6. **Rule-numbering collision (this plan):** residue-pass Task 1 renumbers plans rules Witnesses 22→23 and Generate 23→24, but the foreign Task-coupling rule already occupies 24, which would leave two `^24\. ` lines and fail the plan's own count pin. Renumber Task-coupling 24→25 first (Task 1 here).

Example of the collision, before → after this plan's Task 1 (still before residue-pass Task 1):

```
before:            22 Mechanical, 22 Witnesses, 23 Generate, 24 Task-coupling
after Task 1:      22 Mechanical, 22 Witnesses, 23 Generate, 25 Task-coupling   (^24\. count is 0)
after rp Task 1:   22 Mechanical, 23 Witnesses, 24 Generate, 25 Task-coupling   (all counts correct)
```

Editing the residue-pass plan supersedes its r5 certified digest (fa8b91142892f0da); this plan's own Phase 3 clean review covers the edited plan text as explicit must-fix.

**Authoring-time proof (this plan's own Validation block, recorded 2026-09-02 on branch `2026-09-02-phase3-residue-pass` at 761a5c2):** executed against the current tree, the block is RED and fails at the first Task 1 pin (`25. **Task-coupling sweep...` absent from `plans/SKILL.md`; `^25\. ` count 0). Probe classes (this block's Task 2-5 pins grep the residue-pass plan file `$RP` unless noted): RED-today probes: all Task 1 `$PL` pins including the `^24\. ` count == 0 check (the count is 1 today and drops to 0 when Task 1 renumbers Task-coupling away), all Task 2 `$RP` preamble pins, the Task 3 `$RP` pins (the stop-and-ask span and the inline session-note span are absent from the residue-pass plan today, and its `expect_absent "$RP" 'the short session note described in this row'` guard FIRES until Task 3 removes the forward reference from the prescribed cell), the Task 4 awk check (the glossary bullet currently sits under **Production code (skill contract text)**), and the Task 5 `$RP` re-entry-cap pins; green-today keep-guards: the `bash -n` syntax check. Self-count immunity: this block's Task 3/5 `$RP` spans are the only places their exact text occurs in the residue-pass plan after the edits, because the residue-pass block's own new pins grep `$EP` and use shorter overlapping spans (they contain neither ` and fold`, nor `re-checks or re-synthesizes without re-running workers`, nor `When `re_entry_count` reaches`).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every reclassification/wording change in the residue-pass plan matches the on-disk reality it describes (verified by the plan's own grep probes and this plan's Validation Commands)
- maintainability: the residue-pass plan's Validation block stays internally consistent: every pinned span occurs exactly once in its prescribed snippets (mechanical audit), and `bash -n` passes over the block
- contract safety: no byte of `agents/skills/plans/SKILL.md` changes except the single rule-24 heading line; no byte of `agents/skills/execute-plan/SKILL.md` changes at all in this plan

**Done when:**
- `agents/skills/plans/SKILL.md`: Task-coupling renumbered to 25 with `^25\. ` count 1, `^24\. ` count 0, `^23\. ` count 1 (Generate), and the pre-existing duplicated 22s deliberately untouched (`^22\. ` count 2; resolving them is residue-pass Task 1's job, not this plan's)
- the residue-pass plan preamble classes the Task 2g routing-anchor count as green-today, keeps the rule 24 count in the RED-today class (it counts 0 after this plan's Task 1 until residue-pass Task 1 renumbers Generate into 24), and carries the rule 25 green-today regression pin
- the prescribed 2d cell contains "(a stop-and-ask)" and no forward reference to "the short session note described in this row"
- the prescribed 2f first paragraph contains the re-entry cap sentences
- the glossary bullet sits under **Documentation** in the residue-pass Review Scope
- this plan's Validation Commands pass end to end

**Ship when:**
- (none; all work is repository-local Markdown edits)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill contract text):**
- `agents/skills/plans/SKILL.md` (only the rule opening line `24. **Task-coupling sweep at authoring and after every fold:**` renumbered to 25; all other content frozen)

**Documentation:**
- `docs/plans/2026-09-02-phase3-residue-pass.md` (Validation preamble, Assumptions rule-numbering bullet, prescribed Task 2d cell, prescribed Task 2f first paragraph, Task 1 validation pins, Review Scope glossary bullet; all other content frozen)
- `docs/history/backlog/2026-09-02-phase3-residue-pass-r5-residuals.md` (status → done at archive, moved in the Phase 4 archive commit)

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; deliberately untouched: residue-pass Tasks 2b-2f own its edited spans, and editing now would be clobbered or fork the certified prescription.
- Any other skill file; the 17 residue-pass entries name only paths this plan does not open.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan (implements a task, fixes a regression this plan introduces, or contradicts a contract this plan changed). Otherwise drop with a one-line reason.

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
PL=agents/skills/plans/SKILL.md
RP=docs/plans/2026-09-02-phase3-residue-pass.md

expect_once() {
  _f="$1"; _s="$2"
  [ -f "$_f" ] || { echo "MISSING FILE: $_f"; exit 1; }
  _n=$(grep -cF -- "$_s" "$_f")
  if [ "$_n" -eq 1 ]; then :; else echo "expect_once ($_n) in $_f: $_s"; exit 1; fi
}
expect_absent() {
  _f="$1"; _s="$2"
  [ -f "$_f" ] || { echo "MISSING FILE: $_f"; exit 1; }
  if grep -qF -- "$_s" "$_f"; then echo "expect_absent fired in $_f: $_s"; exit 1; fi
}

# Task 1: foreign rule 24 (Task-coupling) renumbered to 25
expect_once "$PL" '25. **Task-coupling sweep at authoring and after every fold'
expect_absent "$PL" '24. **Task-coupling sweep'
# post-Task-1 state: Generate still at 23 (residue-pass Task 1 owns the 24 slot), so 24 counts 0
test "$(grep -c "^24\. " "$PL")" -eq 0 || { echo "rule 24 count wrong"; exit 1; }
test "$(grep -c "^25\. " "$PL")" -eq 1 || { echo "rule 25 count wrong"; exit 1; }

# Task 2: preamble reclassification + residue-pass validation-block pins
expect_once "$RP" 'the Task 2g routing-anchor count is likewise a green-today count guard'
expect_once "$RP" 'the rule 25 Task-coupling count is a green-today regression guard'
expect_once "$RP" '(22 Mechanical, 23 Witnesses, 24 Generate, 25 Task-coupling)'
expect_once "$RP" 'both re-derived after the Task-coupling 24→25 renumber'
expect_once "$RP" 'carries the duplicated 22s and Witnesses/Generate at 22/23'
test "$(grep -cF '25. **Task-coupling sweep' "$RP")" -eq 1 || { echo "residue-pass rule 25 pin missing"; exit 1; }
test "$(grep -cF 'grep -c "^25\. " "$PL"' "$RP")" -eq 1 || { echo "residue-pass rule 25 count pin missing"; exit 1; }
expect_absent "$RP" 'as do the Task 2g routing-anchor count and the Task 3a fan-out position anchors'

# Task 3: prescribed 2d cell de-forward-ref + stop-and-ask restatement
# spans chosen to occur ONLY in the prescribed cell text, never in the residue-pass block's own
# $EP pin lines (self-count immunity): the EP pin pins 'Fix-risk direction per Hard Gate 23
# (a stop-and-ask)' WITHOUT the trailing ' and fold', so this span stays count 1.
expect_once "$RP" 'Hard Gate 23 (a stop-and-ask) and fold'
expect_absent "$RP" 'the short session note described in this row'
expect_once "$RP" 'then a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) is written and the user ask happens'

# Task 4: glossary bullet under Documentation in residue-pass Review Scope
awk 'BEGIN{ok=0} /^\*\*Documentation:\*\*/{seen=1} /maintenance\/glossary\.md/{if(seen) found=1; else dup=1} /^\*\*Out of scope/{if(!seen || !found || dup){print "glossary bullet not moved cleanly under Documentation"; exit 1}}' "$RP" || exit 1

# Task 5: prescribed 2f re-entry cap (spans chosen for self-count immunity against the
# residue-pass block's own $EP pin lines, which use shorter overlapping spans)
expect_once "$RP" 'Such an uncounted re-entry advances neither `review_round`'
expect_once "$RP" 'When `re_entry_count` reaches 3 within the same round'

# Cross-cutting: residue-pass Validation block still shell-valid
awk '/^```bash$/{f=1;next} /^```$/{if(f){f=0}} f' "$RP" > /tmp/rp-validation.sh || exit 1
bash -n /tmp/rp-validation.sh || { echo "residue-pass validation block shell error"; exit 1; }
rm -f /tmp/rp-validation.sh

echo "ALL VALIDATION PASS"
```

### Task 1: Renumber foreign plans rule 24 (Task-coupling) to 25

Files:
- `agents/skills/plans/SKILL.md`

- [x] Sweep for numbered cross-references to the Task-coupling rule: `grep -rn "rule 24\|rules 24" --include='*.md' agents/ | grep -v docs/` (expect zero hits outside this plan and the residue-pass plan/backlog/review files; verified 2026-09-02 at 761a5c2); record the sweep output in the task log
- [x] In `agents/skills/plans/SKILL.md`, change the rule opening `24. **Task-coupling sweep at authoring and after every fold:**` to `25. **Task-coupling sweep at authoring and after every fold:**`. No other byte changes in this file.
- [x] Run → expect RED before the edit (`^25\. ` count is 0 today), GREEN after: `test "$(grep -c '^24\. ' agents/skills/plans/SKILL.md)" -eq 0 && test "$(grep -c '^25\. ' agents/skills/plans/SKILL.md)" -eq 1 && grep -q '^25\. \*\*Task-coupling' agents/skills/plans/SKILL.md` (post-edit tree: Generate stays at 23, so `^24\. ` counts 0 until residue-pass Task 1 renumbers it)
- [x] Commit: `skills: renumber foreign plans rule 24 (Task-coupling) to 25 ahead of residue-pass Task 1`

Deviation (recorded 2026-09-03, commit 430773b): the repo em-dash gate forced one extra byte change on the renumbered line; the rule body's "created" + em-dash + "a call" became "created; a call". Prescription above names the executed state except for this gate-mandated punctuation normalization.

### Task 2: Residue-pass preamble reclassification + rule 25 guard

Files:
- `docs/plans/2026-09-02-phase3-residue-pass.md`

- [x] In the **Authoring-time proof** paragraph of the Validation preamble, replace ONLY the parenthetical count-guards segment `(the rule 23 count is a green-today invariant guarding against a left-behind duplicate, while the rule 22 and rule 24 counts are RED-today probes that flip green at Task 1, as do the Task 2g routing-anchor count and the Task 3a fan-out position anchors)` (every other byte of the paragraph stays identical) with: `(the rule 23 count is a green-today invariant guarding against a left-behind duplicate, the Task 2g routing-anchor count is likewise a green-today count guard because the anchor already occurs exactly once on disk so its guard never flips, while the rule 22 count, the rule 24 count (0 after the Task-coupling 24→25 renumber by the r5-residuals plan, until residue-pass Task 1 renumbers Generate into 24), the rule 25 Task-coupling count is a RED-today probe that flips green at the r5-residuals plan's Task 1, and the Task 3a fan-out position anchors are RED-today probes)` with: `(the rule 23 count is a green-today invariant guarding against a left-behind duplicate, the Task 2g routing-anchor count is likewise a green-today count guard because the anchor already occurs exactly once on disk so its guard never flips, and the rule 25 Task-coupling count is a green-today regression guard because the r5-residuals plan's Task 1 already renumbered Task-coupling to 25; the rule 22 count and the rule 24 count are RED-today probes that flip green at residue-pass Task 1, when the duplicated 22s resolve and Generate takes the 24 slot, as do the Task 3a fan-out position anchors; the 2d stop-and-ask pin added by the r5-residuals plan is likewise a RED-today probe that flips green when residue-pass Task 2d executes, and the 2f re-entry-cap pins added by the r5-residuals plan are likewise RED-today probes that flip green when residue-pass Task 2f executes)`
  Superseded 2026-09-03: the parenthetical was re-folded after code-review r1 (F2/F3) to the final text above; the executed intermediate text is in commit db2db67.
- [x] Sweep the residue-pass plan for every post-state numbering enumeration and extend it to include the Task-coupling 25 slot: grep for `24 Generate` and `Generate 23->24`; the expected hits are the Done-when bullet beginning `- `grep -c "^22\. "``, `"^23\. "`, and `"^24\. "` over `agents/skills/plans/SKILL.md` are each 1, in monotonic file order (22 Mechanical, 23 Witnesses, 24 Generate).` (extend the parenthetical to `(22 Mechanical, 23 Witnesses, 24 Generate, 25 Task-coupling)` and append exactly this clause: `The pre-state on disk carries the duplicated 22s and Witnesses/Generate at 22/23 until residue-pass Task 1 executes.`) and the Assumptions rule-numbering bullet (extend its basis to note the Task-coupling 24→25 renumber by this plan). If the grep finds additional enumerations, extend those too.
- [x] In the Assumptions bullet on rule-numbering safety, replace the stale basis (`zero numbered cross-references ("rule 22"/"rules 22")`) with: the only numbered cross-references on disk are the residue-pass plan's own validation pins plus the r5-residuals plan's reconciliation, both re-derived after the Task-coupling 24→25 renumber.
- [x] In the Validation Commands block's `# Task 1:` section, add: `expect_once "$PL" '25. **Task-coupling sweep'` and `test "$(grep -c "^25\. " "$PL")" -eq 1 || { echo "rule 25 count wrong"; exit 1; }` (green immediately: this plan's Task 1 already landed; they are regression guards against a left-behind duplicate).
- [x] Run → expect GREEN for the Task 1-2 sections of this plan's Validation Commands block, scoped to those sections' probes; the Task 3-5 probes are still RED at this point (their pins grep spans edited by later tasks): stop-and-ask pin absent, glossary bullet still under Production code, re-entry-cap pins absent.
- [x] Commit: `plans: residue-pass preamble reclassification (green-today counts) + rule 25 guard`

### Task 3: Cap-row prescribed-cell wording fixes (2d)

Files:
- `docs/plans/2026-09-02-phase3-residue-pass.md`

- [x] In the prescribed Task 2d cell text, replace `review-reconciliation runs first, then the short session note described in this row is written and the user ask happens` with `review-reconciliation runs first, then a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) is written and the user ask happens` (removes the forward reference; the note's contents were only defined in the otherwise-branch of the same cell)
- [x] In the same prescribed cell, replace `take the Fix-risk direction per Hard Gate 23 and fold` with `take the Fix-risk direction per Hard Gate 23 (a stop-and-ask) and fold` (restates the single-ask guarantee locally so drift in `receiving-review` cannot silently drop the cap-row ask)
- [x] In the Validation Commands block's `# Task 2d:` section, keep `expect_once "$EP" 'but any such reconciliation still runs first), take the Fix-risk direction per Hard Gate 23'` (still a matching substring of the amended cell) and add exactly one new pin: `expect_once "$EP" 'Fix-risk direction per Hard Gate 23 (a stop-and-ask)'` (RED-today: the span is absent from `execute-plan/SKILL.md` on disk; flips green when residue-pass Task 2d executes). Do NOT add an `expect_absent "$EP" 'the short session note described in this row'` guard: that string never occurs in `execute-plan/SKILL.md` (verified 0 today), so the guard is vacuous, and its pin line would carry the span into the residue-pass plan file, permanently breaking this plan's own `expect_absent "$RP"` probe (self-count).
- [x] In the same edit, add the new `$EP` pin to the residue-pass Authoring-time proof's RED-today Task 2 probe class (the proof paragraph is where probe classes live; task logs only record execution output)
- [x] Run → expect GREEN for the Task 1-3 sections of this plan's Validation Commands block, scoped to those sections' probes; the Task 4 awk check and Task 5 pins are still RED (glossary bullet not yet moved; re-entry-cap sentences not yet inserted). This block's Task 3 pins grep the residue-pass plan file, which this task just edited.
- [x] Commit: `plans: residue-pass cap-row cell de-forward-ref + local stop-and-ask restatement`

### Task 4: Review Scope heading fix (glossary bullet)

Files:
- `docs/plans/2026-09-02-phase3-residue-pass.md`

- [x] Move the `- `docs/maintenance/glossary.md` (Review iteration cap entry only; all other entries frozen)` bullet (with the backticks around the path, exactly as on disk) from **Production code (skill contract text)** to the **Documentation** heading (after the two backlog bullets), keeping the freeze qualifier verbatim. No other Review Scope changes.
- [x] Run → expect GREEN: `awk '/^\*\*Documentation:\*\*/{seen=1} seen && /maintenance\/glossary\.md/{found=1} /^\*\*Out of scope/{if (seen && !found) {print "glossary bullet not under Documentation"; exit 1}}' docs/plans/2026-09-02-phase3-residue-pass.md` (RED before the move, GREEN after)
- [x] Run → expect GREEN for the Task 1-4 sections of this plan's Validation Commands block, scoped to those sections' probes; the Task 5 re-entry-cap pins are still RED (sentences not yet inserted)
- [x] Commit: `plans: move glossary.md to Documentation in residue-pass review scope`

### Task 5: Re-entry cap in prescribed counting paragraph (2f)

Files:
- `docs/plans/2026-09-02-phase3-residue-pass.md`

- [x] In the prescribed Task 2f FIRST paragraph, immediately after the sentence ending `so staging-doc numbering and `review_round` may diverge after a counted re-entry.` (and before `The cap compares `review_round` only`), insert: `A verification-gate or timeout re-entry that re-checks or re-synthesizes without re-running workers advances no counter but still increments `re_entry_count`. When `re_entry_count` reaches 3 within the same round without a staging-doc advance, stop the loop and ask the user before any further re-entry.`
- [x] In the Authoring-time proof paragraph, add the new 2f cap pins to the RED-today probe class (they flip green when residue-pass Task 2f executes)
- [x] In the Validation Commands block's `# Task 2f:` section, add `expect_once "$EP" 'advances no counter but still increments `re_entry_count`'` and `expect_once "$EP" 'reaches 3 within the same round without a staging-doc advance, stop the loop and ask the user'` (RED-today, flipping green at residue-pass Task 2f)
- [x] Run → expect GREEN for the full Validation Commands block (this is the final task; every probe is green at this point)
- [x] Commit: `plans: cap uncounted gate/timeout re-entries in prescribed counting paragraph`

Superseded 2026-09-03: code-review r2 re-folded the inserted sentences (the stop counts every re-entry in the round, counted re-entries never reset the counter, the cap sentence is qualified as max_review_rounds-only, and the counter sentence was reworded); the executed state is the prescribed Task 2f text in the residue-pass plan at this branch's HEAD.

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-17-maintenance-r5-doc-consistency-residuals.md: disposition folded into 2026-09-02-r5-residuals-fixes.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-06-done-marker-r5-residuals.md: disposition folded into 2026-09-02-r5-residuals-fixes.md (2026-09-25); per-item file deleted.
