# Plan: Scope the gate-removal missing-destination hold to the adjudicated branch record's own rows

Backlog origins (scope of record):
- docs/history/backlog/2026-10-31-gate-removal-inherited-manifest-rows.md

Driving force: correctness

Execution budget: 1h total, largest task 0.5h

Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-gate-removal-inherited-manifest-rows-p<token>-r*.md

Authoring claim: docs/tmp/authoring-claims/gate-removal-inherited-manifest-rows.md (session zcode-auth-carrier-a8d20c4a-20261101T1603)

## Terms

- **The manifest**: `<session-dir>/closeout-migration.json`, the shared closeout-migration manifest whose canonical session slug strips the plan date, so re-runs of one plan extend one manifest (execute-plan Step 0.4 canonical session-slug rule).
- **Branch record**: one element of the manifest's `branch` list, written per migrate run as `{"branch": <name>, "source": <path>}`; `_resolve_closeout_reference_state` takes the last element as the authoritative adjudication binding.
- **Verified destination**: a truthy `destination` of a row carrying a truthy `verified` mark, collected by the resolver from the `migrated` then `renamed` sections, manifest-wide, duplicates preserved.
- **The missing-destination hold**: the `cmd_gate_removal` guard segment that fails the guard when a verified destination does not exist under the target (`migrated artifact(s) missing under the target`), with the done-session gate-report exception (`_is_done_session_gate_report`) carved out report-only (the partial arm, landed `eebc930c0`).
- **Run attribution stamp**: the new `record_index` field `_append_manifest` writes onto every row it appends while a `branch` section is present, naming the index the run's branch record takes (or will take) in the manifest's `branch` list; a stamp is recognized only when the value is an int (bool excluded), and `interrupted` is a bool marker carrying no rows, so only `incomplete` among the auxiliary sections carries stampable rows.
- **Adjudicated index**: `len(records) - 1`, the last branch record's position, the record the gate adjudicates.
- **Legacy rows**: rows carrying no stamp. A manifest whose `branch` list holds exactly one record is a single-run legacy manifest; more than one record is a multi-run legacy manifest.

## Why

The manifest is shared per canonical session slug and append-only: every re-run of a plan adds its rows to the same `migrated`/`renamed` arrays. The gate's missing-destination hold runs over all of them, so a prior run's gitignored destination, once drained by the sanctioned docs/tmp sweep lifecycle, permanently refuses every later run's teardown under the fail disposition (witnessed twice 2026-10-31; the partial arm excludes only the done-session gate-report class, and `PLAN_SLUG_PROOF_FILES` retains the manifest by canonical name, so the rows never age out on their own). The refusal is safe but unbounded, and the trigger is every plan re-run.

## Gist & Examples

TLDR: Stamp each migrate row with its run's branch-record index and scope the missing-destination hold to the adjudicated record's own rows, demoting prior-run and unattributable rows to report-only notes, so a drained prior-run destination can no longer permanently refuse a later run's teardown (correctness of the refusal, per the origin row).

Before (today): one swept prior-run artifact in the shared manifest holds the gate forever; two 2026-10-31 witnesses retained worktree-plus-branch pairs past closeout under the fail disposition.

After (this plan): only the adjudicated record's own missing destinations hold; prior-run rows and unattributable legacy rows in multi-run manifests surface as report-only foreign notes naming counts; a single-run legacy manifest keeps today's fail-closed hold; the done-session gate-report exception still applies inside the narrowed scope.

