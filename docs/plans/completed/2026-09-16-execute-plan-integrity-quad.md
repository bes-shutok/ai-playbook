# Plan: execute-plan integrity: readiness, ownership, evidence, terminal completion

Backlog origins (scope of record, all HIGH):
- `docs/history/backlog/2026-09-16-execute-plan-conditional-readiness-gate.md`
- `docs/history/backlog/2026-09-16-execute-plan-interrupted-task-ownership-recovery.md`
- `docs/history/backlog/2026-09-16-execute-plan-review-evidence-and-manifest-gate.md`
- `docs/history/backlog/2026-09-16-execute-plan-terminal-completion-integrity.md`

## Terms

- **Machine manifest**: `{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json`; the single writable execution-state source, owned by the driver.
- **Direct continuation**: resuming the next task without a new whole-plan readiness review because every gate condition still holds.
- **Readiness review**: a fresh `review-plan` round whose sidecar digest covers the current plan bytes (enforced by the Step 0.5 validator).
- **Claim lease**: the maximum age a worker claim may reach before the driver treats the owner as provably gone and permits a reclaim.
- **Orchestration state**: the run-level state name (active, needs-review, needs-fix, paused, waiting-for-capacity, recovering, terminal) derived from machine state plus durable artifacts; never a second writable record.
- **Terminal receipt**: the driver-verified record of `workflow_state: complete` with the archived-plan path, last commit identity, and Phase 5 checklist.
- **Worker receipt**: the normalized result one worker returned; evidence only, never a checkbox or pointer advance by itself.

## Assumptions

- assume plan surfaces are the five files in Review Scope; basis: the P2 conversion note surfaces line (`docs/tmp/future-plan-prompts-2026-09-16.md`) plus each origin's ownership section assigning other skills' parts to their own owners.
- assume origin 3 coverage-state and digest-freshness requirements are already landed (coverage outcome enum in `review-staging` and `scripts/validate_review_staging.py`, commit 2959367b; digest gate in `scripts/plan_readiness.py`); this plan only adds the execute-plan-side refusal wording and the machine terminal predicate; basis: source probes from the authoring session recorded in `docs/tmp/plan-requirements-execute-plan-integrity-quad.md`.
- assume the machine `workflow_state` enum stays `{active, blocked, complete, terminal, aborted}`; the richer orchestration state names are derived, documented states; basis: the runtime contract's single-machine-source rule and the absence of a witnessed failure needing new enum values.
- assume the driver stays standard-library-only and the new operations reuse the manifest lock, generation fencing, and the injectable `clock` and `commit_lookup` seams; basis: the Durable driver boundary section of `runtime-contract.md` and the verified constructor signature.
- assume the runtime-neutrality baseline failure is in scope as Task 1 because this plan's Validation Commands run that suite; basis: authoring-session probe, the suite fails on the committed tree because the plans skill Budget gate Boundaries paragraph names a specific agent runtime product, introduced by commit f482c5ad.
- assume no new Python dependencies and no new files beyond this plan; basis: driver standard-library constraint and the documented surface set.

Decision points requiring a grill: orchestration-state representation: derived documented states over new machine enum values (decision: standing pre-authorization to accept recommended options plus the runtime contract single-machine-source rule; 2026-09-16; affected: Assumptions, Gist, Task 4); quad compartmentalization: execute-plan surfaces only, other skills' asks recorded as out of scope with owners (decision: standing pre-authorization plus the P2 surfaces note; 2026-09-16; affected: Review Scope, Gist); reclaim precondition: lease-expiry-only over process-liveness proof for worker claims (decision: standing pre-authorization; basis: worker claim records carry token, generation, owner, and timestamp but no process identity, so lease expiry is the only machine-provable precondition; 2026-09-16; affected: Task 3, runtime-contract edits).

## Gist & Examples

