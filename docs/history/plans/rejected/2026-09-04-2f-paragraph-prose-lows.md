# Plan: 2f prescribed-paragraph prose Lows (code-review r3, six findings)

Backlog origin: `docs/history/backlog/2026-09-03-2f-paragraph-prose-lows.md`
Source review: `docs/reviews/2026-09-02-r5-residuals-fixes-code-review-r3.md`

## Assumptions

- assume the two target files live at `docs/plans/completed/2026-09-02-phase3-residue-pass.md` and `docs/plans/completed/2026-09-02-r5-residuals-fixes.md`; basis: both plans were executed and archived on 2026-09-02 after the backlog item was written (the backlog's `docs/plans/` paths no longer exist on disk; verified by listing).
- assume scope is the two archived plan documents only; the live `agents/skills/execute-plan/SKILL.md` is out of scope; basis: the backlog's Location section names exactly two files, and the live skill carries its own independently re-folded counting paragraph (line ~654) that already fixed the r3-ds-1 dangle; runtime skill text changes are a separate pass, not this prose-polish rider.
- assume "fold all six clauses in ONE edit" (backlog Warning) applies to the residue-pass plan file: all prescribed-paragraph sentence replacements land in one edit before any validation rerun; basis: backlog Warning line.
- assume the r5-residuals plan's Validation block is re-run with three documented adaptations (current archived paths, re-derived Task 5 spans, and the `^24\.` rule-count re-derivation), because that block pins `$RP` spans that this plan's Task 1 intentionally rewords, and its paths plus rule counts predate the archive moves and the residue-pass rule renumber; basis: on-disk block content, the archive moves above, and the `Generate`-at-24 state verified on disk.

## Terms

- **prescribed 2f paragraph**: the first of the three paragraphs quoted inside Task 2f of the residue-pass plan (the paragraph beginning `Every launch of a Step 3.1 review panel increments`).
- **round-advancing re-entry**: a re-entry that advances `review_round` (re-runs workers in the same round). Replaces the ambiguous label "counted re-entry" (both kinds increment `re_entry_count`; the real distinction is `review_round` advancement; finding 3).
- **round-neutral re-entry**: a re-entry that re-checks or re-synthesizes without re-running workers; advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`. Replaces "uncounted re-entry".
- **`$EP` pins**: the `expect_once`/`expect_absent` lines in the residue-pass plan's Validation Commands block that pin spans in `agents/skills/execute-plan/SKILL.md`. This plan does NOT touch that skill file, so the `$EP` pins are unaffected; the Validation Commands block must still exit 0 after Task 1.
- **re-derived r5 Task 5 spans**: the r5-residuals plan's Validation block pins `$RP` (the residue-pass plan) spans `Such an uncounted re-entry advances neither \`review_round\`` and `When \`re_entry_count\` reaches 3 within the same round`. Task 1 rewords the first span's text, so the re-run of that block in this plan's validation uses updated spans pinned to the reworded text.

## Gist & Examples

Six Low, non-blocking prose-clarity findings from the r3 certification code review all land in the prescribed 2f paragraph of the (now archived) residue-pass plan, plus one missing record in the r5-residuals plan's Task 5 Superseded note. This plan folds all six clauses in ONE edit to the prescribed paragraph (per the backlog's regeneration warning: this paragraph produced wording findings in every review round r1-r3) and extends the Superseded note.

What changes, sentence by sentence, inside the prescribed 2f paragraph only:

1. **(r3-ds-1 + R3-RISK-1, dangled "Such")** Old: `Such an uncounted re-entry advances neither ...`; the preceding sentence's subject is the round-advancing re-entry, so "Such" mis-binds. New: `A round-neutral re-entry (re-checking or re-synthesizing without re-running workers) advances neither ...`; an explicit, self-contained subject.
2. **(r3-ds-2, duplicated staging-doc continuation)** Old: `A counted re-entry advances \`review_round\` while continuing the same round's \`-r<N>\` staging doc; it does not start a new round and does not reset \`re_entry_count\`.`; the continuation fact is already stated by the earlier sentence. New: `A round-advancing re-entry advances \`review_round\`; it does not start a new round and does not reset \`re_entry_count\`.`; only its new facts remain.
3. **(r3-ds-3, labels name the wrong distinction)** Both kinds increment `re_entry_count`; the real distinction is `review_round` advancement. All four label occurrences in the paragraph are renamed: "counted re-entry" → "round-advancing re-entry", "uncounted re-entry" → "round-neutral re-entry" (see Terms), including `which each counted launch advances` → `which each round-advancing launch advances`.
4. **(CD-F1, missing pin-sync record)** The r5-residuals plan's Task 5 Superseded note records the re-folded sentences but not the synced `$EP` pin strings; the note is extended with: `the two \`$EP\` pin strings were synced to the re-folded sentence spans (commit 0b32d08)`. Commit 0b32d08 exists on this repo's history (`plans: address code-review r2 (re-entry stop counts all re-entries, counted re-entries never reset, pin syncs)`).
5. **(R3-RISK-2, reset firing condition unstated)** Old: `(reset each round)`. New: `(reset only when a new round starts, i.e. at the next \`-r<N>\` staging doc)`.

