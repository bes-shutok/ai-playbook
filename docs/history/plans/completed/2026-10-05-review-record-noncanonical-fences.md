# Plan: review-staging gate excludes preservation backups from live-record validation

Backlog origin: docs/history/backlog/2026-10-05-done-review-backup-validation-false-block.md
Driving force: reliability (outside the five driving principles; justification: a witnessed unsound false-block refused a live closeout and both of its documented remedies are destructive to the run's live work, so the fence ships rather than parks; park-triage would not take it: the fix is one filter with pinned fixtures at an already-audited seam)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-review-record-noncanonical-fences-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Preservation backup: the timestamped byte-identical copy pair the record-selection helper's `backup` subcommand writes under the reviews directory before a permitted same-pass replacement (`<basename>.backup-<timestamp>.md` plus its sidecar twin), named by the grammar's single source `BACKUP_INFIX = ".backup-"` in scripts/review_record_selection.py.
- Backup grammar: the name test `BACKUP_INFIX in basename`; the helper's enumeration already uses it to ignore backup-shaped names while counting them informationally, and this plan reuses that one source on the gate side.
- Staging-path predicate: the validator's `is_staging_review_path` (scripts/validate_review_staging.py), whose `BACKUP_NAME_RE` (timestamp-shaped `.backup-<YYYYMMDDTHHMMSS>[-N].md`) already refuses every markdown name the sanctioned backup operation emits (the sidecar twin never passes the predicate's `.md` gate either); the gate's window arm applies it inside `_all_staging_review_paths`, so window-arm candidates never include a real backup pair today, while the manifest arm validates owned paths on `is_file` alone (the documented F4/F8 over-validation asymmetry) and is the one arm where a backup reaches live-record validation.
- Review-staging gate: the done pre-docs gate (`gate_review_staging` in scripts/done_sweep_gates_lib.py) that validates the run's staging docs through the migrated validator as a CLI child; its candidates come from `derive_review_staging_scope`.
- Candidate derivation: `derive_review_staging_scope` in scripts/done_sweep_gates_lib.py, the single construction point of the gate's candidate list; it has two arms (the run-manifest branch and the legacy window-mtime fallback branch) and a report-lines channel for informational, never-fatal observations.
- Informational report line: a scope report line that is printed and never fails the gate (the existing vanish and foreign-exclusion lines are the precedent).
- Canonical record: the live review record the validator must keep validating in full, including the `Supersedes` back-reference integrity family in scripts/validate_review_staging.py; untouched by this plan.
- Single-source import: the flat same-directory import of `review_record_selection` from scripts/done_sweep_gates_lib.py (both modules live in scripts/, the lib runs as a script with its own directory on sys.path, and both test suites insert the scripts directory into sys.path before importing, so the flat arm works in every consumption mode; the helper imports nothing from the gates lib, so no cycle).

## Why

The done pre-docs review-staging gate validated a preservation backup as a live review record and the validator refused the closeout on the backup's stale `Supersedes` link: the back-reference check is name-based, and a byte-identical backup can never match it under any filename, so validating a backup as a live candidate is unsound by construction, not merely unlucky. The witness blocked a live consumer execution's done boundary and was worked around only by relocating the backup pair or staging the file in-session. The gate is half-fenced today: the legacy window arm's staging-path predicate (`BACKUP_NAME_RE`) already refuses backup markdown, but the run-manifest arm validates owned paths on `is_file` alone (the documented F4/F8 over-validation asymmetry), which is the one arm where a backup reaches live-record validation, and the witnessed closeout carried a run manifest. The record-selection helper has always known backup-shaped names are not live records; the manifest arm never learned that.

## Outcome

The review-staging gate's candidate derivation excludes preservation-backup pairs from live-record validation wherever they can reach it, counting each exclusion as an informational report line, sourcing the name test from the helper's single `BACKUP_INFIX` constant, and leaving the canonical record, the validator's link-integrity refusals, and the helper's own behavior byte-untouched.

