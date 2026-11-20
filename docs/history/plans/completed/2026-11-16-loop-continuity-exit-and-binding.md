# Plan: Loop continuity exit composition and duty binding

Backlog origins (scope of record):

- docs/history/backlog/2026-11-16-raced-out-author-exit-starvation-fallthrough.md
- docs/history/backlog/2026-11-16-interactive-maintenance-ask-loop-duty-binding.md

Driving force: reliability (off-taxonomy tag; implemented anyway on the operator's 2026-11-16 direct challenge ordering this hardening, which names the witnessed dark exits; park-triage would not defer it because the defect class silently strands the operator's own windows while dispatchable work remains)
Plan review record: the staging series .ai-playbook/reviews/2026-11-16-plan-review-loop-continuity-exit-and-binding-pf0997c5d-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 1h
Executed: yes (4e897f230 post-rebase; pre-rebase implementation tip 8a5bad7ce)
Authoring claim: 2026-11-16-raced-out-author-exit-starvation-fallthrough.md (session sess_a70f2dbb-1f2d-489b-933d-255924d00db5)

## Terms

- Starvation switch: the Loop modes paragraph in the maintenance skill that lifts a bound mode's lane exclusion when that mode's own lane runs empty; its author predicate reads D2's selection rules, the rolling-log readiness, and the investigate leg's set.
- D1: the maintenance skill's execution-lane decision rule (agents/skills/maintenance/decisions.md), whose selection universe is open plans.
- D2: the maintenance skill's authoring-lane decision rule (agents/skills/maintenance/decisions.md); D3: the shared defer/hold resolution both lanes fall through to.
- Exec-mode selection rule: the exec lane's urgency-first selection bullet in decisions.md; its terminal-exit sentence is the mirrored wording Task 1 composes by reference.
- duties-core: agents/skills/maintenance/duties-core.md, the shared maintenance child duty set carrying the loop-liveness line duty for dispatched children.
- Maintenance router: agents/skills/maintenance/SKILL.md and its step modules; a session that never loads it misses the loop duties bound there.
- `mode-starved-bypass:<lane>`: the decision_reason token the Starvation switch records when it lifts a bound mode's exclusion.
- Starvation fall-through: the composition ordering a lane's terminal exit to consult the Starvation switch before stopping.
- Loop-scoped (for `loop-exit:queue-empty`): every lane's inputs empty, read through the recording session's switched-lane reach.
- Switched-lane reach: the lanes a session can work once the Starvation switch lifts its bound mode's exclusion (for an author-switched turn, D1's plans-only selection).
- D-18 exit token: one of the six recorded loop-exit classes (`queue-empty`, `quota-wall`, `blocked-retry`, `operator-park`, `operator-stop`, `directive-cap`) a maintenance session records at its exit.
- `loop-liveness:` line: the closing-report line naming the exit token or standing-carrier exemption with the armed carrier's id and fire time.
- Byte-budget payment: the repository anti-growth rule that a change growing a skill file past its cap deletes equivalent bytes in the same file in the same change.
- Pins suite: `scripts/check_maintenance_pins.sh`, exit 0 required over the pinned skill-text spans.
- Raced out: an author-mode session whose walk to the only dispatchable entry was beaten by a fresh foreign claim at claim time, exiting with zero picks.
- Survey-only precedence clause: the composition's never-fire condition under the Project-class guard's survey-only resolution or the state file's `survey_only` flag.
- Scan-hold fall-through: D2's `When the scan holds, D2 falls through to D3` resolution.
- D-18: the exit-duty directive record in docs/maintenance/operator-directives.md.
- Mode-gated residual: execution-lane inputs (EXEC-PROMPTS entries, ad-hoc-eligible items) the switch keeps gated to exec-bound sessions even when an author session is switched.
- pending_rearm park: the state-file record plus paired payload copy that parks an unexecutable loop re-arm for the next capable session.

## Why

A maintenance session whose lane walk exhausts, or whose dispatch never routes it through the maintenance router, can end the loop dark: no exit token recorded, no starvation fall-through taken, hours of window and an occupied other lane left unused. The 2026-11-16 three-way author fan-out witnessed both shapes with the primary window mostly unspent and the execution lane holding ten-plus pending plans.

## Gist & Examples

