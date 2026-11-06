# Plan: Preserve finalized manifest terminal state in the primary shadow record

Backlog origin: docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md
Driving force: reliability (outside the closed taxonomy; implemented anyway because the origin row declares it and the plan closes a witnessed false-interruption producer path in the done closeout machinery; park-triage would not take it: the defect produces durable false setup-refusal evidence on every successful worktree closeout)
Plan review record: the staging series .ai-playbook/reviews/2026-11-05-plan-review-done-finalized-manifest-shadow-p3059b0ef-r*.md
Authoring claim: done-finalized-manifest-shadow.md (session sess_26fef284-67f5-41a5-90e5-0270dbf399fe)
Execution budget: 1.5h total, largest task 1.0h
Executed: yes (edebacd968aea39618cac4350fe69c04b21aadf4)

## Terms

- **Primary shadow:** the `docs/tmp/done-session/run-manifest-<run-id>.json` copy the worktree closeout migration transfers to the primary checkout before the source worktree is removed.
- **Source manifest:** the worktree run's own `run-manifest-<run-id>.json` under the worktree's facts-resolved done-session directory.
- **Terminal state:** the finalized manifest bytes where `complete: true` is recorded for the run.
- **Finalize leg:** the `done_run.sh finalize` completion path that runs `finalize-manifest` (scripts/done_sweep_gates_lib.py) against the manifest its run identity resolves.

## Why

A successfully completed worktree run leaves false interruption evidence behind. The closeout migration copies the run manifest to the primary checkout before the source worktree is removed; finalization later marks only the source copy `complete: true`; the worktree removal then destroys that finalized copy. The surviving primary shadow keeps `complete: false`, and `_detect_interrupted_runs` classifies the completed run as interrupted, so a later `done_run.sh setup` can refuse on false evidence. Witnessed: `docs/tmp/execute-plan/automation-fire-time-failure-verification/closeout-migration.json` records the pre-finalize copy while the primary shadow stayed incomplete after source finalization; the primary done-session directory currently holds hundreds of accumulated incomplete shadow records (296 at authoring time, most with dead roots). Draining that existing pool is owned by `docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md` and stays outside this plan; this plan owns only the producer path.

## Gist & Examples

TLDR: propagate the finalized manifest's terminal state to the surviving primary shadow record during the finalize leg, so a completed worktree run stops re-classifying as interrupted after its source copy and worktree are gone.

Before: the closeout migrates the pre-finalize manifest bytes to the primary checkout; the finalize leg marks only the source worktree copy `complete: true`; after worktree removal the primary shadow remains `complete: false` and `_detect_interrupted_runs` reports the completed run as interrupted.

After: when the finalize leg marks a run's manifest complete, the same leg updates the run's primary shadow copy (same run-id, same canonical filename) with the finalized bytes before the closeout ends. A completed worktree run whose source record and worktree are removed leaves the primary record terminal, and the classifier no longer reports it. Genuinely incomplete runs still classify as interrupted and setup still refuses on them.

Edge cases: a primary shadow absent at finalize time is created from the finalized bytes only when the closeout migration records that run's manifest as transferred, never invented from nothing; an identity mismatch between the finalized source bytes and the shadow's recorded run identity aborts the propagation and reports it instead of overwriting; a finalize that fails or withholds its marking propagates nothing; when the invocation checkout already is the primary checkout (a primary-dispatched closeout), the resolved primary shadow path equals the file finalize-manifest just wrote, the propagation is a silent no-op skip with no rewrite and no miss-report; a shadow already carrying terminal or dispositioned bytes is skipped with a report and never overwritten; a shadow write refusal reports the miss with no partial write; the finalize leg keeps its existing failure-reporting honesty arms unchanged, the propagation report carrying its own distinct `shadow propagation:` message prefix so the wrapper's grep-classified advice arms never misroute on it.

## Outcome

A completed worktree run leaves terminal (`complete: true`) evidence in the surviving primary record, and `_detect_interrupted_runs` no longer classifies it as interrupted after the source manifest and worktree are removed.

- The false-interruption producer path is closed for future runs; the existing incomplete-shadow pool is drained by its owning row, not here.
- The classifier's terminal-state contract and its refusal for genuinely incomplete runs are preserved unchanged.
- No second independent terminal-state writer is introduced: the propagation is performed by the existing finalize leg inside its existing completion path.