- In scripts/done_sweep_gates_lib.py, `derive_review_staging_scope` is restructured to compute both arms into local values and construct `ReviewStagingScope` at one shared exit, where one filter moves every candidate whose basename carries `BACKUP_INFIX` (the markdown file and its sidecar twin both match) into the report lines with one informational line per excluded path.
- The filter's live effect is the manifest arm: owned paths bypass the staging-path predicate on `is_file` alone, so a manifest-carried backup reaches validation today and is excluded with the informational line after this plan. The window arm's real backup pairs are already refused upstream by the staging-path predicate and produce byte-identical scope output with zero new report lines; the filter stays armed on that arm as defense-in-depth for a helper-grammar name lacking the timestamp shape (which the predicate does not match but the helper's grammar does).
- The backup grammar is imported, not redefined: the filter uses the helper's constant so a rename of the grammar cannot re-create this defect class one rename later.
- scripts/validate_review_staging.py, scripts/review_record_selection.py, and the done skill's gates-order text are byte-untouched; the seam's three docstrings (`gate_review_staging`, `derive_review_staging_scope`, `derive_review_staging_candidates`) gain the exclusion sentences so the module documents its own non-canonical handling, and the wrapper's F4/F8 sentence names the backup exclusion as the one sanctioned suppression arm.

Scope note: this plan is the uncovered Task 1 remainder of the frozen rolling-log entry `review-record-noncanonical-fences`; that entry's other two tasks (the strip-on-clone supersession duty and the recover-orphan operation) are owned by the landed plan docs/history/plans/2026-10-05-review-round-record-lifecycle-gaps.md, whose riders already flipped the sibling origin rows covered; this plan therefore carries one origin row and does not re-author the covered surfaces.

Gate delta: one new exclusion arm inside an existing candidate derivation (restrictive in direction: it can only remove candidates from validation, never add one), one informational report line class, one new cross-module import, and a local restructure of the scope function's two returns into one shared construction exit. No new refusal class, no validator change, no state field.

## Assumptions

- assume the filter lives in `derive_review_staging_scope` (the candidates' single construction point of `ReviewStagingScope`) rather than the thin public wrapper `derive_review_staging_candidates`, and that the function's two present returns (the legacy arm's early return and the manifest arm's terminal return) are restructured into compute-then-single-return so one filter covers both arms; basis: the live bytes show the wrapper only returns `scope.candidates` while the scope function builds both arms and the report list across two return statements.
- assume the staging-path predicate already excludes real backup pairs from the window arm upstream of the filter (the filter's live effect is the manifest arm's `is_file`-only owned-path validation), and the filter stays armed on the window arm as defense-in-depth for helper-grammar names lacking the timestamp shape the predicate matches; basis: scripts/validate_review_staging.py `BACKUP_NAME_RE` applied inside `_all_staging_review_paths`, versus the manifest arm's documented F4/F8 asymmetry, and the helper's `_unique_path` grammar which can emit a `-N`-counter name the regex's optional counter group does cover while a hand-made grammar name without a timestamp does not.
- assume the single-source import is the flat same-directory form; basis: the done skill invokes the lib by file path (its script directory is then on sys.path), and both test suites insert the scripts directory before importing; the helper imports nothing from the gates lib, so the import is acyclic.
- assume the exclusion is name-based on `BACKUP_INFIX` alone and covers the sidecar twin with the same test (the backup operation copies the pair under one infixed stem); basis: the helper's `_enumerate` and `_unique_path` both key on the infix in the basename.
- assume an informational report line, never a warning bucket change: the existing vanish and foreign-exclusion lines are printed-and-never-fatal, and the origin row's Expected block asks for exclusion with audit preservation, not new failure modes; basis: scripts/done_sweep_gates_lib.py `derive_review_staging_scope` report usage and the origin row.
- assume this plan carries only the backup-false-block origin; basis: the sibling rows `2026-10-05-review-round-copies-stale-supersession-link.md` and `2026-10-05-review-selection-orphan-record-fence.md` are covered by the landed plan docs/history/plans/2026-10-05-review-round-record-lifecycle-gaps.md, whose commit riders flipped both rows covered and whose Task 3 lands the recover-orphan operation this entry's Task 3 named.
- assume the adjacency holds unchanged: the awaiting-execution done-lifecycle-recovery-gaps plan owns the same sweep-gate library seam (its Task 1 records review-candidate classification pre-lock), so anchors re-derive from live bytes at execution and a moved anchor re-keys its pin in the same edit; basis: the frozen entry's adjacency sentence and the plan's presence in the plans root.
- assume authoring runs unattended-capable under the standing D-4 authoring directive, so the plans skill's Phase 1 confirmation is satisfied by the frozen entry's validated record; basis: the maintenance loop's authoring blueprint under the standing operator directive.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the review-staging gate stops validating timestamped preservation backups as live review records, a reliability fence against a witnessed unsound false-block that refused a live closeout.

Before (today): the gate's candidate derivation globs the reviews directory (or trusts the run manifest's owned list) and feeds every match to the validator; a backup pair written by the sanctioned backup operation carries a stale `Supersedes` link that can never name-match, so the closeout refuses on a sound canonical record and the operator must relocate backups or stage files by hand.

After (this plan): the same derivation filters backup-shaped names through the helper's own `BACKUP_INFIX` constant, prints one informational line per excluded pair, and validates only canonical records; a backup stays on disk for audit, and the witnessed closeout shape passes with the exclusion counted.

Edge cases pinned: a manifest-owned backup markdown alone without its sidecar (and a sidecar alone) is excluded by the same name test with its own informational line; a window-fallback reviews directory holding a real backup pair produces byte-identical scope output with zero new report lines (the staging-path predicate already refused the pair upstream; the fixture characterizes that pre-existing exclusion); a hand-made helper-grammar name lacking the timestamp shape (matching `BACKUP_INFIX` but not `BACKUP_NAME_RE`) that slips past the predicate in the window arm is excluded by the filter with the informational line; a canonical record whose name embeds the infix as part of a longer segment is still a backup per the helper's own grammar and is excluded (the helper's select path already refuses emitting such slugs, so no live record collides); a manifest-owned backup-shaped path is excluded like any other (the filter is post-derivation, arm-independent); a reviews directory with no backups produces byte-identical scope output and zero new report lines; the validator's mismatched-back-reference refusal is never relaxed and stays fully armed on canonical records; an unreadable or missing reviews directory behaves exactly as today.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every backup-shaped candidate that can reach validation (the manifest arm's owned paths, plus a window-arm helper-grammar name lacking the timestamp shape) is excluded and counted informationally; every canonical record (including superseded chains whose canonical records carry valid links) still validates in full; the witnessed false-block shape passes with the exclusion reported; window-arm real backup pairs keep today's byte-identical behavior.
- single-source discipline: the name test imports `BACKUP_INFIX` from `review_record_selection`; no second grammar definition appears anywhere in the diff.
- fail-closed placement: the filter only ever removes candidates; a filtering bug cannot suppress a canonical validation, because canonical names never carry the infix the helper refuses to emit.
- observability: each exclusion prints a relative-path report line; a closeout report shows what was excluded and why, matching the vanish and foreign-line precedent.
- maintainability: one filter at one construction point (the two returns restructured into one shared exit), one import, all three seam docstrings updated in place; no validator, helper, or skill-text churn.

