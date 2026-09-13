# Plan: plan_readiness trailer gate r5 deferrals

Backlog origin: `docs/history/backlog/2026-09-07-plan-readiness-trailer-gate-r5-deferrals.md`
Source review: `docs/reviews/2026-09-07-plans-facts-do-not-resolve-design-ambiguity-code-review-r5.md` (round 5 fresh full panel, zero blocking; all findings below deferred non-blocking)

## Terms

- **Trailer gate**: the readiness check (`decision_marker_problem`, wired at the gate step in `scripts/plan_readiness.py`) requiring a decision-points trailer line in `## Assumptions` for plans whose latest review round is dated on or after `DECISION_MARKER_MIN_DATE` (2026-09-08).
- **Decision-points trailer**: the single plain line `Decision points requiring a grill: <value>` inside `## Assumptions`.
- **Fence parser**: `_strip_fences`, the single-active-fence-state pre-parser that removes fenced code blocks from the whole document before section extraction.
- **Pseudo-closer**: a line that resembles a fence closer but legally is not one (carries info text, is a shorter run than the opener, or is indented 4+ spaces).
- **Selftest arm**: one named fixture scenario of the `selftest#decision_marker/<name>` family.
- **Pinning arm**: an arm added in the same change as the fix it guards; RED before the fix, GREEN after.
- **Sidecar**: the `.stats.json` companion file of a review artifact.

## Assumptions

