# Plan: commit scope guard

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-explicit-add-commit-includes-prestaged-deletion.md`

Driving force: reliability (outside the plans skill's closed declaration taxonomy, acknowledged per the dossier precedent: the witnessed failure is a branch-integrity defect the taxonomy's tags do not name; a witnessed 2026-10-05 targeted backlog commit also deleted an unrelated tracked plan: the command staged only the new backlog path, but the Git index already carried the deletion, and the commit succeeded and removed an unrelated artifact from the repository; commit 7b8d1bff is the witness and the deleted file existed at its parent, so the collateral history is a fact of the shared branch)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-commit-scope-guard-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Path-scoped commit: a commit made for a declared set of paths (the done skill's Step 3 explicit-pathspec commits, including its backlog and skill-placement commits); the declared set is what the operator intends the commit to touch.
- Staged set: the entries `git diff --cached --name-status -z HEAD` reports (state token then path records, NUL-delimited; a rename/copy state consumes TWO path records in origin-first order, `state\0origin\0destination\0`), which is what a bare `git commit` would commit.
- Unrelated staged entry: a staged path outside the declared set; the witnessed shape is a pre-staged deletion the commit command never asked for.
- Scope guard: the new `scripts/staged_scope_guard.py` operation, run before an explicitly path-scoped commit, that refuses when the staged set contains unrelated entries and passes otherwise.
- Additive restoration: the origin row's incident remedy for already-landed collateral: restore the exact prior blob in a separate commit that records the restoration, never rewriting shared history; execution-local to the incident that produced it and outside this plan's tasks.

## Why

The done skill's Step 3 guards classify dirt before staging (the baseline arm, the stale-checkout discriminator, the foreign-dirt gate, the dirt-regression gate), but none of them checks the one thing the witnessed failure turned on: the index can hold staged entries that predate the session's staging decisions, and a commit executed for a declared path set commits the whole staged set anyway. The witnessed deletion rode a targeted backlog commit exactly that way. The fix is one mechanical refusal before every path-scoped commit: compare the declared set against the staged set and refuse naming the unrelated entries, so the failure shape becomes impossible to enter silently.

## Outcome

- Before every explicitly path-scoped commit, the guard compares the declared path set against the staged set and refuses with each unrelated staged entry named and its state shown, so a pre-staged deletion can never ride a targeted commit again.
- The guard is wired into the done skill's Step 3 as the pre-commit duty for explicit pathspec commits, and stays generally invocable for targeted commits made outside the done flow.

Gate delta: one new script with a named refusal class (unrelated staged entries) and one skill-text duty; no existing gate weakens: the Step 3 baseline arm, the stale-checkout discriminator, the foreign-dirt gate, and the dirt-regression gate all keep their semantics, and the guard runs beside them as the index-side complement they lack.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so Step 1.4 confirmation is satisfied by the row's validated record rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the guard refuses and names the unrelated entries rather than offering a bypass flag; basis: the remedy for a flagged entry is deliberate (unstage it, or widen the declared set), and a bypass flag would reintroduce the silent path the row exists to close.
- assume the declared set is passed explicitly per invocation (`--include`, repeatable) and never derived from session context; basis: cycle-4's reviewer pinned the same explicit-input shape for recover-orphan, and the declared set is the operator's intent, not derivable state.
- assume the tracker-keyed Sources inspected record: the origin row names tracker key STORY-KEY (its Evidence and Source lines); the STORY-KEY plan file itself was not read for this authoring because the row's own Evidence carries the commit-level witness (7b8d1bff, verified in git this session) and the fix surface is the ai-playbook commit tooling, not the CRM product code; basis: the review-plan tracker-source audit accepts a named-unread source with the reason when the tasks do not implement the tracker's exposed behavior.
- assume the restoration arm of the origin row's Expected is execution-local to the witnessed incident (the deleting session's own additive follow-up) and outside this plan's tasks; basis: the row's Why-not-fixed-now records exactly that shape, and this plan's contract is the guard that prevents the next instance.
- assume the wiring target is the done skill's Step 3 because the witnessed commit was a Step 3 backlog commit; basis: the row's evidence names the done-classifier blocker recording, and Step 3 owns the skill's explicit-pathspec commit procedures.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: one guard runs before every explicitly path-scoped commit, compares the declared paths against the staged set, and refuses naming any unrelated staged entry, so a pre-staged deletion can never ride a targeted commit.

Before (today): the index carries a deletion staged earlier for unrelated reasons; the operator stages a new backlog file and commits for that path; the commit includes the index's deletion of an unrelated plan, and the artifact leaves the branch silently.

After (this plan): the guard refuses: `staged-scope-guard --include docs/history/backlog/<new>.md` finds `D docs/history/plans/<unrelated>.md` in the staged set, names it with its state, and exits 1 before the commit runs; the operator unstages or widens the declared set deliberately, and the targeted commit touches only what it declared.

Edge cases pinned: an unrelated staged modification refuses beside the witnessed deletion; a staged rename consumes both of its path records (origin first) so neither side slips past, and the membership rule is symmetric: a rename/copy entry is related when ANY of its consumed path records is declared, with the refusal naming the unrelated side first (origin before destination); paths bearing spaces round-trip through the NUL-delimited parse; a staged set exactly equal to the declared set passes with the receipt; an empty staged set passes vacuously (nothing to commit is the caller's finding, not the guard's); an absent `--include` refuses as a usage violation; the guard mutates nothing (read-only over the index and HEAD).

## Tasks

### Task 1: The staged-scope guard script, its suite, and the Step 3 wiring

Files:
- `scripts/staged_scope_guard.py` *(new)*
- `scripts/test_staged_scope_guard.py` *(new)*
- `agents/skills/done/SKILL.md`

Evidence:
- `python3 scripts/test_staged_scope_guard.py`; covers every criterion below at the task boundary (new main-shim suite)
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-05-commit-scope-guard.md`; structural gate

