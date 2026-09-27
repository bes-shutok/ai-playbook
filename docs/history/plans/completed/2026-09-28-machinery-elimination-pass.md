# Plan: Machinery elimination pass

Backlog origin: docs/history/backlog/2026-09-28-machinery-elimination-pass.md
Driving force: simplicity
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-machinery-elimination-pass-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Every guard, protocol, and scheduler state field in this repository is tied to the witnessed failure that justifies its compute, and anything that cannot cite a witness is deleted instead of silently kept.

- A machine-checkable inventory (registry plus script) lists every guard script, hook, review-round mechanism, protocol layer, and scheduler state field, with a witness column and a keep-or-delete disposition per entry.
- Entries failing the witness standard are deleted together with their tests, prose references, and registry rows, and the deletions are proven stale-reference-free.
- The inventory script remains as the standing guard: any future unregistered script, hook, or state field fails the check, so machinery cannot regrow silently.
- The four mechanisms the origin names as the expected kept set (public hygiene scan, landing parentage gate, disk-truth verification, minimal claim-if-concurrent rule) carry their citations explicitly.

## Terms

- Machinery registry: the versioned data file `scripts/machinery_registry.json` enumerating every inventory entry with its kind, paths, witness, and disposition; the single source the inventory script validates.
- Witness: a citation justifying kept machinery, in one of the registry's witness classes: `origin-kept-set` (the origin's Expected kept set, a user decision), `red-test` (a test file in this repository's suite that fails when the machinery breaks), `incident` (a repo-durable recorded failure document), `user-decision` (a standing written instruction such as AGENTS.md), `sibling-boundary` (an open sibling item's recorded scope boundary).
- Spent witness: a witness whose triggering event is complete (a one-shot migration already executed, a recovery already landed); it does not re-earn its compute, so the entry deletes with the completed event cited in its note.
- Boundary keep: a keep whose witness is an open sibling item's recorded scope boundary (review-loop exit and cap machinery, the maintenance pipeline continuation fields, the worktree recipe, the residual-exit semantics); these stay until the owning item's outcome and the registry note names the owner.
- Standing regrowth guard: the inventory script's check mode, which fails on any unregistered machinery file, hook, or schema-section state field, and on any registry row failing schema or witness rules; all check inputs are tracked, so the guard is worktree-independent.

## Assumptions

- assume the registry, not the plan prose, is the machine-checkable enumeration the origin asks for; basis: the origin's Suggested fix item 1 ("a script listing gates and state fields is enough; the witness citation is a column in its output"); the plan seeds the disposition procedure, the schema, the kept-set citations, and the named delete rows, and the registry carries every row.
- assume most live machinery legitimately re-earns its place under the origin's own witness vocabulary, because the repository's guard scripts carry red tests in the suite and standing user-decision mandates (AGENTS.md hygiene, vendored-sync, and portability rules); basis: the authoring survey (2026-09-28) found test coverage for the majority of scripts/ entries and consumer references for all but a handful; the plan records this outcome honestly instead of forcing deletions the evidence does not support.
- assume sibling-owned surfaces stay untouched: review-loop exit and cap machinery (origin docs/history/backlog/2026-09-28-review-loop-exit-condition-and-metrics.md, plan landed main 3d029c87), the maintenance pipeline continuation and its state fields (open origin docs/history/backlog/2026-09-28-maintenance-autonomous-pipeline.md), and the worktree recipe (origin docs/history/backlog/2026-09-28-worktree-first-standard-only-mode.md); basis: the origin's own scope boundary paragraph, which names exactly these three. Two further boundaries are author extensions accepted under the origin prompt's standing pre-authorization: the account quota surfaces (open origin docs/history/backlog/2026-09-28-account-level-quota-governor.md, the wave sibling being authored in parallel) and the residual-acceptance exit semantics (open origin docs/history/backlog/2026-09-19-residual-exit-same-day-ordering-semantics.md, whose open plan owns that exit's machinery); both extensions keep this plan from deleting machinery an open sibling is actively reshaping.
- assume the executor runs the inventory script's scaffold mode first and dispositions the generated rows with the plan's decision procedure, recording the outcome in the committed registry; basis: the origin's Suggested fix sequence (generate, disposition, land, keep the script).
- assume `agents/hooks/` hook directories and the observed scheduler state file keys are machinery classes the registry must cover; basis: the origin's Problem paragraph names scheduler state fields and protocol layers, and the hooks directories are executable guard machinery.

Decision points requiring a grill: deletion is the default disposition with keeps requiring citations, and the expected kept set is the four origin-named mechanisms (user direction recorded in the origin's Expected and Environment sections, 2026-09-28; Tasks 1 through 4); the inventory is generated mechanically with the witness as a column (user direction recorded in the origin's Suggested fix item 1, 2026-09-28; Task 1); sibling boundaries stay untouched until the owning items' outcomes (user direction recorded in the origin's scope boundary paragraph, 2026-09-28; Task 2); spent one-shot witnesses delete with the completed event cited (author recommendation accepted under the origin prompt's standing pre-authorization, applying the origin's "re-earn its place or go" standard, 2026-09-28; Task 2).

