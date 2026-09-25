# Plan: straggler wording/pins direct fixes (telemetry r5 residuals + prose-sweep fold-5 pin)

Backlog:
- docs/history/backlog/2026-09-07-token-telemetry-r5-residuals.md
- docs/history/backlog/2026-09-06-prose-sweep-fold5-pin-gap.md

Origin reviews:
- docs/reviews/2026-09-07-2026-09-06-token-usage-telemetry-code-review-r5.md (findings N1, N2, N3; Low, non-blocking, deferred at the 5-round cap)
- docs/reviews/2026-09-06-certified-plan-prose-residue-sweep-code-review-r1.md (finding 1, testing lens, Low, non-blocking)

## Assumptions

- assume backlog item 1 (cwd-less first `session_meta`) is fixed by the documented-accepted-drop option, not the scan-later-metas behavior change; basis: the behavior option would rework the N1/N5 identity pins (FIRST meta decides identity, `cwd_ok` computed once) that the executed telemetry plan certified, for a Low residual on a malformed-input path, while the module already carries an accepted-limitations docstring paragraph in exactly this style. The fix is: document the drop in that paragraph plus a pinning selftest witness.
- assume item 3's home-matching fix checks the path-component boundary AFTER the home occurrence (end of string, a `/`, or a non-path delimiter such as a closing quote), rather than only "at string start or after a path separator" as the backlog sketch words it; basis: the reported mangling (`/Users/name2/...` becoming `~/2/...`) is anchored at string start, so a left-side-only rule still mangles it, and a left-side constraint would break the documented mid-text quoted-path case (`[Errno 2] ...: '/Users/...'`) that `_abbreviate_home_str` exists to cover; the trailing component boundary fixes the reported class and keeps every currently abbreviated case abbreviated, including a quoted home path with no trailing component (`...: '/Users/name'`), which is why the boundary also accepts a non-`/` delimiter and rejects only word characters, dots, and dashes (siblings like `/Users/name2` or `/Users/name.txt` pass through).
- assume the strict six-key gate for `usage.totals` also treats a MISSING key as malformed (treated absent), not as a zero; basis: the backlog item's own prescription ("require all six keys to coerce to non-None ints, else return None").
- assume the fold-5 pin task also repoints the archived prose-sweep plan's `PL_DOC` to the `docs/plans/completed/` path; basis: the target plan was archived on 2026-09-06 (validator-pass-r4-residuals execution) and the block now greps a missing file, so pins added without the repoint would be vacuous (a forbidden-match guard reads a grep file-error as "no match"; a positive pin aborts under `set -e`). The repoint is the mechanical consequence of the archive, not a re-opened fold.
- assume the fold-5 pins are GREEN-today by design; basis: the fold-5 edit landed and was manually verified on 2026-09-06 (the backlog's "Why deferred" paragraph); the pins exist to make the plan's "each prescribed replacement text appears exactly once" criterion assertion-complete for fold 5, guarding against future regression, not to flip a pending edit.
- assume editing `docs/plans/completed/2026-09-05-certified-plan-prose-residue-sweep.md` (an executed, archived plan) deliberately supersedes its certified digest; basis: the backlog item's own "Fix when" clause authorizes exactly this successor-plan re-open, and precedent `docs/plans/completed/2026-09-02-r5-residuals-fixes.md` (post-certification wording amendments covered by the successor plan's review).
- assume both backlog items stay in place under `docs/history/backlog/` while this plan is open; they move to `backlog_completed_dir` with `Status: done` in this plan's completion pass, per the plans lifecycle.

## Gist & Examples

Four small direct fixes that close the two straggler backlog items. Three are Low, non-blocking residuals in the token-usage telemetry scripts from the r5 code-review cap; one is a missing validation pin on an archived plan. No digest-gated content is re-opened beyond what each backlog item prescribes.

1. **`_abbreviate_home_str` sibling mangling (backlog item 3, review N3).** The helper replaces every occurrence of the home path, so a sibling-of-home path such as `/Users/name2/notes` inside an exception message is mangled to `~/2/notes` in stderr diagnostics. Cosmetic, no leakage. The fix requires the home occurrence to end at a path-component boundary (end of string or `/`), so siblings pass through unchanged while every genuine home path (start, under-home, mid-text quoted) still abbreviates.

   Before (today), with home `/Users/name`:

   ```
   FileNotFoundError: [Errno 2] No such file or directory: '/Users/name2/notes'
   ```

   abbreviates to `FileNotFoundError: [Errno 2] No such file or directory: '~/2/notes'`.

   After, the sibling text passes through unchanged, while `'/Users/name/notes'` still abbreviates to `'~/notes'`.

