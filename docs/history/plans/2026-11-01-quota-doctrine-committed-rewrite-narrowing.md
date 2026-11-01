# Plan: Re-anchor the quota-wall witness's committed-revision acceptance to named sanctioned landings

Backlog origins (scope of record):
- docs/history/backlog/2026-10-30-quota-doctrine-committed-rewrite-narrowing.md

Driving force: code-quality

Execution budget: 1h total, largest task 0.5h

Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-quota-doctrine-committed-rewrite-narrowing-p<token>-r*.md

Authoring claim: docs/tmp/authoring-claims/quota-doctrine-committed-rewrite-narrowing.md (session zcode-automation-fd0142f8-20261101T1049)

## Terms

- **The witness**: `scripts/test_quota_wall_doctrine.py`, the directives-file byte-level witness family holding every pre-existing operator-directive record in the file - derived from its `## D-<n>:` headings, D-1..D-17 at authoring time - textually unchanged against a baseline revision.
- **Record-anchor resolution** (`_record_anchor_revision`): the new pure helper that resolves each record's anchor revision.
- **Identity cross-check**: the witness's existing check anchoring this plan's directive record by id and witness literal.
- **Uncommitted drift arm**: the witness's existing red for working-tree changes against the baseline, unchanged by this plan.
- **The em-dash landing (`99f9cd84e`)**: the 2026-10-27 em-dash formatting pass, the witnessed sanctioned revision for D-3..D-5.
- **The D-6/D-17 landing (`fda4548ac`)**: the 2026-10-31 sanctioned landing that flipped D-6 superseded and introduced D-17; the newest sanctioned revision for both.
- **Committed-revision acceptance arm**: the witness behavior that, when the working tree differs from the baseline, accepts the newest committed revision as the alternative - today anchored at HEAD, so any committed rewrite becomes the permanent standard.
- **Sanctioned landing**: a commit that legitimately changed the directives file because an operator-directed record update landed through it; recorded by id in the test's named constant.
- **Record anchor**: for each directive record, the newest commit among its introducing commit (the commit that first added the record) and the sanctioned landings whose committed blob changed that record.
- **Regression pin**: the proof that the committed class is fenced, carried by two instruments: the durable fixture test (a synthesized unsanctioned committed rewrite rejected with the record id named, living in the suite) and the transient commit-cycle exercise (a one-word D-7 mutation committed, red asserted naming D-7, then dropped with `git reset --hard HEAD~1`).

## Why

The witness's committed-revision acceptance arm anchors at HEAD, so once any committed rewrite of a pre-existing record lands, that rewrite becomes the standard every later revision inherits: the committed class erodes invisibly. No committed rewrite has occurred yet; the failure class is witnessed by inspection. The record universe is derived from the file's own headings (D-1..D-17 at authoring time), never a pinned range, so the next record lands inside the fence automatically.

## Gist & Examples

TLDR: Re-anchor the witness's committed-revision acceptance from HEAD to per-record named sanctioned landings - each record held to its newest sanctioned revision, a one-line constant extension per future sanctioned landing - so a committed rewrite outside the sanctions goes red naming the record, restoring code-quality of the doctrine fence.

Before (today): a committed rewrite of any record in the file passes the witness permanently (HEAD becomes the standard); enforcement for the committed class narrows to pre-commit discipline; the silent-erosion class has no post-hoc red and no durable test would notice a regression to HEAD-acceptance.

After (this plan): each record is held against its record anchor; a committed unsanctioned rewrite goes red naming the record id; a sanctioned landing extends the named constant by one line and the suite stays green; the durable fixture test asserts the fence's red path in the suite, and the transient commit-cycle pin exercises it against the real file once.

Edge cases: a record's introducing commit is always sanctioned by definition (the operator-directed record creation), so the anchor exists for every record from D-1 to D-17; the suite edits that accompany a sanctioned landing are not directive-file rewrites and never need the constant; an uncommitted drift keeps today's red-with-id behavior unchanged.

## Outcome

The witness's committed class is fenced against silent erosion: post-edited records are held to their newest sanctioned revision, and the fence is proven live by the regression pin.