## Gist & Examples

TLDR: a registry-plus-script inventory ties every guard, protocol, and state field to its witness and deletes what cannot cite one, leaving the script as the standing guard against regrowth, for simplicity (active elimination).

Today no single artifact answers "why does this gate exist"; machinery is added by plans and almost never removed, and the inventory lives in reviewers' heads. After this plan, `python3 scripts/machinery_inventory.py --check` is the arbiter: it fails on unregistered machinery, on keeps without resolving witnesses, and on deleted machinery reappearing.

Examples:

- `scripts/migrate_backlog_completed.py` and its test file executed the one-shot backlog-completed archive migration (completed plan docs/history/plans/completed/2026-09-25-backlog-completed-archive-policy.md, landed 2026-09-25); the witness is spent, so both files delete and their registry rows move to the removals list.
- A future plan adds `scripts/new_guard.py` without registering it; the next `--check` run fails with the unregistered-path error until the plan either registers the machinery with a witness or deletes it.
- The landing parentage gate keeps with a `red-test` witness naming its suite file, plus an `incident` note citing the orphan-history rebuild the gate prevents.

## Evaluation Criteria

**Quality dimensions:**

- completeness: the check fails when any non-test script, hook directory, tracked-schema state field, or registered protocol lacks a registry row (verified by temporarily renaming a file in a scratch copy and watching the check fail).
- honesty of dispositions: every keep cites a resolving witness in an allowed class; every delete names its spent event or absence of witness; no disposition without a basis.
- deletion hygiene: deleted entries leave zero stale references in scripts/, agents/, projects/.ai-playbook/, docs/maintenance/, and README.md, each proven by a negated sweep.
- minimality: no new validation layer beyond the inventory script and its suite test; the standing guard is one command.

**Done when:**

- `scripts/machinery_inventory.py` with `--scaffold` and `--check` modes exists, and `scripts/machinery_registry.json` carries the full dispositioned inventory (scripts, hooks, state fields, named protocols) including a removals list.
- the named delete rows are landed with their tests and references, and the negated sweeps pass.
- the four origin kept-set mechanisms carry their citations in the registry.
- the suite test `scripts/test_machinery_inventory.py` runs the check mode hermetically and the maintenance skill's survey step consults the guard.
- the Validation Commands block passes end to end.

**Ship when:**

- sibling items' outcomes revisit their boundary keeps (human-owned sequencing; not this plan's checklist).
- other repositories adopt the registry pattern for their own machinery (per-project decision).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/machinery_inventory.py` *(new)*
- `scripts/machinery_registry.json` *(new)*
- `scripts/migrate_backlog_completed.py` *(deleted by Task 3)*
- `scripts/test_migrate_backlog_completed.py` *(deleted by Task 3)*
- `agents/skills/maintenance/SKILL.md`

**Tests:**

- `scripts/test_machinery_inventory.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. Registry delete rows discovered during Task 2's disposition pass may name additional scripts, tests, and prose references; deleting those files and their references is plan-related work under the registry row, and each such path joins the explicit list through its row's paths and note. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- review-loop exit and cap machinery, validator scripts, and staging governance; owned by the landed review-loop exit-condition-and-metrics plan and its open origin (sibling boundary).
- scheduler state fields in the pipeline family (pending_dispatch, pending_rearm, pending_landing, and the other fields the tracked State file schema names whose repair the pipeline sibling owns); owned by that open sibling.
- quota probing and budget-guard machinery; owned by the account-quota-governor sibling (open origin).
- worktree lifecycle recipes; owned by the worktree-first sibling.
- residual-acceptance exit machinery in the execute-plan runtime; owned by the open residual-exit origin.
- `agents/skills/` prose beyond the reference cleanup Task 3's location-based sweep performs; this plan deletes machinery, not skill bodies, and skill rewrites beyond reference cleanup are their own plans.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. Standing regrowth guard: the registry validates against the tree (Task 1 onward;
# at the Task 1 gate run it with --allow-pending while the scaffold rows are still pending).
( cd "$REPO" && python3 scripts/machinery_inventory.py --check ) || { echo "FAIL: machinery inventory check failed"; exit 1; }