The execute-plan workflow already owns a durable driver, a readiness validator, and a review loop, but four witnessed failures show the orchestration layer can still mis-decide transitions. This plan makes each transition decidable: two new driver operations, three skill-level tables (the readiness decision table, the interruption state table, and the orchestration state table), and one machine terminal predicate.

**Origin-to-task traceability** (the machinery test: every gate traces to a witnessed failure):

| Origin witness | Gap today | Task |
|---|---|---|
| Runners launched before a plan amendment reported against an older digest; no compact rule decided when a fresh readiness review was needed; repeated review work before the next task could be claimed | Step 0.5 has a narrow checkbox-only resume exemption; no decision table; manifest-owned conditions are not machine-checkable | Task 2 |
| A wait for an implement worker was interrupted by user input while the worker stayed live; earlier recovery hit plan/manifest disagreement and a path that could not advance without the adapter | The User Interruption section is thin report-and-preserve prose; no worker-claim reclaim exists, so a provably abandoned claim wedges the task | Task 3 |
| Green-looking summaries without proving the current plan, the intended test, or a successful outcome; a stale review treated as fresh after plan mutations | Repo-local coverage-state and digest-freshness parts already landed; the execute-plan-owned refusal at the terminal boundary is prose-only | Task 4 |
| A run reached a non-terminal state and was reported finished; async reviewer notifications were still able to arrive after the response; the machine progress record advanced farther than plan checkboxes justified | The terminal receipt validates argument shapes only: no archived-plan existence, no checkbox scan, no commit provability; no named orchestration state table; no async-join rule | Task 4 |

**Before (today):** an execute-plan run is interrupted while a Task 3 implement worker is live. The user asks for status. The orchestrator has no compact rule: it may launch a duplicate worker for the claimed task, or re-run a whole-plan readiness review although the digest and manifest are unchanged, and a provably abandoned claim (worker died without a result) can never be released because no reclaim path exists. At the end, the terminal receipt accepts an archived-plan path that does not exist, a plan whose checkboxes are unchecked, and a commit identity nothing proved.

**After (this plan):** the same interruption calls the driver `readiness` operation, which returns `observe-worker` naming the live claim, so the orchestrator re-observes the same worker handle with a bounded repeatable wait instead of launching anything. A claim older than the claim lease is released by the `reclaim` operation through a compare-and-swap that preserves checkpoint evidence. A final response is allowed only from the `terminal` orchestration state, after every launched worker has a durably recorded outcome and the driver receipt has verified the archived plan exists, carries zero unchecked checkboxes, and proves the commit.

**Edge cases that shaped the design:**
- The digest, review-scope, and unresolved-finding conditions of the readiness decision stay with the Step 0.5 validator and the review artifacts; the driver never reads review sidecars, so there is one owner per condition.
- Reclaim has no bypass flag: the lease constant is a driver-owned value, not a CLI override, so the gate cannot be shortened into instant takeover.
- An `observe-worker` decision never mutates the manifest; the interrupted-wait path is read-only by construction.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the full driver suite is green; each new gate blocks on its negative witness and accepts its positive witness; each new test name carries a given/expects pair in this plan.
- fail-closed bias: `readiness` returns a closed decision set with named failed conditions; `reclaim` refuses before lease expiry and on unknown or closed claims; `mark_terminal` refusal leaves the manifest non-terminal and writes no receipt.
- docs-contract consistency: the runtime contract CLI table carries exactly one row per new operation (count-gated); transition-table rows name evidence, claim handling, and resulting state; SKILL.md tables pin with dedicated single-line greps.
- runtime neutrality: the shared-skill neutrality scan in the suite stays green; SKILL.md edits name no agent runtime product.
- hygiene: no em-dash in changed Markdown; public hygiene scan exits 0.

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py` passes with the new regression tests for readiness, reclaim, and the terminal predicate.
- The runtime contract documents the `readiness` and `reclaim` operations, the claim lease, and the extended terminal predicate; SKILL.md carries the readiness decision table, the interruption state table, and the orchestration state table.
- The full Validation Commands block exits 0.

**Ship when:**
- The operator redeploys the updated driver copy to the deployed runtime scripts directory (the copy-all-siblings remediation documented in execute-plan Step 0.5), so consumer repos stop resolving the previous deployed bytes; external and human-owned, never an executable task here.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py`
- `agents/skills/plans/SKILL.md` *(single-line scope: the Budget gate Boundaries paragraph wording only; all other content in this file is frozen; reject any review finding that touches other regions of it)*