TLDR: compose the starvation switch into the author lane's terminal exit and bind the D-18 loop-liveness duties onto the workflow surfaces every maintenance session already loads, so a raced-out or interactively dispatched session cannot end the loop dark (reliability).

Before: an author-mode session raced out at the only dispatchable entry walks to exhaustion and stops, recording no exit token; an interactive ask routed only to the plans skill closes with no `loop-liveness:` line while the exec lane holds dispatchable plans. After: the same session consults the starvation switch before its terminal exit, works the exec lane under `mode-starved-bypass:author` when the switch fires, and every maintenance-lane session records its exit token and `loop-liveness:` line through the binding sentences on the surfaces it actually loads.

## Outcome

The author lane's exhausted scan composes the starvation switch before any terminal exit, and every workflow-side maintenance session records the D-18 exit duties at its closeout.

- A raced-out zero-pick authoring session continues into the execution lane (or records `loop-exit:queue-empty` only when every lane's inputs are empty) instead of ending dark.
- Any session performing maintenance-lane work through the plans or execute-plan skill records the `loop-liveness:` line and its exit token, whatever surface delivered the dispatch.
- D-18's `queue-empty` class reads loop-scoped through the recording session's switched-lane reach, so a lane-local exhaustion never stops the whole loop while reachable other-lane work remains.

Gate delta: no new gate, refusal, fence, protocol layer, or schema field; the additions are four by-reference sentences (one composition sentence in D2, three binding sentences on the workflow-side surfaces, each carrying the survey-only precedence clause) and one scope pin inside D-18's record; the prose-only closing-report duty they reach for is priced by the origin rows' rejected-alternatives records (no seventh token, no wake primitive, no payload-carried clause copies: each recorded-rejected there), and no existing refusal, check, or field is removed.

## Assumptions

- The starvation switch's author predicate already includes the investigate leg's set, so composing the switch covers the investigate-leg fall-through without a separate sentence (basis: the Starvation switch paragraph's predicates in the maintenance skill's Loop modes section).
- D-18's scope wording already covers user-directed payload sessions, so the binding sentences add reach, not semantics (basis: D-18's scope line in docs/maintenance/operator-directives.md).
- The byte-budget ratchet rows are advisory and ceiling breaches are blocking; decisions.md sits at 99996 bytes against the 92132 ratchet cap and the 100000-byte blocking single-read ceiling (4 bytes of headroom measured 2026-11-16), so payment precision is ceiling-critical and the delta must be zero or negative (basis: scripts/skill_text_budget.py --check output, 2026-11-16).
- Reach basis for the Outcome's second bullet: the plans router loads handoff-and-done.md "when the review gate reports ready and before finishing the session" (the before-finishing clause being the unconditional finish-time load trigger) and integration-points.md "when a cross-skill boundary needs its contract details"; a plans-skill session closing without a plan still runs the module's own no-charter and stand-down closeout arms, which load the same module, and the launch-rules surface loads at every worker launch and interruption (execute-plan's dispatch entry), so an execute-plan run standing down before its first worker launch is the one class the binding's mechanical reach misses; that class is a recorded omission in Standing constraints.
- No-carrier routing receipt (the design choice the r2 review required in-plan): with no armed carrier standing, the residual-inputs case records `loop-exit:queue-empty` through the recorder's switched-lane reach with the mode-gated residual noted on the `loop-liveness:` line; the residual is then outside every session's reach, so the recorder-scoped loop-scoped reading is literally true and D-18's exemption form (which requires a carrier or directive to name) stays satisfiable (basis: D-18's recorded population and loop-liveness binding in docs/maintenance/operator-directives.md).
Decision points requiring a grill: none remain.

## Standing constraints