# 2. Suite test for the inventory (Task 4); hermetic, scratch-tree completeness probe included.
( cd "$REPO" && python3 -m unittest discover -s scripts -p "test_machinery_inventory.py" ) || { echo "FAIL: inventory suite test failed"; exit 1; }

# 3. Named deletion landed: files gone, zero stale references (Task 3).
test ! -e "$REPO/scripts/migrate_backlog_completed.py" || { echo "FAIL: spent migration script still present"; exit 1; }
test ! -e "$REPO/scripts/test_migrate_backlog_completed.py" || { echo "FAIL: spent migration test still present"; exit 1; }
sweep_rc=0
# machinery_registry.json is excluded: its removals rows are the sanctioned
# retention record of the deleted basenames (the check's removals arm requires
# those paths to stay listed after the files are gone).
grep -rqF "migrate_backlog_completed" "$REPO/scripts" --exclude=machinery_registry.json "$REPO/agents" "$REPO/projects/.ai-playbook" "$REPO/docs/maintenance" "$REPO/README.md" 2>/dev/null || sweep_rc=$?
test "$sweep_rc" -le 1 || { echo "FAIL: stale-reference sweep tool error (rc=$sweep_rc)"; exit 1; }
test "$sweep_rc" -eq 1 || { echo "FAIL: stale references to deleted migration machinery"; exit 1; }

# 4. Kept-set citations resolve (Task 2): the four origin-named mechanisms stay, cited.
( cd "$REPO" && python3 - <<'PYKEEP' ) || { echo "FAIL: kept-set citations unresolved"; exit 1; }
import json, os, sys
from pathlib import Path
reg = json.loads(Path("scripts/machinery_registry.json").read_text())
rows = {r["id"]: r for r in reg["entries"]}
kept_names = {"public-hygiene-scan", "landing-parentage-gate", "disk-truth-verification", "claim-if-concurrent"}
missing = kept_names - set(rows)
assert not missing, f"missing kept-set rows: {missing}"
for name in sorted(kept_names):
    row = rows[name]
    assert row["disposition"] == "keep", name
    assert row["witness"]["class"] == "origin-kept-set", name
    assert Path(row["witness"]["ref"]).exists(), name
PYKEEP

