# Plan: execute-plan review/fix pipeline efficiency

Backlog origins (scope of record): `docs/history/backlog/2026-09-14-execute-plan-parallel-review-address-workers.md`, `docs/history/backlog/2026-09-14-execute-plan-mid-round-quota-resume-watcher.md`, `docs/history/backlog/2026-09-14-execute-plan-batched-implement-launch.md`

Guidelines: Python driver changes follow `python_guidelines.md` under `shared_docs_dir` (resolve from `~/.ai-playbook/facts.md`).

Plan review: `docs/reviews/2026-09-15-plan-review-execute-plan-review-fix-pipeline-efficiency-r*.md` (prefix reference; the latest round certifies the current bytes)

## Terms

- **Address pass**: the per-round Step 3.3 receiving-review pass that folds accepted review findings; today always a single sub-agent.
- **Address fan-out**: running up to 3 address passes in parallel, each over a pairwise-disjoint finding subset grouped by shared files.
- **File-affinity grouping**: findings that share any file go to the same worker; the grouping is derived deterministically from the staging doc's canonical `finding_files` data, never from judgment.
- **Canonical finding file set**: the non-empty, repository-relative, normalized file list recorded for one finding in `extensions.address_fanout.finding_files`; it is the only input to fan-out grouping and is canonicalized again against the active repository before a worker scope is issued.
- **Wave boundary**: a Phase 3 point where a worker wave launches: the Step 3.1 panel launch and the Step 3.3 address launch (single or fanned).
- **Standing resume watcher**: a one-shot, self-disarming, idempotent scheduled automation at the known binding window's reset time plus one minute, scheduled at every continue boundary with a trusted reset epoch; each later boundary replaces it.
- **Batch implement launch**: ONE implement sub-agent launch and session covering up to four consecutive unchecked tasks whose canonical `Files:` sets are pairwise disjoint; the same session resumes at each next member with that member's policy.
- **Batch group**: the authoritative machine-state record that owns ordered members, active member, group generation, group policy metadata, anchor session, and one launch record; member claims reference it rather than copying its state.
- **Progress revision**: a monotonic machine-state counter advanced only by named execution progress such as launch, checkpoint, done commit, group-member advancement, or peer resumption; receipt timestamp refreshes do not advance it.
- **Staging doc**: the per-round review record under `{reviews_dir}` plus its `.stats.json` sidecar, per `review-staging`.

## Assumptions

- assume the runtime driver `scripts/execute_plan_runtime.py` is the only authority for claim, launch, and checkpoint state in Phase 1; basis: execute-plan runtime-neutral execution contract and the agent-logs machine-state section.
- assume the machine-manifest create path is the canonical producer for task file sets: it normalizes repository-relative `Files:` entries with the same path resolver used by the action envelope, persists their canonical form and a document-order ordinal, and rejects duplicate canonical paths; basis: the driver's fail-closed path policy and the batch queue's document-order requirement.
- assume both `create_manifest` and the CLI `_operation_create` path use that same producer contract: raw `Files:` aliases are canonicalized before persistence, duplicate canonical paths within one task are rejected, cross-task overlap remains representable but stops the batch prefix, and every pending or resumed selector consumes the persisted document ordinal; basis: the driver is the machine-manifest authority and the batch queue must not reconstruct order from task numbers.
- assume a current-v1 staging sidecar can carry the fan-out input in `extensions.address_fanout.finding_files`; versionless legacy sidecars remain on the single-worker path and are not upgraded implicitly; basis: review-staging's extension boundary and historical compatibility contract.
- assume live address fan-out state is authoritative in the `address_fanout` section of `runtime_state.json`, owned and mutated by the parent driver under the manifest lock; `manifest.md` and the sidecar are projections and final accounting only, and neither authorizes retry, patch application, or commit; basis: the existing runtime-state versus human-receipt authority boundary.
- assume the plan file never appears in a task's `allowed_paths` (the orchestrator owns checkbox flips), so batch disjointness needs no plan-file carve-out; basis: implement worker rule 7 and Step 1.3.
- assume the watcher uses the host's one-shot automation capability, falling back to a launchd one-shot with a sentinel self-disable file, then report-only; basis: the existing Budget gate pause protocol fallback chain.
- assume the watcher implementation exposes one workflow-neutral state-adapter protocol: Task 5 supplies the execute-plan runtime adapter and Task 6 supplies the plans-skill authoring adapter; the two workflows use different JSON state files but share one executable watcher state machine, lock protocol, replacement fence, and scheduler adapter.
- assume the validation runners are `python3 scripts/test_execute_plan_runtime.py`, `python3 scripts/validate_review_staging.py --selftest`; basis: files verified on disk 2026-09-15.
- assume `scripts/check-no-em-dash.sh` and the public-hygiene scan are clean on every surface this plan edits; basis: both gates ran clean on all ten surfaces at authoring time 2026-09-15.

Decision points requiring a grill: worker-partitioning shape resolved to file affinity over lens affinity; source: origin item 2026-09-14-execute-plan-parallel-review-address-workers.md prescribes pairwise-disjoint file sets and lens grouping cannot keep parallel edits conflict-free because same-file findings would land in different workers; date 2026-09-14; affects Gist, Tasks 1 and 2, Task 8 grouping; watcher protocol home resolved to the canonical execute-plan Budget gate section with the plans skill carrying mirror deltas; source: origin item 2026-09-14-execute-plan-mid-round-quota-resume-watcher.md plus the plans mirror Canonical home contract; date 2026-09-14; affects Tasks 5 and 6; sidecar accounting vehicle for fan-out address contributions resolved to the current-v1 `extensions.address_fanout` object plus canonical `finding_files` and per-finding Analysis attribution markers; versionless sidecars stay on the single-worker path; source: review-staging version-1 extension boundary and historical compatibility contract; date 2026-09-15; affects Tasks 3 and 4

## Design Invariants (CR Guard)

- Canonical-home contract for the shared pause protocol survives every edit: the canonical home stays the execute-plan Budget gate section; the plans skill carries only its declared deltas (source: plans SKILL.md "Canonical home" note and the execute-plan integration note naming plans as the mirror).
- A batch is ONE worker launch, never parallelism: implement/done/review-fix are never launched in parallel (source: orchestrator duty lineage "never parallel for implement/done/review-fix"; the Hard Gate 3 rewrite must keep the never-parallel clause).
- Address fan-out workers never commit and never edit the staging doc; the parent merges triage results and lands exactly one address commit per round (source: origin item 1 guardrails).
- Budget-probe fail-open policy is unchanged for workflow admission: a missing or unopenable probe is `status: unknown`, the flow continues, and it never blocks; because unknown has no trusted reset epoch, it records an explicit report-only outcome and schedules no watcher (source: Budget gate exit-code contract).
- Synthesis statistics stay immutable during triage; fan-out attribution lives outside the Panel, Deduplication, Discarded, Severity calibration, and Counts tables (source: review-staging orchestrator recording rule 7).
- The driver keeps at most one live claim group at a time; per-task checkpoints, per-task done boundaries, and per-task commits remain ordered (source: driver single-claim semantics and Step 1.4 / Step 3.4 gates). The group record owns shared launch/session state; every member claim has its own token, canonical allowed paths, attempt, and moving baseline. Only the active member may be launched or resumed, and a member's done never stages a batch-mate's file.

## Gist & Examples

Three mechanisms reshape execute-plan orchestration. All three are opt-in, capped, and serial-fail-open: when their trigger conditions do not hold, behavior is byte-for-byte today's. The driving principle is that machinery must pay for itself in measured wall-clock and token spend, so each mechanism records the evidence it earned its complexity with.

### Mechanism 1: address fan-out (origin 1)

Measured on the budget-gate run: the five-lens review panel already runs in parallel (17-33 min), but the serial tail (synthesis, one address worker, done) was 2-3x the panel time (address passes of 38, 20, and 12 minutes folding 14 findings across 8 files, then fewer). Round wall clock is bounded by one worker's serial edit-verify cycle over the widest file spread.

**Before (today):** the r1 staging doc holds 14 unresolved blocking findings across 8 files. The parent launches one Address Review sub-agent that fixes all 14 serially, re-runs validation, and returns after 38 minutes. The round cannot finish sooner.

**After (this plan):** the parent computes the deterministic file-affinity grouping from the canonical `finding_files` map (findings sharing any file land in the same worker; connected components over shared files, packed into at most 3 workers). Suppose the components are {5 findings over files A,B}, {6 findings over C,D,E}, {3 findings over F}. The parent launches 3 Address Fan-out Workers in parallel, each in an ephemeral patch workspace with its finding ids, canonical allowed files, worker scope token, attempt id, and log path `review-r1-receiving-review-w<W>.log.md`. Each worker fixes only its subset in its isolated workspace, never commits, never edits the staging doc, and returns a binary patch, changed-path receipt, and per-finding triage decisions with verification evidence. The parent rejects any patch whose paths, commit objects, or receipt exceed the worker token, applies accepted patches serially to the main worktree, merges triage into the staging doc and sidecar, and creates any durable backlog items itself. The parent re-runs the FULL Validation Commands block once after all workers return and lands the round's single address commit. Fallback: when no grouping into 2 or more non-empty disjoint subsets exists, or any finding lacks an unambiguous file set, one worker runs exactly as today. A failed or timed-out worker is retried on its subset only after the original attempt is cancelled and verified stopped; the initial attempt plus one retry is the maximum, and an unclean cancellation or second failure records a terminal blocked subset while the other workers' accepted results stand.

### Mechanism 2: wave-boundary probes and the standing resume watcher (origin 2)

Measured on the same run: the r1 panel completed at 00:47 with about two hours of quota window left, outside the 20-minute pause threshold, so the boundary-only gate said continue. The window expired mid-round in the gate-free stretch between panel completion and the address launch; no `budget_pause` was recorded, nothing was scheduled, and the run sat idle 12.8 hours until a manual resume.

