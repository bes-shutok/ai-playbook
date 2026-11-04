# Plan: Reclassify-then-restore and report-coverage fixes for the closeout clobber guard

Backlog origins (scope of record):
- docs/history/backlog/2026-11-02-closeout-migrate-deletion-arm-recheck-parity.md
- docs/history/backlog/2026-11-02-closeout-migrate-owned-vintage-restore-signature.md
- docs/history/backlog/2026-11-02-closeout-migrate-foreign-staged-report-coverage.md
- docs/history/backlog/2026-11-02-closeout-migrate-prevented-clobber-teardown-consumer.md

Driving force: code-quality

Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-closeout-migrate-clobber-guard-restore-arms-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 2h total, largest task 1h

Authoring claim: closeout-migrate-clobber-guard-restore-arms.md (session sess_52a58c31-0dfc-4bf2-94ff-494ab78223af)

## Terms

- clobber guard: `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py` (introduced 32ae9c25c), the post-run staged-set ownership check that restores between-snapshot rewinds and reports foreign staged work.
- owned path: a repo-relative path this run carried into the target whose destination appears in the guard's ownership set - the `migrated` and `replaced` manifest destinations under the target root (`scripts/worktree_closeout_migrate.py`, the `owned_rels` comprehension in `cmd_migrate`). Collision-`renamed` destinations are NOT owned today; this plan deliberately does not widen the set - a staged rewind at a renamed destination stays foreign work, reported not restored, so collision-renamed carries keep their current report-only treatment.
- unmerged entry: an index entry in merge-conflict state (stages 1-3 present); detected by `git ls-files -u -- <rel>` returning output, per lesson 370's index-membership oracle rule - `git rev-parse :<rel>` alone cannot discriminate (it exits 128 for both unmerged and index-absent shapes).
- index-absent entry: a staged path with no index entry (the staged-deletion shape); `git rev-parse :<rel>` exits 128 with no `git ls-files -u` output.
- delivered blob: the git blob sha (via `git hash-object`) of the bytes this run actually delivered for a carried rel, held in memory for the guard pass and recorded additively on the run's own manifest rows.
- reclassify-then-restore helper: the shared compare-then-act sequence both restore arms run: re-read the staged entry immediately before the restore decision, act only when the re-read matches the classification read, and verify the restore outcome after it (a failed restore is detected; the window between recheck and restore is bounded, not closed).

## Why

The closeout clobber guard has one silent-wrong-action defect and three contract holes: a merge conflict on an owned path mid-closeout is classified as a staged deletion and the guard's restore resolves the operator's merge to HEAD in index and worktree while presenting it as a routine rewind repair (live-probe verified); the owned-vintage restore cannot distinguish an incident rewind from the run's own delivered bytes and restores both; two staged shapes skip or fall past the foreign-work report with no output while the guard's doc surfaces over-claim coverage; and the prevented_clobbers manifest evidence cannot reach the teardown decision it exists to inform.

## Gist & Examples

TLDR: the guard's restore arms gain a shared reclassify-then-restore helper with index-membership discrimination, the owned signature is tightened to the delivered blob, the walked shapes that produced no output emit, and a non-empty prevented_clobbers manifest surfaces at teardown, closing the silent merge-resolution and report-hole classes, for code-quality.

Before: an owned path sitting at index stages 1-3 (mid-merge) is classified as a staged deletion and restored from HEAD, resolving the operator's merge under a misleading rewind-repair line; a staged historical vintage equal to the bytes the run delivered is restored from HEAD, destroying the run's own output; a staged new file absent at HEAD and an owned path staged with brand-new bytes both skip the report silently; a non-empty prevented_clobbers manifest changes nothing at teardown.

After: unmerged entries route to the report-only path with zero restore spawns while index-absent entries keep the owned deletion restore arm; both restore arms run the reclassify-then-restore helper (classification re-read immediately before the restore, still-absent-means-unchanged on the deletion arm, post-restore outcome verification); the owned-vintage restore fires only when the staged blob differs from the in-memory delivered blob for that rel; the previously silent walked shapes emit a prevented-clobber-check line naming the shape; gate-removal reports a non-empty prevented_clobbers section naming the restored paths, report-only, the operator deciding.

