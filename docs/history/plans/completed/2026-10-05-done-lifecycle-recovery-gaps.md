# Plan: done lifecycle recovery gaps

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-done-marker-manifest-partial-failure.md`
- `docs/history/backlog/2026-10-05-done-interrupted-manifest-recovery.md`
- `docs/history/backlog/2026-10-05-done-closeout-checkpoint-writer-gap.md`
- `docs/history/backlog/2026-10-05-done-manifest-review-candidate-classification.md`
- `docs/history/backlog/2026-10-05-execute-plan-done-owner-fence-diagnostic.md`
- `docs/history/backlog/2026-10-05-done-revert-classifier-source-resolution.md`

Driving force: reliability (six witnessed 2026-10-05 closeout failures across one live execution's done boundaries: a setup that kept running into the manifest writer after the marker command failed, an interrupted manifest whose live root left only adopt-or-finalize with no deterministic verification, a skill-mandated resumable-closeout checkpoint with no writer behind it, a review-candidate classification discovered only after the lock and marker were taken, a done refusal that named the wrong missing fields when the owner fence failed, and a classifier resolution order that false-blocked a closeout while the canonical copy existed; the done boundary is the loop's own commit path crossed by every lane, so each gap taxes every closeout in every repository)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-done-lifecycle-recovery-gaps-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Run-start marker: the content-bearing `run-start-YYYYmmddTHHMMSSZ` file under `{tmp_dir}/done-session/`; its single line records the creation epoch, the SHA-256 hex digest of the trailing-slash-stripped resolved repo root, and the writing PID.
- Content-confirmed marker: a marker confirmed through the library's two-form confirmation (a 64-hex digest record compares against the freshly recomputed repo-root digest; a legacy raw-path record compares by resolved path); the sweep gates anchor the session window on the newest content-confirmed marker.
- Run manifest: the `run-manifest-<run_id>.json` ownership record beside the marker (`scripts/done_sweep_gates_lib.py`, `RunManifest`): run identity, marker filename, start commit and porcelain snapshot, owned plan/review/path claims, foreign review paths, the explicit `adopted_from` link, and the `complete` flag.
- Interrupted manifest: a manifest with `complete` false and no adopter naming it; `write-manifest` refuses a new boundary while one stands (`write-manifest: undisposed-interrupted:`) and the refusal's remedy line names the exits.
- `dispositioned` record: the one-time record (`reason`, `date`, `note`) stamped by `disposition-manifest` that suppresses interrupted-run detection; the dead-root closure command owns it today and refuses a live root by contract.
- Deliverables witness: `disposition-manifest`'s set-specific resolution of every owned deliverable before it stamps, exactly as the code implements per set: an owned plan passes at its recorded path, `HEAD:<path>`, its completed-archive twin, or note-backed; an owned review resolves on the docs branch; an owned path passes at `HEAD:<path>`, its completed-archive twin, through a landed deletion, or note-backed; the all-three-sets-empty arm passes vacuously with the named note.
- Owned-commits ledger: the per-commit ownership record appended at done Step 1; resume verification reads its commits as reachable from the landing destination.
- Resumable-closeout checkpoint: the sibling JSON the done skill requires when a run enters the finalizer span, naming the run_id, the manifest path, the session identity, the manifest's sha256, and the gates already green; Step 6 refreshes it at the finalize preamble and a successful finalize removes it (agents/skills/done/SKILL.md, Step 0 run-manifest paragraph and Step 6).
- Done receipt: the parent-side done handoff receipt the runtime validates in `_record_done_locked`: checkpoint identity, task id, success status, action scope, checkbox and clean-state flags, `commit_identity`, `log_evidence`, `claim_token`, `generation`, and the fence fields checked against the live claim.
- Claim-owner fence: `_claim_receipt_owner_matches` (`scripts/execute_plan_runtime.py`): when the live claim records `claim_owner_id`, the receipt must carry the same value; the fence rides beside the driver-ownership, token, and generation checks in the `fenced` conjunction.
- Reverted-scope guard: the manifest writer's claim-or-foreign gate over every staging candidate on disk at Step 0; a candidate neither owned nor foreign aborts Step 0 with the bulk-affordance remedies.

## Why

A single live execution hit six distinct done-boundary failures on 2026-10-05 and filed each as its own operator-marked row. They share one production seam (agents/skills/done/SKILL.md Step 0 and `scripts/done_sweep_gates_lib.py`) plus one companion surface (the runtime's done receipt in `scripts/execute_plan_runtime.py`), and each one stranded a closeout that the surrounding work had already finished: implementation and review complete, commit boundary unreachable. Five rows concern the done skill's own setup-and-recovery contract; the sixth concerns the receipt contract the execute-plan driver assembles at the same boundary. The cluster is authored as one plan so the shared file is touched once, the refusal vocabulary stays coherent across the new commands, and the skill text lands aligned with the library instead of drifting between six separate landings.

## Outcome

A done closeout survives every witnessed failure shape:

- Setup is atomic from the operator's perspective: the review-candidate classification is recorded before the lock and marker are taken, a failed marker recipe aborts Step 0 before the manifest writer runs and leaves a named partial-setup receipt, the manifest writer binds to this run's own marker by explicit flag with fail-closed refusals, and one documented resume procedure distinguishes an unadopted manifest from a stale marker without staging or sweeping first.
- An interrupted manifest with a live root has an evidence-driven recovery command: it verifies the owned deliverables and the owned commits against the repository before any write, stamps the closing record only when the work is verifiably landed, and refuses with named evidence otherwise, leaving the boundary for adopt or finalize.
- The resumable-closeout checkpoint has a writer: one schema-validated operation creates, refreshes, verifies, and removes the checkpoint sibling, the skill's Step 0 and Step 6 text names the concrete invocations, and a successful finalize is the only thing that removes it.
- A done receipt refusal names the failed fence field (owner, token, generation, or driver ownership) separately from missing evidence fields, and the receipt contract carries the live claim-owner identity alongside token and generation so the first attempt is correct.
- The revert-set classifier's documented resolution order includes the facts-resolved canonical skills checkout, so a service checkout without repo-local or deployed copies resolves the canonical script instead of false-blocking.

Gate delta: the new commands arrive with named refusal classes (marker binding refusals, recovery verification refusals, checkpoint lifecycle refusals) and one refusal decomposition (the owner fence named inside the existing done-refusal line rather than a new gate). Each is priced by its witnessed row: the marker binding closes the cross-shell continuation the partial-failure row witnessed; the recovery verification closes the unverified-dispose risk the interrupted-manifest row witnessed; the checkpoint refusals enforce the freshness and identity semantics the skill text already declares; the owner-field refusal closes the misdiagnosed-retry cost the diagnostic row witnessed. No existing refusal weakens: the marker-to-manifest identity check, the claim-or-foreign gate, the dead-root disposition contract, and the fail-closed done fence all keep their current semantics.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so Step 1.4 confirmation is satisfied by the rows' validated records rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the checkpoint's session identity is caller-supplied and recorded, not derived from a manifest field; basis: the `RunManifest` schema carries no session field (run identity, marker, PID, root digest only), the skill's checkpoint contract names a session identity without fixing a source, and the caller writing the checkpoint is the same session that acquired the lock and holds the run record in context; the operation requires a non-empty identity value and records it verbatim.
- assume `recover-manifest` stamps the shared `dispositioned` record shape with its own reason value rather than inventing a second suppression record; basis: `dispositioned` already suppresses interrupted-run detection (the exact before-another-closeout effect the row wants), the record shape and its idempotent reprint semantics exist, and one suppression mechanism keeps `write-manifest`'s refusal logic untouched; the dead-root command keeps its own precondition and refusal unchanged.
- assume the classification reorder is skill-text ordering over the existing affordances, not new flags; basis: `--emit-foreign-candidates` and `--foreign-review-from` exist and are documented, the emit invocation writes no manifest, and the row's Expected asks for the classification to happen before the lock and marker, which is an ordering contract.
- assume `--run-marker` is opt-in and backward compatible; basis: existing invocations keep today's newest-anchor binding, the skill mandates the flag for the composed Step 0 block, and the witnessed failure is the cross-shell continuation the explicit binding closes.
- assume checkpoint removal stays outside `finalize-manifest` and rides the refreshed Step 6 recipe (refresh, finalize, remove); basis: `finalize-manifest`'s two-way identity contract is frozen semantics, the remove arm verifies `complete` true so a failed finalize leaves the checkpoint present, and the skill text already describes Step 6 as the refresher and the successful finalize as the remover.
- assume Task 1 folds its three rows because they share the Step 0 region of the skill and the marker/classifier surface of the library, and each arm keeps its own validation lines; basis: the shared-file seam rule (tasks editing the same production file stay in one plan) and the rows' own fix shapes, which are ordering and resolution-text changes plus one writer flag.
- assume `disposition-manifest`'s deliverables-witness arms are the reuse surface for Task 2's verification, present at authoring; basis: the command's docstring names the recorded-path, completed-twin, `HEAD:<path>`, landed-deletion, and note-backed resolutions as implemented behavior, re-verified on this tree before authoring.
- assume the done receipt's `claim_owner_id` back-compat arm stays: a claim without an owner keeps accepting an ownerless receipt; basis: `_claim_receipt_owner_matches` treats a missing claim owner as matched, and the row's contract is the fence diagnostic, not a widening of which claims fence.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the done boundary gains fail-atomic setup with pre-lock classification, a verified live-root recovery command for interrupted manifests, the mandated checkpoint writer, named owner-fence refusals on the done receipt, and the canonical-checkout arm in the classifier resolution order.

Before (today): a done run's marker recipe fails in a fresh shell context; the shell continues into the manifest writer, which binds the manifest to the previous run's content-confirmed marker; the first pre-commit sweep rejects the mismatched pair and recovery needs a second marker and an explicit adoption boundary. A prior interrupted manifest with a live root blocks every new write-manifest with only adopt-or-finalize as remedies and no deterministic verification of what the interrupted run actually landed. The skill orders a checkpoint written at the finalizer span, but no operation exists to write one, so the session either hand-edits state (prohibited) or records the gap and proceeds bare. A done receipt missing `claim_owner_id` is refused with the wrong missing-field names, costing a manual comparison against the live claim. A service checkout without repo-local or deployed classifier copies false-blocks while the canonical checkout holds the script.

After (this plan): the classification emit invocation runs before the lock and marker; the marker recipe and the manifest writer compose as one fail-atomic block passing `--run-marker`; a marker failure aborts Step 0 with a named partial-setup receipt and never reaches the writer. A found partial setup resolves through one documented procedure (newest content-confirmed marker versus the manifest's recorded marker filename). An interrupted live-root manifest closes through `recover-manifest`, which verifies the deliverables witness and owned-commit reachability, stamps the shared closing record on success, and refuses with named evidence otherwise. The checkpoint exists as `checkpoint-manifest` create/refresh/verify/remove with digest and identity refusals, wired into the Step 0 finalizer-span and Step 6 text. A done receipt fence failure names the exact failed field, and the receipt contract carries `claim_owner_id` beside token and generation. The classifier resolution order reads repo-local, then deployed home, then the facts-resolved canonical skills checkout.

Edge cases pinned: a manifest writer invoked with a `--run-marker` path that is absent, foreign-content, or no longer the newest content-confirmed marker refuses with no manifest written; an absent flag keeps today's binding; a recovery command pointed at a dead root refuses and names `disposition-manifest`; a recovery command whose owned commits are not reachable or whose owned deliverables do not resolve refuses with no mutation; a checkpoint created twice refuses and names refresh; a checkpoint verify after a manifest byte change refuses as stale; a checkpoint remove before `complete` refuses; a failed finalize leaves the checkpoint present; a refusal on the done receipt leaves the done-pending claim unchanged and an exact retry with the owner id completes; a claim without an owner keeps accepting an ownerless receipt.

## Tasks

### Task 1: Step 0 setup atomicity, pre-lock classification, and classifier source resolution

Files:
- `agents/skills/done/SKILL.md`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_revert_set_classifier.py`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$PY" ] || PY=python3; "$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers the marker-binding criteria below at the task boundary (the suite owns a pytest runner, no main shim)
- `python3 scripts/test_revert_set_classifier.py`; covers the classifier regression criterion (main-shim suite)
- `bash scripts/check_maintenance_pins.sh`; covers the resolution-contract pin and any re-keyed span