2. **Garbage-string `usage.totals` counted in the coverage numerator (backlog item 2, review N2).** `_usage_totals_from_payload` gates only on `isinstance(totals, dict)` and then maps every value through `_coerce_int`, which sends garbage strings to 0. A sidecar whose totals are all garbage therefore counts as "has usage" in the coverage numerator while contributing zero tokens, contradicting the module's "malformed usage record is treated as absent" seam claim. The fix requires all six `_USAGE_TOTAL_KEYS` values to coerce to non-None ints, else the record returns None (treated absent, excluded from the numerator). Missing keys count as malformed under the same gate. This only ever shrinks the numerator (conservative direction).

   Before: `usage.totals = {"input_tokens": "many", ...}` (all six keys garbage strings) counts toward coverage with zero tokens.
   After: the same payload returns None and the sidecar counts as without usage.

3. **cwd-less first `session_meta` silently dropped (backlog item 1, review N1).** A Codex rollout whose FIRST parseable `session_meta` carries a `session_id` but no `cwd` is dropped (cwd_ok False breaks the read) even when a later meta names the matching repo cwd; the drop is invisible and undocumented. Per the assumption above, the accepted-drop option applies: the module docstring's accepted-limitations paragraph gains the drop sentence, and a characterization selftest witness pins the behavior so a future refactor cannot change it silently.

4. **Fold-5 validation pin on the archived prose-sweep plan (second backlog item).** The archived plan's Validation Commands pin folds 1-4 (positive `-eq 1` pins plus superseded-span guards) but have no pin and no guard for fold 5 (the Task 1 second-checklist-bullet rationale reword), so a skipped, partial, or wrong fold-5 edit would still pass the block. The fix adds the positive pin on the new span and the two forbidden-match guards on the old spans, and repoints `PL_DOC` to the target's archived path (see Assumptions). Verified at authoring time against the current tree: the new span occurs exactly once in the archived target, both old spans occur zero times, so the added pins are green today and fire on regression.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each fix matches its backlog item's prescription (with the two recorded assumption refinements); existing behavior otherwise unchanged (`--selftest` fully green on both scripts after each task)
- observability/documentation: the cwd-less drop is no longer undocumented (docstring sentence plus pinning selftest witness); the home-abbreviation rule is stated in the docstring it replaces
- assertion-completeness: after Task 4, every prose-sweep fold (1 through 5) has both a positive pin and superseded-span guards in the archived plan's Validation Commands
- immutability: edits outside the prescribed functions/spans are rejected; the archived prose-sweep plan's Task/Review-Scope prose stays frozen

**Done when:**
- both script selftests exit 0 end to end
- the archived prose-sweep plan's full Validation Commands block exits 0 end to end against the post-edit tree
- the Validation Commands below exit 0

**Ship when:**
- (none; all work is repository-local script and Markdown edits)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/review_usage_capture.py` (only: `_abbreviate_home_str` and its docstring, the module docstring accepted-limitations paragraph, the rollout fixture builder extension prescribed by Task 3, and the new selftests; all other functions frozen)
- `scripts/summarize_review_stats.py` (only: `_usage_totals_from_payload`, a new strict coercion helper next to `_coerce_int`, and the new selftest; `_coerce_int` itself and all other functions frozen)

**Documentation:**
- `docs/plans/completed/2026-09-05-certified-plan-prose-residue-sweep.md` (only: the `PL_DOC=` line, the `PLAN_FILE=` line, and the fold-5 pin/guard insertions inside the Validation Commands block; all other content frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`, `scripts/validate_review_staging.py`, and any other script; reason: the backlog items name exactly two script files
- any other plan document under `docs/plans/`; reason: the only plan edit is the prescribed prose-sweep validation block
- the two backlog item files themselves during execution; reason: they move in the completion pass, not by a plan task

## Validation Commands