- Skill text anti-growth rules: operative text cites the incident in at most one line; any growth past a file's cap pays an equivalent same-file deletion in the same change.
- The pins suite must stay exit 0 after every edit (`scripts/check_maintenance_pins.sh`).
- Scoped omissions recorded: (a) the binding sentences bind exit-side duties only; the Step 0 turn-start carrier re-arm stays router-bound because arming requires the automation primitives and state-file semantics whose homes the router owns, and a workflow-side session without the router cannot safely arm (the existing pending_rearm park covers a dark parent for the next router-reading session); (b) no provider-side attestation clause is added to the maintenance skill's Integration Points in this plan: the duties cited are already single-homed in D-18 and duties-core, and adding provider-side text to a file already over its Part 4 pilot target for drift-aid symmetry is deferred to a future plan that can pay its bytes.
- The workflow-side binding sentences make sessions read the state file's `survey_only` flag and the facts document's `project_type`, reader classes outside the flag's declared contract (SKILL.md's Mode enforcement paragraph declares the flag's only contract its reader text); that sentence is deliberately left unedited here and its staleness is this recorded disposition, a future router-side edit owning the refresh.
- An execute-plan run standing down before its first worker launch never loads the launch-rules surface and its closeout misses the binding; that class's recording stays router-side (the scheduler turn or the operator-visible stand-down report) and is a recorded omission here.
- Follow-up disposition: no candidate rejection is anticipated; the origin rows' Alternatives sections already record the rejected dispositions with their evidence, and any execution-time candidate rejected there takes that recorded route.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each added sentence names its duty home by reference (Starvation switch paragraph, D-18 record, duties-core loop-liveness duty) and never restates their semantics.
- Byte discipline: every touched skill file's delta is net-zero or negative where the file sits past its ratchet cap, reported in the run report with before-bytes, after-bytes, and delta.
- Non-regression: D2's scan semantics outside the scan-hold fall-through, the survey-only precedence ordering, and the pinned spans stay byte-identical or semantically equivalent; the Exec-mode selection rule's terminal-exit sentence stays byte-identical, verified by Task 2's byte-identity checkbox (the scoped `git diff` assertion).

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0.
- `python3 scripts/skill_text_budget.py --check` reports 0 ceiling breaches.
- The D2 scan-hold fall-through composes the switch before the fall-through, per Task 1's first item.
- D-18's record pins `queue-empty` loop-scoped through the switched-lane reach, per Task 1's D-18 record pin item.
- The three workflow-side files carry the binding sentences.
- The public hygiene scan exits 0.
- Content verification note: the three content-bearing edits above are verified by review-panel diff inspection against this plan's task text (the pins suite has no pins over the edited spans; the suite's exit 0 is a regression guard over pre-existing pins, not content verification).

**Ship when:**
- The next raced-out or interactively dispatched maintenance session records its exit token and takes the starvation fall-through (operational condition; observed on later runs, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1, Task 2)
- `docs/maintenance/operator-directives.md` (Task 1)
- `agents/skills/maintenance/CHANGELOG.md` (Task 2, Task 3)
- `agents/skills/plans/integration-points.md` (Task 3)
- `agents/skills/plans/handoff-and-done.md` (Task 3)
- `agents/skills/execute-plan/launch-rules-and-gates.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/` validators and suites; reason: execution-time tools, edited only if a suite fails against the new text, which routes through the plan-related extension rule.
- `agents/skills/maintenance/SKILL.md`; reason: the Starvation switch paragraph is already mode-generic and needs no edit; a finding there is out of scope unless the composition sentence cannot resolve without it.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_skill_text_budget.py -q
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Author terminal exit composes the starvation switch; D-18 pins queue-empty loop-scoped

Context surface: the plan's Terms, this task, and `## Standing constraints`; documentation-only task (no Primary class anchors block): the owning surfaces are D2's scan-hold sentence in decisions.md and D-18's directive record in operator-directives.md.

Files:
- `agents/skills/maintenance/decisions.md`
- `docs/maintenance/operator-directives.md`

