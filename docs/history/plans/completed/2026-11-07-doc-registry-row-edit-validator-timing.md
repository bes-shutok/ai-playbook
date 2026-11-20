# Plan: Edit-time doc-registry validation and suite baseline repair

Backlog origins (scope of record):
- docs/history/backlog/2026-10-31-doc-registry-row-edit-validator-timing.md
- docs/history/backlog/2026-11-06-invocation-telemetry-finalize-pin-recapture.md
- docs/history/backlog/2026-11-07-machinery-inventory-unregistered-fire-outcomes-script.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-doc-registry-row-edit-validator-timing-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 2.5h total, largest task 0.75h
Executed: yes (73abb5332178b267f5b734694225c3833e40b257)

Authoring claim: 2026-10-31-doc-registry-row-edit-validator-timing.md (session sess_5461ba27-4867-4c74-8965-6c044107e682)

## Terms

- doc-registry: `docs/maintenance/document-registry.md`, the document ownership registry table.
- row edit: any hand edit of the registry table's rows or its header comment, on any commit path.
- ladder commit: a commit made through `scripts/done_run.sh commit`, whose built-in sweep already runs the doc-registry gate.
- rider commit: a commit made on the default branch outside the ladder, typically a post-landing rider or a direct primary-checkout commit; it never runs the sweep.
- landing sweep: the `done_sweep_gates.sh landing` gate set; its `doc-registry` gate runs `scripts/doc_registry_validator.py validate` and hard-refuses on violations.
- validate: the read-only validator invocation `python3 scripts/doc_registry_validator.py validate`; it reports violations and exits nonzero, it never mutates files.
- finalize output pins: the frozen stdout and stderr fixtures in `scripts/test_invocation_telemetry.py` that preserve the observable `done_run finalize` contract.
- learn heading parity: the ordered module-heading contract checked against the split learn modules.
- machinery inventory: `scripts/machinery_registry.json` and its check of tracked scripts against their registered disposition.

## Why

A malformed registry row reached `main` in commit `c63419139` and sat there for roughly 80 minutes until a different session's landing sweep caught it, because that edit was a rider commit outside the ladder and no check ran where the edit was made. The fix moves the validator run to the editing session for every commit path. The execution run also requires the repository suite to pass, so it includes three independently reproduced baseline corrections: stale finalize-output pins, a missing learn-module heading in the parity contract, and an unregistered operative script in the machinery inventory.

## Gist & Examples

TLDR: name edit-time registry validation and repair the three reproduced suite baselines, so the documented expectation and the required full-suite gate both hold; the driving force is code-quality.

**Before (today):** a session clears a registry row's audit note as a post-landing rider commit, as witnessed in `c63419139`. The hand edit drops the trailing empty-cell pipe and the row lands with 8 of 9 cells. Nothing validates the edit: rider commits never run the ladder sweep. The malformed row sits on main for roughly 80 minutes until another session's landing sweep hard-refuses, and the repair rides that foreign session's landing (`0cda7cc45`, landed in `bc227e63e`). The editor never learns the row was broken; a peer pays the repair.

**After (this plan):** the same session, editing the same note, reads the registry header comment, which now instructs every editor to run `python3 scripts/doc_registry_validator.py validate` before committing any registry edit and to fix what it reports first. For an editor that follows the note, the malformed shape never leaves the editing session and no foreign landing is burdened; an editor that skips the note recreates the witnessed failure unchanged, and the sweep gate stays the backstop that catches it. The header comment is the surface editors already follow (the identity scheme and the 9-cell shape live there today), so the expectation lands where the edit happens.

**Suite baseline before (observed):** the full repository suite reports five finalization-output pin mismatches, one learn module-heading parity mismatch, and one real-tree machinery inventory failure for `scripts/maintenance_fire_outcomes.py`. Each failure reproduces on the rebased run worktree before these added tasks.

**After (suite gate):** the telemetry fixtures pin the current finalization line with its source landing recorded; the learn parity contract includes the intended capture-freshness heading; and the existing machinery inventory registers the operative script. Runtime behavior and the inventory checker remain unchanged.

**Edge cases:** the registry note must stay inside the existing HTML comment and its lines must carry no pipe-leading row shapes, because the validator's row scan reads pipe-leading lines even inside the comment (a pipe-leading example line strictly inside the comment hard-errors `validate`); the validator is read-only, and the note says so, because an editor might otherwise fear running it mid-edit. Commits that already pass through the ladder keep their existing sweep coverage unchanged; the note is additive prevention for exactly the paths the sweep cannot see.

## Outcome

Registry row edits are expected to be validated by their own editor before commit, on every commit path; the expectation binds by skill text, and the landing sweep remains the enforcement backstop. The five finalize-output pins, learn heading parity contract, and machinery registry entry also match the current behavior, and the required full suite passes.

- A rider-commit row edit that breaks the 9-cell shape is expected to be caught by the editing session's own validator run and fixed before the commit, when the editor follows the header expectation.
- The landing sweep's `doc-registry` gate remains the unchanged fail-closed backstop for anything that slips past the editor.
- The full repository suite passes with the baseline corrections included.
- No runtime code, gate, validator, lock, ledger, or refusal class is added, removed, or changed; the machinery inventory receives only an entry for an existing script.