**Before (today):** the Budget gate runs only at the Step 1.5 and Step 3.5 boundaries. A continue decision there never looks again before the next worker wave, and a mid-round death schedules nothing.

**After (this plan):** the probe also runs before every Phase 3 worker-wave launch: the Step 3.1 panel launch and the Step 3.3 address launch, single or fanned. Every outcome is recorded in the human receipt and authoritative machine state. Additionally, at every budget-gate boundary whose decision is continue and whose report contains a trusted binding reset epoch, the orchestrator schedules the standing resume watcher at reset time plus one minute. The watcher state is written under the machine-manifest lock with a unique watcher id, scheduling epoch, expected generation, and expected progress revision; `manifest.md` receives only a projection. Its prompt re-enters execute-plan on the plan path, atomically verifies that its receipt is still current, the plan is active, the workflow is not aborted or complete, and the semantic progress revision is unchanged, then applies the Step 0.5 resume rules. Guard and fired-marker cleanup uses a serialized compare-and-delete operation, not an unlocked re-read followed by unlink. A newer boundary replaces the prior watcher by compare-and-swap, never stacks; clean exit or archive records cancellation and leaves a stale scheduled callback to self-disarm. An unknown quota report remains report-only with the exact manual resume command and schedules no watcher. The weekly secondary binding stays report-only and schedules no watcher. A simulated mid-round death therefore resumes at most one minute after a known reset instead of idling until a human notices.

### Mechanism 3: batch implement launch (origin 3)

Measured on the same run: six Phase 1 tasks took 15-24 minutes each end-to-end for implement work that is minutes per task; the fixed per-task cycle (claim, launch record, sub-agent launch, verification, marker plus checkbox, done, probe, manifest) dominates when consecutive tasks are independent.

**Before (today):** Tasks 2 and 3 touch two different skill files; the orchestrator runs the full cycle twice: claim, launch, wait, verify, mark, done, then claim, launch, wait, verify, mark, done.

**After (this plan):** when the next K unchecked tasks (K at most 4, a prefix of the unchecked queue in canonical document order) have pairwise-disjoint canonical `Files:` sets and the combined file count is at most 8, the orchestrator MAY batch them into ONE implement sub-agent launch. The driver creates one explicit batch group with ordered member ordinals and one anchor session. The worker receives only the active member's policy token, implements that member, writes that member's RED/GREEN log section, and returns a member checkpoint; after the per-task done commit, the parent resumes the same session for the next member with a new member token and the moving baseline. Thus one launch replaces K launches while preserving member-scoped authorization, per-task verification, per-task checkbox flips, per-task done commits in document order, per-task driver checkpoints, K commits, and no batch-level commit. The group advances only under the manifest lock; a failure, timeout, cancellation uncertainty, stale receipt, or late result stops the batch at member j and leaves j and later recoverable through the standard fix path. Batch size 1 emits no batch fields anywhere, so single-task runs are indistinguishable from today's manifests.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the batch state-machine tests pass (canonical producer persistence, document-order selectors, lexical and symlink alias overlap, canonical prefix assembly, overlap stop, cap, combined file-count cap, size-1 field-free, no-opt-in single claim, wrapper and CLI opt-in, one immutable group launch identity, member-scoped launch/resume tokens, typed member-resume action, active-member ordering, member scope witness, mid-batch failure, own-files done close, per-member done close, single-group invariant, late-receipt rejection); the address fan-out harness proves the production parent entrypoint, canonical connected-component grouping, isolated patch application, active-attempt fencing, fallback, bounded subset retry, parent merge, and one commit; the watcher harness proves both runtime and authoring adapters, known-to-non-schedulable supersession, canonical plan identity, shared guard-lock cleanup, and real RuntimeDriver persistence; the staging validator selftest covers the version-1-only `extensions.address_fanout` shape with positive, malformed, legacy, status/reason, and conservation cases; every mechanism's fallback is pinned in its contract file.
- performance: caps are present and pinned (batch cap of four, fan-out cap of three); the first qualifying post-implementation run must record fan-out versus single-worker address wall-clock and the batch launch count (Ship when).
- maintainability: each mechanism is opt-in with a serial-fail-open fallback stated in the same section that grants the option; integration notes run in both directions (execute-plan Step 3.3 and the receiving-review, review-loop, review-staging consumer rows).
- observability: the machine state records the fan-out grouping, worker scope token, attempt history, terminal subset outcome, batch group and active member, every wave-boundary probe outcome, semantic progress revision, and current watcher receipt; the human manifest projects those facts without becoming an authority.

**Done when:**
- every task checkbox is `[x]` and the plan's Validation Commands block exits 0 from the repo root
- `python3 scripts/test_execute_plan_runtime.py` passes including the batch state-machine and CLI tests
- `python3 scripts/test_execute_plan_runtime_codex.py` and `python3 scripts/test_runtime_capabilities.py` pass for the batch adapter boundary and activation contract
- `python3 scripts/test_execute_plan_address_fanout.py` passes for grouping, isolated patch application, retry, merge, and commit discipline
- `python3 scripts/test_execute_plan_resume_watcher.py` passes with injected time and fake automation/launchd schedulers
- `python3 scripts/validate_review_staging.py --selftest` passes including the version-1-only `address_fanout` cases
- the em-dash scan is clean on every edited prose surface, and the per-task staged-diff byte scans in Tasks 1, 4, 5, 6, and 8 prove no em-dash entered a Python surface

**Ship when:**
- the first qualifying execute-plan run after implementation records the measured round wall-clock for a fanned mixed-file address round against the single-worker baseline (origin acceptance 6), records the batch launch count for a qualifying Phase 1 batch, and demonstrates one mid-round watcher resume drill (scheduled at reset plus one minute, stood down or resumed per the manifest). These are runtime observations collected by future execute-plan runs, not repository artifacts this plan can produce.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` *(address-fan-out state and parent-entrypoint integration, watcher progress and receipt persistence, and batch claim group, launch, checkpoint witness, done close; unrelated runtime operations and outcomes remain frozen)*
- `scripts/execute_plan_address_fanout.py` *(new; pure grouping and transition functions plus the injected parent orchestration entrypoint, worker scope, patch verification, and bounded attempts)*
- `scripts/execute_plan_runtime_codex.py` *(batch member progress and anchor-session launch/resume translation; all unrelated host-envelope translation frozen)*
- `scripts/runtime_capabilities.py` *(batch result and member-token capability fields only; all other capability validation frozen)*
- `scripts/execute_plan_resume_watcher.py` *(new; shared machine-state watcher transition and scheduler adapter)*
- `scripts/validate_review_staging.py` *(the `extensions.address_fanout` shape gate and its selftest cases; frozen everywhere else)*
- `scripts/quota_window_probe.py` *(shared guard lock around flag replacement only; probe report and fail-open decisions remain frozen)*
- `scripts/test_quota_window_probe.py` *(shared guard-lock replacement interleaving only; report and fail-open tests remain frozen)*
- `agents/hooks/budget-guard/budget_guard_core.py` *(shared guard lock around expiry cleanup only; blocking and fail-open decisions remain frozen)*
- `scripts/test_budget_guard_hooks.py` *(shared guard-lock cleanup interleaving only; blocking and fail-open tests remain frozen)*
- `agents/hooks/budget-guard/codex.sh`
- `agents/hooks/budget-guard/zcode.sh`
- `agents/hooks/budget-guard/README.md` *(the shared lock and atomic cleanup contract only)*
- `agents/skills/execute-plan/runtime-contract.md` *(the claim/launch/checkpoint state fields the batch contract introduces; all other documented transitions frozen)*

**Tests:**
- `scripts/test_execute_plan_runtime.py` *(new batch tests plus regressions the batch work touches)*
- `scripts/test_execute_plan_address_fanout.py` *(new; deterministic grouping, patch isolation, retry, merge, and single-commit harness)*
- `scripts/test_execute_plan_runtime_codex.py` *(batch progress and anchor-session adapter tests)*
- `scripts/test_runtime_capabilities.py` *(batch result and member-token validation tests)*
- `scripts/test_execute_plan_resume_watcher.py` *(new; injected-clock scheduler and machine-state transition harness)*

**Skill contracts (production contracts of this repo):**
- `agents/skills/execute-plan/SKILL.md` *(Step 3.1 and Step 3.3 probe lines and their verification gates, the Step 3.3 launch log line, the Step 3.4 preceding-step pass list and its verification gate item 1, Budget gate section, Phase 1 Steps 1.1 and 1.2, frontmatter description, Phase 3 manifest tracking list, Sub-Agent Launch Rules table, Hard Gate 3, the Orchestrator Responsibilities never-parallel parenthetical, the Consumes plans integration note, the User Interruption section's one-line interrupt-marker rule; all other sections frozen)*
- `agents/skills/execute-plan/subagent-prompts.md` *(Address Fan-out Worker and Implement Task Batch templates, and the Done (per review iteration) template's preceding-step log list; other templates frozen)*
- `agents/skills/execute-plan/agent-logs.md` *(path table rows and the per-iteration done read rule; rest frozen)*
- `agents/skills/done/SKILL.md` *(batch-member done handoff and scoped staging receipt only; all other done behavior frozen)*
- `agents/skills/receiving-review/SKILL.md` *(one orchestrated-subset note plus the execute-plan integration row; rest frozen)*
- `agents/skills/review-loop/SKILL.md` *(integration pointer only; rest frozen)*
- `agents/skills/review-staging/SKILL.md` *(Address fan-out accounting subsection, Version-1 sidecar extension rule, Historical compatibility boundary, and the receiving-review consumer row; rest frozen)*
- `agents/skills/plans/SKILL.md` *(Budget gate section mirror deltas only; rest frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-14-review-runner-bounded-timeout-fallback.md`; reason: related open item (per-worker bounded timeouts); a separate future plan
- persistent per-worker Phase 1 worktrees and claim-graph parallel task clusters; reason: origin 3 explicit non-goal; address fan-out uses only the ephemeral patch workspaces defined by Tasks 1 and 2

