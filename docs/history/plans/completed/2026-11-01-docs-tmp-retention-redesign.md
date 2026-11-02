# Plan: Settle the docs/tmp retention policy - never-synced scratch age bound, dead-root marker drain, and the proof-family terminal-state bound

Backlog origins (scope of record):
- docs/history/backlog/2026-10-30-docs-tmp-sweep-sync-precondition-catch-22.md
- docs/history/backlog/2026-10-30-done-session-cross-repo-marker-immortality.md
- docs/history/backlog/2026-10-30-execute-plan-proof-family-retention-unbounded.md

(Three-row promotion: one plan covering the survey's three policy rows deliberately; each row's decision is a separate task.)

Driving force: simplicity

Execution budget: 2h total, largest task 1h

Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-docs-tmp-retention-redesign-p2c21a780-r*.md

Authoring claim: docs/tmp/authoring-claims/docs-tmp-retention-redesign.md (session zcode-automation-fd0142f8-20261101T1049)

## Terms

- **Never-synced scratch**: a regular file at the `docs/tmp/` top level whose docs-branch sync state reads `never-synced` (the docs branch holds zero `docs/tmp/` paths by the archive-root exclusion, so every top-level file is never-synced). The never-synced arm covers every top-level regular file regardless of extension; the existing synced arm's shape classes are unchanged.
- **Deletion horizon**: the named constant (default 30 days) a scratch file's mtime and birth time must both exceed, beside the session-window check, before the file is deletable.
- **Session window**: the window `derive_session_window` anchors from content-confirmed run-start markers; an unanchorable window keeps everything (never guessing).
- **Cross-repo marker**: a run-start marker whose recorded checkout root does not confirm as this primary checkout, recorded as a 64-hex digest (current writers) or a raw path (legacy pre-digest writers, matched by realpath).
- **Dead-root marker**: a cross-repo marker whose recorded root matches no existing candidate checkout root and whose epoch precedes the window anchor.
- **Candidate checkout root set**: one per-pass snapshot of the primary checkout root, every registered `git worktree list` entry, and the repository's sibling worktree-root families, enumerated once and consumed by all three arms.
- **Proof family**: `closeout-baseline.json`, `closeout-baseline-skip.json`, `closeout-migration.json` (and their `.wt-*` siblings) inside an execute-plan session directory.
- **Terminal session**: an execute-plan session directory whose readable `runtime_state.json` carries `terminal_receipt` or reads `workflow_state` complete (the closeout predicate `gate_execute_plan_closeout` writes), or a receipt-less legacy session whose `closeout-migration.json` records a branch ref that no longer resolves and whose manifest-recorded source worktree is unregistered or the primary checkout (the long-landed class the witnessed residue is made of).
- **Citation hold**: the `_closeout_reference_hold` merge-lock span; `referenced` is the set of bytes a retained manifest cites, and `referenced: None` means the hold could not be verified, where every arm prunes nothing.
- **Protected scratch classes**: the review-loop telemetry (`review-loop` prefix), the `code-review` and `handoff` scratch directories, and execute-plan sessions whose plan is still pending - the classes outside every drain arm.
- **Drain posture**: the facts-document knob (`docs_tmp_drain_arms`: `report-only` default, `on`, or `off`) gating whether the three arms unlink or only report; the horizon knob `docs_tmp_deletion_horizon_days` falls back to the module constant when absent.

## Why

Every mechanism that should drain `docs/tmp/` is inert at HEAD, the accumulation is measured and unbounded, and no live-at-HEAD wrong result is witnessed. The detail lives in Gist Before.

## Gist & Examples

TLDR: Give the docs/tmp sweep three bounded, attributable drain arms - a never-synced scratch age bound, a dead-root marker drain, and a proof-family terminal-state bound - inside the existing `gate_docs_tmp_sweep` policy behind a report-only default posture, so accumulation stops growing while every keep-side protection stays intact and the arms promote only after a witnessed census cycle.

Before (today): the only general deletion arm can never fire over `docs/tmp` (never synced, by design); 305 run-start markers accumulate with 273+ permanently unprunable cross-repo records and the window riding two confirmed anchors; proof families retain unconditionally (186M measured, about 60M for one long-landed plan), and every sweep pass re-reports the same kept rows.