Gate delta: none (explicit). The registry header comment, test contracts, and one existing-script inventory entry change. The landing sweep gate, validator, finalize implementation, learn implementation, and machinery checker stay byte-unchanged. No gate or fence is added, so no ledger citation is required.

## Assumptions

- assume ladder commits already run the validator at commit time; basis: `gate_doc_registry` is wired into the sweep in `scripts/done_sweep_gates_lib.py` (present since commit `fe61c8471`, 2026-09-27) and `agents/skills/done/SKILL.md` Step 3 places the landing sweep inside the commit ladder, so the witnessed gap is specific to non-ladder edits.
- assume the witness edit was a non-ladder commit; basis: `c63419139` (2026-10-31 20:17) sits directly on the landing commit `721e6cc21` as a post-landing rider on the default branch, a path that never runs `done_run.sh commit`.
- assume editors follow the registry header comment; basis: the header comment is already the operative format contract (the identity scheme, backfill and archived-date rules, and the consumed-by-validator note live there, and the table's 9-cell shape persists because editors follow it).
- assume no schema expansion; basis: the origin row's explicit out-of-scope line ("Do not claim migration rejects every semantically invalid baseline"; the validator grammar is unchanged and the note adds no validation rules).
- assume the finalization line is intended contract output; basis: the fresh reproductions match the five stale literals and the originating `done-finalize-resume-marking-honesty` landing.
- assume the additional learn heading is intended module content; basis: `docs/history/plans/completed/2026-11-06-learn-capture-freshness-reprobe.md` added the section and the current test fails only because its expected heading list omits it.
- assume the machinery script remains operative; basis: the open inventory row traces it to commit `833e4c7d3` and its current post-fire consumers.

Simpler-design comparison for the selected arm: a done commit-stage duty is rejected because the ladder already runs the sweep gate at commit time, so a new duty adds nothing there and a runner-side check cannot reach non-ladder commits at all; a pre-commit hook is rejected in the origin row itself (heavier machinery than the defect prices); a serializer or round-trip helper is rejected because it adds tooling for a rarely edited file whose prevention overlaps the note plus the unchanged sweep backstop. The header note is the only candidate that reaches the widest editor population at the moment of edit while adding zero machinery.

Decision points requiring a grill: arm selection resolved on the maintenance-selected path: skill-text expectation single-homed in the registry header comment (receipt: the origin's Direction names "a pre-commit expectation named in the skill text" as a candidate arm; the comparison and evidence sit in the Simpler-design paragraph above; decided 2026-11-07 by sess_5461ba27 under the operator one-shot automation-90fcace6 standing authorization). Scope extension resolved in: include the seven reproduced Phase 2 failures as Tasks 2-4 (receipt: user explicitly answered yes to the scope choice on 2026-11-07; evidence is the Phase 2 rerun log and the focused rerun; this plan's Outcome, Evaluation Criteria, Review Scope, Validation Commands, and Tasks 2-4 are affected).

Scope extensions (grilled): seven reproduced Phase 2 suite failures across finalize-output pins, learn heading parity, and machinery registry admission: in (user explicit acceptance, 2026-11-07).

Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**
- correctness: after the edit, `python3 scripts/doc_registry_validator.py validate` exits 0 over the registry (the note lives inside the HTML comment the table parser ignores).
- precision: the note names the exact command, the any-commit-path scope, and the read-only nature of the validator; no other registry bytes change.
- backstop integrity: the landing sweep gate, validator implementation, finalize implementation, learn module, and machinery checker are unchanged.
- suite integrity: all seven reproduced failures are repaired without relaxing any test or validator expectation.

**Done when:**
- the header comment instructs editors to run `python3 scripts/doc_registry_validator.py validate` before committing any registry edit and to fix reported violations first, with the sweep gate named as the backstop.
- the validator exits 0 over the edited file; the focused failure modules and complete repository suite pass; no document-registry table row bytes or validator/gate implementation bytes changed.

**Ship when:**
- none (repository-verifiable only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production and test contracts:**
- `docs/maintenance/document-registry.md` (Task 1)
- `scripts/test_invocation_telemetry.py` (Task 2)
- `scripts/test_learn_router_dispatch.py` (Task 3)
- `scripts/machinery_registry.json` (Task 4)

**Documentation and provenance:**
- `docs/history/plans/completed/2026-11-05-automation-fire-time-failure-verification.md` (Task 4)

**Origin status rows:**
- `docs/history/backlog/2026-11-06-invocation-telemetry-finalize-pin-recapture.md` (Task 2)
- `docs/history/backlog/2026-11-07-machinery-inventory-unregistered-fire-outcomes-script.md` (Task 4)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/doc_registry_validator.py`; the validator grammar is unchanged by design (origin out-of-scope line).
- `agents/skills/done/SKILL.md`; the ladder path is already covered by the sweep gate and stays byte-unchanged.
- `scripts/done_run.sh`, `agents/skills/learn/step-completion.md`, `scripts/maintenance_fire_outcomes.py`, and `scripts/machinery_inventory.py`; the fixes update their existing test or inventory contracts without changing runtime behavior.

## Validation Commands

```bash
python3 scripts/doc_registry_validator.py validate
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_invocation_telemetry.py scripts/test_learn_router_dispatch.py scripts/test_machinery_inventory.py -q
python3 scripts/machinery_inventory.py --check
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_*.py -q
```

### Task 1: Name the edit-time validation expectation in the registry header

Context surface: the plan's Terms, this task, and `## Standing constraints` (not declared; absent).

Files:
- `docs/maintenance/document-registry.md`

- [x] Extend the existing HTML header comment in `docs/maintenance/document-registry.md` with an edit-time expectation block: every session editing this file runs `python3 scripts/doc_registry_validator.py validate` before committing the edit, on every commit path (ladder or rider), and fixes any reported violation before the commit. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same expectation block: name the validator read-only, name the landing sweep's `doc-registry` gate as the unchanged fail-closed backstop, and keep the note inside the HTML comment with no table row bytes changed and no pipe-leading lines (the validator's row scan reads pipe-leading lines even inside the comment). [class: IMPLEMENTATION_REQUIRED]
- [x] Cite the witnessed defect class in one line inside the same expectation block: commit `c63419139`, an 8-of-9-cell row caught roughly 80 minutes later at another session's landing. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/doc_registry_validator.py validate` over the edited registry and expect exit 0 with no row violations (the note's lines carry no pipe-leading row shapes). [class: REPOSITORY_TEST]
- [x] Verify scope containment: `git diff --name-only` against the base shows exactly `docs/maintenance/document-registry.md`. [class: REPOSITORY_TEST]
- [x] Commit: `docs: name the edit-time doc-registry validation expectation in the registry header` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Recapture the finalize-output pins