Edge cases: a peer restaging a path between the classification read and the restore downgrade to report-only (the existing recheck's semantics, generalized); the residual window between recheck and restore stays a bounded silent-drop window (priced in Assumptions); a rel with no in-memory delivered blob (a defensive absence rule, never a manifest read) keeps the current vintage-only signature; a prior run's prevented rows report as foreign at teardown, never attributed to the adjudicated run.

## Outcome

The guard never resolves a live merge and never destroys the run's own delivered bytes, every conflict, vintage, and new-bytes shape the guard walks produces either a restore line or a report line, and a between-snapshot rewind caught in-run is visible at the teardown decision.

- Unmerged index entries route to the report-only path; the unmerged-entry restore misclassification is dead.
- The deletion and vintage restore arms share one reclassify-then-restore helper with post-restore verification.
- The owned-vintage signature compares the staged blob against the in-memory delivered blob.
- The previously silent walked shapes emit, and the three doc surfaces' claims match the emitted lines; gate-removal reports a non-empty prevented_clobbers section, warning-first.

Gate delta: narrows one restore arm (the owned-deletion arm no longer fires for unmerged entries - a destructive-restore class removal, the report-only path absorbing the shape); adds three report emission lines in the guard walk and one report-only summary line at gate-removal; adds one additive per-row manifest field (`delivered_blob` on the run's own migrated/replaced rows) priced by the owned-vintage incident row's witnessed silent-restore defect; no new gate, ledger, validator, or refusal surface; the teardown line lands warning-first with its promotion to a hold requiring a true catch plus a pre-registered registry-removal row.

## Assumptions

- The guard's protective value justifies repair rather than removal; the continuity disposition in the serving entry records the demonstrated independent protective value (a between-snapshot rewind caught in-run) and no arm removes the guard.
- The delivered blob is held in memory for the guard pass (computed during the carry loop, before the manifest append) and recorded additively on the run's own manifest rows for post-run auditability; the guard's decision never reads the manifest, so a legacy-manifest fallback is a defensive in-memory absence rule (no delivered blob known for a rel reverts that rel to the current vintage-only signature).
- The teardown arm stays report-only per the Machinery admission protocol; no witnessed incident justifies a blocking teardown hold.
- The r3 record's interception recipe (`.ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md`, finding F6) is the pin recipe of record for the downgrade kill.
- Residual-window disposition: the reclassify-then-restore helper's recheck narrows the race but does not close it - the window between the recheck read and the restore subprocess stays a subprocess-latency-width silent-drop window (a peer restage inside it is overwritten by the restore and the post-restore verification then finds HEAD's blob, a clean pass), accepted because detection at that width requires holding the index lock across the span, whose hold width prices worse against the parallel-restage traffic the closeout index shares (the serving entry's own pricing of the alternative); there is no later automatic detection (the guard runs once post-run; gate-removal reads manifest rows, never re-walks the index) - only the operator's own subsequent git inspection would surface a restage lost this way.
- Deliberate-reversal residual: the delivered-blob signature still restores a deliberate operator revert staged at a committed historical vintage (both shapes present as an older vintage differing from the delivered blob); what the signature removes is the destruction of the run's own delivered bytes staged after delivery. The residual is recorded, not fixed, in this plan; r2 F6's opposite direction (restore only on delivered match) is explicitly rejected because it leaves the standard rewind staged, gutting the guard's witnessed protective value.

Decision points requiring a grill: delivered-blob owned signature deviates from r2 F6's recorded remedy direction and leaves the deliberate-reversal residual standing - taken deliberately, decision source this plan's Assumptions bullet pricing r2's direction as not viable, 2026-11-02, affected section Task 2; post-restore re-read chosen over the index-lock residual-window closure, the window accepted as bounded silent-drop - source the serving entry's arm pricing against parallel-restage traffic, 2026-11-02, affected section Task 1.

## Standing constraints

- Script changes stay in `scripts/worktree_closeout_migrate.py` and its test file; no other guard-bearing path is touched.
- New pins land in the guard's existing test suite; the suite stays the run's regression surface (see Validation Commands).

## Evaluation Criteria

**Quality dimensions:**

- Correctness: a merge-conflict fixture routes to the report-only path with zero restore spawns; the interception mutant (a restage between classification and restore) dies at the pin.
- Contract fidelity: every conflict, vintage, and new-bytes shape the guard walks emits; no walked shape in those classes produces zero output.
- Compatibility: a rel absent from the in-memory delivered-blob map keeps the current behavior; existing pins stay green.

**Done when:**

- The four origin rows' scope arms are implemented and pinned; the acceptance fixtures (merge-conflict routing, interception mutant, both silent branches, teardown summary with a prevented entry, delivered-equal leave-untouched) pass.
- The three doc surfaces' claims match the emitted lines, verified by reading each surface against the line it documents.
- `python3 scripts/plan_readiness.py <plan>` exits 0 over the final review series.

**Ship when:**

- The landed guard runs green in a real closeout migrate pass with the new lines exercised (operations follow-up, owner: the next closeout run that walks a non-empty staged set).

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md
```

## Design Invariants

- The guard's foreign-staged-work enumeration byte contract: staged entries this run did not carry are reported, never touched; no arm changes the enumeration.
- The restore arms restore from HEAD only for owned paths; the foreign path stays read-only.
- The prevented_clobbers manifest section shape is unchanged; the delivered blob is an additive per-row field on migrated/replaced rows.

## Review Scope

**Explicit must-fix:**

- `scripts/worktree_closeout_migrate.py` (Task 1): the guard walk's index-membership routing and the reclassify-then-restore helper.
- `scripts/test_worktree_closeout_migrate.py` (Task 1): the unmerged-routing pin, the interception pin, the deletion-arm retention fixtures.
- `scripts/worktree_closeout_migrate.py` (Task 2): the delivered-blob capture in the carry loop and the tightened owned-vintage signature.
- `scripts/test_worktree_closeout_migrate.py` (Task 2): the staged-equals-delivered fixture and the absence-rule fallback tests.
- `scripts/worktree_closeout_migrate.py` (Task 3): the walked-shape emission lines and the three doc surfaces.
- `scripts/test_worktree_closeout_migrate.py` (Task 3): the silent-branch and equals-HEAD emission pins.
- `scripts/worktree_closeout_migrate.py` (Task 4): the gate-removal prevented-clobbers summary line.
- `scripts/test_worktree_closeout_migrate.py` (Task 4): the teardown pin with a prevented-entry manifest.

**Production code:** the guard walk and restore arms, the carry loop's delivered-blob capture, the manifest row fields, and gate-removal's summary line.

**Tests:** the guard suite's new fixtures and pins.

## Tasks

### Task 1: Index-membership routing and the shared reclassify-then-restore helper

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py`

- [x] `_prevent_tracked_clobbers` delivers unmerged-entry routing: given an owned path at index stages 1-3 (mid-merge), expects the report-only foreign-path line naming the unmerged state and zero restore spawns; given an index-absent owned path (staged deletion), expects the deletion restore arm still to run (discrimination via `git ls-files -u`, per lesson 370's index-membership oracle rule) [class: IMPLEMENTATION_REQUIRED]
- [x] Both restore arms deliver reclassify-then-restore: given a peer restage between the classification read and the restore decision, expects report-only with the peer's bytes intact; given a restore subprocess failure or a post-restore re-read mismatch, expects a report line and no re-restore [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given any foreign staged shape (not in the ownership set), expects zero mutations of that entry [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the unmerged-routing pin and the interception pin (the r3 F6 subprocess-run interception restaging recipe) fail against the current guard [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: discriminate unmerged entries and share the reclassify-then-restore sequence in the clobber guard` [class: IMPLEMENTATION_REQUIRED]

Evidence: new pins red before the fix, green after; full guard suite passes.

### Task 2: Delivered-blob owned signature

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py`
- `cmd_migrate` in `scripts/worktree_closeout_migrate.py`

- [x] `cmd_migrate` delivers delivered-blob capture: given a run carrying migrated/replaced paths, expects an in-memory rel-to-delivered-blob map (blob shas via `git hash-object`, computed during the carry loop, before the manifest append) passed into the guard pass and recorded additively as `delivered_blob` on the run's own migrated/replaced manifest rows [class: IMPLEMENTATION_REQUIRED]
- [x] `_prevent_tracked_clobbers` delivers the tightened owned-vintage signature: given an owned path staged at a historical vintage whose blob differs from the rel's in-memory delivered blob, expects the rewind restore; given a staged blob equal to the delivered blob, expects leave-untouched with a report line; given no in-memory delivered blob for the rel (defensive absence rule, never a manifest read), expects the current vintage-only signature [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the new staged-equals-delivered fixture (rewound HEAD plus re-staged delivered bytes, authored new - no existing fixture holds this shape) fails against the current guard [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: restore owned rewound vintages only off the run's delivered blobs` [class: IMPLEMENTATION_REQUIRED]

Evidence: the new fixture documents the semantic decision (naming the origin row's pricing and the r2-direction deviation recorded in Assumptions); suite passes.

### Task 3: Report-coverage emission and doc-surface alignment

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_prevent_tracked_clobbers` in `scripts/worktree_closeout_migrate.py`

- [x] `_prevent_tracked_clobbers` delivers full walked-shape emission: given a staged new file absent at HEAD (the `head_blob is None` skip), expects a prevented-clobber-check line naming staged-new-at-target; given an owned path staged with brand-new bytes (the fall-past branch), expects the line naming staged-new-bytes-on-a-carried-path; given a staged blob equal to HEAD (including mode-only changes), expects a line naming the no-op restage [class: IMPLEMENTATION_REQUIRED]
- [x] The three doc surfaces match the emitted lines: the `_prevent_tracked_clobbers` docstring ("reported, never touched" span), the module header paragraph describing the post-run guard, and the `migrate` subcommand help - the help currently carries no claim, so the alignment there is an add of the claim text, stated as such [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the two silent-branch pins and the equals-HEAD emission pin fail against the current guard [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: emit report lines for every walked clobber-guard shape and align the doc claims` [class: IMPLEMENTATION_REQUIRED]

Evidence: no conflict, vintage, or new-bytes shape produces zero output; pins green; each doc surface read against the line it documents (docstring ↔ the walk's report lines; module header ↔ the guard's contract; migrate help ↔ the guard's foreign-work reporting).

### Task 4: Teardown summary line and full-gate verification

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`

- [x] `cmd_gate_removal` delivers the prevented-clobbers summary: given a manifest whose adjudicated run's rows include non-empty prevented_clobbers, expects a report-only summary line naming the restored paths and the operator-decide note, no hold [class: IMPLEMENTATION_REQUIRED]
- [x] Prior-run prevented rows stay foreign: given prevented rows from prior runs' manifest rows, expects them reported as foreign, never attributed to the adjudicated run (deliberate in-plan addition matching the existing unattributable-rows report-only demotion shape, priced here because silent attribution of another run's prevented rows would misstate the adjudicated run's teardown evidence) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the teardown pin (a manifest carrying a prevented entry) fails against the current gate-removal [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: surface prevented clobbers at the gate-removal teardown decision` [class: IMPLEMENTATION_REQUIRED]
- [x] Full readiness gate over the final assembled series exits 0 [class: REPOSITORY_TEST]

Evidence: pin green; `python3 scripts/plan_readiness.py <plan>` exit 0 over the final series.

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-02-closeout-migrate-deletion-arm-recheck-parity.md: covered by this plan (Task 1; unmerged-entry routing via the ls-files -u discriminator, deletion arm retained for index-absent entries), origin row deleted in the execution landing.
- docs/history/backlog/2026-11-02-closeout-migrate-owned-vintage-restore-signature.md: covered by this plan (Task 2; delivered-blob signature, delivered-equal staged bytes left untouched with a report line), origin row deleted in the execution landing.
- docs/history/backlog/2026-11-02-closeout-migrate-foreign-staged-report-coverage.md: covered by this plan (Task 3; every walked shape emits, doc surfaces aligned), origin row deleted in the execution landing.
- docs/history/backlog/2026-11-02-closeout-migrate-prevented-clobber-teardown-consumer.md: covered by this plan (Task 4; gate-removal prevented-clobbers report-only summary with prior-run-foreign attribution), origin row deleted in the execution landing.
- Execution residuals captured as docs/history/backlog/2026-11-04-clobber-guard-phase3-review-residuals.md, docs/history/backlog/2026-11-04-gate-removal-prevented-attribution-pin-residuals.md, and docs/history/backlog/2026-11-04-clobber-guard-report-line-wording-residuals.md (all reviewed, non-blocking).