Gate delta: one propagation arm inside the existing finalize leg plus its failure-honesty reporting; no new gate, validator, lock, ledger, or schema field. Machinery admission: incident: `docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md`; expected catch frequency: every successful worktree closeout whose finalize follows the pre-removal migration (witnessed recurring shape, hundreds of accumulated shadows); false-positive cost: bounded, the propagation only moves already-verified terminal bytes for the same run-id behind the identity check and the already-terminal guard (a dispositioned or complete shadow is skipped with a report, so no sanctioned closure record is destroyed); review date: 2026-12-05; promotion requires a true catch and a pre-registered registry-removal row; machinery-inventory disposition: no registry row, the propagation writer is part of the existing finalize-manifest operation's protocol surface, not a new write protocol.

## Design Invariants

- One authoritative writer: the `finalize-manifest` operation's success path (the operation inside scripts/done_sweep_gates_lib.py that the finalize leg invokes, and the same operation the printed recovery remedies call directly) is the only code path that writes terminal state into the primary shadow record. No new standalone finalize-shadow command, no closeout-migration write of terminal bytes, no classifier write-back.
- Run identity binds the propagation: the primary shadow is located by the exact canonical filename `run-manifest-<run-id>.json` for the run-id the finalize leg just completed; before overwriting, the shadow's recorded run identity fields (run_id, and repo_root/plan_path identity fields the manifest carries) must be consistent with the finalized source bytes (the manifest's real fields: run_id, repo_root, owned_plan_paths), else the propagation aborts with a report and leaves both files untouched.
- Already-terminal shadow guard: the arm skips with a report when the shadow payload already carries `complete: true` or a non-null `dispositioned` record; it overwrites only a strict pre-finalize twin (`complete: false`, `dispositioned` null, identity fields equal), so a sanctioned one-time closure record is never silently destroyed.
- The classifier contract is untouched: `_detect_interrupted_runs` keeps its run-identity closure semantics (a terminal record on any file of the run suppresses the run) and its refusal behavior for genuinely incomplete runs.
- Failure honesty: when the propagation cannot run or verify (missing shadow, unresolvable primary root, shadow write refusal), the finalize leg reports the miss on its failure channel without failing the finalize itself; the run's completion honesty arms (the existing FAILED lines) keep governing.
- No pool drain, no migration-order change for non-manifest artifacts, no change to the closeout migration's own verified-transfer receipts.

## Tasks

### Task 1: Reproduce the false interruption in a regression

Files:
- `scripts/test_done_sweep_gates_lib.py` (existing file; adds cases)

Primary class anchors: `_detect_interrupted_runs` in `scripts/done_sweep_gates_lib.py`

