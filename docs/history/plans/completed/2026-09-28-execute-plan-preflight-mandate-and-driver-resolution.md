# Plan: Execute-plan preflight mandate, direct-claim prelaunch recovery, and driver resolution

Backlog origins (scope of record):
- docs/history/backlog/2026-09-28-execute-plan-direct-claim-prelaunch-recovery.md
- docs/history/backlog/2026-09-28-execute-plan-driver-resolution-and-project-state.md

Driving force: automation (primary), efficiency (secondary)
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-execute-plan-preflight-mandate-and-driver-resolution-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

An execute-plan run can no longer strand a blocked direct claim for the full claim lease, and can no longer resolve the shared driver against the wrong repository root.

- A direct initial claim blocked before launch by a `runtime-policy-unavailable` refusal is reclaimed immediately under identity fencing, whichever driver site persisted the refusal: the blocked-persist boundary leaves no stale launch residue, and the reclaim proof reads the persisted shapes the driver actually writes.
- The preflight-emitted continuation command is self-sufficient: it carries the driver's own absolute path, the run's recorded runtime id, the target repository root, and any recorded approval receipt, all shell-quoted, so invoking exactly that command reaches the adapter and cannot repeat the witnessed omission; a failing preflight emits no command.
- The execute-plan skill mandates a passing preflight before any claim is created or continued, mandates the runtime id at create, and forbids hand-assembled continuation commands; the documented recovery sequence records its evidence at the reclaim boundary in one locked transition, and a bounded prelaunch-reclaim budget caps a persistent-blocker cycle with a named terminal outcome.
- One normative resolution-policy statement (runtime-contract.md) states that the driver implementation is shared while every run artifact stays under the target project's facts-resolved tmp dir; the skill carries the scoped application statement and cross-references the contract.

## Terms

- preflight: the driver's read-only `--operation preflight`; validates readiness, plan-versus-claim scope drift, approval evidence, and activation evidence, emits one canonical continuation command on a passing result, and never mutates state.
- canonical continuation command: the command string preflight emits for the decision it made (the direct-continuation command, or the successor-advance command for an admitted done-successor state), carrying the same self-sufficiency fields; the only command the skill permits for advancing a claim.
- direct initial claim: a claim created for a task with no prior claim, no prepared handoff intent, and no registered worker.
- prelaunch activation failure: a blocked claim the driver can prove never launched a worker: no registered worker identity, a blocked receipt whose reason code is exactly `runtime-policy-unavailable` (never the broader hard-block family), receipt claim identity equal to the live claim, and no stale launch residue (the blocked-persist boundary releases the reservation and drops the launch record it had just written).
- claim lease: `CLAIM_LEASE_SECONDS` (14,400 seconds); the age an ordinary reclaim requires.
- approval receipt: the auditable file supplied through `--approval-receipt` proving a verified non-interactive host approval policy; persisted resolved to an absolute path.
- shared driver resolution: the rule that the driver implementation is one shared deployed copy while the repository root and tmp artifacts resolve from the target project.

## Assumptions

- assume resolution policy option (1) from the driver-resolution origin: the shared implementation stays the single deployed source of truth and every invocation pins the target `--repo-root`; a project-local `.ai-playbook/` entry point remains a deliberate, explicitly configured override and is not built by this plan; basis: the origin's Expected clause and the machinery-elimination pass that removed the deploy helper.
- assume the direct-claim recovery arm adds a parallel identity fence and keeps the existing handoff-intent fence untouched for intent-backed claims; basis: the origin's Expected clause, "extends proven-prelaunch recovery from prepared handoffs to direct initial claims".
- assume approval evidence and the runtime id become recorded state at the mutating manifest operations only (create seeds them; claim, continue, resume, worker-start, and reclaim record supplied values in the same locked save as their transition; refusals stay byte-identical), while preflight, readiness, and diagnose stay strictly read-only; basis: preflight's write-free construction contract and the recovery sequence's single-passable boundary.
- assume emitted-command hardening (absolute driver path, runtime id, `--repo-root`, recorded absolute receipt path, shell-quoting) makes the emitted command safe to invoke verbatim from any working directory; basis: the driver-resolution origin's witness and the resume watcher's quoting precedent.
- assume skill-text insertions stay runtime-neutral; basis: the shared-body forbidden-term gate `test_shared_skill_bodies_remain_runtime_neutral` in scripts/test_execute_plan_runtime.py.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: preflight becomes the mandated claim boundary and its emitted command becomes self-sufficient, so a blocked direct claim recovers immediately and the shared driver always resolves the right repository root.

