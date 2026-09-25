# Plan: plan-readiness polish (four residual backlog items)

Backlog origins:
- `docs/history/backlog/2026-09-05-plan-readiness-migration-r5-residuals.md` (two folds into the archived migration plan doc)
- `docs/history/backlog/2026-09-05-plan-readiness-readme-eligibility-positivity-clause.md`
- `docs/history/backlog/2026-09-05-plan-readiness-selftest-fixture-runner-extraction.md`
- `docs/history/backlog/2026-09-05-plan-readiness-task5-fence-annotation.md`

Reference: the executed and archived `docs/plans/completed/2026-09-05-plan-readiness-migration.md` plan (fold target for three of the four items).

## Terms

- **readiness validator**: `scripts/plan_readiness.py`, the fail-closed gate called by `execute-plan` and `done` on a saved plan artifact.
- **the migration plan doc**: `docs/plans/completed/2026-09-05-plan-readiness-migration.md`, the executed and archived plan whose Tasks 2 and 5 receive historical folds in this plan.
- **hook README**: `agents/hooks/plan-readiness/README.md`.
- **doc_has**: the flatten-grep helper pattern used in this plan's Validation Commands (flatten newlines to spaces, fixed-string match, fail loud on miss).
- **RED-today proof**: executing a forbidden-pattern or missing-obligation check against the current tree at authoring time and recording that it fires, so the gate flips GREEN exactly when its task lands.

## Assumptions

