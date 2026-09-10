# Plan: Execute-plan runtime residuals

Close the residual findings from the agent-agnostic execute-plan runtime work in one pass: out-of-tree policy anchoring, driver state and locking corrections, registry and validator de-duplication, hermeticity witnesses, done-lock cleanups, and contract prose consolidation.

Backlog origins (scope of record; moved to `docs/history/backlog/completed/` at completion):

- `docs/history/backlog/2026-09-09-agent-agnostic-plan-prose-accuracy-residuals.md`
- `docs/history/backlog/2026-09-09-execute-plan-runtime-r4-deferred-findings.md`
- `docs/history/backlog/2026-09-09-execute-plan-runtime-r5-deferred-findings.md`
- `docs/history/backlog/2026-09-10-execute-plan-runtime-r6-findings.md`
- `docs/history/backlog/2026-09-09-runtime-hermeticity-witness-gaps.md`

Plan review: `docs/reviews/2026-09-10-plan-review-execute-plan-runtime-residuals-r*.md` (latest staged round; findings folded before the next review).

Guidance: `projects/.ai-playbook/agent_workflow_guidelines.md` (plan quality sections).

## Terms

- **Continuation driver**: the deterministic state machine in `scripts/execute_plan_runtime.py` that owns the runtime manifest and selects the next workflow step.
- **Runtime manifest**: the driver-owned durable state file recording tasks, claims, checkpoints, and policy scope; its path and ownership are owned by the runtime contract.
- **Policy fields**: the manifest fields that define what a worker may do: `allowed_paths`, `baseline_revision`, `owner`, and `generation`.
- **Scope witness**: the driver checks that compare worktree and committed paths against the claim policy: `_worktree_scope_violation`, `_git_changed_paths`, `_git_diff_paths`, and the done-boundary verification inside `record_done`.
- **Policy anchor**: the out-of-tree 0600 file under `~/.execute-plan/<repo-hash>/` that records the digest of the manifest's policy fields at claim launch; witnesses recompute the digest against it.
- **Policy token**: the capability receipt structure that authorizes adapter launch, wait, and resume operations.
- **Hermeticity witness**: a test that asserts the runtime does not read or leak host state (environment sanitization, live-installation read denial, fixture-root confinement).

## Assumptions

- assume the scope is exactly the union of the five backlog origins; no other runtime work enters this plan; basis: the authoring task names the five items as the scope of record and each item enumerates its findings.
- assume origin finding line numbers have shifted since capture; tasks pin symbol and test names instead; basis: authoring probes on the current tree (for example the adapter special case sits at `scripts/runtime_capabilities.py:277` today, the fixed retry key `#attempt-initial` at `scripts/execute_plan_runtime.py:599`, the `core.quotePath=false` witnesses at lines 1007, 1018, 1054, and 1068).
- assume completed-history artifacts stay body-immutable; the prose-accuracy origin closes as a recorded disposition with no edit to `docs/plans/completed/2026-09-09-agent-agnostic-execute-plan.md`; basis: doc-hierarchy "Document states" and the doc-hierarchy-upkeep refusal rule (ADR-0003); the errata record already lives in the origin item.
- assume the runtime is exercised on a host with `python3` and `git` on `PATH`; basis: every existing script and selftest in this area requires both.
- assume tests follow the repo's unittest discovery and bash selftest conventions; basis: the completed runtime plan's Validation Commands and the existing `scripts/test_*.py` layout.

Decision points requiring a grill: policy anchor design = out-of-tree digest anchor over the manifest's policy fields, the manifest keeps its contract-owned home; source: the r6 origin lists relocating policy state and verifying an out-of-tree digest as the two structural options, the digest variant is selected at authoring under the standing accept-recommended-options pre-authorization because it adds one anchor file plus two witness checks instead of relocating manifest ownership; date: 2026-09-10; affected sections: Task 2, Gist & Examples. Inventory shape = deferrals section with reason "no verified adapter"; source: r4 origin first-listed option; date: 2026-09-10; affected sections: Task 5. Untracked-noise outcome = resumable `cleanup-required` blocked result; source: r6 origin first-listed option; date: 2026-09-10; affected sections: Task 3. Prose-accuracy errata = recorded disposition without body edits to the completed plan; source: doc-hierarchy Document states plus the upkeep refusal rule (ADR-0003); date: 2026-09-10; affected sections: Task 12.

## Design Invariants (CR Guard)

- Fail-closed direction: every check this plan adds or changes fails closed on absence, mismatch, ambiguity, or error (anchor missing or stale, baseline missing on a launched claim, `OSError` in the escape check, committed symlink, zero retry budget); no new fail-open path is introduced.
- Manifest preservation on block: blocked outcomes preserve the manifest and never relaunch an ambiguous worker; the driver still never performs the commit itself.
- Seed-only conveniences: baseline sentinels and seed anchors exist only in test seeds; a production launched claim always carries both a baseline revision and a policy anchor.
- Adapter thinness: the Codex adapter keeps translating host protocol only; shared skill bodies stay runtime-neutral; after Task 7 the adapter imports nothing from the driver module.
- Authorization boundary unchanged: no operation gains automatic approval; the done handoff, gated-action policy, and approval-receipt semantics stay as landed, and the receipt stays operator-attested.

