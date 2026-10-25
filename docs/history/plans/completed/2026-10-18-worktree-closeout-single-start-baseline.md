# Plan: one run-start baseline for worktree closeout

Backlog origins:
- docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md
- docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md
Driving force: reliability
Authoring claim: docs/tmp/authoring-claims/2026-10-08-worktree-closeout-baseline-fallback.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-worktree-closeout-single-start-baseline-pb65298a4-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.5h
Classification: [class: fix-class] reliability; authoring only

## Terms

- **Run-start baseline**: the path and SHA-256 inventory captured before a run creates artifacts that must transfer at closeout.
- **Skip record**: the baseline sibling JSON that records capture failure or an unavailable pre-work baseline and selects scoped copy. A single-plan path is `{tmp_dir}/execute-plan/<PLAN_SLUG>/closeout-baseline-skip.json`; a zero- or multi-plan run uses `{tmp_dir}/done-session/worktree-migrate-baseline-${RUN_ID}-skip.json`, beside the legacy run-ID baseline path.
- **Scoped copy**: the enumerated copy of run-created or changed gitignored artifacts, verified by digest and recorded in the session manifest.
- **Migration manifest**: the record emitted by `worktree_closeout_migrate.py` for transferred, renamed, skipped, and failed paths.
- **Single-plan run**: a run whose existing manifest names exactly one `owned_plan_paths` entry; its plan slug selects the standard Phase 0 closeout-baseline path.
- **Run-scoped inventory**: the manually enumerated inventory in the existing scoped-copy procedure. `owned_plan_paths` select plan identity and the `{tmp_dir}/execute-plan/<PLAN_SLUG>` session, `{tmp_dir}/authoring/<plan-slug>/context.jsonl` authoring telemetry, and metrics archive; plan files themselves are never transfer candidates. The plan-deliverables record contributes only entries exactly matching current `owned_plan_paths`; that record is a control input. Transfer candidates are the current run’s execute-plan session files, its authoring telemetry, its per-plan metrics archive or telemetry-absence record, the plan-owned review-certification seal under `{review_certs_dir}`, explicitly owned review Markdown and required sidecars, complete review pairs whose `extensions.plan_identity` matches an owned plan path, and `done-session` files whose names contain the exact `RUN_ID`. Use `git status --ignored --porcelain` only to discover run-written artifacts inside configured migration roots; exclude the skip record and any temporary inventory notes. The existing manual scoped-copy procedure remains responsible for accounting for every run-created or changed artifact, verifying each digest, and recording the full list before removal.
- **Primary checkout**: the repository checkout that receives verified artifacts from a run worktree.

## Why

The migration helper skips files whose current digest matches its baseline. Capturing another baseline immediately before transfer can classify all earlier run artifacts as pre-existing. Closeout must reuse a unique pre-work baseline or use the existing scoped-copy fallback when no unique baseline exists.

## Gist & Examples

TLDR: reuse one run-start digest baseline for recovery and transfer to protect worktree closeout reliability.

Before: a run creates review records, then `done_run.sh commit` captures a baseline immediately before migration. The migration sees the new records in its baseline and skips them.

After: a single-plan worktree bootstrap captures its baseline before run artifacts are written, and continuity recovery and done migration consume that same file. An ordinary or multi-plan run records the existing skip state and uses the existing manual scoped-copy procedure for its complete run-owned artifact inventory.

Missing capture: a recorded skip follows the existing scoped-copy path. When neither a baseline nor a valid skip record exists, the current fail-closed refusal remains. Unchanged files stay excluded, and collision, digest verification, ownership, and removal checks remain in force.

## Outcome

When a run has exactly one owned plan, worktree recovery and done closeout use the same baseline captured before transferable artifacts are written. A run with no owned plan or multiple owned plans records the skip state and uses the existing manual scoped-copy procedure instead of taking a late snapshot or choosing one plan arbitrarily.

