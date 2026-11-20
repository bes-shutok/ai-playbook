# Plan: Dispatch-time claim re-check for execution worker launches

Backlog origin: docs/history/backlog/2026-11-10-duplicate-exec-carrier-same-task.md
Driving force: efficiency + token-usage
Plan review record: the staging series .ai-playbook/reviews/2026-11-10-plan-review-exec-dispatch-claim-recheck-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 2.0h total, largest task 1.0h
Executed: yes (4366322e9b447e7cd44d3b81a7904d6514f6cc17)
Authoring claim: exec-dispatch-claim-recheck.md (session sess_92ac2358-ae43-40df-b32b-bbda111a66c6)

## Terms

- Dispatch-time claim re-check: the pre-launch check a carrier runs immediately before launching an execution worker, classifying the target's execution-claim state and refusing when a fresh foreign claim holds the target (the fresh-foreign class), deferring on tool errors and on gateway skew.
- Claim-presence probe: the read-only `probe` mode of `scripts/execution_claim.sh`; it takes the same plan-path operand the gateway's other modes take and derives the slug through the existing derive_slug substrate; it classifies the target's claim evidence through the same script-local freshness substrate the take path uses (the same FRESHNESS_SECS constant and claim_field helpers, no second boundary constant) and never creates, refreshes, or deletes a claim.
- Fresh claim: a claim file whose `updated:` line is fresher than one cadence period (2 hours), the same freshness rule the lane guards' discovery arms read.
- Stale claim: a claim file at or past one cadence period; occupies nothing and never blocks at this boundary. A stale foreign claim on an unoccupied branch is takeover territory owned by the take path's existing contract; a run's own stale claim is Phase 0's refresh duty, not this fence's.
- Candidate continuation: when a dispatch refuses in a surface that holds an ordered candidate list, the selection continues down that list with the refusal recorded; an execute-plan single-plan run holds no candidate list and stops with the refusal recorded, a guard-fire stop, not a wait.
- Machinery admission: the incident, expected catch frequency, false-positive cost, and review date a blocking addition must name (repository guidelines, Machinery admission protocol).

## Why

On 2026-11-09 at 22:15 and 22:48 two execution carriers dispatched Task 1 of the hook-timeout-recurrence-diagnostic plan into the same worktree; the later worker detected the overlap mid-flight and burned 18 minutes and roughly 3.3M subagent tokens re-verifying completed work. What the witness artifacts actually record, re-derived: the origin row records no claim state at either dispatch; the take-side contracts prove the second dispatch did not take into a foreign-occupied worktree (take refuses any target branch held by an existing worktree, including the absent-claim case, and adoption arms make the registered worktree the run's own), and the same incident's sibling row records a take refused at the conversion scan with the operator reconciling a continuation on the preserved claim (the row records the refusal, the claim preservation, and the reconciliation; the second-dispatch identification is the derivation clause's own work). The 22:48 dispatch therefore ran under its own preserved claim and worktree: a same-lineage duplicate that no claim-state classification distinguishes from a legitimate resume. That witnessed shape is this arm's founding harm evidence, in the same relation to this arm as the gateway's founding 2026-10-07 incident (duplicate execution, about 130 lane-minutes) is to the take refusal wired the same day: the harm is witnessed, the arm fences the reachable window of the class, and the residual is named. The reachable window this arm fences: a dispatch whose launch boundary observes a fresh foreign claim on the target, which is exactly the racing-peer drift window (a peer carrier takes the target between this surface's pick and its launch or create). The same-lineage duplicate residual stays fenced by Phase 0 take, the takeover contract's liveness probe, the wake-queue sibling layer, and the worker-side parallel-landing detection, which stays unchanged as the backstop.

## Gist & Examples

TLDR: execution worker launches gain a dispatch-time claim re-check, a read-only probe plus a refuse clause bound at the in-session launch (refusing at the idle and execution-lane fallback legs) and advisory at the clocked legs of the maintenance dispatch ladder, so an overlapping carrier is stopped at dispatch instead of at mid-flight worker detection (efficiency + token-usage).

**Before (today):** At 22:15 and 22:48 on 2026-11-09 two carriers each dispatched Task 1 of the hook-timeout-recurrence-diagnostic plan into the same worktree. Each dispatch passed its own claim and worktree take, launched its worker, and the overlap survived every fence until the later worker happened to read sources proving a parallel session had completed the task; it switched to verify-and-fix and spent 18 minutes and roughly 3.3M subagent tokens re-verifying completed work.

**After (this plan):** The same racing shape is fenced at the next reachable boundary: before any worker launch (or before a ladder dispatch create), the carrier runs the claim-presence probe against the target. The probe reads the target's claim evidence in the primary checkout, the same file and freshness rule the pick-time guards read. A fresh foreign claim refuses the launch: no worker starts, the refusal is recorded with the foreign session id, its updated stamp, and the occupying-worktree evidence, and the surface continues down its candidate list or stops with the record. Every non-refusing classification (no claim, the run's own claim fresh or stale) passes and is recorded. The overlap window that is reachable at dispatch is caught before any worker capacity is spent.