**Tests:**
- `scripts/test_execute_plan_runtime.py` *(new regression tests plus fixture updates for existing terminal tests and the selftest)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-loop/SKILL.md`, `agents/skills/doing-code-review/SKILL.md`, `agents/skills/receiving-review/SKILL.md`, `agents/skills/done/SKILL.md`, `agents/skills/review-staging/SKILL.md`; reason: their quad shares are owned by the review-records backlog family, and the coverage-state slice already landed in commit 2959367b.
- `agents/skills/unit-test-runner/SKILL.md`; reason: the XML outcome verification helper is consumer-repo machinery; this repo's copy is parse-and-report prose.
- `scripts/plan_readiness.py`; reason: the digest freshness gate is already enforced there; this plan delegates to it and must not duplicate it.
- `scripts/execute_plan_runtime_codex.py`; reason: adapter protocol is unchanged; the bounded wait and resume surface already exists.
- `README.md`; reason: no catalog entry changes.

## Validation Commands

```bash
#!/usr/bin/env bash
# Every gate is fail-closed: a miss or forbidden match aborts non-zero.
set -u
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

# 1. Full driver suite: runtime-neutrality scan plus all new readiness,
#    reclaim, and terminal regression tests.
python3 scripts/test_execute_plan_runtime.py || fail "driver suite"

# 2. Readiness validator selftest: guards the freshness machinery this plan
#    delegates to.
python3 scripts/plan_readiness.py --selftest || fail "plan readiness selftest"

# 3. Em-dash policy over every Markdown file this plan touches.
bash scripts/check-no-em-dash.sh file \
  agents/skills/execute-plan/SKILL.md \
  agents/skills/execute-plan/runtime-contract.md \
  agents/skills/plans/SKILL.md || fail "em-dash scan"

# 4. Public hygiene scan, anchored to the repo root because the scanner
#    resolves its scan root from the invocation cwd.
HYG_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
( cd "$HYG_TOP" && bash scripts/scan-public-hygiene.sh ) || fail "hygiene scan"

# 5. Dedicated structural gates: one grep per obligation, each fails when
#    THAT obligation is absent. Pins are single-line spans; keep every pinned
#    line single-line in the target file.
EP_SKILL=agents/skills/execute-plan/SKILL.md
EP_CONTRACT=agents/skills/execute-plan/runtime-contract.md
DRIVER=scripts/execute_plan_runtime.py
TESTS=scripts/test_execute_plan_runtime.py

grep -qF '### Readiness decision table' "$EP_SKILL" || fail "readiness decision table heading"
grep -qF 'never re-runs the whole-plan readiness review between ordinary task transitions' "$EP_SKILL" || fail "readiness liveness line"
grep -qF '### Interruption state table' "$EP_SKILL" || fail "interruption state table heading"
grep -qF 're-observe the same worker handle' "$EP_SKILL" || fail "observe-same-worker rule"
grep -qF '### Orchestration state table' "$EP_SKILL" || fail "orchestration state table heading"
for STATE in needs-review needs-fix waiting-for-capacity recovering; do
  grep -qF "$STATE" "$EP_SKILL" || fail "orchestration state $STATE missing"