```bash
set -euo pipefail
python3 scripts/review_usage_capture.py --selftest
python3 scripts/summarize_review_stats.py --selftest

SWEEP_DOC="docs/plans/completed/2026-09-05-certified-plan-prose-residue-sweep.md"
TARGET_DOC="docs/plans/completed/2026-09-05-validator-pass-r4-deferred-residuals.md"
test -f "$SWEEP_DOC" || { echo 'FAIL: sweep plan missing'; exit 1; }
test -f "$TARGET_DOC" || { echo 'FAIL: archived target plan missing'; exit 1; }

# Task 4 pins exist in the sweep plan's validation block (positive pins, exactly once).
test "$(grep -cF "grep -cF 'the entry count depends on how many parsing passes'" "$SWEEP_DOC")" -eq 1 || { echo 'FAIL: fold-5 positive pin missing'; exit 1; }
test "$(grep -cF "if grep -qF 'exactly ONE entry'" "$SWEEP_DOC")" -eq 1 || { echo 'FAIL: fold-5 old-rationale guard missing'; exit 1; }
test "$(grep -cF "if grep -qF 'legacy-panel-mode'" "$SWEEP_DOC")" -eq 1 || { echo 'FAIL: fold-5 legacy-span guard missing'; exit 1; }
grep -qF 'PL_DOC="docs/plans/completed/2026-09-05-validator-pass-r4-deferred-residuals.md"' "$SWEEP_DOC" || { echo 'FAIL: PL_DOC not repointed to archived path'; exit 1; }
grep -qF 'PLAN_FILE="docs/plans/completed/2026-09-05-certified-plan-prose-residue-sweep.md"' "$SWEEP_DOC" || { echo 'FAIL: PLAN_FILE not repointed to archived path'; exit 1; }

# The archived plan's full validation block passes end to end (includes bash -n of itself).
mkdir -p docs/tmp
awk '/^```bash$/{f=1;next} /^```$/{f=0} f' "$SWEEP_DOC" > docs/tmp/straggler-sweep-validation-extract.sh
bash docs/tmp/straggler-sweep-validation-extract.sh || { echo 'FAIL: sweep validation block'; exit 1; }
rm -f docs/tmp/straggler-sweep-validation-extract.sh

# Formatting gates over this plan file.
PLAN_FILE="docs/plans/2026-09-07-straggler-wording-pins.md"
bash scripts/check-no-em-dash.sh file "$PLAN_FILE" || { echo 'FAIL: em dash in plan'; exit 1; }
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh || { echo 'FAIL: hygiene scan'; exit 1; }
```

Authoring-time record (2026-09-07, against the pre-edit tree): the three Task 4 pin greps and the two repoint greps were executed against the current `SWEEP_DOC` and all five returned 0 (pins absent, RED-today), and the pin patterns were positively controlled against the archived target (`the entry count depends on how many parsing passes` occurs exactly once; `exactly ONE entry` and `legacy-panel-mode` occur zero times in `docs/plans/completed/2026-09-05-validator-pass-r4-deferred-residuals.md`), so the pins flip green exactly when Task 4 lands and the guards fire if the old spans ever return.

### Task 1: Component-boundary home abbreviation in `review_usage_capture`

Files:
- `scripts/review_usage_capture.py`

- [ ] `review_usage_capture#selftest_abbreviate_home_sibling_prefix`; given home `/Users/name`, expects `_abbreviate_home_str("/Users/name2/notes", home)` unchanged (no `~/2`), `"/Users/name/sub"` becomes `"~/sub"`, `"/Users/name"` becomes `"~"`, `FileNotFoundError: [Errno 2] No such file or directory: '/Users/name/notes'` becomes the same text with `'~/notes'` (mid-text quoted home still abbreviated), and the quoted exact home `FileNotFoundError: [Errno 2] No such file or directory: '/Users/name'` becomes the same text with `'~'` (regression witness for the quoted-exact-home class)
- [ ] Run → expect RED: `python3 scripts/review_usage_capture.py --selftest` fails in the new witness (sibling input mangles to `~/2/notes` today)
- [ ] Implement: `_abbreviate_home_str` matches the home occurrence only when it ends at a path-component boundary, via `re.sub(re.escape(str(home)) + r"(?=/|\Z|[^\w.-])", "~", s)` (no left-side constraint; the boundary accepts end of string, `/`, or a non-path delimiter such as a closing quote, and rejects word characters, dots, and dashes so siblings like `/Users/name2` and `/Users/name.txt` pass through; see Assumptions); add a module-level `import re` if absent (the module today has no top-level `re` import); update the docstring rationale from "plain textual replacement" to the component-boundary rule and why (sibling paths like `/Users/name2` must pass through)
- [ ] Run → expect GREEN: `python3 scripts/review_usage_capture.py --selftest` exits 0
- [ ] Commit: `fix: abbreviate home only at path-component end in review_usage_capture`

### Task 2: Strict totals gate in `summarize_review_stats`

Files:
- `scripts/summarize_review_stats.py`