Edge cases: an absent claim, the run's own fresh claim, and any stale claim never block (freshness and session decide; a run whose own claim went stale owes Phase 0 its refresh, and a stale foreign claim on an unoccupied branch is the take path's takeover territory); a probe that cannot decide is a tool error and defers the dispatch, never reading as clear; an unknown probe mode from a stale consumer-side gateway copy (version skew) also defers with no launch started, recorded as gateway-skew distinct from the fresh-foreign refusal record with the required capability named, a stale-copy fleet deferring loudly until the scripts sync that Ship-when leaves unordered (the accepted consequence); the probe resolves without creating the claims directory when it does not exist; a claim read that fails parsing re-reads once before reporting a tool error; a false pass residual is named: a claim state the fence passes (own, stale, absent) rides to the unchanged worker-side detection, and a refusal record carries the same user-directed override-route pointer the take refusal carries so an operator can recover a dead-but-fresh false positive.

## Outcome

An execution worker launch can no longer proceed blind into a target a different live session freshly claimed: the dispatch boundary itself verifies who holds the target.

- A dispatch racing a peer carrier that freshly claimed the target is refused at the launch boundary before worker capacity is spent; list surfaces continue down their candidate lists and single-plan runs stop with the record.
- The probe classifies claim state through the same freshness substrate the take path uses, so dispatch-time and take-time cannot disagree about the classification.
- The maintenance Child dispatch ladder carries the same check in its two-posture form: refusing at the legs with near-zero create-to-fire distance (the idle leg and the execution-lane fallback legs), advisory reordering at the clocked legs (the launchd clocked-order chain and one-shot children), whose fire-time protection remains the child's own Phase 0 take with the Step 1.2 clause as backstop.
- The machinery registry's existing `script:execution_claim.sh` entry carries the check's admission fields, the review date, and removal criteria, and the guard ledger carries the 2026-11-09 harm row, keeping the addition priced and reviewable.

Gate delta: the dispatch-time claim re-check lands as a new arm of the existing execution-claim-gateway guard, not a standalone gate: the guard already refuses duplicate starts at take (its ledger notes name the fresh-foreign refusal wired 2026-10-07), the arm extends the same refusal to the launch boundary, and the guard ledger gains the arm's founding harm row (the 2026-11-09 overlap, 18 minutes plus roughly 3.3M tokens, the same duplicate-execution class as the guard's founding 2026-10-07 incident of about 130 lane-minutes) in the same change. No gate, fence, protocol layer, or schema field is removed or simplified; the take fences and the worker-side backstop stay unchanged. Net blocker growth is explicitly approved by the operator: direction "Refusing, family arm (Recommended)", answered in the authoring session sess_92ac2358-ae43-40df-b32b-bbda111a66c6 on 2026-11-10, standing as the admission protocol's explicit net-growth approval after the witnessed harm of this class. Pricing witness, the frozen PLAN-PROMPTS entry's pre-registered Machinery admission quoted as written for its verbatim fields (expected catch frequency and false-positive cost; the incident field is paraphrased and the review date concretizes the frozen relative date) (incident: the witnessed 2026-11-09 overlap recorded in the origin row; expected catch frequency: "every dispatch racing a peer carrier for the same task or worktree"; false-positive cost: "one claim-presence probe per dispatch; a refused dispatch re-routes through the existing candidate walk"; review date: one quarter after landing, 2027-02-10), with the recorded deltas this arm's folded contract adds: the reachable refusal window is the pick-to-create drift on list surfaces plus the launch-boundary verification in adoption and skip geometries; the single-plan guard-fire stop supersedes the frozen reroute wording where no candidate list exists, admitted under the recorded operator direction; and the witnessed same-lineage duplicate shape is the named accepted residual fenced by Phase 0 take, the takeover contract's liveness probe, and the worker-side backstop. Guard liveness ledger context at authoring time, re-derived from scripts/gate_liveness_ledger.json: the execution-claim-gateway guard holds the 2026-10-07 founding incident row beside its catch and override rows; the claim-or-foreign family (four catches across its three members) is done-sweep staging machinery unrelated to execution claims, and its figures are not this arm's pricing witness.

