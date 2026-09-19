# Plan: execute-plan Phase 3 process: reconciliation trigger and archive safety

Backlog origins: docs/history/backlog/2026-09-18-execute-plan-review-reconciliation-trigger-not-invoked.md; docs/history/backlog/2026-09-18-execute-plan-archive-before-task-completion.md
Design input: docs/reviews/2026-09-18-review-reconciliation-execute-plan-review-fix-pipeline-efficiency.md (reconciliation ledger)
Language guidelines: projects/.ai-playbook/python_guidelines.md (driver and tests are Python)

## Terms

- **Recurrence group**: one entry on the session manifest's `recurrence_groups` line: a root issue shared by review findings across rounds, normalized per review-reconciliation "Reconciliation method" step 1 (violated invariant, data flow, owner, or missing witness; never finding id or wording).
- **Trigger instance**: a fired recurrence condition recorded on the `recurrence_groups` line with status `triggered`; it stays `triggered` until review-reconciliation has run for it and the ledger path is recorded.
- **Regeneration (defect in the prior fix)**: a blocking finding this round whose files intersect the changed files of `last_fix_commit`, the previous round's accepted-fix commit.
- **Archive gate receipt**: the machine-state object `archive_gate` written by the driver's terminal pre-archive stage after the eligibility predicate passes; carries the source active plan path, the declared destination, plan digest, commit identity, checklist, and timestamp. It is the prerequisite of the final terminal stage, which verifies the recorded source path is absent and the archived bytes still hash to the recorded digest.
- **Resolved plans-completed directory**: the destination path produced only by resolving the `plans_completed_dir` key from the opening TOML block of `.ai-playbook/facts.md` (via `scripts/facts_paths.py` `resolve_toml_key_raw` anchored at the driver's repository root, the pattern `doc_registry_validator.resolve_repo_relative_key` established for this exact key); never a path constructed from a folder name.
- **Clean-round sidecar**: the `.stats.json` sidecar of the Phase 3 code-review staging doc for the exit round (schema version 1, `source_kind: "code"`, `verdict` field, per-finding `blocking` flags, optional `last_fix_commit`).
- **Machine manifest**: `runtime_state.json` per runtime-contract.md; the session `manifest.md` is the human projection.

## Assumptions

- assume the authoring base is the post-efficiency skill state (the efficiency plan's skill and driver changes landed before authoring); basis: git log read 2026-09-18.
- assume the live budget-gate decision-table execution may still mutate the shared driver surfaces, so this plan's execution sequences after that run lands and re-verifies the Phase 3 and Phase 4 sections at its Phase 0 drift check; basis: that run's session directory under the resolved execute-plan tmp root exists (Phase 0 recorded 2026-09-18 14:19 local).
- assume recurrence tracking lives in the session manifest.md next to the existing review counters, not in machine state; basis: SKILL.md Phase 3 "Track in manifest.md" list design.
- assume the driver may read the clean-round sidecar at the terminal gate only and the readiness operation keeps its no-sidecar boundary; basis: SKILL.md readiness decision table scopes that rule to the readiness operation.
- assume destination resolution uses the repo-local scripts/facts_paths.py `resolve_toml_key_raw` for `plans_completed_dir`, anchored at the driver's repository root (the facts key lives in the TOML fence, which the table-row parser cannot read, and an unanchored relative value would resolve against the process CWD); a missing TOML key or missing directory refuses; basis: `.ai-playbook/facts.md` fence format and the `doc_registry_validator.resolve_repo_relative_key` precedent verified on disk 2026-09-18.
- assume the archive backlog origin (docs/history/backlog/2026-09-18-execute-plan-archive-before-task-completion.md) was committed during authoring by a peer session; execution must not modify it outside the promoted-backlog move in the archive commit; basis: git log on the origin path read 2026-09-18.

Decision points requiring a grill: recurrence evaluation placement: Step 3.2 evaluation with invocation gates at Step 3.5 plus a Step 3.1 pre-launch backstop, decision: standing pre-authorization accepting the composition of backlog Prevention 1's two allowed placements, source: authoring prompt 2026-09-18, affects Step 3.1, Step 3.2, Step 3.5; trigger condition shape: two mechanical arms (same normalized root group in two consecutive rounds, or blocking findings whose files intersect the last fix commit's changed files), decision: standing pre-authorization accepting backlog Prevention 1 with review-reconciliation's Trigger section, source: authoring prompt 2026-09-18, affects Step 3.2 and the recurrence_groups line; terminal staging shape: two-stage protocol, an eligibility gate receipt written before the move as the pre-move terminal-evidence proof and the final terminal receipt after the move naming the archived path (the accepted form of the origin's receipt-before-move ordering), decision: standing pre-authorization accepting archive origin Required behavior 2 ordering and regression fixture 4, source: authoring prompt 2026-09-18, affects Phase 4, Phase 5, the driver terminal operation, and the runtime contract; checker script: no new standalone recurrence checker, the manifest line plus prose gates plus the driver operation are the witnesses, decision: standing pre-authorization accepting the minimal option, source: authoring prompt 2026-09-18, affects Task 3; review-loop unchanged: the standalone interactive loop keeps its prose trigger, decision: standing pre-authorization accepting the origin's scope as the execute-plan orchestrator, source: authoring prompt 2026-09-18, affects Review Scope.