## Gist & Examples

Five review rounds of the agent-agnostic execute-plan runtime deferred residuals instead of regenerating findings in capped rounds. This plan closes them in one pass, grouped into four families: policy and boundary hardening (r6 F1-F4, F8-F10, F12, F13), driver state and locking (r5 F5-F8, F16, F17, overflow items), registry and contract structure (r4 F13-F15, F18, overflow items), and witness plus documentation accuracy (the hermeticity origin, r5 F9-F11, F14-F15, and the prose-accuracy origin).

Before (today): a same-user worker process can quietly edit the gitignored runtime manifest to widen `allowed_paths` or erase `baseline_revision`; both scope witnesses read only tracked worktree state (`git status --porcelain` variants without `--ignored`), so the tampering is invisible and out-of-scope files can be committed under the widened policy. On the same code path, a second consecutive worker error overwrites the first attempt's durable checkpoint record (the fixed `#attempt-initial` key), owner identity is read from an unlocked manifest snapshot, adapter resume runs while the manifest flock is held, and a profile-less CLI construction silently downgrades durable capability receipts to `unsupported`.

After (this plan): at claim launch the driver writes a policy anchor, a 0600 file under `~/.execute-plan/<repo-hash>/<plan-slug>/` holding the sha256 digest of the manifest's policy fields plus the claim identity. The worktree scope witness and the done boundary recompute that digest and fail closed on a mismatch, and on a missing anchor for a launched claim, while legitimate checkpoints and checkbox updates leave the policy-field digest untouched. The fence raises the bar from silent tampering to active anchor forgery and detects same-user drift; it does not stop a determined same-user adversary, who can rewrite the out-of-tree anchor too (the r6 accepted limitation, retained as a bounded blast-radius statement). Retry records carry a derived attempt ordinal so two consecutive errors stay two records; owner resolution and capability receipts happen under the manifest lock; adapter I/O runs outside the flock.

More before and after pairs, one per family. Registry: `resolve_adapter()` today special-cases `runtime-adapter:codex` by name inside the provider-neutral registry module, and the inventory declares seven lifecycle capabilities for eight profiles that consumers never read; after this plan the registry resolves adapters generically from an in-module entrypoint mapping, and the seven no-adapter runtimes live in a deferrals section with reason "no verified adapter". Validators: the two divergent codex-local policy-token validators become one parameterized validator in `runtime_capabilities.py`, called at both the launch-validity and claim-revalidation boundaries, and `load_approval_receipt` starts requiring owner-only permissions and a config-policy cross-check instead of validating JSON shape alone. Witnesses and docs: the hermeticity suite gains discriminating tests for environment sanitization, live-installation read denial, and the ambient package-manifest read, and the capability-boundary paragraph keeps one full statement in `runtime-contract.md` with pointer sentences in the hook READMEs instead of a pasted copy in `agents/hooks/skill-gate/README.md`.

Edge cases covered: a `retry_budget` of 0 grants zero retries instead of one; ambient untracked noise (`.DS_Store`, editor swaps) still blocks but returns a resumable `cleanup-required` outcome instead of a non-resumable dead end; a committed symlink at an allowed in-scope path pointing outside the repo is rejected at the done boundary; a recycled PID inside the timeout poll window is never signaled before its identity is consulted.

## Evaluation Criteria

**Quality dimensions:**

- Security: the policy anchor closes the gitignored-policy tampering blindness for same-user drift detection at both boundaries; the r6 accepted limitation stands (a same-user adversary can also rewrite the out-of-tree anchor, so the fence detects drift, not malice, with blast radius bounded to this workstation); approval receipts require owner-only permissions and a config-policy cross-check; the timeout kill path consults identity before `SIGKILL`.
- Correctness: two consecutive retry errors produce two durable records; owner identity and capability receipts are consistent under concurrent construction; adapter I/O never holds the manifest flock; every fail-closed small (baseline absence, `OSError`, porcelain escaping, zero budget) behaves as specified.
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
expect_no_match '#attempt-initial' scripts/execute_plan_runtime.py
expect_no_match 'load_lock_session' scripts/done-lock.sh
expect_no_match 'read_label' scripts/done-lock.sh
expect_no_match 'DONE_LOCK_GENERATION' scripts/done-lock.sh
expect_no_match 'from execute_plan_runtime import' scripts/execute_plan_runtime_codex.py
expect_no_match '_valid_policy_token' scripts/execute_plan_runtime_codex.py
if [ -e scripts/testdata/execute-plan/activation/loaded ]; then echo "committed activation loaded tree still present" >&2; exit 1; fi
expect_match 'SAFE_ENV_KEYS' scripts/test_execute_plan_runtime_codex.py
expect_match '"create"' scripts/execute_plan_runtime.py
expect_match 'no verified adapter' projects/.ai-playbook/execute-plan-runtime-inventory.toml
expect_match 'for the normative runtime contract, result schema, policy boundary, manifest ownership, and continuation transitions' agents/skills/execute-plan/SKILL.md
count="$(grep -rls 'cannot enforce a policy when its event' agents/ | wc -l | tr -d ' ')"
[ "$count" = "1" ] || { echo "capability boundary full statement must live in exactly one file, found $count" >&2; exit 1; }
expect_match 'cannot enforce a policy when its event' agents/skills/execute-plan/runtime-contract.md
run_check python3 -c 'import pathlib,re; t=pathlib.Path("scripts/execute_plan_runtime.py").read_text(); n=len(re.findall(r"\"-c\",\s+\"core[.]quotePath=false\"", t)); assert n >= 4, n'
run_check bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