## Validation Commands

```bash
#!/usr/bin/env bash
# Validation: execute-plan review/fix pipeline efficiency. Run from the repo root.
set -u
REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
cd "$REPO" || exit 1
fail() { echo "VALIDATION FAILED: $1"; exit 1; }
present() { grep -qF "$1" "$2" 2>/dev/null || fail "missing in $2: $1"; }
no_match() {
  grep -qF "$1" "$2" 2>/dev/null; local rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden text present in $2: $1"; fi
  if [ "$rc" -ge 2 ]; then fail "search tool error rc=$rc on $2"; fi
}

EP=agents/skills/execute-plan/SKILL.md
TPL=agents/skills/execute-plan/subagent-prompts.md
ALOG=agents/skills/execute-plan/agent-logs.md
RRV=agents/skills/receiving-review/SKILL.md
RLO=agents/skills/review-loop/SKILL.md
RST=agents/skills/review-staging/SKILL.md
PLN=agents/skills/plans/SKILL.md
RC=agents/skills/execute-plan/runtime-contract.md
DRV=scripts/execute_plan_runtime.py
COD=scripts/execute_plan_runtime_codex.py
CAP=scripts/runtime_capabilities.py
WATCH=scripts/execute_plan_resume_watcher.py
FANOUT=scripts/execute_plan_address_fanout.py
PROBE=scripts/quota_window_probe.py
PROBET=scripts/test_quota_window_probe.py
GUARD=agents/hooks/budget-guard/budget_guard_core.py
GREADME=agents/hooks/budget-guard/README.md
GUARDT=scripts/test_budget_guard_hooks.py
TST=scripts/test_execute_plan_runtime.py
CODT=scripts/test_execute_plan_runtime_codex.py
CAPT=scripts/test_runtime_capabilities.py
FANOUTT=scripts/test_execute_plan_address_fanout.py
WATCHT=scripts/test_execute_plan_resume_watcher.py
VAL=scripts/validate_review_staging.py
DONE=agents/skills/done/SKILL.md

for f in "$EP" "$TPL" "$ALOG" "$RRV" "$RLO" "$RST" "$PLN" "$RC" "$DRV" "$COD" "$CAP" "$WATCH" "$FANOUT" "$PROBE" "$PROBET" "$GUARD" "$GREADME" "$GUARDT" "$TST" "$CODT" "$CAPT" "$FANOUTT" "$WATCHT" "$VAL" "$DONE"; do
  [ -f "$f" ] || fail "missing surface file: $f"
done

# Task 1: Step 3.3 fan-out contract (each obligation its own probe)
present 'Fan-out option (file affinity)' "$EP"
present 'workers never commit and never edit the staging doc' "$EP"
present 'deterministic file-affinity grouping' "$EP"
present 'falls back to the single address worker' "$EP"
present 'retried on its subset only' "$EP"
present 'the base address log and every per-worker address log exist and are non-empty' "$EP"
present 'the parent owns the base address log' "$EP"
present 'up to 3 file-affinity workers in parallel' "$EP"
present 'run_address_fanout' "$EP"
present 'active-attempt compare-and-swap' "$EP"
present 'runtime_state.json.address_fanout' "$EP"

# Task 2: fan-out worker template + per-worker log rows
present '## Address Fan-out Worker' "$TPL"
present 'Fix only your subset findings on your allowed files' "$TPL"
present 'or the single address log (no fan-out)' "$TPL"
present 'review-r<R>-receiving-review-w<W>.log.md' "$ALOG"
present 'plus every per-worker address log for the round' "$ALOG"

# Task 3: receiving-review subset note + review-loop pointer
present 'An orchestrated run may hand the pass a finding subset plus its allowed files' "$RRV"
present 'may fan the step-3 receiving-review pass per the execute-plan Step 3.3 fan-out contract' "$RLO"

# Task 4: review-staging accounting + validator gate
present 'Address fan-out accounting' "$RST"
present 'never consume review-time budget or overflow' "$RST"
present 'extensions.address_fanout' "$RST"
present 'finding_files' "$RST"
present 'version-1-only' "$RST"
present 'address_fanout' "$VAL"
present 'selftest: address_fanout unknown finding id fails hard' "$VAL"
present 'selftest: address_fanout count mismatch fails hard' "$VAL"
present 'selftest: address_fanout duplicate finding assignment fails hard' "$VAL"
present 'selftest: address_fanout well-formed shape passes hard' "$VAL"
present 'selftest: address_fanout missing round fails hard' "$VAL"
present 'selftest: address_fanout missing log fails hard' "$VAL"
present 'selftest: address_fanout unknown reason code fails hard' "$VAL"
present 'selftest: address_fanout invalid status reason combination fails hard' "$VAL"
present 'batch claim group' "$RC"

# Task 5: wave-boundary probes + standing resume watcher
present 'before every Phase 3 worker-wave launch' "$EP"
present 'the Step 3.1 panel launch and the Step 3.3 address launch' "$EP"
present 'Standing resume watcher' "$EP"
present 'reset time plus one minute' "$EP"
present 'stands down when the semantic progress revision changed after the scheduling point' "$EP"
present 'stands down when a peer session resumed the work' "$EP"
present 'stands down when the plan is archived or completed' "$EP"
present 'stands down when the run was explicitly aborted or interrupted' "$EP"
present 'later boundaries replace, never stack, watchers' "$EP"
present 'the weekly secondary binding still writes no flag and schedules no watcher' "$EP"
present 'canonical plan path, plan-byte digest' "$EP"
present 'supersedes and clears any existing pending watcher' "$EP"
present 'pending_resume_watcher' "$EP"
present 'the authoring-boundary watcher deltas' "$EP"
present 'WatcherStateAdapter' "$WATCH"
present 'budget-guard.lock' "$PROBE"
present 'budget-guard.lock' "$GUARD"
present 'test_guard_cleanup_does_not_remove_replaced_flag' "$PROBET"
present 'test_guard_cleanup_does_not_remove_replaced_marker' "$GUARDT"

# Task 6: plans mirror deltas
present 'schedule the same standing resume watcher' "$PLN"
present 'the authoring-boundary watcher deltas' "$PLN"
present 'fixture-verified on one runtime; pending the first-start trust-prompt approval and the deny-envelope drive on the other runtime' "$PLN"

present 'never parallel for implement or done; the review-fix address pass may fan out only under the Step 3.3 fan-out contract' "$EP"
present 'a fanned address wave inherits the Step 3.1 timeout semantics' "$EP"

# Task 7: batch implement contract
present 'ONE implement sub-agent launch' "$EP"
present 'cap of four' "$EP"
present 'never batch tasks carrying host-wiring exception receipts, inclusion-gate ambiguity, or overlapping files' "$EP"
present 'batch decision and membership are recorded in the session manifest' "$EP"
present 'the driver computes the batch membership as the maximal disjoint prefix' "$EP"
present 'batch implement launch' "$EP"
present 'batch opt-in flag' "$EP"
present 'a failure in batch task j stops the batch' "$EP"
present 'per-task done commits in document order' "$EP"
present 'combined member file count is capped at 8' "$EP"
present 'a launch may batch up to four file-disjoint tasks as one batch implement launch under the Step 1.2 batch contract' "$EP"
present 'user_interrupt: <ISO8601 timestamp>' "$EP"
present 'into its own task-<N>-implement.log.md' "$TPL"
present '## Implement Task Batch' "$TPL"
present 'active-member ordering' "$RC"
present 'claim_groups' "$DRV"
present 'member-scoped authorization' "$RC"
present 'progress_revision' "$WATCH"
present 'report-only' "$WATCH"
present 'test_batch_late_receipt_is_rejected' "$TST"
present 'test_address_fanout_scope_violation_is_quarantined' "$FANOUTT"
present 'test_address_fanout_entrypoint_launches_and_merges_with_worker_doubles' "$FANOUTT"
present 'test_address_fanout_late_attempt_receipt_is_quarantined' "$FANOUTT"
present 'test_address_fanout_state_round_trip_and_projection_fence' "$TST"
present 'test_watcher_unknown_budget_is_report_only' "$WATCHT"

# Superseded wording must be gone (forbidden-match sweeps, rc-aware)
flatten_file() {
  python3 - "$1" <<'PY'
import re
import sys
from pathlib import Path

print(re.sub(r"\s+", " ", Path(sys.argv[1]).read_text(encoding="utf-8")))
PY
}
flat_match() {
  local needle="$1" file="$2" flattened
  if ! flattened="$(flatten_file "$file")"; then
    return 2
  fi
  case "$flattened" in
    *"$needle"*) return 0 ;;
    *) return 1 ;;
  esac
}
no_match_flat() {
  local needle="$1" file="$2" rc
  flat_match "$needle" "$file"
  rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden text present in $file: $needle"; fi
  if [ "$rc" -ge 2 ]; then fail "flattened search error rc=$rc on $file"; fi
}
for f in "$EP" "$TPL" "$ALOG" "$RRV" "$RLO" "$RST" "$PLN" "$RC" "$DRV" "$COD" "$CAP" "$WATCH" "$FANOUT" "$PROBE" "$GUARD" "$GREADME" "$TST" "$CODT" "$CAPT" "$FANOUTT" "$WATCHT" "$VAL" "$DONE"; do
  no_match_flat 'One task per implement iteration' "$f"
  no_match_flat 'At the Step 1.5 and Step 3.5 boundaries only' "$f"
  no_match_flat 'implement one task at a time' "$f"
  no_match_flat 'one task per iteration' "$f"
done

# RED witness: the flattened sweep must catch a forbidden phrase wrapped across lines.
RED_SWEEP="$(mktemp "${TMPDIR:-/tmp}/execute-plan-sweep.XXXXXX")" || fail "cannot create sweep witness"
printf '%s\n%s\n' 'One task per implement' 'iteration' > "$RED_SWEEP" || fail "cannot write sweep witness"
if ! flat_match 'One task per implement iteration' "$RED_SWEEP"; then
  rm -f "$RED_SWEEP"
  fail "flattened sweep RED witness was not detected"
fi
rm -f "$RED_SWEEP"

# Task 8: driver batch support (field names + state-machine test obligations)
present 'claim_groups' "$DRV"
present 'resume_member' "$DRV"
present 'anchor session' "$DRV"
present '--batch' "$DRV"
present 'default-off `batch` opt-in on claim' "$DRV"
present 'test_batch_claim_assembles_canonical_disjoint_prefix' "$TST"
present 'test_manifest_create_persists_canonical_paths_and_document_ordinals' "$TST"
present 'test_batch_claim_stops_at_canonical_alias_overlap' "$TST"
present 'test_batch_claim_stops_at_overlap_and_caps' "$TST"
present 'test_batch_claim_single_task_and_no_opt_in_are_field_free' "$TST"
present 'test_batch_group_has_one_anchor_launch_record' "$TST"
present 'test_batch_member_policy_is_scoped' "$TST"
present 'test_batch_member_progress_resumes_anchor_session' "$TST"
present 'test_batch_done_returns_typed_resume_member_action' "$TST"
present 'test_batch_done_returns_typed_resume_member_action' "$TST"
present 'test_batch_member2_witnesses_from_member1_done' "$TST"
present 'test_batch_mid_member_failure_preserves_prefix_and_suffix' "$TST"
present 'test_batch_done_closes_members_individually' "$TST"
present 'test_batch_late_receipt_is_rejected' "$TST"
present 'test_claim_blocked_while_batch_live' "$TST"
present 'test_cli_batch_opt_in_and_no_flag_control' "$TST"
present 'test_batch_wrapper_opt_in_and_no_flag_control' "$TST"
present 'test_cli_continue_batch_opt_in_and_no_flag_control' "$TST"
present 'test_batch_wrapper_opt_in_and_no_flag_control' "$TST"
present 'test_cli_continue_batch_opt_in_and_no_flag_control' "$TST"
present 'test_batch_progress_translation_and_anchor_resume' "$CODT"
present 'test_batch_result_and_member_policy_validation' "$CAPT"

# Suites: task-local harnesses are run by their owning tasks; these are the final full-suite gates.
python3 scripts/test_execute_plan_runtime.py || fail "runtime driver suite failed"
python3 scripts/test_execute_plan_runtime_codex.py || fail "Codex adapter suite failed"
python3 scripts/test_runtime_capabilities.py || fail "runtime capability suite failed"
python3 scripts/test_execute_plan_address_fanout.py || fail "address fan-out harness failed"
python3 scripts/test_execute_plan_resume_watcher.py || fail "resume watcher harness failed"
python3 scripts/test_quota_window_probe.py || fail "quota probe lock suite failed"
python3 scripts/test_budget_guard_hooks.py || fail "budget guard lock suite failed"
python3 scripts/validate_review_staging.py --selftest || fail "staging validator selftest failed"

# Repo format and hygiene gates over the changed surfaces
bash scripts/check-no-em-dash.sh file "$EP" "$TPL" "$ALOG" "$RRV" "$RLO" "$RST" "$PLN" "$RC" "$GREADME" "$DONE" || fail "em dash found in a changed prose surface"
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || fail "public hygiene scan failed"

echo "VALIDATION OK"
```