## Gist & Examples

Two process gaps in the execute-plan orchestrator, both evidenced by the efficiency execution's five-round wedge and stop (82540fd1):

1. **The reconciliation trigger fired but nothing evaluated it.** The review-reconciliation skill's trigger ("same root issue in two consecutive rounds", "a fix regenerates findings in the next round") was true from round 3 onward, but no Phase 3 step computes it, so an unattended orchestrator that fixes every finding each round experienced regeneration as ordinary progress. Reconciliation ran only after the five-round cap, on user request, and then found two representation-level root causes that five rounds of seam fixes never closed. The fix: a mechanical recurrence evaluation at Step 3.2 with a manifest witness, and invocation gates at Step 3.5 and Step 3.1 that refuse to launch another panel while a trigger instance has not run reconciliation.

   Example: round 4's blocking findings sit in code round 3's fix wrote, and one root group now appears in rounds 3 and 4. At Step 3.2 the orchestrator normalizes the findings, sees both arms, records `triggered` on the recurrence_groups line, finishes the round's own fix and done as usual, and at Step 3.5 invokes review-reconciliation before any round 5 panel; the ledger it produces replaces per-seam fixing with the representation fix.

2. **Archival had no gate before the move.** A run moved its plan into a folder named `plans_completed` while tasks were still unchecked, and the only existing check (the post-move completeness gate) plus the terminal receipt both run after the move, so a premature archive looked like completion. The fix: archival becomes one ordered, fail-closed transition owned by a machine predicate. The orchestrator runs the driver's terminal pre-archive stage before any move; the driver resolves the destination itself from facts, proves machine completion (tasks complete, checkboxes clean, no live claims), proves the clean-round sidecar evidence, and only then writes the archive gate receipt; the move to the echoed destination, the ownership-registry row, and the final terminal stage follow, and the final stage refuses unless the gate receipt exists and the archived file sits exactly at the declared destination with the source gone.

   Example: an archive attempt with a fully complete plan but candidate destination `plans_completed` is refused with `unsupported archive destination`, and nothing moves (fixture 1); a separate attempt with the correct destination but one unchecked task checkbox is refused with the unchecked-checkbox evidence instead, because active-plan integrity precedes the destination check in the fixed order (fixture 2). In both cases the machine manifest is unchanged and the active plan stays in place for recovery.

Code and prose change together because the ledger's G3 root cause is prose that restates code semantics: Phase 4 prose commands the driver operation instead of restating its checks, and the recurrence prose cites review-reconciliation's normalization method instead of duplicating it.

## Design Invariants (CR Guard)