Notes: the `expect_no_match` sweeps over `runtime-adapter:codex`, `#attempt-initial`, `load_lock_session`, `read_label`, `DONE_LOCK_GENERATION`, the adapter import edge, `_valid_policy_token`, and the committed `loaded/` tree are intentionally RED at authoring (each fires on today's tree; verified during authoring) and flip GREEN exactly when the corresponding task lands. The `expect_match` pins flip GREEN with their owning tasks: `create` with Task 8, the inventory deferrals reason with Task 5, the SKILL.md pointer sentence with Task 10, and `SAFE_ENV_KEYS` with Task 11; the capability-boundary single-home count is 2 today (the `lessons-recall` README carries a copy) and must reach exactly 1 after Task 10's pointer conversion. The single-home grep keys on the exact contract sentence; the skill-gate README pointer must not reuse that sentence. The em-dash rule is enforced at authoring over this plan file only; edited files are not swept for pre-existing content this plan does not touch.

### Task 1: Split the checkpoint recorder and done boundary (r6 F12, F13)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] Run → expect GREEN (characterization, captures behavior before refactor): `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`; in particular `test_done_commit_boundary`, `test_commit_before_checkpoint_reconciles`, `test_success_checkpoint_selects_next_incomplete_step`, `test_worker_permission_request_does_not_pause_authorized_work`, and `test_atomic_claim_prevents_duplicate_launch` pass unchanged.
- [ ] Extract `_done_boundary_block`: the shared done-boundary verification (launch baseline lookup, committed-path scope and escape checks) extracted from `record_done`; Task 1 itself changes no outcomes, and Task 3's RED witness wires `reconcile_commit_before_checkpoint` to call the same helper.
- [ ] Extract `_complete_and_claim`: the shared success-path completion and next-claim transition used by the checkpoint success path and the done handoff.
- [ ] Split `record_worker_checkpoint` so retry and blocked handling (budget accounting, retry launches) is separate from the success-path commit that calls `_complete_and_claim`; no behavior change.
- [ ] Run → expect GREEN: the same discovery command; all characterization witnesses still pass with the helpers in place.
- [ ] Commit: `refactor: split checkpoint recorder and done boundary helpers`

### Task 2: Out-of-tree policy digest anchor (r6 F1)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] `ExecutePlanRuntimeTest#test_policy_anchor_written_at_claim`; given a claim launch with `HOME` pointed at a fixture root, expects a 0600 anchor file at `<home>/.execute-plan/<repo-hash>/<plan-slug>/policy-anchor.json` recording the sha256 digest of the manifest's policy fields (`allowed_paths`, `baseline_revision`, `owner`, `generation`) plus the claim identity and generation; `<repo-hash>` is a short sha256 of the resolved repo root; the file is written once at a claim generation's first launch and never rewritten while that generation stays live.
- [ ] `ExecutePlanRuntimeTest#test_anchor_is_write_once_across_relaunch`; given a relaunch of the same claim generation whose manifest policy fields changed since the anchor was written, expects fail-closed policy-anchor-mismatch and no silent re-anchor; given a legitimately new claim generation of the same run, expects the run's anchor atomically replaced for that generation.
- [ ] `ExecutePlanRuntimeTest#test_anchor_scoped_per_run_no_cross_talk`; given two concurrent run identities (different plan slugs) in the same repo with different policy fields, expects each run's witnesses to verify against its own anchor file and neither run's new-generation replacement to invalidate the other run's anchor; at claim launch the driver prunes sibling anchor entries under the same repo-hash whose mtime is older than 30 days (bounded retention without cross-run interference).
- [ ] `ExecutePlanRuntimeTest#test_launch_record_is_the_seed_discriminator`; given a seeded claim that never passed the production launch path (no launch record), expects the seed-only exemptions to apply (no anchor requirement, seed baseline accepted); given a claim carrying the launch record, expects both the anchor digest and the baseline revision enforced.
- [ ] `ExecutePlanRuntimeTest#test_scope_witness_blocks_on_policy_digest_mismatch`; given a launched claim whose manifest `allowed_paths` are widened after the anchor was written, expects both the worktree scope witness and the done-boundary verification to fail closed with a policy-anchor-mismatch reason, manifest preserved, no commit handoff.
- [ ] `ExecutePlanRuntimeTest#test_scope_witness_blocks_on_missing_anchor_for_launched_claim`; given a launched claim with the anchor file absent, expects fail-closed blocked; given a seeded claim that never launched, expects no anchor requirement (seed-only exemption per the Design Invariants).
- [ ] `ExecutePlanRuntimeTest#test_anchor_survives_legitimate_checkpoints`; given checkpoints and checkbox updates recorded after the anchor, expects the policy-field digest unchanged and both witnesses green; this discriminates the policy-subset digest from a whole-manifest digest.
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`; the anchor does not exist yet.
- [ ] Implement the anchor write on the claim launch path, the digest recomputation in both witnesses, and the seed-only exemption keyed on a launch record: the production launch path atomically records `baseline_revision`, the anchor digest reference, and a launch timestamp on the claim, and every exemption or fail-closed decision keys on that record's presence, never on the `state` field alone (seeded test claims already say `launched`); the anchor digest is computed over the live claim's policy fields (that claim's `allowed_paths` and `baseline_revision`, which live claim-scoped under `manifest["claims"]`, plus the run-level `owner` and `generation`), and the driver's single-live-claim state machine keeps the per-run anchor always describing the claim the witnesses evaluate; anchors are written 0600 into a 0700 directory; anchor read or digest failures fail closed; the anchor is keyed per run (repo-hash plus plan-slug, so parallel sessions never share an anchor), atomically replaced only when the same run's new claim generation first launches, write-once within a generation, and pruned at launch for same-repo sibling entries older than 30 days.
- [ ] Document the policy anchor in `runtime-contract.md` beside the manifest ownership section: when it is written, what it covers, that witnesses fail closed on mismatch or absence for launched claims, that the anchor is keyed per run so concurrent sessions do not interfere, and that retention is bounded (per-run entries, pruned after 30 days at launch).
- [ ] Run → expect GREEN: the discovery command passes including the four new witnesses.
- [ ] Commit: `fix: anchor manifest policy fields out of tree for scope witnesses`

### Task 3: Witness fail-closed and usability smalls (r6 F4, F9, F8, F2, F10, F3)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/runtime_capabilities.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [ ] `ExecutePlanRuntimeTest#test_missing_baseline_fails_closed_for_launched_claim`; given a launched claim (it carries the Task 2 launch record) whose `baseline_revision` was erased from the manifest, expects both witnesses to fail closed (blocked), not silently disable; test seeds without a launch record pin a sentinel baseline revision so seeded claims keep working.
- [ ] `ExecutePlanRuntimeTest#test_path_escape_check_fails_closed_on_oserror`; given `_path_escapes_repo` raising `OSError` for a candidate path (injected failure), expects the path treated as escaping (fail closed) or the outcome escalated to `unavailable`, never a pass.
- [ ] `ExecutePlanRuntimeTest#test_porcelain_witness_parses_escaped_paths`; given a worktree file whose name contains a double quote, which git C-quotes even with `core.quotePath=false`, created outside the allowed paths, expects the witness using `git status --porcelain -z` (or an equivalent C-unquote) to report the real path as out of scope, not the quoted form; a non-ASCII name alone does not discriminate because all four invocation sites already pass `core.quotePath=false` (authoring-verified).
- [ ] `ExecutePlanRuntimeTest#test_done_boundary_rejects_committed_symlink_escape`; given a commit containing a symlink (blob mode 120000, checked via `git ls-tree`) at an allowed in-scope path pointing outside the repo, expects the done-boundary verification in `_done_boundary_block` to block the handoff.
- [ ] `ExecutePlanRuntimeTest#test_reconcile_runs_done_boundary_verification`; given `reconcile_commit_before_checkpoint` on a commit containing an out-of-scope path, expects the same blocked boundary outcome as `record_done` produces for the same commit.
- [ ] `ExecutePlanRuntimeTest#test_ambient_untracked_noise_is_resumable_cleanup_required`; given only ambient untracked files (for example `.DS_Store`) whose mtime predates the claim's launch record, expects a blocked outcome marked resumable `cleanup-required` with cleanup guidance.
- [ ] `ExecutePlanRuntimeTest#test_post_launch_untracked_escape_stays_hard_blocked`; given an untracked out-of-policy path whose mtime is at or after the claim's launch record, expects the existing non-resumable blocked stance (the pinned untracked-escape witness keeps its hard outcome; the mtime comparison against the launch record is the ambient-versus-worker-caused discriminator).
- [ ] `ExecutePlanRuntimeTest#test_startup_ambient_noise_is_resumable_cleanup_required`; given untracked noise whose mtime predates the run's creation hitting the startup dirty-worktree path (`reconcile_startup` and `continue_parent` before launch), expects a resumable `cleanup-required` outcome instead of the non-resumable `dirty-worktree` block; tracked modifications keep the hard block on the same path.
- [ ] Run → expect RED: the discovery command; none of the eight behaviors exist yet.
- [ ] Implement the eight fixes in the witness and boundary paths, keeping every new branch fail closed per the Design Invariants; register the new `cleanup-required` reason in the closed `REASON_CODES` and `RESUMABLE_REASONS` sets in `runtime_capabilities.py` (resumable: yes) and add it to the result/reason documentation in `runtime-contract.md`.
- [ ] Run → expect GREEN: the driver discovery command passes with the seven new witnesses, and `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'` stays green after the reason-code registration.
- [ ] Commit: `fix: fail closed and stay resumable in scope witnesses`

### Task 4: Driver state and lock corrections (r5 F5, F6, F7, F8; r5 overflow items)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] `ExecutePlanRuntimeTest#test_second_retry_persists_distinct_attempt_record`; given two consecutive error checkpoints for one checkpoint identity under retry budget 2, expects two distinct durable attempt records under derived ordinals, both visible to reconciliation; the fixed `#attempt-initial` key is gone.
- [ ] `ExecutePlanRuntimeTest#test_owner_resolved_under_lock`; given two concurrent first constructions of drivers on a fresh manifest, expects one owner identity committed under the manifest lock and the loser adopting it or failing closed at construction; the loser never silently fails every later owner fence.
- [ ] `ExecutePlanRuntimeTest#test_resume_runs_adapter_io_outside_manifest_lock`; given a slow injected adapter resume, expects the manifest flock released during adapter I/O (state transitions and manifest writes locked, adapter calls unlocked, mirroring the launch pattern); a concurrent driver gets no spurious blocked or stale-claim outcome during the adapter window.
- [ ] `ExecutePlanRuntimeTest#test_profile_less_invocation_preserves_receipts`; given a CLI construction without a runtime profile after a profiled run wrote durable capability receipts, expects the receipt fields unchanged; no silent downgrade to `unsupported`.
- [ ] `ExecutePlanRuntimeTest#test_record_done_has_single_commit_pending_transition`; given the `record_done` path, expects `commit-pending` owned solely by `mark_commit_pending` with no written-then-overwritten dead transition (the update at the old record_done overflow site is collapsed to one).
- [ ] `ExecutePlanRuntimeTest#test_authorize_action_reuses_loaded_manifest`; given several `authorize_action` calls inside one checkpoint cycle, expects no per-call manifest re-read (the already-read manifest or generation passes through), observed by counting manifest loads with an injected loader.
- [ ] Run → expect RED: the discovery command; the six behaviors do not exist yet.
- [ ] Implement on top of Task 1's split structure: derive the attempt ordinal from existing checkpoint history, move owner resolution and the receipt refresh inside the locked section, restructure resume and the rewrite-retry path to release the flock across adapter I/O, skip the receipt write when no profile was supplied, and pass the loaded manifest through the authorization path.
- [ ] Run → expect GREEN: the discovery command passes.
- [ ] Commit: `fix: retry identity, lock scoping, and receipt preservation in driver`

### Task 5: Registry adapter resolution, inventory deferrals, activation fixture generation (r4 F13, F14; r4 overflow b)

Files:
- `scripts/runtime_capabilities.py`
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `scripts/testdata/execute-plan/expected-runtime-ids.json`
- `scripts/testdata/execute-plan/activation/` (committed `loaded/` copies deleted)
- `scripts/test_runtime_capabilities.py`

- [ ] `RuntimeCapabilitiesTest#test_resolve_adapter_uses_entrypoint_mapping`; given the eligible codex profile, expects the adapter resolved generically through the in-module entrypoint mapping and `importlib`; given a profile naming a missing entrypoint, expects a fail-closed registry error, never a leaked `ImportError`; given an unbound profile, expects `UnsupportedAdapter`.
- [ ] `RuntimeCapabilitiesTest#test_deferred_runtime_resolves_unsupported`; given a runtime listed in the deferrals section, expects `UnsupportedAdapter` with a fail-closed reason naming the deferral; the class is kept, not deleted.
- [ ] `RuntimeCapabilitiesTest#test_inventory_deferrals_section`; given the inventory, expects the seven no-adapter runtimes in a deferrals section each carrying reason "no verified adapter"; eligible profiles keep the adapter entrypoint plus the receipt capabilities consumers read (`parent_continuation`, `final_response`, `resume`); `validate_inventory` accepts the deferrals section and retains its malformed-row rejection (a deferral row missing its reason fails).
- [ ] `RuntimeCapabilitiesTest#test_no_name_based_adapter_special_case`; given `resolve_adapter`, expects no vendor-name conditional in the provider-neutral module (the `runtime-adapter:codex` branch is gone).
- [ ] `RuntimeCapabilitiesTest#test_independent_runtime_ids_updated_for_deferrals`; given `test_independent_runtime_ids_match_every_catalog_and_probe`, expects its hardcoded eligible-count and deferral-set assertions (today `len == 8` and a fixed deferral set) updated in this commit to the deferrals shape, with no stale literal count or fixed deferral set remaining.
- [ ] `RuntimeCapabilitiesTest#test_verify_activation_against_generated_tree`; given the fixture root assembled from the committed source seeds under `scripts/testdata/execute-plan/activation` plus the loaded tree generated into the test's temp directory at setup, expects `capabilities.verify_activation` byte parity green; because the generated tree is never written under `scripts/testdata/`, this composes with the Validation guard that fails on a committed `activation/loaded` directory.
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'` (the mapping, deferrals, and generated-fixture witnesses do not exist yet).
- [ ] Implement the entrypoint mapping, the inventory schema change, and the `validate_inventory` updates; the eligible profiles' `adapter_entrypoint` values become import-path form (`execute_plan_runtime_codex:CodexAdapter`) and the legacy `runtime-adapter:codex` token is retired from both the inventory and the module (the Validation sweep keys on its absence); the deferrals shape is the single implementation: eligible profiles keep the adapter entrypoint plus `parent_continuation`, `final_response`, and `resume`, while deferral rows carry the runtime id, display name, `eligibility: "deferred"`, the existing `aliases` list (retained because `canonicalize_runtime_id` reads it and the module selftest asserts the `agy` alias), and `reason`, with the lifecycle capabilities moved out of deferral rows (this shape keeps `validate_inventory`'s deferred-eligibility requirement and the pi reason assertion in `test_all_documented_runtimes_have_profiles` green); update the capability-name inventory (`CAPABILITY_NAMES`), the `required_capabilities` set, and the unbound-profile catalog test's key reads (`test_unbound_profiles_are_explicitly_unsupported`) to that same shape in this commit; keep `hooks_probe.py` reading `final_response` working unchanged; extract the byte-copy staging step from the activate path into a reusable helper (for example `stage_package(source_root, target_root)`) that the activation tests reuse at setup; delete the committed `loaded/` tree (5 tracked files; the two committed seed files `activation.json` and `help_probe.py` under `activation/` stay) in this same commit so Tasks 6 and 7 never see a stale committed copy, with the setup generator keeping untracked `__pycache__` payloads out of the regenerated tree; update `scripts/testdata/execute-plan/expected-runtime-ids.json` in the same commit so the canonical-id expectation matches the shrunken eligible set (the catalog test reads it from the repo root).
- [ ] Run → expect GREEN: the registry discovery (including the updated catalog-count and activation witnesses) and `python3 scripts/hooks_probe.py --selftest` pass.
- [ ] Commit: `refactor: generic adapter resolution, inventory deferrals, generated activation fixture`

