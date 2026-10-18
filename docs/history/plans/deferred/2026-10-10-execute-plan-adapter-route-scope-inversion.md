# Plan: Execute-plan adapter-route scope inversion (represent the witnessed route, scope the adapter to fan-out)

Backlog origin: docs/history/backlog/2026-10-10-execute-plan-adapter-route-scope-inversion.md (the PLAN-PROMPTS entry `execute-plan-adapter-route-scope-inversion` carries the operator-confirmed prompt)
Driving force: simplicity, code-quality
Design input: the operator's adapter-necessity ask with its recorded friction witness ("ZCode works without issues and Codex which uses adapter has a lot of hiccups", 2026-10-10); the liveness ledger's route economics (run-manifest-writer rows all incident-no-catch, done-receipts incident, per-task-done-subagent spawn already removed by the closeout-gate demotion program change 9); the two rent-paying guards' live catches (write-manifest-claim-or-foreign 2026-10-07 + 2026-10-08; undisposed-interrupted-refusal 2026-10-08); the registry's codex-only fan-out eligibility with every other runtime deferred
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-execute-plan-adapter-route-scope-inversion-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-execute-plan-adapter-route-scope-inversion.md

## Terms

- The `in-session sequential route`: execute-plan's implementation shape where the parent implements every task itself, in-session, with no implement sub-agent launch: one commit per task, `wip:` checkpoint commits at task boundaries per the standing checkpoint duty, the full Phase 3 review protocol, and the standing landing gates. Its receipt set is exactly: per-task done commits with plan checkbox flips, checkpoint commits, the Phase 3 review records, and the landing-gate evidence (the archive transition per the plans skill lifecycle, the reconcile receipt, and the worktree-closeout proof). The route reaches Phase 4/5 directly and skips the driver's manifest-bound machinery: no staged terminal operation (the Phase 4 archive transition runs on the plans skill's own lifecycle checks instead of the driver gate), no machine manifest (`runtime_state.json`), no runtime adapter, no preflight/claim/reclaim operations, and no adapter lifecycle receipts, capacity witness, or atomic handoff records.
- Worker fan-out: the implementation shape that launches implement sub-agents (single-task, batch, or parallel-group per Step 1.2). This is the shape every adapter obligation binds today and the only shape they bind after this plan.
- The adapter requirement: the registry-selected adapter boundary plus its machinery - adapter profile contract, lifecycle receipts through adapter hooks, the receipt-fed capacity witness, atomic handoffs, the machine manifest as authoritative state, the preflight/claim/reclaim driver operations, and the staged terminal gate. Today it binds execute-plan unconditionally; after this plan it binds worker fan-out only.
- Registry shape eligibility: the runtime inventory's `eligibility` values (eligible/deferred) scope to worker fan-out launches. The in-session sequential route consults no adapter eligibility: any runtime runs it, including every runtime the registry defers for fan-out. The default implementation shape for any execute-plan run is the in-session sequential route; a fan-out selection requires a registry-eligible runtime with a verified adapter, or explicit operator direction.

## Why

The execute-plan run contract has exactly two represented shapes, and neither is the route that keeps landing plans: the adapter-backed contract is formally available only to codex (every other runtime defers with "no verified adapter"), and the Manual mode excludes Phase 3 by definition, so the witnessed route - the parent implementing tasks in-session with the full review protocol and the unchanged landing gates - is represented by neither. The liveness ledger shows the manifest-side machinery is a net cost on its own home route (run-manifest-writer rows are incidents with zero catches; done-receipts records an incident; the per-task done sub-agent spawn was already removed by demotion change 9), while the two guards that do pay rent guard the staging/claim boundary that in-session runs cross too. The operator's ask records the friction directly. The fix inverts the contract's default: the route that works becomes a named, first-class shape with a minimal receipt set, and the adapter machinery keeps binding exactly the shape that needs it - fan-out.

## Gist & Examples

TLDR: one mode paragraph in execute-plan SKILL.md names the `in-session sequential route` as a first-class implementation shape with its minimal receipt set (task done commits, checkpoint commits, Phase 3 records, landing-gate evidence), the adapter-profile and machine-manifest mandates re-scope to worker fan-out, registry eligibility becomes shape-based, the two rent-paying guards and the ledger stay byte-untouched, and the remaining zero-catch driver guards route to the closeout-gate demotion program's continuation as one exec-lane entry at landing - not this plan's lanes - because the witnessed successes need none of that surface (simplicity, code-quality).

Before: a ZCode run of execute-plan formally cannot start - the registry defers it ("no verified adapter") - yet ZCode runs keep landing plans in-session with none of the adapter surface; the contract's "registry-selected runtime adapter is the only host boundary" describes a boundary the successful route never crosses.

After: the same run is the named in-session sequential route: worktree-first, per-task done commits, `wip:` checkpoints at boundaries, full Phase 3, unchanged landing gates - with no adapter, no machine manifest, and no lifecycle-receipt obligations; a codex fan-out run keeps every existing obligation byte-identically.

Edge cases: an operator may direct the fan-out shape only where the registry admits the runtime (verified adapter) or by explicit operator direction; the shape is declared in the run-contract announcement at Step 0 and recorded in the session manifest (default: in-session sequential; never inferred), and re-checked at every Step 1.2 launch against the recorded choice; a run never mixes shapes - batches and parallel groups are fan-out launches, so a run that launches any of them is a fan-out run for the whole contract, and the re-check surfaces the flip at the launch that would cause it; an in-session run's interruption recovery is ordinary session continuity plus its `wip:` checkpoints (the interruption-snapshot and reconcile-before-resume machinery is worker-lifecycle machinery and stays fan-out-scoped); the Manual mode is untouched (it still excludes Phase 3); the budget gate and Step 0.5 readiness gate apply to both shapes unchanged.

## Outcome

The contract-reality inversion closes: the route that keeps landing plans is named and carries a minimal, honest receipt set, and the adapter machinery binds only the fan-out shape whose four witnessed failure classes (stale inventory counting, inherited owner/token across handoffs, log paths as validation proof, unreconciled interruption state) it exists to prevent.

- execute-plan runs without an adapter on any runtime, on the named in-session sequential route, with the same landing gates as today.
- A codex fan-out run keeps every existing adapter obligation byte-identically.
- The registry records shape-based eligibility; the two rent-paying guards and the ledger stay byte-untouched.
- The five zero-catch driver guards leave this plan with one named exec-lane entry and no executed demotion.

Gate delta: one mode paragraph plus scope re-wording in `agents/skills/execute-plan/SKILL.md` (the spans enumerated in Task 1: the contract opening's "only host boundary" sentence, the preflight mandate paragraph, the runtime policy alignment paragraph, the blocked-direct-claim recovery paragraph, the adapter-profile and lifecycle-receipts paragraph, the atomic-handoff paragraph, the terminal-response gate paragraph, the orchestration state table's driver-operation rows, the invocation gate's execute-plan option, the "Do not implement tasks inline" line, the execution hard-gate items "One implement launch per iteration" and "Parent-agent implementation does not satisfy this gate", the anti-pattern table's "Announcement is not execution" row, and the Phase 4 archive-gate sentence; nothing beyond the named spans); one scope arm plus the eligibility sentences and the "Deferred profiles are not eligible for execution." sentence in `agents/skills/execute-plan/runtime-contract.md`; two additive registry items in `projects/.ai-playbook/execute-plan-runtime-inventory.toml` (the `eligibility_scope` key in `[inventory]` plus one deferrals-section comment); one staged-runtime tuple extension in `scripts/runtime_capabilities.py` (`stage_package` gains `plan_shape.py`, repairing the registry suite's one pre-existing error - measured 44 tests OK after the extension); pins added/re-aimed in `scripts/check_maintenance_pins.sh`. The mode paragraph carries one supremacy sentence: any span of the skill that mandates an implement sub-agent launch, a machine manifest, or an adapter boundary without naming an execution shape scopes to worker fan-out, and wherever a mandate names a driver receipt set (the machine manifest, adapter lifecycle receipts), the in-session route substitutes the four-artifact receipt set defined in the Terms. Counted-class admission: this plan adds no gate, validator, fence, refusal class, or schema state field - every receipt the new route owes is an artifact the witnessed runs already produce, so the admission statement names no incident for new machinery because none is added; the change is an enforcement-scope narrowing, and its one ceremony growth is priced here: the shape declaration adds one sentence to the Step 0 run-contract announcement and one re-check line to every Step 1.2 launch (plus the mode paragraph itself), no new machinery.

## Assumptions

- The two rent-paying guards are byte-untouched: `write-manifest-claim-or-foreign` and `undisposed-interrupted-refusal` guard the staging/claim boundary that in-session runs cross too (the done closeout runs there), and their ledger rows stay as landed. Basis: the ledger's own catch rows (2026-10-07, 2026-10-08) and the entry's preserved-guards point.
- The machine manifest and driver stay exactly as landed for fan-out; this plan re-scopes which runs enter that contract, never the driver's internals. The reclaim fences and the `wip:` checkpoint duty (landed 2026-10-10) are preserved byte-identically - the in-session route adopts the `wip:` duty as its own checkpoint receipt. Basis: the entry's scope point (2) and the reclaim-after-terminal-worker and wip-auto-checkpoint landings.
- The five zero-catch incident-bearing driver guards named by the entry (run-manifest-writer compliance legs, done-receipts, plan-readiness, plan-readiness-digest-gate, execution-claim-gateway) route to the closeout-gate demotion program's continuation: the program's own record closed at commit 3a21a297c ("changes 0-9 complete" final landing; EXEC-PROMPTS.md is the pruned post-closure record), so this plan's landing rider creates one fresh EXEC-PROMPTS.md exec-lane entry naming the five guards and the one-gate-per-change rule, and each future demotion lands as its own change with its own ledger row update at its own evidence intake, never inside this plan. Basis: the entry's routing point (5) and the program's closing commit.
- The registry change is additive and the new key is descriptive today: `[inventory]` gains `eligibility_scope = "worker-fan-out"` plus one comment line on the deferrals section stating the scope, `schema_version` stays 1, and existing consumers keep working unchanged - the driver touches the inventory only through shape-agnostic helpers (`canonicalize_runtime_id` and `load_inventory` in scripts/runtime_capabilities.py, no eligibility consumer), `validate_inventory` tolerates unknown `[inventory]` keys, and mechanical fan-out admission stays gated by the `ADAPTER_ENTRYPOINT_MODULES` check in scripts/runtime_capabilities.py. Basis: the registry's own header rule ("capability values belong here only"), the entry's shape-based eligibility point (3), and the driver/validator sources on disk.
- The seed-evidence sibling's 4,096-byte evidence envelope cap is left to its own lane: this plan takes the entry's sanctioned "left separate" disposition - neither widens nor absorbs it, and no task touches any envelope cap. Basis: the entry's explicit carve-out.
- Shape binds per run and is visible: the default is the in-session sequential route, declared at the Step 0 run-contract announcement and recorded in the session manifest, re-checked at every Step 1.2 launch; because the batch and parallel-group options are fan-out launches by construction, the re-check surfaces any shape flip at the launch that would cause it - the mixed-shape run is detectable from the receipts (a fan-out launch's worker claims and receipts are recorded), not assumed away. Basis: the Step 1.2 batch/parallel-group mechanics and the manifest-recording duty in Task 1.
- The battery runs under `python3.14` and the registry suite's baseline red is repaired in-plan: bare `python3` (3.9.6 here) cannot import `tomllib` (imported at `runtime_capabilities.py` module top), so the parse smoke and both suites pin `python3.14`; the registry suite carries exactly one pre-existing error on the freeze tree - `stage_package` stages four runtime scripts while the staged driver imports `plan_shape` - and Task 2's one-line tuple extension is verified to turn it green (44 tests OK, measured at the r2 round). Basis: the r2 targeted round's on-disk runs.

Decision points requiring a grill: none remain (the operator-confirmed entry names the route, the receipt set, the registry change, the preserved guards, the routing disposition, and five rejected alternatives; the shape-selection default is settled by this plan's Terms: in-session sequential is the default, fan-out requires registry eligibility or explicit operator direction, and the declaration site is the Step 0 run-contract announcement).

## Standing constraints

- The two rent-paying guards and `scripts/gate_liveness_ledger.json` are byte-untouched by every task; any task whose diff touches either path is wrong.
- The driver (`scripts/execute_plan_runtime.py`) internals are byte-untouched by every task; this plan re-scopes the skill and registry prose that invokes the contract, never the driver.
- Both prose homes are pinned surfaces: the pins suite stays green at every task landing. All pin additions and all pin re-aims for spans the edits touch land in Task 3 (one owner); Tasks 1-2 never touch the pins script.
- The full battery stays green at every task landing, except the arms whose introducing task has not landed: at Task 1's landing the expected-red set is exactly span checks 3-5 (Task 2's files) and the registry suite's single pre-existing `stage_package` error (repaired in Task 2), measured 0/1/0/0/1 and 44 tests with 1 error on the freeze tree; from Task 2's landing every leg is green. The battery interpreter is `python3.14` (bare `python3` is 3.9.6 without `tomllib` on this host, measured): the parse smoke and both suites invoke it explicitly.
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert in reverse task order - Task 3's pin additions freeze the post-edit spans, so a revert of Task 1 or 2 reverts the corresponding Task 3 pins in the same operation (or first); the change is prose scope-narrowing plus additive registry items, so the reverse-order revert restores today's text exactly.

## Evaluation Criteria

**Quality dimensions:**
- correctness: after landing, the contract names exactly two implementation shapes (worker fan-out, in-session sequential), binds the adapter requirement to fan-out only, reaches the landing gates directly on the in-session route (no driver staged terminal), and the in-session route's receipt set is exactly the four named artifacts - no machine manifest obligation leaks onto the route.
- regression safety: the pins suite stays green at every landing; both test suites are green from Task 2's landing on (Task 1 records the measured pre-repair baseline with no regression beyond it); every pinned span intact or re-aimed beside provenance (in Task 3); the two guards' ledger rows byte-identical before and after.
- scope discipline: no driver edits, no ledger edits, no new scripts; the routing disposition for the five zero-catch guards is recorded (the landing rider's exec-lane entry), not executed.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green, including the untouched proofs.

**Ship when:**
- A fan-out-deferred runtime (zcode) runs execute-plan on the in-session sequential route as a named, first-class shape - no adapter, no machine manifest - with the full Phase 3 protocol and unchanged landing gates, and a codex fan-out run keeps every existing obligation byte-identically; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the spans enumerated in Task 1 and the mode paragraph; nothing beyond the named spans)
- `agents/skills/execute-plan/runtime-contract.md` (the scope arm beside the adapter profile contract, the runtime-selection eligibility sentences, and the "Deferred profiles are not eligible for execution." sentence; nothing else in the file)
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml` (the `[inventory]` eligibility_scope key, the deferrals-section scope comment; nothing else in the file)
- `scripts/check_maintenance_pins.sh` (the must-carry witness pins beside provenance in Task 3; re-aims for any span the edits touch, Task 3 only)
- `scripts/runtime_capabilities.py` (the `stage_package` staged-runtime tuple gains `plan_shape.py`; nothing else in the file)

**Tests:**
- `scripts/test_runtime_capabilities.py` (the registry's owning suite; green from Task 2's `stage_package` repair in `scripts/runtime_capabilities.py`, no suite-file edits planned; suite-file edits only if the additive keys must keep its fixtures passing, and the executor verifies first and leaves no edits when the fixture set does not touch these keys)

**Docs (untouched by the tasks; flipped or added by the landing rider):**
- `docs/history/backlog/2026-10-10-execute-plan-adapter-route-scope-inversion.md`
- `docs/history/backlog/PLAN-PROMPTS.md` (untouched by the tasks; the landing rider prunes the entry with the prune receipt)
- `docs/history/backlog/EXEC-PROMPTS.md` (untouched by the tasks; the landing rider adds the five-guard continuation entry here; the demotion program's own record is its closing commit 3a21a297c)

**Read-only (referenced, never edited):**
- `scripts/gate_liveness_ledger.json` (the route economics of record; byte-untouched)
- `docs/history/plans/completed/2026-09-22-agent-aware-execute-plan-skill-contract.md` (the adapter origin plan whose four witnessed failure classes the fan-out scope preserves)
- `docs/history/backlog/2026-10-10-execute-plan-worker-terminal-reconciliation.md` and `docs/history/backlog/2026-10-09-execute-plan-seed-evidence-criteria-over-limit.md` (the cluster rows)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-execute-plan-adapter-route-scope-inversion.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## execute-plan-adapter-route-scope-inversion` (frozen under docs/tmp/authoring-claims/2026-10-10-execute-plan-adapter-route-scope-inversion.md; pruned by the landing rider with the prune receipt)
- Continuation rider: the landing rider adds the EXEC-PROMPTS.md exec-lane entry naming the five zero-catch guards and the one-gate-per-change rule (recorded, never executed by this plan)

## Validation Commands

**Production (per-home occurrence counts; all five read RED on the freeze tree, measured 0/1/0/0/1 - checks 1-2 go green at Task 1, checks 3-5 at Task 2):**
```bash
grep -oF "in-session sequential route" agents/skills/execute-plan/SKILL.md | wc -l   # expect >=3 (mode paragraph, gate option, receipt-set reference)
grep -oF "worker fan-out" agents/skills/execute-plan/SKILL.md | wc -l   # expect >=4 (each scoped span names the shape it binds; measures 1 today)
grep -oF "eligibility_scope" projects/.ai-playbook/execute-plan-runtime-inventory.toml | wc -l   # expect 1
grep -oF "in-session sequential route" agents/skills/execute-plan/runtime-contract.md | wc -l   # expect >=1 (the scope arm)
grep -cF "Deferred profiles are not eligible for execution." agents/skills/execute-plan/runtime-contract.md   # expect 0 after Task 2 (re-worded to the shape-scoped sentence); grep -c exits 1 at count 0 - the printed count is the witness, record both
```

**Untouched proofs (every task landing; anchored to the freeze commit, worktree-inclusive, exit-code semantics - not diffstat counts):**
```bash
git diff --quiet 003751046 -- scripts/gate_liveness_ledger.json scripts/execute_plan_runtime.py && echo UNTOUCHED   # expect UNTOUCHED (exit 0)
```

**Tests (every task landing; interpreter `python3.14` - bare `python3` is 3.9.6 without `tomllib` here, measured):**
```bash
bash scripts/check_maintenance_pins.sh   # exit 0
python3.14 -c "import tomllib; tomllib.load(open('projects/.ai-playbook/execute-plan-runtime-inventory.toml','rb'))"   # exit 0 (the registry parses)
python3.14 scripts/test_runtime_capabilities.py   # exit 0 (the registry's owning suite; green from Task 2's stage_package repair)
python3.14 scripts/test_execute_plan_runtime.py   # exit 0 (the byte-untouched driver's suite; green on the freeze tree under python3.14, measured)
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/runtime-contract.md   # exit 0
bash scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: the in-session sequential route in the execute-plan skill

Files:
- agents/skills/execute-plan/SKILL.md

- [ ] Add the mode paragraph to the Runtime-neutral execution contract region defining the `in-session sequential route` per the Terms (parent-implemented, one commit per task, `wip:` checkpoints at task boundaries, full Phase 3, direct landing gates, the four-artifact receipt set, no machine manifest/adapter/lifecycle obligations), including the shape-declaration duty (declared at the Step 0 run-contract announcement, recorded in the session manifest, default in-session sequential, re-checked at every Step 1.2 launch) and the one supremacy sentence per the Gate delta. Re-scope, to worker fan-out with the in-session route carved out or superseded in each, exactly these spans: (a) the contract opening's "the registry-selected runtime adapter is the only host boundary" sentence; (b) the preflight mandate paragraph; (c) the runtime policy alignment paragraph; (d) the blocked-direct-claim recovery paragraph; (e) the adapter-profile and lifecycle-receipts paragraph; (f) the atomic-handoff paragraph; (g) the terminal-response gate paragraph; (h) the orchestration state table's driver-operation rows (the `recovering` and `terminal` rows; the `waiting-for-capacity` row's pinned claim-less derivation stays byte-identical, and any pinned needle an edit would move is re-aimed in Task 3); (i) the invocation gate's execute-plan option (both shapes named, selection declared); (j) the "Do not implement tasks inline unless a sub-agent fails and you must recover." line; (k) the execution hard-gate items carrying "One implement launch per iteration" and "Parent-agent implementation does not satisfy this gate."; (l) the anti-pattern table's "Announcement is not execution" row; (m) the Phase 4 archive-gate sentence (the in-session route archives per the plans skill lifecycle without the driver's staged terminal operation). Each span states its fan-out scope or defers to the mode paragraph; nothing outside the named spans changes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the span checks, the untouched proof, and the full battery from `## Validation Commands`; record each exit code in the session log; fix any red check attributable to this task's edits before reporting the task done. Expected red at this landing, none of them a Task 1 defect: span checks 3-5 (their files land in Task 2) and the registry suite's single pre-existing `stage_package` error (repaired in Task 2). [class: REPOSITORY_TEST]

### Task 2: the runtime-contract scope arm and the registry shape eligibility

Files:
- agents/skills/execute-plan/runtime-contract.md
- projects/.ai-playbook/execute-plan-runtime-inventory.toml
- scripts/runtime_capabilities.py

- [ ] Add the scope arm to runtime-contract.md beside the adapter profile contract: the adapter requirement (profiles, lifecycle receipts, capacity witness, atomic handoffs, machine manifest, preflight/claim/reclaim, staged terminal gate) binds worker fan-out launches; the in-session sequential route owes its own four-artifact receipt set and consults no adapter eligibility. Scope the runtime-selection eligibility sentences and the "Deferred profiles are not eligible for execution." sentence to fan-out the same way. Add the `[inventory]` `eligibility_scope = "worker-fan-out"` key and the deferrals-section comment (deferral values scope to fan-out; the in-session route consults none; the key is descriptive today - no driver consumer), leaving `schema_version` and every per-runtime value unchanged. Extend `stage_package`'s staged-runtime tuple in `scripts/runtime_capabilities.py` with `plan_shape.py` (the staged driver imports `plan_shape` at module top; without the entry every generated fixture probe of the staged driver dies on ModuleNotFoundError - the registry suite's one pre-existing error; the four existing entries stay byte-identical). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full battery from `## Validation Commands`; record each exit code in the session log; fix any red check attributable to this task's edits before reporting the task done. At this landing the whole battery is green: this task's `stage_package` repair turns the registry suite green and the registry edit turns span checks 3-5 green. [class: REPOSITORY_TEST]

### Task 3: the witness pins and the battery

Files:
- scripts/check_maintenance_pins.sh

- [ ] Add the must-carry pins beside their provenance, per file, using the suite's occurrence-count idiom (`grep -oF '<needle>' <file> | wc -l`) on operative spans rather than bare phrases any future cross-reference would satisfy: in execute-plan SKILL.md the mode paragraph's defining sentence (pinned exactly once) and the four-artifact receipt-set sentence; in runtime-contract.md the scope arm's binding sentence ("binds worker fan-out launches", exactly 1); in the registry the `eligibility_scope` key literal (exactly 1). Any existing pin whose span the two prose edits touch is re-aimed beside provenance in this task - Task 3 owns every pin re-aim of this plan. [class: REPOSITORY_TEST]
- [ ] Run the full battery under `python3.14` (the pins suite, both test suites, the registry parse smoke, both em-dash checks, the untouched proofs, the hygiene scan), record each exit code in the session log, and fix any red check before reporting the task done. [class: REPOSITORY_TEST]