## Assumptions

- assume the probe reads the same claim evidence pick time reads (the execution claim file under the primary checkout, 2h freshness cadence) rather than new lock state; basis: the origin row's Expected wording ("the same probe pick time uses") and the guards' G1e freshness rule
- assume the frozen entry's "Phase 0 dispatch step" resolves to execute-plan Step 1.2, the per-task worker-launch boundary; Phase 0 owns only the run-level take, and the launch-boundary re-check runs per launch including resumes; basis: Step 1.2 is the launch-implement-worker step per the execute-plan gate table and procedure headings
- assume refuse resolves as a guard-fire stop: no worker launch, a typed manifest record naming the probe outcome class with the foreign session id and updated stamp and occupying-worktree evidence where the claim carried them; a surface holding a candidate list continues down its list; never a wait and never new recovery machinery; basis: the entry's machinery admission false-positive cost line and the queue-drain precedent that a fresh foreign claim on the same plan is a guard-fire stop
- assume the probe's session operand is this run's claim-holding session id read from the run's claim or manifest record (a ladder leg uses the deciding parent's own id), never a loosely supplied value; basis: the dead-run conversion arm's exact-ID validation precedent and the gateway's required --session in every mode
- assume the probe mutates nothing; basis: the take and worktree take fences already own every mutation; the launch boundary needs classification only; the absent-directory case (the probe resolves without creating the claims directory) is witnessed in the mutation test, and the validation runs never invoke the registry's mutating scaffold form
- assume a probe tool error or unresolvable outcome defers the dispatch rather than reading as clear, and an unknown-mode usage refusal from a pre-probe gateway copy also defers with no launch started (recorded gateway-skew, the missing capability named); basis: the outcome contract's conservatism, the overlap cost asymmetry, and execute-plan Step 0.4's repo-local-first resolution
- assume coordination not absorption with the scheduler wake-queue row; basis: the origin row's Cluster line and the entry's Stage 1 roster split

Decision points requiring a grill: blocking posture: RESOLVED 2026-11-10, operator answer "Refusing, family arm (Recommended)" (the explicit net-growth approval after the witnessed 2026-11-09 overlap), recorded in the authoring session sess_92ac2358-ae43-40df-b32b-bbda111a66c6; the check lands as an arm of the execution-claim-gateway guard with refusal teeth per that direction; source: repository guidelines Machinery admission protocol plus the operator's session answer, 2026-11-10, affected: Outcome Gate delta and Task 4

## Standing constraints

- Focused suites only: this repository's `test_suite_policy` is `focused-never-full`; validation runs the named focused suites, never a full-suite run.
- Skill text edits keep the surrounding style: no em-dashes in added lines, no absolute filesystem paths, no personal or machine-specific data.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe's freshness classification uses the same script-local substrate as the take path (one FRESHNESS_SECS constant, one boundary: 7199s reads fresh, exactly 7200s reads stale)
- fail-safety: the probe's outcome-to-exit map is total (passes exit 0; the refusal exits 1 OUTCOME: fail with evidence on stderr; tool errors exit 3 OUTCOME: tool_error on stdout; the unknown-mode usage refusal exits 3 with its usage line on stderr) and every non-pass outcome defers or refuses per its class, recorded distinguishable from the fresh-foreign refusal record; no surface can read any of them as "target free"
- maintainability: the gateway owns the freshness classification and the numeric cadence home; the probe consumes that substrate; both mirror texts reference the probe rather than restating parsing rules or restating the figure
- test coverage: the probe suite covers absent, fresh-own, fresh-foreign (refusal), stale, both freshness boundary twins with their seeded sessions, the no-directory mutation carve-out, the torn-read re-read seam, malformed claim bytes, and the unknown-mode usage discriminator