Edge cases: re-used branch names across re-runs stay distinct because attribution is the record index, never the branch name; `replaced`/`skipped`/`failed`/`incomplete` rows are stamped but never referenced (only `migrated`/`renamed` feed the resolver's destinations, and `interrupted` is a bool with no rows); the done-session sweep's whole-manifest consumption of `verified_destinations` is unchanged; a manifest with zero branch records never reaches the destination hold.

## Outcome

The gate's hold is scoped to the run it adjudicates and the permanent-refusal class is closed, without weakening fail-closed protection for the adjudicated run.

- `_append_manifest` stamps appended rows with `record_index` at the single choke point; the resolver gains an additive `verified_rows` field (the source rows) beside the untouched `verified_destinations`.
- `cmd_gate_removal` partitions the rows: stamped rows at the adjudicated index keep the hold (fail-closed, gate-report exception preserved); stamped rows at any other index that are missing become a report-only foreign note listing the destinations (today's up-to-five form) plus counts; stamp-less rows keep the hold only in a single-record manifest and become a report-only foreign note otherwise (in a multi-run legacy manifest the adjudicated run's own rows are stamp-less, so their missing artifacts demote to the note per the disclosed posture change).
- No manifest rows are ever deleted or rewritten; the manifest stays append-only.

Gate delta: the hold narrows for two bounded populations (prior-run rows, multi-run legacy rows), priced under the machinery admission protocol's completion shape: incident, the origin row's two 2026-10-31 witnessed retained worktree-plus-branch pairs; expected catch, every plan re-run whose shared manifest carries a prior-run drained destination; false-positive cost, none new for the adjudicated run (its own missing migration still refuses), with the one documented posture change that a multi-run legacy manifest reports unattributable missing rows instead of refusing; review date, the next gate-removal machinery maintenance pass.

## Assumptions

- Record-index attribution wins over branch-name attribution: `authoring/<slug>` branch names repeat across re-runs, so a name-based filter would conflate runs; the index is positionally unique per manifest. Basis: the resolver's own authoritative-binding rule (`records[-1]`) and the origin row's shared-slug mechanism.
- The stamp lands in `_append_manifest`, not in `cmd_migrate`: it is the single persistence choke point for every section, so no row-writing site can forget it, and non-migrate callers (no `branch` section) are unstamped and inert. Basis: `_append_manifest` (the load-extend-atomic-replace helper) and `cmd_migrate`'s sections assembly.
- The multi-run legacy posture change is bounded and loud: unattributable missing rows become report-only foreign notes on the existing notes channel (the `eebc930c0` disposition shape), never silent, and the single-run legacy case keeps the hold so the protection witness (a genuinely missing migration in the common one-run manifest) is preserved byte-for-byte.
- Arm 2 (a sanctioned row-retirement migrate operation) is rejected: it adds a new producer-contract operation, new machinery surface, to solve the same block the scoping removes. Basis: the origin row's and the entry's rejected alternatives (auto-delete on absence erases loss evidence; per-run manifest files are a larger producer-contract change).
- A check-time-only fix with no stamp was considered and rejected as unsound: rows carry no run identity today, so no read-side rule can attribute them; the stamp is the minimal write-side attribution the scoping needs.

Decision points requiring a grill: none remain. The maintenance-selected authoring authorization resolves the source-supported choices above (the attribution-model receipt sits in the first Assumption).

Scope extensions (grilled): none proposed. The retention-family surfaces and the sweep's consumption are omitted under the maintenance-selected scope (`omit-extension` disposition).

Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**

- A prior-run drained destination no longer refuses a later run's teardown; it surfaces as a report-only note.
- The adjudicated run's own missing migration still refuses when its rows are stamped or the manifest is single-record legacy; multi-run legacy manifests report unattributable rows instead of refusing (the disclosed posture change).

**Done when:**

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q` passes with the new attribution and scoping tests, and the preserved expired-gate-report test stays green.

**Ship when:**

- None; this plan is repository-verifiable.

## Design Invariants

- The hold for rows attributable to the adjudicated record is never weakened: stamped rows at the adjudicated index keep the exact today refusal text and guard-failure behavior, and a single-run legacy manifest keeps today's hold for all its rows; the one disclosed demotion is the multi-run legacy population, whose unattributable rows (which may include the adjudicated run's own) report instead of refusing.
- `_resolve_closeout_reference_state`'s existing fields and error semantics are unchanged; `verified_rows` is additive and no consumer outside the gate reads it.
- No new gate, ledger, registry, or migrate operation: the stamp is data, not machinery (machinery admission completion shape).
- The manifest stays append-only; nothing rewrites or drops rows, including legacy ones.

## Review Scope

**Explicit must-fix:**

- `scripts/worktree_closeout_migrate.py`: the `_append_manifest` stamp, the resolver's additive `verified_rows`, and the `cmd_gate_removal` scoped hold with its report-only note arms.
- `scripts/test_worktree_closeout_migrate.py`: the two-run drained-destination pass test, the adjudicated-row fail-closed test, the legacy single-run hold test, the mixed legacy-plus-stamped transition tests (pass+note and refuse), and the stamp unit test.
- `docs/history/backlog/2026-10-31-gate-removal-inherited-manifest-rows.md`: one sentence appended to the Partial arm paragraph noting the full scoping lands via this plan (the row's history stays true; the landing flips the row covered).

**Production code:**

- The single production script named under Explicit must-fix; no other script, skill, or hook file changes.

**Validation:** See the commands in `Validation Commands` below.

**Out of scope; reject unless plan-related:**

- The done-session sweep's consumption of `verified_destinations` and any retention-family change.
- Row retirement, deletion, or manifest format versioning (the rejected arm 2 shapes).
- The `interrupted`/`incomplete` section semantics beyond receiving the stamp.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)"
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: Run attribution stamp and the scoped missing-destination hold

Files: `scripts/worktree_closeout_migrate.py`, `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_append_manifest` in `scripts/worktree_closeout_migrate.py`, the persistence choke point this plan stamps
- `_resolve_closeout_reference_state` in `scripts/worktree_closeout_migrate.py`, the resolver this plan extends additively
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`, the missing-destination hold segment this plan scopes

- [ ] In `_append_manifest`, when the sections carry a `branch` list, compute the incoming record's index as the current length of the manifest's `branch` list and stamp every appended row of every list section with `"record_index": <index>`; when no `branch` section is present, append unstamped exactly as today. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `_resolve_closeout_reference_state`, collect the additive `verified_rows` field (the verified row dicts from `migrated` then `renamed`, manifest order, duplicates preserved) beside the untouched `verified_destinations`; the `destinations_error` handling covers both fields identically. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the `cmd_gate_removal` guard segment, hold on missing rows attributed to the adjudicated index exactly as today: a stamp counts only when its `record_index` is an int (bool excluded); the `_is_done_session_gate_report` exception stays report-only within this scope. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same guard segment, demote the unattributed population to a report-only foreign note: stamped rows at any other index, and stamp-less rows whenever `len(records) > 1`, join a note listing the missing destinations (today's up-to-five form) plus the attributed and unattributed counts, never holding the guard. [class: IMPLEMENTATION_REQUIRED]
- [ ] Test the pass path: two migrate runs into one session dir whose run-1 drained destination is a non-gate-report shape; the gate prints the removal authorization line and no held or failed-guard disposition, with the report-only note naming the drained destination. [class: IMPLEMENTATION_REQUIRED]
- [ ] Test the hold paths: (a) the adjudicated run's own destination missing in a multi-record manifest refuses with today's text; (b) a single-record legacy manifest (unstamped rows) still refuses. [class: IMPLEMENTATION_REQUIRED]
- [ ] Test the legacy and mixed transitions: (a) a multi-record all-unstamped manifest reports unattributed rows and passes; (b) a mixed manifest (unstamped record-0 rows with a drained non-gate-report destination beside stamped record-1 rows) passes with the note; (c) the same mixed shape with a missing stamped adjudicated destination refuses while the legacy note still prints. [class: IMPLEMENTATION_REQUIRED]
- [ ] Test the stamp: a migrate run stamps its rows with the incoming record's index; the preserved expired-gate-report test stays green. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the suite and confirm green before committing. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `fix: scope gate-removal missing-destination hold to the adjudicated branch record's rows` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Origin row note and full-gate verification

Files: `docs/history/backlog/2026-10-31-gate-removal-inherited-manifest-rows.md`

- [ ] Append one sentence to the row's Partial arm paragraph noting the remaining breadth (non-gate-report drained destinations, unattributable legacy rows) closes via this plan's record-index scoping, naming the bounded posture change (multi-run legacy manifests report unattributable missing rows instead of refusing) beside the `eebc930c0` partial-arm history. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full `Validation Commands` set and confirm the suite, pins, em-dash gate, and hygiene scan are clean (a pins failure red at base is reported as pre-existing with no delta contribution, never folded silently). [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: note the completed gate-removal scoping on the origin row` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- None: the gate's and resolver's docstrings carry the attribution model; no skill text references the manifest row shape.