done
grep -qF 'lacks a durably recorded outcome' "$EP_SKILL" || fail "async-join rule"
grep -qF 'refuses completion when review freshness or verification evidence is invalid' "$EP_SKILL" || fail "terminal evidence-refusal rule"
grep -qF '| `readiness` |' "$EP_CONTRACT" || fail "readiness CLI table row"
grep -qF '| `reclaim` |' "$EP_CONTRACT" || fail "reclaim CLI table row"
grep -qF 'zero unchecked' "$EP_CONTRACT" || fail "terminal checkbox predicate"
grep -qF 'claim lease' "$EP_CONTRACT" || fail "claim lease documentation"
grep -qF 'def _operation_readiness' "$DRIVER" || fail "readiness CLI operation"
grep -qF 'def _operation_reclaim' "$DRIVER" || fail "reclaim CLI operation"
grep -qF 'CLAIM_LEASE_SECONDS' "$DRIVER" || fail "claim lease constant"
grep -qF 'test_readiness_direct_continuation_on_fresh_manifest' "$TESTS" || fail "readiness happy-path test"
grep -qF 'test_reclaim_releases_expired_claim' "$TESTS" || fail "reclaim lease test"
grep -qF 'test_terminal_refuses_unchecked_plan_checkboxes' "$TESTS" || fail "terminal checkbox test"

# 6. Exactly-once count gates for the new contract table rows.
test "$(grep -oF '| `readiness` |' "$EP_CONTRACT" | wc -l)" -eq 1 || fail "readiness row count"
test "$(grep -oF '| `reclaim` |' "$EP_CONTRACT" | wc -l)" -eq 1 || fail "reclaim row count"