The witnessed failure chain (consumer run, 2026-09-28): a continuation command omitted the required `--approval-receipt`; the adapter rejected the policy token; the driver recorded `runtime-policy-unavailable` against a direct initial claim before launch; early reclaim refused because the four-hour lease had not expired, so the run stranded. A second consumer session watched the driver resolve its repository root from the working directory and could not tell shared implementation from project-local run artifacts.

After this plan the same chain reads differently. The skill mandates preflight before any claim is created or continued and the runtime id at create, so the omission cannot be hand-assembled and the default create shape cannot wedge. The driver persists a supplied approval receipt (resolved to an absolute path) and the runtime id at the mutating boundaries; the launch-path blocked persist releases the launch residue it had just written, so a prelaunch-proofable claim stays proofable; and the emitted command carries the recorded receipt, the runtime id, the driver's own absolute path, and `--repo-root`, all shell-quoted, while a failing preflight emits nothing. The recovery sequence is one reclaim invocation: supply `--approval-receipt` and `--runtime` to reclaim, which validates, records, and rotates in the same locked transition; preflight again; invoke the emitted command. A two-attempt prelaunch-reclaim budget caps a persistent blocker with a named terminal outcome. The normative contract states the resolution policy and the direct-claim proof boundary, and integration locks prove each working directory resolves the target repository and lands artifacts under its resolved tmp dir. The mandate binds only against a driver whose emitted command pins the script path, runtime, and root; the skill says to check that line before invoking.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the direct-claim recovery arm reclaims only when every proof conjunct holds against the persisted shapes the driver actually writes, with one canary per proof conjunct and one accept canary per prelaunch refusal site; canaries show each single missing or mismatched conjunct is refused.
- correctness: the emitted command re-invoked verbatim from a foreign working directory resolves the same manifest and target root, reaches the recorded runtime's adapter, and lands artifacts under the target project's resolved tmp dir; the manifest path reads and emits under one resolution rule.
- reliability: an omitted approval receipt cannot strand a direct claim for the lease duration (the bootstrapping reclaim records and accepts in one invocation); a persistent blocker cannot loop block-reclaim-preflight forever (a two-attempt prelaunch-reclaim budget ends in the named `prelaunch-reclaim-cap` outcome); a failing preflight emits no command.
- maintainability: one normative owner (runtime-contract.md) states the resolution policy; the skill carries a scoped application statement and cross-references it instead of duplicating it.

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py` exits 0 including the new persistence, emission, direct-claim, and path-resolution tests.
- The shared-body runtime-neutrality test still passes after the skill insertions.
- The no-em-dash and public-hygiene gates exit 0 over the changed files.

**Ship when:**
- Consumer repositories pick up the updated shared skill, contract, and driver on their next sync, driver deploy first, so the mandated emitted command is never older than the skill mandating it; no consumer-side action beyond the sync is required by this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- scripts/execute_plan_runtime.py

**Tests:**
- scripts/test_execute_plan_runtime.py

**Documentation:**
- agents/skills/execute-plan/SKILL.md (including the Step 0.6 precondition example and the Budget gate watcher command examples)
- agents/skills/execute-plan/runtime-contract.md (including the `reclaimed` transition row and the preflight paragraph this plan extends)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- scripts/execute_plan_resume_watcher.py implementation changes; this plan only reuses its quoting precedent (the path-resolution locks cover the behavior).
- Consumer repository wrappers or a reintroduced deploy helper; rejected by the p78 log entry after the machinery-elimination pass.
- Other driver siblings (worktree bootstrap, worker registry); no witnessed defect names them.

## Validation Commands

```bash
python3 scripts/test_execute_plan_runtime.py
python3 scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md scripts/execute_plan_runtime.py scripts/test_execute_plan_runtime.py
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md scripts/execute_plan_runtime.py scripts/test_execute_plan_runtime.py
```

### Task 1: Driver persists approval receipts and the runtime id at the mutating boundaries

Files:
- scripts/execute_plan_runtime.py
- scripts/test_execute_plan_runtime.py

- [x] `ExecutePlanRuntimeTest#test_approval_receipt_and_runtime_persist_at_create`; given a create invocation supplied a valid `--approval-receipt` and `--runtime`, expects the persisted manifest to record `approval_receipt` with the receipt path resolved to an absolute path plus the runtime id, and a later `preflight` invoked without the flags to validate the recorded receipt and report "approval receipt: valid" [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_records_supplied_evidence_on_rotation`; given a reclaim invocation supplied `--approval-receipt` and `--runtime` over a blocked direct claim, expects the same locked transition to validate the evidence, accept under the prelaunch arm, rotate the claim, and persist the receipt (absolute path) and runtime id; a refused reclaim persists nothing (byte-identical manifest); this test stays RED at the Task 1 boundary and greens when Task 3's acceptance arm lands [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_persists_at_every_mutating_boundary`; parameterized over create, claim, continue, resume, worker-start, and reclaim, each invoked with the evidence flags where its CLI accepts them, expects the persisted manifest to record the supplied evidence (absolute receipt path plus runtime id) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preflight_records_nothing`; given a preflight invocation supplied `--approval-receipt` and `--runtime`, expects the manifest bytes byte-identical after the operation (the read-only contract holds; the existing preflight byte-identity tests stay green) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preflight_fails_naming_policy_remedy`; given a manifest whose task carries a blocked receipt with reason `runtime-policy-unavailable` and no recorded approval receipt, expects preflight to fail with a problem naming both candidate causes and concrete remedies (when the blocked receipt coexists, the remedies name reclaim-with-flags first; claim-with-flags only for a live pre-claim manifest; re-create only for the genuine pre-claim case), and to emit no continuation command [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_failing_preflight_emits_no_command`; given a direct-continuation manifest recording an approval receipt whose file has been deleted, expects preflight to fail with the load-error problem named and `continuation_command` absent (the fail-closed emission gate; this is new behavior, so the test is RED until the gate lands) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_post_done_preflight_emits_successor_advance_command`; given a manifest whose task completed through a done handoff leaving a prepared-intent successor claim and recorded evidence, expects preflight to pass and to emit the successor-advance command and the readiness operation's decision output for that state to stay unchanged; given a mismatched or consumed intent, expects the activation-evidence problem to stand; given a receipt-less manifest in the same successor state, expects the admission to stand and the emitted command to carry no `--approval-receipt` [class: REPOSITORY_TEST]
- [x] Run the new tests; expect tests 1, 2, 5, and 6 RED, the successor-advance canary RED, and test 3 RED where its sweep reaches unimplemented sites, test 4 GREEN at this task boundary [class: REPOSITORY_TEST]
- [x] Implement: the CLI boundary validates a supplied receipt (the existing `load_approval_receipt` path, resolved to absolute) and, for the mutating manifest operations only (create, claim, continue, resume, worker-start, reclaim), persists `approval_receipt` (absolute path, plus runtime) and the runtime id into the machine manifest in the same locked save as the operation's own transition; a refused operation persists nothing; preflight, readiness, and diagnose mutate nothing; operations outside the approval-evidence persistence scope (precondition; the watcher family's own state writes are unchanged) are excluded [class: IMPLEMENTATION_REQUIRED]
- [x] Implement: preflight's problem list gains the policy-evidence arm naming both remedies per cause (when a `runtime-policy-unavailable` blocked receipt coexists, the remedies name reclaim-with-flags first; re-create is scoped to the genuine pre-claim case), and the continuation command is gated on `not problems` so a failing preflight emits no command (new fail-closed behavior) [class: IMPLEMENTATION_REQUIRED]
- [x] Implement: preflight admits the exact fresh done-successor as authorized prelaunch state: a live claim backed by a `prepared` handoff intent with task, token, and generation agreement is exempt from the activation-evidence problem and from the not-provable failed condition that the claimed successor status otherwise trips, and its approval-evidence conjunct validates the recorded receipt only where the manifest records one (a receipt-less manifest admits under the receipt-less emission rule); the exemption and the emission are preflight-local (the shared readiness decision's returned tuple and the readiness operation's documented closed decision set are unchanged), and preflight emits the canonical successor-advance command for the admitted state under the same self-sufficiency rules (quoted absolute script path, recorded runtime id and root, recorded receipt); identity-mismatched or already-consumed intents are never admitted [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN for the tests Task 1 closes (tests 3, 4, 5, 6, and the successor-advance canary); test 1 greens here and test 2 stays RED until Task 3's acceptance arm lands [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan driver persists approval evidence at mutating boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Emitted continuation command becomes self-sufficient

Files:
- scripts/execute_plan_runtime.py
- scripts/test_execute_plan_runtime.py

- [x] `ExecutePlanRuntimeTest#test_emitted_command_carries_runtime_root_and_receipt`; given preflight on a direct-continuation manifest recording an approval receipt and a runtime id, expects the emitted command to contain the driver's own absolute script path, `--runtime` with the recorded id, `--repo-root` with the resolved repository root, and `--approval-receipt` with the recorded absolute path, every interpolated value shell-quoted (the space-bearing-root case stays one argument) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_emitted_command_without_receipt_omits_flag`; given preflight on a receipt-less manifest, expects the emitted command to carry the quoted absolute script path, `--runtime`, and `--repo-root`, and to carry no `--approval-receipt` argument [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_emitted_command_survives_space_bearing_root`; given a target repository root containing a space, expects the emitted command to remain a valid paste-and-run line (quoting witnesses the resume watcher's injection precedent) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preflight_without_runtime_id_fails_closed`; given a direct-continuation manifest recording neither receipt nor runtime id, expects preflight to fail with a problem naming the missing runtime id and the re-create or claim-boundary remedies and to emit no command [class: REPOSITORY_TEST]
- [x] Run the new tests; expect all four RED at this task boundary (the current emission carries only the manifest path and `--operation continue`, and no fail-closed runtime gate exists) [class: REPOSITORY_TEST]
- [x] Implement: the preflight emission builds the command from the driver's own resolved script path and appends `--runtime` with the manifest-recorded runtime id, `--repo-root` with the driver's resolved repository root, and `--approval-receipt` exactly when the manifest records one; every interpolated value is an asserted-absolute path passed through `shlex.quote` (an absolute path cannot parse as an option); the manifest path is resolved at preflight entry against the driver's repository root and the same resolved path is read and emitted (the resolution rule is preflight-scoped; other operations keep their existing manifest resolution and the emitted absolute path keeps the round trip consistent); when the manifest records no runtime id, preflight fails with a named problem and emits no command; the existing preflight fixture family (the shared setUp manifest and the preflight success test that runs over it) gains the recorded runtime id in the same change set, and the touched pre-existing test (`test_preflight_success_mutates_nothing_and_names_one_continuation`) is named here for traceability [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan preflight emits a self-sufficient continuation command` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Direct-claim prelaunch recovery arm with identity fencing and a bounded budget