Steps:
1. Add a regression that builds the witnessed shape end to end at the unit level: a primary shadow manifest with `complete: false` for run R, a finalized source manifest for run R with `complete: true`, the source file then removed, and `_detect_interrupted_runs` over the primary done-session directory reporting run R as interrupted.
2. Add its permanent contract twin, green on landing: a primary shadow carrying terminal (`complete: true`) bytes for run R suppresses run R from `_detect_interrupted_runs` output (the classifier's existing terminal-on-any-file closure, pinned at the detection level). Both cases land green in this task; the red-to-green assertion lives in Task 2 against the real propagation entry point, not here.

Testing: both cases run green under the existing suite runner; the detector-level contract (incomplete reported, terminal suppressed) is pinned unchanged by this task.

### Task 2: Propagate terminal state in the finalize leg

Files:
- `scripts/done_run.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_run_wrapper.py` (existing file; adds cases)
- `scripts/test_done_sweep_gates_lib.py` (existing file; adds cases)

Primary class anchors: `cmd_finalize` in `scripts/done_run.sh`; `finalize-manifest` in `scripts/done_sweep_gates_lib.py`

Steps:
1. In the `finalize-manifest` operation's success path, add the propagation arm: resolve the primary checkout root with the existing git-based resolution (`_resolve_primary_checkout` in scripts/done_sweep_gates_lib.py; the same resolution the closeout migration uses, not a facts key) and the done-session directory under the facts-resolved `tmp_dir` of that primary root; read `run-manifest-<run-id>.json` there, verify its run identity fields (run_id and repo_root, plus the run's owned-plan identity in the manifest's real `owned_plan_paths` field) against the finalized source bytes, apply the already-terminal guard, and write the finalized bytes over it. The arm also runs on the operation's already-complete early return, so a re-run after an earlier skipped or failed propagation still propagates (idempotent: the same finalized bytes); the arm's shadow path resolves through the migration's lenient `_facts_tmp_root` helper, named in the same function-local import set. When the resolved primary done-session directory equals the invocation checkout's own (a primary-dispatched closeout), the arm is a silent no-op skip. When the primary shadow is absent but the run's closeout migration record (the `closeout-migration.json` transfer entry for that manifest, located via the existing `_plan_session_slug` and record-path helpers from scripts/worktree_closeout_migrate.py, imported function-locally per the lib's established pattern) witnesses a transfer, write the finalized bytes as the surviving record; when neither the shadow nor a transfer witness exists, skip with a report.
2. Wire the arm to report on its failure channel when it cannot run or verify, per the Design Invariants failure-honesty shape, without changing the finalize exit semantics for the finalize itself. Because the arm lives inside the `finalize-manifest` operation (success path and already-complete early return), the printed direct-CLI recovery remedies (finalize-manifest with --run-id) propagate terminal state through the same path; a rerun from the primary checkout after source removal still hits the operation's identity refusal for a worktree-rooted shadow (the documented dead-root disposition shape governs there), so the first successful finalize remains the authoritative propagation chance.
3. Add the red-to-green assertion here against the real entry point: with the arm in place, the Task 1 witnessed shape (source finalized then removed) leaves the primary shadow terminal and `_detect_interrupted_runs` no longer reports run R. Add wrapper-level cases covering: shadow present and updated; shadow absent with transfer witness; shadow absent without witness (skip+report); identity mismatch (abort+report, both files untouched); finalize withheld (no propagation); primary-dispatched no-op (no rewrite, no miss-report); after propagation, `classify-run-boundary` on the primary shadow returns `finalized` and setup continues with a fresh boundary; shadow already terminal (`complete: true` or non-null `dispositioned`) is skipped with a report and never overwritten; primary root unresolvable at finalize time reports the miss with the finalize's own outcome and FAILED-line arms unchanged; shadow write refused reports the miss with no partial write; a rerun after an earlier skipped propagation still propagates; the propagation report lines never trip the wrapper's `run-manifest identity mismatch` advice routing. The wrapper's `run_finalize` helper gains a `cwd` parameter so the worktree-dispatched finalize cases reuse the existing hermetic fixtures.
4. Keep the existing post-removal ordering and identity-refusal arms byte-identical in behavior for runs that do not reach the new arm.

Testing: the done-run wrapper suite and the gates-lib suite pass; the Task 2 red-to-green pair is green after the arm; no existing case regresses.

### Task 3: Contract note and closeout-doc touch

Files:
- `agents/skills/done/SKILL.md` (the finalize contract sentence and the Step 6 composition list, plus one added paragraph)

Primary class anchors: the finalize/closeout sequence description in `agents/skills/done/SKILL.md`

Steps:
1. Amend the existing sentence "Finalize mutates only the invocation checkout; an exported manifest never routes mutation into another checkout" to carve out the named exception: terminal-state propagation into the primary checkout's surviving shadow record for the same run-id, performed by the `finalize-manifest` operation.
2. Amend the Step 6 composition list that enumerates finalize's mutations to include the shadow propagation.
3. Add one paragraph documenting that the finalize leg now propagates terminal state to the surviving primary shadow record and what the failure-honesty report looks like when the propagation skips or aborts.

Testing: documentation-only; hygiene scan over the touched file.

## Testing

- `scripts/test_done_sweep_gates_lib.py` and `scripts/test_done_run_wrapper.py` under the repository test runner (`PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_<name>.py -q`).
- The Task 1 before/after pair is the regression contract; the post-fix twin stays green permanently.
- Public hygiene scan over the touched files.

## Assumptions

- The finalize leg's completion path is the correct and only propagation point; the closeout migration and the classifier stay write-free.
- The primary root resolution available to the finalize leg (git-resolved primary checkout root plus the facts-resolved `tmp_dir` under it, the same two-part resolution the closeout migration uses) is reachable at finalize time in the witnessed sequences; where it is not, the arm reports and skips rather than guessing.
- Draining the accumulated existing incomplete shadows (hundreds at authoring time) is out of scope (owned by the orphaned-pool row).
Decision points requiring a grill: none - the origin row names the exact surfaces (the finalize leg, the closeout migration, the interrupted-run classifier) and the entry's scope arms fix the design choice (propagate terminal state in the finalize leg; keep the classifier contract and the pool drain outside this change).

## Disposition of migrated backlog items

The single backlog origin `docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md` is covered by this plan's execution: the finalize leg propagates the finalized manifest's terminal state into the surviving primary shadow record (propagation arm inside the `finalize-manifest` operation, identity-bound, already-terminal-guarded, witness-gated creation, failure-honest reporting under the `shadow propagation:` prefix), closing the witnessed false-interruption producer path; the origin row is deleted in the same landing. Draining the already-accumulated incomplete-shadow pool stays owned by `docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md`, unchanged.