- [x] D2's scan-hold sentence (`When the scan holds, D2 falls through to D3`, mid-bullet before the quota-state-aware carrier-selection rule) is edited in place to order, by reference, the Starvation-switch consultation before that fall-through only [class: IMPLEMENTATION_REQUIRED]
- [x] The composed sentence names the Step 3 mode-enforcement paragraph's switch bullet as the in-file composition home and the Loop modes switch paragraph as the predicate home; every other D3 resolution (survey-only precedence, audit/retriage dues, log-entry authoring, quota deferrals) stays byte-untouched [class: IMPLEMENTATION_REQUIRED]
- [x] The stand-down routing follows the Exec-mode selection rule's terminal-exit arm by reference: for a switched author turn the stand-down predicate reads the workable set (D1's plans-only selection empty) [class: IMPLEMENTATION_REQUIRED]
- [x] Mode-gated residual execution inputs (EXEC-PROMPTS entries, ad-hoc-eligible items) outstanding at that point record the D-18 standing-carrier exemption on the `loop-liveness:` line when the coverage consult finds an armed standing carrier, and with no armed carrier standing record `loop-exit:queue-empty` through the recorder's switched-lane reach with the residual noted on the line [class: IMPLEMENTATION_REQUIRED]
- [x] The composition never fires where the Project-class guard's survey-only resolution or the state file's `survey_only` flag stands the lanes down [class: IMPLEMENTATION_REQUIRED]
- [x] That condition the composing session resolves by reading the facts document's `project_type` under the guard's confirmation semantics and the `survey_only` flag at the primary checkout's `.ai-playbook/scheduler-state.json` (the first `git worktree list --porcelain` entry, per the state file's explicit-rooting convention) before composing [class: IMPLEMENTATION_REQUIRED]
- [x] D-18's record pins `loop-exit:queue-empty` as loop-scoped with the authoritative reading stated: loop-scoped means every lane's inputs empty per the switch predicates read through the recording session's switched-lane reach [class: IMPLEMENTATION_REQUIRED]
- [x] An author-bound recorder over mode-gated residual execution work names the standing carrier on the `loop-liveness:` line when an armed carrier stands and, with no armed carrier, records `loop-exit:queue-empty` through its switched-lane reach with the residual noted on the line, the loop-scoped reading then literally true at the recorder's reach [class: IMPLEMENTATION_REQUIRED]
- [x] Run → recorded: the byte-budget check exits 0 and the pins suite exits 1 on the pre-existing foreign red (witness 2026-11-17: PIN FAIL "prompt log has no all-served (stale) entry", the asd-ste100 lane's PLAN-PROMPTS prune owned by that lane per its prune rule; failing set byte-identical at merge-base 617af0c9c and on main's clean checkout) The edited spans carry no pins; the suite's exit-0 expectation was a regression-guard reading, not content verification (see the Content verification note). [class: REPOSITORY_TEST]
- [x] Commit: `docs: compose starvation switch into author terminal exit and pin queue-empty loop-scoped` [class: IMPLEMENTATION_REQUIRED]

### Task 2: decisions.md byte payment and non-regression evidence

Context surface: the plan's Terms, this task, and `## Standing constraints`; documentation-only task (no Primary class anchors block): the owning surfaces are decisions.md's D1 landing-gate paragraph (the byte payment) and the maintenance CHANGELOG revision line.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/CHANGELOG.md`

- [x] decisions.md's byte payment is measured, ordered, and pre-registered: the deletion lands before or atomically with the addition at the change boundary the squash landing composes (Task 1's checkpoint commit may transiently hold the composition growth on the unlanded branch; the 0-ceiling-breach acceptance binds at Task 3's GREEN and at the landing boundary) [class: IMPLEMENTATION_REQUIRED]
- [x] The pre-registered candidate compresses the D1 landing-gate paragraph's operand-choice clauses SKILL.md's fleet-cap invariant carries in parallel (claim-live-admission-record, done-session-homes, retired-claim, conservative-verdict; the duplication verified by reading both spans) to a by-reference mention of SKILL.md's parallel enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] decisions.md keeps verbatim the exit-3 tool-error defer, the claim-staleness arms including the authoring-run staleness pairing clause, the source-less-run enumeration, and the entire authoring-lane derived-record arm, the derivation SKILL.md's fleet-cap invariant and scheduling.md's final-slot re-consult declare decisions.md the one wording home for; any further deletion searched among the file's longest sentences under the same bar [class: IMPLEMENTATION_REQUIRED]
- [x] Acceptance is measured in the run report as before-bytes taken at the pre-Task-1 baseline, after-bytes, and delta with delta <= 0, keeping `skill_text_budget.py --check` at 0 ceiling breaches [class: IMPLEMENTATION_REQUIRED]
- [x] An rg sweep verifies that no inbound citation targets the deleted span's distinctive phrases and that the pointer-form citations still resolve (SKILL.md's and scheduling.md's by-name references to the D1 landing-gate derivation), with scheduling.md's own compact enumeration exempted as its own wording [class: IMPLEMENTATION_REQUIRED]
- [x] The Exec-mode selection rule's terminal-exit sentence stays byte-identical: the run report records a scoped `git diff` assertion over that bullet showing no changed lines [class: REPOSITORY_TEST]
- [x] CHANGELOG.md carries one revision line per changed surface citing this covering plan as the witness (its path, its completed twin after archival) and naming the origin rows only as origin pointers [class: IMPLEMENTATION_REQUIRED]
- [x] Run → recorded: the budget tool's own suite passes (19 passed) and the pins suite exits 1 on the same pre-existing foreign red recorded at Task 1's GREEN row (the edited spans carry no pins) [class: REPOSITORY_TEST]
- [x] Commit: `docs: pay the decisions.md byte budget with the pre-registered compression` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Loop-duty binding sentences on the workflow-side surfaces

Context surface: the plan's Terms, this task, and `## Standing constraints`; documentation-only task (no Primary class anchors block): the owning surfaces are the With-maintenance integration point and Final Step in the plans skill modules and the Sub-Agent Launch Rules quota-wall doctrine neighborhood in the execute-plan module.