After (this plan): a top-level never-synced file older than the deletion horizon in both mtime and birth time, outside the session window, and uncited drains with the attributable reason `expired never-synced scratch`; a cross-repo marker whose root matches no existing candidate root and whose epoch precedes the window anchor drains as `dead-root marker`; an execute-plan session whose receipt reads terminal or whose legacy migration manifest names a gone branch and a gone source worktree, and whose bytes no live closeout cites, drains the session directory (proof family and local manifests); every arm defaults to report-only until a census cycle witnesses zero mispriced would-drain rows, and every deletion names its arm.

Edge cases: bytes a retained manifest cites stay kept - the check and the unlink share one citation-hold span per pass, and an unverifiable hold prunes nothing (the opposite-direction guard from the completed plan `docs/history/plans/completed/2026-10-29-done-gate-report-retention.md`); a live worktree run's marker keeps the fence; a second clone's stale marker outside the candidate root set can drain as dead-root (the priced false-positive, bounded by the window-age guard); a legacy raw-path marker drains by realpath or stays kept - neither class is lost silently; a fresh arrival carrying a preserved old mtime keeps (birth-time guard); an unanchorable window, an unreadable birth time, and an uncertain docs-branch state each keep; a session state file that is unparseable keeps; a session whose recorded branch ref still resolves keeps its migration manifests (the gate-removal binding operand) while its baseline artifacts drain; a retry after a terminal-state drain starts a new run and reads a fresh setup baseline; the horizon is a named constant re-priced at the next census.

## Outcome

The sweep's retention policy becomes bounded and attributable: three drain arms land inside `scripts/done_sweep_gates_lib.py`, each deletion names its arm, the arms default to report-only, and the kept-forever classes shrink to the genuinely protected ones (manifest-cited bytes, live-root markers, window-fresh records, malformed records, the protected scratch classes, and unresolvable-state fail-closed keeps).

- No new gate, ledger, or registry row: the arms narrow or complete the existing sweep gate's policy (the admission protocol's completion shape); the report-only posture is the arm's own default state, not a new machinery surface.
- The docs-branch sync precondition and its shape classes stay as-is; the never-synced arm is additive, names its own reason, and covers the full top-level regular-file population (receipt in Assumptions).
- The live-worktree fence holds: a marker whose root matches an existing candidate checkout root is never pruned by this plan's arms.
- The done skill's docs-tmp-sweep paragraph documents the three arms, the posture knob, and the retry-after-drain path.

Gate delta: no gate, refusal class, or validator behavior is added or removed; the sweep gate's deletion policy gains three bounded drain classes with printed attributable reasons behind a report-only default, and its keep-side protections are unchanged.

## Assumptions