- The 2026-10-13 recovery case no longer re-captures and freezes its surviving implement log.
- The 2026-10-18 plan-owned done closeout transfers review artifacts created after its Phase 0 baseline and before `done_run.sh commit` began.
- A missing baseline never becomes an implicit empty inventory or a broad copy.

Gate delta: no new blocking gate, validator, lock, refusal class, manifest field, pause, or required ceremony; remove the late capture in `done_run.sh commit` and the mid-run re-capture repair arm. Route unique pre-work baselines through existing digest verification. When a recorded skip governs, retain the already documented manual scoped-copy procedure; do not add an executable inventory validator or a new refusal condition. The manual procedure accounts for every run artifact, verifies each source and destination digest, records the full list, and completes before removal. This scope addresses the [2026-10-18 artifact-loss witness](docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md); review this fallback on 2027-04-18. Keep the missing-record refusal and blocking review duties unchanged.

## Design Invariants

- When capture succeeds, one baseline is captured before any artifact that needs transfer is created or modified.
- Exactly one `owned_plan_paths` entry selects its canonical pre-work baseline. Zero or multiple entries select the run-ID-keyed skip record and explicit scoped-copy route; no consumer chooses an arbitrary plan baseline. Plan bootstrap, continuity recovery, and done migration never create competing baselines.
- A continuity repair never re-captures a baseline over surviving artifacts. When capture was skipped, it records the sanctioned skip record and uses the existing manual scoped-copy procedure.
- Modified operative skill text replaces or narrows the current capture instructions; it does not add net wording for the same duty.
- For baseline transfers, the migration helper's digest comparison, destination verification, collision handling, and manifest format stay unchanged. The skip-record arm uses the existing manual scoped-copy procedure.
- Migration and primary-home verification stay before docs-branch sync and worktree removal.
- No copy root expands. No baseline is inferred from an empty directory or a missing file.

## Tasks

### Task 1: Reuse a unique baseline and retain the documented manual fallback

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Context: the runner currently invokes `capture` immediately before `migrate` in its docs-sync stage. The migration helper's digest match skips an unchanged file; it does not know whether that file was created earlier in the same run. The existing scoped-copy procedure is documented for execute-plan; this plan reuses that manual fallback for the done-run skip case rather than creating a second transfer owner.