- [ ] `test_unrelated_staged_deletion_refuses` (given a fixture repo whose index stages a deletion of an unrelated tracked file and a declared include of the new backlog path, expects exit 1 with the unrelated path and its `D` state named; the witnessed shape) [class: REPOSITORY_TEST]
- [ ] `test_unrelated_staged_modification_refuses` (given a staged modification outside the declared set, expects the same named refusal with the `M` state) [class: REPOSITORY_TEST]
- [ ] `test_rename_consumes_both_sides` (given a staged rename whose origin and destination both sit outside the declared set, expects the refusal to name both paths, proving the two-record origin-first consumption; and given a rename with the origin outside and the destination inside the declared set, expects a pass, and given a rename with the origin inside and the destination outside, expects a refusal naming the destination (the symmetric any-side membership rule and the origin-before-destination naming order both pinned, so a swapped parse reading cannot pass the suite green)) [class: REPOSITORY_TEST]
- [ ] `test_paths_with_spaces_round_trip` (given staged and declared paths bearing spaces, expects exact matching through the NUL-delimited parse with no split-path false refusals) [class: REPOSITORY_TEST]
- [ ] `test_exact_set_passes_and_empty_set_passes` (given a staged set exactly equal to the declared set, expects exit 0 with the pass receipt and the final `OUTCOME: pass` line; given an empty staged set, expects exit 0 vacuously; given no `--include`, expects exit 3 as a usage violation with `OUTCOME: tool_error`) [class: REPOSITORY_TEST]
- [ ] `test_guard_mutates_nothing` (given the refusal fixture, expects the index and working tree byte-identical before and after the run) [class: REPOSITORY_TEST]
- [ ] Implement `scripts/staged_scope_guard.py`: read the staged set through `git diff --cached --name-status -z HEAD` (state token first, then path records; a rename/copy state consumes two path records in origin-first order, `state\0origin\0destination\0`), compare against the repeated `--include` values, refuse with one named line per unrelated entry (path plus state) and exit 1, pass with the receipt and exit 0, usage violations exit 3; every run ends with the outcome contract's final `OUTCOME:` line (pass, fail, indeterminate, or tool_error matching the exit; a git plumbing failure over already-resolved inputs maps to the indeterminate exit 2 like the sibling guards) and the pass receipt is one line naming the compared staged-entry count, read-only over the index and HEAD; resolve the script repo-relative per the skills' standard resolution order (repo-local first, then the deployed home copy) [class: IMPLEMENTATION_REQUIRED]
- [ ] Skill text wiring: the done skill's Step 3 pre-commit guard region (item 1) gains the scope-guard duty: before every Step 3 commit made for a declared path set - whether or not the command carries a pathspec, since a bare `git commit` after an explicit `git add` is the shape that rides unrelated staged entries - run the guard with the commit's declared paths as `--include` values; a refusal stops the commit until the unrelated entries are unstaged, the declared set is deliberately widened, or the commit proceeds as an explicit pathspec commit covering exactly the declared set (a pathspec commit never rides unrelated staged entries) with the foreign or peer disposition recorded per the item 0 and item 1a adjudications for shared-checkout entries; the refusal evidence is recorded in the session notes in every arm [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full new suite, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: staged-scope guard refuses unrelated index entries before path-scoped commits` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Files in scope (the union of the task Files lists): `scripts/staged_scope_guard.py`, `scripts/test_staged_scope_guard.py`, `agents/skills/done/SKILL.md`.

Reviewers judge: fail-closed posture (the refusal names every unrelated entry, mutates nothing, and offers no bypass), the parse grammar's correctness (NUL-delimited records, rename origin consumption, space-bearing paths), the wiring's coherence with Step 3's existing guard family (complement, not replacement), scope discipline (the restoration arm stays out of tasks), and test reality (every criterion has a named test runnable in this repository against a fixture repo).

## Validation Commands

The per-task checklists reference the suite, pins, em-dash scan, hygiene scan, and readiness probe by name; the exact invocations are the five literals below.

```bash
python3 scripts/test_staged_scope_guard.py
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-commit-scope-guard.md
```