Files:
- `agents/skills/plans/integration-points.md`
- `agents/skills/plans/handoff-and-done.md`
- `agents/skills/execute-plan/launch-rules-and-gates.md`
- `agents/skills/maintenance/CHANGELOG.md`

- [x] The With-maintenance integration point binds, by reference to D-18, the Step 4 quota leg, the Loop modes Starvation switch paragraph, and Task 1's composed D2 sentence as the in-file composition home, the closing `loop-liveness:` line, exit-token recording, boundary quota probe, and starvation composition for any session performing maintenance-lane work whose plan lands under the resolved plans_dir or whose origin is an open backlog row [class: IMPLEMENTATION_REQUIRED]
- [x] The binding's structural trigger: the work happens in a repository whose scheduler state file exists at the primary checkout (the first `git worktree list --porcelain` entry's `.ai-playbook/scheduler-state.json`); an interactive one-shot ask whose picks are complete records its exit through D-18's per-run-directive composition clause (`directive-cap` naming the ask), never `queue-empty` [class: IMPLEMENTATION_REQUIRED]
- [x] The composition never fires where the Project-class guard's survey-only resolution or the state file's `survey_only` flag stands the lanes down, a condition the session resolves by reading the facts document's `project_type` under the guard's confirmation semantics (the Project-class guard paragraph, `agents/skills/maintenance/SKILL.md`) and the `survey_only` flag at the primary checkout's state file before composing [class: IMPLEMENTATION_REQUIRED]
- [x] handoff-and-done.md's Final Step carries the same binding so the authoring lane's closeout records the exit token and liveness line even when the dispatch never routed the session through the maintenance router [class: IMPLEMENTATION_REQUIRED]
- [x] launch-rules-and-gates.md carries the mirrored binding for execution-side sessions beside the quota-wall dispatch doctrine, with the same structural trigger, per-run-directive classification hint, and survey-only precedence clause with its resolution mechanics [class: IMPLEMENTATION_REQUIRED]
- [x] Each touched skill file's byte delta reports payment per the anti-growth rules in the run report (before-bytes, after-bytes, delta) [class: IMPLEMENTATION_REQUIRED]
- [x] CHANGELOG.md carries one revision line per Task 3 changed surface with the same covering-plan witness form as Task 2's line [class: IMPLEMENTATION_REQUIRED]
- [x] Run → recorded: the byte-budget check and the public hygiene scan exit 0; the pins suite exits 1 on the same pre-existing foreign red recorded at Task 1's GREEN row [class: REPOSITORY_TEST]
- [x] Commit: `docs: bind loop-liveness exit duties onto the workflow-side surfaces` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-16-raced-out-author-exit-starvation-fallthrough.md`: executed by this plan; the author terminal exit now composes the Starvation switch through decisions.md's composed D2 sentence (consult-before-fall-through-only, the switch bullet as composition home with the Loop modes predicate home, the Exec-mode terminal-exit stand-down routing, the two-arm residual recording with the D-18 Loop-scoped pin naming `loop-exit:queue-empty`'s authoritative reading, survey-only precedence, D3 fall-through preserved), and the byte payment kept decisions.md net-negative (99996 → 99797).
- `docs/history/backlog/2026-11-16-interactive-maintenance-ask-loop-duty-binding.md`: executed by this plan; the loop-liveness closing duties bind onto the workflow-side surfaces every maintenance-work session already loads (the With-`maintenance` integration point, handoff-and-done's Final Step, and the execute-plan launch-rules-and-gates mirror beside the quota-wall doctrine), each carrying the same structural trigger, directive-cap classification for complete one-shot asks, and survey-only precedence clause.