Authoring-time RED record (2026-09-15, re-baselined after the focused panel fold): `bash -n` on the block is clean. Against the pre-change tree, the first failing gate is now the file-existence loop for the new fan-out and watcher helpers/tests; after those files exist, the new contract pins and state-machine test-name pins are expected to fail until their owning tasks land. Passing today: the existing staging-validator selftest, em-dash scan, and hygiene scan. NOT passing today: `python3 scripts/test_execute_plan_runtime.py` carries one pre-existing failure at HEAD (`test_shared_skill_bodies_remain_runtime_neutral`, the term `codex` in `agents/skills/plans/SKILL.md`, introduced by commit 0b533bab); Task 6 remediates it and restores the baseline Task 8 relies on. The focused review confirmed the plan now requires task-local gates, a current-v1-only fan-out extension, canonical file-set input, isolated patch workers, bounded attempts, authoritative watcher state, and member-scoped batch sessions. The pin-versus-prescription audit must be rerun after any future plan edit; every positive pin must occur in the task that prescribes it. The Python em-dash gates remain scoped to staged diffs in Tasks 4 and 8 because pre-existing em-dashes live in frozen regions; prose-surface scans remain whole-file.

**Task-scoped validation rule:** the full `## Validation Commands` block is a Task 9 final gate only. Every earlier task runs only the validation command listed in that task, against files that exist at that task boundary, and records the result before its commit. The batch worker template receives each member's task-local command rather than the final block. A task-local gate may use a focused grep or selftest for a contract-only task, but it must not require artifacts introduced by a later task.

### Task 0: Drift re-verification (execute-time; run before Task 1)

The driver and its skill contracts executed three times this plan's drafting week (commits `0b533bab`, `1318ef75`, `6606a88f`). Before editing, re-verify every current-state anchor this plan edits against the working tree; a drifted anchor means the plan is stale and must be re-certified before any edit.

Files:
- `agents/skills/execute-plan/SKILL.md` *(read-only this task)*
- `scripts/execute_plan_runtime.py` *(read-only this task)*