- assume the fold target for the three plan-doc residual items is the archived copy `docs/plans/completed/2026-09-05-plan-readiness-migration.md`, not the pre-archive path `docs/plans/2026-09-05-plan-readiness-migration.md` named in two items; basis: the migration plan completed and was archived to `docs/plans/completed/` on 2026-09-05, and the task5-fence item itself scopes to the archived copy.
- assume folds into the archived migration plan doc are historical prescription corrections (the same convention as that doc's existing `(rN FN fold: ...)` divergence annotations), not re-execution instructions; basis: the migration plan is fully checked off and archived.
- assume the selftest extraction is behavior-preserving with identical fixture names and identical check output; basis: the extraction item's own suggested fix states this contract.
- assume all four promoted backlog items move to `docs/history/backlog/completed/` with `Status: done` at this plan's completion pass, per the plans lifecycle; basis: plans skill Plan Lifecycle.

## Gist & Examples

Five deferred findings across four backlog items (the migration-r5-residuals item bundles two folds) are cleaned up in one pass: three are historical wording folds into the archived migration plan doc, one is a real doc bug in the hook README, and one is a maintainability refactor of the readiness validator's selftest.

**Hook README eligibility clause (Before/After).** Trigger: a maintainer reads only the hook README's Verdict representation section to decide when the legacy Summary grammar can be deleted. **Before (today):** the README states the deletion eligibility gate as only "`--sweep` coverage reports covered equal to total over the live plan-review corpus", while the sweep's actual print (`run_sweep` in `scripts/plan_readiness.py`) and the deletion backlog item both gate on `total is positive and covered equals total`. A maintainer could treat an empty corpus (0/0, sweep exit 0) as eligible. **After (this plan):** the README sentence reads "coverage reports a positive total with covered equal to total over the live plan-review corpus", matching the code and the deletion item.

**Archived plan doc folds.** The migration plan doc records three divergences incompletely: (a) its Task 5 review-loop fence lacks the divergence annotation that its other fences carry, so a reader comparing the fence to the shipped `agents/skills/review-loop/SKILL.md` paragraph sees unexplained wording drift (the shipped paragraph names a missing reviews_dir and sibling compat failure as additional non-zero-exit causes); (b) its Task 5 interim "Run → expect GREEN" gate does not say that the full Validation block fails at that task point (the em-dash loop's `test -f` pre-check fails on the Task 7 backlog file, which does not exist until Task 7); (c) its Task 2 Integration Points anchor text renders without the backticks the host sentence carries around `ready=yes` and `## Summary`, and its clause-fragment replacement fence leaves the host sentence mildly ungrammatical. Each gets a targeted fold matching the doc's existing annotation convention.

**Selftest fixture-runner extraction (Before/After).** Trigger: a maintainer adds or edits a fixture family in `run_selftest`. **Before (today):** `run_selftest` spans over 1200 lines; the cleanup idiom `for path in reviews_dir.iterdir(): path.unlink()` occurs 34 times, and each fixture family hand-repeats the write-state / run / check / clean sequence. **After (this plan):** a fixture context helper owns the write-state / yield / clean-reviews-dir-on-exit cycle (and/or per-family functions called from `run_selftest`), the cleanup idiom exists once, and the full selftest still prints the identical 90 `PASS: selftest#...` lines and `ALL PASS`.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the hook README eligibility sentence matches the gate the sweep actually enforces (positive total AND covered equals total); the readiness selftest passes before and after the refactor with byte-identical check names and verdicts.
- maintainability: the per-fixture cleanup idiom in `run_selftest` collapses from 34 occurrences to one shared helper; fixture families read as write-state / run / check without hand cleanup.
- documentation consistency: the three folds into the archived migration plan doc follow that doc's existing annotation convention and leave no new contradiction with the shipped skill files.

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` prints 90 `PASS:` lines and `ALL PASS` on the refactored tree.
- The Validation Commands block below exits 0 end to end.

**Ship when:**
- The four promoted backlog items are archived to `docs/history/backlog/completed/` with `Status: done` in the plan completion pass (repository-verifiable at completion, not by an executor task).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (only `run_selftest` and new selftest-local helpers; all other functions are frozen; reject any review finding that touches them)

**Tests:**
- none new; the readiness selftest itself is the characterization net and is part of `scripts/plan_readiness.py` above

**Docs:**
- `agents/hooks/plan-readiness/README.md` (Verdict representation section eligibility sentence only; all other sections frozen)
- `docs/plans/completed/2026-09-05-plan-readiness-migration.md` (three named fold sites only: the Task 5 review-loop fence annotation, the Task 5 interim-run gate sentence, the Task 2 Integration Points anchor/fence; all other content frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-plan/SKILL.md`, `agents/skills/review-loop/SKILL.md`, `agents/skills/review-staging/SKILL.md`, `scripts/validate_review_staging.py`; reason: these carry the migration plan's executed shape and are frozen history for this plan, whose folds only annotate the archived prescription
- `docs/plans/2026-09-04-backlog-gate-hardening.md`, `projects/.ai-playbook/development_lessons.md`, `scripts/check_backlog_inbox_location.py`; reason: peer-session or peer-owned working-tree state at authoring time, untouched by this plan (verify current dirtiness at execution before treating any of them as present)
- `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md`; reason: the time-gated deletion item is a separate tracked concern, not touched here

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
python3 scripts/plan_readiness.py --selftest || { echo "FAIL: plan_readiness selftest"; exit 1; }
PASS_COUNT="$(python3 scripts/plan_readiness.py --selftest | grep -c '^PASS')"
test "$PASS_COUNT" -eq 90 || { echo "FAIL: expected 90 PASS lines, got $PASS_COUNT"; exit 1; }
python3 scripts/plan_readiness.py --selftest | grep -qF 'PASS: selftest#legacy_or_unsupported_sidecar/bypass_closed_after_edit' || { echo "FAIL: sentinel check-name pin"; exit 1; }
GOLD="$(python3 scripts/plan_readiness.py --selftest | grep '^PASS: selftest#' | LC_ALL=C sort | shasum -a 256 | cut -d' ' -f1)"
test "$GOLD" = "d8e1292f83fd3592031cf7fcd72c4e296060608a28b8102570cbce06afc27cc2" || { echo "FAIL: selftest check-name golden hash drift: $GOLD"; exit 1; }
# Docs obligations: one dedicated flatten-grep per obligation (newline-tolerant).
doc_has() { tr '\n' ' ' < "$2" | grep -qF "$1" || { echo "FAIL: missing in $2: $1"; exit 1; }; }
doc_has 'coverage reports a positive total with covered equal to total' agents/hooks/plan-readiness/README.md
doc_has 'shipped paragraph broadens the non-zero-exit meaning' docs/plans/completed/2026-09-05-plan-readiness-migration.md
doc_has 'the em-dash loop and the full Validation block run only at Task 8' docs/plans/completed/2026-09-05-plan-readiness-migration.md
doc_has 'wraps `ready=yes` and `## Summary` in backticks' docs/plans/completed/2026-09-05-plan-readiness-migration.md
doc_has 'as a full-sentence replacement block' docs/plans/completed/2026-09-05-plan-readiness-migration.md
# Forbidden: the pre-fix README eligibility wording must be gone. Flattened
# sweep: the phrase is line-wrapped in the file today (RED-today verified at
# authoring: the flatten-grep fires on the pre-fix tree). The new wording
# ("a positive total with covered equal to total") does not match this fixed
# string, so the gate stays GREEN after Task 1 lands.
if tr '\n' ' ' < agents/hooks/plan-readiness/README.md | grep -qF 'coverage reports covered equal to total'; then echo "FAIL: stale README eligibility wording"; exit 1; fi
# Forbidden: the hand-rolled per-fixture cleanup idiom must not survive in
# run_selftest after the extraction (RED-today verified: 34 occurrences today).
# The pattern is split across lines in the source, so count the iterdir loop
# heads; the shared helper owns the single allowed occurrence.
CLEANUPS="$(grep -c 'for path in reviews_dir.iterdir' scripts/plan_readiness.py)"
test "$CLEANUPS" -le 1 || { echo "FAIL: $CLEANUPS hand-rolled cleanup loops remain in run_selftest"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "FAIL: hygiene scan"; exit 1; }
```

### Task 1: Hook README eligibility positivity clause (backlog: readme-eligibility-positivity-clause)

Files:
- `agents/hooks/plan-readiness/README.md`

- [x] In the Verdict representation section, in the sentence with anchor text `Deleting the legacy Summary grammar is TIME-GATED`, replace the span from `eligible only` through `plan-review corpus` (currently reading `eligible only once `--sweep` coverage reports covered equal to total over the live plan-review corpus`, line-wrapped across three lines) with exactly (the line wrap in the file may differ; the sentence text is what is pinned):

```text
eligible only once `--sweep` coverage reports a positive total with covered equal to total over the live plan-review corpus
```

- [x] Run → expect GREEN: `tr '\n' ' ' < agents/hooks/plan-readiness/README.md | grep -qF 'coverage reports a positive total with covered equal to total'` succeeds, and the stale-wording forbidden sweep from the Validation Commands block prints nothing (it is RED on today's pre-fix tree, verified at authoring)
- [x] Commit: `docs: hook README eligibility gate requires a positive sweep total`

### Task 2: Archived migration plan doc folds (backlog: migration-r5-residuals, task5-fence-annotation)

Files:
- `docs/plans/completed/2026-09-05-plan-readiness-migration.md`

- [x] Fold (task5-fence-annotation): immediately after the closing fence of the Task 5 review-loop paragraph ```text block (the fence whose body starts `**Verdict-shape drift check (every round, before launching the review):**`), insert this annotation line as its own paragraph, matching the doc's existing fence-annotation convention:

```text
(r3 review-fix note: the shipped paragraph broadens the non-zero-exit meaning to name a missing or misconfigured reviews_dir and a sibling compatibility failure; the fence records the prescription, not the final bytes.)
```

- [x] Fold (r5 residual, interim-gate scope): in the Task 5 checklist item beginning `- [x] Run → expect GREEN: the Validation Commands doc-grep section passes`, append this sentence before the existing trailing sentence about the tie-break fixture: `Restrict this interim run to the doc-grep lines and the forbidden-README check; the em-dash loop and the full Validation block run only at Task 8 (the em-dash loop is one line inside that block; its `test -f` pre-check fails on the Task 7 backlog file, which does not exist yet).`
- [x] Fold (r5 residual, anchor accuracy): in the Task 2 checklist item beginning `- [x] `review-plan/SKILL.md` Integration Points validator paragraph`, replace the span-description text `replace the full span from `and the review Markdown reports `ready=yes` in its `## Summary` with zero unresolved blocking findings (`is_review_ready`)` (backticks included, through the closing paren) with exactly:` with exactly `replace the ENTIRE final sentence, which wraps `ready=yes` and `## Summary` in backticks, from `and the review Markdown reports` through the closing paren of `(`is_review_ready`)`, as a full-sentence replacement block with exactly:` so the anchor is backtick-accurate and the replacement is stated as a full sentence
- [x] Same item, replace the clause-fragment fence body `the verdict is established from the sidecar `verdict` field first, with the Summary total rule over the review Markdown as the legacy fallback, and alongside zero unresolved blocking findings (`is_review_ready`)` with the full-sentence fence body:

```text
and reports zero unresolved blocking findings (`is_review_ready`); the verdict is established from the sidecar `verdict` field first, with the Summary total rule over the review Markdown as the legacy fallback.
```

Then append this divergence note line below the fence's existing annotations, keeping chronological fold order (after the pre-existing r4 F4 fold line):

```text
(r5 executed-shape note: the shipped sentence carries further wording from the later r7 F1 fold about Summary-only edits; the fence records the prescription, not the final bytes.)
```

- [x] Run → expect GREEN: all four migration-doc doc_has pins from the Validation Commands block succeed against the edited file; this task's folds produce all four
- [x] Commit: `docs: fold r5 residuals + task5 fence annotation into archived migration plan`

### Task 3: run_selftest fixture-runner extraction (backlog: selftest-fixture-runner-extraction)

Files:
- `scripts/plan_readiness.py`

- [x] Run → expect GREEN (characterization baseline, before the refactor): `python3 scripts/plan_readiness.py --selftest` prints 90 `PASS:` lines ending `ALL PASS` (verified at authoring on the pre-refactor tree)
- [x] Extract the fixture lifecycle into module-level private helpers in `scripts/plan_readiness.py`, keeping every existing check name string (`selftest#...`) and the PASS/FAIL output format byte-identical: (a) one reviews-dir context helper (for example a `_selftest_reviews_dir` contextmanager or a `_clean_reviews_dir(reviews_dir)` function called by a context helper) that owns the reviews-dir cleanup, replacing the 34 hand-rolled `for path in reviews_dir.iterdir(): path.unlink()` loops (the final Validation Commands block allows at most one remaining occurrence; the shared helper's own implementation may be that one); (b) per-family fixture functions named `_selftest_<family>` at MODULE level (not nested inside `run_selftest`, so `run_selftest` shrinks to a dispatcher over the families), each receiving the shared `plans_dir`/`reviews_dir` paths and the `check` callback it needs; `write_clean_state`, `_review_markdown`, and `_clear_sidecar` keep their signatures and semantics and move to module level only if the family functions need them (otherwise they stay in place)
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` still prints exactly 90 `PASS:` lines ending `ALL PASS`; `grep -c 'for path in reviews_dir.iterdir' scripts/plan_readiness.py` reports at most 1
- [x] Commit: `refactor: extract fixture runner helpers from plan_readiness run_selftest`

### Task 4: Final validation

Files: none (checks only)

- [x] Run the full `## Validation Commands` block from the repo root; every check exits 0 (selftest with 90 PASS pins, doc_has pins over the hook README and the archived migration plan doc, the two forbidden-pattern sweeps, hygiene scan)
- [x] If any check fails: fix and re-run the whole block; only then report the task complete (no commit line unless a fix was needed; a fix commit reuses the owning task's commit prefix)