- [x] `test_write_manifest_run_marker_binds_newest_confirmed` (given a done-session directory with two content-confirmed markers and `write-manifest --run-marker <older>`, expects a named refusal and no manifest written; with `--run-marker <newest>`, expects the manifest created and its `marker` field naming that marker) [class: REPOSITORY_TEST]
- [x] `test_write_manifest_run_marker_refusals` (three refusal arms: absent marker path, marker whose content does not confirm under the two-form confirmation, marker path pointing at a file outside the done-session directory; each expects a named one-line refusal, non-zero exit, and the done-session directory byte-identical before and after) [class: REPOSITORY_TEST]
- [x] `test_write_manifest_without_flag_keeps_newest_anchor` (given the flag absent, expects today's behavior: the manifest binds to the newest content-confirmed marker) [class: REPOSITORY_TEST]
- [x] Implement the `--run-marker` flag in `_cmd_write_manifest` (scripts/done_sweep_gates_lib.py): the manifest binds to the named marker; named one-line refusals when the marker path is absent, sits outside the done-session directory, carries content that does not confirm under the two-form confirmation (digest record against the recomputed root digest, legacy raw-path record against the resolved path), or is no longer the newest content-confirmed marker; the flag absent keeps today's newest-anchor binding [class: IMPLEMENTATION_REQUIRED]
- [x] Step 0 text, classification ordering: move the review-candidate classification ahead of lock acquisition and the run-start marker in agents/skills/done/SKILL.md Step 0: the `--emit-foreign-candidates` invocation and the owned-claims decision are recorded before the lock is taken and the marker is written, with a stated reason (the classification is read-only and writes no manifest, so taking the lock before classifying only risks discovering an ownership abort mid-setup); the real `write-manifest` invocation then runs with the reviewed `--foreign-review-from` list or the per-path flags [class: IMPLEMENTATION_REQUIRED]
- [x] Step 0 text, fail-atomic composition: the marker recipe and the manifest writer compose as one fail-atomic block: a marker-recipe failure (sha256 tooling missing, malformed digest, location self-check) or a manifest-writer failure inside the composed block (any named write-manifest refusal or the empty-echo abort) stops Step 0 before staging or sweeping and records the same named partial-setup receipt line in the session notes (the failed step, its refusal evidence, no manifest written for a marker failure; the writer's refusal evidence and no manifest bound for a writer failure); the composed block passes `--run-marker "$MARKER"` to the writer, and the same skill edit adds `--run-marker` to the stale-deployment signature's documented-flag enumeration so a stale runtime-home copy is diagnosed by the redeploy recipe, not an investigate detour [class: IMPLEMENTATION_REQUIRED]
- [x] Step 0 text, partial-setup resume procedure: one documented decision procedure for a found partial setup that compares the newest content-confirmed marker against the found manifest's recorded marker filename: manifest marker is the newest marker means an unadopted current-boundary manifest, resolved through the existing remedies (`--adopt` or `finalize-manifest`); manifest marker is older or absent means a stale marker, and the manifest belongs to the earlier boundary per the interrupted-manifest remedies; neither marker nor manifest means a fresh Step 0; the procedure never stages or sweeps before it resolves and keeps the marker-to-manifest identity check fail-closed [class: IMPLEMENTATION_REQUIRED]
- [x] Revert-set paragraph, third resolution arm: the classifier resolution order in the Step 0 revert-set adjudication paragraph reads repo-local first, then the deployed home copy, then the facts-resolved canonical skills checkout (`skills_repo_path`), with the missing-dependency block standing only when all three arms miss; the same edit adds a pins row over the amended paragraph naming the three ordered arms and the all-miss block, so the pins suite is the resolution contract's mechanical witness (the classifier's own outcome handling stays pinned by its existing suite) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full lib and classifier suites, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: done step 0 gains fail-atomic setup, pre-lock classification, and the canonical classifier arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Live-root interrupted-manifest recovery command

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

Evidence:
- `PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$PY" ] || PY=python3; "$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers every criterion below at the task boundary
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_recover_manifest_stamps_when_work_verified` (given an interrupted manifest with a live recorded root, an owned plan resolving at its recorded path, and every owned-commits ledger entry reachable from HEAD, expects exit 0, the shared closing record stamped with the reason literal `work-verified-landed-live-recovery` and date, the command's receipt line printed, and the manifest suppressed from interrupted-run detection; a second identical invocation reprints the existing record and exits 0) [class: REPOSITORY_TEST]
- [x] `test_recover_manifest_dead_root_refusal` (given a manifest whose recorded root digest names a nonexistent checkout, expects a named refusal directing to `disposition-manifest`, with no record stamped) [class: REPOSITORY_TEST]
- [x] `test_recover_manifest_unverified_evidence_refusals` (two arms: an owned deliverable that resolves through none of the witness arms refuses naming the deliverable and the arms attempted; an owned-commits entry not reachable from HEAD refuses naming the commit; both leave the manifest byte-identical and still interrupted) [class: REPOSITORY_TEST]
- [x] `test_recover_manifest_state_refusals` (arms: already `complete` refuses; already adopted by another manifest refuses; unowned tree preservation: the command mutates nothing outside the manifest record, verified by byte-comparing the worktree and index before and after) [class: REPOSITORY_TEST]
- [x] Implement the `recover-manifest` subcommand in scripts/done_sweep_gates_lib.py: for an interrupted manifest whose recorded root matches the current repository through the shared two-arm matcher (`_repo_root_matches_value`: a 64-hex record compares by digest, a legacy raw-path record by resolved path, either arm per record), verify before any write (the deliverables witness reusing `disposition-manifest`'s set-specific resolution arms per set unchanged, empty owned sets vacuously passing with the named note, and owned-commits reachability of every ledger entry from the landing destination), then stamp the shared closing record with the recovery reason and date and print a receipt line, reusing `disposition-manifest`'s stamp-time compare-and-swap unchanged (the payload re-read through the reader's parse contract and the fresh adoption re-scan immediately before the write, refusing post-check finalize and post-check adoption so a concurrent Step 6 finalize or competing closure cannot be overwritten); refusals name the failed evidence and mutate nothing; `--note` records the operator note inside the stamped record for the note-backed escape [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, live-root recovery paragraph: the Manifest disposition region of agents/skills/done/SKILL.md gains the live-root sibling arm (when an interrupted manifest's root is live and the operator directs closure, `recover-manifest` verifies and stamps; a refusal keeps the boundary for `--adopt` or `finalize-manifest` with the named evidence recorded); the same edit extends every refusal surface that names the interrupted-manifest exits (the `write-manifest: undisposed-interrupted:` refusal line, the partial-setup resume procedure's remedy sentence, and the lib's disposition-manifest live-root refusal message) with `recover-manifest`, and updates the Step 0 resume-continuation sentence's parenthetical that calls the disposition record a dead-root-only mechanism to name the live-root recovery arm beside it, so the landed skill never self-contradicts about which boundaries can close and no landed commit names an absent command [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full lib suite, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: recover-manifest verifies and closes live-root interrupted boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Resumable-closeout checkpoint writer

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

Evidence:
- `PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$PY" ] || PY=python3; "$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers every criterion below at the task boundary
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_checkpoint_create_refresh_verify_remove_lifecycle` (create writes the sibling checkpoint JSON naming run_id, manifest path, session identity, manifest sha256, green-gate list, and created epoch; refresh updates the recorded sha and gate set in place; verify recomputes the manifest digest and compares identity, exiting 0 with a verified receipt; remove refuses while `complete` is false and succeeds after finalize set it true, deleting the sibling) [class: REPOSITORY_TEST]
- [x] `test_checkpoint_refusals` (arms: create on an existing checkpoint refuses and names refresh; refresh with no checkpoint present refuses and names create; create or refresh on an absent manifest refuses, and verify and remove name their absent-manifest behavior (verify refuses as unverifiable; remove refuses naming finalize as the prerequisite); refresh after the manifest is already `complete` refuses; verify after any manifest byte change refuses as stale with the recomputed digest named; verify with a mismatched session identity or run_id refuses; every refusal leaves the checkpoint and manifest byte-identical) [class: REPOSITORY_TEST]
- [x] `test_failed_finalize_leaves_checkpoint` (given the refreshed Step 6 sequence refresh, finalize that aborts on the identity check, remove: expects the remove to refuse because `complete` stayed false and the checkpoint sibling to remain present) [class: REPOSITORY_TEST]
- [x] Implement the `checkpoint-manifest` subcommand in scripts/done_sweep_gates_lib.py with `--run-id`, `--mode create|refresh|verify|remove`, `--session <identity>` (required non-empty for create and refresh, recorded verbatim; optional for verify, where an omitted session skips the session-identity comparison and a present one is compared), and `--gates <comma,list>` (the green-gate set recorded at write time); the checkpoint is a per-run sibling JSON beside the manifest owned by this operation (the filename derives from the run_id, so one run's orphaned checkpoint cannot collide with a later run's create), manual checkpoint editing stays unsupported, and verify is the mechanical gate the resume continuation reads (identity match plus recomputed sha match) [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text alignment: the Step 0 finalizer-span sentence and the Step 6 preamble and resume-continuation sentences in agents/skills/done/SKILL.md name the concrete `checkpoint-manifest` invocations (create at finalizer-span entry, refresh at the finalize preamble, remove after the successful finalize, verify at resume) while preserving the existing resume-continuation contract wording where it does not name an operation [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full lib suite, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: checkpoint-manifest writes the resumable-closeout record the done skill mandates` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Done-receipt owner fence and refusal diagnostics

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

Evidence:
- `python3 scripts/test_execute_plan_runtime.py`; covers every criterion below at the task boundary
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_done_receipt_owner_fence_refusal_names_field` (three arms: the live claim records an owner and the receipt omits `claim_owner_id`, the refusal names the owner fence; the receipt carries a different owner, the refusal names the mismatch; the receipt carries the exact owner, the done lands and the task closes) [class: REPOSITORY_TEST]
- [x] `test_done_receipt_refusal_preserves_and_retries` (given a refused done receipt, expects the claim unchanged in state, token, and generation, and an exact retry that adds the owner id completes the same task without rotating the claim or losing its commit) [class: REPOSITORY_TEST]
- [x] `test_done_receipt_missing_evidence_still_named` (given a receipt missing `log_evidence` with the owner fence satisfied, expects the refusal to name the missing evidence field, not the owner fence; given a receipt failing both the owner fence and an evidence field, expects the refusal to name both; given a receipt failing a non-evidence non-fence conjunct such as the checkbox flag, expects the refusal to name that conjunct's field; given a receipt whose task id resolves to no task, expects the refusal to name the task lookup) [class: REPOSITORY_TEST]
- [x] `test_done_receipt_ownerless_claim_backcompat` (given a live claim without `claim_owner_id`, expects an ownerless receipt to remain acceptable) [class: REPOSITORY_TEST]
- [x] Implement the refusal decomposition in `_record_done_locked` (scripts/execute_plan_runtime.py): the refusal names every failed conjunct of the validity check by its own field (the fence fields: claim ownership by driver, `claim_owner_id` presence or match, `claim_token` match, `generation` match; the evidence fields: `commit_identity`, `log_evidence`; the remaining conjuncts: task and claim lookup (a receipt naming no task, or a task with no live claim), task status, action scope, checkbox, clean state, commit identity length, checkpoint-to-task consistency, planned-commit echo), so a receipt failing any one conjunct reads the failed field's name and never a generic or misattributed line; every refusal keeps the preserve-and-reconcile outcome with no state mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Receipt contract text: the done receipt schema in agents/skills/execute-plan/runtime-contract.md carries `claim_owner_id` beside `claim_token` and `generation`, sourced from the live claim, so the assembled receipt is correct on the first attempt; a pinned span reworded by this task is recorded as a pin-rekey follow-up receipt in the session notes instead of a same-edit pins change (no pin overlaps this task's edit regions today, verified at authoring) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full runtime suite, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: done receipt carries the claim owner and refusals name the failed fence` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Files in scope (the union of the task Files lists): `agents/skills/done/SKILL.md`, `scripts/done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_lib.py`, `scripts/test_revert_set_classifier.py`, `scripts/check_maintenance_pins.sh`, `scripts/execute_plan_runtime.py`, `scripts/test_execute_plan_runtime.py`, `agents/skills/execute-plan/runtime-contract.md`.

Reviewers judge: contract preservation (the frozen `finalize-manifest` identity contract, the dead-root `disposition-manifest` precondition, the claim-or-foreign gate, and the fail-closed done fence must keep their semantics), fail-closed posture of every new refusal (named one-line errors, no mutation, byte-identical state after refusal), the recovery verification's soundness (the deliverables witness and owned-commit reachability must be sufficient to close a boundary, and the note-backed escape must stay operator-explicit), the checkpoint schema's sufficiency for the resume-continuation contract the skill text already declares, the `--run-marker` binding's backward compatibility, the owner-fence decomposition's completeness (no fence conjunct left unnamed), scope discipline (no task reaches beyond its Files list), and test reality (every criterion has a named test that can run in this repository without external services).

## Validation Commands

```bash
PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$PY" ] || PY=python3
"$PY" -m pytest scripts/test_done_sweep_gates_lib.py -q
python3 scripts/test_revert_set_classifier.py
python3 scripts/test_execute_plan_runtime.py
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-done-lifecycle-recovery-gaps.md
```

## Residual findings (cap closure)

(none): the cap-closure fold batch landed the r4 probe's single Low into Task 1's fail-atomic criterion before this section; no deferred residuals remain at the standard-class five-round cap.