- [ ] Verify each current-state anchor is present exactly as pinned: in `agents/skills/execute-plan/SKILL.md`: `At the Step 1.5 and Step 3.5 boundaries only` (Budget gate section), `One task per implement iteration` (Hard Gate 3), `implement one task at a time` (frontmatter description), `### Step 3.3: Launch address-review sub-agent`, `one task per iteration` (Phase 1 Step 1.1 rule; the live line wraps it in bold markers); in `scripts/execute_plan_runtime.py`: `another task is already claimed` (single-claim invariant) and `launch_record` (per-claim launch records); run: `grep -qF '<anchor>' <file> && echo OK` per pair, expect seven `OK` lines
- [ ] If any anchor is missing, STOP: do not edit; report the drift and request a fresh review round of this plan against the current bytes (the readiness gate will fail the stale digest); do not improvise edits around a moved anchor
- [ ] Confirm the three origin backlog items still sit at `docs/history/backlog/` with `Status: open` (they move to `completed/` only at this plan's completion)

### Task 1: Address fan-out contract in execute-plan Step 3.3

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/execute_plan_runtime.py` *(address-fan-out state and parent-entrypoint integration only; watcher and batch changes remain in their owning tasks; unrelated runtime transitions frozen)*
- `scripts/execute_plan_address_fanout.py` *(new; deterministic grouping, patch-scope witness, and bounded attempt state)*
- `scripts/test_execute_plan_address_fanout.py` *(new; hermetic fan-out harness)*
- `scripts/test_execute_plan_runtime.py` *(address-fan-out state round-trip and projection-fence witness)*

- [ ] In `### Step 3.3: Launch address-review sub-agent`, add a `**Fan-out option (file affinity):**` block that grants the parent the option to fan the address pass across 2-3 receiving-review workers when the round's unresolved blocking findings group into at least 2 non-empty pairwise-disjoint file sets; the block must state, using these exact sentences: `The grouping is a deterministic file-affinity grouping derived from the staging doc's canonical finding_files data: findings that share any file go to the same worker (connected components over shared files, packed greedily by descending finding count into at most three workers).` and `When no grouping into two or more non-empty disjoint subsets exists, the pass falls back to the single address worker, which is the default whenever fan-out is not clearly beneficial.` and `Fan-out workers never commit and never edit the staging doc; the parent merges worker results, updates the staging doc triage fields and sidecar itself, re-runs the FULL Validation Commands block once after all workers return, and lands one address commit per round, launched as the usual per-round done.`
- [ ] Reconcile the never-parallel lineage with the fan-out grant in the same file: rewrite the parenthetical of the Orchestrator Responsibilities worker-launch item from `(never parallel for implement/done/review-fix)` to `(never parallel for implement or done; the review-fix address pass may fan out only under the Step 3.3 fan-out contract, with parent-owned merge and the single per-round commit)`, so the frozen lineage and the Step 3.3 grant say the same thing
- [ ] Extend the fan-out bookkeeping into the downstream gates in the same file: the Step 3.3 launch line passes each worker's per-worker log path alongside the base address log path; the Step 3.4 preceding-step pass list carries the base address log `plus every per-worker address log for the round` when the round fanned; the Step 3.4 verification gate item 1 counts the per-worker logs among the preceding-step logs a fanned round's done must read; a fanned address wave inherits the Step 3.1 timeout semantics: 20 minutes without the base address log and every per-worker log triggers the focused relaunch path, and a timed-out worker is retried on its subset only
- [ ] In the same block, state the grouping inputs and merge bookkeeping: each worker receives its finding id subset, its canonical allowed files, an opaque worker scope token bound to the current round and attempt, and its own per-worker log path; the parent creates an ephemeral patch workspace under `{tmp_dir}/execute-plan/<PLAN_SLUG>/address-r<R>-w<W>-a<A>/` from the pre-round HEAD and records the workspace, baseline, worker id, attempt id, token digest, and expected paths in the machine session state; the manifest records the grouping (worker, finding ids, canonical file sets); a failed or timed-out worker is `retried on its subset only` while the other workers' accepted results stand; in a fanned round `the parent owns the base address log` `review-r<R>-receiving-review.log.md`, heartbeating it before the fan-out and appending the merge pass after the workers return
- [ ] Make the isolation boundary enforceable: a worker returns a binary patch, its changed-path receipt, its attempt id, and its final status; before applying a patch, the parent verifies the patch applies cleanly to the recorded baseline, contains no commit object, changes only the worker's canonical file set, and matches the worker token and attempt; any mismatch is quarantined and cannot be merged or committed; patches are applied serially to the parent worktree after all accepted workers finish
- [ ] Define bounded retry ownership: each worker has at most two attempts (initial plus one retry); a timeout or runtime error first cancels the original worker and requires verified session/process termination, and no retry is allowed after cleanup-unverified, an ambiguous patch, or a second failure; the parent records every attempt and a terminal `blocked` subset outcome in machine state and `extensions.address_fanout` while preserving accepted results from other workers
- [ ] Implement `scripts/execute_plan_address_fanout.py` as the shared parent-side helper with pure functions for canonical file-affinity connected components, deterministic greedy packing capped at three workers, missing/ambiguous-file fallback, worker scope-token issuance, patch changed-path and no-commit verification, attempt transition, cancellation receipt, and terminal blocked-subset recording; add a production `run_address_fanout` entrypoint with injected worker-launch, cancellation, workspace, and patch-application ports that owns workspace creation, worker launch and collection, termination verification before retry, serial application of accepted patches, and a merge receipt, but never edits the staging doc or creates commits
- [ ] Wire the Step 3.3 parent contract to `run_address_fanout`: the parent invokes this entrypoint for every eligible fanned round, supplies the current round and canonical finding data, persists the returned lifecycle transitions in `runtime_state.json.address_fanout` under the manifest lock, then merges the returned triage and receipt into the staging doc and sidecar and creates the single address commit; no launch, cancellation, patch-application, or retry behavior may remain prose-only
- [ ] Make `runtime_state.json.address_fanout` the one authoritative live fan-out record: it owns round, grouping, worker scope, active attempt, attempt state, accepted patch receipts, terminal subset state, and a monotonically increasing fan-out generation; `manifest.md` and `extensions.address_fanout` are generated projections, and finalization renders both from one lock-held machine-state snapshot with the same generation, refusing to advertise completion if projection replacement fails
- [ ] Require every result to pass an active-attempt compare-and-swap under that authority before triage merge or patch application: the worker, round, attempt id, token digest, and parent generation must identify the still-active attempt; closed, cancelled, superseded, aborted, or replaced attempts are quarantined and cannot mutate the worktree or machine state
- [ ] Add named harness cases in `scripts/test_execute_plan_address_fanout.py`: `test_address_fanout_transitive_grouping`, `test_address_fanout_scope_violation_is_quarantined`, `test_address_fanout_subset_retry_requires_termination`, `test_address_fanout_missing_file_data_falls_back`, `test_address_fanout_parent_merge_is_single_commit`, `test_address_fanout_assignment_is_complete`, `test_address_fanout_entrypoint_launches_and_merges_with_worker_doubles`, and `test_address_fanout_late_attempt_receipt_is_quarantined`; use a temporary Git repository, the production `run_address_fanout` entrypoint, deterministic worker doubles, real binary patches, injected attempt ids, and an interleaving where a cancelled first attempt returns after its retry is accepted
- [ ] Add `ExecutePlanRuntimeTest#test_address_fanout_state_round_trip_and_projection_fence` in `scripts/test_execute_plan_runtime.py`; drive the real parent driver API through a reload, assert `runtime_state.json.address_fanout` is the only live authority, and prove a stale projection generation cannot authorize a retry, patch application, or commit while a lock-held finalization renders the manifest and sidecar from one current snapshot
- [ ] In the Step 3.3 verification gate, add the fan-out item: when the round fanned, `the base address log and every per-worker address log exist and are non-empty`, every worker patch has passed the parent scope and attempt witness, the grouping and final worker statuses are recorded in machine state and the manifest, and the sidecar carries `extensions.address_fanout` (Task 4 shape); a missing item relaunches only an eligible affected subset, and never relaunches an attempt whose termination or scope is unverified
- [ ] In the `Sub-Agent Launch Rules` table, change the Address review row to read `Fan-out: up to 3 file-affinity workers in parallel; merge and commit stay parent-owned; otherwise No` and keep the never-parallel wording for implement and done rows untouched
- [ ] Validation: run `python3 scripts/test_execute_plan_address_fanout.py` and `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_address_fanout_state_round_trip_and_projection_fence` (file-form runner: the module form cannot import from the repo root); run focused searches proving the Step 3.3 block contains the canonical file-set input, production parent entrypoint, ephemeral patch workspace, parent patch witness, active-attempt compare-and-swap, two-attempt bound, verified cancellation before retry, terminal blocked subset, authoritative machine-state record, and parent-owned merge; expect GREEN and every dedicated search to pass before committing this task
- [ ] Before committing, stage the helper and harness and run `git diff --cached -- scripts/execute_plan_address_fanout.py scripts/test_execute_plan_address_fanout.py | grep -c "$(printf '\xe2\x80\x94')"` and expect 0
- [ ] Commit/owner: the parent owns the single commit after the task-local gate; commit `skills: execute-plan Step 3.3 file-affinity address fan-out contract`

### Task 2: Address Fan-out Worker template and per-worker log paths

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`

- [ ] Add a `## Address Fan-out Worker` template after `## Address Review`, a variant of it that takes the finding id subset, the canonical allowed files, an opaque worker scope token, attempt id, isolated workspace path, and per-worker log path; it must instruct, using this exact sentence: `Fix only your subset findings on your allowed files; do not touch findings outside your subset, do not edit the review doc (the orchestrator merges), and do not commit.`; it keeps receiving-review per-finding Fix/Triage semantics and scope-limited validation re-runs, but the parent owns all durable backlog items for valid findings it does not fix; the worker must write only its isolated workspace and log, return a binary patch, patch digest, changed-path receipt, token and attempt echo, per-finding triage (done, drop, pending with reason), files changed, and tests run; a timed-out or failed attempt does not authorize the worker to keep writing after the parent requests cancellation
- [ ] In `agent-logs.md` path convention table, add the fan-out row `review-r<R>-receiving-review-w<W>.log.md` (one log per fan-out worker, append-only, same create-versus-append rules), note that in a fanned round the base `review-r<R>-receiving-review.log.md` stays parent-owned (heartbeat plus merge pass), and extend the per-review-iteration done read rule to read that base log `plus every per-worker address log for the round` when the round fanned
- [ ] Extend the `Done (per review iteration)` template's preceding-step list to match: it reads the base address log `or the single address log (no fan-out)` plus every per-worker address log for the round when the round fanned, so the done prompt and the path-convention rule cannot disagree; it also reads the parent merge and terminal-subset receipts before accepting the round
- [ ] Validation: run focused searches proving the template carries the scope token, isolated workspace, binary patch, changed-path receipt, attempt echo, parent-owned backlog rule, cancellation rule, and per-worker log requirements; expect every dedicated search to pass before committing this task
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `skills: address fan-out worker template and per-worker log paths`

### Task 3: receiving-review orchestrated-subset note and review-loop pointer

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [ ] In receiving-review `Staging doc triage outcomes`, add one note before the numbered list: `An orchestrated run may hand the pass a finding subset plus its allowed files; per-finding Fix and Triage semantics are unchanged, the subset worker does not edit the staging doc (the orchestrator merges triage outcomes) and does not commit.`; keep every existing rule intact
- [ ] In receiving-review `Integration Points` with the `execute-plan` skill, extend the row with the fan-out handoff (subset, allowed files, per-worker log path, parent merge) so the provider and consumer describe the same mechanics in both directions
- [ ] In review-loop `Integration Points`, add a note that an orchestrated loop `may fan the step-3 receiving-review pass per the execute-plan Step 3.3 fan-out contract` (file affinity, cap of three, parent merge, one commit per round); the standalone default stays the single step-3 pass
- [ ] State the contract boundary explicitly: `extensions.address_fanout` is emitted and validated only for current-v1 sidecars; versionless legacy sidecars keep the existing single-worker path and are not upgraded by receiving-review; the parent, not any subset worker, writes the sidecar extension and runs the final `--hard` validation
- [ ] Validation: run dedicated searches for the subset note, the bidirectional integration rows, the current-v1-only boundary, the legacy single-worker fallback, and the parent-owned sidecar merge; expect every search to pass before committing this task
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `skills: receiving-review subset note and review-loop fan-out pointer`

### Task 4: review-staging address fan-out accounting and validator gate

Files:
- `agents/skills/review-staging/SKILL.md`
- `scripts/validate_review_staging.py`

- [ ] In review-staging under `## Review Statistics` rules, add a subsection titled `Address fan-out accounting`: fan-out address workers are not Panel rows and `never consume review-time budget or overflow`; per-finding attribution is recorded by the parent as an `Address worker: <id>` line on the finding's Analysis section; the sidecar carries the attribution only for current-v1 records in `extensions.address_fanout` with shape `{"round": "<rN>", "finding_files": [{"id": 1, "files": ["repo/relative/path"]}], "workers": [{"id": "<wN>", "findings": [1], "files": ["repo/relative/path"], "attempts": [{"id": "<attempt>", "status": "success|blocked|cancelled", "reason_code": "completed|worker_error|worker_timeout|cancellation_unverified|ambiguous_patch|scope_violation|stale_attempt|parent_merge_conflict|superseded", "log": "<path>"}], "status": "complete|blocked", "fixed": N, "dropped": N, "deferred": N, "pending": N, "log": "<path>"}]}`; the listed `reason_code` values are the closed address-fan-out enum owned by this subsection, with `completed` required for a successful attempt, `worker_error` or `worker_timeout` required for the corresponding worker failure, and the remaining codes reserved for blocked or cancelled outcomes; this is a `version-1-only` extension; `round` equals the sidecar's `round` after string normalization; every `finding_files` id exists exactly once in the sidecar findings; every file is a non-empty repository-relative normalized path; every worker's files equal the union of its finding file sets; every assigned finding id occurs in exactly one worker; every worker has one or two attempts and a final status; each worker row's four counts sum to its findings length; all assigned ids equal the exact fanned subset recorded by the parent; synthesis tables stay immutable. Versionless legacy sidecars reject `address_fanout` and remain on the single-worker path.
- [ ] In review-staging's consumer table, extend the `receiving-review` row notes with the fan-out attribution obligation (parent-written, validator-checked) so provider and consumer match
- [ ] In `scripts/validate_review_staging.py`, add a shape and conservation gate: `extensions.address_fanout` is legal only on current-v1 records; it must be an object with `round`, `finding_files`, and `workers` of the exact types above, complete unique id sets, canonical relative file paths, worker file-set equality, one-or-two attempt rows, the closed address-fan-out status and reason-code enums with their valid combinations, final status, required log paths, non-negative integer counts, per-row counts summing to the row's findings length, exact round equality, and no finding id in more than one row; any violation fails hard with a message naming `address_fanout`; a versionless record carrying the extension fails closed with a version-boundary message
- [ ] Add table-driven selftests next to the existing extension-shape cases, each labeled with its exact comment: `selftest: address_fanout unknown finding id fails hard`, `selftest: address_fanout count mismatch fails hard`, `selftest: address_fanout duplicate finding assignment fails hard`, `selftest: address_fanout missing round fails hard`, `selftest: address_fanout missing log fails hard`, `selftest: address_fanout malformed type fails hard`, `selftest: address_fanout incomplete assignment fails hard`, `selftest: address_fanout unknown reason code fails hard`, `selftest: address_fanout invalid status reason combination fails hard`, `selftest: address_fanout versionless legacy fails hard`, and one positive case labeled `selftest: address_fanout well-formed shape passes hard` where a well-formed `address_fanout` rides a valid current-v1 sidecar through `--hard`
- [ ] Before committing, stage the validator change and run `git diff --cached -- scripts/validate_review_staging.py | grep -c "$(printf '\xe2\x80\x94')"` and expect 0 (the whole-file em-dash sweep cannot gate this file: pre-existing em-dashes live in frozen regions no task edits)
- [ ] Run `python3 scripts/validate_review_staging.py --selftest`, expect GREEN
- [ ] Validation: run `python3 scripts/validate_review_staging.py --selftest`; expect GREEN, including every named address-fanout case and the current-v1 versus versionless boundary
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `validate_review_staging: address fan-out accounting shape gate with selftests`

### Task 5: Wave-boundary probes and the standing resume watcher (canonical home)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/execute_plan_runtime.py` *(progress revision, interrupt, watcher receipt persistence, and address-fan-out state only; unrelated runtime transitions frozen)*
- `scripts/execute_plan_resume_watcher.py` *(new; workflow-neutral watcher state machine, state adapters, and scheduler boundary)*
- `scripts/test_execute_plan_resume_watcher.py` *(new; hermetic watcher harness)*
- `scripts/quota_window_probe.py` *(shared guard lock around flag replacement only; probe report and fail-open decisions remain frozen)*
- `agents/hooks/budget-guard/budget_guard_core.py` *(shared guard lock around expiry cleanup only; blocking and fail-open decisions remain frozen)*
- `scripts/test_quota_window_probe.py` *(shared guard-lock replacement interleaving witness only)*
- `scripts/test_budget_guard_hooks.py` *(shared guard-lock cleanup interleaving witness only)*
- `agents/hooks/budget-guard/README.md` *(shared guard lock and atomic cleanup contract only)*

- [ ] In the Budget gate section, replace the boundary sentence `At the Step 1.5 and Step 3.5 boundaries only (never mid-task), run:` with: `At the Step 1.5 and Step 3.5 boundaries, before every Phase 3 worker-wave launch (the Step 3.1 panel launch and the Step 3.3 address launch, single or fanned), and never mid-task, run:`; the wave boundaries are probe-only boundaries: finishing the wave launch after a continue needs no additional bookkeeping beyond the manifest outcome line
- [ ] Add a `#### Standing resume watcher` subsection to the Budget gate section: at every budget-gate boundary whose decision is continue and whose probe report contains a trusted binding reset epoch, schedule a one-shot resume automation `reset time plus one minute` after the binding window's reset (rounded up to the whole minute), `self-disarming and idempotent`; a `status: unknown` report is explicitly report-only, schedules no watcher, and names the exact manual resume command; its prompt re-enters execute-plan on the plan path and applies four stand-down checks before any relaunch, each with its own machine-state detection: it `stands down when the semantic progress revision changed after the scheduling point`, it `stands down when a peer session resumed the work`, it `stands down when the plan is archived or completed`, and it `stands down when the run was explicitly aborted or interrupted` (an aborted workflow state in machine state, or a `user_interrupt` field newer than this watcher's scheduling epoch, so a latched old interrupt never trips a later watcher); when no stand-down fires it applies the Step 0.5 resume rules and continues the loop
- [ ] Make watcher state authoritative and fenced: `scripts/execute_plan_runtime.py` persists a monotonic `progress_revision` and a `resume_watcher` object in `runtime_state.json` containing watcher id, plan slug, canonical repository root, canonical plan path, plan-byte digest, scheduling epoch, reset epoch, expected generation, expected progress revision, current boundary generation, binding, status, and replacement predecessor; all writes and replacement, cancellation, supersession, and no-schedule transitions run under the manifest lock with compare-and-swap on watcher id, generation, and boundary generation; `manifest.md` receives a human-readable projection only; a watcher re-reads machine state immediately before firing and refuses to clear guards or relaunch when its id, generation, progress revision, workflow state, canonical repository root, canonical plan path, plan digest, or current boundary generation no longer matches
- [ ] At every budget boundary, atomically record the boundary decision: a known continue decision installs or replaces exactly one watcher, while an unknown, weekly-secondary, pause, abort, or complete decision supersedes and clears any existing pending watcher even when no replacement is scheduled; a stale callback from any superseded watcher self-disarms
- [ ] Implement `scripts/execute_plan_resume_watcher.py` as one workflow-neutral state machine over an explicit `WatcherStateAdapter` and `SchedulerAdapter`: Task 5 provides the runtime-state adapter and Task 6 provides the plans authoring-state adapter; adapters expose the same lock-held read, compare-and-swap replacement/cancellation, semantic-progress, boundary, and projection operations, so the two workflows do not grow separate watcher protocols
- [ ] Implement guard cleanup as an atomic compare-and-delete operation in `scripts/execute_plan_resume_watcher.py`, using a shared `fcntl.flock` lock file at `~/.ai-playbook/runtime/budget-guard.lock` for the probe writer, both hook adapters, the watcher, and fired-marker cleanup; the read, compare, and unlink occur while that shared lock is held, and the writer's `os.replace` also participates in it; never use a standalone re-read followed by unlink or an inode check without writer participation; late callbacks self-disarm without changing current state
- [ ] Give the interrupt stand-down its input: in the `## User Interruption` section of the same file, add one rule line so an interrupted run records `user_interrupt: <ISO8601 timestamp>` in authoritative machine state and projects it into the session manifest: prescribe the writer as a driver operation `--operation interrupt` that persists `user_interrupt` under the manifest lock while keeping `workflow_state` unchanged (a plain interrupt stays resumable), and the User Interruption rule instructs the orchestrator to invoke it; without this line the interrupt branch has no written input and a plain interrupt is indistinguishable from the untouched positive control
- [ ] In `scripts/test_execute_plan_resume_watcher.py`, build a hermetic fake-clock, fake-automation, fake-launchd, temporary-machine-state harness, and real `RuntimeDriver` file-backed integration fixture: assert reset rounding, known-binding scheduling, unknown-budget report-only behavior, idempotent scheduling, replacement and cancellation, known-then-unknown supersession, known-then-weekly-secondary supersession, one-watcher cardinality, semantic-progress and peer-resume stand-down, archived/completed and abort/interrupt stand-down, untouched-state resume, canonical plan-path and digest mismatch, atomic guard compare-and-delete interleavings with the probe writer and backstop hook, fired-marker replacement protection, launchd sentinel self-disable, report-only fallback, exact plan-path prompt, and a crash after the pre-relaunch manifest refresh; the integration fixture must exercise the real `runtime_state.json`, `_manifest_lock`, injected clock, schedule, replace, progress, cancellation, reload, and callback paths, with no live `docs/tmp/` fixtures
- [ ] Include named cases `test_watcher_unknown_budget_is_report_only`, `test_watcher_replacement_is_single_and_fenced`, `test_watcher_stands_down_on_semantic_progress`, `test_watcher_compare_and_delete_does_not_remove_newer_flag`, `test_watcher_known_then_unknown_supersedes_pending`, `test_watcher_known_then_weekly_secondary_supersedes_pending`, and `test_watcher_runtime_driver_persistence_round_trip`
- [ ] Add `test_guard_cleanup_does_not_remove_replaced_flag` to `scripts/test_quota_window_probe.py` and `test_guard_cleanup_does_not_remove_replaced_marker` to `scripts/test_budget_guard_hooks.py`; both must exercise the shared lock with a replacement interleaving and prove the newer flag or fired marker remains
- [ ] In the same subsection, state the replace and cancel rules: `later boundaries replace, never stack, watchers` (the machine state records the superseded watcher id and compare-and-swap result); every non-schedulable boundary also supersedes and clears a pending watcher; `the weekly secondary binding still writes no flag and schedules no watcher`; clean exit or archive leaves the last watcher to stand itself down via its own checks; missing automation capability takes the pause-protocol fallback chain (launchd one-shot with a sentinel self-disable file, then report-only naming the exact resume command and time)
- [ ] Add `pending_resume_watcher` to the Phase 3 `Track in manifest.md` list (value: the scheduled watcher id, or `none`), and add one manifest line per wave-boundary probe outcome in the same list
- [ ] In `### Step 3.1: Parent-orchestrated code review` and `### Step 3.3: Launch address-review sub-agent`, add one line before the launch instruction: run the Budget gate at this wave boundary per the Budget gate section and record the outcome in the manifest before launching
- [ ] In the `Consumes plans skill` integration note, extend the declared-deltas enumeration with `the authoring-boundary watcher deltas` so the canonical note and the mirror note enumerate the same set
- [ ] Validation: run `python3 scripts/test_execute_plan_resume_watcher.py`, `python3 scripts/test_quota_window_probe.py`, and `python3 scripts/test_budget_guard_hooks.py`; run dedicated searches for the wave-boundary sentence, known-binding-only scheduling, unknown report-only branch, machine-state authority, semantic progress revision, compare-and-swap replacement, atomic compare-and-delete cleanup, shared guard lock, and interrupt fence; expect GREEN before committing this task
- [ ] Before committing, stage the watcher helper, test, and runtime change and run `git diff --cached -- scripts/execute_plan_runtime.py scripts/execute_plan_resume_watcher.py scripts/test_execute_plan_resume_watcher.py scripts/quota_window_probe.py scripts/test_quota_window_probe.py agents/hooks/budget-guard/budget_guard_core.py | grep -c "$(printf '\xe2\x80\x94')"` and expect 0
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `skills: wave-boundary budget probes and standing resume watcher (canonical)`