- The acceptance arm's HEAD anchor is replaced by the record-anchor resolution; the uncommitted drift arm and the identity cross-check are unchanged.
- The named constant starts with the two witnessed sanctioned landings, `99f9cd84e` (the em-dash landing; newest sanctioned revision for D-3..D-5) and `fda4548ac` (the D-6/D-17 landing; newest sanctioned revision for D-6 and D-17); every record's introducing commit completes the anchors, and the re-anchored suite is green against the live tree before the commit lands.
- The origin row's and its sibling count row's record-range text read the derived-from-headings universe (D-1..D-17 at authoring time).

Gate delta: the witness-validator's checked set grows - the committed-rewrite class gains a post-hoc red it does not have today - priced under the machinery admission protocol's completion shape: incident, the origin row's by-inspection witness (no landed incident; the class is fenced pre-commit only); expected catch, any unsanctioned committed rewrite of any record; false-positive cost, a sanctioned landing needs a one-line constant extension (and a red until it lands); review date, the next directives-file maintenance pass.

## Assumptions

- The named per-record sanction list wins over the single dated anchor: the dated anchor covers only D-3..D-6, while the record-anchor rule (introducing commit plus named sanctioned landings) mechanically covers all seventeen records and keeps the future cost of a sanctioned rewrite at one constant line. Basis: the origin row's Direction records both options without selecting; the seed set is grounded in the live tree (D-3..D-5 at `99f9cd84e`, D-6 and D-17 at `fda4548ac`, every other record at its introducing commit).
- Accepting HEAD with a per-rewrite marker file was rejected before authoring (the origin row's own rejected alternative: new machinery with no witnessed incident), and this plan does not revive it.
- The regression pin is a transient commit cycle by design: the mutation is committed (the committed class is the one under test - an uncommitted edit already reds today and cannot discriminate), the red asserted naming D-7, and the commit dropped with `git reset --hard HEAD~1` in the same task, with a clean-tree check closing the task; the durable teeth live in the fixture test, which is hermetic and re-runnable. Basis: the origin row's Regression pin paragraph (which says "commit a one-word edit") and the suite's read-only docstring (the pin is a task step, never an in-suite test against the real file).
- The record-range corrections are text-only edits to this origin row and the sibling count row's target text; the sibling row stays open for its own concerns. Basis: the two rows' Cluster lines (the sibling routes ad-hoc separately).

- The origin row's landing disposition: the row stays open, re-scoped to the preamble acceptance residual (the same acceptance exists for the preamble; this plan's Task 2 text corrections are living-row edits), so the durable record of that residual survives the landing. Basis: the row's Problem parenthetical and the plans skill's omit-extension disposition (no new row created).

Decision points requiring a grill: none remain. The maintenance-selected authoring authorization resolves the source-supported choice above (the anchor-model receipt sits in the first Assumption).

Scope extensions (grilled): none proposed. The preamble acceptance arm and the identity cross-check's own semantics are omitted under the maintenance-selected scope (`omit-extension` disposition); the preamble residual's record lives in the re-scoped origin row.

Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**

- The committed class has a post-hoc red: an unsanctioned committed rewrite names the rewritten record id.
- A sanctioned landing keeps the suite green with a one-line constant extension.