### Task 6: One policy-token validator and receipt hardening (r4 F18, r5 F17)

Files:
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] `RuntimeCapabilitiesTest#test_single_policy_token_validator`; given repo-root equality mismatch, generation mismatch, and a foreign absolute repo root, expects one verdict from the single parameterized validator in `runtime_capabilities.py` at both boundaries (launch validity and claim revalidation); the codex-local `_valid_policy_token` and `_validate_policy_token` copies are deleted.
- [ ] `RuntimeCapabilitiesTest#test_load_approval_receipt_requires_owner_only_permissions`; given a receipt file with mode 0644, expects rejection; given mode 0600 with a matching runtime, expects the receipt to load; given mode 0600 but a receipt missing `config_path` or `policy_fingerprint`, expects rejection (both fields are required, never optional).
- [ ] `RuntimeCapabilitiesTest#test_load_approval_receipt_cross_checks_config_policy`; given a receipt recording a codex config path plus a policy fingerprint, expects `load_approval_receipt` to re-read that config path from the host (an injected config root in tests, never the ambient environment) and to reject when the file is missing or the recorded non-interactive approval policy is absent; the receipt schema gains exactly these two fields (`config_path`, `policy_fingerprint`), both mandatory, documented in `runtime-contract.md` as operator-attested evidence, not a cryptographic credential.
- [ ] Update the existing 0644 shape-only approval-receipt fixtures in `scripts/test_execute_plan_runtime.py` and `scripts/test_execute_plan_runtime_codex.py` in this same commit: mode 0600 plus the two new required fields, with the config path pointing at an injected config root, so the CLI approval-receipt flows stay green under the mandatory reading.
- [ ] Run → expect RED: the registry discovery command.
- [ ] Implement the unified validator, delete the codex-local copies, and add the permission and cross-check requirements to `load_approval_receipt`.
- [ ] Run → expect GREEN: the registry discovery command passes.
- [ ] Commit: `fix: unify policy-token validation and harden approval receipts`