- Arm 1 uses an age bound over the session-window signal alone, because the window degrades to two confirmed anchors under the marker immortality the sibling row witnesses; an age bound is deterministic. Basis: the catch-22 row's Suggested investigation records the explicit age bound as one of its open decision options, and this plan selects it; the window check and the top-level-files-only shape come from the covered `done-recursive-tmp-sweep-safety` plan, the manifest-citation check from the gate-report-retention guard.
- Arm 1 covers every top-level regular file (the broad population): the existing shape classes reach 2 of 343 measured files, so the narrow reading leaves the witnessed accumulation untouched; the widened class is fenced by the birth-time guard, the window check, the citation hold, and the report-only posture instead of by a filename filter. Basis: the 2026-10-30 census in the catch-22 row and the Terms receipt.
- Arm 2 drains via a dead-root attribution arm instead of migration re-stamping: re-stamping fixes inflow only, rewrites marker identity, and leaves the existing pool immortal; the dead-root arm drains both the historical pool and future inflow (a migrated worktree marker becomes drainable once its worktree is removed at closeout) without touching the producer. Basis: the cross-repo row's Suggested investigation options and its inflow witness (`worktree-migrate-manifest-20261021T014329Z-*`).
- The dead-root candidate set is bounded to this repository's checkout family (one per-pass snapshot: primary, registered worktrees, sibling worktree-root families) rather than a host-wide scan; the residual false positive (a stale marker from an unlisted second clone) is priced inline: a kept file re-reports one more pass, and a drained second-clone marker only ever fed window anchoring. Basis: the cross-repo row's own methodology (digest matching over checkout roots).
- Arm 3 consumes the closeout's own per-session terminal receipt (`runtime_state.json` as written by `gate_execute_plan_closeout`; the receipt keys are `terminal_receipt` and `workflow_state`, with any worktree key read best-effort) rather than the interrupted-manifest run-manifest machinery, and adds the receipt-less legacy arm beside it: the witnessed residue directory carries no state file at all, so the receipt-only predicate would leave the plan's own target undrained; the legacy arm prices that class through the migration manifest's branch-ref and source-worktree records behind the same citation hold and report-only posture. Basis: `terminal_receipt`/`workflow_state` at `gate_execute_plan_closeout`, the zero-manifest corpus survey, and the witnessed receipt-less `self-heal-before-workflow-stop` directory.
- Primary-rooted terminal sessions drain like worktree-rooted ones (the 60M witnessed residue is a primary session); a session whose recorded branch ref still resolves keeps its `closeout-migration.json` family so a later gate-removal adjudication of the retained branch keeps its binding operand. Basis: the proof-family row's census witness and `worktree_closeout_migrate.py gate-removal --migration-manifest`'s branch-only binding.
- The `2026-10-29-branch-only-closeout-terminal-state.md` row's own remedy stays out of scope: the row's Skill-step names `cmd_gate_removal` and `_run_gate_on_twin` (a gate-removal completion receipt), while this plan consumes the closeout's session-local receipt instead. Basis: the row's Skill-step header.
- The report-only default is the admission posture for arms whose failure mode is unrecoverable deletion; promotion criterion: one docs/tmp census cycle whose would-drain rows are all confirmed correctly priced. Basis: the repository guidelines' Machinery admission protocol (warning-only landing, promotion after a true catch) applied to the completion shape.
- The deletion horizon default is 30 days as a named module constant with the facts knob beside it: the value is a policy knob the next census re-prices. Basis: the entry's review-date pricing (the next docs/tmp census).

