# Plan: Execute-plan runtime residuals

Close the residual findings from the agent-agnostic execute-plan runtime work in one pass: launch-record drift detection, driver state and locking corrections, registry and validator de-duplication, hermeticity witnesses, done-lock cleanups, and contract prose consolidation. (The r6 out-of-tree policy-anchor proposal is deferred by the 2026-09-11 threat-model decision; see Decision points and the deferred backlog item.)

Backlog origins (scope of record; moved to `docs/history/backlog/completed/` at completion):

- `docs/history/backlog/2026-09-09-agent-agnostic-plan-prose-accuracy-residuals.md`
- `docs/history/backlog/2026-09-09-execute-plan-runtime-r4-deferred-findings.md`
- `docs/history/backlog/2026-09-09-execute-plan-runtime-r5-deferred-findings.md`
- `docs/history/backlog/2026-09-10-execute-plan-runtime-r6-findings.md`
- `docs/history/backlog/2026-09-09-runtime-hermeticity-witness-gaps.md`

Plan review: `docs/reviews/*plan-review-execute-plan-runtime-residuals*.md` (latest staged round by round number; findings folded before the next review).

Guidance: `projects/.ai-playbook/agent_workflow_guidelines.md` (plan quality sections).

## Terms

- **Continuation driver**: the deterministic state machine in `scripts/execute_plan_runtime.py` that owns the runtime manifest and selects the next workflow step.
- **Runtime manifest**: the driver-owned durable state file recording tasks, claims, checkpoints, and policy scope; its path and ownership are owned by the runtime contract.
- **Launch record**: the snapshot the driver writes on a claim at launch (`baseline_revision`, `generation`, `launched_at`); the drift checks compare the live manifest against it.
- **Scope witness**: the driver checks that compare worktree and committed paths against the claim policy: `_worktree_scope_violation`, `_git_changed_paths`, `_git_diff_paths`, and the done-boundary verification inside `record_done`.
- **Policy token**: the capability receipt structure that authorizes adapter launch, wait, and resume operations.
- **Hermeticity witness**: a test that asserts the runtime does not read or leak host state (environment sanitization, live-installation read denial, fixture-root confinement).

## Assumptions

- assume the scope is exactly the union of the five backlog origins; no other runtime work enters this plan; basis: the authoring task names the five items as the scope of record and each item enumerates its findings.
- assume origin finding line numbers have shifted since capture; tasks pin symbol and test names instead; basis: authoring probes on the current tree (for example the adapter special case sits at `scripts/runtime_capabilities.py:277` today, the fixed retry key `#attempt-initial` at `scripts/execute_plan_runtime.py:599`, the `core.quotePath=false` witnesses at lines 1007, 1018, 1054, and 1068).
- assume completed-history artifacts stay body-immutable; the prose-accuracy origin closes as a recorded disposition with no edit to `docs/plans/completed/2026-09-09-agent-agnostic-execute-plan.md`; basis: doc-hierarchy "Document states" and the doc-hierarchy-upkeep refusal rule (ADR-0003); the errata record already lives in the origin item.
- assume the runtime is exercised on a host with `python3` and `git` on `PATH`; basis: every existing script and selftest in this area requires both.
- assume the public-hygiene scanner can resolve its deny patterns: the Validation block exports a repo-rooted fallback (`docs/scan-public-hygiene.patterns.example`) when no host-local patterns file exists; basis: the scanner exits fatal without patterns, and the fallback keeps the final gate reproducible from a clean clone.
- assume tests follow the repo's unittest discovery and bash selftest conventions; basis: the completed runtime plan's Validation Commands and the existing `scripts/test_*.py` layout.

Decision points requiring a grill: policy anchor design = DEFERRED (threat-model): the r6 F1 out-of-tree digest anchor and all anti-adversarial-worker mechanisms are out of this plan's scope per the 2026-09-11 user threat-model decision (`projects/.ai-playbook/agent_workflow_guidelines.md` section 64; backlog `docs/history/backlog/2026-09-11-deferred-malicious-worker-hardening.md`); Task 2 instead adds the minimal launch-record snapshot for honest-concurrency drift detection; source: user decision on 2026-09-11 after the r9-r14 re-cert loop; date: 2026-09-11; affected sections: Task 2, Task 12, Gist & Examples. Inventory shape = deferrals section with reason "no verified adapter"; source: r4 origin first-listed option; date: 2026-09-10; affected sections: Task 5. Untracked-noise outcome = resumable `cleanup-required` blocked result on the pre-launch startup path only; post-launch ambient noise keeps the hard block (per Task 3, launch-record presence is the discriminator); source: r6 origin first-listed option as qualified by review round r9; date: 2026-09-10; affected sections: Task 3. Prose-accuracy errata = recorded disposition without body edits to the completed plan; source: doc-hierarchy Document states plus the upkeep refusal rule (ADR-0003); date: 2026-09-10; affected sections: Task 12.

## Design Invariants (CR Guard)

- Fail-closed direction: every check this plan adds or changes fails closed on absence, mismatch, ambiguity, or error (baseline or generation changed on a launched claim, `OSError` in the escape check, committed symlink, zero retry budget); no new fail-open path is introduced.
- Manifest preservation on block: blocked outcomes preserve the manifest and never relaunch an ambiguous worker; the driver still never performs the commit itself.
- Launch record: a production launched claim carries a launch-record snapshot (baseline revision and generation); pre-launch claims carry none and undergo no drift checks; no out-of-tree state is introduced (threat-model decision, guidelines section 64).
- Adapter thinness: the Codex adapter keeps translating host protocol only; shared skill bodies stay runtime-neutral; after Task 7 the adapter imports nothing from the driver module.
- Authorization boundary unchanged: no operation gains automatic approval; the done handoff, gated-action policy, and approval-receipt semantics stay as landed, and the receipt stays operator-attested.

## Gist & Examples

The deferred residuals from five backlog origins (r4-r6 findings plus the r8 overflow fold, re-certified through the r9-r14 loop) instead of regenerating findings in capped rounds. This plan closes them in one pass, grouped into four families: policy and boundary hardening (r6 F2-F4, F8-F10, F12, F13; r6 F1 deferred by the threat-model decision), driver state and locking (r5 F5-F8, F16, overflow items), registry and contract structure (r4 F13-F15, F18, r5 F17, r6 F5, F6, r5 F11, overflow items; Task 7 executes the adapter-edge, kill-order, and retry-clamp findings and spans this and the driver family), and witness plus documentation accuracy (the hermeticity origin, r6 F11, r5 F9-F10, F14-F15, and the prose-accuracy origin).

Before (today): a same-user worker process can quietly edit the gitignored runtime manifest to widen `allowed_paths` or erase `baseline_revision`; both scope witnesses read only tracked worktree state (`git status --porcelain` variants without `--ignored`), so the tampering is invisible and out-of-scope files can be committed under the widened policy. On the same code path, a second consecutive worker error overwrites the first attempt's durable checkpoint record (the fixed `#attempt-initial` key), owner identity is read from an unlocked manifest snapshot, adapter resume runs while the manifest flock is held, and a profile-less CLI construction silently downgrades durable capability receipts to `unsupported`.

