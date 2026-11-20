# Plan: maintenance indefinite-operation stop-gap closures

Backlog origins (scope of record):
- docs/history/backlog/2026-11-12-admission-consult-blocks-disjoint-dispatches-on-authoring-claims.md
- docs/history/backlog/2026-11-12-queued-execution-aging-bound-fires-on-guard-blocked-piles.md
- docs/history/backlog/2026-11-12-bookkeeping-class-g2-alert-self-clear.md
- docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md
- docs/history/backlog/2026-11-12-session-mint-approval-gated-child-posture-gap.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-maintenance-indefinite-operation-stop-gaps[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 3.5h total, largest task 1.75h
Executed: yes (6962083425789cbdc89af71a55a9a8bbb6861f8d)
Authoring claim: maintenance-indefinite-operation-stop-gaps.md (session sess_7b19dc51-0e25-403f-a413-65c4fce59330)

## Terms

- landing gate: the target-disjointness admission consult a deciding turn runs before dispatching a child.
- outstanding run: a recorded or claim-live run another session owns, tested for overlap against the candidate's owned paths.
- source-less run: an outstanding run with no done-setup manifest; the consult's conservative case today.
- derived admission record: a JSON record the deciding turn writes from a live authoring claim, whose `owned_paths` name the surfaces the authoring run will predictably edit.
- aging bound: the survey rule that fires `turn_error: queued-execution-starved` when a queued_execution entry survives three consecutive surveys without dispatch.
- sanctioned hold: a recorded must-dispatch exemption reason in a survey turn's decision record; the aging bound's carve-out reads the survey's recorded hold vocabulary as the closed set at its source (the must-dispatch exemption enumeration in decisions.md D1), never a plan-pinned subset.
- bookkeeping-class alert: a G2 alert whose tripping reason is a bookkeeping streak, not repeated real child failure.
- missed fire: a recorded carrier fire time that passed without the automation's `lastRunAt` advancing past it.
- carrier-liveness operation: the new read-only `execute_plan_runtime.py` operation that classifies a missed fire from the scheduler state file and the runtime store.
- session-minted child: a child session created through the runtime's session-creation primitive; on this runtime it starts approval-gated (each mutating call requests operator access) because the primitive exposes no posture parameter.

## Why

The loop parked itself for 26 hours on 2026-11-11/12 while quota read abundant and seven certified plans stood dispatchable. D-18 already orders indefinite operation; five machinery gaps defeat it, and the operator's 2026-11-12 live directive orders them closed. The fifth surfaced live mid-arc: the hand-spawned corrections writer parked on an operator approval request at its first gated calls, because a session-minted child runs approval-gated and no rule names that consequence.

## Gist & Examples

TLDR: close the five false-stop gaps (admission operand evidence, aging-bound carve-out, bookkeeping-alert self-clear, missed-fire liveness, session-mint posture) so the loop runs until the queue empties or the 5h wall, the operator's standing D-18 direction.

Before: one paused peer authoring claim (review-fold-output-prevalidation, fresh at 13:31Z, surface disjoint from every candidate) refused both lanes' dispatches for days; the refusal-explained starvation fired a `turn_error` each survey; three of those armed a G2 alert no turn could clear; and a silently skipped 11:00Z carrier fire was visible to nothing.
After: the same consult verdicts on real overlap (the derived record names the claim's row and entry origins, so a disjoint candidate admits and a same-origin candidate still refuses); hold-explained surveys stop counting as starvation; a bookkeeping-class alert self-clears with a dated trace when its named cause drains; a missed fire is classified by a read-only operation a launchd carrier runs, so the gap is visible outside the turn lifecycle; and the dispatch ladder names a session-minted child's approval-gated default, so unattended legs never depend on one and the operator-attendance cost of a sanctioned mint is stated up front.

## Outcome

The maintenance loop runs until the eligible queue empties or the 5h wall binds, without parking on bookkeeping or needing an operator to notice a stalled surface.

- A live foreign authoring run no longer blocks target-disjoint execution dispatches; same-origin collisions still refuse.
- Queued plans held by recorded sanctioned holds stop aging into false starvation signals.
- A bookkeeping-class alert self-clears on verified resolution; real child-failure alerts keep their human gate.
- A silently missed carrier fire is classified by a read-only operation and reported, warning-first.
- A session-minted child's approval-gated posture is named in the dispatch ladder; unattended legs route through automation-born carriers or hold for the operator.

Gate delta: adds one warning-only read-only liveness operation plus its launchd carrier (report-only first two weeks; machinery registry duty row with a pre-registered removals row, review date 2026-12-12); adds one bounded evidence-gated self-clear lifecycle write for the bookkeeping alert class; removes the blanket conservative refusal surface for derivable authoring claims (Task 1), the starvation signal on hold-explained surveys (Task 2), and the unconditional human-gate requirement for the bookkeeping alert class (Task 3, priced by the witnessed 26-hour healthy-loop park recorded in the origin rows); Task 5 adds no gate (one ladder bullet naming an existing runtime constraint); no schema fields change.

## Assumptions

- assume D-18 is the standing policy of record and this plan enforces it; basis: docs/maintenance/operator-directives.md D-18 (landed in 3449f3090).
- assume the admission consult needs no script change; basis: scripts/dispatch_admission.py's manifest reader accepts derived owned_paths records (read at authoring).
- assume the liveness operation rides the existing runtime-operation and launchd watcher conventions; basis: scripts/execute_plan_runtime.py's operation registry and the budget-resume watcher family it drives.
- assume the two live peer arcs (review-fold-output-prevalidation, byte-budget posture plan) are separate lanes, untouched here; basis: their own claims and plans.
- assume the session-mint posture fix is text-only; basis: the runtime session-creation primitive exposes no posture parameter (read at authoring) and automation-born carriers run full-automatic (weeks of unattended 03:00 completions).

Decision points requiring a grill: T4 landing posture: warning-only with a pre-registered removals row and review date 2026-12-12, basis the row's machinery admission fields and the guidelines' new-machinery protocol, affects Task 4; T3 allowlist: the self-clear reason class starts closed with exactly queued-execution-starved, basis the witnessed class only, affects Task 3; T1 shape: operand derivation lives in the deciding-turn procedure text with no script change, basis dispatch_admission.py already accepts records, affects Task 1; T5 shape: the posture rule is one dispatch-ladder bullet naming the consequence, no gate and no change to the corrections route's scheduled-workflow sentence, basis that separation-of-duties clause is load-bearing and operator-owned, affects Task 5.

## Standing constraints

- Skill-text anti-growth rules (repository guidelines): each amendment lands in its named home; the incident story stays in the origin rows; operative text cites an incident in at most one line.
- The pins suite (`scripts/check_maintenance_pins.sh`) pins literals in the guarded maintenance modules this plan edits; run it after each task's edit.
- No new top-level section in any edited module: each insertion extends the section the origin row names, or the row's named absence is the design input.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the witnessed admission repro with a derived record admits and without it refuses, both verified by running the real consult; the aging and alert arms verified against their witnessed scenarios on the live state files.
- compatibility: pins suite, public hygiene scan, and focused suites all exit 0.
- maintainability: one-line incident citations only; no new top-level section in any edited module.

**Done when:**
- focused suites green: the runtime suite's new liveness-operation cells pass and `machinery_inventory.py --check` reports no new finding.
- pins and hygiene exit 0 over the changed files.
- the full readiness gate passes on the certified plan bytes.

**Ship when:** the next scheduler turn under a live foreign authoring claim dispatches an execution child, and a bookkeeping-class alert self-clears on a later survey; observation is human-owned on the live loop.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/scheduling.md` (Task 1)
- `agents/skills/maintenance/survey-arms.md` (Task 2)
- `agents/skills/maintenance/guards.md` (Task 3)
- `agents/skills/maintenance/state-file.md` (Task 3)
- `agents/skills/maintenance/failure-cap.md` (Task 3)
- `agents/skills/maintenance/zcode-dispatch-ladder.md` (Task 5)
- `scripts/execute_plan_runtime.py` (Task 4)
- `scripts/machinery_registry.json` (Task 4)
- `agents/skills/maintenance/CHANGELOG.md` (Task 1) with one line each from Tasks 1-5

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` (Task 4)

**Plan-related extension:** implementation and review may change files not listed above when causally related to a task (for example the survey-arms census clause's sibling references). Otherwise out of scope.

**Out of scope; reject unless plan-related:**
- `scripts/dispatch_admission.py`; reason: the consult script is unchanged by design (Task 1's receipt).
- `agents/skills/maintenance/zcode-recurring-recipe.md` and zcode-scheduling-primitives.md; reason: the carrier arming and chaining shapes are unchanged; Task 4 adds a read-only operation beside them.

## Validation Commands

Authoring preflight record (rule 29, 2026-11-12, placement root = the authoring worktree):
- no-em-dash: `touched` scan OUTCOME pass; `added-lines --base 3449f3090` OUTCOME pass.
- public hygiene scan: OUTCOME pass.
- maintenance pins suite: OUTCOME pass.
- pre-round structural gate: OUTCOME pass; advisory warnings accepted (execution budget above the 3h plan cap and 5 tasks above the 4-task cap, intrinsic to the five origin classes; the files-coverage warnings were fixed at authoring).
- plan_readiness.py full mode: the pre-review state is the tolerated no-review-artifact class; the full gate re-proves review-record bindings at round-close.
- pytest scripts/test_execute_plan_resume_watcher.py: 248 passed, 78 subtests (GREEN baseline).
- pytest scripts/test_machinery_inventory.py: RED today, 1 failed (RealTreeCheck::test_real_tree_checks_green, 26 passed), 4 findings witnessed identically on main and in this worktree: stale witness refs to docs/history/backlog/2026-11-07-operative-files-exceed-read-tool-single-read-cap.md and to docs/history/plans/2026-11-08-clocked-order-payload-session-execution.md, plus unregistered scripts/profile_skill_gate_consult.py and scripts/run_required_test_suite.py; the repair is Task 4's registry-repair item.
- dispatch_admission repro: OUTCOME fail with the conservative-verdict reason; expected pre-Task 1; this command is the defect demonstration the plan closes.
- rg session-mint over the dispatch ladder: no match; expected pre-Task 5 presence check.
- rule 22 authoring-time mechanical audit: bash -n over this block OK; this plan pins no literal validation spans (tasks name sections and intent, not exact spans), so the exactly-once span audit has no spans to check.

Round-start state for r1: branch authoring/maintenance-indefinite-operation-stop-gaps; base 3449f3090.

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-12-maintenance-indefinite-operation-stop-gaps.md
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_machinery_inventory.py -q
python3 scripts/dispatch_admission.py --candidate-run repro --plan docs/history/plans/2026-11-12-maintenance-indefinite-operation-stop-gaps.md --outstanding-without-manifest review-fold-output-prevalidation --outstanding-claim-updated review-fold-output-prevalidation "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --stale-after-hours 8
rg -n "session-mint" agents/skills/maintenance/zcode-dispatch-ladder.md
```

### Task 1: derived owned-path operands for source-less authoring claims

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `Landing gate` in `agents/skills/maintenance/decisions.md`

- [x] `Landing gate` operand choice delivers `derived admission record`: given a claim-live authoring outstanding run whose claim file resolves at the primary checkout and names its item row and origins, expects the deciding turn to pass `--outstanding-with-manifest` with a derived record whose `owned_paths` are the claim's item row plus the frozen entry's `Origins:` rows, written to the session tmp [class: IMPLEMENTATION_REQUIRED]
- [x] `Landing gate` operand choice keeps `conservative fallback`: given an authoring claim that does not resolve or whose entry cannot be read, expects the existing `--outstanding-without-manifest` conservative path byte-unchanged in behavior [class: IMPLEMENTATION_REQUIRED]
- [x] The final-slot consult sentence in the scheduling module carries the same operand choice by reference: given the Step 5 final-slot re-consult, expects the identical derivation with no second wording home [class: IMPLEMENTATION_REQUIRED]
- [x] Probe: run the consult with a derived record for the witnessed claim against the disjoint candidate and expect `OUTCOME: pass`; run without the record and expect `OUTCOME: fail`; record both outputs in the task evidence [class: REPOSITORY_TEST]
- [x] Same-origin collision witness: given a candidate whose owned paths include the claimed row, expects refusal naming the intersecting path (run the consult with an intersecting candidate and expect `OUTCOME: fail`) [class: REPOSITORY_TEST]
- [x] Pins + hygiene exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: derive authoring-claim owned-path operands for the admission consult` [class: IMPLEMENTATION_REQUIRED]

### Task 2: aging-bound carve-out for hold-explained surveys

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `Landed-plan disposition fence` in `agents/skills/maintenance/survey-arms.md`

- [x] Census clause delivers `fourth carve-out`: given a queued_execution entry whose no-dispatch surveys each recorded a sanctioned hold covering the entry's lane, expects the bound to record the standing reason and not fire `turn_error` [class: IMPLEMENTATION_REQUIRED]
- [x] Census clause keeps `real starvation signal`: given an entry with at least one unexplained no-dispatch survey inside the three-survey window, expects the count to resume and the bound to fire exactly as today [class: IMPLEMENTATION_REQUIRED]
- [x] The three existing carve-outs and the bound's thresholds read byte-unchanged after the edit (diff check recorded in task evidence) [class: REPOSITORY_TEST]
- [x] Pins + hygiene exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: exempt hold-explained surveys from the queued-execution aging bound` [class: IMPLEMENTATION_REQUIRED]

### Task 3: bookkeeping-class G2 alert self-clear

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/failure-cap.md`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `G2 (failure cap)` in `agents/skills/maintenance/guards.md`
- `Human clear procedure` in `agents/skills/maintenance/state-file.md`

- [x] `G2` bullet delivers `bookkeeping-class self-clear`: given a standing alert whose tripping reason is `queued-execution-starved` and whose named entries have since dispatched, left the plans root, or whose blocking consult now admits on a live rerun, expects a survey turn to clear the alert, reset the tripped counter, delete the memory-side note, and record the dated evidence trace, without an operator [class: IMPLEMENTATION_REQUIRED]
- [x] `G2` bullet keeps `human-gated classes`: given a child-cap, duplicate-parent, merge-lock-stale, or write-failure tripping reason, expects no self-clear path to fire [class: IMPLEMENTATION_REQUIRED]
- [x] Self-clear keeps `cause-must-drain`: given the named entries still blocked on a fresh consult rerun, expects the alert to stand with no counter growth and the survey evidence recorded [class: IMPLEMENTATION_REQUIRED]
- [x] Human clear procedure paragraph names the machine-executed self-clear as the bookkeeping class's sanctioned clearer (one insertion, the procedure's own clearer list) [class: IMPLEMENTATION_REQUIRED]
- [x] Pins + hygiene exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: evidence-gated self-clear for bookkeeping-class G2 alerts` [class: IMPLEMENTATION_REQUIRED]

### Task 4: missed-fire carrier-liveness operation (warning-only)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_runtime.py` *(new operation on the existing registry)*
- `scripts/test_execute_plan_resume_watcher.py`
- `scripts/machinery_registry.json`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `main` in `scripts/execute_plan_runtime.py`

- [x] `main` delivers `carrier-liveness` operation: given the scheduler state file's `next_turn_at` plus the recorded parent's listing state read through the task-index store conventions scripts/maintenance_fire_outcomes.py already uses, expects a JSON verdict classifying `ok`, `missed-fire` (past a bounded grace window with `lastRunAt` not advanced), or `unknown` (state or store unreadable), read-only, writing nothing [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a fresh fire still inside the grace window, expects the verdict `ok`, never a missed classification [class: IMPLEMENTATION_REQUIRED]
- [x] Warning-only wiring: given a `missed-fire` verdict, expects the verdict to be recorded report-only in the survey turn's notes entry in the scheduler state file (no re-arm, no ledger write) until the promotion review [class: IMPLEMENTATION_REQUIRED]
- [x] Darkness-window trace: given no survey turn runs after a missed-fire verdict, expects the verdict's durable trace to be the launchd carrier's logged operation output until a later survey turn records it in the notes entry [class: IMPLEMENTATION_REQUIRED]
- [x] The machinery registry duty row carries the pre-registered removals row and review date 2026-12-12 [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused runtime suite, expect RED on the new cells before implementation, GREEN after; record both runs [class: REPOSITORY_TEST]
- [x] Registry repair over the red-today baseline: update the two stale witness refs (the operative-files single-read-cap row and the clocked-order plan) to their durable homes re-derived from disk (the completed/ twin or the covering plan) [class: IMPLEMENTATION_REQUIRED]
- [x] Registry repair continues: register or disposition the two unregistered scripts (`profile_skill_gate_consult.py`, `run_required_test_suite.py`) per the exemplar row shape; the machinery inventory check exits 0 after both repair items (the four pre-existing findings witnessed red at authoring, recorded in the Validation preamble) [class: IMPLEMENTATION_REQUIRED]
- [x] The machinery inventory check reports zero findings attributable to the new carrier-liveness duty row after registration [class: REPOSITORY_TEST]
- [x] Pins + hygiene exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: warning-only carrier-liveness operation for missed carrier fires` [class: IMPLEMENTATION_REQUIRED]

### Task 5: session-mint posture rule for approval-gated spawned children

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode-dispatch-ladder.md`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `Child dispatch ladder` in `agents/skills/maintenance/zcode-dispatch-ladder.md`

- [x] `Child dispatch ladder` delivers `session-mint posture`: given any encoded or proposed session-spawn arm, expects the rung text to name the minted child's approval-gated default and its operator-attendance consequence [class: IMPLEMENTATION_REQUIRED]
- [x] `Child dispatch ladder` keeps `unattended routing`: given a leg that must complete without an operator, expects the rung text to keep session-minted children out of the unattended shapes (automation-born carriers and hold-for-operator remain the only unattended rungs) [class: IMPLEMENTATION_REQUIRED]
- [x] Payload disclosure duty: given a sanctioned operator-present mint, expects the rule to require the spawned payload to state the approval expectation up front [class: IMPLEMENTATION_REQUIRED]
- [x] The corrections route's scheduled-workflow sentence (the writer sentence of the correction_authorizations paragraph in `agents/skills/maintenance/state-file.md`) reads byte-unchanged after the edit (diff check recorded in task evidence) [class: REPOSITORY_TEST]
- [x] Pins + hygiene exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: session-mint posture rule for approval-gated spawned children` [class: IMPLEMENTATION_REQUIRED]


## Origins dispositions

- `docs/history/backlog/2026-11-12-admission-consult-blocks-disjoint-dispatches-on-authoring-claims.md` - closed covered by this plan's execution landing (Task 1 closes the consult's false refusal; row deleted in the completion pass, this fold is its witness).
- `docs/history/backlog/2026-11-12-queued-execution-aging-bound-fires-on-guard-blocked-piles.md` - closed covered by this plan's execution landing (Task 2's fourth carve-out; row deleted in the completion pass).
- `docs/history/backlog/2026-11-12-bookkeeping-class-g2-alert-self-clear.md` - closed covered by this plan's execution landing (Task 3's evidence-gated self-clear; row deleted in the completion pass).
- `docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md` - closed covered by this plan's execution landing (Task 4's warning-only carrier-liveness operation plus survey-side consult bullet; row deleted in the completion pass; between-survey arming rides the registry removals row's 2026-12-12 review).
- `docs/history/backlog/2026-11-12-session-mint-approval-gated-child-posture-gap.md` - closed covered by this plan's execution landing (Task 5's dispatch-ladder posture bullet; row deleted in the completion pass; the sibling corrections-writer spawn-arm row stays open under its own lane).

## Disposition of migrated backlog items

All five origin rows completed their execution flip to `covered` and are deleted in the same completion pass per the plans lifecycle (the fold-and-delete shape the origins gate accepts), each named here as its fold witness:
- `docs/history/backlog/2026-11-12-admission-consult-blocks-disjoint-dispatches-on-authoring-claims.md`
- `docs/history/backlog/2026-11-12-queued-execution-aging-bound-fires-on-guard-blocked-piles.md`
- `docs/history/backlog/2026-11-12-bookkeeping-class-g2-alert-self-clear.md`
- `docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md`
- `docs/history/backlog/2026-11-12-session-mint-approval-gated-child-posture-gap.md` The execution run's own filings: the off-plan em-dash residue row (decisions.md D1), the round-1 through round-3 deferral rows (carrier-liveness test-cell gaps, pins presence needles, disabled-parent arm, code simplification, wording shrink pack, posture drift signal, revert couplings, holds member cap, liveness note evidence slots, plan-record divergence banner, admission delta-note review date) all remain open by design - they are the graded Phase 3 exit's backlogged residuals, each a durable row filed in the run's own commits. The failure-cap stop-posture pointer row was superseded: its one-clause fix landed in the same run (commit 0f2480afb) and the row was deleted with the fix rather than left as a covered stub.

Disposition banner (the plan-record divergence capture): Task 4's darkness-trace expectation delivered as the survey-notes-entry trace of record per the Phase 3 address-pass rewording (commit 0f2480afb); between-survey visibility (any launchd-carrier-side pass) is the removals row's 2026-12-12 review's arming decision; the warning-only period ends at that review (the plan's Gist and Gate delta wording predates this delivery truth and is superseded by this banner on the authoritative completed/ twin).