- **Cite owners, never restate:** recurrence normalization is owned by review-reconciliation "Reconciliation method" step 1; execute-plan cites it. The archive predicate is owned by the driver's staged terminal operation and runtime-contract.md; Phase 4 prose commands it. (Ledger G3: prose restating behavior drifts again.)
- **Reconciliation skill ownership unchanged:** the design-reflection gate and the reset-only-after-fresh-review rule stay owned by review-reconciliation ("Return control to the original orchestrator"); execute-plan references them and does not weaken them.
- **Readiness boundary preserved:** the two existing driver-wide no-sidecar sentences are re-scoped to the readiness operation, with the terminal gate's clean-round sidecar read as the only documented extension; no unqualified driver-wide claim survives.
- **Minimal normal path:** one resolved destination, one ordered predicate, one terminal receipt; no recurring readiness review, no second review ceremony for ordinary task progression (archive origin "Proposed implementation").
- **Machine manifest authority unchanged:** the archive gate receipt lives in runtime_state.json under the manifest lock; manifest.md stays a projection; refusals preserve machine state exactly.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the ordered eligibility predicate refuses each failure mode with exactly the first failed condition and preserves machine state on every refusal; the archive origin's seven regression fixtures exist as named tests and pass
- consistency: every new skill obligation has a dedicated fail-closed validation probe; prose cites the owning section or script for normalization and predicate semantics
- minimality: no new standalone checker script, no second review ceremony; the diff touches only the listed surfaces
- hygiene: `scripts/check-no-em-dash.sh` and `scripts/scan-public-hygiene.sh` exit 0 over the touched surfaces; `scripts/plan_readiness.py` exit 0

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py` passes including the fourteen new test methods across Tasks 1 and 2 that together cover the archive origin's seven regression fixtures (fixtures 1 through 7 mapped across the two tasks)
- the full Validation Commands block passes

**Ship when:**
- execution of this plan is sequenced after the live budget-gate-decision-table run on the shared driver file lands (re-verified at execution Phase 0)
- deployed `$HOME/.ai-playbook/scripts` runtime copies refresh in the separate standing maintenance pass (not this plan's gate)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py`

**Tests:**
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. The Task 4 destination-hygiene sweep may produce plan-related fixes in `agents/skills/plans/SKILL.md` or `agents/skills/done/SKILL.md` where the sweep proves an archive destination constructed from the bare folder name; those fixes are in scope with a one-line justification.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-loop/SKILL.md`; standalone interactive loop, its rule 5 and exit criterion 5 already own the prose trigger, unchanged per the review-loop decision receipt
- `agents/skills/review-reconciliation/SKILL.md`; owns the normalization method and design-reflection gate, this plan consumes it and never edits it
- `scripts/execute_plan_resume_watcher.py`, `scripts/execute_plan_address_fanout.py`; budget and fan-out machinery untouched

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1

expect_match() {
  p="$1"; shift
  for f in "$@"; do
    if [ ! -f "$f" ]; then echo "FAIL: missing swept path $f"; exit 1; fi
    if ! grep -qF -- "$p" "$f"; then echo "FAIL: obligation missing in $f: $p"; exit 1; fi
  done
}

expect_no_match() {
  p="$1"; shift
  for f in "$@"; do
    if [ ! -f "$f" ]; then echo "FAIL: missing swept path $f"; exit 1; fi
  done
  rc=0
  grep -nE "$p" "$@" || rc=$?
  if [ "$rc" -ge 2 ]; then echo "FAIL: sweep tool error rc=$rc for $p"; exit 1; fi
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden pattern present: $p"; exit 1; fi
}

SK="agents/skills/execute-plan/SKILL.md"
SP="agents/skills/execute-plan/subagent-prompts.md"
RC="agents/skills/execute-plan/runtime-contract.md"

# 1. Driver suite, including the fourteen new Task 1/Task 2 test methods covering the archive origin's seven regression fixtures (fixtures 1-7)
python3 scripts/test_execute_plan_runtime.py || { echo "FAIL: driver suite"; exit 1; }

# 2. Recurrence mechanics obligations; one dedicated probe per obligation, spans quoted from Task 3
expect_match '- `recurrence_groups`;' "$SK"
expect_match "Recurrence evaluation (mechanical, every round)" "$SK"
expect_match "\"Reconciliation method\" step 1" "$SK"
expect_match "intersect the changed files of" "$SK"
expect_match "un-run triggered reconciliation instance" "$SK"
expect_match "evaluated mechanically every round" "$SK"
expect_match "in-loop before the next panel" "$SK"
expect_match "relay the recurrence status line verbatim" "$SP"

# 3. Archive lifecycle obligations; spans quoted from Task 4
expect_match '"stage": "pre-archive"' "$SK"
expect_match "declared_destination" "$SK"
expect_match "never construct the destination from a folder name" "$SK"
expect_match "doc_registry_validator.py validate" "$SK"
expect_match "final terminal stage" "$SK"
expect_match "unsupported archive location" "$SK"
expect_match "without a gate receipt" "$SK"
expect_match "the readiness operation never reads review sidecars" "$SK"
expect_match "the readiness operation never reads review sidecars" "$RC"
expect_match "archive_gate" "$RC"
expect_match "evaluates in one fixed order" "$RC"
expect_match "terminal-gate-only" "$RC"

# 4. Destination hygiene: no archive path constructed from the bare folder name in lifecycle surfaces
#    (the underscore form plans_completed_dir is the resolved key and is fine)
expect_no_match 'plans_completed([^_]|$)' "$SK" "$SP" "$RC" "scripts/execute_plan_runtime.py"

# 5. Authoring hygiene over the touched surfaces and this plan
#    CHECK_NO_EM_DASH_ALL=1 extends the scan past the prose-extension filter, so the .py surfaces are really scanned
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file "$SK" "$SP" "$RC" "scripts/execute_plan_runtime.py" "scripts/test_execute_plan_runtime.py" || { echo "FAIL: em dash present"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "FAIL: public hygiene scan"; exit 1; }
```