- [x] For exactly one `owned_plan_paths` entry, resolve and reuse its canonical Phase 0 baseline. The capture command includes configured `review_certs_dir` alongside `{reviews_dir}`, `{tmp_dir}`, and `{metrics_dir}`. For zero or multiple entries, write/use the run-ID-keyed sibling skip record; never choose one plan baseline arbitrarily or add a manifest field [class: IMPLEMENTATION_REQUIRED]
- [x] Remove commit-time capture. Before `done_run.sh commit`, complete the existing manual scoped copy and record its complete artifact list in the session manifest. The wrapper must recognize a valid skip record, bypass baseline-based `migrate`, and continue to docs sync; when neither baseline nor valid skip record exists, preserve the existing migration refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Use `owned_plan_paths` only as identity selectors; never copy tracked plan files. For the manual scoped-copy inventory, filter plan-deliverables entries by exact membership in current `owned_plan_paths`; exclude the shared record itself [class: IMPLEMENTATION_REQUIRED]
- [x] Manually enumerate explicitly owned review Markdown and required sidecars, complete review pairs whose `extensions.plan_identity` matches an owned plan path, exact-`RUN_ID` `done-session` files, and each owned plan’s execute-plan session directory, authoring telemetry file, plan-owned review-certification seal under `review_certs_dir`, and metrics archive or telemetry-absence record [class: IMPLEMENTATION_REQUIRED]
- [x] Use the ignored-path listing only to discover run-written artifacts under configured migration roots, never as a blanket copy instruction. Exclude foreign reviews, prior-run deliverables, tracked plan files, unrelated artifacts, and the skip record [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the manual inventory complete: enumerate every listed source class, including both a metrics archive and its telemetry-absence record as applicable. Record the source and destination digest for each artifact; if a source is missing or any digest differs, leave the transfer incomplete and keep the source worktree for recovery under the existing transfer-before-removal procedure [class: IMPLEMENTATION_REQUIRED]
- [x] Route baseline transfers through the existing migration owner before docs sync. If neither valid baseline nor valid skip evidence exists, keep the existing refusal. When a skip record governs, complete the existing manual inventory and digest-verified scoped copy before invoking the wrapper; the wrapper skips baseline migration for that arm, then the existing transfer-before-removal procedure remains authoritative [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: test baseline reuse after a new artifact is created [class: REPOSITORY_TEST]
- [x] Run → expect RED: test baseline migration and capture-root coverage for reviews, tmp, metrics, and review certs; retain the documented manual inventory for the skip arm [class: REPOSITORY_TEST]
- [x] Verify the manual scoped-copy instructions enumerate every candidate class, exclude tracked plans, stale deliverables, foreign reviews, unrelated artifacts, and control inputs, and require source/destination digest equality before closeout [class: REPOSITORY_TEST]
- [x] Test zero-plan and multiple-plan runs separately, plus a single-plan capture failure; verify the valid-skip wrapper branch bypasses `migrate` after the fixture’s manual copy record exists, reaches docs sync, and never takes a late baseline [class: REPOSITORY_TEST]
- [x] Test missing skip evidence through the existing refusal. Test that an incomplete inventory or digest mismatch leaves transfer incomplete and the source worktree available; retain the existing removal path and refusal behavior [class: REPOSITORY_TEST]
- [x] Keep baseline migration entries in the unchanged manifest at `verified: true`; require the manual scoped-copy record to list every copied source and destination with matching independently re-read digests [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 -m unittest scripts.test_done_run_wrapper scripts.test_worktree_closeout_migrate -q` [class: REPOSITORY_TEST]
- [x] Commit: `done: reuse the run-start baseline for worktree migration` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Align bootstrap, continuity recovery, and done instructions

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `scripts/test_execute_plan_worktree_bootstrap.py`

Context: plan authoring and execute-plan already identify a plan slug and document an early baseline. The continuity repair arm can re-capture after artifacts survive, and the done skill describes a separate transfer consumer.

- [x] Keep plan-authoring and execute-plan capture at Phase 0, before run artifacts; pass the existing target plan path to done setup so a single owned-plan identity resolves that same baseline. Record zero/multiple-plan runs as skip cases without a new manifest field [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the continuity-repair re-capture arm. A surviving baseline remains unchanged; when baseline capture failed, retain the existing skip-record and manual scoped-copy behavior. If both records are absent, retain the existing stop [class: IMPLEMENTATION_REQUIRED]
- [x] Update done closeout instructions to invoke the existing manual scoped-copy procedure when a valid skip record governs, verify every source and destination digest match, and record the complete artifact list in the session manifest without changing migration-manifest fields, and preserve migration before docs sync and removal [class: IMPLEMENTATION_REQUIRED]
- [x] Add bootstrap regression coverage proving that a failed continuity check cannot replace a baseline that predates a surviving run artifact [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 -m unittest scripts.test_execute_plan_worktree_bootstrap scripts.test_done_run_wrapper scripts.test_worktree_closeout_migrate -q` [class: REPOSITORY_TEST]
- [x] Commit: `skills: share the immutable worktree closeout baseline` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```bash
python3 -m unittest scripts.test_done_run_wrapper scripts.test_worktree_closeout_migrate scripts.test_execute_plan_worktree_bootstrap -q
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Assumptions

- Exactly one `owned_plan_paths` entry resolves the plan baseline; zero or multiple entries resolve the run-ID-keyed skip record. Existing manifest identity supports both paths without a new field.
- Plan authoring and execute-plan callers can pass their existing target plan path to done setup before any plan-file write; basis: Phase 0 already fixes that path before setup completes.
- When capture fails, the existing skip-record and scoped-copy contract remains the recovery route; basis: `agents/skills/execute-plan/SKILL.md`, Transfer-out-and-deletion implementation.

Decision points requiring a grill: none remain.

## Residual findings (cap closure)

- [folded] `implementation#skip-fallback-runner-wiring`: for a valid skip record, perform and record the complete manual scoped copy before invoking `done_run.sh commit`; bypass baseline migration only for that arm, and retain the existing refusal when neither valid baseline nor valid skip record exists.
- [folded] `testing#missing-test`: name every manual inventory source class in the acceptance checks and require a mismatch or missing source to leave transfer incomplete with the source worktree available.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the baseline predates transferable artifacts, and every consumer resolves the same run's baseline.
- safety: missing capture remains explicit; no broad copy, implicit empty baseline, or worktree removal over an unverified transfer.
- compatibility: primary-checkout no-op behavior and existing migration digest, collision, manifest, and removal checks remain unchanged.

**Done when:** the continuity-recapture witness, late-done-capture witness, baseline-reuse case, scoped-copy case, ambiguous-plan case, and missing-state refusal have regression evidence; every path transfers and verifies its run-owned artifacts at the primary home before sync/removal.

**Ship when:** the updated runner, workflow contracts, regression coverage, and both backlog dispositions land together.

## Review Scope

The cleanup scope ledger extends Review Scope because the required path inventory does not record which existing capture and recovery arms are removed or retained.

- Base ref: the execution worktree's recorded start commit.
- Task-owned files: the paths listed under Tasks and the source/test paths below.
- Remove: the `done_run.sh commit` capture immediately before migration and the continuity-repair re-capture arm; basis: both backlog origins document the baseline-freeze witnesses.
- Keep: `worktree_closeout_migrate.py` digest matching, destination verification, collision handling, migration manifest, and the missing-state refusal for baseline transfers; the skip-record arm continues to use the already documented manual scoped-copy procedure; basis: the two backlog origins and `docs/history/plans/completed/2026-10-01-worktree-closeout-artifact-migration-and-residue.md`.
- Keep: the manual skip-record scoped-copy recovery and the transfer-before-sync/removal order; basis: `agents/skills/execute-plan/SKILL.md`, Transfer-out-and-deletion implementation.
- Defer: a broad artifact copy, a second migration owner, executable inventory validation, a gate, or a new ledger; basis: the already documented manual scoped-copy procedure owns the skip path and the existing migration helper owns baseline transfers.
- Pre-existing dirt and untracked paths: classify from the execution worktree's recorded start state; do not adopt unrelated paths.

**Explicit must-fix:** findings on these paths are in scope.

**Production code:**
- `scripts/done_run.sh`
- `scripts/worktree_closeout_migrate.py`

**Tests:**
- `scripts/test_done_run_wrapper.py`
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/test_execute_plan_worktree_bootstrap.py`

**Documentation:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md`
- `docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md`
- `docs/history/backlog/PLAN-PROMPTS.md` (landing prune rider, this entry only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it implements a task, fixes a regression caused by plan work, closes wiring or documentation implied by a must-fix change, or contradicts a contract this plan changes. If the link to the plan is weak or speculative, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- A broad recursive artifact copy or new transfer root; reason: it can copy unrelated work and the existing configured roots are the intended boundary.
- An executable inventory validator, gate, lock, or ledger; reason: the existing manual scoped-copy procedure already covers the skip path, while the existing migration helper handles baseline transfers.
- Changes to the migration helper's digest and collision algorithm; reason: the witnessed failure is baseline timing, while those checks already define safe transfer.

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md: covered by this plan's execution (late commit-time capture removed; the canonical Phase 0 baseline is the single owned plan's only reusable baseline; the run-ID skip record's producer lives in done_run.sh setup with the commit-stage bypass; landed as the run squash on main 2026-10-25).
- docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md: covered by this plan's execution (the continuity-repair re-capture arm removed; a surviving baseline is never replaced across a repair; the skip-record and manual scoped-copy route retained; landed as the run squash on main 2026-10-25).
- Residuals of the landed work are tracked in docs/history/backlog/2026-10-25-closeout-skip-record-producer-residuals.md (r2 review backfill).