### Task 7: Sever the adapter import edge, kill order, retry clamp (r6 F5, r5 F16, r6 F6, r5 F11; closes r5 F14)

Files:
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_runtime_capabilities.py`

- [ ] Authoring note verified: no test currently patches `bounded_evidence` or `MAX_EVIDENCE_BYTES` via `setattr` or string-form `mock.patch`; re-run the symbol-move patch audit at execution before moving, covering all reference forms: direct imports, module-qualified references (`runtime.bounded_evidence`, `runtime.MAX_EVIDENCE_BYTES`, which exist today at `scripts/test_execute_plan_runtime.py:839-840`), `setattr` patches, and string-form `mock.patch`; retarget every hit to the new owning module in the same commit, or have the driver re-export the moved symbols from `runtime_capabilities` (a driver-to-capabilities import only; the adapter still imports nothing from the driver).
- [ ] `RuntimeCapabilitiesTest#test_bounded_evidence_owned_by_capabilities`; given `bounded_evidence` and the `MAX_EVIDENCE_*` constants, expect their single home in `runtime_capabilities.py`; both the driver and the adapter import from there; `scripts/execute_plan_runtime_codex.py` contains no `from execute_plan_runtime import` line (this closes the r5 F14 unused-import finding by removal).
- [ ] `CodexAdapterTest#test_identity_check_precedes_sigkill`; given a timeout kill where `_pid_identity_matches` flips to false between poll and kill (injected), expects the identity consulted immediately before `os.kill` so no `SIGKILL` lands on a recycled foreign process.
- [ ] `CodexAdapterTest#test_recycled_pid_test_uses_disposable_child`; given the recycled-PID timeout test rebuilt around a real disposable child process instead of `os.getpid()`, expects a regressed identity guard to fail an assertion instead of risking the test runner's own process.
- [ ] `RuntimeCapabilitiesTest#test_zero_retry_budget_grants_zero_retries`; given `retry_budget = 0`, expects zero retries (clamp `max(0, ...)` plus an explicit `none` retry mode); given budget 2, expects two.
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` and `python3 -m unittest discover -s scripts -p 'test_runtime_capabilities.py'`.
- [ ] Implement the move, the kill-order change, and the clamp change in one pass; imports retargeted everywhere in the same commit so every commit compiles.
- [ ] Run → expect GREEN: both discovery commands pass.
- [ ] Commit: `refactor: capabilities owns evidence helpers; identity-safe kill; zero-budget clamp`

### Task 8: Documented seeding boundary (r4 F15; r6 overflow)

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] `ExecutePlanRuntimeTest#test_create_operation_seeds_manifest`; given `--operation create` with a task list and owner, expects a 0600 manifest with pending tasks and a fresh generation, shape-identical to the selftest seeding; `create` joins the CLI operation choices.
- [ ] `ExecutePlanRuntimeTest#test_directory_valued_allowed_path_rejected_with_actionable_error`; given an `allowed_paths` entry naming a directory, expects the create and validation path to reject it with an actionable error naming the entry; directory prefix matching stays explicitly out of scope (r6 overflow disposition: fail closed beats a silent never-matching entry).
- [ ] Docs: `agents/skills/execute-plan/SKILL.md` Phase 0/1 names the `create` operation as the only documented path that translates plan checkboxes into machine manifest state.
- [ ] Docs: `runtime-contract.md` documents the resume reconciliation rule (the manifest wins; divergent checkboxes are rewritten through the skill-gate step) and the seeding producer for per-task `allowed_paths` that feeds the empty-scope fail-closed gate.
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` for the `create` operation witness.
- [ ] Implement the `create` operation and land both doc edits.
- [ ] Run → expect GREEN: the discovery command passes; `expect_match '"create"' scripts/execute_plan_runtime.py` holds.
- [ ] Commit: `feat: create operation as the documented manifest seeding boundary`

### Task 9: done-lock cleanups (r4 overflow a; r5 overflow items 1-3)

Files:
- `scripts/done-lock.sh`

- [ ] `DONE_LOCK_GENERATION` is removed as a tautological alias of the token: the fence writes and reads the lock identity under the single `DONE_LOCK_TOKEN` name in the session file, release consumes the token directly instead of hard-failing on a missing alias export, and the selftest covers release under the new shape.
- [ ] Dead `read_label` is deleted; the used argument loops give a clear error on a missing `--label` value and reject an empty label.
- [ ] `try_acquire`'s two near-identical acquisition bodies collapse into one helper used by both call sites; `bash scripts/done-lock.sh selftest` stays green.
- [ ] `load_lock_session` (repo-controlled file sourcing, arbitrary code execution if ever wired) is deleted; the no-sourcing invariant is asserted by the selftest and by the Validation Commands sweep.
- [ ] Run → expect GREEN after each bullet: `bash scripts/done-lock.sh selftest`.
- [ ] Commit: `refactor: done-lock alias, label parsing, acquisition helper, no-sourcing`

### Task 10: Contract prose single home (r5 F15; r4 overflow c, d, e)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/plan-readiness/README.md`
- `README.md`

