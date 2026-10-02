# Plan: Scanner and validator parallel-surface single-sourcing

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-19-scanner-allowlist-glob-single-source.md`
- `docs/history/backlog/2026-09-19-validator-fence-classifier-parameterization.md`

Driving force: code-quality + simplicity
Plan review record: the staging series docs/reviews/2026-10-03-plan-review-scanner-validator-single-sourcing-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

One declared owner per hand-copied parallel surface in the public-hygiene scanner and the review-staging validator, so the copies can no longer drift silently.

- Adding an allowlist glob edits exactly one list in scripts/scan-public-hygiene.sh, and all three scan modes (full tree, changed-from, explicit paths) follow it mechanically.
- The two date-fence classifiers and the five inline non-canonical derivations in scripts/validate_review_staging.py collapse onto single helpers, so a rule change is one edit instead of two or five.
- scripts/review_record_selection.py's fence mask consumes the validator's shared fence state machine through a declared seam, with its intentional opener divergence carried as a named parameter.
- The scanner selftest asserts surface agreement, so a future hand-copied divergence fails its own gate instead of waiting for an incident.

Gate delta: counted classes (refusal classes, hard gates, fences, protocol layers, schema state fields) +0 added, +0 removed: every consolidation preserves the existing classifications exactly (same fence constants, same three-clause predicate, same close rule); the one declared behavior alignment is the explicit-paths mode's root LICENSE.txt scan instance being removed, which is the r3 F5 asymmetry the scanner origin records as the known instance to resolve, removed by the glob allowlist becoming the single owner rather than by a refusal-class change; prose and test additions (the shared helpers, the declared seam parameter, the selftest agreement arms) are not counted classes.

## Terms

- **glob surface**: one of the three places scripts/scan-public-hygiene.sh applies the standard allowlist globs: the rg-fed array, the changed-from per-path filter, and the explicit-paths predicate.
- **date-fence classifier**: the two-surface classifier that parses a staging filename's leading date and a sidecar date and classifies each as undated, pre-fence, or post-fence against a minimum-date constant.
- **non-canonical predicate**: the declared record-kind test (present, enum-valid, different from canonical) that five validator gate sites re-derive inline.
- **fence mask**: the per-line boolean list marking fenced content inside a Markdown record, derived from the fence state machine.
- **declared seam**: an explicitly named parameter or import edge that carries an intentional divergence between two consumers of one shared mechanism.

## Assumptions

- assume the shared bash matcher consumes the FULL declared glob list in every mode; the changed-from surface keeps its existing SCAN_STRICT root filter, so globs outside agents/skills and projects stay inert there; basis: the superset is behavior-identical under the existing root filter at scripts/scan-public-hygiene.sh lines 193-196 and removes the hand-maintained nine-glob subset at lines 201-210.
- assume the root LICENSE.txt alignment direction: explicit-paths mode adopts the rg doublestar reading (a bare root LICENSE.txt is excluded), so the r3 F5 asymmetry becomes all-modes-agree; basis: the scanner origin's fix shape (one shared matcher consumed by all three surfaces) records the asymmetry as the known instance to resolve, and the flip is fail-open only for the allowlisted shape the other two modes already skip.
- assume the helper mask imports the validator's classifier directly instead of introducing a new shared module; basis: no import cycle exists (validate_review_staging.py imports nothing from review_record_selection.py, verified by grep at authoring time), and summarize_review_stats.py already imports the validator module as a library surface, so the import edge has precedent.
- assume sequencing against the sibling entries: this plan lands before any outcome-contract-migration-queue batch (that entry's validation commands then re-derive against the refactored surfaces), and the selection-docstring-precision docstring edits land after this plan (disjoint spans: the SelectionUsageError exit-taxonomy and _pair_pattern paragraphs versus the fence mask); basis: both sibling entries' coordination clauses delegate the sequencing choice to the authoring passes and require only that the choice be recorded; this plan records refactor-first.
- assume the third fence grammar in scripts/check_prompt_log_origins.py (a backtick-only opener regex) stays out of scope; basis: neither origin names it and its grammar is deliberately narrower because prompt logs carry no tilde fences.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: single-sources the hand-copied glob surfaces, date-fence classifiers, non-canonical derivations, and the fence mask into declared owners with agreement selftests, so drift fails a gate instead of waiting for an incident, code-quality with a simplicity dividend.

Today a maintainer who adds one allowlist glob must hand-edit three surfaces in scripts/scan-public-hygiene.sh (the rg array, the changed-from inline list, the explicit-paths case branches) and keep a fourth copy of the fence state machine alive in scripts/review_record_selection.py; the 2026-10-01 restoration receipts record exactly this drift happening (thirteen globs hand-synced into the case branches; the non-canonical predicate grown from four inline derivations to five). After this plan the same maintainer edits one list and one helper per mechanism, and the scanner selftest proves the modes agree.

## Evaluation Criteria

**Quality dimensions:**
- behavior preservation: every existing selftest arm in the scanner selftest, the validator selftest, and scripts/test_review_record_selection.py stays green before and after each task, with the single declared exception of the root LICENSE.txt agreement arm that is RED at authoring and GREEN after Task 1.
- single ownership: after each task, the consolidated mechanism has exactly one owner symbol per file set, verified by the negated stale-reference sweeps in Validation Commands.
- declared divergence: the helper mask's opener divergence and the unclosed-fence refusal survive as named parameters and unchanged caller behavior, not silent copies.

**Done when:**
- `bash scripts/scan-public-hygiene.sh --selftest` exits 0 with the new agreement arms present and green.
- `python3 scripts/validate_review_staging.py --selftest` exits 0 with the wrappers delegating to the shared classifier and the five sites consuming the predicate helper.
- `python3 scripts/test_review_record_selection.py` exits 0 including the new seam arms.
- The negated sweeps show the deleted copies' markers gone from the edited files.

**Ship when:**
- Nothing; the work is repository-internal with no deploy, cross-team, or human-owned condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/scan-public-hygiene.sh`
- `scripts/validate_review_staging.py`
- `scripts/review_record_selection.py`

