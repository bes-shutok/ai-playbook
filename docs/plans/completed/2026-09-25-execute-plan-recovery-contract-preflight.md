# Plan: execute-plan recovery contract and preflight (recovery-interruptions systemic remedy)

Origin: `docs/history/backlog/2026-09-24-execute-plan-recovery-interruptions.md` (Priority: high)
Consolidated origin: `docs/history/backlog/2026-09-23-execute-plan-preflight-before-claim-launch.md` (this plan's Task 4 implements that item's preflight; route it done as consolidated at this plan's completion processing)
Supersession (2026-09-25): `docs/plans/2026-09-24-exec-plan-recovery-interruptions.md` (landed on main at 43f98bf6) declares the same origin as its scope of record and the same consolidated siblings, and its premise that the parked workstream is reference-only contradicts this plan's land-after-workstream serialization. This plan supersedes it: Task 8 archives the predecessor with a superseded registry row naming this plan as successor, and the next dispatch selects this plan, never the predecessor.
Related, not consolidated (references resolve on the parked workstream branch, not on main): `2026-09-23-execute-plan-codex-initial-capacity-witness.md`, `2026-09-22-execute-plan-handoff-recover-persisted-launch.md` (driver-residual batch family), `2026-09-24-done-pending-recovery-r1-low-findings.md` (Task 8 routes it conditionally per verified Low coverage).
Driving force: Primary: reliability. Secondary: simplicity and recoverability.

## Terms
- **Recovery transition**: any driver operation that requeues, rotates, or re-binds a claim after a failed or interrupted state: `recover_done_pending`, handoff recovery, interrupted-task adoption.
- **Terminal receipt**: the immutable recovery receipt recorded by a successful recovery transition, correlating the closed claim identity, the pending task, and the requeue generation.
- **Preflight**: a read-only validation pass, run before a claim is created or rotated, that proves the next task can be claimed, launched, completed, committed, and resumed; it mutates nothing.
- **Plan-versus-claim scope drift**: the plan's Tasks/Files/checklists naming paths that the seeded immutable task scopes in the machine manifest do not authorize.
- **The parked workstream**: unlanded branch `2026-09-22-codex-execute-plan-runtime-reconciliation`, which owns the current generation of the driver recovery paths, the manifest worker-schema validator (`validate_manifest_worker_schema`), and the reconciliation predicates this plan builds on. None of that code exists on `main` at authoring time.

## Assumptions
1. The parked workstream lands before Tasks 2 through 6 execute; this plan does not re-implement workstream-owned code, it hardens it. Phase-0 drift check (Task 1) is the mechanical gate for this assumption and re-baselines touched surfaces if the branch landed with different shapes.
2. The model-guard hook (`agents/hooks/codex-model-guard/require-luna.py`) is repo-owned, but the defect the origin describes is branch-relative: on `main` the hook's worker-tool markers are exact names (`spawn_agent`, `spawn-agent`, `subagent`) with a transcript-model fallback, while the parked workstream's version adds the bare `agent` marker that produces the denial the origin witnessed. Task 5 therefore edits the hook as landed by the drift gate and is bound to it like Tasks 2 through 4.
3. `scripts/test_codex_model_guard.py` and `scripts/test_execute_plan_runtime.py` remain the canonical test twins for their surfaces; new tests join them rather than new files unless a task says otherwise.
4. The provider-specific process/session probing stays in the Codex adapter; durable policy stays in the runtime driver (scope boundary from the origin item).
5. Small non-blocking findings may be deferred with evidence rather than reopening a review loop (origin non-goal).

Decision points requiring a grill: none remain.

## Gist & Examples
TLDR: make every execute-plan recovery transition provably safe and every launch preflighted, by (a) gating implementation on the parked workstream's landing with a drift check, (b) correlating terminal worker records with their immutable receipts so recovery never leaves the manifest unusable, (c) validating each transition's resulting manifest before persistence with byte-identical rollback on failure, (d) adding one read-only preflight that catches scope drift and claimability gaps before a claim is consumed, (e) replacing the model guard's substring match with exact worker-creation tool identities, and (f) making resume orchestration derive one next action from the driver instead of re-running whole-plan machinery.
Example: today a `recover_done_pending` requeue can rotate a claim while a historical terminal worker record remains; the next launch's schema validation refuses with `worker claim identity does not match claim`, and recovery has "succeeded" into an unusable manifest. After this plan, the transition's resulting manifest is validated before persistence and a failure restores the prior bytes, so the operator never inherits a broken manifest from a successful recovery.

## Evaluation Criteria
- After any recovery transition, the persisted manifest passes the same schema and reconciliation validation the next launch runs; a validation failure leaves the manifest byte-identical to pre-transition bytes.
- A terminal historical worker record is accepted only when the exact closed-claim + pending-task + matching-terminal-receipt tuple holds; live workers must still match the live claim.
- The preflight reports plan-versus-claim scope drift, checklist ownership gaps, missing capacity evidence, and claimability refusals before a claim is created or rotated, and never mutates state.
- The model guard grants wait, inspect, send, and close operations without a launch model field and denies worker creation without the selected model, matched on exact tool identities.
- Resume after an unchanged digest derives the next action from the driver and recorded artifacts without repeating whole-plan review or relaunching to repair plan prose.
- Repeated recovery cycles with a retained historical launch record converge: requeue increments the generation, the reconciler ignores only the exact receipt-backed record, and the task is selectable again.

## Review Scope
- Production code: `scripts/execute_plan_runtime.py`, `scripts/execute_plan_runtime_codex.py`, `scripts/execute_plan_worker_registry.py` (as landed by the workstream), `agents/hooks/codex-model-guard/require-luna.py`.
- Repository tests: `scripts/test_execute_plan_runtime.py`, `scripts/test_execute_plan_runtime_codex.py`, `scripts/test_codex_model_guard.py`.
- Documentation: `agents/skills/execute-plan/SKILL.md` (resume and recovery paragraphs only), `agents/skills/execute-plan/runtime-contract.md` (recovery contract paragraphs only), `agents/hooks/codex-model-guard/README.md`.
- Plans/backlog: this plan's origin items under `docs/history/backlog/` (Disposition lines and archive moves only).
- Exclusions: `agents/skills/execute-plan/runtime-adapters/codex.md` and `scripts/execute_plan_resume_watcher.py` are workstream-owned unless the Phase-0 drift check finds them landed and a task explicitly names them; fixture trees under `scripts/testdata/` change only inside a task that names the fixture.

## Validation Commands
Run from the repo root; every gate must be green at done:
```bash
python3 scripts/plan_readiness.py docs/plans/2026-09-25-execute-plan-recovery-contract-preflight.md
bash scripts/check-no-em-dash.sh file docs/plans/2026-09-25-execute-plan-recovery-contract-preflight.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files docs/plans/2026-09-25-execute-plan-recovery-contract-preflight.md
python3 scripts/test_codex_model_guard.py
python3 scripts/test_execute_plan_runtime.py
grep -qF 'exact worker-creation tool identities' agents/hooks/codex-model-guard/README.md
grep -qF 'byte-identical rollback' agents/skills/execute-plan/runtime-contract.md
```
Per-task gates are the per-task test-arm checklist items; a task that edits a parked-workstream-owned file defers its gate runs until Task 1's drift check re-baselines the file list.

## Tasks

### Task 1: Phase-0 drift check and serialization gate against the parked workstream [class: IMPLEMENTATION_REQUIRED]
- [x] Verify whether branch `2026-09-22-codex-execute-plan-runtime-reconciliation` has landed on the default branch (commit search for its squash subject); record the finding in the execution manifest [class: REPOSITORY_TEST]
- [x] If unlanded: Tasks 2 through 6 each stop at their workstream-independent boundary and wait; if landed: diff every file this plan touches against the landed workstream shapes and re-baseline the task file lists and Validation needles before any edit (Tasks 2 through 6 all touch workstream-owned or workstream-rewritten surfaces) [class: IMPLEMENTATION_REQUIRED]
- [x] Record the serialization decision (land-after-workstream, with the re-cert obligation on drift) in the plan's own execution notes; never merge this plan's worktree into the workstream's branch [class: IMPLEMENTATION_REQUIRED]

### Task 2: Terminal worker validation correlated with immutable receipts [class: IMPLEMENTATION_REQUIRED]
- [x] In the manifest worker-schema validation path (workstream-landed `validate_manifest_worker_schema`), accept a historical terminal worker record only when the exact tuple holds: the claim it names is closed, the task is pending, and a terminal recovery receipt matches the record's original claim identity and the requeue generation [class: IMPLEMENTATION_REQUIRED]
- [x] Keep active workers fully matched against the live claim (no weakening of existing mismatch refusals) [class: IMPLEMENTATION_REQUIRED]
- [x] Regression arms in `scripts/test_execute_plan_runtime.py`: requeue after terminal worker completion passes; active-worker mismatch still refuses; an ambiguous handoff (no receipt) still follows the existing reconciliation path rather than the new exception [class: REPOSITORY_TEST]

### Task 3: Post-transition validation with byte-identical rollback on every recovery path [class: IMPLEMENTATION_REQUIRED]
- [x] Wrap every recovery transition (`recover_done_pending`, handoff recovery, interrupted-task adoption) so the resulting manifest is validated through the same schema and reconciliation path the next launch uses, before persistence [class: IMPLEMENTATION_REQUIRED]
- [x] On validation failure, persist nothing: the manifest file is byte-identical to pre-transition bytes (temp-write and atomic rename or restore-from-captured-bytes, whichever the driver's existing persistence helper supports) [class: IMPLEMENTATION_REQUIRED]
- [x] Regression arms: a forced post-transition validation failure leaves the manifest byte-identical; the successful path still persists [class: REPOSITORY_TEST]

### Task 4: Read-only execution preflight with scope-drift reporting [class: IMPLEMENTATION_REQUIRED]
- [x] Add a read-only preflight command to the driver that, before a claim is created or rotated, validates: plan digest and review readiness, per-task plan-versus-claim path scope including checklist ownership, runtime activation and capacity evidence (subsuming the origin's adapter-configuration noun), the required approval receipt where the seeded scope records one, claimability, and post-recovery worker-registry schema [class: IMPLEMENTATION_REQUIRED]
- [x] Publish one canonical continuation command or wrapper that supplies all required runtime inputs from the verified local configuration, so a resume run does not hand-assemble inputs [class: IMPLEMENTATION_REQUIRED]
- [x] Scope drift is reported before any claim is consumed, naming the plan paths and the machine-seeded scopes side by side [class: IMPLEMENTATION_REQUIRED]
- [x] The preflight mutates nothing: test asserts zero byte changes to manifest and claims under a failing preflight; missing, stale, or invalid activation evidence leaves the claim and handoff retryable; a valid preflight proceeds on the same authorized claim [class: REPOSITORY_TEST]

### Task 5: Model guard exact tool-identity matching [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/hooks/codex-model-guard/require-luna.py` as landed by the drift gate (main's marker tuple is already exact-name based with a transcript-model fallback; the workstream version adds the bare `agent` marker that produces the witnessed denial), enforce the rule with a match set of exact worker-creation tool identities; wait, inspect, send, and close operations remain callable without a launch model field, and no marker reverts to a bare substring [class: IMPLEMENTATION_REQUIRED]
- [x] Tests in `scripts/test_codex_model_guard.py`: creation without the selected model is denied; each lifecycle operation passes without a model field; a near-miss tool name that merely contains the substring is not treated as a launch [class: REPOSITORY_TEST]
- [x] Update `agents/hooks/codex-model-guard/README.md` decision table to the identity-based rule; the table carries the literal phrase "exact worker-creation tool identities" [class: IMPLEMENTATION_REQUIRED]

### Task 6: Resume orchestration derives one next action [class: IMPLEMENTATION_REQUIRED]
- [x] Resume decisions derive from the driver and recorded artifacts: unchanged digest means claim/recovery state only, never a repeated whole-plan review; plan-prose mismatches never relaunch or re-seed a claim [class: IMPLEMENTATION_REQUIRED]
- [x] Document the resume decision table (one supported action per condition; retryable pre-launch vs ambiguous post-launch; never manual machine-state edits) in `agents/skills/execute-plan/SKILL.md` recovery paragraphs and the runtime contract's recovery section [class: IMPLEMENTATION_REQUIRED]
- [x] Unrelated validation or hygiene failures are recorded as separate follow-ups and do not invalidate the active task's correctness or commit scope [class: IMPLEMENTATION_REQUIRED]

### Task 7: End-to-end recovery cycle coverage [class: IMPLEMENTATION_REQUIRED]
- [x] Hermetic end-to-end test exercising successive claim, launch, terminal receipt, done handoff, recovery, and next-task launch against fixture manifests (no live provider) [class: REPOSITORY_TEST]
- [x] Rebased-plan case: task files differ from machine-seeded scopes and the preflight reports drift before claim consumption [class: REPOSITORY_TEST]
- [x] Repeated-cycle case: a task with a retained historical launch record is requeued with a new generation and selected again; the reconciler ignores the old record only on the exact receipt-backed tuple [class: REPOSITORY_TEST]

### Task 8: Origin routing and deferred follow-ups [class: IMPLEMENTATION_REQUIRED]
- [x] Route the origin item `2026-09-24-execute-plan-recovery-interruptions.md` done with this plan as implementation reference [class: IMPLEMENTATION_REQUIRED]
- [x] Archive `docs/plans/2026-09-24-exec-plan-recovery-interruptions.md` as superseded by this plan: registry row naming this plan as successor; its premise that the parked workstream is reference-only is contradicted by Task 1's drift gate [class: IMPLEMENTATION_REQUIRED]
- [x] Route `2026-09-23-execute-plan-preflight-before-claim-launch.md` done as consolidated ONLY when each of its asks verifies against landed code: the canonical continuation wrapper exists (Task 4), the retryability and valid-path test arms exist (Task 4), and the approval-receipt validation exists (Task 4); otherwise leave open with a Disposition line naming the uncovered asks [class: IMPLEMENTATION_REQUIRED]
- [x] Route `2026-09-24-done-pending-recovery-r1-low-findings.md` done only if each Low verifies as covered (backlog-evidence validation, group-anchor resolution, docs fold); otherwise leave open with a Disposition line naming the uncovered Lows [class: IMPLEMENTATION_REQUIRED]
- [x] Defer per backlog-deferral default with evidence: paired ambiguous-handoff retry/proof tests if existing tests already establish the contract; Interrupt-hook subprocess timing measurement; environment-dependent hygiene script inputs; Task 6 route/mismatch cross-product trims; smoke-witness artifact removal if no repository consumer exists [class: IMPLEMENTATION_REQUIRED]

### Task 9: Final validation suite [class: REPOSITORY_TEST]
- [x] Run the whole `## Validation Commands` block plus every per-task gate; expect green with no skipped check; record full output in the task log [class: REPOSITORY_TEST]
- [x] Confirm the origins-closure check passes with every origin dispositioned [class: REPOSITORY_TEST]

## Decision Points
- Task 1's landed/unlanded finding decides which of Tasks 2 through 6 proceed this run; both outcomes are acceptable completions of the task as written.
- Task 8's coverage verdict on the done-pending Lows decides route-done versus leave-open; both are first-class outcomes, never a review failure.

## Execution notes

Execution 2026-09-25, two runs (both in-session under standing pre-authorization):

- Run 1 (boundary run, squash f3b920d4): Task 1 drift check found the workstream branch UNLANDED; Tasks 2 through 6 waited per Decision Point 1; the predecessor `2026-09-24-exec-plan-recovery-interruptions.md` was archived as superseded with a registry row naming this plan as successor.
- Unblock: the parked workstream branch `2026-09-22-codex-execute-plan-runtime-reconciliation` was rebased onto main (3 conflicts union-resolved: runtime --input help text, document-registry rows, lessons corpus with the branch's two unwitnessed lessons renumbered #429/#430), all five suites green (404+ tests), and squash-landed as 5b414ee3. This satisfied Task 1's landed arm: the landed shapes match the plan's expected anchors (`validate_manifest_worker_schema`, terminal receipts, `recover_done_pending`, the model-guard marker tuple), so no re-baseline of task file lists or needles was needed.
- Run 2 (Tasks 2 through 9): Task 5 exact tool-identity matching in the model guard (substring `in` replaced by exact set membership on both gates) with near-miss and lifecycle tests and the README decision table carrying the needle phrase; Task 2 hardens the landed terminal exemption - a mismatched historical terminal record is accepted only when a `done-pending-recovery` history receipt matches its original claim identity, rotation without receipt backing refuses, ambiguous handoffs (matched identity, no receipt) still follow the existing reconciliation path; Task 3 wraps every recovery transition's success persistence (`recover-done-pending` requeue/defer/abort, `recover-ambiguous-handoff`, `reconcile-interruption`) with pre-save `validate_manifest_worker_schema` and byte-identical rollback on failure (forced-failure and success-persist regression arms); Task 4 adds the read-only `preflight` operation (worker-registry schema, plan readability, whole readiness decision, per-task plan-versus-claim scope drift naming plan paths and seeded scopes side by side, approval-receipt revalidation, one canonical continuation command; mutation-freedom, retryability, and drift-before-claim-consumption arms); Task 6 adds the resume decision table to the SKILL.md recovery paragraphs and the recovery guarantees paragraph (carrying the `byte-identical rollback` needle) to the runtime contract; Task 7 adds the hermetic end-to-end claim/launch/terminal/recovery/reclaim cycle test (repeated-cycle receipt-backed convergence) plus the rebased-plan drift arm. Task 8 routed all three origins done with verified dispositions (including the done-pending r1 Lows: F1 requeue backlog-evidence gating and F2 group launch-record anchor resolution implemented with regression tests, F3 folded into the contract docs).
- Review loop: r1 (2026-09-25, ready=no, 2 blocking) folded both blockers: (1) the three routed origin files' completed-path copies are committed (the boundary `git add -u` had stranded them as untracked), and (2) the preflight now honestly covers the ticked Task 4 bullet: manifest-recorded plan-digest verification, checklist-ownership agreement for the next task's plan section, live-claim activation-evidence presence (missing/stale evidence reported while the claim and handoff stay retryable), and the registry capacity witness.
- Task 9 validation: full `## Validation Commands` block plus per-task suites green pre-landing; full output in the session task log.

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-23-execute-plan-preflight-before-claim-launch.md: disposition folded into 2026-09-25-execute-plan-recovery-contract-preflight.md (2026-09-25); per-item file deleted.