### Task 1: Driver terminal pre-archive eligibility stage (fixtures 1, 2, 3 and the pre-move half of fixture 5)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `ArchiveGatePreArchiveTest#test_refuses_lookalike_destination`; given a fixture facts file in the real TOML-fence format resolving `docs/plans/completed/` and a pre-archive input naming candidate destination `plans_completed/`, expects blocked `done-pending` with evidence naming `unsupported archive destination`, machine manifest bytes unchanged, and the active plan file still present at its active path (fixture 1)
- [x] `ArchiveGatePreArchiveTest#test_refuses_unchecked_plan_checkbox`; given a manifest whose tasks are all complete but whose active plan still carries one `- [ ]` line, expects blocked with evidence naming the unchecked checkbox and its line number, manifest unchanged (fixture 2)
- [x] `ArchiveGatePreArchiveTest#test_refuses_incomplete_machine_tasks`; given a manifest with one task not complete, expects blocked naming the incomplete task before any file or destination check runs (fixture 2, machine half)
- [x] `ArchiveGatePreArchiveTest#test_refuses_foreign_plan_path`; given a manifest whose `plan_slug` names this run's plan and a supplied active plan path that is complete, checkbox-clean, sits under the resolved plans directory, but whose filename does not match `plan_slug`, expects blocked with evidence naming the plan-identity mismatch (backlog origin Required behavior 1's source-binding guard)
- [x] `ArchiveGatePreArchiveTest#test_refuses_missing_or_unclean_review_sidecar`; given a sidecar path that is missing, or a sidecar with a present non-`"yes"` `verdict` (`"no"`, `"maybe"`), or a sidecar carrying a `"blocking": true` findings row, or a well-formed version-1 sidecar with `source_kind` `"plan"` (the plan-review sibling a directory mixup would supply), or a sidecar missing `schema_version`, expects blocked in all sub-cases (six shapes, including a non-boolean blocking row) naming the clean-round review evidence condition (fixture 3); a sidecar with no `verdict` key is accepted instead (r3 CC3-1: the review-staging schema makes the verdict optional, so an absent verdict falls through to the blocking-rows check; witnessed by `test_accepts_sidecar_without_verdict_key`)
- [x] `ArchiveGatePreArchiveTest#test_refuses_stale_last_fix_commit`; given a clean sidecar whose `last_fix_commit` is not an ancestor-or-self of HEAD, expects blocked naming the review freshness condition (fixture 3, freshness half)
- [x] `ArchiveGatePreArchiveTest#test_success_writes_gate_receipt_and_stays_active`; given complete machine tasks, zero unchecked boxes, a clean sidecar, a provable commit, and no candidate destination, expects success: `archive_gate` recorded with the facts-resolved `declared_destination`, the plan sha256 digest, commit identity, checklist, and timestamp; `workflow_state` stays `active`; no `terminal_receipt` exists (fixture 5, pre-move half)
- [x] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py`; the new class fails because the terminal operation has no `pre-archive` stage, and the existing suite stays green
- [x] Implement: extend the `terminal` operation with a `stage` field accepting `pre-archive` and `final`, default `final`, which preserves today's input contract. The `pre-archive` input carries the active `plan_path`, an optional candidate `destination`, the `review_sidecar` path, `last_commit_sha`, and `phase5_checklist`. The predicate evaluates in one fixed order and returns the first failure only, as blocked `done-pending`, leaving the manifest untouched: (1) machine completeness: non-empty task map, every task complete via the existing completeness helper, every claim record closed, no pending done handoff; (2) active-plan integrity and identity: the plan path resolves under the resolved `{plans_dir}` through the fail-closed path policy, and its filename must match the manifest's `plan_slug` (`<plan_slug>.md`; when a watcher record with a canonical plan path exists, it must equal that path too), refusing a foreign plan with evidence naming the identity mismatch; then it reads under the bounded-read policy and carries zero line-anchored unchecked checkbox lines; a path under any other directory is refused with `unsupported archive location` naming the path; (3) destination: resolve `plans_completed_dir` via `facts_paths.resolve_toml_key_raw` anchored at the driver's repository root (never the table-row parser: this repo's facts store the key in the TOML fence), refuse a missing key or a non-existent directory, and refuse a supplied candidate that differs from the resolved destination with `unsupported archive destination`; (4) clean-round sidecar: resolve the supplied `review_sidecar` path through the same fail-closed path policy before opening it, then parse schema version 1, require `source_kind` `"code"`, `verdict` `"yes"`, zero findings rows with `"blocking": true`, and `last_fix_commit` ancestor-or-self of HEAD when non-null, the ancestry check running through an injectable helper beside the existing `commit_lookup` seam so fixture roots without a git repository can stub it; (5) commit identity via the existing `commit_lookup`. On success write `archive_gate` (`plan_path` recording the source active plan path, `declared_destination`, `plan_digest`, `last_commit_sha`, `phase5_checklist`, `recorded_at`) under the manifest lock; re-running the pre-archive stage overwrites the gate receipt in place with the identity fields stable and `recorded_at` refreshed; never set `workflow_state` and never write `terminal_receipt` at this stage. The eligibility predicate and the final-stage checks of Task 2 are implemented as two named helpers so the terminal operation stays a small dispatcher
- [x] Run → expect GREEN: the new class passes and the full suite passes
- [x] Commit: `scripts: execute-plan driver pre-archive eligibility stage`

### Task 2: Driver terminal final-stage hardening and relocation detection (fixtures 4, 6, 7 and the post-move half of fixture 5)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `TerminalFinalStageTest#test_refuses_without_gate_receipt`; given a complete manifest whose plan already sits at the resolved destination but with no `archive_gate` receipt, expects blocked `done-pending` naming the missing pre-archive gate with `workflow_state` still active (fixture 4)
- [x] `TerminalFinalStageTest#test_refuses_archived_path_mismatch`; given a gate receipt whose `declared_destination` differs from the supplied archived path, expects blocked naming the destination mismatch
- [x] `TerminalFinalStageTest#test_refuses_source_still_present`; given the source plan path recorded in the gate receipt still exists on the filesystem after the supposed move, expects blocked naming the source-present condition (fixture 5, post-move half)
- [x] `TerminalFinalStageTest#test_refuses_archived_content_drift`; given archived bytes whose sha256 differs from the gate receipt's `plan_digest`, expects blocked `done-pending` naming the digest mismatch with the manifest unchanged
- [x] `TerminalFinalStageTest#test_success_records_exact_destination_and_digest`; given the full happy path, expects `workflow_state` `complete` with the receipt's `archived_plan_path` equal to the gate's `declared_destination` and the receipt carrying the gate digest after the final stage verified the archived bytes hash to it (fixture 5)
- [x] `ArchiveLocationTest#test_reports_unsupported_sibling_location`; given the active plan placed under a completed-folder-like sibling that is neither the resolved plans directory nor the resolved completed directory, the pre-archive stage expects blocked naming `unsupported archive location` with the offending path (fixture 7)
- [x] `TerminalResumeTest#test_interrupted_run_resumes_without_double_archive`; given a manifest with a gate receipt but no move performed, the resume/continuation path keeps `workflow_state` active, leaves task claims intact, and a repeated pre-archive call succeeds with the identity fields (`declared_destination`, `plan_digest`, `last_commit_sha`) unchanged while `recorded_at` may advance (fixture 6)
- [x] Run → expect RED for all five `TerminalFinalStageTest` cases (the four refusals plus the success case, whose receipt cannot carry a gate digest yet); the resume case and `ArchiveLocationTest` pass on Task 1 behavior (Task 1 already delivers the in-place gate overwrite with stable identity fields); Task 1 class stays green; record the observed failing set
- [x] Implement: the final stage requires `archive_gate` present, requires the supplied archived path to equal `archive_gate.declared_destination` exactly, verifies the gate-recorded source plan path (`archive_gate.plan_path`) is absent from the filesystem, recomputes the archived file's digest and refuses `done-pending` when it differs from `archive_gate.plan_digest`, and then runs today's archived-plan checks; the terminal receipt gains `plan_digest` from the gate record only after that equality held; refusals keep today's state-preservation behavior. The two stages live in the named helpers Task 1 introduces, keeping the terminal operation a dispatcher
- [x] Migrate the existing terminal fixtures: add a helper seeding a conforming `archive_gate` receipt (declared destination equal to the archived fixture path, digest over the fixture bytes, source path pointing at the absent active path) and move the existing `mark_terminal` success and refusal call sites onto it; update the existing refusal fixtures' expected evidence to the new gate-first order; add one ordering assertion that an incomplete and gateless manifest is refused with the machine-completeness evidence before any gate clause, so the prescribed gate-first order cannot be silently inverted to keep old assertions green
- [x] Run → expect GREEN: the full suite passes
- [x] Commit: `scripts: execute-plan staged terminal gate with archive safety`