**Done when:**

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_wall_doctrine.py -q` passes with the new anchor tests including the durable fixture test.
- The regression pin, given a transient one-word D-7 mutation: expects the suite red with D-7 named; reverted, expects the suite green.

**Ship when:**

- None; this plan is repository-verifiable.

## Design Invariants

- The witness's whole-file value holds: all seventeen records stay under the byte-level witness; no record-range narrowing.
- The uncommitted drift arm's red-with-id behavior is unchanged by this plan.
- No new machinery: the sanctioned set is a named constant in the test, not a marker-file scheme.

## Review Scope

**Explicit must-fix:**

- `scripts/test_quota_wall_doctrine.py`: the record-anchor resolution (the named sanctioned-landing constant plus the introducing-commit fallback), the committed-revision acceptance re-anchored to the record anchors, and the red naming the rewritten record id.
- `docs/history/backlog/2026-10-30-quota-doctrine-committed-rewrite-narrowing.md` and the record-range sentence of `docs/history/backlog/2026-10-30-inventory-count-reconciliation.md`: D-1..D-12 corrected to the derived-from-headings universe (D-1..D-17 at authoring time).

**Production code:**

- Beside `_baseline_revision`, the witness module may gain the small pure anchor-resolution helper; the existing helpers stay.

**Validation:** See the commands in `Validation Commands` below.

**Out of scope; reject unless plan-related:**

- Changes to the directives file's records themselves (the regression pin's mutation is transient and reverted).
- Marker-file or HEAD-acceptance schemes (the origin row's rejected alternatives).
- The sibling count row's other concerns.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_wall_doctrine.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)"
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: Record-anchor resolution and the re-anchored acceptance arm

Files: `scripts/test_quota_wall_doctrine.py`

Primary class anchors:
- `_baseline_revision` in `scripts/test_quota_wall_doctrine.py`, the revision model this plan re-anchors
- `_record_anchor_revision` in `scripts/test_quota_wall_doctrine.py`, the per-record anchor decision

- [ ] Add the named sanctioned-landing constant seeded with `99f9cd84e` and `fda4548ac`, and the `_record_anchor_revision` helper: for each directive record, the anchor is the newest commit among the record's introducing commit and the sanctioned landings whose committed blob changed that record. [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-anchor the committed-revision acceptance arm to the record anchors: given a committed record byte-state equal to the record's anchor, expects the suite green; given any other committed state, expects red naming the rewritten record id. Run the cycle: before the re-anchor lands, expects the synthesized unsanctioned state green under today's HEAD-acceptance (RED proves the class was open); after, expects red (GREEN proves the fence). [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the durable fixture test: in a temp-repo fixture (the `_make_fixture_repo` precedent in `scripts/check_cleanup_scope_baseline.py`, git env scrubbed of `GIT_DIR`-class variables and global/system config pointed at `os.devnull`), commit a directives file with two records (introducing commit), commit a sanctioned rewrite of one record recorded in a test-local sanctioned set, then commit a second unsanctioned rewrite of the same record. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extract the anchor resolution and the acceptance decision into the pure helper both the real witness and the fixture drive, and assert the sanctioned state passes, the unsanctioned state is rejected with the record id named, and the anchor resolves to the sanctioned commit rather than the newest commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Confirm the re-anchored suite is green against the live tree (every record's tree state equals its anchor) before committing. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `test: quota-wall witness anchors committed record acceptance at named sanctioned landings` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Regression pin and record-range corrections

Files: `scripts/test_quota_wall_doctrine.py`, `docs/history/backlog/2026-10-30-quota-doctrine-committed-rewrite-narrowing.md`, `docs/history/backlog/2026-10-30-inventory-count-reconciliation.md`

Primary class anchors:
- `test_witness_every_preexisting_record_is_textually_unchanged_against_baseline` in `scripts/test_quota_wall_doctrine.py`, owns the red the pin asserts

- [ ] Exercise the regression pin as a transient commit cycle: apply a one-word edit to D-7 in the directives file, commit it, run the witness, and assert it goes red naming D-7 (the only step that discriminates the old HEAD-acceptance from the new anchors). [class: IMPLEMENTATION_REQUIRED]
- [ ] Drop the pin commit with `git reset --hard HEAD~1` and confirm a clean tree (`git status --porcelain -- docs/maintenance/operator-directives.md` prints nothing) and a green suite; if the task is interrupted before the reset, re-derive from disk and drop any stray pin commit before proceeding. No mutation bytes land. [class: IMPLEMENTATION_REQUIRED]
- [ ] Correct the record-range text to the derived-from-headings universe (D-1..D-17 at authoring time) in this plan's origin row (Skill-step, Problem, and the Cluster line's own stale range mention) and in the sibling count row's concern-1 sentence, per the two rows' Cluster lines; the origin row stays open re-scoped to the preamble acceptance residual. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `test: correct record ranges to the heading-derived universe; re-scope the origin row to the preamble residual` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- None: the witness test's docstrings carry the model; no skill text references the revision model.