- [ ] `agents/skills/execute-plan/SKILL.md` shrinks its "Runtime-neutral execution contract" section to a short summary plus the read-first pointer sentence "Read agents/skills/execute-plan/runtime-contract.md for the normative runtime contract, result schema, policy boundary, manifest ownership, and continuation transitions."; every contract edit after this task lands in the contract file only.
- [ ] `runtime-contract.md` keeps the single full statement of the hook capability boundary ("A host hook cannot enforce a policy when its event cannot block the operation or cannot carry the payload needed to evaluate the policy."); `agents/hooks/skill-gate/README.md` "Capability boundary and registry parity" section becomes a pointer that must not reuse that sentence; the lessons-recall and plan-readiness READMEs are swept for restatements and converted to pointers the same way.
- [ ] Verify-and-close (r4 overflow d): confirm the contract's lock section describes the done-lock session fence as its own file matched by generation and token and carries no env-field list; record the check in this task's log; no edit if already accurate.
- [ ] `README.md` moves the `runtime-contract.md` row out of the Scripts table to beside the execute-plan skill catalog entry; sweep the catalog for stale references after the move.
- [ ] Run → expect GREEN: the Validation single-home grep (exactly one file carries the full statement) and the SKILL.md pointer pin.
- [ ] Commit: `docs: single home for runtime contract and capability boundary prose`