### Task 3: Phase 3 recurrence mechanics prose

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

- [x] In the Phase 3 "Track in manifest.md" list add the exact bullet `- `recurrence_groups`; the per-round recurrence ledger and trigger status written by the Step 3.2 recurrence evaluation`, in the backticked counter style of the sibling bullets
- [x] Append to Step 3.2 a subsection headed `##### Recurrence evaluation (mechanical, every round)` with exactly this contract: normalize each unresolved blocking finding in the current staging doc to a root group per review-reconciliation `"Reconciliation method" step 1`; update the `recurrence_groups` manifest line with one entry per group carrying the normalized root, the rounds it appeared in, and the change relation; the evaluation runs every round, where round 1 records groups without comparing because no prior round's line exists, and from round 2 on the comparison runs against the previous round's recorded groups; the trigger fires when the same root group appears in two consecutive rounds, or when any blocking finding's files intersect the changed files of `last_fix_commit` (`git show --name-only --pretty=format: <sha>`); record the trigger status `triggered` with the group names, or `clear`, on the same line; state that the two mechanical arms are a witnessed subset, not a replacement, and shapes neither arm catches (cross-file regeneration under a brand-new root group, artifact contradiction, the configured cap) remain owned by the Step 3.5 reconciliation row
- [x] Rewrite the Step 3.5 reconciliation table row so the trigger is `evaluated mechanically every round` from the `recurrence_groups` line rather than only at the cap: when an instance is `triggered` and no reconciliation ledger path is recorded for it, invoke review-reconciliation in-loop before the next panel (the outstanding-ask wait still applies), record the ledger path on the `recurrence_groups` line, and return to Step 3.1 through the normal parent-orchestrated panel; reset the affected groups' counters only after the fresh post-reconciliation review completes clean, and when the same root group reappears after the reset, retain the recurrence chain and escalate per review-reconciliation "Return control to the original orchestrator"; keep the existing fix-risk and cap-row interactions unchanged
- [x] Add to Step 3.1 "Before launching": refuse to launch while the manifest records an `un-run triggered reconciliation instance`; run review-reconciliation first per Hard Gate 24, then relaunch
- [x] Reword Hard Gate 24 to state that the trigger is `evaluated mechanically every round` (Step 3.2) with the `recurrence_groups` manifest line as its witness, that invocation happens `in-loop before the next panel` and not only at the cap, and that the execute-plan parent remains the original orchestrator running the fresh normal panel after any reconciliation change
- [x] Update the Integration Point "Consumes review-reconciliation" to say Phase 3 evaluates the trigger mechanically at Step 3.2 with the manifest witness and invokes reconciliation in-loop at Step 3.5 before the next panel
- [x] In subagent-prompts.md "Done (per review iteration)", add to the Context block the line `Recurrence status: <verbatim recurrence_groups trigger status from manifest.md>` and a required-output rule that the done sub-agent must `relay the recurrence status line verbatim` as a structured signal the parent records at the Step 3.4 checkpoint (when the done sub-agent returns), reporting `recurrence status: none recorded` when manifest.md carries no `recurrence_groups` line
- [x] Run the recurrence obligation probes from Validation Commands section 2 → expect GREEN; the archive probes from sections 3 and 4 stay in their prior state at this task point
- [x] Commit: `skills: execute-plan mechanical recurrence trigger with manifest witness`