**Tests:**
- `scripts/test_review_record_selection.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** in scripts/validate_review_staging.py only the fence classifiers (_freshness_fence, _record_kind_fence, the coverage-fence consumption site at the vrs-freshness-fence-single-helper comment), the five non-canonical predicate sites, classify_fence_lines and its FENCE_LINE_RE constant, and any docstring those tasks rewrite are in scope; all other validators, gates, selftest arms, and frozen legacy regions in the file are frozen; reject any review finding that touches them. In scripts/scan-public-hygiene.sh only the GLOB_EXCLUDES declaration block, changed_files_in_scope, _path_is_excluded, _path_matches_glob, their comments, and cmd_selftest's arms are in scope; the deny-pattern engine and the remaining mode plumbing are frozen.

**Out of scope; reject unless plan-related:**
- `scripts/check_prompt_log_origins.py`; its backtick-only fence regex is a third, deliberately narrower grammar that neither origin names (Assumptions).
- `scripts/summarize_review_stats.py`; it consumes the preserved public alias record_kind_fence and is only a smoke-validation target, with no edit planned.
- `scripts/OUTCOME_CONTRACT.md` and the 2026-10-03-outcome-contract-migration-* backlog rows; the sibling entry outcome-contract-migration-queue owns the migration batches and its own sequencing record.
- `agents/skills/**`; the caller-obligation surfaces belong to the migration entry's arm 6, not to this refactor.

## Validation Commands

```bash
bash scripts/scan-public-hygiene.sh --selftest
python3 scripts/validate_review_staging.py --selftest
python3 scripts/test_review_record_selection.py
python3 scripts/summarize_review_stats.py --help
if grep -qF 'Keep _path_is_excluded below in sync' scripts/scan-public-hygiene.sh; then echo "stale coupling comment survived"; exit 1; fi
if grep -qF '(mirrors ``_freshness_fence``)' scripts/validate_review_staging.py; then echo "hand-copy docstring claim survived"; exit 1; fi
```

Authoring-time gate evidence (rule 19/22/29): the two stale-reference sweeps are RED today (the coupling comment exists at scripts/scan-public-hygiene.sh line 27 and the hand-copy docstring claim at scripts/validate_review_staging.py line 1570, both verified by execution at authoring time) and flip GREEN exactly when Tasks 1 and 2 land; the four run-gates are GREEN today and must stay green through every task boundary; the plan bytes passed the no-em-dash touched scan, the public-hygiene scan, and `python3 scripts/plan_readiness.py --pre-round` before round 1.

### Task 1: Single-source the scanner glob surfaces

Files:
- `scripts/scan-public-hygiene.sh`

Evidence:
- `bash scripts/scan-public-hygiene.sh --selftest`; covers the new surface-agreement arms, the matcher unit arms, and every pre-existing selftest arm staying green
- `bash scripts/scan-public-hygiene.sh --files README.md`; covers explicit-paths mode stays functional on a real file

- [ ] RED: add cmd_selftest arms first, via the existing selftest_check_files harness plus direct calls to the EXISTING explicit-paths predicate (the shared matcher does not exist yet at this checkpoint): (a) a direct arm asserting the current predicate excludes a nested agents/skills/x/LICENSE.txt, docs/tmp/child.txt, and docs/reviews/r.md, and does not exclude a bare root LICENSE.txt, docs/history/backlog/draft.md, or agents/skills/clean/SKILL.md; (b) a cross-mode agreement arm over fixtures the full-tree mode can actually visit or that are allowlisted, EVERY one planted with a deny-pattern hit (the allowlisted fixtures from (a) plus agents/skills/clean/SKILL.md), asserting the full-tree and explicit-paths modes return the SAME verdict for each; docs/history/backlog/draft.md carries no deny hit and stays outside the agreement arm because its scanned-when-named verdict is owned by the existing explicit-paths selftest sub-test, not by this plan; run → expect RED exactly on the root LICENSE.txt legs (the full-tree and changed modes never visit root-level shapes because their scan roots are agents/skills and projects, so only the explicit-paths mode consults a matcher on the root shape today: the r3 F5 asymmetry) [class: REPOSITORY_TEST]
- [ ] Declare the bare-glob list (one array of glob bodies) as the single owner at the existing GLOB_EXCLUDES declaration block, deriving the rg-argument view from it at that same site so the frozen rg invocations keep consuming the derived view unchanged, and replace the line 27 keep-in-sync comment with the declared-owner comment naming the list [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the shared matcher function consuming the declared list with rg doublestar semantics: a leading **/ matches zero or more directories (so a bare root LICENSE.txt matches), a trailing /** stays inside its prefix (docs/tmp/** must not match docs/history/backlog/draft.md), and plain entries match literally [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewire changed_files_in_scope and _path_is_excluded to consume the shared matcher, deleting the inline nine-glob loop and the case-glob branches (their divergence comment goes with them); changed-from keeps its SCAN_STRICT root filter ahead of the matcher; the RED checkpoint's direct and agreement arms re-target onto the shared matcher here, flipping the root LICENSE.txt legs GREEN while every other leg keeps its verdict [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/scan-public-hygiene.sh --selftest` [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0: `bash scripts/scan-public-hygiene.sh --files README.md` [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: single-source the scanner allowlist glob surfaces` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Parameterize the date-fence classifiers

Files:
- `scripts/validate_review_staging.py`

Evidence:
- `python3 scripts/validate_review_staging.py --selftest`; covers every existing freshness and record-kind fence arm staying green plus the new shared-owner characterization arm

- [ ] Extract _date_fence(staging_name, sidecar_date, min_date) as the single owner of the two-surface classification; _freshness_fence and _record_kind_fence become thin wrappers with unchanged names, signatures, return shape, and public alias record_kind_fence, and the shared malformed-date nuance is stated once in the shared docstring instead of drifting between the copies [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a characterization arm asserting _freshness_fence and _record_kind_fence return identical shapes (the same keys and the same undated/pre-fence/post-fence vocabulary) for a fixed date matrix, with classes differing exactly on dates on or after EXTENDED_SIDECAR_MIN_DATE and earlier than RECORD_KIND_SIDECAR_MIN_DATE (both fences compare with a strict less-than, so the band is inclusive of the lower constant and exclusive of the upper) [class: REPOSITORY_TEST]
- [ ] Run → expect OK: `python3 scripts/validate_review_staging.py --selftest` [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: parameterize the two date-fence classifiers` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Single-source the declared non-canonical predicate

Files:
- `scripts/validate_review_staging.py`

Evidence:
- `python3 scripts/validate_review_staging.py --selftest`; covers the five consuming gates' existing arms (coverage exemption, markdown agreement exemption, clean-verdict eligibility, kind_noncanonical, md_kind_noncanonical)

- [ ] Add _declared_noncanonical_kind(record_kind) returning exactly the three-clause predicate (present, in RECORD_KIND_VALUES, different from canonical) and rewire the five inline sites: the coverage-exempt site, the markdown-agreement exempt site, the clean-verdict eligibility gate (whose early return for missing or non-enum kinds is preserved verbatim, with only the non-canonical comparison replaced), and the two kind_noncanonical assignments [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect OK: `python3 scripts/validate_review_staging.py --selftest` [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: single-source the declared non-canonical predicate` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Fold the helper fence mask onto the shared classifier

Files:
- `scripts/validate_review_staging.py`
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`

Evidence:
- `python3 scripts/test_review_record_selection.py`; covers the existing mask and mark-superseded arms plus the new seam arms
- `python3 scripts/validate_review_staging.py --selftest`; covers the classifier's own arms with the new parameter at its default

- [ ] Give classify_fence_lines a keyword-only fence_line_re parameter defaulting to FENCE_LINE_RE, so the opener spelling is a declared seam parameter and every existing consumer and selftest arm is unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewire _fence_mask as an adapter: import classify_fence_lines from validate_review_staging, pass the helper's own _FENCE_LINE_RE opener regex through the declared parameter, and derive (mask, unclosed_opener_index) from the returned events (a line is masked exactly when its event is in_fence_content); the caller's unclosed-fence SelectionUsageError refusal is untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] `FenceMaskSeamTest#test_mask_matches_classifier_events`; given a fixture matrix covering bare, equal-length, and longer close runs, an other-delimiter run, an info-string suffix, tilde versus backtick delimiters, a heading inside an open fence (masked) and a heading outside any fence (unmasked), a form-feed-prefixed fence opener (matched by the classifier's default opener and not by the helper's: the case that fails while the declared fence_line_re parameter is left unwired), and an unclosed fence, _fence_mask's mask equals the in_fence_content events of classify_fence_lines invoked with the helper's opener regex, and the unclosed index matches [class: REPOSITORY_TEST]
- [ ] Run → expect OK: `python3 scripts/test_review_record_selection.py` [class: REPOSITORY_TEST]
- [ ] Run → expect OK: `python3 scripts/validate_review_staging.py --selftest` [class: REPOSITORY_TEST]
- [ ] Commit: `refactor: fold the helper fence mask onto the shared classifier` [class: IMPLEMENTATION_REQUIRED]