echo "validation: all gates green"
```

### Task 1: Repair the shared-skill runtime-neutrality regression

Files:
- `agents/skills/plans/SKILL.md` *(the Budget gate Boundaries paragraph only)*

- [x] `ExecutePlanRuntimeTest#test_shared_skill_bodies_remain_runtime_neutral`; given the committed plans skill Budget gate Boundaries paragraph naming a specific agent runtime product, expects the shared-skill neutrality scan to pass; today it fails because that paragraph names one runtime product as pending its first-start trust-prompt approval
- [x] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral` fails on the committed tree (exactly one suite failure today; every other test green)
- [x] Reword the Boundaries paragraph to name no runtime product, for example "fixture-verified on one agent runtime; on other runtimes pending the first-start trust-prompt approval and the envelope drive, see the budget-guard README", preserving the sentence's meaning; touch nothing else in the file
- [x] Run → expect GREEN: the single-test command passes
- [x] Run → expect GREEN: the full suite passes (136 tests at authoring time; the suite may have grown since, so only the zero-failure outcome is the gate)
- [x] Commit: `test: restore runtime-neutrality scan over shared skill bodies`

### Task 2: Conditional readiness decision machinery (origin 1)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `ExecutePlanRuntimeTest#test_readiness_direct_continuation_on_fresh_manifest`; given a seeded active manifest with every task pending and an agreeing plan file, expects the `readiness` operation to return decision `direct-continuation`, the first task id as the provable next task, and an empty failed-conditions list
- [x] `ExecutePlanRuntimeTest#test_readiness_observes_live_claim`; given a manifest with one launched claim, expects decision `observe-worker` naming that task id, and expects the claim token, generation, and task status to be byte-identical after the call
- [x] `ExecutePlanRuntimeTest#test_readiness_recovery_on_done_pending`; given a manifest with a task in done-pending, expects decision `recovery` and a failed condition naming the unresolved done handoff
- [x] `ExecutePlanRuntimeTest#test_readiness_recovery_on_plan_manifest_disagreement`; given a partially checked plan task (some boxes checked, one line unchecked) while the manifest records that task complete, expects decision `recovery` with a failed condition naming plan-manifest disagreement and the recovery action of correcting the plan through the skill-gated plan-edit step
- [x] `ExecutePlanRuntimeTest#test_readiness_recovery_on_blocked_state`; given `workflow_state: blocked` with no claim in state claimed or launched, expects decision `recovery` naming the machine state as the failed condition, whatever the task statuses are
- [x] `ExecutePlanRuntimeTest#test_readiness_refuses_aborted_workflow`; given `workflow_state: aborted` with otherwise clean pending tasks, expects decision `recovery` with a failed condition naming the machine state and a stop-or-recovery action
- [x] `ExecutePlanRuntimeTest#test_readiness_terminal_path_when_all_complete`; given every task complete, whether `workflow_state` is active or already complete, expects decision `terminal-path`
- [x] `ExecutePlanRuntimeTest#test_readiness_cli_requires_plan`; given the CLI invoked with `--operation readiness` and no `--plan`, expects a non-zero exit and the manifest unmutated
- [x] `ExecutePlanRuntimeTest#test_readiness_never_mutates_manifest`; given the direct-continuation and the recovery fixtures, expects the manifest file bytes byte-identical before and after the call
- [x] Run → expect RED: the full suite fails only on the new tests (the operation does not exist yet: an argparse `SystemExit` or an `AttributeError`), every pre-existing test green
- [x] Implement the `readiness` driver method and `_operation_readiness` CLI operation: load and validate the machine manifest (fail closed on missing or malformed), require `--plan`, evaluate exactly four machine-owned conditions: (a) manifest schema and ownership validation passes and `workflow_state` is `active` (an already `complete` manifest is handled first by the terminal-path decision; `aborted` or `blocked` is a failed condition naming the machine state with a stop-or-recovery action), (b) no unresolved handoff or fenced claim exists (no task in done-pending or commit-pending, no claim in state blocked), (c) for each manifest task the manifest records in the progressed set `{done-pending, commit-pending, checkpointed, complete}`, the plan's matching `### Task <N>` section (the id suffix after `task-`; the heading line matches `### Task <N>:` with the number terminated by its colon, so the Task 1 section never scans Task 10's heading or content) contains no unchecked checkbox line; any unchecked line there is disagreement, with the manifest winning per the seeding boundary, while a pending task's unchecked boxes agree with the manifest, (d) the next incomplete task is provable; return the closed decision set `direct-continuation`, `observe-worker`, `recovery`, `terminal-path`, evaluating decisions in the fixed order terminal-path (fires only when every task is complete or checkpointed and `workflow_state` is `active`, `complete`, or `terminal`), observe-worker (a claim in state claimed or launched on a task not in the progressed set), recovery (any failed condition otherwise), direct-continuation (all four conditions pass); evaluate all four conditions against one manifest snapshot read under the manifest lock, released before returning, and never mutate the manifest; digest, review-scope, and unresolved-finding conditions stay delegated to the Step 0.5 validator and review artifacts
- [x] Run → expect GREEN: the full suite passes
- [x] `runtime-contract.md`: add the `| \`readiness\` |` row to the CLI operation table (exactly one row) and a readiness decision subsection documenting the closed decision set and its fixed evaluation order, the four machine-owned conditions including the machine `workflow_state` requirement with the plan-section parsing contract, the progressed set, the locked one-snapshot consistency model, and the explicit delegation of digest, review-scope, and unresolved-finding conditions
- [x] `SKILL.md`: add the `### Readiness decision table` subsection at Step 0.5 mapping every origin trigger (changed digest, inconsistent manifest, unresolved blocker, review-scope boundary crossed, next task unprovable) to its owning mechanism and the direct-continuation conditions, including the line that the workflow never re-runs the whole-plan readiness review between ordinary task transitions while those conditions hold
- [x] Commit: `feat: execute-plan conditional readiness decision machinery`