Files:
- scripts/execute_plan_runtime.py
- scripts/test_execute_plan_runtime.py

- [x] `ExecutePlanRuntimeTest#test_blocked_persist_releases_launch_residue`; given the real launch-path chain (claim launched, adapter refused with `runtime-policy-unavailable`, no worker registered), expects the blocked persist to release the capacity reservation and drop the launch record in the same locked write, leaving the durable state the prelaunch proof reads [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_accepts_blocked_direct_claim_launch_path`; driving the real chain from the previous test, expects reclaim to accept immediately (the witnessed shape: `resume_allowed` false, receipt token and generation equal to the live claim) and to rotate the claim token and generation [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_accepts_no_adapter_blocked_direct_claim`; given the claim-time "no adapter configured" persisted shape (no launch record, no reservation), expects reclaim to accept [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_accepts_activation_failure_blocked_direct_claim`; given the claim-time adapter activation-failure persisted shape, expects reclaim to accept [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_bootstraps_supplied_evidence`; given a blocked direct claim whose manifest records no approval receipt, a reclaim invocation supplied `--approval-receipt` and `--runtime` accepts and records in the same locked transition (the bootstrapping invocation of the documented recovery sequence) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_refuses_direct_claim_token_mismatch`; given the same state with the receipt's embedded claim token differing from the live claim token, expects the stale-claim refusal and a byte-identical manifest [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_refuses_direct_claim_generation_mismatch`; given the receipt's embedded generation differing from the live claim generation, expects the stale-claim refusal [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_refuses_direct_claim_with_launch_record`; given the real launch-path blocked state with the launch record and matching capacity reservation hand-restored into the manifest before reclaiming (the receipt reason stays `runtime-policy-unavailable`), expects the stale-claim refusal with a byte-identical manifest [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_survives_foreign_stale_reservation`; given a reclaimable claim whose manifest carries a stale launch reservation matching no live claim, expects reclaim to succeed and to clear the reservation where today the capacity gate refuses [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_expired_lease_reclaim_ignores_budget_cap`; given a task record at the prelaunch-reclaim budget whose claim lease has expired, expects the ordinary reclaim to proceed through rotation regardless of the count [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_refuses_direct_claim_with_registered_worker`; given the blocked receipt with a registered worker identity on the task, expects the reclaim refusal [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_refuses_non_prelaunch_reason`; given a blocked receipt whose reason code is any value other than `runtime-policy-unavailable` (for example `approval-required` from the hard-block family), expects the reclaim refusal [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_without_evidence_flags_refuses_early_path`; given a blocked direct claim and a reclaim invoked without `--approval-receipt` where the manifest records no receipt, expects the direct-claim arm to refuse the early path and the claim to wait the ordinary lease (the driver enforces the skill ordering) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_prelaunch_reclaim_budget_caps_the_cycle`; driving two real block-reclaim-re-claim cycles against a deterministically refusing adapter, expects the third direct-claim prelaunch reclaim to refuse with the named `prelaunch-reclaim-cap` outcome directing the operator at the adapter policy [class: REPOSITORY_TEST]
- [x] Run the intent-backed early-recovery tests; expect GREEN unchanged at this task boundary (existing handoff-intent behavior is not touched) [class: REPOSITORY_TEST]
- [x] Run the new tests; expect the three site-accept canaries, the bootstrap canary, the residue-release test, the budget-cap canary, and the stale-reservation canary RED, and the five refusal tests plus the no-flags gate test GREEN (six GREEN tests), with the expired-lease-at-cap canary GREEN at this boundary as a regression lock over already-satisfied behavior (with no handoff intent and no acceptable shape the predicate returns False and reclaim falls through to the lease gate, which is what the refusal tests assert) [class: REPOSITORY_TEST]
- [x] Implement: the launch-path blocked persist releases the capacity reservation and drops the launch record for every non-resumable outcome with a written reservation (the `runtime-policy-unavailable` and `runtime-error` launch-path shapes; timeouts stay resumable and untouched), stamps the verified claim identity onto an adapter-returned raw receipt at the same persist tail (the tail re-verifies token and generation under the lock); the identity-keyed stale-reservation sweep (task, claim token, and generation matching no live claim, where live means any claim carrying the reservation's identity triple including the reclaim-target blocked claim) runs after the refuse-only fences immediately before the capacity reconciliation so the gate sees the post-sweep set; each group-member reclaim exit pops the identity-keyed reservation in its own existing locked save; the two claim-time persisted refusal sites (the "no adapter configured" and adapter activation-failure outcomes) embed `claim_token` beside `generation` (the launch-path TypeError site is the conforming model); the shared prelaunch conjuncts restructure so the direct-claim branch evaluates on the real persisted shapes (`resume_allowed` false tolerated inside the branch) [class: IMPLEMENTATION_REQUIRED]
- [x] Implement: `_proven_prelaunch_activation_failure` accepts a direct claim (no handoff intent, no registered worker, no uncleaned launch residue) when the blocked receipt's reason is exactly `runtime-policy-unavailable` and its embedded claim token and generation equal the live claim's, supplied-and-validated evidence at the invocation satisfies the recorded-receipt conjunct, and the task-record prelaunch-reclaim count is under the budget of two (two = the initial recovery invocation plus exactly one transient retry; a third prelaunch reclaim is by definition a persistent policy blocker); the count lives on the task record, where it survives both the claim rotation and the task reset, is incremented in the same locked rotation save as each accepted early reclaim, and the cap gates only the lease-bypass path: at or beyond `CLAIM_LEASE_SECONDS` the ordinary reclaim proceeds through rotation regardless of the count; the at-cap state (every other conjunct holding, count at the budget) is detected beside the predicate and returns the named `prelaunch-reclaim-cap` refusal before lease accounting, independent of lease expiry; the intent-backed path keeps its existing successor-identity match [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan reclaims a blocked direct claim under prelaunch identity fencing` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Skill preflight mandate, contract proof boundary, and resolution policy

Files:
- agents/skills/execute-plan/SKILL.md
- agents/skills/execute-plan/runtime-contract.md

- [x] SKILL.md, Runtime-neutral execution contract and the machine-manifest seeding region: add the preflight mandate; before any claim is created or continued, run `--operation preflight` and invoke only the canonical continuation command it emitted on a passing result (the mandate scopes to that emitted command for the decision preflight made; the batch opt-in and parallel-group claim forms the skill documents are separate driver contracts governed by their own steps, and other driver-side operations stay governed by theirs); hand-assembled continuation commands are never invoked; before invoking the emitted command, verify it pins `--repo-root` and `--runtime` (an emission without them means the deployed driver predates the mandate: stop and deploy the driver first); document the blocked-direct-claim recovery sequence as one reclaim invocation (reclaim with `--approval-receipt` and `--runtime` validates, records, and rotates in the same locked transition; preflight again; invoke the emitted command), the two-attempt prelaunch-reclaim budget (initial recovery plus one transient retry), and the `prelaunch-reclaim-cap` outcome; document the done-successor advance: preflight admits the prepared-intent successor and emits its canonical advance command [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md, the create guidance and the Step 0.6 precondition example (sweep every `scripts/execute_plan_runtime.py` invocation in the skill): the create invocation mandates `--runtime` (and the receipt when applicable); the scoped application statement for the resolution policy cross-references runtime-contract.md as the normative owner, states that the target repository root is passed or preserved at every invocation boundary, and covers every remaining relative invocation form the sweep finds, including the Phase 4 terminal-gate example and the interruption-reporting example [class: IMPLEMENTATION_REQUIRED]
- [x] runtime-contract.md, Durable driver boundary: add the normative resolution policy; run artifacts stay under the target project's facts-resolved tmp dir; a project-local entry point is legitimate only as a deliberate, explicitly configured override; the emitted canonical continuation command pins script path, runtime id, and repository root so invocation from the shared tooling checkout cannot silently retarget the run [class: IMPLEMENTATION_REQUIRED]
- [x] runtime-contract.md, the `reclaimed` transition row and the preflight paragraph: extend the reclaimed evidence cell with the direct-claim prelaunch fast path beside the existing lease-expiry exit (reason code exactly `runtime-policy-unavailable`, receipt-embedded token and generation equality, no registered worker, no launch residue, evidence supplied at the invocation or already recorded, the two-attempt task-record budget ending in `prelaunch-reclaim-cap` and gating only the lease-bypass path), define the direct-claim proof boundary and its fencing guarantees (supplied-at-reclaim evidence persists on success only; refusals stay byte-identical; a claim rotated between block and reclaim fails the equality fence back to the lease), and state in the preflight paragraph the policy-evidence problem arm, the prepared-intent successor admission with its preflight-emitted advance command (the readiness operation's decision set unchanged), and the fail-closed emission rule (a failing preflight emits no command) while keeping the never-mutates-state statement true [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep the lease-only reclaim statements both surfaces carry (the SKILL.md recovery-table reclaim row and the runtime-contract.md interrupted-claim recovery sentences plus the reclaim operation-table row): each names the direct-claim prelaunch fast path beside the existing lease expiry and the r4-F2 lease-waived exit, so no operator-facing sentence still says reclaim happens only after lease expiry; Task 4's contract touch set also names the reason-code inventory paragraph, extending the CLI-envelope sentence with `prelaunch-reclaim-cap` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

- F1 admission receipt-less ambiguity (architecture#dual-surface-policy-parity): folded
- F2 Task 1 boundary inventory and canary ordering (testing#non-discriminating-pin): folded
- F3 policy-remedy canary split (consistency#policy-remedy-test-implementation-split): folded
- F4 cap detection and sweep insertion semantics (implementation#acceptance-mechanism-gap): folded
- F5 sweep ordering ambiguity (quality#pipeline-ordering): folded
- F6 expired-lease canary classification (testing#non-discriminating-pin): folded
- F7 no-runtime-id remedy text (testing#needle-unreachable-from-prescribed-text): folded
- F8 carve-out form not on surface (consistency#carve-out-form-not-on-surface): folded
- F9 reason-code inventory and group-exit drain (documentation#inventory-drift, security#sweep-drain-reachability): folded
- [x] Run the shared-body runtime-neutrality test; expect GREEN (insertions carry no runtime-specific vocabulary) [class: REPOSITORY_TEST]
- [x] Commit: `docs: execute-plan preflight mandate, proof boundary, and resolution policy` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Path-resolution integration locks from every root

Files:
- scripts/test_execute_plan_runtime.py

- [x] `ExecutePlanRuntimeTest#test_cli_resolves_target_root_from_flag_over_cwd`; given a driver CLI invocation from a foreign working directory with `--repo-root` pointing at a temporary target repository, expects a preflight in that mode to emit `--repo-root` with the flag-given root and the manifest and run artifacts to land under the target repository's resolved tmp dir (characterization plus discriminating observable) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_cli_resolves_target_root_from_cwd_default`; given a driver CLI invocation with no `--repo-root` whose working directory is the target repository, expects a preflight in that mode to emit `--repo-root` with the cwd-resolved root (the complementary leg) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_emitted_command_reinvoked_from_foreign_cwd_reaches_adapter`; given the Task 2 emitted command, parse its argv and re-invoke it in-process through the driver's main with the adapter seam patched to a recording fake and the process working directory temporarily set to the foreign directory; expects the fake to receive the recorded runtime id and the same resolved target root and manifest, and artifacts to land under the target repository's resolved tmp dir (no real worker launches; these tests construct the driver directly or invoke the CLI, bypassing the shared helper that hardcodes its repo root) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_relative_manifest_resolves_identically_for_read_and_emission`; given a preflight invoked with a relative `--manifest` from the foreign working directory, expects the read path and the emitted command to target the same resolved file [class: REPOSITORY_TEST]
- [x] Run all four tests at this task boundary; expect GREEN as characterization and integration locks over the completed Tasks 1-4 [class: REPOSITORY_TEST]
- [x] Run the full Validation Commands block; expect every gate green [class: REPOSITORY_TEST]
- [x] Commit: `test: execute-plan path-resolution locks for shared and target root invocations` [class: IMPLEMENTATION_REQUIRED]