### Task 4: Archive lifecycle prose, staged terminal contract, hygiene sweep

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] Rewrite the Phase 4 intro to prescribe the ordered transition and stop at the first refused step: (1) run the driver's terminal pre-archive stage (`--operation terminal --stage pre-archive`) with the active plan path, the clean-round sidecar path, the last commit sha, and the Phase 5 checklist, and record the outcome in manifest.md; on a blocked outcome move nothing and resolve the `first failed condition` it names (execution deviation recorded in r1: the stage selects via the `--input` JSON payload field `"stage": "pre-archive"`; the driver has no `--stage` argparse flag); (2) perform `git mv` of the plan only to the `declared_destination` echoed by the pre-archive outcome, resolved by the driver from the facts key; add the sentence `never construct the destination from a folder name`; (3) in the same archive commit, append the ownership-registry row for the archived path in docs/maintenance/document-registry.md, run `python3 scripts/doc_registry_validator.py validate`, and move any promoted backlog origin item per the existing promoted-backlog rule; the origin's registry-exactly-once clause is owned by this commit-granularity step plus the validator run (a resumed archive re-enters the ordered transition and appends no second row because the append lives only in the one archive commit), and the absence of a dedicated row-count fixture is a recorded residual
- [x] Keep the existing post-move archive completeness gate (UL#193) and Step 4.1 unchanged
- [x] In Phase 4's closing and Phase 5's terminal receipt paragraph, prescribe the `final terminal stage`: after the archive commit, call the terminal operation at its default final stage with the archived path and last commit sha, and re-read the receipt, which now also carries the gate's plan digest; align the Phase 5 success checklist wording to the resolved completed path (execution deviations recorded in r2/r3: the final stage requires the Phase 5 checklist input, and the gate fields are confirmed by re-reading the manifest's terminal_receipt or a follow-up resume/continue call, not from the success stdout)
- [x] Add a Recovery subsection `Bad-archive recovery (path-integrity failure)`: when the active plan is missing from its resolved plans directory or sits outside it, run the pre-archive stage with the suspected path so the blocked reason (`unsupported archive location`) names the offending path; `record the relocation` in manifest.md, restore the plan to the supported active or completed path according to its actual evidence, treat a move performed `without a gate receipt` as unsupported (the plan stays active and the ordered transition re-runs), and never delete the plan or rewrite its body to hide the lifecycle error
- [x] In runtime-contract.md, add a `Staged terminal operation (archive gate)` section documenting the two stages, the `archive_gate` receipt fields (including the recorded source plan path), a clause that the predicate `evaluates in one fixed order` and returns the `first failed condition` only, the state-preservation rule on refusal, and the sentence that the terminal operation reads the clean-round review sidecar as a `terminal-gate-only` boundary extension; in the same file amend the existing readiness-section sentence `the driver never reads review sidecars` to the exact wording `the readiness operation never reads review sidecars; the terminal gate's clean-round sidecar read is the only documented extension`
- [x] In SKILL.md, amend the readiness decision table's unqualified `the driver never reads review sidecars` sentence to the same exact wording `the readiness operation never reads review sidecars; the terminal gate's clean-round sidecar read is the only documented extension`, and update the Runtime-neutral execution contract's Terminal-response gate paragraph and the orchestration state table `terminal` row for the staged call shape (the pre-archive stage before the move, the final stage after it) and the receipt's `plan_digest` field
- [x] Run the Task 4 destination-hygiene sweep: `grep -rnE 'plans_completed([^_]|$)' agents/skills/execute-plan agents/skills/plans agents/skills/done scripts/execute_plan_runtime.py`; fix any archive destination constructed from the bare folder name (execute-plan surfaces in this task; plans/done hits as plan-related fixes with a one-line justification or a backlog capture), leaving zero hits
- [x] Extract the Validation Commands bash block from this plan file, run `bash -n` on it, and execute it → expect GREEN on the full block (suite, all obligation probes, hygiene sweep)
- [x] Commit: `skills: execute-plan archive lifecycle gate and staged terminal contract`
