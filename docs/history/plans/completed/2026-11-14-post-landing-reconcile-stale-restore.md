# Plan: re-class the post-landing reconcile landing-deleted leg

Language guidelines: `projects/.ai-playbook/python_guidelines.md` (the touched script is Python; plain `python3` for repo-local trusted scripts).

Backlog origin: docs/history/backlog/2026-11-14-post-landing-reconcile-restores-pre-landing-bytes.md
Driving force: reliability
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-post-landing-reconcile-stale-restore-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 1.0h
Executed: yes
Authoring claim: 2026-11-14-post-landing-reconcile-restores-pre-landing-bytes.md (session sess_bd5b093a-c100-4049-999b-a87ed29ba334)

## Terms

- Landing-deleted leg: the discriminator branch for a path the landing commit deleted (absent from the post tip) in a live checkout of the base branch (scripts/reconcile_post_landing.py `classify()`, the `post_blob is None` arm).
- Removal class: the re-classed deletion verdicts this plan introduces: a landing-deleted path whose checkout bytes are pure ancestor blobs (index or worktree byte state matching an ancestor commit's blob) is removed, never restored and never left standing on the fresh-mtime bound, in both the standalone and `--landing-tail` modes.
- Pure ancestor orphan: a landing-deleted path whose index entry is absent and whose worktree bytes equal an ancestor blob (the pre-landing tip's blob or any older one); removed directly with `os.remove` (the docstring's own contract, because `git restore` cannot express removing an index-absent path).
- Staged-residue removal: a landing-deleted path whose index carries an ancestor blob (staged-looking only because HEAD moved under the checkout) with the worktree bytes absent or ancestor: removed through the single-path restore from the post tip (which drops both the index entry and the worktree file), row verb `removed`.
- Staged-peer-edit block: a landing-deleted path whose index carries a non-ancestor blob (a peer's staged edit); blocked, never restored (byte-unchanged).
- Genuine-modification block: a landing-deleted path whose worktree bytes match no ancestor blob; blocked (byte-unchanged).
- Fresh-mtime bound: the primary-checkout guard that converts an ancestor-blob restore into a block row when the worktree file mtime postdates the pre-landing tip's commit time (`mtime_gated` / `FRESH_MTIME_WITNESSES`); byte-unchanged for every non-deletion witness (stale, wholesale-residue, added, half-synced), and the `--landing-tail` stale-only lift stays byte-unchanged.
- `removed` row: the receipt line `removed <checkout> <path>`; the re-classed deletions print this verb (today the index-present removal prints `restored`).
- Witnessed stale-restore shape: the 2026-11-14 regression (origin row): after two worktree landings, the primary working tree held the archived plan at its pre-archive path and two folded origin rows with pre-landing bytes; the learn commit 9e7472c23 swept them into history and 53f3e4cb5 reverted the sweep.
- Fixture pair: the two suite fixture families this plan pins: (a) a fold-and-delete landing whose reconcile receipt shows `removed` rows and no resurrected paths in the primary tree, and (b) the witnessed stale-restore shape as the regression canary.
- Dry run: a scratch-repo exercise of the real script (`python3 scripts/reconcile_post_landing.py` with `--landing-tail`, the landing flow's own invocation shape) over the fixture pair, recorded in the task log.

## Why

The landing-deleted leg still routes the landing's own stale bytes into restore-shaped verdicts: the index-present ancestor shape prints `restored` for what is a removal, and both deletion shapes sit inside the primary fresh-mtime bound, so the landing's own just-restored residue (fresh mtime by construction) is blocked instead of removed and the stale orphan stands in the primary tree. The witnessed session lost exactly this way twice in one window: the stale copies stood after the landings, a learn commit swept them into history, and a corrective revert was needed. The module docstring already states the target contract (the index-absent orphan is removed with `os.remove`); the implementation's leg ordering contradicts it.

## Gist & Examples

TLDR: the reconcile's landing-deleted leg re-classes to a removal class (pure ancestor-byte deletions are removed with `removed` rows, exempt from the fresh-mtime bound, in both standalone and `--landing-tail` modes), so a fold-and-delete landing can no longer strand its own pre-landing copies in the primary tree, which is why the reliability force applies: the landed tree stays authoritative after every landing without a manual revert.

Before: a fold-and-delete landing's tail reconcile leaves the archived plan and folded origin rows standing in the primary (fresh-mtime blocks over ancestor bytes, receipts reading `restored`), and the next docs/history commit silently regresses the landed state.

After: the same tail reconcile removes the landing-deleted orphans (receipt rows `removed`, exit 0), the primary tree carries no resurrected paths, and the witnessed stale-restore shape fails to reproduce; genuine peer edits still block exactly as before.

Edge cases: a staged non-ancestor index blob (peer's edit) still blocks as staged-peer-edit; worktree bytes matching no ancestor still block as genuine-modification except where the index state already routes the path to the removal class (the staged-residue removal with absent or ancestor worktree bytes); a path absent from both index and worktree stays `synced`; a failed `os.remove` or restore still degrades to the `restore-refused` block row; the `--check-primary` read-only sweep is untouched.

## Outcome

After this plan, the reconcile discriminator's landing-deleted leg matches its own docstring: landing-deleted paths with pure ancestor bytes are removed (rows `removed`) in both invocation modes regardless of the primary fresh-mtime bound, the deletion family's receipts use the removal verb, and the witnessed stale-restore regression canary cannot reproduce. Every non-deletion discriminator arm (stale, wholesale-residue, added, half-synced, genuine-modification, staged-peer-edit) and the fresh-mtime bound with its tail stale-only lift stay byte-unchanged.

Gate delta: narrows an existing restore arm's operand set inside one script (the landing-deleted leg's verdict routing and row verb) plus its suite cells; no new gate, validator, lock, ledger, or required ceremony; removals: none.

Follow-up disposition: none; the witnessed incident closes with this plan (the corrective revert 53f3e4cb5 already repaired the tree, and the regression canary pins the class shut). No backlog row is created.

## Assumptions

- assume the re-classed deletion removals are exempt from the primary fresh-mtime bound in both modes; basis: authoring probes B and C (the bound's fresh-mtime false-block over pure ancestor bytes is the witnessed regression vector; recorded in the requirements buffer docs/tmp/plan-requirements-post-landing-reconcile-stale-restore.md) and the stale-only lift's own landed rationale that ancestor-identical bytes carry no peer edit content (215f23ca9).
- assume the bound exemption extends to both deletion shapes (the index-absent pure orphan and the staged-residue removal); basis: the same no-peer-content rationale applies to both, and the witnessed event plausibly covered the index-present shape (the primary index holds the pre-landing tree after a ref-level landing).
- assume the genuine-peer-edit block rows and the fresh-mtime bound with the tail stale-only lift stay byte-unchanged outside the re-classed leg; basis: the entry prompt's "keep the genuine-peer-edit block rows and the fresh-mtime bound byte-unchanged" clause read as scoping the re-class to the landing-deleted leg.
- assume the re-classed deletions print the `removed` verb; basis: the module docstring's output vocabulary (lines 53-54) and the entry prompt's "(the recorded `removed` row)".
- assume `git restore --source=<post tip> --staged --worktree` removes a landing-deleted path whose index carries an entry on the host git (probed 2026-11-14, rc 0, file gone, index entry dropped); the index-absent orphan rides `os.remove` and does not depend on git behavior; basis: probe D recorded in the requirements buffer.
- assume scripts/land_squash.sh (the tail invocation shape) and the Worktree-first standard's discriminator text stay byte-unchanged; basis: the origin row's exact-location pin (scripts/reconcile_post_landing.py) and the docstring being the discriminator contract's home.
- assume the clean-checkout shape (a landing-deleted path absent from index and worktree) stays `synced` through the existing first classify branch and gains a regression cell; basis: probe E.

Decision points requiring a grill: none remain; deletion removals versus the fresh-mtime bound = the re-classed removals are bound-exempt in both modes (decided 2026-11-14 under the standing authorization; simpler-design comparison: keeping the bound over the deletion legs leaves the landing's own stale orphan standing on a fresh mtime, which is exactly the witnessed regression the entry closes, while the exemption reuses the stale-lift rationale already landed for ancestor-identical bytes and the false-positive cost is the reported removal of bytes that match an ancestor blob).

## Standing constraints

- The genuine-peer-edit block rows (staged-peer-edit, genuine-modification) keep their current witness names, row shape, and exit-code semantics byte-unchanged.
- The fresh-mtime bound (`mtime_gated`, `FRESH_MTIME_WITNESSES`) and the `--landing-tail` stale-only lift keep their current operands and semantics byte-unchanged for every non-deletion witness; no lift widening beyond the re-classed deletion exemption.
- The `--check-primary` read-only sweep performs no restore, no remove, and no index operation, byte-unchanged.
- The reconcile's exit-code contract (0 verified, 1 blocks, 2 tool failure) is unchanged; a re-classed removal that fails degrades to its block row, never a tool failure.
- No other script, skill, or standard text changes in this plan; the Worktree-first standard's post-landing reconciliation contract keeps citing the module docstring as the discriminator home.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the deletion matrix cells prove the removal class (index-absent orphan, staged-residue removal), the unchanged blocks (staged-peer-edit, genuine-modification), and the synced no-op, in both invocation modes (Task 1).
- regression safety: the witnessed stale-restore shape cannot reproduce (the canary cell: no resurrected paths in the primary tree after a fold-and-delete tail); the reconcile suite and the handoff suite stay green (Tasks 1 and 2).
- contract alignment: the module docstring and the implementation state the same landing-deleted contract after the change (Task 1).
- receipt fidelity: the deletion family's rows carry the `removed` verb (pinned by cell assertions).

**Done when:**
- The focused reconcile suite passes with the new `deleted_reclass` cells green and the two flipping legacy pins amended to the removal contract.
- The real-script dry run over the fixture pair in both modes records `removed` rows, no resurrected paths, and exit 0 in the task log.
- The handoff suite (test_reconcile_execute_plan_handoff.py) passes byte-unchanged.

**Ship when:**
- No further condition; the change is repository-local and takes effect at the next landing's reconcile tail.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reconcile_post_landing.py` (Task 1)

**Tests:**
- `scripts/test_reconcile_post_landing.py` (Task 1)
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: the landing flow's tail invocation shape is frozen by this plan's standing constraints; the fix is inside the reconcile script.
- `agents/skills/execute-plan/worktree-first.md`; reason: the standard's discriminator text cites the module docstring as the contract home; the docstring is updated, not the standard.
- `scripts/reconcile_post_landing.py` `--check-primary` mode body; reason: the read-only sweep is out of this plan's deletion-leg scope (standing constraint).

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_reconcile_post_landing.py -q -k deleted_reclass || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_reconcile_post_landing.py -q || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_reconcile_execute_plan_handoff.py -q || exit 1
bash scripts/check-no-em-dash.sh file scripts/reconcile_post_landing.py || exit 1
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || exit 1
```

Validation preamble (authoring-time preflight record, 2026-11-14, rule 29):

- Selector `-k deleted_reclass` on scripts/test_reconcile_post_landing.py: collects 0 tests today (92 collected overall in the file; measured 2026-11-14 at the authoring worktree base 1fd30f4ad via pytest --collect-only), so the pinned `|| exit 1` makes it RED on the authoring tree and GREEN once Task 1 lands the deleted_reclass-named cells (the amended tail-lift pin carries the token in its renamed form; the second flipping pin, test_landing_deleted_path_removed, keeps its name and flips its row-verb assertion).
- Whole-suite pin on scripts/test_reconcile_post_landing.py: 92 pre-existing cells measured green at authoring (focused run per the facts test_suite_policy focused-never-full; no whole-repo suite pinned).
- Handoff suite pin on scripts/test_reconcile_execute_plan_handoff.py: 31 cells measured green at authoring (31 passed, 5 subtests passed, 2026-11-14); Task 2 expects the same green byte-unchanged.
- Em-dash file check on scripts/reconcile_post_landing.py: clean today (exit 0, measured 2026-11-14), re-run after Task 1's edits.
- Pinned hygiene scan: `OUTCOME: pass` (measured 2026-11-14 at the authoring worktree).
- Em-dash authoring-time self-check: the write-time fixer ran over the new plan bytes before round 1 and re-runs after every fold batch; `bash scripts/check-no-em-dash.sh file docs/history/plans/2026-11-14-post-landing-reconcile-stale-restore.md` recorded clean.
- Rule 19 RED-today evidence: the deletion-removal contract cells reference behavior that contradicts the current implementation (probe B: the fresh-mtime block leaves the orphan standing today; the tail-lift pin currently asserts the block and test_landing_deleted_path_removed currently asserts the `restored` verb), so the RED leg is real at the cell level; the `-k deleted_reclass` selector gives command-level RED evidence today (0 collected).
- Rule 22 authoring-time mechanical audit: the Validation Commands block passes `bash -n` (every fallible line carries `|| exit 1`, so the hygiene scan always runs); the plan pins fixed-string checks against files this plan edits only.
- Rule 29 per-line execution record (2026-11-14): `-k deleted_reclass` RED (0 selected of 92, pytest exit 5 into `|| exit 1`), reconcile suite GREEN (92 passed, 41.87s), handoff suite GREEN (31 passed, 5 subtests, 4.91s), em-dash file check exit 0, hygiene `OUTCOME: pass`.

### Task 1: Re-class the landing-deleted leg to the removal contract

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/reconcile_post_landing.py`
- `scripts/test_reconcile_post_landing.py`

Primary class anchors:
- `classify` in `scripts/reconcile_post_landing.py`
- `apply_entry` in `scripts/reconcile_post_landing.py`

- [x] Reproduction probe first: rebuild the witnessed stale-restore shape as a suite fixture (fold-and-delete landing; primary HEAD at post tip; index and worktree holding pre bytes; fresh mtime) and record today's observed behavior (fresh-mtime block, orphan standing) in the task log before any implementation edit [class: IMPLEMENTATION_REQUIRED]
- [x] Canary cell (deleted_reclass): the witnessed shape under `--landing-tail` expects exit 0, `removed` row(s), no resurrected paths in the primary tree, the file absent, and clean status [class: IMPLEMENTATION_REQUIRED]
- [x] Index-absent orphan cells (deleted_reclass): standalone and tail modes each expect the `os.remove` removal with a `removed` row and the fresh mtime no longer blocking [class: IMPLEMENTATION_REQUIRED]
- [x] Staged-residue removal cells (deleted_reclass): index carrying an ancestor blob, worktree absent or ancestor, both modes expect the restore-removal with a `removed` row (not `restored`) [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the two flipping legacy pins: `test_landing_tail_lift_is_stale_only_fresh_mtime_deleted_still_blocked` (renamed with the deleted_reclass token; expectation flips from the fresh-mtime block to the removal contract, amended docstring says why) and `test_landing_deleted_path_removed` (index-present staged-residue shape; its `restored` row assertion flips to the `removed` verb per the re-class) [class: IMPLEMENTATION_REQUIRED]
- [x] Older-ancestor deletion cells (deleted_reclass): a landing-deleted path whose checkout bytes match an ancestor blob older than the pre-landing tip (not equal to it) expects the same removal class per the Terms matrix (index-absent orphan and staged-residue variants, at least one per mode) [class: IMPLEMENTATION_REQUIRED]
- [x] Block-unchanged cells (deleted_reclass): a staged non-ancestor index blob still blocks as staged-peer-edit; worktree bytes matching no ancestor still block as genuine-modification, in both modes [class: IMPLEMENTATION_REQUIRED]
- [x] Synced no-op cell (deleted_reclass): a landing-deleted path absent from both index and worktree expects the `synced` row and exit 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Bound-untouched cells: the stale and wholesale-residue fresh-mtime behaviors and the tail stale-only lift keep their current expectations (existing cells stay green without amendment beyond the two flipping legacy pins) [class: IMPLEMENTATION_REQUIRED]
- [x] Implementation: re-class `classify()`'s `post_blob is None` arm into the removal class per the Terms matrix (pure ancestor orphan, staged-residue removal, unchanged blocks), exempt the re-classed removals from `mtime_gated` gating, route the row verb to `removed`, keep the restore-refused degradation for a failed removal [class: IMPLEMENTATION_REQUIRED]
- [x] Docstring alignment: the module docstring's landing-deleted paragraphs state the removal contract (both modes, bound-exempt, `removed` rows) and no longer contradict the implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused suite expecting the deleted_reclass cells RED before the implementation edit and GREEN after; every cell other than the two amended pins stays green [class: REPOSITORY_TEST]
- [x] Commit: `fix: re-class the reconcile landing-deleted leg to the removal contract` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Dry-run validation over the fixture pair

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/reconcile_post_landing.py` (review-only; no edits)
- `scripts/test_reconcile_execute_plan_handoff.py` (review-only; no edits, validation run only)

Primary class anchors:
- `main` in `scripts/reconcile_post_landing.py`

- [x] Dry run (standalone): in a scratch repo, mint a fold-and-delete landing (ref move under a primary checkout holding pre bytes, fresh mtimes), run the real script standalone, and record the receipt in the task log: `removed` rows, no resurrected paths, exit 0 [class: REPOSITORY_TEST]
- [x] Dry run (tail): the same scratch fixture run with `--landing-tail` (the landing flow's invocation shape) records the same post-state contract in the task log [class: REPOSITORY_TEST]
- [x] Run the handoff suite (test_reconcile_execute_plan_handoff.py) expecting green byte-unchanged [class: REPOSITORY_TEST]
- [x] Run the full Validation Commands block and record the per-line outcomes in the task log (the rule 29 record) [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

Origin row `docs/history/backlog/2026-11-14-post-landing-reconcile-restores-pre-landing-bytes.md` (`Status: covered-pending-execution`): covered by this plan's execution landing (tip 9a9ceb316, 2026-11-19) and folded with the row's deletion; the row's witnessed stale-restore shape is pinned shut by the deleted_reclass canary cell and the removal-class re-class.