Context surface: `scripts/test_invocation_telemetry.py` and the telemetry backlog origin above.

Files:
- `scripts/test_invocation_telemetry.py`
- `docs/history/backlog/2026-11-06-invocation-telemetry-finalize-pin-recapture.md`

- [x] Given each of the five finalize scenarios, expects its frozen output literal to include the current finalization line in the observed position while preserving the surrounding pinned output. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Task 2 lands, expects the telemetry origin row to read `covered-pending-execution` with this plan as its witness and no other row content changed. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the finalization line is added to the pins, expects the test header to cite landing `998d1dade` as its provenance. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the invocation-telemetry module runs, expects all finalize tests to pass without weakening their byte-parity assertions. [class: REPOSITORY_TEST]
- [x] Commit: `tests: recapture finalize output pins` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Restore learn module heading parity

Context surface: the learn router dispatch contract and completed plan `docs/history/plans/completed/2026-11-06-learn-capture-freshness-reprobe.md`.

Files:
- `scripts/test_learn_router_dispatch.py`

- [x] Given the completion module defines `### Capture-freshness re-probe mechanics`, expects the module heading contract to include that heading in source order. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the learn router parity module runs, expects all module-heading and dispatch-order checks to pass without changing the learn module contents. [class: REPOSITORY_TEST]
- [x] Commit: `tests: include the learn completion heading in router parity` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Register the operative fire-outcomes script

Context surface: the machinery inventory backlog origin above and `scripts/machinery_registry.json`.

Files:
- `scripts/machinery_registry.json`
- `docs/history/backlog/2026-11-07-machinery-inventory-unregistered-fire-outcomes-script.md`
- `docs/history/plans/completed/2026-11-05-automation-fire-time-failure-verification.md`

- [x] Given the existing machinery registry schema, expects the operative fire-outcomes script registered with its class and `witness.ref` pointing to tracked file `docs/history/plans/completed/2026-11-05-automation-fire-time-failure-verification.md`, with registry provenance noting introducing commit `833e4c7d3`. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the machinery inventory check runs, expects zero failures while the checker remains unchanged. [class: REPOSITORY_TEST]
- [x] Given Task 4 lands, expects the machinery origin row to read `covered-pending-execution` with this plan as its witness and no other row content changed. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `registry: register the maintenance fire outcomes script` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-31-doc-registry-row-edit-validator-timing.md`, Completed by Task 1: the registry header now directs editors to run the read-only validator before committing, and the edited registry validates with zero hard findings. The origin file is deleted in this archive pass.
- `docs/history/backlog/2026-11-06-invocation-telemetry-finalize-pin-recapture.md`, Completed by Task 2 and the Phase 3 hermeticity fix: finalize output pins now match the current emission, the non-interactive Bash tests scrub `BASH_ENV`, and the focused and isolated full suites pass. The origin file is deleted in this archive pass.
- `docs/history/backlog/2026-11-07-machinery-inventory-unregistered-fire-outcomes-script.md`, Completed by Task 4: the operative script is registered with a tracked witness and the machinery inventory check passes. The origin file is deleted in this archive pass.