**Done when:**
- all task boxes checked; the sweep-gate suite passes under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_review_record_selection.py -q` exits 0); the pins suite exits 0 (OUTCOME: pass); the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-review-record-noncanonical-fences.md` exits 0 on the final bytes.

**Ship when:**
- a reviews directory holding a preservation-backup pair passes the pre-docs review-staging gate with the exclusion counted informationally while the canonical record still validates, and a backup-free directory behaves byte-identically to today.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (the `derive_review_staging_scope` restructure and filter arm; the docstring sentences of `gate_review_staging`, `derive_review_staging_scope`, and `derive_review_staging_candidates`)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (new backup-exclusion fixtures beside the existing review-staging gate fixtures)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`: the link-integrity refusals stay untouched; the inherited-stale-link and orphan surfaces belong to the landed sibling plan.
- `scripts/review_record_selection.py`: the helper's grammar, enumeration, and backup operation stay byte-untouched; this plan is the consumer side.
- `agents/skills/done/SKILL.md` and `agents/skills/review-staging/SKILL.md`: no duty-text change is required by the exclusion (the gate docstring is the documentation surface).
- the strip-on-clone supersession duty and the recover-orphan operation: owned by docs/history/plans/2026-10-05-review-round-record-lifecycle-gaps.md.
- the awaiting-execution done-lifecycle-recovery-gaps plan's surfaces: adjacency only; anchors re-derive, no pre-coordination edits.

## Validation Commands

```bash
# Sweep-gate suite (new fixtures) and selection-helper regression
# (the venv runner is the canonical invocation; bare python3 executes
# nothing on these suites)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_review_record_selection.py -q
# Pins: the sweep-gate and review-store surfaces stay pinned; a moved
# anchor re-keys its pin in the same edit
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews, green from r1 on
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-review-record-noncanonical-fences.md
```

### Task 1: Backup-exclusion filter in the review-staging gate's candidate derivation

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers every criterion below at the task boundary (bare `python3` cannot even import the suite off-venv: rc 1 with a pytest import error, fail-closed rather than vacuous)
- `grep -c "BACKUP_INFIX" scripts/done_sweep_gates_lib.py`; covers the single-source import presence (RED at authoring: zero hits)
- `grep -c "excluded preservation backup" scripts/done_sweep_gates_lib.py`; covers the informational line presence (RED at authoring: zero hits)

- [x] Re-derive the anchors from live bytes: the `derive_review_staging_scope` function (its two arms, its two return statements, the report-lines channel, and the `ReviewStagingScope` construction), the thin wrapper `derive_review_staging_candidates` and its F4/F8 docstring sentence, the staging-path predicate's `BACKUP_NAME_RE` application inside `_all_staging_review_paths`, the helper's `BACKUP_INFIX` constant, its `_enumerate` name test, and its `_unique_path` grammar, and the pins suite's sweep-gate surfaces; if any anchor moved from the bytes this plan quotes, update the owning pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Restructure `derive_review_staging_scope` to compute both arms into local values and construct `ReviewStagingScope` at one shared exit, add the flat same-directory import of the helper's `BACKUP_INFIX` constant at the top of scripts/done_sweep_gates_lib.py, and filter the constructed candidates at that exit: every candidate whose basename carries `BACKUP_INFIX` moves into the report lines with one informational line per excluded path (the relative path and the exclusion reason, never a failure), the markdown file and its sidecar twin excluded by the same name test, manifest-owned and window-fallback candidates alike; the filter's live effect is the manifest arm (owned paths validated on `is_file` alone bypass the staging-path predicate), the window arm's real backup pairs stay upstream-excluded by `BACKUP_NAME_RE` and byte-identical, and the filter remains armed there for a helper-grammar name lacking the timestamp shape; the canonical record is never filtered (names the helper refuses to emit cannot collide) and the validator's link-integrity family is untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Update all three seam docstrings (`gate_review_staging`, `derive_review_staging_scope`, `derive_review_staging_candidates`) with the exclusion sentences: the derivation documents its own non-canonical handling (preservation backups are audit state, never live candidates, sourced from the helper's single grammar), and the wrapper's F4/F8 sentence names the backup exclusion as the one sanctioned suppression arm instead of stating that a claimed artifact is never suppressed [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the fixtures in scripts/test_done_sweep_gates_lib.py beside the existing review-staging gate fixtures, reusing the suite's existing helpers (`ctx_for`, `sweep_env`, `_seed_run_manifest`, the stub validator): a manifest-owned backup pair expects both members excluded with two informational lines and any canonical owned record still validated; a window-fallback reviews directory holding a real backup pair plus a canonical record expects byte-identical scope output, zero new report lines, and the canonical record validated (characterizing the predicate's pre-existing exclusion); a window-arm candidate whose name matches `BACKUP_INFIX` but not the timestamp regex expects the filter's informational line; a backup-free directory expects byte-identical scope output and zero new report lines; a canonical record with a valid `Supersedes` chain still passes (the witnessed false-block regression shape) [class: REPOSITORY_TEST]
- [x] Run → GREEN: the sweep-gate suite and the selection-helper regression suite OK under the venv runner [class: REPOSITORY_TEST]
- [x] Commit: `fix: review-staging gate excludes preservation backups from live-record validation` [class: IMPLEMENTATION_REQUIRED]

## Disposition

- Outcome: executed and landed on main (squash commit recorded at landing).
- Task 1 complete; all six checkboxes ticked; implementation commit 3ed88612 (derive_review_staging_scope restructured to one shared construction exit with the BACKUP_INFIX filter, three seam docstrings updated, six fixtures) and fold commit (this stub commit).
- Exec review: r4 fresh adversarial (one High digest-churn finding, the designed mid-loop state resolved by this plan's r5 digest-binding probe; one Low stub-literal finding folded); records + sidecars at docs/reviews/2026-10-05-plan-review-review-record-noncanonical-fences-r{4,5}.md.
- Gates on the final bytes: sweep + selection suites 207 passed + 3 subtests under the venv runner; pins OUTCOME: pass; em-dash added-lines exit 0; hygiene OUTCOME: pass.
- Deferred residuals: none.