- [ ] `summarize_review_stats#garbage_string_totals_treated_absent`; given a payload whose `usage.totals` maps all six `_USAGE_TOTAL_KEYS` to garbage strings (for example `"input_tokens": "many"`), expects `_usage_totals_from_payload` returns None
- [ ] `summarize_review_stats#garbage_string_totals_partial_missing_key`; given a payload whose `usage.totals` has five int values and one missing key, expects `_usage_totals_from_payload` returns None (missing key is malformed, per Assumptions)
- [ ] `summarize_review_stats#garbage_string_totals_valid_still_parses`; given a payload whose `usage.totals` has all six keys as ints, expects `_usage_totals_from_payload` returns the coerced dict (positive control: no regression on the shape current fixtures carry)
- [ ] Run → expect RED: `python3 scripts/summarize_review_stats.py --selftest` fails in the two new witnesses (garbage totals return a zero-filled dict today)
- [ ] Implement: add a strict coercion helper returning `int | None` (bool excluded, int accepted, integral float accepted, everything else None) next to `_coerce_int`; `_usage_totals_from_payload` returns None unless every `_USAGE_TOTAL_KEYS` value coerces to a non-None int; keep `_coerce_int` and all other callers unchanged; reword `_usage_totals_from_payload`'s docstring so the stale "Tolerance mirrors the validator's" sentence states the new strict contract (all six keys must coerce, else the record is treated as absent)
- [ ] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` exits 0
- [ ] Commit: `fix: treat non-coercible usage totals as absent in summarize_review_stats`

### Task 3: Document the cwd-less first-meta drop with a pinning witness

Files:
- `scripts/review_usage_capture.py`

- [ ] `review_usage_capture#selftest_codex_first_meta_cwd_less_drop`; given a rollout file whose first `session_meta` carries a `session_id` but no `cwd`, followed by a `token_count` event and a later `session_meta` naming the anchor cwd, expects the capture result contains no record for that file (characterization witness for the accepted drop; GREEN today and must stay GREEN)
- [ ] Fixture route: the rollout fixture builder (`_Fixture.codex_rollout`) cannot express a cwd-less first `session_meta` (its `cwd=None` means the repo cwd, not absent); extend it with an explicit route for a first meta without a cwd key (existing callers' behavior unchanged), and build this witness through that route
- [ ] Run → expect GREEN (characterization: captures the documented accepted drop before the docstring edit; no behavior change in this task)
- [ ] Module docstring, accepted-limitations paragraph: append the drop sentence, in the same style as the surrounding limitations: a rollout whose first `session_meta` carries no `cwd` is dropped even when a later meta names the matching repo cwd (N1 keeps the FIRST meta as the sole identity decider; scanning later metas would let a foreign meta claim usage already parsed)
- [ ] Run → expect GREEN: `python3 scripts/review_usage_capture.py --selftest` exits 0
- [ ] Commit: `docs: document accepted cwd-less first-meta drop in review_usage_capture`

### Task 4: Add the fold-5 validation pin to the archived prose-sweep plan

Files:
- `docs/plans/completed/2026-09-05-certified-plan-prose-residue-sweep.md`

- [ ] Replace the line `PL_DOC="docs/plans/2026-09-05-validator-pass-r4-deferred-residuals.md"` with `PL_DOC="docs/plans/completed/2026-09-05-validator-pass-r4-deferred-residuals.md"` and replace the line `PLAN_FILE="docs/plans/2026-09-05-certified-plan-prose-residue-sweep.md"` with `PLAN_FILE="docs/plans/completed/2026-09-05-certified-plan-prose-residue-sweep.md"`; add a one-line comment beside them: both targets were archived on 2026-09-06 (validator-pass-r4 execution); the pin and extraction paths follow the archive
- [ ] After the existing Task 1 positive pins (the `-n`-less grep pin line), insert the fold-5 positive pin: `test "$(grep -cF 'the entry count depends on how many parsing passes' "$PL_DOC")" -eq 1 || { echo 'FAIL: fold-5 reworded rationale missing'; exit 1; }`
- [ ] After the existing Task 1 superseded-span guards (the typing-import guard line), insert the two fold-5 guards: `if grep -qF 'exactly ONE entry' "$PL_DOC"; then echo 'FAIL: fold-5 old rationale survives'; exit 1; fi` and `if grep -qF 'legacy-panel-mode' "$PL_DOC"; then echo 'FAIL: fold-5 old legacy span survives'; exit 1; fi`
- [ ] Run → expect the plan-level pin checks above to flip green and the archived block to exit 0 end to end (the pins are green-today against the archived target by design; see Assumptions)
- [ ] Commit: `plans: add fold-5 validation pin to archived prose-sweep plan`

### Task 5: Final validation and audits

- [ ] Run → expect GREEN: the full Validation Commands block exits 0 end to end
- [ ] Pin-vs-prescription audit: every new grep pin in the archived block occurs exactly once in the sweep plan's Validation Commands and matches the prescribed snippet byte-for-byte; run `bash -n` over the extracted block (already covered by the block's own tail; confirm no regression)
- [ ] Sweep this plan's Assumptions, Gist, Evaluation Criteria, and Validation Commands for branch names or branching/push constraints; remove any hit (the plan must stay branch-agnostic)
- [ ] Commit: `plans: straggler wording/pins direct fixes (telemetry r5 residuals + fold-5 pin)`
