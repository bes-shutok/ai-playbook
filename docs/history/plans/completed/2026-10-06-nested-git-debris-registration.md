# Plan: nested git debris disposition, presence probe, and classifier evidence completeness

Backlog origin: docs/history/backlog/2026-10-04-nested-git-debris-root-registration.md
Second origin: docs/history/backlog/2026-10-04-untracked-root-debris-detection-gap.md
Driving force: reliability (not one of the five driving principles; justification: complete failure evidence and a written disposition home replace hand-derived remedies and partial reports; park-triage would not take it: the defect is live on the survey's routine turn and every nested-repo flare re-costs a hand-derived remedy) + automation (closed-taxonomy principle; the probe moves root-debris detection into the routine survey loop)
Plan review record: the staging series docs/reviews/2026-10-06-plan-review-nested-git-debris-registration-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- nested-repository debris: an untracked non-ignored directory inside the project tree that carries its own `.git` directory (the witnessed `h/` form at the repo root, 2026-10-04).
- disarm: renaming the embedded `.git` directory to `.git-deactivated` (the witnessed form, contents byte-preserved) so no out-of-repo scanner can detect or register the preserved copy.
- preserve location: the record home debris is moved into intact before disarm (the witnessed form under the gitignored `docs/tmp/done-session/` corpus).
- presence probe: the survey arm that lists untracked non-ignored top-level entries and adjudicates each against the live authoring claims (the Authoring-claim consult's `authoring-claims/` surface) and the allowlist.
- allowlist: the repo-side list of top-level untracked non-ignored entry names that are never debris, recorded in the probe paragraph; empty at landing, appended only by a later plan naming a witness.
- collection failure: a git plumbing failure inside the revert-set classifier's per-path loop (the `indeterminate` returns), after which the loop stops.
- paths attempted: the paths carrying an emitted row before a collection failure stopped the loop.

## Why

Two witnessed instances in one morning (2026-10-04): an IDE registered a nested repository at the repo root as a Git root, and after the debris was moved intact to the preserve location the same registration symptom re-fired there minutes later; the hand remedy (rename the embedded `.git` to `.git-deactivated`) is applied to the preserved copy, but no repo text owns the rule, no routine turn surfaces root debris, and the revert-set classifier reports only the failing path when a plumbing failure stops its loop, silently discarding the rows already collected.

## Outcome

The maintenance survey owns the debris-disposition rule and the presence probe, and the revert-set classifier's indeterminate evidence carries every path attempted before the failure.

- The maintenance skill's survey region gains the nested-repository debris disposition paragraph: move intact to the preserve location, disarm via the `.git-deactivated` rename, and record the scanner-side remedy for an already-dangling registration (remove the stale root mapping in the scanner's version-control settings; the gitignored `.idea/vcs.xml` is an advisory repo-side check only).
- The survey gains the presence-probe arm listing untracked non-ignored top-level entries each run, adjudicated live-claim-first then against the allowlist, reporting suspected debris with the disposition pointer, never removing.
- `scripts/revert_set_classifier.py` reports every path attempted before a collection failure in its indeterminate evidence, and the selftest gains the nested-repository fixture.
- Gate delta: grows the maintenance survey's checked-condition set (the disposition rule and the presence probe) and the classifier's evidence completeness; no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the two same-morning flare instances recorded under the gitignored session corpus and the classifier's failing-path-only indeterminate witness, both re-derived from the session records and the script bytes in the investigate pass.

## Assumptions

- assume the disposition rule's home is the maintenance skill's survey region, not the done skill: basis: the survey is the routine turn where root debris is encountered (the flare ran as a maintenance-turn record), the done skill's revert-set arm classifies tracked dirt and explicitly never removes untracked paths, and skill files are on-demand surfaces outside the entrypoint budget (learn Step 6.5 budgets only the always-loaded repo-root instruction entrypoints), with done out of scope, so the home adjudication adds no done-skill bytes.
- assume the allowlist lands empty: basis: no benign untracked top-level entry is witnessed in the current tree (the gitignored roots cover the known scratch surfaces), the second origin's witnessed benign candidates are handled by the unclassified-presence routing until a later plan appends them with witnesses, and the probe paragraph records the mechanism so those appends are one-line entries.
- assume the probe is report-only and never removes: basis: the record-only doctrine and the origin Outcome's preserve-and-disarm direction (Debris disposition disarms nested repositories as it preserves them).
- assume the presence probe partitions cleanly from the sibling plans-root probe: the surfaces are disjoint (the repo top level versus the plans root) and the adjudications differ (allowlist-second versus live/stranded classification); basis: the sibling plan docs/history/plans/2026-10-05-authoring-round-liveness-gap.md is authored, certified, and execution-pending at the plans root, so its probe owns the plans-root surface when it executes and no script duplication exists today.
- assume the classifier's exit codes and the outcome-contract vocabulary stay untouched: basis: `scripts/OUTCOME_CONTRACT.md` pins the four-outcome shape and the 1abfaa32 landing froze the fail-closed indeterminate contract; the change only enriches the indeterminate message's evidence.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The debris rule gets a repo home and a routine-turn probe, and the classifier stops discarding collected evidence on plumbing failures (reliability + automation).

**Before (today):** A nested repository surfaces at the root, an IDE registers it, and the operator re-derives the disarm remedy by hand from the flare record; no routine turn lists untracked root entries, so debris presence waits for a human; and a plumbing failure mid-classification prints the failing path with no mention of the paths already classified.

**After (this plan):** The survey paragraph owns the rule (move intact, disarm `.git-deactivated`, record the scanner-side remedy), the probe lists untracked non-ignored top-level entries each survey run and adjudicates them live-claim-first then allowlist, and the classifier's indeterminate line names every path attempted before the failure.

Edge cases: a live authoring claim naming the untracked entry classifies it live, never debris; an allowlisted entry is skipped by the probe; the preserve location sits under the gitignored `docs/tmp/`, so preserved debris never re-enters the probe's listing (the witnessed re-detection was the scanner registering the copied `.git`, which the disarm prevents); the classifier's change adds evidence without altering any exit code.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the classifier selftest passes with the nested-repository fixture and the attempted-paths reporting assertion; every exit code is unchanged.
- regression safety: the pins suite stays green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: the probe never removes anything; the classifier's change touches only the indeterminate evidence and no outcome vocabulary.

**Done when:**
- `( cd "$REPO" && python3 scripts/test_revert_set_classifier.py )` exits 0.
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- The next maintenance survey reports the top-level presence listing and the next debris encounter follows the written disposition rule; both are routine-turn behaviors requiring no further human action in this repository beyond the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (the two new bullets in the survey region after the Dirty-primary classification arm; all other sections are frozen)
- `scripts/revert_set_classifier.py` (the indeterminate evidence enrichment; all other behavior frozen)
- `scripts/test_revert_set_classifier.py` (the new fixtures)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/done/SKILL.md`; reason: the done skill's revert-set arm keeps its tracked-dirt scope and the home adjudication lands in the maintenance skill.
- `.idea/vcs.xml` and any scanner configuration; reason: gitignored and machine-local; the paragraph records the advisory remedy only.
- `docs/tmp/done-session/` flare records; reason: gitignored session evidence, read-only inputs.
- `scripts/OUTCOME_CONTRACT.md`; reason: the four-outcome vocabulary is frozen by the 1abfaa32 landing.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed `python3 scripts/plan_readiness.py --pre-round` with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match; the preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning prescribed snippet (rule 36 mirrors included; the preserved spans matched against the current target bytes) and `bash -n` accepted the Validation Commands block. Round-start state for r4: authoring worktree ai-playbook-wt-ngdr, branch 2026-10-06-nested-git-debris-registration, plan bytes at the r3 fold commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/test_revert_set_classifier.py -v )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Pin the evidence-completeness contract (RED fixtures)

Files:
- `scripts/test_revert_set_classifier.py` *(existing suite, extended)*

Evidence:
- `( cd "$REPO" && python3 scripts/test_revert_set_classifier.py )`; covers the RED-today criterion: the attempted-paths reporting test fails on the absent evidence span while the nested-repository fixture passes

- [x] Add a fixture test building a scratch repository (the file's existing scratch-repo idiom) containing an embedded nested repository: an untracked directory `h/` at the scratch repo root with its own `.git` (git init plus one commit inside `h/`), then run the classifier on the outer repo and assert exit 2, stderr evidence containing `revert-set-classifier: effective state failed for h/`, and the final `OUTCOME: indeterminate` line (the witnessed fail-closed contract: the classifier cannot classify an untracked directory and refuses the whole verdict, as the second origin pins); this test passes today and pins the behavior so Task 2's evidence enrichment cannot silently alter it [class: REPOSITORY_TEST]
- [x] Add a reporting test asserting the evidence-completeness contract: with two dirty paths where the git plumbing fails on the second path's lookup (a path-selective variant of the existing git-shim idiom, failing only the second path's addition lookup), the classifier exits 2 with `OUTCOME: indeterminate` and its stderr evidence names the failing path AND contains `paths attempted before failure` naming the first attempted path (`paths attempted before failure: a.txt`); this test fails today because the indeterminate message names only the failing path [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && python3 scripts/test_revert_set_classifier.py )` fails with the reporting test failing on the absent evidence span, while the nested-repository fixture and all pre-existing tests pass [class: REPOSITORY_TEST]
- [x] Commit: `test: pin debris evidence-completeness and nested-repository classifier contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Evidence-complete reporting and the survey home (GREEN)

Files:
- `scripts/revert_set_classifier.py`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `( cd "$REPO" && python3 scripts/test_revert_set_classifier.py )`; covers the GREEN criterion: the full suite passes including both new fixtures
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: no pin row's literal broke

- [x] In `scripts/revert_set_classifier.py`, change every `indeterminate(...)` return inside the per-path classification loop to append the attempted evidence to its message through one shared suffix builder fed by a collected-paths list maintained parallel to the rows (the path appended at every row-emission site; never parse paths back out of the row strings, which embed the path mid-format), keeping the pinned evidence span at exactly one occurrence in the file: the failing path stays named, and the message gains `; paths attempted before failure: ` followed by the comma-separated sorted collected paths, or `none` when the failure fired on the first path; every loop site carries the clause (the status-parse failure sits before the loop and carries no attempted evidence); exit codes and the `OUTCOME:` vocabulary are untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Insert the following paragraphs into `agents/skills/maintenance/SKILL.md` immediately after the Dirty-primary classification arm bullet (the paragraph whose body begins the unique span `Dirty-primary classification arm (added 2026-10-02, the primary revert-set adjudication plan)`), as two new bullets in the same list [class: IMPLEMENTATION_REQUIRED]

```markdown
- Nested-repository debris disposition (added 2026-10-06, the nested-git-debris-registration plan): when the surveyed tree holds nested-repository debris (an untracked non-ignored directory carrying its own `.git`), the disposition moves the debris intact to the preserve location (the resolved tmp directory's `done-session/` corpus) and disarms the copy by renaming its embedded `.git` to `.git-deactivated` (contents byte-preserved; witnessed form 2026-10-04), so no out-of-repo scanner registers the preserved copy; for an already-dangling registration the remedy is scanner-side (remove the stale root mapping in the scanner's version-control settings; the gitignored `.idea/vcs.xml` is an advisory repo-side check only). The disposition never deletes debris (record-only doctrine) and never treats classified reversal dirt as debris (the dirty-primary classification arm above owns that classification).
- Top-level presence probe (added 2026-10-06, the same plan): every survey, after the dirty-primary classification, lists untracked non-ignored top-level entries (`git status --porcelain=v1 -z`, untracked records only, an entry whose path contains no `/` before the trailing directory marker, if any) and adjudicates each: a fresh authoring claim naming the entry (fresh = an `updated:` within one cadence period, per the Authoring-claim consult's freshness rule) classifies it live, an entry named in the allowlist is skipped, an entry matching the debris shape (a directory carrying its own `.git`) is reported as suspected debris with the disposition pointer to the paragraph above, and any other unclaimed entry is reported as unclassified presence for the existing foreign-work and item adjudication protocols; the allowlist is empty at landing and appends only by a later plan naming a witness; the probe is report-only and never removes or moves anything itself.
```

- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_revert_set_classifier.py )` passes all 22 tests (20 pre-existing plus 2 new); the pins suite exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: debris disposition home, presence probe, and evidence-complete classifier reporting` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span introduced by this plan, `grep -cF` over its owning file returns exactly 1 after the edits (`Nested-repository debris disposition`, `untracked non-ignored top-level entries`, and `version-control settings` in `agents/skills/maintenance/SKILL.md`; `paths attempted before failure` in `scripts/revert_set_classifier.py`), and for the preserved spans it returns at least 1 (`Dirty-primary classification arm` in `agents/skills/maintenance/SKILL.md`; `revert-set: partial` in `scripts/revert_set_classifier.py`) [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/history/plans/2026-10-06-nested-git-debris-registration.md`; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-ngx (branch plan-nested-git-debris-registration-exec) by the standing maintenance execution lane. Task 1 (2d38a6f2): the two named fixtures pin the witnessed nested-repository fail-closed contract and the evidence-completeness reporting contract with the prescribed RED split (the reporting test failing on the absent span, the nested fixture and all twenty pre-existing tests passing). Task 2 (238e2bba): every in-loop indeterminate site appends the attempted-paths evidence through one shared suffix builder fed by a collected-paths list maintained at every row-emission site, the pinned span occurring exactly once, with the pre-loop status-parse failure clause-free and exit codes and outcome vocabulary untouched; the Nested-repository debris disposition and Top-level presence probe bullets land verbatim after the Dirty-primary classification arm in agents/skills/maintenance/SKILL.md.

Validation: classifier suite 22/22 OK; pins suite exit 0; em-dash added-lines scan and hygiene scan exit 0; span uniqueness holds for all new-duty and preserved spans; the review's live adversarial scratch runs additionally covered the sorted multi-path, none-on-first-failure, ls-tree, vintage-walk, and nested-debris clause shapes. Exec review r6 (fresh-adversarial, one worker) found zero findings with two informational plan-conformant notes; records at docs/reviews/2026-10-06-plan-review-nested-git-debris-registration-r6.{md,stats.json} plus the r7 certification probe.

Deferred residuals: none. Both origin rows are covered by this execution and folded in the landing.