Example of the label fix in context (before → after):

> ... so staging-doc numbering and `review_round` may diverge after a **counted** re-entry. **Such an uncounted** re-entry advances neither ...
> ... so staging-doc numbering and `review_round` may diverge after a **round-advancing** re-entry. **A round-neutral** re-entry (re-checking or re-synthesizing without re-running workers) advances neither ...

All `$EP`-pinned spans survive the rewording verbatim (verified span-by-span at authoring time; each pinned span text below occurs in the reworded paragraph exactly as pinned), so the residue-pass Validation block keeps passing against the untouched skill file.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each of the five edits above is present exactly once in the prescribed 2f paragraph; no old spans remain; no `$EP` pin span is altered or duplicated.
- minimality: only the prescribed paragraph (paragraph 1 of the Task 2f quote) and the r5 Superseded note change; paragraphs 2-3, the Authoring-time proof paragraph, and the Validation Commands block of the residue-pass plan are byte-identical before/after.
- regeneration safety: the full residue-pass Validation block exits 0 after the edit (re-run with the documented path remap), and the r5-derived checks with re-derived spans pass.
- shell hygiene: both archived Validation blocks remain `bash -n` clean.

**Done when:**
- All validation commands in this plan exit 0 on the post-edit tree.

**Ship when:**
- Not applicable; repository-docs-only change, no deploy or external dependency.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `docs/plans/completed/2026-09-02-phase3-residue-pass.md` (prescribed 2f first paragraph plus the appended provenance-note paragraph ONLY; all other sections frozen)
- `docs/plans/completed/2026-09-02-r5-residuals-fixes.md` (Task 5 Superseded note ONLY; all other sections frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; reason: live runtime skill carries its own re-folded paragraph; changing executed behavior text is a separate pass, not this backlog rider (see Assumptions).
- `docs/plans/completed/2026-09-02-phase3-residue-pass.md` paragraphs 2-3 of the Task 2f quote, the Authoring-time proof paragraph, and the Validation Commands block; reason: frozen history, no r3 finding touches them.
- Backlog file `docs/history/backlog/2026-09-03-2f-paragraph-prose-lows.md`; reason: moves to `backlog_completed/` only at plan completion per the plans lifecycle, not by this plan's tasks.

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
TMPDIR="${TMPDIR:-/tmp}"
RP=docs/plans/completed/2026-09-02-phase3-residue-pass.md
R5=docs/plans/completed/2026-09-02-r5-residuals-fixes.md

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

# Task 1 checks: the five rewordings, each exactly once in the plan file
expect_once "$RP" '(reset only when a new round starts, i.e. at the next `-r<N>` staging doc)'
expect_once "$RP" 'A round-neutral re-entry (re-checking or re-synthesizing without re-running workers) advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`.'
expect_once "$RP" 'A round-advancing re-entry advances `review_round`; it does not start a new round and does not reset `re_entry_count`.'
expect_once "$RP" 'may diverge after a round-advancing re-entry'
expect_once "$RP" 'which each round-advancing launch advances'

# Task 1 checks: old spans gone (negated; the archive must no longer carry them)
expect_absent "$RP" 'Such an uncounted re-entry'
expect_absent "$RP" 'A counted re-entry advances `review_round` while continuing'
expect_absent "$RP" '(reset each round) and continues'
# label rename is complete inside the plan file: no bare counted/uncounted re-entry labels left
expect_absent "$RP" 'counted re-entry'
expect_absent "$RP" 'uncounted re-entry'

# Task 1 check: staging-doc continuation phrase survives exactly once (the r3-ds-2 dedup;
# apostrophe-free span per plans rule 22; the removed S3 prefix is separately covered by the
# expect_absent on 'A counted re-entry advances `review_round` while continuing' above)
test "$(grep -oF 'continues the same round' "$RP" | wc -l | tr -d ' ')" -eq 1 || { echo "continuation-phrase count wrong"; exit 1; }

# Task 1 check: provenance note present exactly once (symmetric with Task 2's r5 note)
expect_once "$RP" '*(Prescribed paragraph 1 prose-reworded 2026-09-04 post-archive per `docs/history/backlog/2026-09-03-2f-paragraph-prose-lows.md`; the executed skill text in `agents/skills/execute-plan/SKILL.md` is unchanged by that pass.)*'

# Task 2 check: CD-F1 Superseded note extension in the r5 plan
expect_once "$R5" 'the two `$EP` pin strings were synced to the re-folded sentence spans (commit 0b32d08)'

# Cross-cutting: residue-pass full Validation block still exits 0 (its $EP pins target the
# untouched skill). The block is re-run with ONE documented adaptation: pre-archive
# `docs/history/backlog/` paths are remapped to `docs/history/backlog/completed/` because
# the referenced backlog files were archived after this block was authored (verified GREEN
# with this remap on the pre-edit tree at authoring time).
awk '/^```bash$/{f=1;next} /^```$/{if(f){f=0}} f' "$RP" > "$TMPDIR/rp-validation.sh" || exit 1
sed -i '' 's|docs/history/backlog/2026-09-02|docs/history/backlog/completed/2026-09-02|g' "$TMPDIR/rp-validation.sh" || sed -i 's|docs/history/backlog/2026-09-02|docs/history/backlog/completed/2026-09-02|g' "$TMPDIR/rp-validation.sh"
bash "$TMPDIR/rp-validation.sh" || { echo "residue-pass validation block failed after Task 1"; exit 1; }
bash -n "$TMPDIR/rp-validation.sh" || { echo "residue-pass block shell error"; exit 1; }

# Cross-cutting: r5-derived checks with RE-DERIVED Task 5 spans (the original r5 block pins
# $RP spans 'Such an uncounted re-entry advances neither `review_round`' and
# 'When `re_entry_count` reaches 3 within the same round'; the first is intentionally
# reworded by Task 1, so the rerun pins the reworded text). All other $RP pins in the r5
# block are quoted spans in frozen sections this plan does not touch and are re-run as-is
# via the block below with the same path remap. A third adaptation re-derives the block's
# stale `^24\.` rule-count check (r5 expected count 0; the residue-pass plan itself resolved
# the duplication by landing Generate at 24, verified on disk today), so the rerun asserts
# count 1. The re-derived Task 5 span was verified RED at authoring time 2026-09-04 (the
# reworded sentence does not exist yet) and flips GREEN exactly when Task 1 lands.
awk '/^```bash$/{f=1;next} /^```$/{if(f){f=0}} f' "$R5" > "$TMPDIR/r5-validation.sh" || exit 1
sed -i '' 's|docs/plans/2026-09-02-phase3-residue-pass.md|docs/plans/completed/2026-09-02-phase3-residue-pass.md|g; s|Such an uncounted re-entry advances neither `review_round`|A round-neutral re-entry (re-checking or re-synthesizing without re-running workers) advances neither `review_round`|g; s#"$PL")" -eq 0 || { echo "rule 24 count wrong"#"$PL")" -eq 1 || { echo "rule 24 count wrong"#' "$TMPDIR/r5-validation.sh" || sed -i 's|docs/plans/2026-09-02-phase3-residue-pass.md|docs/plans/completed/2026-09-02-phase3-residue-pass.md|g; s|Such an uncounted re-entry advances neither `review_round`|A round-neutral re-entry (re-checking or re-synthesizing without re-running workers) advances neither `review_round`|g; s#"$PL")" -eq 0 || { echo "rule 24 count wrong"#"$PL")" -eq 1 || { echo "rule 24 count wrong"#' "$TMPDIR/r5-validation.sh"
bash "$TMPDIR/r5-validation.sh" || { echo "r5 validation block (re-derived) failed after Task 1"; exit 1; }
bash -n "$TMPDIR/r5-validation.sh" || { echo "r5 block shell error"; exit 1; }
rm -f "$TMPDIR/rp-validation.sh" "$TMPDIR/r5-validation.sh"

# Mechanical pin-vs-prescription audit (plans rule 22): every $EP pin span in the
# residue-pass block must occur EXACTLY ONCE in the live skill file it pins (unchanged by
# this plan, but the audit proves the rewording did not alias or duplicate any pinned span).
awk '/^```bash$/{f=1;next} /^```$/{if(f){f=0}} f' "$RP" | grep -E '^expect_(once|absent) "\$EP" ' | while IFS= read -r line; do
  _kind=${line%% *}
  _span=${line#*\"\$EP\" }
  _span=${_span%\'}; _span=${_span#\'}
  _n=$(grep -cF -- "$_span" agents/skills/execute-plan/SKILL.md)
  if [ "$_kind" = "expect_once" ] && [ "$_n" -eq 1 ]; then :; elif [ "$_kind" = "expect_absent" ] && [ "$_n" -eq 0 ]; then :; else echo "EP pin audit $_kind ($_n): $_span"; exit 1; fi
done || { echo "EP pin audit failed"; exit 1; }

echo "ALL VALIDATION PASS"
```

### Task 1: prescribed 2f paragraph prose fixes (one edit, findings 1-3 and 5)

Files:
- `docs/plans/completed/2026-09-02-phase3-residue-pass.md`

Apply ALL replacements below to the FIRST paragraph quoted in Task 2f (the paragraph beginning `Every launch of a Step 3.1 review panel increments`) in ONE edit. Do not touch paragraphs 2-3, the Authoring-time proof paragraph, or the Validation Commands block.

- [ ] Verify pre-state: `grep -cF 'Such an uncounted re-entry' <file>` returns 1; `grep -cF 'round-advancing' <file>` returns 0 (recorded RED-today at authoring time 2026-09-04 on branch `2026-09-04-2f-paragraph-prose-lows`)
- [ ] Replace `(reset each round)` with `(reset only when a new round starts, i.e. at the next \`-r<N>\` staging doc)` (R3-RISK-2); the old string must remain nowhere else in the file (the standalone `reset each round` table row lives in the skill file, not here; verify with `grep -n 'reset each round' <file>` before editing: exactly one hit, inside this parenthetical)
- [ ] Replace `Such an uncounted re-entry advances neither \`review_round\` nor the \`-r<N>\` staging doc but still increments \`re_entry_count\`.` with `A round-neutral re-entry (re-checking or re-synthesizing without re-running workers) advances neither \`review_round\` nor the \`-r<N>\` staging doc but still increments \`re_entry_count\`.` (r3-ds-1 + R3-RISK-1; keeps the `$EP`-pinned tail span verbatim)
- [ ] Replace `may diverge after a counted re-entry` with `may diverge after a round-advancing re-entry` (r3-ds-3)
- [ ] Replace `A counted re-entry advances \`review_round\` while continuing the same round's \`-r<N>\` staging doc; it does not start a new round and does not reset \`re_entry_count\`.` with `A round-advancing re-entry advances \`review_round\`; it does not start a new round and does not reset \`re_entry_count\`.` (r3-ds-2 dedup + r3-ds-3 relabel)
- [ ] Replace `which each counted launch advances` with `which each round-advancing launch advances` (r3-ds-3)
- [ ] Verify post-state: `grep -cF 'counted re-entry' <file>` returns 0 and `grep -cF 'uncounted re-entry' <file>` returns 0 (whole file; the labels must not survive anywhere in the archived plan)
- [ ] Immediately after the Task 2f quoted paragraphs (after the third quoted paragraph's closing backtick), append this provenance line as its own paragraph: `*(Prescribed paragraph 1 prose-reworded 2026-09-04 post-archive per `docs/history/backlog/2026-09-03-2f-paragraph-prose-lows.md`; the executed skill text in `agents/skills/execute-plan/SKILL.md` is unchanged by that pass.)*`; the residue-pass file then records its own post-archive rewording, symmetric with Task 2's r5 Superseded note
- [ ] Run the plan's `## Validation Commands` Task 1 sections → expect GREEN (all five `expect_once` pins flip from RED-today; the residue-pass and r5 blocks go GREEN at this task; if any `$EP` pin fails, STOP; a pinned span was altered, revert and re-derive)
- [ ] Commit: `plans: fold 2f paragraph prose lows (dangle, dup, labels, reset condition)`

### Task 2: CD-F1 Superseded note extension in the r5 plan

Files:
- `docs/plans/completed/2026-09-02-r5-residuals-fixes.md`

- [ ] In the `Superseded 2026-09-03:` note under Task 5, append one sentence: `the two \`$EP\` pin strings were synced to the re-folded sentence spans (commit 0b32d08).` (CD-F1; no other change to the file)
- [ ] Run the plan's `## Validation Commands` Task 2 section → expect GREEN
- [ ] Commit: `plans: record EP pin-string sync in r5 Task 5 superseded note (CD-F1)`