### Task 3: Interrupted-claim ownership recovery (origin 2)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `ExecutePlanRuntimeTest#test_reclaim_blocked_before_lease_expiry`; given a launched claim with a fresh timestamp, expects the `reclaim` operation to return blocked with reason `stale-claim` and the claim token, generation, and task status unchanged
- [x] `ExecutePlanRuntimeTest#test_reclaim_releases_expired_claim`; given the same claim with its timestamp backdated past `CLAIM_LEASE_SECONDS`, expects reclaim to succeed, set the task back to pending, mark the replaced claim `replaced` with a rotated token and generation, preserve prior checkpoint records, and leave every other task and claim untouched; a subsequent `claim_next_task` succeeds claiming the freed task under the replacement generation, and the original claim token no longer passes claim-identity checks
- [x] `ExecutePlanRuntimeTest#test_reclaim_unknown_task_fails_closed`; given a task id with no live claim, expects blocked with reason `stale-claim` and the manifest unmutated
- [x] `ExecutePlanRuntimeTest#test_reclaim_refuses_progressed_task`; given an expired claim whose task is in the progressed set (done-pending), expects blocked with reason `stale-claim` and the task status and checkpoint records unchanged
- [x] `ExecutePlanRuntimeTest#test_reclaim_preserves_other_claims`; given an expired claim on one task and a live claim on another, expects reclaim on the expired task to leave the live claim byte-identical
- [x] Run → expect RED: the full suite fails only on the new tests (the operation does not exist yet), every pre-existing test green
- [x] Implement the `reclaim` driver method and `_operation_reclaim` CLI operation (`--operation reclaim --task-id <id>`): under the manifest lock, admit only a claim in `{claimed, launched, blocked}` on a task not in the progressed set `{done-pending, commit-pending, checkpointed, complete}`, whose `timestamp` is at least `CLAIM_LEASE_SECONDS` (14400, four hours, an order of magnitude above the execute-plan 20-minute per-worker timeout so a live worker's task normally completes well inside the lease; the claim timestamp is written once and never renewed, so a task still running past the lease has its post-reclaim checkpoint fail fenced as owner-mismatch rather than corrupting state) old using the injectable clock, then compare-and-swap the release: replace the claim generation and token and mark it `replaced` (the resume path's recycle pattern), set the task status back to pending, preserve recorded checkpoints as evidence; refuse before expiry, on unknown tasks, on closed, replaced, or aborted claims, and on progressed tasks; the constant is driver-owned code with no environment or CLI override, so the no-bypass property covers more than the flag surface
- [x] Run → expect GREEN: the full suite passes
- [x] `runtime-contract.md`: add the `| \`reclaim\` |` CLI table row (exactly one row), a transition-table row for the reclaim event naming required evidence (expired claim lease on a claim in claimed, launched, or blocked with the task outside the progressed set), claim handling (replace generation and token, mark the old claim replaced, task back to pending, checkpoints preserved), the resulting state, a zero retry budget, and the recovery action, plus the claim lease constant with its value, basis, and fail-closed no-override reading
- [x] `SKILL.md`: replace the User Interruption section body with the `### Interruption state table`: wait cancelled with the worker possibly live means re-observe the same worker handle with a bounded repeatable wait and leave claim and task identity unchanged; worker returned means the receipt records only what returned and never advances a checkbox or pointer by itself; failed, partial, timed-out, cancelled, and adapter-unavailable outcomes each name one resumable next action; reclaim goes only through the driver `reclaim` operation after lease expiry; a retry preserves plan digest and task identity; unchanged digest, manifest validity, review scope, and findings state route to direct continuation per the readiness decision table; keep the existing true guidance (report the current task, unchecked items, and last per-task done commit, and call out work that exists only uncommitted; never mark incomplete work as `[x]`; preserve session tmp; offer resume from the topmost incomplete task, refreshing the session manifest `updated:` witness as the resume first action)
- [x] Commit: `feat: lease-gated claim reclaim and interruption state table`