### Task 11: Hermeticity witnesses that discriminate (hermeticity origin F2, F4; r5 F10; r6 F11)

Files:
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] `CodexAdapterTest#test_subprocess_env_sanitized`; given a poisoned parent environment launched through the real `_subprocess_runner`, expects the child to see only `SAFE_ENV_KEYS` plus the runner's injected policy variables (`EXECUTE_PLAN_POLICY_TOKEN` and `EXECUTE_PLAN_ALLOWED_PATHS`); mutation probe: widen `SAFE_ENV_KEYS` by one key, expect this test to fail, revert (probe set recorded in the task log per the empirical-derivation rule).
- [ ] `CodexAdapterTest#test_no_live_installation_read`; given `HOME` and `EXECUTE_PLAN_PACKAGE_MANIFEST` pointed at a fixture root with reads observed via an audit hook or a patched opener, expects the adapter lifecycle to open nothing outside the fixture root.
- [ ] `CodexAdapterTest#test_package_manifest_ambient_read`; given `EXECUTE_PLAN_PACKAGE_MANIFEST` absent, expects construction to take the documented default-deadline fallback (the current contract; the hermeticity origin's missing-var fail-closed upgrade is declined here as a behavior change that would break non-activated runs and roughly ten existing test constructions, and the decline is recorded in the Task 12 disposition); given a valid manifest path, expects the manifest loaded and used.
- [ ] `ExecutePlanRuntimeTest#test_hermeticity_round_trip_asserts_locale_and_clock_env`; given the fixture environment with `TZ=UTC`, `LANG=C`, `LC_ALL=C`, expects the subprocess round-trip in `test_runtime_replay_is_hermetic_to_fixture_root` to assert all three took effect in the child, not only `cwd` and `HOME`.
- [ ] `ExecutePlanRuntimeTest#test_patched_socket_window_drives_continue_parent`; given `continue_parent` driven across the patched-socket window, expects the network guard to intersect the code under test (the guard observes a real attempt or is documented and removed as decorative in the same task); the same drive-or-drop rule applies to the `outside.txt` assertions that today never intersect the code under test.
- [ ] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` (these witnesses pin correct current behavior; each carries a recorded mutation probe or a drive-or-drop resolution instead of a RED step).
- [ ] Commit: `test: discriminating hermeticity witnesses for env, manifest, and network guards`

### Task 12: Verify-and-close, errata disposition, origins close-out

Files:
- `docs/history/backlog/` (the five origin items, completion move)
- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (checkboxes)

- [ ] Verify-and-close (r5 F9): confirm every witness invocation carries `-c core.quotePath=false` (4 invocation sites at authoring: the diff, status, merge-base, and committed-diff witnesses; the Validation command counts invocation-form matches only, so the docstring mention does not count); no re-fix; the closure is recorded here.
- [ ] Errata disposition (prose-accuracy origin): re-probe `test_evidence_and_fixtures_are_hermetic` (asserts evidence redaction, secret absence, and manifest mode 0600 only) and `test_runtime_replay_is_hermetic_to_fixture_root` (holds the environmental hermeticity assertions); record in the task log that the four prose findings are dispositioned record-only and the completed plan body at `docs/plans/completed/2026-09-09-agent-agnostic-execute-plan.md` stays untouched per the completed-history refusal rule.
- [ ] Move all five backlog origins to `docs/history/backlog/completed/` marking `Status: done`, adding a one-line disposition note in the same edit where the disposition differs from a plain fix: the prose-accuracy item (record-only under the refusal rule), the r5 origin (F9 verify-closed, F14 closed by the Task 7 move), the r6 origin (F1 closed by the Task 2 digest anchor; overflow items closed by the Task 2 retention rule and the Task 8 directory-path rejection), and the hermeticity origin (the missing-var fail-closed upgrade declined as a behavior change breaking non-activated runs; the ambient-read witness covers both branches of the current contract instead).
- [ ] Complete this plan per the plans lifecycle: archive move to `docs/plans/completed/`, and append the ownership-registry row in the same pass when the doc-hierarchy registry convention is present.
- [ ] Run → expect GREEN: the full Validation Commands block on the final tree, including the cleanup-baseline checker with this plan's ledger allow-list.

## Documentation Impact Assessment

- `agents/skills/execute-plan/runtime-contract.md`: policy anchor, seeding operation and reconciliation rule, receipt semantics (Tasks 2, 6, 8).
- `agents/skills/execute-plan/SKILL.md`: seeding path naming and contract summary shrink (Tasks 8, 10).
- `agents/hooks/*/README.md` and `README.md`: capability-boundary pointers and catalog row move (Task 10).
- No new documentation files; no README config section changes.