Decision points requiring a grill: none remain. The maintenance-selected authoring authorization resolves the source-supported choices above (each decision's receipt sits in the Assumptions bullet that owns it).

Scope extensions (grilled): none proposed. The docs-branch runner's archive-root exclusion, the machinery registry rows, and the branch-only terminal-state remedy are all omitted under the maintenance-selected scope (`omit-extension` disposition).

Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**

- Every deletion the sweep makes carries a printed attributable reason naming its arm; in report-only posture every would-drain prints as a would-drain row.
- Every keep-side protection that exists at HEAD still exists after: manifest-cited bytes, live-root markers, session-window freshness, malformed-record preservation, the protected scratch classes (review-loop telemetry, code-review and handoff scratch, pending-plan sessions).

**Done when:**

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q` passes with the new arms' tests.
- Arm 1, given a docs-branch-less fixture repo seeding a docs branch holding zero `docs/tmp` paths and a top-level file with mtime and birth time 40 days old, outside the window, uncited: expects the file drained in `on` posture and reported as a would-drain row in `report-only` posture; and given a fresh file, a manifest-cited file, a directory, a preserved-old-mtime fresh arrival, a window-unanchorable pass, and an uncertain docs-branch state: expects each kept with its existing or new named reason.
- Arm 2, given a fixture marker whose recorded root digest matches no candidate root and whose epoch precedes the anchor: expects the marker drained in `on` posture; and given a live-root marker (digest of a registered worktree), a fresh cross-repo marker, a malformed marker, a legacy raw-path marker resolving to an existing candidate, and an enumeration-failure pass: expects each kept with a fence- or fail-closed-naming reason.
- Arm 3, given a fixture session whose `runtime_state.json` carries `terminal_receipt` with an unregistered worktree and a gone branch ref, or a receipt-less legacy session whose migration manifest names a gone branch ref and an unregistered source worktree: expects the session directory drained including its proof family; and given a non-terminal session, an unparseable state file, a session whose worktree is still registered, and a session whose branch ref still resolves: expects each kept with the last's migration manifests retained and its baseline drained; and given any cited byte inside a session: expects the whole directory kept.

**Ship when:**

- None; this plan is repository-verifiable.

## Design Invariants

- The opposite-direction guard holds: no arm prunes bytes a retained manifest still cites; the citation lookup and the unlink share one citation-hold span per pass, all arms consuming the same `referenced` set inside the span's consume, and an unverifiable hold prunes nothing and reports kept.
- The live-worktree fence holds: a marker whose root matches an existing candidate checkout root is never pruned by recency or by the dead-root arm; no arm re-derives worktree registration independently (one shared per-pass snapshot).
- The covered safety plan's shape holds: no recency-blind recursive sweep; directories stay outside arm 1; the protected scratch classes stay outside every arm.
- No new machinery: the arms complete `gate_docs_tmp_sweep`'s existing policy; the machinery registry gains no row and no removal; the posture knobs are the arm's own posture, not a new surface.
- Drain-classification reads happen through the session descriptor with identity rechecks (the sweep arms' existing discipline), never through a lexical path read that a concurrent closeout could swap between classify and discard.

## Review Scope

**Explicit must-fix:**

- `scripts/done_sweep_gates_lib.py`: the three drain arms (never-synced age bound in `gate_docs_tmp_sweep`; dead-root drain in `_prune_done_session_markers`; terminal-state bound in `_sweep_execute_plan_sessions`), the shared per-pass candidate-root snapshot and citation-hold consumption, and each arm's printed attributable reason.
- `agents/skills/done/SKILL.md`: the docs-tmp-sweep paragraph names the three arms, the posture knob, the keep-side protections, and the retry-after-drain path.

**Production code:**

- Beside the arms, the sweep module may gain small pure helpers: the per-pass candidate-root snapshot (built on the existing worktree-entry parsing), the two-arm root matching, and the shared classification helper for top-level files returning (arm, reason).
- Tests live in `scripts/test_done_sweep_gates_lib.py` beside its current shapes (fixture digests synthesized in-fixture via the lib's own root-digest derivation over fixture paths; isolated-parent repo idiom).

**Validation:** See the commands in `Validation Commands` below.

**Out of scope; reject unless plan-related:**

- `scripts/worktree_closeout_migrate.py` producer changes (no re-stamping).
- The docs-branch runner and its archive-root exclusion.
- The `2026-10-29-branch-only-closeout-terminal-state.md` remedy and the gate-report retention shape.
- Machinery registry rows, new gates, new ledgers.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)"
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: Never-synced scratch age bound in the docs/tmp sweep

Files: `scripts/done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `gate_docs_tmp_sweep` and its window helper in `scripts/done_sweep_gates_lib.py` own the top-level file classification and the drain.
- The shared classification helper (new, beside the arms) owns the (arm, reason) decision for every top-level regular file.

- [x] Add the deletion horizon as a named module constant (30 days) with the facts knobs (`docs_tmp_drain_arms` default `report-only`, `docs_tmp_deletion_horizon_days` falling back to the constant). [class: IMPLEMENTATION_REQUIRED]
- [x] Route every top-level regular file through one shared classification helper that returns (arm, reason): shape-class and `synced` state follow the existing synced arm verbatim; `never-synced` state goes to the new arm; `uncertain` state keeps with the existing uncertain reason. [class: IMPLEMENTATION_REQUIRED]
- [x] Evaluate the cheap pure guards first (mtime and birth time both strictly older than the horizon, mtime outside the session window; an unanchorable window or an unreadable birth time keeps, never guessing), then resolve the sync state for surviving candidates with one batched docs-branch listing (zero hits means never-synced for all survivors). [class: IMPLEMENTATION_REQUIRED]
- [x] In `on` posture the survivor uncited by the shared `referenced` set drains with the printed reason `expired never-synced scratch (age > horizon, outside window, uncited)`; in `report-only` posture the same survivor prints as a would-drain row and nothing unlinks. Directories and the protected scratch classes stay outside the arm. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: given the docs-branch-less fixture seeding a docs branch holding zero `docs/tmp` paths and a stale uncited survivor, expects a drain in `on` and a would-drain row in `report-only`. [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture tests, given/expects: a fresh file, a manifest-cited file, and a directory each stay kept with their named reasons. [class: REPOSITORY_TEST]
- [x] Fixture tests, given/expects: a fresh arrival with a preserved 40-day-old mtime and birth time, a window-unanchorable pass, an uncertain docs-branch state, and a boundary file with mtime and birth time exactly at the horizon each stay kept (the boundary keeps, mirroring the existing strict-anchor semantics). [class: REPOSITORY_TEST]
- [x] Fixture tests, given/expects: with the citation-hold merge lock held by a stub publisher the arm drains nothing and reports the hold-unverified keep reason; with the posture knob at `off` the arm prints no drain rows and keeps everything. [class: REPOSITORY_TEST]
- [x] Commit: `feat: docs/tmp sweep drains expired never-synced scratch behind the report-only posture` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Dead-root marker drain in the done-session marker prune

Files: `scripts/done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_prune_done_session_markers` in `scripts/done_sweep_gates_lib.py` owns the dead-root classification and prune.
- The per-pass candidate-root snapshot helper (new) owns the candidate checkout root enumeration consumed by all three arms.

- [x] Build the per-pass candidate-root snapshot (primary root, registered worktree entries via the existing worktree-entry parsing, the sibling worktree-root families) and consume it in `_prune_done_session_markers`' dead-root arm. [class: IMPLEMENTATION_REQUIRED]
- [x] Match a cross-repo marker's recorded root against the snapshot with the parser's two-arm logic (64-hex digest match, or legacy raw-path realpath match), and prune as `dead-root marker (root absent, pre-window)` when the root matches no existing candidate and the marker's epoch strictly precedes the window anchor. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the classification and unlink inside the same per-pass citation-hold merge-lock span as the existing aged prune, reusing the quarantine-then-reparse flow with the post-quarantine epoch recheck. [class: IMPLEMENTATION_REQUIRED]
- [x] On an enumeration failure (registration unreadable, sibling scan error) mark the snapshot unverified and prune nothing that pass with a named keep reason; a marker whose root matches an existing candidate stays fenced exactly as today; malformed markers are never pruned. [class: IMPLEMENTATION_REQUIRED]
- [x] The sweep summary gains `dead-root-drained=<n>` and `dead-root-kept=<n>` rows as the class census surface; in `report-only` posture the dead-root class prints would-drain rows instead of unlinking. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: given a fixture marker with a synthesized digest matching no candidate and an epoch before the anchor, expects a drain in `on` and a would-drain row in `report-only`. [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture tests, given/expects: the live-root marker written with a fixture worktree's digest (registered via the existing linked-worktree helper, digests synthesized in-fixture over fixture paths, isolated-parent repo idiom) stays kept with a fence-naming reason. [class: REPOSITORY_TEST]
- [x] Fixture tests, given/expects: a fresh cross-repo marker, a malformed marker, a legacy raw-path marker resolving to an existing candidate, and an enumeration-failure pass each stay kept with fail-closed-naming reasons; the census rows report drained and kept dead-root counts; a boundary marker with epoch exactly at the anchor keeps. [class: REPOSITORY_TEST]
- [x] Commit: `feat: done-session marker prune drains dead-root cross-repo markers behind the live-root fence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Proof-family terminal-state bound in the execute-plan session sweep

Files: `scripts/done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_sweep_execute_plan_sessions` in `scripts/done_sweep_gates_lib.py` owns the terminal-state drain decision.
- The shared candidate-root snapshot and citation-hold consumption own the registration and citation inputs.

- [x] Add the terminal-state bound: when a session directory holds proof-family members, read its `runtime_state.json` through the session descriptor with the identity recheck, and classify the session terminal when the state file parses and carries `terminal_receipt` or reads `workflow_state` complete. [class: IMPLEMENTATION_REQUIRED]
- [x] Require for the drain: the session terminal; the recorded worktree resolved against the shared candidate-root snapshot as either unregistered or the primary checkout itself (primary terminal sessions drain - the witnessed 60M residue is a primary session), read best-effort from the state file's worktree-family keys. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the receipt-less legacy arm: a session with no readable state file qualifies when its `closeout-migration.json` records a branch ref that no longer resolves and its manifest-recorded source worktree is unregistered or the primary checkout. [class: IMPLEMENTATION_REQUIRED]
- [x] Require the session's recorded branch ref unresolvable for the full-directory drain (a still-resolving branch keeps the `closeout-migration.json` family - the gate-removal binding operand - while the baseline and other artifacts drain), and no byte inside the session named by the shared `referenced` set (any cited byte keeps the whole directory). [class: IMPLEMENTATION_REQUIRED]
- [x] Keep, with a fail-closed reason: an unparseable state file, a non-terminal session, an unresolvable registration, and a session with neither a readable state file nor a qualifying migration manifest (never guessed from age or directory shape alone). [class: IMPLEMENTATION_REQUIRED]
- [x] In `on` posture the qualifying session directory is removed with the printed reason `consuming closeout terminal; proof family drained (retry reads a fresh setup baseline)`; in `report-only` posture it prints as a would-drain row. Witness: given a fixture session with a `terminal_receipt` state file, an unregistered worktree, and a gone branch ref, expects the directory drained in `on` and a would-drain row in `report-only`. [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture tests, given/expects: the drain case above with a multi-file proof family, and a primary-rooted terminal session with a gone branch ref, each drain in `on` posture. [class: REPOSITORY_TEST]
- [x] Fixture tests, given/expects: a non-terminal session, an unparseable state file, a missing state file, a session whose worktree is still registered (fixture worktree registered via the linked-worktree helper), and a session containing any cited byte each stay kept with their named reasons. [class: REPOSITORY_TEST]
- [x] Fixture tests, given/expects: a session whose branch ref still resolves keeps with its migration manifests retained and its baseline drained; a receipt-less session whose migration manifest names a branch that still resolves stays kept and a session whose source worktree still exists stays kept; with the citation-hold merge lock held, nothing drains and the hold-unverified reason prints. [class: REPOSITORY_TEST]
- [x] Fixture tests, given/expects: the receipt-less legacy drain case (no state file, gone branch ref, unregistered source worktree) drains in `on` posture and prints a would-drain row in `report-only`. [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan session sweep drains proof families once the consuming closeout is terminal` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Documentation and acceptance battery

Files: `agents/skills/done/SKILL.md`, `scripts/done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- The docs-tmp-sweep paragraph in `agents/skills/done/SKILL.md` owns the operator-facing policy documentation.

- [x] Update the done skill's docs-tmp-sweep paragraph: name the three arms and the posture knob with its report-only default and the promotion criterion. [class: IMPLEMENTATION_REQUIRED]
- [x] Document the keep-side protections in the same paragraph: manifest citations and the citation-hold span, the live-root fence, the session window, the protected scratch classes, and the fail-closed keeps. [class: IMPLEMENTATION_REQUIRED]
- [x] State what a retry after a terminal-state drain reads: a fresh `done_run.sh setup` baseline; the landing evidence lives in the plans archive and the landed commits - the session's local manifests are drained by the terminal-state arm. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the acceptance battery: the sweep lib suite, the pins suite, the em-dash added-lines gate over the branch delta, and the public hygiene scan; confirm by one manual sweep invocation over a fixture tree that every deletion reason and would-drain row names its arm and posture. [class: REPOSITORY_TEST]
- [x] Commit: `docs: done skill documents the three bounded docs/tmp drain arms` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- `agents/skills/done/SKILL.md` docs-tmp-sweep paragraph: updated by Task 4 (the only skill-text change; no other skill references the sweep's deletion classes).
- The backlog rows' resolution rides the landing's mark-covered closeout; no separate disposition records are needed.

## Disposition of migrated backlog items

The plan's three backlog origins (docs/history/backlog/2026-10-30-docs-tmp-sweep-sync-precondition-catch-22.md, docs/history/backlog/2026-10-30-done-session-cross-repo-marker-immortality.md, docs/history/backlog/2026-10-30-execute-plan-proof-family-retention-unbounded.md) are deleted by this rider: each row's decision is one landed task (Task 1 never-synced scratch age bound, Task 2 dead-root marker drain, Task 3 proof-family terminal-state bound), landing commit e1e1a792d, with the review chain staged as 2026-11-02-docs-tmp-drain-arms-code-review-r1/r2. Residual r1/r2 findings ride their own open rows (docs/history/backlog/2026-11-02-docs-tmp-drain-*.md and 2026-11-02-drain-r2-*.md); the stale-registration-snapshot row gates any `docs_tmp_drain_arms` promotion past `report-only`.