### Task 4: Terminal completion integrity (origins 3 and 4, execute-plan slice)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `ExecutePlanRuntimeTest#test_terminal_refuses_missing_archived_plan`; given an archived-plan path that does not exist under the repository root, expects `mark_terminal` to return blocked with reason `done-pending`, write no receipt, and leave `workflow_state` non-terminal
- [x] `ExecutePlanRuntimeTest#test_terminal_refuses_unchecked_plan_checkboxes`; given an archived plan file containing an unchecked checkbox line, expects blocked `done-pending` and no receipt written
- [x] `ExecutePlanRuntimeTest#test_terminal_ignores_inline_checkbox_literals`; given an archived plan whose prose contains an inline unchecked checkbox mention but no unchecked checkbox line, expects the complete receipt
- [x] `ExecutePlanRuntimeTest#test_terminal_refuses_unprovable_commit`; given a `commit_lookup` that returns false for the supplied identity, expects blocked `done-pending`
- [x] `ExecutePlanRuntimeTest#test_terminal_accepts_verified_receipt`; given an existing archived plan with every checkbox checked and a provable commit identity, expects the complete receipt echoing the checklist, archived-plan path, and commit identity
- [x] Run → expect RED: `test_terminal_refuses_missing_archived_plan`, `test_terminal_refuses_unchecked_plan_checkboxes`, and `test_terminal_refuses_unprovable_commit` fail against the current shape-only validation, while `test_terminal_ignores_inline_checkbox_literals` and `test_terminal_accepts_verified_receipt` pass at RED (the current validation accepts everything they assert); the existing terminal tests and selftest stay green (they pass today with nonexistent archived-plan paths because no existence check exists yet)
- [x] Implement the machine terminal predicate in `mark_terminal`: resolve the archived-plan path through the fail-closed safe-path policy under the driver repository root, read the file (bounded to its first 1,000,000 bytes), require zero lines whose first non-whitespace token is an unchecked checkbox (mid-prose mentions of the marker do not count), and require `commit_lookup` to prove the commit identity; any miss returns blocked `done-pending` with evidence naming the failed check and leaves the manifest non-terminal
- [x] Update the selftest and the existing `mark_terminal` fixtures to write a real archived plan file with every checkbox checked and to use a provable commit identity; Run → expect GREEN: the full suite passes
- [x] `runtime-contract.md`: extend the completion-receipt sentence that opens the Durable task state machine section, and the `terminal_result` paragraph in Lock liveness and generation fencing, with the three machine checks (archived-plan existence under the repository root, zero unchecked checkbox lines under the line-anchored reading, provable commit identity) and the preserved-manifest refusal
- [x] `SKILL.md`: add the `### Orchestration state table` subsection after the Terminal-response gate paragraph with rows for active, needs-review, needs-fix, paused, waiting-for-capacity, recovering, and terminal, each naming its machine `workflow_state` witness and durable artifacts (manifest counters, budget-pause record, staging attempt rows, review artifacts) and the only allowed user-facing response per state (a progress or pause update naming the state, the next action, and the resume condition; a final response only from terminal after the driver receipt); add the mandatory transition-loop sentence: after every worker return, review result, quota decision, and user status question the orchestrator selects and starts the next action before control returns; add the async-join rule: no final response while any launched worker of this run lacks a durably recorded outcome in the machine manifest (every live claim closed or its task terminal), mirrored into the session manifest and logs; state that the terminal gate refuses completion when review freshness or verification evidence is invalid, per the Phase 5 checklist and the Step 0.5 digest rule
- [x] Commit: `feat: machine terminal predicate and orchestration state table`

### Task 5: Final validation sweep

Files:
- none; this task runs the plan's `## Validation Commands` block and records the outputs in the session log

- [x] Run the full Validation Commands block from the repository root → expect exit 0 on every gate
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` (whole suite, including the neutrality scan over the edited skill bodies)
- [x] No commit expected; if any must-fix file drifted after its task commit, return it to that task's owner step instead of committing here