**Done when:**
- `scripts/execution_claim.sh probe` classifies a real claim file correctly for all four claim classes with the pinned exit map, verified by fresh command output
- execute-plan Step 1.2 carries the pre-launch re-check clause naming the probe and the fresh-foreign refusal; the maintenance Child dispatch ladder carries the two-posture mirror bullet
- the machinery registry's `script:execution_claim.sh` entry carries the admission fields, the review date, and removal criteria, and the guard ledger carries the 2026-11-09 harm row
- the focused suite for the claim gateway passes with the new probe tests included

**Ship when:**
- Consumer repositories running the shared skills pick up the amended skill text at their next skills sync (external sync; no checklist item; until the synced scripts arrive, consumer lanes defer on gateway-skew per the recorded consequence).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execution_claim.sh` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/maintenance/zcode.md` (Task 3)
- `scripts/machinery_registry.json` and `scripts/gate_liveness_ledger.json` (Task 4)

**Tests:**
- `scripts/test_execution_claim.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/decisions.md`; reason: the occupied-lane chaining duty owns post-deferral retry arming, a different boundary than pre-launch verification
- `agents/skills/maintenance/guards.md`; reason: the G1e discovery arm's freshness rule is the read-only surface this plan reuses, not a surface it changes
- `docs/history/backlog/EXEC-PROMPTS.md` and the scheduler wake-queue surface; reason: the sibling row 2026-11-09-codex-quota-wake-cross-thread-duplicate-target owns that layer (clustered, not absorbed)

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execution_claim.py -q
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
python3 scripts/gate_liveness_ledger.py show
python3 scripts/skill_text_budget.py --check
```

Baseline scoping (recorded pre-existing reds, re-verified as the same failures at execution, never new failures): the pins suite exits 1 on its staleness pin alone (STALE rows backlog-completed-dir-regrowth and test-suite-runtime-residual-optimization-path, pre-existing), and the early exit leaves the pins after that checkpoint unexecuted, so Task 4 witnesses the pinned literals of the two edited files directly; `machinery_inventory.py --check` exits 1 on exactly the named pre-existing regrowth row (`scripts/profile_skill_gate_consult.py`), which is the recorded expectation (any other failure line is a new failure); `skill_text_budget.py --check` is advisory (breach lines never move the exit) and currently reports zcode.md over cap, which Task 3's growth-payment constraint must not grow; no validation run invokes the registry's mutating scaffold form.

### Task 1: Claim-presence probe mode in the execution-claim gateway

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execution_claim.sh`
- `scripts/test_execution_claim.py`

Primary class anchors:
- `Probe` in `scripts/execution_claim.sh`

