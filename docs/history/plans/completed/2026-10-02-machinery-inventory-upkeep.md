# Plan: Machinery inventory upkeep (register 8 scripts, re-point 7 dead witnesses)

Backlog origin: docs/history/backlog/2026-10-02-machinery-inventory-upkeep.md
Driving force: reliability (the machinery inventory is the elimination-pass policing document; with 15 standing check failures the survey's regrowth guard reports permanent noise, so real regrowth is undetectable until the registry describes the tree again)
Plan review record: the staging series docs/reviews/2026-10-02-plan-review-machinery-inventory-upkeep-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Restore the machinery registry to a faithful description of the tracked tree so the regrowth guard consult returns to a zero-failure signal.

- `python3 scripts/machinery_inventory.py --check` exits 0 with "0 failure(s)" on the landed tree.
- Every script under `scripts/` is registered with a live witness or consciously removal-listed; the 8 unregistered scripts from the origin item carry keep rows.
- Every witness ref resolves to a tracked path that is the testimony's current home (archived plan or skill source of truth); the 7 dead refs from the origin item are re-pointed, never blankly deleted.
- The scaffold's `SEED_PROTOCOLS` constants carry no dead backlog paths (data hygiene: the scaffold emits seed rows with an empty witness ref regardless, so this is readability upkeep, not a behavior change).

Gate delta: none. This plan changes registry data rows, row notes, and dead path constants inside the existing inventory surfaces only; no gate, refusal class, fence, protocol layer, or scheduler state field is added, extended, or removed.

## Terms

- **Machinery inventory**: `scripts/machinery_registry.json` plus its checker `scripts/machinery_inventory.py`; the keep-or-delete register of every guard script, hook, protocol, and scheduler state field (2026-09-28 machinery-elimination-pass plan).
- **Registry row**: one entry in the inventory's `entries` array; `id`, `kind`, `disposition` (`keep`/`delete`/`pending`), `paths`, `tests`, `note`, and a `witness` object (`class` from the closed taxonomy, `ref` that must resolve to a tracked path).
- **Witness**: the tracked document that justifies keeping a row's machinery alive; its `ref` is checked for path resolution by `--check`.
- **Scaffold**: `machinery_inventory.py --scaffold`, which merges candidate rows (disposition `pending`) from tracked sources into the registry; the registration starting point for unregistered files.

## Assumptions

- Each of the 8 unregistered scripts was delivered by a reviewed, archived plan; its delivering plan is re-derivable from `git log --follow --diff-filter=A --format=%H -- <script>`; the ownership registry `docs/maintenance/document-registry.md` is a best-effort cross-check only, not a required co-source (it indexes documents rather than scripts and its rows are backfilled) (basis: the machinery delta doctrine requires landing-time registration, so the missing rows are drift, not unreviewed machinery).
- The testimony behind each of the 7 dead witnesses survives at a current tracked home; the homes the tasks name are re-derived starting candidates, and every re-point verifies its target before writing on two axes: the target is tracked (`git ls-tree HEAD -- <path>`) AND the target carries the row's testimony (grep the field or protocol name in the candidate home), because `--check` tests path resolution only and cannot catch a misattributed testimony (basis: the corpus sweep that deleted the old witnesses folded or archived the owning work; the r1 review caught three resolving-path candidates whose bytes never mention their rows' testimony, so the name-presence check is load-bearing).
- The enforcing suite (`scripts/test_machinery_inventory.py`, 14 tests) exercises the checker contract on fixtures, not the registry data, so registry data edits cannot break it (basis: suite green before and after the 2026-10-02 survey; the suite stayed green while the consult reported 15 failures).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the machinery registry re-joins the tree (8 new keep rows with delivering-plan witnesses, 7 dead witness refs re-pointed to their testimony's current homes, dead seed paths purged), so the regrowth guard consult returns to zero-failure signal instead of permanent 15-failure noise (reliability force).

The drift came from legitimate work skipping a bookkeeping step: reviewed plans landed new scripts (for example `prestage_freshness_gate.py` from the worktree-complete landing lifecycle plan, `revert_set_classifier.py` from the primary revert-set adjudication plan) without adding their registration rows, and the done-origin fold-delete corpus sweep deleted backlog files that seven registry rows and four seed constants still named as witnesses. This plan repairs both sides with the inventory's own tooling: `--scaffold` proposes the missing rows, the executor promotes each to `keep` with a re-derived delivering-plan witness, and the dead refs are re-pointed to where the testimony lives today (an archived plan under `docs/history/plans/completed/`, or the skill document that pins the protocol). Nothing is deleted from the registry and no new machinery is created; a witness re-point changes the `ref` and, where the old class testified an open sibling that no longer exists, the `class` and the note; new script rows take the registry's dominant class convention (`red-test` with the test file as ref when the script ships with a test, `user-decision` with the delivering plan otherwise).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every row edit names a witness ref that is tracked and carries the row's testimony (verified with `git ls-tree HEAD` plus a name grep in the target before writing, not copied from this plan; path resolution alone is not enough because `--check` tests resolution only).
- Completeness: `--check` reports zero failures; every failure line from the origin item's verbatim list is dispositioned by exactly one checklist action.
- Maintainability: each edited or new row's `note` names its testimony home, so the next lifecycle move is a one-row re-point instead of a re-derivation.

**Done when:**
- `python3 scripts/machinery_inventory.py --check` exits 0 printing "0 failure(s)".
- `python3 scripts/test_machinery_inventory.py` prints OK (14 tests).
- After each task's commit, `git show --name-only --format=%h HEAD` covers exactly that task's Files list; across the run's commits the combined set is exactly `scripts/machinery_registry.json` and `scripts/machinery_inventory.py`, plus this plan's own bytes at execution closeout.

**Ship when:**
- Nothing beyond Done when: the plan has no deployed, cross-team, or human-owned surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/machinery_registry.json` *(modified)*
- `scripts/machinery_inventory.py` *(modified; the `SEED_PROTOCOLS` seed constants only)*

**Tests:**
- `scripts/test_machinery_inventory.py` *(read-only context; the enforcing suite must stay green, no test edits planned)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Any new script, gate, or check; reason: the plan's contract is registering and re-pointing existing machinery, not adding any.
- The enforcing suite's fixture data; reason: fixtures model the checker contract, not the live registry.
- Skill files and the maintenance skill text; reason: no contract there changes.

## Validation Commands

```bash
# Executor note: run from the repository root. Exit status is the contract
# for command 1; the OK summary line is the contract for command 2; the
# per-commit path set is the contract for command 3, evaluated after each
# task's commit.
python3 scripts/machinery_inventory.py --check
python3 scripts/test_machinery_inventory.py
git show --name-only --format=%h HEAD
```

### Task 1: Re-point the 7 dead witness refs and re-home the dead seed refs

Files:
- `scripts/machinery_registry.json` *(modified)*
- `scripts/machinery_inventory.py` *(modified; `SEED_PROTOCOLS` constants only)*

Evidence:
- `python3 scripts/machinery_inventory.py --check`; covers "no witness-ref failure remains for the seven named rows" (resolution only; the per-item tracked-plus-name-grep checks carry the testimony attribution)

- [ ] Re-point the `script:check_prompt_log_origins.py` row's witness `ref` to `docs/history/plans/completed/2026-10-01-prompt-log-prune-check.md`, verifying the target is tracked (`git ls-tree HEAD -- <path>`) and pins the row's testimony before writing [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point the `state-field:pending_dispatch`, `state-field:pending_landing`, `state-field:pending_rearm`, and `state-field:rate_limited_events` rows' witness `ref` to `agents/skills/maintenance/SKILL.md` (its State file section is the schema home defining all four fields and already witnesses the other 15 state-field rows), verifying the target is tracked and greps each field name before writing; set each row's witness `class` to `user-decision` (the prior `sibling-boundary` class testified an open sibling that the corpus sweep deleted), and replace each row's stale "open sibling owns its repair" note with one naming the schema home [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point the `protocol:five-round-review-cap` row's witness `ref` to `agents/skills/review-loop/SKILL.md` (its configuration pins `max_full_panel_rounds` default 5, the cap value; `agents/skills/plans/SKILL.md` separately pins the cap-closure terminal shape without the value and is named in the note, not the ref) with witness `class: user-decision`, verifying the target is tracked and names `max_full_panel_rounds` before writing, and replace the row's stale "open sibling owns review-loop exit and cap machinery" note [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point the `protocol:residual-acceptance-exit` row's witness `ref` to the archived residual-exit plan `docs/history/plans/completed/2026-09-28-residual-exit-same-day-ordering-gates.md` (renamed at archival from the deleted open item's name) with witness `class: user-decision` (mirroring the other re-pointed rows; the prior `sibling-boundary` class testified the deleted open item), verifying the target is tracked and its Backlog-origin line names the deleted item before writing [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point the four `SEED_PROTOCOLS` entries in `scripts/machinery_inventory.py` whose refs point into `docs/history/backlog/` to live homes: the two entries whose registry rows this task edits take the rows' new refs, and `quota-probing-budget-guard` / `worktree-recipe` take their own registry rows' current refs (`docs/history/plans/completed/2026-09-28-account-quota-governor.md`, `docs/history/plans/completed/2026-09-28-worktree-first-standard-only-mode.md`); data hygiene only (the scaffold emits seed rows with an empty witness ref regardless, so no Validation Command observes seed content; the on-disk edit is the only gate for this step) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/machinery_inventory.py --check`; expect the seven witness-ref failures gone and only the eight regrowth failures remaining [class: REPOSITORY_TEST]
- [ ] Commit: `fix: re-point 7 dead machinery inventory witnesses to current homes` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Register the 8 unregistered scripts

Files:
- `scripts/machinery_registry.json` *(modified)*

Evidence:
- `python3 scripts/machinery_inventory.py --check`; covers "zero failures: every script registered or removal-listed"
- `python3 scripts/test_machinery_inventory.py`; covers "enforcing suite stays green"

The 8 scripts to register (from the origin item's verbatim failure list): `scripts/check_backlog_root_closure.py`, `scripts/check_investigate_entries.py`, `scripts/check_review_landing_receipt.py`, `scripts/check_skill_description_length.py`, `scripts/codex_model_guard_probe.py`, `scripts/prestage_freshness_gate.py`, `scripts/reconcile_post_landing.py`, `scripts/revert_set_classifier.py`.

- [ ] Run `python3 scripts/machinery_inventory.py --scaffold` to merge candidate rows (disposition `pending`) for the 8 unregistered scripts [class: IMPLEMENTATION_REQUIRED]
- [ ] For each of the 8 pending rows: re-derive the delivering plan from `git log --follow --diff-filter=A --format=%H -- <script path>` (primary source; the ownership registry `docs/maintenance/document-registry.md` is a best-effort cross-check only, since it indexes documents rather than scripts and its rows are backfilled); set `disposition` to `keep`, fill `paths`, list the script's test file under `tests` when one exists (glob `scripts/test_<stem>.py`, verified on disk; 5 of the 8 have one), and set the witness per the registry's class convention: `red-test` with the test file as `ref` when a test file exists, `user-decision` with the delivering plan's archived path under `docs/history/plans/completed/` when it does not, verifying each ref is tracked before writing and keeping the delivering plan named in the row's note in both cases (replacing the scaffold's placeholder note); a script whose delivering plan cannot be re-derived is stood down and reported, never guessed [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `python3 scripts/machinery_inventory.py --check`; expect exit 0 printing "0 failure(s)" [class: REPOSITORY_TEST]
- [ ] Run `python3 scripts/test_machinery_inventory.py`; expect OK (14 tests) [class: REPOSITORY_TEST]
- [ ] Commit: `fix: register 8 machinery inventory scripts with delivering-plan witnesses` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `git show --name-only --format=%h HEAD HEAD~1`; expect the two task commits' combined file set to cover exactly `scripts/machinery_registry.json` and `scripts/machinery_inventory.py` [class: REPOSITORY_TEST]