# 5. Em-dash cleanliness, scoped to what this plan creates and adds (rule 28: edited
# files carry legacy content no task touches). BASE is recorded by Task 1's first
# item before any task commit; the unset guard keeps a missing base from scanning nothing.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-machinery-elimination-pass.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
test -n "$BASE" || { echo "FAIL: BASE not recorded (Task 1 first item)"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE" ) || { echo "FAIL: em-dash in added lines"; exit 1; }

# 6. Maintenance consult landed (Task 4).
grep -qF "machinery_inventory.py --check" "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: maintenance consult missing"; exit 1; }
```

### Task 1: Inventory script and registry scaffold

Files:

- `scripts/machinery_inventory.py` *(new)*
- `scripts/machinery_registry.json` *(new)*
- `scripts/test_machinery_inventory.py` *(new)*

- [ ] Record the base revision for validation command 5 in the run notes: `BASE="$(git rev-parse HEAD)"`, executed before any task commit of this run. [class: REPOSITORY_TEST]
- [ ] Create `scripts/machinery_inventory.py` (stdlib only, no em-dashes) with two modes: `--scaffold` generates candidate registry rows from TRACKED sources only (every non-test `scripts/*.py` and `scripts/*.sh` file, every `agents/hooks/*/` directory, every state-field name parsed from the tracked "State file" schema section of `agents/skills/maintenance/SKILL.md`, plus the seed protocol rows listed in Task 2) with `disposition: "pending"` and empty witnesses; state-field rows carry key-qualified ids (`state-field:<name>`) and empty `paths` so they never trip the overlapping-paths arm, and the gitignored observed state file, when present, is a cross-check that only adds rows, never a check input; `--check` validates the registry against the tracked tree and fails non-zero on any of: an existing non-test scripts file or hooks directory, or a schema-section state-field name, with no registry row (regrowth), a row whose paths do not exist for a keep disposition, a keep whose witness class is none or whose ref does not resolve (path exists for red-test, incident, user-decision, sibling-boundary, and origin-kept-set refs; every ref must point at a TRACKED path so the check is worktree-independent), a delete row without a note naming its spent event or unwitnessed basis, duplicate ids or overlapping paths, or a removals-list row whose paths still exist, or a row whose disposition is `pending` (the scaffold tolerance flag `--allow-pending` skips exactly that arm and nothing else, so the Task 1 scaffold gate can pass an all-pending registry while every later gate fails one). [class: IMPLEMENTATION_REQUIRED]
- [ ] Create `scripts/machinery_registry.json` with `schema_version: 1`, `entries: []`, `removals: []`, and the row schema: `id`, `kind` (`script` | `hook` | `state-field` | `protocol`), `paths` (array), `tests` (array of witness test files, may be empty), `witness` (`{"class": "none" | "origin-kept-set" | "red-test" | "incident" | "user-decision" | "sibling-boundary", "ref": string or null}`), `disposition` (`pending` | `keep` | `delete`), `note`. [class: IMPLEMENTATION_REQUIRED]
- [ ] `scripts/test_machinery_inventory.py`; given a scratch tree built in a temp directory carrying a tracked-layout fixture (a scripts directory with one registered and one unregistered script, a hooks directory, a fixture skill file carrying a two-field schema section), expects `--scaffold` to emit rows for both scripts, the hooks directory, and each schema field, and `--check` to exit zero once the generated rows are dispositioned with resolving witnesses; then, one arm at a time, each of these mutations makes `--check` exit non-zero: the unregistered script left out of the registry (regrowth), a keep row whose ref path is missing, a keep row with witness class none, a delete row with an empty note, a duplicate row id, a removals row whose path still exists, a schema field missing its row, a keep row whose paths do not exist in the tree, two rows sharing one path (overlapping paths), and a row reverted to `pending`, which plain `--check` fails and `--allow-pending` passes; ends with explicit temp-directory teardown. [class: REPOSITORY_TEST]
- [ ] Run → expect RED before implementation: validation command 1 (the script does not exist today); expect GREEN after this task with an all-pending scaffold registry checked into the tree, running the check with `--allow-pending` at this task point only (plain `--check` at this point exits non-zero on the pending rows by design). [class: REPOSITORY_TEST]
- [ ] Commit: `stats: machinery inventory script with registry scaffold and check modes` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Disposition the inventory

Files:

- none beyond Task 1's registry and script; this task edits only `scripts/machinery_registry.json` (created in Task 1 and already listed under Review Scope)

- [ ] Run `--scaffold`, then disposition every generated row with the decision procedure: keep when the row cites a resolving witness in an allowed class (origin kept set, red test that exists in the suite, repo-durable incident document, standing written user decision, open sibling boundary); delete when no witness resolves or the witness is spent (a one-shot event already executed, with the completed event named in the note); no row stays `pending`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Seed these kept-set rows explicitly, citing the origin Expected kept set (witness class `origin-kept-set`, ref `docs/history/backlog/2026-09-28-machinery-elimination-pass.md`): `public-hygiene-scan` (protocol; paths `docs/scan-public-hygiene.patterns.example` plus the AGENTS.md mandate; note names the deployed scanner home), `landing-parentage-gate` (script; paths `scripts/landing_parentage_gate.py` and its suite test; note names the orphan-history incident it prevents), `disk-truth-verification` (protocol; ref additionally cites the plans skill degraded-generation section), `claim-if-concurrent` (protocol; ref cites the tracked maintenance authoring blueprint section that mandates the claim file, `agents/skills/maintenance/prompt-templates.md`; the gitignored claims directory under `docs/tmp/authoring-claims/` is named in the note only, never as a resolving path). [class: IMPLEMENTATION_REQUIRED]
- [ ] Seed these protocol rows explicitly (the plan's named-protocol universe; kind `protocol`, disposition per the decision procedure): five-round review cap and cap-closure terminal shape (sibling boundary, ref `docs/history/backlog/2026-09-28-review-loop-exit-condition-and-metrics.md`), review-staging sidecar schema governance and the staging validator hard gates (red test: `scripts/validate_review_staging.py` suite via `scripts/plan_readiness.py` tests), plan readiness gate (red test: `scripts/test_plan_readiness*.py` if present, else user-decision: AGENTS.md commit rules), digest re-certification arm and receipt/generation fencing in the execute-plan runtime (red tests: `scripts/test_execute_plan_runtime.py`), merge landing lock (incident: the orphan-history rebuild recorded under `docs/history/plans/completed/2026-09-27-churn-prevention-landing.md` if present, else red test), budget pause protocol (red tests: `scripts/test_execute_plan_resume_watcher.py`), done-sweep gates (red test: `scripts/test_done_sweep_gates_lib.py`), reverse-squash and dirt gates (incident: the staged-revert dirt incident recorded in `projects/.ai-playbook/development_lessons.md`), skills-gate marker machinery (user-decision: `agents/hooks/skill-gate/README.md`), quota probing and budget guard (sibling boundary, ref `docs/history/backlog/2026-09-28-account-level-quota-governor.md`), worktree recipe (sibling boundary, ref `docs/history/backlog/2026-09-28-worktree-first-standard-only-mode.md`), residual-acceptance exit (sibling boundary, ref `docs/history/backlog/2026-09-19-residual-exit-same-day-ordering-semantics.md`); a cited ref that does not exist resolves at execution to the tracked alternative named in the same bullet (the test file that exists, or the tracked skill section), and the registry note records which was used. [class: IMPLEMENTATION_REQUIRED]
- [ ] Disposition the remaining state-field rows by tracked-consumer evidence: a state field read or written by a tracked surface (`agents/skills/maintenance/SKILL.md`, the runtime driver and its tests) keeps with witness class `user-decision` (ref: the tracked skill section) or `red-test` (ref: the covering test file); a state field no tracked surface references deletes with the note naming the zero-reference sweep; the pipeline state-field family named by the tracked State file schema keeps under the pipeline sibling boundary regardless of consumer evidence. [class: IMPLEMENTATION_REQUIRED]
- [ ] Disposition `migrate_backlog_completed.py` and `scripts/test_migrate_backlog_completed.py` as delete (spent witness: the one-shot backlog-completed archive migration executed 2026-09-25, completed plan `docs/history/plans/completed/2026-09-25-backlog-completed-archive-policy.md`), and disposition any further scaffold rows that fail the standard the same way, each with its spent event or unwitnessed basis in the note. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 1 with every row dispositioned and every keep's witness resolving; expect the command to fail if any row is reverted to pending (spot-check by temporarily flipping one row in a scratch copy of the registry, then restoring it). [class: REPOSITORY_TEST]
- [ ] Commit: `stats: disposition machinery inventory with witness citations` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Land the deletions

Files:

- `scripts/migrate_backlog_completed.py` *(deleted)*
- `scripts/test_migrate_backlog_completed.py` *(deleted)*

- [ ] For every row dispositioned delete in Task 2 (the named migration pair plus any further rows): delete the files, move the row from `entries` to `removals` with its note intact, and sweep its basename across `scripts/`, `agents/`, `projects/.ai-playbook/`, `docs/maintenance/`, and `README.md`, cleaning every stale reference (a reference in a completed-history document under `docs/history/` is history and stays; the registry's own removals row is the one sanctioned post-landing retention of the deleted basenames, and validation command 3 excludes it for exactly that reason). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 3 (files gone, negated sweeps clean, removals list consistent) and command 1 (the check passes with the removals rows present). [class: REPOSITORY_TEST]
- [ ] Commit: `stats: land machinery deletions with stale-reference sweeps` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Standing guard wiring

Files:

- `agents/skills/maintenance/SKILL.md` (the Task 1-created test file gains one suite-level test here; it is already listed under Review Scope)

- [ ] In the maintenance skill's survey step (Step 1 area), add one consult bullet: run `python3 scripts/machinery_inventory.py --check` and report a non-zero exit as a maintenance finding (regrown or unregistered machinery), sharing the step's guard and fail-open semantics; the guard is consultative here, the suite test is its enforcing arm. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend `scripts/test_machinery_inventory.py` with a suite-level test that runs the check mode against the real repository tree and asserts exit zero (the enforcing arm of the standing guard). [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: validation command 6 (maintenance consult pin) and command 2 (the suite test, now covering the real tree). [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the full Validation Commands block (rule 21 interim expectation: at this point every command in the block passes). [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: wire the machinery regrowth guard into the survey consult and suite` [class: IMPLEMENTATION_REQUIRED]

## Origins dispositions

- `docs/history/backlog/2026-09-28-machinery-elimination-pass.md` - folded into this plan at execution (squash main 8f769503); origin file deleted.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-28-machinery-elimination-pass.md` was deliberately folded into this plan and its per-item file deleted at execution (squash main 8f769503).