After (this plan): at claim launch the driver records a launch snapshot (`baseline_revision`, `generation`, `launched_at`) on the claim under the manifest lock; both scope witnesses compare the live manifest against that snapshot and surface the resumable `stale-claim` outcome if another session rewrote the manifest mid-run, while legitimate checkpoints and checkbox updates leave the snapshot untouched. Out-of-tree tamper-detection fencing (the r6 digest-anchor proposal and everything built on it) is deferred by the threat-model decision: honest sessions need drift detection, not adversarial proofing (guidelines section 64). Retry records carry a derived attempt ordinal so two consecutive errors stay two records; owner resolution and capability receipts happen under the manifest lock; adapter I/O runs outside the flock.

More before and after pairs, one per family. Registry: `resolve_adapter()` today special-cases `runtime-adapter:codex` by name inside the provider-neutral registry module, and the inventory declares seven lifecycle capabilities for eight profiles that consumers never read; after this plan the registry resolves adapters generically from the inventory's `adapter_entrypoint` declaration (the single normative source) through the module's import table, and the seven no-adapter runtimes join `pi` in the deferrals section (each of the seven carrying reason "no verified adapter"; `pi` keeps its existing reason). Validators: the two divergent codex-local policy-token validators become one parameterized validator in `runtime_capabilities.py`, called at both the launch-validity and claim-revalidation boundaries, and `load_approval_receipt` starts requiring owner-only permissions and a config-policy cross-check instead of validating JSON shape alone. Witnesses and docs: the hermeticity suite gains discriminating tests for environment sanitization, live-installation read denial, and the ambient package-manifest read, and the capability-boundary paragraph keeps one full statement in `runtime-contract.md` with pointer sentences in the hook READMEs instead of a restated copy in `agents/hooks/skill-gate/README.md` (the verbatim copy the single-home grep keys on lives in `agents/hooks/lessons-recall/README.md`).

Edge cases covered: a `retry_budget` of 0 grants zero retries instead of one; ambient untracked noise (`.DS_Store`, editor swaps) present before the claim's launch record blocks with a resumable `cleanup-required` outcome instead of a non-resumable dead end, while the same noise appearing after the launch record keeps the hard block (launch-record presence, not mtime, is the discriminator); a committed symlink at an allowed in-scope path pointing outside the repo is rejected at the done boundary; a recycled PID inside the timeout poll window is never signaled before its identity is consulted.

## Evaluation Criteria

**Quality dimensions:**

- Security: approval receipts require owner-only permissions and a config-policy cross-check; the timeout kill path consults identity before `SIGKILL`; anti-tamper fencing is out of scope by the threat-model decision (guidelines section 64) and deferred with the r6 F1 origin.
- Correctness: two consecutive retry errors produce two durable records; owner identity and capability receipts are consistent under concurrent construction; adapter I/O never holds the manifest flock; every fail-closed small (baseline or generation change on a launched claim, `OSError`, porcelain escaping, zero budget) behaves as specified.
- Maintainability: one policy-token validator, one adapter-resolution mechanism, one full capability-boundary statement, one seeding operation, and the checkpoint recorder and done boundary split into named helpers.
- Testability: every witness added or kept by this plan intersects the code under test; each new hermeticity witness has a recorded mutation probe that flips it.
- Documentation accuracy: the completed plan body stays untouched and the errata disposition is recorded; contract prose has one home with pointers; the README catalog row sits beside the skill entry.

**Done when:**

- All 12 tasks are checked off with their commits landed and each task's gates green at its task point.
- The Validation Commands block exits 0 on the final tree, including the structural greps that are RED today and flip GREEN as the tasks land.
- The five backlog origins are moved to `docs/history/backlog/completed/` with `Status: done` and their per-item disposition notes, and this plan is archived per the plans lifecycle (registry row appended when the ownership-registry convention is present).
- A fresh review round on the final digest reports `ready=yes` with zero unresolved blocking findings.

**Ship when:**

- Each host's staged package is re-activated via `scripts/runtime_capabilities.py --activate <runtime> --source agents/skills/execute-plan` (byte parity plus the harmless lifecycle probe) so loaded copies pick up the changed driver, adapter, and registry.
- The Codex path is exercised once in its real runtime after re-activation; missing host prerequisites are recorded as an explicit release blocker, not silently treated as repository success.
- A human reviews and merges the changes; push and deploy remain explicit human actions.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/runtime_capabilities.py`
- `scripts/done-lock.sh`
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `scripts/hooks_probe.py`

**Tests:**

- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/testdata/execute-plan/expected-runtime-ids.json`
- `scripts/testdata/execute-plan/activation/` (committed `loaded/` copies deleted; tree generated at test setup)

**Documentation:**

- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/plan-readiness/README.md`
- `projects/.ai-playbook/agent-runtime-layout.md` (registry eligibility mirror refreshed by Task 5)
- `README.md`

**Backlog and plan lifecycle (completion pass):**

- `docs/history/backlog/` (the five origin items move to `docs/history/backlog/completed/` with `Status: done`)
- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (this plan's own checkbox updates and archive move)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `docs/plans/completed/**`; completed-history artifacts are body-immutable (doc-hierarchy refusal rule); this plan edits none of them.
- `docs/reviews/**` historical round artifacts; they are records, not edit targets.
- Vendor runtime source code or hosted service behavior; adapters translate, never change, the vendor.
- Push, deploy, merge, and external communication; these stay release or approval decisions.

## Cleanup scope ledger

- Base ref: the execute-plan Phase 0 branch base (main at execution start). All plan work lands as this plan's own commits on the Phase 0 branch.
- Task-owned paths: the Review Scope explicit must-fix list, plus the five backlog origin paths in the completion pass only (move plus `Status:` line edit; body text beyond the status line untouched).
- Frozen areas: `docs/plans/completed/**` (no body edits, including the prose-accuracy errata target `docs/plans/completed/2026-09-09-agent-agnostic-execute-plan.md`); `docs/reviews/**` round artifacts; peer-session files.
- Deletion permissions: committed copies under `scripts/testdata/execute-plan/activation/loaded/` (regenerated at test setup); `load_lock_session` in `scripts/done-lock.sh`; dead `read_label`; the codex-local policy-token validator functions after unification; the `MAX_EVIDENCE_BYTES`/`bounded_evidence` definitions in `scripts/execute_plan_runtime.py` after the move to `runtime_capabilities.py` (imports retargeted in the same commit).
- Keep/defer disposition: anything else dirty or deleted on the execution branch is outside this ledger; classify before touching, and leave peer-owned work alone.
- Mechanical check: `python3 scripts/check_cleanup_scope_baseline.py --repo-root . --base main` with this ledger's task-owned and deletion paths as `--allow` entries must pass at the final task.

## Validation Commands

```bash
set -u
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

run_check() {
  "$@" || { echo "validation failed: $*" >&2; exit 1; }
}

# expect_no_match: rc 0 = forbidden match found (fail), rc 1 = clean (pass),
# rc >= 2 = tool error (abort). Three-way split per the authoring rules.
expect_no_match() {
  pattern="$1"; shift
  rc=0
  grep -rn -F -- "$pattern" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "forbidden pattern present: $pattern" >&2; exit 1; fi
  if [ "$rc" -ge 2 ]; then echo "grep error rc=$rc for: $pattern" >&2; exit 1; fi
}

expect_match() {
  pattern="$1"; shift
  grep -q -F -- "$pattern" "$@" || { echo "required pattern absent: $pattern" >&2; exit 1; }
}

run_check python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'
run_check python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'
run_check python3 scripts/runtime_capabilities.py --selftest
run_check python3 scripts/execute_plan_runtime.py --selftest
run_check python3 scripts/hooks_probe.py --selftest
run_check bash scripts/done-lock.sh selftest
run_check python3 scripts/skill_gate.py --selftest
run_check python3 scripts/check_cleanup_scope_baseline.py --selftest
run_check python3 scripts/plan_readiness.py --selftest

# Structural obligations, one search per obligation.
expect_no_match 'runtime-adapter:codex' scripts/runtime_capabilities.py
expect_no_match 'runtime-adapter:codex' projects/.ai-playbook/execute-plan-runtime-inventory.toml
expect_no_match '#attempt-initial' scripts/execute_plan_runtime.py
expect_no_match 'load_lock_session' scripts/done-lock.sh
expect_no_match 'read_label' scripts/done-lock.sh
expect_no_match 'DONE_LOCK_GENERATION' scripts/done-lock.sh
expect_no_match 'from execute_plan_runtime import' scripts/execute_plan_runtime_codex.py
expect_no_match '_valid_policy_token' scripts/execute_plan_runtime_codex.py
expect_no_match '_validate_policy_token' scripts/execute_plan_runtime_codex.py
if [ -e scripts/testdata/execute-plan/activation/loaded ]; then echo "committed activation loaded tree still present" >&2; exit 1; fi
expect_match 'SAFE_ENV_KEYS' scripts/test_execute_plan_runtime_codex.py
expect_match '_operation_create' scripts/execute_plan_runtime.py
expect_match 'no verified adapter' projects/.ai-playbook/execute-plan-runtime-inventory.toml
expect_match 'for the normative runtime contract, result schema, policy boundary, manifest ownership, and continuation transitions' agents/skills/execute-plan/SKILL.md
count="$(grep -rls 'cannot enforce a policy when its event' agents/ | wc -l | tr -d ' ')"
[ "$count" = "1" ] || { echo "capability boundary full statement must live in exactly one file, found $count" >&2; exit 1; }
expect_match 'cannot enforce a policy when its event' agents/skills/execute-plan/runtime-contract.md
run_check python3 -c 'import pathlib,re; t=pathlib.Path("scripts/execute_plan_runtime.py").read_text(); n=len(re.findall(r"\"-c\",\s+\"core[.]quotePath=false\"", t)); assert n == 5, n'
expect_no_match '"git", "status"' scripts/execute_plan_runtime.py
expect_no_match '"git", "diff"' scripts/execute_plan_runtime.py
export PUBLIC_HYGIENE_PATTERNS_FILE="${PUBLIC_HYGIENE_PATTERNS_FILE:-$REPO_ROOT/docs/scan-public-hygiene.patterns.example}"
run_check bash scripts/scan-public-hygiene.sh
```

Notes: the `expect_no_match` sweeps over `runtime-adapter:codex`, `#attempt-initial`, `load_lock_session`, `read_label`, `DONE_LOCK_GENERATION`, the adapter import edge, `_valid_policy_token`, and the committed `loaded/` tree are intentionally RED at authoring (each fires on today's tree; verified during authoring) and flip GREEN exactly when the corresponding task lands. The `expect_match` pins flip GREEN with their owning tasks: the `_operation_create` symbol with Task 8, the inventory deferrals reason with Task 5, the SKILL.md pointer sentence with Task 10, and `SAFE_ENV_KEYS` with Task 11; the capability-boundary single-home count is 2 today (the `lessons-recall` README carries a copy) and must reach exactly 1 after Task 10's pointer conversion. The single-home grep keys on the exact contract sentence; the skill-gate README pointer must not reuse that sentence. The em-dash rule is enforced at authoring over this plan file only; edited files are not swept for pre-existing content this plan does not touch. The inventory `runtime-adapter:codex` sweep line (r8 overflow fold) was RED at this fold's own authoring and flips GREEN with Task 5 together with the module sweep. The `"git", "status"`/`"git", "diff"` negative sweeps are intentionally RED at authoring (the unflagged `_git_worktree_dirty` invocation matches today) and flip GREEN with Task 3, which also moves the exact quotePath count pin from four to five flagged sites; the sweeps guard the count against new unflagged invocation sites from then on, and the hygiene scan runs with the repo-rooted patterns fallback exported two lines above.

### Task 1: Split the checkpoint recorder and done boundary (r6 F12, F13)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] Run → expect GREEN (characterization, captures behavior before refactor): `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`; in particular `test_done_commit_boundary`, `test_commit_before_checkpoint_reconciles`, `test_success_checkpoint_selects_next_incomplete_step`, `test_worker_permission_request_does_not_pause_authorized_work`, and `test_atomic_claim_prevents_duplicate_launch` pass unchanged.
- [x] Extract `_done_boundary_block`: the shared done-boundary verification (launch baseline lookup, committed-path scope and escape checks) extracted from `record_done`; Task 1 itself changes no outcomes, and Task 3's RED witness wires `reconcile_commit_before_checkpoint` to call the same helper.
- [x] Extract `_complete_and_claim`: the shared success-path completion and next-claim transition used by the checkpoint success path and the done handoff.
- [x] Split `record_worker_checkpoint` so retry and blocked handling (budget accounting, retry launches) is separate from the success-path commit that calls `_complete_and_claim`; no behavior change.
- [x] Run → expect GREEN: the same discovery command; all characterization witnesses still pass with the helpers in place.
- [x] Commit: `refactor: split checkpoint recorder and done boundary helpers`

### Task 2: Launch-record snapshot and drift detection (r6 F1 deferred; concurrency correctness)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `ExecutePlanRuntimeTest#test_launch_record_written_at_claim`; given a claim launch, expects the claim to carry a launch record (`baseline_revision`, `generation`, `launched_at`) written atomically with the claim transition under the manifest lock; pre-launch seeded claims carry no launch record.
- [x] `ExecutePlanRuntimeTest#test_baseline_or_generation_change_maps_to_stale_claim`; given a launched claim whose manifest `baseline_revision` is erased or changed, or whose generation is replaced, by another session after launch, expects both the worktree scope witness and the done-boundary verification to surface the resumable `stale-claim` outcome, manifest preserved, no commit handoff; legitimate checkpoints and checkbox updates keep the snapshot valid and both witnesses green.
- [x] `ExecutePlanRuntimeTest#test_pre_launch_claim_has_no_drift_checks`; given a genuinely pre-launch claim (no launch record, no recorded checkpoints, pending status), expects no drift checks (seeded claims keep working unchanged); a claim in any post-launch state (recorded checkpoints or a non-pending status) whose launch record is missing — for example written by the pre-change driver during the re-activation or rollback window — maps to the resumable `stale-claim` outcome instead of the exemption, so record absence never disarms drift detection on a claim that has demonstrably launched.
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`; the launch record does not exist yet.
- [x] Implement the launch record on the claim launch path: the production launch atomically records `baseline_revision`, `generation`, and a launch timestamp on the claim under the manifest lock, and both drift checks compare the live manifest against that snapshot through one shared helper (for example `_claim_drift_outcome`) that consumes a manifest snapshot read under the manifest lock (never an ambient unlocked read), mapping a change to the resumable `stale-claim` outcome (already in `RESUMABLE_REASONS`; no new reason codes); a genuinely pre-launch claim (no launch record, no recorded checkpoints, pending status) undergoes no drift checks, while a claim in any post-launch state with a missing launch record maps to `stale-claim` (record absence never disarms detection on a demonstrably launched claim, covering manifests written across the re-activation or rollback window); document the launch record, the post-launch-state rule, and the locked-read discipline in `runtime-contract.md` beside the manifest ownership section.
- [x] Run → expect GREEN: the discovery command passes including the three new witnesses.
- [x] Commit: `feat: launch-record snapshot with drift detection`

### Task 3: Witness fail-closed and usability smalls (r6 F4, F9, F8, F2, F10, F3)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/runtime_capabilities.py`
- `scripts/test_runtime_capabilities.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_path_escape_check_fails_closed_on_oserror`; given `_path_escapes_repo` raising `OSError` for a candidate path (injected failure), expects the path treated as escaping (fail closed) or the outcome escalated to `unavailable`, never a pass.
- [x] `ExecutePlanRuntimeTest#test_porcelain_witness_parses_escaped_paths`; given a worktree file whose name contains a double quote, which git C-quotes even with `core.quotePath=false`, created outside the allowed paths, expects the witness using `git status --porcelain -z` (or an equivalent C-unquote) to report the real path as out of scope, not the quoted form; a non-ASCII name alone does not discriminate because all four invocation sites already pass `core.quotePath=false` (authoring-verified).
- [x] `ExecutePlanRuntimeTest#test_done_boundary_rejects_committed_symlink_escape`; given a commit containing a symlink (blob mode 120000, checked via `git ls-tree`) at an allowed in-scope path pointing outside the repo, expects the done-boundary verification in `_done_boundary_block` to block the handoff.
- [x] `ExecutePlanRuntimeTest#test_reconcile_runs_done_boundary_verification`; given `reconcile_commit_before_checkpoint` on a commit containing an out-of-scope path, expects the same blocked boundary outcome as `record_done` produces for the same commit.
- [x] `ExecutePlanRuntimeTest#test_post_claim_ambient_noise_stays_hard_blocked`; given only ambient untracked files (for example `.DS_Store`) appearing after the claim's launch record, expects the same non-resumable blocked stance as worker-caused escapes (post-launch, mtime is not the ambient-versus-worker discriminator because a worker can forge it; only the pre-launch startup path stays resumable `cleanup-required`).
- [x] `ExecutePlanRuntimeTest#test_post_launch_untracked_escape_stays_hard_blocked`; given an untracked out-of-policy path appearing after the claim's launch record, expects the existing non-resumable blocked stance (the pinned untracked-escape witness keeps its hard outcome; launch-record presence, not an mtime comparison, is the ambient-versus-worker-caused discriminator).
- [x] Rework `_git_worktree_dirty` (today the only unflagged git invocation, `git status --porcelain` without `core.quotePath=false` or `-z`) to route through the same flagged `-z` enumeration the scope witness uses (one shared git-invocation helper), feeding the ambient-noise allowlist on `reconcile_startup` and `continue_parent`; the Validation quotePath count pin moves from four to the resulting five flagged sites in this same commit.
- [x] `ExecutePlanRuntimeTest#test_startup_ambient_noise_is_resumable_cleanup_required`; given untracked files matching the ambient-noise allowlist (`.DS_Store` and editor-swap patterns) hitting the startup dirty-worktree path (`reconcile_startup` and `continue_parent` before launch), expects a resumable `cleanup-required` outcome instead of the non-resumable `dirty-worktree` block; anything outside the allowlist, including tracked modifications, keeps the hard block on the same path (mtime is not used as a discriminator on either side of the launch boundary, because a worker can forge it).
- [x] Run → expect RED: the discovery command; the five genuinely new behaviors are red, while the two post-launch hard-block witnesses pin existing behavior and arrive green (characterization pins, not RED steps).
- [x] Implement the five genuinely new behaviors in the witness and boundary paths (the other two witnesses are characterization pins requiring no production change), keeping every new branch fail closed per the Design Invariants; register the new `cleanup-required` reason (resumable: yes) in the closed `REASON_CODES` and `RESUMABLE_REASONS` sets in `runtime_capabilities.py` (no other new reasons are introduced; `stale-claim` is already registered), update `test_reason_code_set_is_closed_and_fails_closed` in `scripts/test_runtime_capabilities.py` (listed in this task's Files) to the enlarged sets in the same commit, and document the new reason in `runtime-contract.md`.
- [x] Run → expect GREEN: the driver discovery command passes with the seven new witnesses, and `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'` stays green after the reason-code registration.
- [x] Commit: `fix: fail closed and stay resumable in scope witnesses`

### Task 4: Driver state and lock corrections (r5 F5, F6, F7, F8; r5 overflow items)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_second_retry_persists_distinct_attempt_record`; given two consecutive error checkpoints for one checkpoint identity under retry budget 2, expects two distinct durable attempt records under derived ordinals, both visible to reconciliation; the fixed `#attempt-initial` key is gone.
- [x] `ExecutePlanRuntimeTest#test_owner_resolved_under_lock`; given two first constructions of drivers on a fresh manifest with a deterministic interleaving injected between them (the competing construction runs between the loser's manifest read and its write, injected the same way as the loader-counting witness), expects one owner identity committed under the manifest lock and the loser adopting it or failing closed at construction; the loser never silently fails every later owner fence; free-running thread or process racing alone is not acceptable evidence.
- [x] `ExecutePlanRuntimeTest#test_resume_runs_adapter_io_outside_manifest_lock`; given a slow injected adapter resume, expects the manifest flock released during adapter I/O (state transitions and manifest writes locked, adapter calls unlocked, mirroring the launch pattern); a probe driver invoked at a controlled point inside the adapter window gets no spurious blocked or stale-claim outcome; and a competing writer injected during the adapter window is detected on re-acquisition: the subsequent nested checkpoint write either proceeds against the freshly re-read manifest (generation unchanged) or fails closed with the resumable `stale-claim` outcome (generation changed); a stale in-memory snapshot is never written back.
- [x] `ExecutePlanRuntimeTest#test_profile_less_invocation_preserves_receipts`; given a CLI construction without a runtime profile after a profiled run wrote durable capability receipts, expects the receipt fields unchanged; no silent downgrade to `unsupported`.
- [x] `ExecutePlanRuntimeTest#test_record_done_has_single_commit_pending_transition`; given the `record_done` path, expects `commit-pending` owned solely by `mark_commit_pending` with no written-then-overwritten dead transition (the update at the old record_done overflow site is collapsed to one), observed by injecting a manifest-save recorder that captures each saved claim-state snapshot and asserting across a full `record_done` cycle that exactly one snapshot marks `commit-pending` and none rewrites that transition afterwards.
- [x] `ExecutePlanRuntimeTest#test_record_done_launches_next_task_after_released_lock`; given a full `record_done` cycle under the non-reentrant lock, expects the next-claim transition to run after the locked region ends (the driver returns the `launch-task` action, never `stale-claim`), covering the nested `claim_next_task` acquisition site.
- [x] `ExecutePlanRuntimeTest#test_blocked_persist_keeps_contract_violation_receipt`; given a checkpoint-path scope violation under the non-reentrant lock, expects the blocked persist to record the `contract-violation` receipt (never the `owner-mismatch` misdiagnosis), covering the nested `_persist_blocked_claim` acquisition site.
- [x] `ExecutePlanRuntimeTest#test_authorize_action_reuses_loaded_manifest`; given several `authorize_action` calls inside one checkpoint cycle, expects no per-call manifest re-read (the already-read manifest or generation passes through), observed by counting manifest loads with an injected loader.
- [x] Run → expect RED: the discovery command; the eight behaviors do not exist yet.
- [x] Implement on top of Task 1's split structure: inventory every same-thread nested `_manifest_lock` acquisition site and restructure each in this commit (the held-set removal makes a nested acquisition fail to `acquired=False`): `record_done`'s next-claim transition moves outside its locked region, and `_persist_blocked_claim` splits into an unlocked inner helper used by locked callers with the locking wrapper retained for unlocked call sites; derive the attempt ordinal from existing checkpoint history, move owner resolution and the receipt refresh inside the locked section, restructure resume and the rewrite-retry path onto a plain non-reentrant manifest lock (the thread-local reentrancy held-set is removed): locked regions end before adapter calls begin, and after the adapter window the lock is re-acquired and the manifest re-read, running Task 2's shared drift helper (`_claim_drift_outcome`) rather than a fresh inline comparison and failing closed with the resumable `stale-claim` outcome if the claim's generation or `baseline_revision` changed during the window (a cached-snapshot write-back is forbidden), so a nested `record_worker_checkpoint` always runs against a freshly read manifest, skip the receipt write when no profile was supplied while the locked owner initialization still persists `manifest["owner"]` (the receipt refresh is the only owner-persistence site today, so the literal skip must not drop owner persistence for profile-less CLI runs and `test_cli_two_processes_share_derived_owner_without_flag` keeps passing), and pass the loaded manifest through the authorization path.
- [x] Run → expect GREEN: the discovery command passes.
- [x] Commit: `fix: retry identity, lock scoping, and receipt preservation in driver`

### Task 5: Registry adapter resolution, inventory deferrals, activation fixture generation (r4 F13, F14; r4 overflow b)

Files:
- `scripts/runtime_capabilities.py`
- `scripts/hooks_probe.py` (`_profile_runtime_ids` dedupe)
- `agents/skills/execute-plan/runtime-contract.md` (capabilities-row update)
- `projects/.ai-playbook/agent-runtime-layout.md` (registry eligibility mirror refresh)
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `scripts/testdata/execute-plan/expected-runtime-ids.json`
- `scripts/testdata/execute-plan/activation/` (committed `loaded/` copies deleted)
- `scripts/test_runtime_capabilities.py`

- [x] `RuntimeCapabilitiesTest#test_resolve_adapter_uses_entrypoint_mapping`; given the eligible codex profile, expects the adapter resolved generically through the in-module entrypoint mapping and `importlib`; given a profile naming a missing entrypoint, expects a fail-closed registry error, never a leaked `ImportError`; given an unbound profile, expects `UnsupportedAdapter`.
- [x] `RuntimeCapabilitiesTest#test_deferred_runtime_resolves_unsupported`; given a runtime listed in the deferrals section, expects `UnsupportedAdapter` with a fail-closed reason naming the deferral; the class is kept, not deleted.
- [x] `RuntimeCapabilitiesTest#test_inventory_deferrals_section`; given the inventory, expects eight deferral rows (the seven newly deferred no-adapter runtimes plus the existing `pi` deferral); the seven newly deferred rows carry reason "no verified adapter", while `pi` keeps its existing reason text unchanged ("Execute-plan resume behavior is not documented or verified for Pi.") — the test asserts the per-row reason mapping, not a single uniform value; eligible profiles keep the adapter entrypoint plus the receipt capabilities consumers read (`parent_continuation`, `final_response`, `resume`); `validate_inventory` accepts the deferrals section and retains its malformed-row rejection (a deferral row missing its reason fails).
- [x] `RuntimeCapabilitiesTest#test_no_name_based_adapter_special_case`; given `resolve_adapter`, expects no vendor-name conditional in the provider-neutral module (the `runtime-adapter:codex` branch is gone).
- [x] `RuntimeCapabilitiesTest#test_independent_runtime_ids_updated_for_deferrals`; given `test_independent_runtime_ids_match_every_catalog_and_probe`, expects its hardcoded eligible-count and deferral-set assertions (today `len == 8` and a fixed deferral set) updated in this commit to the deferrals shape, with no stale literal count or fixed deferral set remaining.
- [x] `RuntimeCapabilitiesTest#test_verify_activation_against_generated_tree`; given the fixture root assembled from the committed source seeds under `scripts/testdata/execute-plan/activation` plus the loaded tree generated into the test's temp directory at setup, expects `capabilities.verify_activation` byte parity green; because the generated tree is never written under `scripts/testdata/`, this composes with the Validation guard that fails on a committed `activation/loaded` directory.
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'` (the mapping, deferrals, and generated-fixture witnesses do not exist yet).
- [x] Implement the entrypoint mapping, the inventory schema change, and the `validate_inventory` updates; make `resolve_adapter` consult the deferrals section when the canonical id is absent from `runtimes` and return `UnsupportedAdapter` carrying the deferral's `reason` before the not-eligible error path; retarget the two canonical-id equality checks to the eligible sets so the deferrals shape passes them: `validate_inventory` compares `set(runtimes)` against `set(canonical_ids) - set(deferred_ids)` (keeping the deferrals-versus-`deferred_ids` equality and malformed-row rejection), and `verify_activation` compares the loaded registry's profile set against the eligible expectation (derived as the canonical set minus the deferred set; no new key is added to `expected-runtime-ids.json`); drive `activate()`'s package-manifest entrypoint verification from the same entrypoint declaration the registry resolves from (no second codex-name conditional left in the module), the eligible profiles' `adapter_entrypoint` values become import-path form (`execute_plan_runtime_codex:CodexAdapter`) and the legacy `runtime-adapter:codex` token is retired from both the inventory and the module (the Validation sweep keys on its absence); rollout note, recorded: a host still running the pre-change package fails closed on the new `adapter_entrypoint` value until `--activate` re-activation, so the Ship-when re-activation step is ordering-critical, not hygiene; refresh the registry mirror in `projects/.ai-playbook/agent-runtime-layout.md` in this same commit (eligible-profile count, the adapters table's entrypoint column, and the eligibility column for the seven newly deferred runtimes); the inventory `adapter_entrypoint` is the single normative declaration and the module's import table (the allowlist of importable module names) is the same table the resolution path consults, with `validate_inventory` asserting every eligible entrypoint's module is in that table so drift fails closed at validation time; the deferrals shape is the single implementation: eligible profiles keep the adapter entrypoint plus `parent_continuation`, `final_response`, and `resume`, while deferral rows carry the runtime id, display name, `eligibility: "deferred"`, the existing `aliases` list (retained because `canonicalize_runtime_id` reads it and the module selftest asserts the `agy` alias), and `reason` (`pi` keeps its existing reason text; only the seven newly deferred rows carry "no verified adapter"), with the lifecycle capabilities moved out of deferral rows (this shape keeps `validate_inventory`'s deferred-eligibility requirement green; `test_all_documented_runtimes_have_profiles` in `scripts/test_runtime_capabilities.py` is rewritten in this same commit to assert only the eligible side (the single `codex` profile with the import-path entrypoint and the three-name `required_capabilities` set) plus a count cross-reference against the inventory's `deferred_ids`, leaving the full deferral-row enumeration (ids, names, aliases, per-row reasons) owned solely by `test_inventory_deferrals_section`); update the capability-name inventory (`CAPABILITY_NAMES`), the `required_capabilities` set, and the unbound-profile catalog test's key reads (`test_unbound_profiles_are_explicitly_unsupported`) to that same shape in this commit; update the profile-field table's `capabilities` row (and any other seven-name capability enumeration) in `agents/skills/execute-plan/runtime-contract.md` to the three-name receipt-capability shape, noting deferral rows carry no lifecycle capabilities, in this same commit; keep `hooks_probe.py` reading `final_response` working unchanged, and make `_profile_runtime_ids` return an order-preserving unique union of `canonical_ids` and `deferred_ids` (the canonical-deferred overlap would otherwise emit duplicate probe rows and break the catalog length pin); the updated `test_independent_runtime_ids_match_every_catalog_and_probe` keeps `len(rows) == len(all_ids)` against the deduped enumeration (nine unique ids: eight canonical plus `pi`); extract the byte-copy staging step from the activate path into a reusable helper (for example `stage_package(source_root, target_root)`) that the activation tests reuse at setup; delete the committed `loaded/` tree (5 tracked files; the two committed seed files `activation.json` and `help_probe.py` under `activation/` stay) in this same commit so Tasks 6 and 7 never see a stale committed copy, with the setup generator keeping untracked `__pycache__` payloads out of the regenerated tree; update `scripts/testdata/execute-plan/expected-runtime-ids.json` in the same commit to the full compared shape, not only the canonical-id list: shrink `profiles` to the single codex row carrying the new import-path entrypoint and the three receipt capabilities (`parent_continuation`, `final_response`, `resume`), keep `aliases` for all nine runtimes (the catalog test iterates them for every runtime including `pi`), and grow `deferred_ids` from the current `pi`-only list to the eight-entry deferral set (the seven newly deferred runtimes plus `pi`), because `verify_activation` compares `canonical_ids`, `deferred_ids`, and every `profiles` row's `adapter_entrypoint`, `capabilities`, and `retry_budget` fields (the catalog test reads the file from the repo root); `canonical_ids` keeps its current eight runtime ids: the seven newly deferred runtimes stay canonical-but-deferred, while `pi` remains deferred-only exactly as today (non-canonical, resolvable through its alias via `canonicalize_runtime_id` and the hooks-probe rows), and the catalog-count assertion is updated to the value the file pins rather than deleted.
- [x] Run → expect GREEN: the registry discovery (including the updated catalog-count and activation witnesses) and `python3 scripts/hooks_probe.py --selftest` pass.
- [x] Commit: `refactor: generic adapter resolution, inventory deferrals, generated activation fixture`

### Task 6: One policy-token validator and receipt hardening (r4 F18, r5 F17)

Files:
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `RuntimeCapabilitiesTest#test_single_policy_token_validator`; given repo-root equality mismatch, generation mismatch, and a foreign absolute repo root, expects one verdict from the single parameterized validator in `runtime_capabilities.py` at both boundaries (launch validity and claim revalidation); the codex-local `_valid_policy_token` and `_validate_policy_token` copies are deleted.
- [x] `RuntimeCapabilitiesTest#test_load_approval_receipt_requires_owner_only_permissions`; given a receipt file with mode 0644, expects rejection; given mode 0600 with a matching runtime, expects the receipt to load; given mode 0600 but a receipt missing `config_path` or `policy_fingerprint`, expects rejection (both fields are required, never optional).
- [x] `RuntimeCapabilitiesTest#test_load_approval_receipt_cross_checks_config_policy`; given a receipt recording a codex config path plus a policy fingerprint, expects `load_approval_receipt` to re-read that config path from the host (an injected config root in tests, never the ambient environment) and to reject when the file is missing, the recorded non-interactive approval policy is absent, or the recomputed policy fingerprint differs from the recorded `policy_fingerprint` (a third witness case covers the mismatch); the receipt schema gains exactly these two fields (`config_path`, `policy_fingerprint`), both mandatory, documented in `runtime-contract.md` as operator-attested evidence, not a cryptographic credential.
- [x] Run → expect RED: the registry discovery command (the fixture suites are still green at this point).
- [x] Implement the unified validator (public `validate_policy_token` in `runtime_capabilities.py`; the adapter imports and calls it under that name only, since either retired literal appearing anywhere in the adapter file, including an import, fails the Validation sweep), delete the codex-local copies, and add the permission and cross-check requirements to `load_approval_receipt`: compute the policy fingerprint from the re-read config and reject on mismatch, missing file, or missing policy, documenting the mismatch rejection reason in `runtime-contract.md` beside the other re-attestation remediations.
- [x] Run → expect RED on both fixture suites (`python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`) with the fixtures not yet updated: their 0644 shape-only receipts are rejected under the mandatory reading (this observation proves the hardened reader rejects the pre-upgrade receipt shape; record in the task log as an intra-commit working-tree state).
- [x] Then update the existing 0644 shape-only approval-receipt fixtures in `scripts/test_execute_plan_runtime.py` (`test_cli_approval_receipt_enables_and_invalid_receipt_blocks`) and `scripts/test_execute_plan_runtime_codex.py` in this same commit: mode 0600 plus the two new required fields, with the config path pointing at an injected config root, so the CLI approval-receipt flows stay green under the mandatory reading. Pre-upgrade operator receipts lacking the new fields fail closed under the mandatory reading by design and must be re-attested after host re-activation; document in `runtime-contract.md` the reason code a rejected receipt produces and its resumability, with the re-attestation remediation beside the other operator remediations; this is a documented migration step, not an unplanned break.
- [x] Run → expect GREEN: the registry discovery command and the `test_execute_plan_runtime*.py` discovery both pass under the mandatory receipt reading.
- [x] Commit: `fix: unify policy-token validation and harden approval receipts`

### Task 7: Sever the adapter import edge, kill order, retry clamp (r6 F5, r5 F16, r6 F6, r5 F11; closes r5 F14)

Files:
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_runtime_capabilities.py`

- [x] Authoring note verified: no test currently patches `bounded_evidence` or `MAX_EVIDENCE_BYTES` via `setattr` or string-form `mock.patch`; re-run the symbol-move patch audit at execution before moving, covering all reference forms: direct imports, module-qualified references (`runtime.bounded_evidence`, `runtime.MAX_EVIDENCE_BYTES`, which exist today at `scripts/test_execute_plan_runtime.py:839-840`), `setattr` patches, and string-form `mock.patch`; retarget every hit to the new owning module in the same commit (no driver re-export alias: the single-home witness requires no `bounded_evidence`/`MAX_EVIDENCE_BYTES` definition or assignment to remain in the driver).
- [x] `RuntimeCapabilitiesTest#test_bounded_evidence_owned_by_capabilities`; given `bounded_evidence` and the `MAX_EVIDENCE_*` constants, expect their single home in `runtime_capabilities.py`; both the driver and the adapter import from there; `scripts/execute_plan_runtime_codex.py` contains no `from execute_plan_runtime import` line (this closes the r5 F14 unused-import finding by removal).
- [x] `CodexAdapterTest#test_identity_check_precedes_sigkill`; given a timeout kill where `_pid_identity_matches` flips to false between poll and kill (injected), expects the identity consulted immediately before `os.kill` so no `SIGKILL` lands on a recycled foreign process; `runtime-contract.md` records that the identity check is a best-effort narrowing and the kernel-level recycle race is closed only by a pidfd-based signal where the platform provides one.
- [x] `CodexAdapterTest#test_recycled_pid_test_uses_disposable_child`; given the recycled-PID timeout test rebuilt around a real disposable child process instead of `os.getpid()`, expects a regressed identity guard to fail an assertion instead of risking the test runner's own process.
- [x] `RuntimeCapabilitiesTest#test_zero_retry_budget_grants_zero_retries`; given `retry_budget = 0`, expects zero retries (clamp `max(0, ...)` plus an explicit `none` retry mode); given budget 2, expects two.
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` and `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'`.
- [x] Implement the move, the kill-order change, and the clamp change in one pass; imports retargeted everywhere in the same commit so every commit compiles.
- [x] Run → expect GREEN: both discovery commands pass.
- [x] Commit: `refactor: capabilities owns evidence helpers; identity-safe kill; zero-budget clamp`

### Task 8: Documented seeding boundary (r4 F15; r6 overflow)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `ExecutePlanRuntimeTest#test_create_operation_seeds_manifest`; given `--operation create` with a task list and owner, expects a 0600 manifest with pending tasks and a fresh generation, shape-identical to the selftest seeding; `create` joins the CLI operation choices.
- [x] `ExecutePlanRuntimeTest#test_directory_valued_allowed_path_rejected_with_actionable_error`; given an `allowed_paths` entry naming a directory, expects the create and validation path to reject it with an actionable error naming the entry; directory prefix matching stays explicitly out of scope (r6 overflow disposition: fail closed beats a silent never-matching entry).
- [x] Docs: `agents/skills/execute-plan/SKILL.md` Phase 0/1 names the `create` operation as the only documented path that translates plan checkboxes into machine manifest state.
- [x] Docs: `runtime-contract.md` documents the resume reconciliation rule (the manifest wins; divergent checkboxes are rewritten through the skill-gate step) and the seeding producer for per-task `allowed_paths` that feeds the empty-scope fail-closed gate.
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` for both new witnesses (the `create` operation and the directory-valued allowed-path rejection).
- [x] Implement the `create` operation (the dispatch handler is a named symbol containing `_operation_create`, which the Validation pin keys on, since the bare string `"create"` cannot discriminate) and land both doc edits.
- [x] Run → expect GREEN: the discovery command passes; `expect_match '_operation_create' scripts/execute_plan_runtime.py` holds.
- [x] Commit: `feat: create operation as the documented manifest seeding boundary`

### Task 9: done-lock cleanups (r4 overflow a; r5 overflow items 1-3)

Files:
- `scripts/done-lock.sh`

- [x] `DONE_LOCK_GENERATION` is removed as a tautological alias of the token: the fence writes and reads the lock identity under the single `DONE_LOCK_TOKEN` name in the session file, release consumes the token directly instead of hard-failing on a missing alias export, and the selftest covers release under the new shape. Migration note: session files written by the current shape already carry `DONE_LOCK_TOKEN` (the generation name is written beside it as a tautological alias of the same value), so the token-only release path reads old-shape locks unchanged; any residue the new path cannot consume stays covered by the existing `stale-clean` operator path (age-bounded by `DONE_LOCK_STALE_SECS`), so no mid-session upgrade step is required. Rollback hazard, recorded: the pre-change fence requires the generation alias, so reverting `done-lock.sh` while a token-only lock is live blocks release until `stale-clean` is run manually after confirming the holder is dead; the selftest pins the token-only session shape by covering its consumption by the release path.
- [x] Dead `read_label` is deleted; the used argument loops give a clear error on a missing `--label` value and reject an empty label; the selftest gains one case per stance (missing value, empty label) asserting the specific error.
- [x] `try_acquire`'s two near-identical acquisition bodies collapse into one helper used by both call sites; the selftest drives one contended and one uncontended acquisition per call site through the shared helper; `bash scripts/done-lock.sh selftest` stays green.
- [x] `load_lock_session` (repo-controlled file sourcing, arbitrary code execution if ever wired) is deleted; the no-sourcing invariant is asserted by the selftest and by the Validation Commands sweep. New selftest case names, assertions, and comments in `done-lock.sh` must not contain the retired literals `load_lock_session`, `read_label`, or `DONE_LOCK_GENERATION` (the Validation sweeps match literal substrings in this same file); assert the no-sourcing invariant by checking that no `source` or `.` command reads session files, and keep the rollback-hazard note in the task log rather than the script.
- [x] Run → expect GREEN after each bullet: `bash scripts/done-lock.sh selftest`.
- [x] Commit: `refactor: done-lock alias, label parsing, acquisition helper, no-sourcing`

### Task 10: Contract prose single home (r5 F15; r4 overflow c, d, e)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/plan-readiness/README.md`
- `README.md`

- [x] `agents/skills/execute-plan/SKILL.md` shrinks its "Runtime-neutral execution contract" section to a short summary plus the read-first pointer sentence "Read agents/skills/execute-plan/runtime-contract.md for the normative runtime contract, result schema, policy boundary, manifest ownership, and continuation transitions."; every contract edit after this task lands in the contract file only.
- [x] `runtime-contract.md` keeps the single full statement of the hook capability boundary ("A host hook cannot enforce a policy when its event cannot block the operation or cannot carry the payload needed to evaluate the policy."); `agents/hooks/skill-gate/README.md` "Capability boundary and registry parity" section becomes a pointer that must not reuse that sentence; the lessons-recall and plan-readiness READMEs are swept for restatements and converted to pointers the same way.
- [x] Verify-and-close (r4 overflow d): confirm the contract's lock section describes the done-lock session fence as its own file matched by generation and token and carries no env-field list; record the check in this task's log; no edit if already accurate.
- [x] `README.md` moves the `runtime-contract.md` row out of the Scripts table to beside the execute-plan skill catalog entry; sweep the catalog for stale references after the move.
- [x] Run → expect GREEN: the Validation single-home grep (exactly one file carries the full statement) and the SKILL.md pointer pin.
- [x] Commit: `docs: single home for runtime contract and capability boundary prose`

### Task 11: Hermeticity witnesses that discriminate (hermeticity origin F2, F4; r5 F10; r6 F11)

Files:
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py` (also on the drive-or-drop branch: deletion of the decorative socket patch and the dead `outside.txt` assertion in `test_runtime_replay_is_hermetic_to_fixture_root`)

- [x] `CodexAdapterTest#test_subprocess_env_sanitized`; given a poisoned parent environment launched through the real `_subprocess_runner`, expects the child to see only `SAFE_ENV_KEYS` plus the runner's injected policy variables (`EXECUTE_PLAN_POLICY_TOKEN` and `EXECUTE_PLAN_ALLOWED_PATHS`); the asserted expectation is a literal key set written in the test (never derived from `SAFE_ENV_KEYS` itself, so the mutation probe can discriminate); mutation probe: widen `SAFE_ENV_KEYS` by one key, expect this test to fail, revert (probe set recorded in the task log per the empirical-derivation rule).
- [x] `CodexAdapterTest#test_no_live_installation_read`; given `HOME` and `EXECUTE_PLAN_PACKAGE_MANIFEST` pointed at a fixture root with reads observed via module-scoped patches of the open call sites in `scripts/execute_plan_runtime_codex.py` and `scripts/runtime_capabilities.py` (not process-wide audit hooks; the patch targets are `pathlib.Path.open`, `pathlib.Path.read_text`, `pathlib.Path.read_bytes`, and `io.open`, since the modules' read sites go through `pathlib`; the patched openers record `(path, caller_module)` and the denial assertion fires only on opens whose nearest frame module is `execute_plan_runtime_codex` or `runtime_capabilities`, while the zero-observation guard (at least one intercepted open inside the fixture root) stays unfiltered; `TMPDIR` is pinned into the fixture root in the same setup so system-temp reads cannot false-positive, and all modules are pre-imported before arming so importlib opens cannot fire), expects the adapter lifecycle to open nothing outside the fixture root; child-process reads are out of this witness's scope and covered by the env-allowlist witness. Mutation probe: patch the opener to additionally open one path under the real `HOME`, expect this test to fail, revert (recorded in the task log).
- [x] `CodexAdapterTest#test_package_manifest_ambient_read`; given `EXECUTE_PLAN_PACKAGE_MANIFEST` absent, expects construction to take the documented default-deadline fallback (the current contract; the hermeticity origin's missing-var fail-closed upgrade is declined here as a behavior change that would break non-activated runs and roughly ten existing test constructions, and the decline is recorded in the Task 12 disposition); given a valid manifest path, expects the manifest loaded and used. Mutation probes, one per branch: on the absent-var branch, change the documented default deadline constant in the adapter and expect the fallback assertion to fail; on the valid-manifest branch, set the fixture manifest deadline to a value distinct from the default, assert the constructed deadline equals the manifest value, and probe by making the loader ignore the manifest (expect that assertion to fail); revert both (recorded in the task log).
- [x] `ExecutePlanRuntimeTest#test_hermeticity_round_trip_asserts_locale_and_clock_env`; given the fixture environment with `TZ=UTC`, `LANG=C`, `LC_ALL=C`, expects the subprocess round-trip in `test_runtime_replay_is_hermetic_to_fixture_root` to assert all three took effect in the child, not only `cwd` and `HOME`.
- [x] `ExecutePlanRuntimeTest#test_patched_socket_window_drives_continue_parent`; given `continue_parent` driven across the patched-socket window, expects the network guard to intersect the code under test: first attempt to drive a real guarded call inside the patched window and require the guard to fire; only if driving is impossible, delete the decorative guard and the dead `outside.txt` assertions in the same task, recording the impossibility evidence in the task log (an undriven guard is never kept).
- [x] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` (these witnesses pin correct current behavior; each carries a recorded mutation probe or a drive-or-drop resolution instead of a RED step).
- [x] Commit: `test: discriminating hermeticity witnesses for env, manifest, and network guards`

### Task 12: Verify-and-close, errata disposition, origins close-out

Files:
- `docs/history/backlog/` (the five origin items, completion move)
- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (checkboxes)

- [x] Verify-and-close (r5 F9): confirm every witness invocation carries `-c core.quotePath=false` (5 invocation sites after Task 3: the diff, status, merge-base, and committed-diff witnesses plus the reworked startup dirty check; the Validation command counts invocation-form matches only, so the docstring mention does not count); no re-fix; the closure is recorded here.
- [x] Errata disposition (prose-accuracy origin): re-probe `test_evidence_and_fixtures_are_hermetic` (asserts evidence redaction, secret absence, and manifest mode 0600 only) and `test_runtime_replay_is_hermetic_to_fixture_root` (holds the environmental hermeticity assertions); record in the task log that the four prose findings are dispositioned record-only and the completed plan body at `docs/plans/completed/2026-09-09-agent-agnostic-execute-plan.md` stays untouched per the completed-history refusal rule.
- [x] Move all five backlog origins to `docs/history/backlog/completed/` marking `Status: done`, adding a one-line disposition note in the same edit where the disposition differs from a plain fix: the prose-accuracy item (record-only under the refusal rule), the r5 origin (F9 verify-closed, F14 closed by the Task 7 move), the r6 origin (F1 deferred by the threat-model decision to `docs/history/backlog/2026-09-11-deferred-malicious-worker-hardening.md`; overflow items closed by the Task 8 directory-path rejection), and the hermeticity origin (the missing-var fail-closed upgrade declined as a behavior change breaking non-activated runs; the ambient-read witness covers both branches of the current contract instead).
- [x] Complete this plan per the plans lifecycle: archive move to `docs/plans/completed/`, and append the ownership-registry row in the same pass when the doc-hierarchy registry convention is present.
- [x] Commit: `chore: close execute-plan runtime residuals origins and archive plan`
- [x] Run → expect GREEN: the full Validation Commands block on the final tree, including the cleanup-baseline checker with this plan's ledger allow-list.

## Documentation Impact Assessment

- `agents/skills/execute-plan/runtime-contract.md`: launch-record drift rule, seeding operation and reconciliation rule, receipt semantics (Tasks 2, 6, 8).
- `agents/skills/execute-plan/SKILL.md`: seeding path naming and contract summary shrink (Tasks 8, 10).
- `agents/hooks/*/README.md` and `README.md`: capability-boundary pointers and catalog row move (Task 10).
- No new documentation files; no README config section changes.