### Task 6: plans-skill Budget gate mirror deltas

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/execute_plan_resume_watcher.py` *(plans state-adapter implementation only; the shared watcher state machine remains owned by Task 5)*
- `scripts/test_execute_plan_resume_watcher.py` *(authoring-adapter and cross-workflow regression cases)*

- [ ] In the plans Budget gate section, extend both authoring boundaries (before launching each review-plan round in the Plan Quality Gate loop; before the final done handoff): on `pause_decision: continue`, `schedule the same standing resume watcher` per the canonical protocol (reset time plus one minute, self-disarming, replaced at each later boundary, stood down on progressed, peer-resumed, archived or completed, or aborted or interrupted where the authoring runtime records an interrupt (same newer-than-scheduling comparison against the authoring machine state, so a latched old interrupt never trips a later watcher); otherwise the scheduling-snapshot and plan-state checks carry the stand-down), with the authoring pause-protocol fallback chain unchanged
- [ ] Define the authoring machine-state home for that mirror: `{tmp_dir}/plan-requirements-<slug>.json` stores `progress_revision`, `user_interrupt`, and the same fenced `resume_watcher` receipt; `{tmp_dir}/plan-requirements-<slug>.md` remains the human notes and audit projection; the watcher never infers authoring progress from Markdown `updated:` text; the authoring loop updates the machine state under the shared watcher lock before and after each review round and done handoff; extend the plans Plan Lifecycle docs/tmp cleanup bullet to delete `{tmp_dir}/plan-requirements-<slug>.json` in the same completion pass as the `.md` notes so the state file cannot outlive its owner under the done sweep
- [ ] Implement the plans `WatcherStateAdapter` in `scripts/execute_plan_resume_watcher.py` and invoke the shared watcher state machine from this skill; it must use the authoring JSON as its authority, project to the Markdown notes only after a lock-held state transition, and share the same replacement, cancellation, boundary generation, canonical plan path and digest, semantic-progress, peer-resume, archive, completion, abort, and interrupt fences as the execute-plan runtime adapter; do not duplicate a second watcher state machine in prose
- [ ] Update the `Canonical home` paragraph's delta list to add `the authoring-boundary watcher deltas` alongside the existing declared deltas, keeping the on-conflict-canonical-wins rule intact
- [ ] Remediate the pre-existing shared-bodies violation this plan's suite gate depends on: in the same Budget gate section, reword the backstop-hook parenthetical `(fixture-verified on zcode; on codex pending the first-start trust-prompt approval and the envelope drive, see the budget-guard README)` to `(fixture-verified on one runtime; pending the first-start trust-prompt approval and the deny-envelope drive on the other runtime, see the budget-guard README)`, so `test_shared_skill_bodies_remain_runtime_neutral` passes again; the failure exists at HEAD (introduced by commit 0b533bab) and would block every later suite gate in this plan; keep the reworded sentence free of every term that test forbids
- [ ] Run `python3 scripts/test_execute_plan_runtime.py`, expect GREEN including `test_shared_skill_bodies_remain_runtime_neutral` (this restores the regression baseline Task 8 relies on)
- [ ] Before committing, stage the watcher-adapter change and run `git diff --cached -- scripts/execute_plan_resume_watcher.py scripts/test_execute_plan_resume_watcher.py | grep -c "$(printf '\xe2\x80\x94')"` and expect 0 (the prose em-dash gate cannot gate these Python surfaces)
- [ ] Validation: run `python3 scripts/test_execute_plan_runtime.py` and `python3 scripts/test_execute_plan_resume_watcher.py`; run dedicated searches for both authoring boundaries, the shared watcher adapter, the machine-state JSON home, the Markdown projection-only rule, the known-binding-only watcher branch, the canonical plan digest fence, and the authoring `user_interrupt` fence; expect GREEN before committing this task
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `skills: plans budget gate mirrors the standing resume watcher`

### Task 7: Batch implement launch contract in execute-plan Phase 1

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

- [ ] In the frontmatter description, replace `implement one task at a time (tests must pass)` with `implement tasks one launch at a time (a launch may batch up to four file-disjoint tasks under the Step 1.2 batch contract; tests must pass)`
- [ ] In Phase 1 `### Step 1.2: Launch implement sub-agent`, add a `**Batch option (disjoint tasks):**` block. Its opening sentence names the mechanism (a `batch implement launch`), states the trigger (the next K unchecked tasks, taken as a prefix of the unchecked queue in canonical document order, with a `cap of four`, `have pairwise-disjoint` canonical `Files:` sets), and bounds worker context (the `combined member file count is capped at 8`); on that trigger the orchestrator MAY batch them into `ONE implement sub-agent launch`, `passes the driver's batch opt-in flag` when claiming a batch, and declines the option by claiming without the flag (a no-flag claim is today's single-task claim); the driver computes the batch membership as the maximal disjoint prefix (cap four, canonical document order, no skipping past an overlapping task, and the combined member file count capped at 8); the worker uses one session and implements only the active member at a time, returns a member checkpoint at each task boundary, and resumes the same session for the next member with a fresh member policy token and moving baseline, writing `into its own task-<N>-implement.log.md` for each member (create or append per agent-logs), so every member's Step 1.4 done reads its own preceding-step log exactly as today; downstream stays exactly as today: `per-task done commits in document order`, per-task verification per the Step 1.2 exit criteria, per-task checkbox flips with a fresh marker refresh per write, per-task driver checkpoints, and K commits with no batch-level commit; state the guardrail sentence `never batch tasks carrying host-wiring exception receipts, inclusion-gate ambiguity, or overlapping files`; the `batch decision and membership are recorded in the session manifest`; state the failure sentence `a failure in batch task j stops the batch`: earlier batch tasks verify, checkpoint, and commit normally, and task j and later recover through the standard fix path; the inclusion hard gate runs on every batched task before the single launch
- [ ] Rewrite Hard Gate 3 to: `One implement launch per iteration, never parallel; a launch may batch up to four file-disjoint tasks as one batch implement launch under the Step 1.2 batch contract; batching never creates a batch-level commit and never launches implement or done in parallel.`; the never-parallel clause is what makes a batch one launch rather than parallel launches, and the address fan-out's parallelism stays governed by the Step 3.3 contract and the launch-rules table, so this gate's clause scopes to implement and done only
- [ ] Update the Step 1.1 rule wording (the live line carries it inside bold markers: `- Implement **one task per iteration**; all clauses in that task section, not the whole plan.`) from `Implement one task per iteration` to read `Implement one launch per iteration`; the launch may be a single task or a batch implement launch under the Step 1.2 batch contract, and all clauses in that iteration's task sections apply; no superseded phrase remains anywhere in the file
- [ ] In `subagent-prompts.md`, add a `## Implement Task Batch` template after `## Implement Task`: it takes the ordered task sections, the per-task canonical `Files:` lists, each task-local validation command, the group id, active member ordinal, member policy token, anchor session id, and per-task implement log paths; it requires `into its own task-<N>-implement.log.md` a per-task section with that task's RED/GREEN evidence, returns a machine-readable member checkpoint before the session advances, forbids cross-task file edits, forbids committing (the orchestrator launches done per task), and returns per-task status blocks plus session and attempt identity; the parent rejects any result whose member, token, ordinal, or changed paths do not match the active group state
- [ ] Keep the mechanism naming single: the Step 1.2 block prose, the Hard Gate 3 rewrite, and the frontmatter replacement all call the mechanism a `batch implement launch` or reference it by the Step 1.2 batch contract label; the block title and the template heading stay literal titles
- [ ] Validation: run dedicated searches proving the canonical prefix, member-scoped session, fresh policy token and moving baseline, one-launch/no-batch-commit rule, failure stop rule, batch opt-in, and task-local validation handoff; expect every search to pass before committing this task
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `skills: batch implement launch contract for file-disjoint tasks`