- [x] The probe classifies claim state through the take path's freshness substrate, taking the plan-path operand and deriving the slug through the existing derive_slug substrate; the passing classes pin: `claim: absent` exits 0 `OUTCOME: pass`; `claim: fresh-own session=<own-id> updated=<stamp>` exits 0 `OUTCOME: pass`; `claim: stale session=<id> updated=<stamp>` exits 0 `OUTCOME: pass` [class: IMPLEMENTATION_REQUIRED]
- [x] The refusing and error classes pin the rest of the outcome-to-exit map: `claim: fresh-foreign session=<id> updated=<stamp>` exits 1 `OUTCOME: fail` (the modeled refusal path, classification and evidence lines on stderr); malformed claim bytes that still fail after the torn-read re-read exit 3 `OUTCOME: tool_error` on stdout [class: IMPLEMENTATION_REQUIRED]
- [x] The output rule is single-sourced: every classification line carries `session=<id>` for the claim's holder (the caller's own id on fresh-own lines) and `updated=<stamp>` whenever a claim file exists; the fresh-foreign refusal line additionally carries the occupying-worktree evidence `occupying-worktree=<path>` when the claim's branch maps to a registered worktree via the gateway's occupying-worktree naming (evidence in the refusal record, not a fence axis) [class: IMPLEMENTATION_REQUIRED]
- [x] The refusal class is exactly one: a fresh foreign claim; the refusal record mirrors the take refusal's user-directed override-route pointer so an operator can recover a false positive [class: IMPLEMENTATION_REQUIRED]
- [x] The freshness boundary is witnessed at both twins with their seeded sessions, using the existing idiom with its full call shape (`_seed_claim(session, age, plan_path=..., now=seed_now, branch=...)` plus the `_date_shim`/`path_prepend` fixture pattern): at 7199s an own claim reads `claim: fresh-own` and passes; at 7199s a foreign claim reads `claim: fresh-foreign` and refuses [class: REPOSITORY_TEST]
- [x] The stale side of the boundary: at exactly 7200s a foreign claim reads `claim: stale` and passes (never blocks), citing the in-repo pattern twins test_freshness_boundary_7199s_refuses and test_freshness_boundary_7200s_takes_over in scripts/test_execution_claim.py [class: REPOSITORY_TEST]
- [x] The probe mutates nothing: given any probe run over an existing claim, the claim file bytes are unchanged after the run; and given an absent claim and no claims directory, the run exits 0 with `claim: absent` and creates no `docs/tmp/execution-claims/` directory (the mkdir carve-out is witnessed, not assumed) [class: REPOSITORY_TEST]
- [x] A claim file read that fails parsing re-reads once before reporting the tool error (the torn-read rule, since the create path writes directly under noclobber; the re-read witness uses the existing PATH-shim idiom on the claim_field read path) [class: REPOSITORY_TEST]
- [x] The unknown-mode usage refusal is pinned as the gateway-skew discriminator: an unknown mode exits 3 with the `unknown mode:` usage line on stderr (the existing usage-violation test's contract), which Task 2's skew matcher keys on, distinct from the tool-error path's stdout OUTCOME line [class: REPOSITORY_TEST]
- [x] Run the focused suite before writing the probe, expect RED on the new cases; run the focused suite after, expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: add read-only claim-presence probe to execution claim gateway` [class: REPOSITORY_TEST]

### Task 2: Pre-launch re-check clause in execute-plan Step 1.2

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Step 1.2 carries a dispatch-time claim re-check paragraph placed before the worker-prompt composition: the parent runs the probe (addressed at the primary checkout, this run's claim-holding session id read from the run's claim or manifest record) before launching [class: IMPLEMENTATION_REQUIRED]
- [x] Given a fresh foreign claim on the target, the clause expects no worker launch and a typed manifest record naming the probe outcome class with the foreign session id, its `updated:` stamp, and the occupying-worktree evidence where carried [class: IMPLEMENTATION_REQUIRED]
- [x] The refusal is exempt from the bounded-retry budget and from the Step 1.2 inline fallback; a single-plan run stops with the record (a guard-fire stop, not a wait) [class: IMPLEMENTATION_REQUIRED]
- [x] The clause names the conservative outcome rules: given a probe tool error or an unresolvable outcome, expects the launch deferred, never read as target-free; and given an unknown probe mode from a pre-probe gateway copy, expects a gateway-skew deferral with no launch started, the required capability named in the record, the lane's protection posture remaining the unchanged worker-side backstop until the synced scripts arrive [class: IMPLEMENTATION_REQUIRED]
- [x] The clause names the backstop explicitly: worker-side parallel-landing detection stays unchanged as the documented backstop [class: IMPLEMENTATION_REQUIRED]
- [x] All other steps and paragraphs of `agents/skills/execute-plan/SKILL.md` are byte-unchanged; the diff touches only the Step 1.2 region; verification pairs two literal grep needles, `execution_claim.sh probe` and the conservative-outcome sentence fragment `never read as target-free`, RED before the edit and GREEN after, with a diff-scope witness (`git diff --stat` names exactly the one file and every diff hunk header falls inside the Step 1.2 region) [class: REPOSITORY_TEST]
- [x] Commit: `feat: bind dispatch-time claim re-check to execute-plan worker launches` [class: REPOSITORY_TEST]

### Task 3: Mirror bullet in the maintenance Child dispatch ladder

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`

- [x] The Child dispatch ladder carries one mirror bullet beside the dispatch bullets in its two-posture form, scoped onto the ladder's named surfaces: at the legs with near-zero create-to-fire distance (the idle leg and the execution-lane fallback legs) the dispatch runs the same pre-launch re-check with refusal teeth (the execute-plan Step 1.2 clause is the procedure of record, referenced, not restated) [class: IMPLEMENTATION_REQUIRED]
- [x] At the clocked legs (the launchd clocked-order chain and one-shot children) the probe runs at create time as advisory reordering only, the candidate stays eligible at the next window, and fire-time protection remains the child's own Phase 0 take with the Step 1.2 clause as backstop [class: IMPLEMENTATION_REQUIRED]
- [x] Given a fresh foreign claim on the candidate at a refusing leg, the selection continues down its ordered candidate list with the refusal recorded, and a single-plan leg stops with the record [class: IMPLEMENTATION_REQUIRED]
- [x] The bullet names the conservative outcome rules and the backstop reference in one line each, matching Task 2's semantics [class: IMPLEMENTATION_REQUIRED]
- [x] Growth payment: the mirror bullet lands only together with equivalent deleted bytes in `zcode.md` in the same commit (candidates: a condensed superseded witness passage or retired-leg narration elsewhere in the file), the bullet stays reference-not-restate, and the commit message records the byte delta; `python3 scripts/skill_text_budget.py --check` after the edit reports no new breach growth [class: REPOSITORY_TEST]
- [x] All other bullets of the ladder and the rest of `agents/skills/maintenance/zcode.md` are byte-unchanged apart from the growth-payment deletions; verification pairs the literal grep needle `execution_claim.sh probe`, RED before the edit and GREEN after, with a diff-scope witness (the diff names exactly `agents/skills/maintenance/zcode.md` and its hunks are confined to the ladder region plus the growth-payment deletion regions) [class: REPOSITORY_TEST]
- [x] Commit: `feat: mirror dispatch-time claim re-check in Child dispatch ladder` [class: REPOSITORY_TEST]

### Task 4: Machinery registry arm admission and validation runs

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`
- `scripts/gate_liveness_ledger.json`

- [x] The registry's existing `script:execution_claim.sh` entry is amended (no new row): its note gains the dispatch-time claim re-check admission fields, the single home of the arm's admission [class: IMPLEMENTATION_REQUIRED]
- [x] The admission fields name the incident (the witnessed 2026-11-09 overlap, evidence re-pointed to the `docs/history/plans/completed/` twin this plan's completion pass creates) and the review date 2027-02-10 with the removal criteria (demote the arm to warning-only at review if true catches are zero and false positives dominate) [class: IMPLEMENTATION_REQUIRED]
- [x] The admission fields name the expected catch (every dispatch racing a peer carrier for the same task or worktree, reachable as the pick-to-create drift on list surfaces and the launch-boundary verification in adoption and skip geometries) and the false-positive cost (one probe per dispatch, a refusal re-routing through the existing candidate walk on list surfaces or stopping single-plan runs under the recorded operator direction) [class: IMPLEMENTATION_REQUIRED]
- [x] The guard ledger's `execution-claim-gateway` guard gains the arm's founding harm row, kept minimal and cross-referenced to the registry admission: kind incident, dated 2026-11-09, about 18 minutes, origin evidence re-pointed to the completed plan twin, one-line note naming the duplicate-execution class [class: IMPLEMENTATION_REQUIRED]
- [x] The registry and the ledger parse and round-trip through their own loaders, verified by fresh command output: `gate_liveness_ledger.py show` exits 0, and `machinery_inventory.py --check` exits 1 with exactly the named pre-existing regrowth row and no other failure line (the recorded expectation; any other failure is a new failure) [class: REPOSITORY_TEST]
- [x] The pins suite's masked tail is witnessed directly: the pinned literal search strings `scripts/check_maintenance_pins.sh` defines for `agents/skills/execute-plan/SKILL.md` and `agents/skills/maintenance/zcode.md` are grepped against the two edited files before and after Tasks 2 and 3, expecting identical match counts (the early-exit staleness red leaves these pins unexecuted under the standing red) [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block within the recorded baseline scoping: the focused claim suite, the hygiene scan, the pins suite (staleness red re-verified unchanged, masked tail witnessed per the bullet above), the registry and ledger loaders per their recorded expectations, and the budget check reporting no new breach growth [class: REPOSITORY_TEST]
- [x] Commit: `feat: register dispatch-time claim re-check machinery admission` [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-10-duplicate-exec-carrier-same-task.md`: deleted in this completion pass through the fold-and-delete disposition; the execution witness is this archived twin's `Executed: yes (4366322e9b447e7cd44d3b81a7904d6514f6cc17)` header field.