- assume all 12 findings are still open exactly as the backlog item describes; basis: arm-by-arm source verification on 2026-09-09 (every named arm, value, and behavior confirmed in the current file; the backlog's line anchors have drifted, so this plan anchors by arm name).
- assume the plan is single-task and `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md` is NOT folded in; basis: `python3 scripts/plan_readiness.py --sweep` at authoring time printed coverage 87/328, and that item's eligibility gate requires a positive total with covered equal to total.
- assume the baseline selftest passes before Task 1 starts; basis: `python3 scripts/plan_readiness.py --selftest` run at authoring time 2026-09-09 ended `ALL PASS` with exit 0.
- assume implementation touches only `scripts/plan_readiness.py`; basis: all 12 findings name that file, and no documented contract changes (the only doc-adjacent item, finding 12, is a docstring inside the same file).
- assume micro-choices left open by the backlog text take its recommended option: finding 3 uses the multi-needle convention, finding 9 uses `value` directly; basis: the scope of record plus the standing pre-authorization on the authoring task (2026-09-09).

Decision points requiring a grill: none remain.

## Gist & Examples

The r5 full panel of the plans-facts execution returned 12 valid non-blocking findings against the trailer gate and its selftest family. The panel budget was exhausted, so they were deferred to the backlog item this plan promotes. They fall into three groups, landed in the backlog's prescribed order:

1. **Selftest discrimination (findings 1-4).** Three closer arms place the quoted trailer BEFORE the pseudo-closer, so they stay green under both the r4 CommonMark closer rules and a lenient closer regression: both parsers swallow the trailer either way. The malformed-sidecar-date arm uses a value that sorts below the gate minimum, so removing the shape guard changes nothing.
2. **Fence parser residuals (findings 7-8).** `_strip_fences` iterates `text.splitlines()`, which also splits on CR, VT, FF, and the Unicode separators U+0085/U+2028/U+2029, then rejoins with `\n`. A separator embedded inside a fence-character run therefore fabricates a parser-line closer and exposes quoted trailer text (fail-open). Two CommonMark deviations add fail-closed-but-wrong behavior: a backtick opener whose info string contains a backtick is accepted as an opener (CommonMark: it is a paragraph), swallowing the rest of the document; and `lead` counts a tab as one column, so a tab-indented fence line opens or closes fences (CommonMark: tab means indent >= 4).
3. **Mechanical and cosmetic (findings 3-6, 9-12).** A dropped minimum-date assertion, a missing arms-table pairing assert, two missing tilde-side arms, a dead `strip()` pair, repeated sidecar-arm scaffolding, name-restating comments, and an inverted docstring clause.

**Before (today):** the `trailer_inside_short_close_fails` arm is a 4-backtick opener, the quoted trailer, then a 3-backtick pseudo-closer, and nothing closes the fence after it (it stays open to end of input). Under the current parser the pseudo-closer is content and the trailer is swallowed; under a lenient closer the pseudo-closer closes the fence while the trailer is already swallowed too. The arm passes under both, so it pins nothing.

**After (this plan):** the arm places a REAL trailer AFTER the pseudo-closer. Current parser: pseudo-closer is content, fence stays open, trailer swallowed, arm green. Lenient replay: pseudo-closer closes the fence, real trailer becomes visible, gate passes, arm red. Verified by replay at authoring time (all three reshaped arms flip under a lenient whole-function closer substitute).

Concrete fail-open example fixed here: with ```` ```\nquoted template\n``` \u2028\n<real trailer>\n``` ```` in a plan, today's `splitlines()` cuts the third line into ```` ``` ```` (a bare closer) and an empty line, so the real trailer is exposed. After the fix (`split("\n")` only) the separator stays inside the line, the closer regex rejects it, the fence stays open, and the trailer stays swallowed: fail-closed.

No documentation updates: no README, skill, or hook contract changes; finding 12 corrects a docstring inside the same file.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every reshaped or new arm flips under its named regression (lenient closer, missing shape guard, `splitlines()`, backtick-info opener, tab indent), each proven by a recorded probe, and the parser fixes keep the fail-closed model (an unterminated fence swallows to end of input).
- non-regression: `python3 scripts/plan_readiness.py --selftest` ends `ALL PASS` with exit 0 at every commit, and every `selftest#decision_marker/*` check name that exists before Task 1 still exists after Task 4.
- faithfulness: findings land in the backlog's prescribed order (1-2 first; 7-8 with their pinning arms in the same change; 3-6 and 9-12 mechanical).

**Done when:**

- All 12 findings are dispositioned in code exactly as the finding list prescribes.
- The full selftest ends `ALL PASS`, exit 0, and the arm-name before/after diff shows removals of none and additions of exactly the seven new arms this plan names.
- Every commit in the plan touches only `scripts/plan_readiness.py`.

**Ship when:**

- The hardened gate consumes real plan reviews in continuous use without new false rejections or false acceptances (no deploy step exists; the validator runs from the repo on every plan certification).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`

**Tests:** the selftest family lives inside `scripts/plan_readiness.py`; its arms are covered by the Production code entry above (no separate test path exists in this repo).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md`; reason: the conditional fold gate was closed at authoring time (sweep coverage 87/328), so that item stays untouched.
- `README.md`, `agents/`, and all docs; reason: no documented contract changes.
- every other file under `scripts/`; reason: the scope of record names one file.

## Design Invariants (CR Guard)

- Fail-closed closer model: an unterminated fence stays open to end of input and everything it swallowed is dropped; never emit swallowed content.
- The r4 CommonMark closer rules stay: same fence character, run at least the opener length, bare line with only optional whitespace, indent at most 3 spaces.
- Every existing `selftest#decision_marker/*` check name survives verbatim (backlog acceptance criterion).
- Both trailer and Review Scope gates stay forward-looking and date-gated; no retrofit of legacy artifacts.
- Finding order: 1-2 land before any parser change relies on the arms; 7-8 land with their pinning arms in one commit.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --selftest
```

Expect: the last output line is `ALL PASS` and the exit code is 0.

### Task 1: Discrimination arms and assertions (findings 1-4)

Test-only change; every arm stays green under the current parser, so the run is GREEN at the end of the task. Discrimination is proven by the replay probe below, not by a red run.

Files:
- `scripts/plan_readiness.py`

Except where an item says otherwise (scratch-only), every checklist item in this task edits the file listed above.

- [x] Record the baseline arm-name set for the Task 4 preservation check: `python3 scripts/plan_readiness.py --selftest | grep -oE 'selftest#decision_marker/[A-Za-z0-9_/]+' | sort -u` into `docs/tmp/decision-marker-names.before` (create the file; scratch only, never committed) and record the base commit for the Task 4 scope check: git rev-parse HEAD > docs/tmp/trailer-gate-base-sha.txt
- [x] Reshape `trailer_inside_close_with_info_text_fails` (name, date, `expect_ok=False`, needle `"missing decision-points trailer"` all unchanged); plan_text becomes `"# P\n\n## Assumptions\n\n```\nquoted template\n``` note\n" + trailer + "none remain.\n```\n"`, so a REAL trailer sits after the ```` ``` note ```` pseudo-closer inside the still-open fence
- [x] Reshape `trailer_inside_short_close_fails` the same way: plan_text `"# P\n\n## Assumptions\n\n````\nquoted template\n```\n" + trailer + "none remain.\n````\n"`, so the real trailer sits after the 3-backtick pseudo-closer inside the still-open 4-backtick fence
- [x] Reshape `trailer_after_indent_4_closer_stays_fenced` the same way: plan_text `"# P\n\n## Assumptions\n\n```\nquoted template\n    ```\n" + trailer + "none remain.\n```\n"`, with the genuine bare closer ending the fence after the real trailer
- [x] Discrimination replay probe (scratch run, not committed): substitute a lenient `_strip_fences` that toggles fence state on ANY line starting (after optional whitespace) with a run of 3+ backticks or tildes, ignoring character, run length, indent, and info text; run `decision_marker_problem` on the three reshaped fixtures and record that each returns `None` (trailer visible: the arm would flip red under the regression); restore the real function afterwards
- [x] Finding 2: in `sidecar_date_malformed_exempt`, change the malformed sidecar date from `09/10/2026` to `2026-09-08T12:00` (shape-invalid, so exempt with the guard; sorts at/above the 2026-09-08 minimum, so gated without the guard; `09/10/2026` sorts below the minimum and pins nothing, verified at authoring time); name, fixture date, and `expect_ok=True` unchanged
- [x] Finding 3: restore the dropped minimum-date assertion via the multi-needle convention: `gated_missing_trailer_fails` needle becomes `"missing decision-points trailer|2026-09-08"`, and the loop assertion becomes `all(n in (reason or "") for n in needle.split("|"))` (single-needle arms are unaffected: `split` on a needle without `|` yields the whole string)
- [x] Finding 4: as the first statement of the arms-loop body, add `assert (needle is None) == expect_ok, suffix` so the table validates its own needle/polarity pairing
- [x] Run the Validation Commands block → expect GREEN: `ALL PASS`, exit 0
- [x] Commit: `test: make trailer-gate selftest arms discriminate (r5 findings 1-4)`

### Task 2: Fence parser line model and CommonMark openers (findings 7-8)

Parser fixes and their pinning arms land in the same commit (backlog acceptance). The three fix-pinning arms are RED before the parser change; the CRLF characterization arm is GREEN before and after.

Files:
- `scripts/plan_readiness.py`

Except where an item says otherwise (scratch-only), every checklist item in this task edits the file listed above.

- [x] Add pinning arm `trailer_after_unicode_separator_close_stays_fenced` (fail-arm, needle `"missing decision-points trailer"`): plan_text `"# P\n\n## Assumptions\n\nNone needed.\n\n```\nquoted template\n``` \u2028\n" + trailer + "none remain.\n```\n"`; the U+2028 embedded in the would-be closer run must not fabricate a parser-line closer (RED today: verified at authoring time, the trailer is exposed)
- [x] Add pinning arm `backtick_info_opener_is_paragraph_passes` (pass-arm): plan_text `"# P\n\n## Assumptions\n\n```Decision points``` styled text.\n" + trailer + "none remain.\n"`; a backtick opener whose info string contains a backtick is CommonMark paragraph content, not an opener (RED today: verified, the accepted opener swallows the trailer)
- [x] Add pinning arm `tab_indented_fence_line_is_content_passes` (pass-arm): plan_text `"# P\n\n## Assumptions\n\n\t```\nquoted template\n" + trailer + "none remain.\n"`; a leading tab reads as indent >= 4, so the line can never open or close a fence (RED today: verified, the tab-indented line opens a fence that swallows the trailer)
- [x] Add pinning arm `tab_indented_closer_line_is_content_fails` (fail-arm, needle `"missing decision-points trailer"`): plan_text `"# P\n\n## Assumptions\n\nNone needed.\n\n```\nquoted template\n\t```\n" + trailer + "none remain.\n```\n"`; the same tab rule guards the CLOSER direction: today the tab-indented line closes the fence and exposes the real trailer (RED today, re-verified by the r3 probe), while after the fix it is fence content, the fence stays open, and the trailer stays swallowed
- [x] Add characterization arm `crlf_fenced_quote_passes` (pass-arm, GREEN before and after): plan_text `"# P\r\n\r\n## Assumptions\r\n\r\n```\r\nquoted template\r\n```\r\n\r\n" + trailer + "none remain.\r\n"`; a CRLF plan keeps passing the gate
- [x] Run → expect RED: exactly the four fix-pinning arms FAIL (`trailer_after_unicode_separator_close_stays_fenced`, `backtick_info_opener_is_paragraph_passes`, `tab_indented_fence_line_is_content_passes`, `tab_indented_closer_line_is_content_fails`); `crlf_fenced_quote_passes` and all pre-existing arms PASS
- [x] Finding 7: in `_strip_fences`, iterate `text.split("\n")` instead of `text.splitlines()`, normalizing each line by removing ONE trailing `"\r"` and using that stripped line for BOTH fence matching and emission (a match-only strip would leave the `\r` in the emitted line and falsely reject every CRLF plan at the `[ \t]*$` anchors); every other Unicode separator stays inside its line so it can no longer fabricate a closer, while CRLF input keeps today's behavior (the normalization also keeps a trailing `\r` out of captured trailer values, which finding 9 relies on)
- [x] Finding 8, same change: a BACKTICK opener whose info string contains a backtick is treated as ordinary content, not an opener (tilde openers keep accepting any info string, per CommonMark); a line whose leading whitespace contains a tab is treated as indent >= 4 for both opener and closer matching (fail-closed: such a line neither opens nor closes)
- [x] Run → expect GREEN: `ALL PASS`, exit 0
- [x] Commit: `fix: split-on-newline fence line model and CommonMark opener deviations (r5 findings 7-8)`

### Task 3: Remaining arms and mechanical folds (findings 5-6, 9-12)

All green-today changes verified at authoring time; no behavior change beyond the two new arms.

Files:
- `scripts/plan_readiness.py`

Except where an item says otherwise (scratch-only), every checklist item in this task edits the file listed above.

- [x] Finding 5: add fail-arm `trailer_inside_tilde_close_with_info_text_fails` (needle `"missing decision-points trailer"`): plan_text `"# P\n\n## Assumptions\n\nNone needed.\n\n~~~\nquoted template\n~~~ end\n" + trailer + "none remain.\n~~~\n"`; a tilde closer line carrying info text is fence content, not a closer (tilde-side twin of the info-text backtick arm; green under the current parser, verified)
- [x] Finding 6: add pass-arm `trailer_after_backtick_block_with_stray_tildes_passes`: plan_text `"# P\n\n## Assumptions\n\n```\nquoted template\n~~~\nmore quoted text\n```\n\n" + trailer + "none remain.\n"`; a stray `~~~` line inside an open backtick fence must not toggle fence state (cross-character mirror of `trailer_after_tilde_block_with_stray_backticks_passes`; green under the current parser, verified)
- [x] Finding 9: in `decision_marker_problem`, drop the dead `value.strip()` and `value.lstrip()` calls and use `value` directly; safe only after Task 2 (the per-line `"\r"` normalization) because the regex's `[ \t]*$` anchor guarantees no trailing space or tab but not a trailing carriage return
- [x] Finding 10: fold the three bespoke sidecar-mutation arms into one `(name, comment, mutate)` table with a single fixture write and one `mutate(sidecar)` call per row: `sidecar_date_missing_exempt` deletes the `date` key, `sidecar_date_blank_exempt` sets it to `" "`, `sidecar_date_malformed_exempt` sets it to `"2026-09-08T12:00"`; names, rationale comments, and `expect_ok=True` unchanged
- [x] Finding 11: prune name-restating comments: delete the six bare restating comment lines (`# plan_outside_plans_dir.`, `# missing_plan_path.`, `# gated_none_remain_passes.`, `# gated_missing_trailer_fails.`, `# gated_placeholder_trailer_fails.`, `# gated_receipt_passes.`), and for arms-table comments whose first word restates the tuple's first element, strip that leading name token and keep the rationale text (discovery aid: `grep -nE '^\s*# [a-z0-9_]+(/[a-z0-9_]+)?[.:]\s*$' scripts/plan_readiness.py`; wrapped-sentence tails such as `# gate.` are continuation lines, keep them)
- [x] Finding 12: fix the `_strip_fences` docstring clause that states the opposite of the code (`len(m.group(1)) >= fence[1]`): it must read "a shorter run never closes a longer one early in the fail-open direction"
- [x] Run → expect GREEN: `ALL PASS`, exit 0
- [x] Commit: `refactor: trailer-gate arms and parser cosmetics (r5 findings 5-6, 9-12)`

### Task 4: Final validation

Files:
- `scripts/plan_readiness.py`

Except where an item says otherwise (scratch-only), every checklist item in this task edits the file listed above.

- [x] Run the Validation Commands block → expect `ALL PASS`, exit 0
- [x] Arm-name preservation: regenerate the name set into `docs/tmp/decision-marker-names.after` and run `comm -23 docs/tmp/decision-marker-names.before docs/tmp/decision-marker-names.after`; expect EMPTY output (no name removed), and `comm -13` shows exactly the seven new names (`backtick_info_opener_is_paragraph_passes`, `crlf_fenced_quote_passes`, `tab_indented_closer_line_is_content_fails`, `tab_indented_fence_line_is_content_passes`, `trailer_after_backtick_block_with_stray_tildes_passes`, `trailer_after_unicode_separator_close_stays_fenced`, `trailer_inside_tilde_close_with_info_text_fails`)
- [x] Scope check: `git log --name-only <base>..HEAD` over the commits this plan created lists only `scripts/plan_readiness.py` over the base recorded by Task 1: git log --name-only "$(cat docs/tmp/trailer-gate-base-sha.txt)"..HEAD
- [x] Delete the scratch files `docs/tmp/decision-marker-names.before`, `docs/tmp/decision-marker-names.after`, `docs/tmp/trailer-gate-base-sha.txt`, and any replay-probe scratch