### Task 8: Driver support for batch implement launches (RED then GREEN)

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/runtime_capabilities.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] RED: add the batch, adapter, capability, CLI, reload, and late-receipt tests below in `given/expects` form; run the task-local suites and record the RED/GREEN split in the batch implement log. Do not weaken a test to force RED. Tests that pin today's default-off single-task behavior may be GREEN before implementation; the new group, session, and member-boundary tests must be RED until their implementation lands.
- [ ] `ExecutePlanRuntimeTest#test_batch_claim_assembles_canonical_disjoint_prefix`; given three consecutive pending tasks whose manifest-seeded canonical `allowed_paths` are disjoint, expects one opted-in claim to create one group with ordered members, explicit ordinals, one generation bump, and member claims referencing that group
- [ ] `ExecutePlanRuntimeTest#test_manifest_create_persists_canonical_paths_and_document_ordinals`; given raw `Files:` entries through the real `create_manifest` and CLI `--operation create` paths, including both `./a` versus `a` and an in-repository symlink versus its target, expects canonical `allowed_paths` and document ordinals after reload, rejects duplicate canonical paths within one task, and retains cross-task overlap for queue stopping rather than silently rewriting it
- [ ] `ExecutePlanRuntimeTest#test_batch_claim_stops_at_canonical_alias_overlap`; given cross-task aliases that resolve to the same canonical path, expects the maximal batch prefix to stop before the overlap or use the single-task fallback, never a falsely disjoint group; both lexical and symlink alias fixtures are mandatory
- [ ] `ExecutePlanRuntimeTest#test_batch_claim_stops_at_overlap_and_caps`; given an overlapping next task and then six disjoint tasks, expects the maximal prefix to stop before the overlap and never exceed four members or eight combined canonical files
- [ ] `ExecutePlanRuntimeTest#test_batch_claim_single_task_and_no_opt_in_are_field_free`; given one pending task or a no-flag claim, expects no batch fields and today's single-task result
- [ ] `ExecutePlanRuntimeTest#test_batch_group_has_one_anchor_launch_record`; given a three-member group, expects an explicit `claim_groups` record with anchor, ordered members, active member, group generation, group state, and one launch-record slot; member claims hold only their own canonical paths, member token, ordinal, and group reference
- [ ] `ExecutePlanRuntimeTest#test_batch_member_policy_is_scoped`; given a worker result or resume for member 1 that changes member 2's file, expects the member-1 checkpoint and done boundary to reject the foreign path even though the group contains both files; a witness-only union, if needed for diagnostics, must not authorize actions
- [ ] `ExecutePlanRuntimeTest#test_batch_member_progress_resumes_anchor_session`; given member 1 success and done commit, expects the group to advance atomically to member 2, retain the immutable group launch identity and single anchor session, create a per-member attempt record with a fresh member-2 token and baseline, and resume without a second launch record
- [ ] `ExecutePlanRuntimeTest#test_batch_done_returns_typed_resume_member_action`; given member 1 done, expects `record_done` to atomically close member 1 and return a typed `resume_member` action naming the group, next member ordinal, anchor session, fresh policy token, and moving baseline; a first member may use `launch`, but later members may use only `resume`
- [ ] `ExecutePlanRuntimeTest#test_batch_member2_witnesses_from_member1_done`; given a four-member batch and a fresh driver reload at every boundary, expects each member to witness only its own changes against the immediately preceding member commit and to reject a foreign path or stale predecessor
- [ ] `ExecutePlanRuntimeTest#test_batch_mid_member_failure_preserves_prefix_and_suffix`; given member 2's checkpoint blocked or timed out, expects member 1 closed, member 2 blocked with its attempt receipt, later members pending, and resume to select only the first unfinished member through the anchor session
- [ ] `ExecutePlanRuntimeTest#test_batch_done_closes_members_individually`; given per-member done handoffs in document order, expects each member claim closed at its own boundary and the group released only after the last member
- [ ] `ExecutePlanRuntimeTest#test_batch_late_receipt_is_rejected`; given a success, error, done, or checkpoint receipt for a closed, superseded, aborted, or old-attempt member, expects a blocked stale-claim outcome with no state mutation
- [ ] `ExecutePlanRuntimeTest#test_claim_blocked_while_batch_live`; given a live group, expects a second group claim to retain today's blocked stale-claim outcome
- [ ] `ExecutePlanRuntimeTest#test_cli_batch_opt_in_and_no_flag_control`; given a temporary manifest and explicit `--repo-root`, expects the real `--operation claim --batch` entrypoint to persist a group and the no-flag entrypoint to persist one task only
- [ ] `ExecutePlanRuntimeTest#test_batch_wrapper_opt_in_and_no_flag_control`; given a live manifest, expects `launch_next_task(batch=True)` and `continue_parent(batch=True)` to propagate the opt-in and create or resume the group, while both no-flag calls preserve today's single-task behavior
- [ ] `ExecutePlanRuntimeTest#test_cli_continue_batch_opt_in_and_no_flag_control`; given a reloaded live group and explicit `--repo-root`, expects the real `--operation continue --batch` entrypoint to resolve the active member and resume the anchor session, while no flag uses the existing single-task continuation
- [ ] `CodexAdapterTest#test_batch_progress_translation_and_anchor_resume`; given host envelopes with ordered member progress, attempt, batch id, member ordinal, and one session id, expects normalized results to preserve those fields and `resume` to use the anchor session with the active member prompt and policy token
- [ ] `RuntimeCapabilitiesTest#test_batch_result_and_member_policy_validation`; given missing, stale, mismatched, or cross-member tokens and malformed partial-progress envelopes, expects fail-closed validation; given a valid active-member receipt, expects success
- [ ] GREEN: implement `scripts/execute_plan_runtime.py` with named `create_manifest` and `_operation_create` canonicalization: normalize raw `Files:` to persisted canonical `allowed_paths`, reject within-task canonical duplicates, retain a persisted document ordinal, and make claim, pending selection, `launch_next_task`, `continue_parent`, reload, and member advancement consume that ordinal; default-off `batch` opt-in on claim, CLI, `launch_next_task`, and `continue_parent`; an authoritative `claim_groups` mapping with an immutable group launch identity, ordered members, active member, group generation, state, anchor, anchor session, one launch record, semantic progress revision, and per-member attempt record; one generation bump per group; member claims with individual canonical allowed paths, a member-scoped policy token, member ordinal, attempt, moving baseline, and group reference; only the active member may launch, checkpoint, resume, or close; member done advances the group under the manifest lock, returns the typed `resume_member` action, initializes the next member from the completed member commit, and suppresses generic next-claim until the group closes; reload resolves the active member and anchor session from the group; old or late receipts fail closed
- [ ] GREEN: implement `scripts/execute_plan_runtime_codex.py` and `scripts/runtime_capabilities.py` with an optional batch-progress result envelope containing batch id, member id and ordinal, attempt, status/evidence, and anchor session id; one initial launch record remains on the group, later members resume that session, and every launch/resume uses the active member's own policy token; reject malformed, stale, or mismatched member receipts
- [ ] GREEN: update `agents/skills/execute-plan/runtime-contract.md` and `agents/skills/done/SKILL.md` so the normative state documents the batch claim group, group/member protocol, one launch plus same-session member resumes, member-scoped authorization and done staging, moving baselines, active-member ordering, late-receipt fencing, and the unchanged no-batch single-task path; keep unrelated transitions frozen
- [ ] Run `python3 scripts/test_execute_plan_runtime.py`, `python3 scripts/test_execute_plan_runtime_codex.py`, and `python3 scripts/test_runtime_capabilities.py`; expect GREEN including all pre-existing tests and the CLI subprocess witness
- [ ] Before committing, stage the driver, adapter, capability, test, and contract changes and run `git diff --cached -- scripts/execute_plan_runtime.py scripts/execute_plan_runtime_codex.py scripts/runtime_capabilities.py scripts/test_execute_plan_runtime.py scripts/test_execute_plan_runtime_codex.py scripts/test_runtime_capabilities.py | grep -c "$(printf '\xe2\x80\x94')"` and expect 0 (pre-existing em-dashes live in frozen regions no task edits, so the gate scopes to this task's staged lines)
- [ ] Run the three task-local suites twice more, once after the batch contract wording lands if ordering shifted and once before this plan's final validation; expect GREEN both times
- [ ] Validation: run the three task-local suites and verify the named group, member-token, active-member, canonical-path, CLI, and late-receipt witnesses are present in the implementation and tests before committing this task
- [ ] Commit/owner: the parent owns the commit after the task-local gate; commit `execute_plan_runtime: batch implement launch claim groups with member-scoped session protocol`

### Task 9: Final validation and cross-contract sweep

Files:
- none (verification only; no file edits in this task)

- [ ] Run the full `## Validation Commands` block from the repo root; expect exit 0 with `VALIDATION OK`
- [ ] Run `python3 scripts/test_execute_plan_runtime.py` and `python3 scripts/validate_review_staging.py --selftest` once more with fresh output and expect GREEN (fresh test output per Hard Gate 9 of the executing skill; never cite stale runs)
- [ ] Run the fail-closed superseded-mechanics sweep over every explicit must-fix surface, including `agents/skills/done/SKILL.md`: normalize all whitespace and line breaks before checking each of `One task per implement iteration`, `At the Step 1.5 and Step 3.5 boundaries only`, `implement one task at a time`, and `one task per iteration`; tool errors are failures, and a temporary RED witness with a phrase split across Markdown lines must be detected before the real surfaces are checked; none of the changed surfaces may reintroduce the old wording
- [ ] Validation/owner: Task 9 owns the full validation block and fresh test output; it performs no edits and creates no commit
