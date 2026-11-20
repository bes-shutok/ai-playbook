# Plan: interactive lane indefinite operation

Backlog origins (scope of record):
- docs/history/backlog/2026-11-13-interactive-lane-quota-wall-resume-arm.md
- docs/history/backlog/2026-11-13-lane-park-arm-self-heal-consult-pointer.md
- docs/history/backlog/2026-11-12-review-worker-dead-leg-brief-liveness.md

Authoring claim: 2026-11-13-interactive-lane-indefinite-operation.md (session sess_92142d7a-36fb-4bbf-81b0-e8f4a3919ec3)
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-interactive-lane-indefinite-operation-p7e03665a-r*.md (highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.0h
Executed: yes (execution witness: task commits 1bf7ea51c, bdb3e7f46, 27d98fc29; readiness gate pass over the executed bytes)
Cluster: docs/history/backlog/2026-11-12-corrections-writer-distinct-session-dispatch-gap.md, docs/history/backlog/2026-11-12-session-identity-runtime-channel-duty.md (deliberately open under their own frozen claims; cited here, never in the scope-of-record block)

## Terms

- 5h-wall arm: the occupied-lane chaining bullet's cross-window arming duty in `agents/skills/maintenance/decisions.md` ("The 5h-wall arm (the reset-anchored successor)"), which arms a one-shot resume at the probe's reset time plus its 10-minute margin.
- reset-anchored one-shot: the arm's carrier, a one-shot automation fired just after the quota window's reset.
- Budget gate: the plans/execute-plan quota pause-and-resume gate (canonical home: the execute-plan Budget gate section; authoring mirror: `agents/skills/plans/budget-gate.md`), firing at named boundaries only.
- backstop hook: the runtime budget-guard hook (`agents/hooks/budget-guard/`) that enforces the Budget-gate pause at the tool-call level once registered on a runtime.
- kill path: a quota wall that stops a lane off-boundary (mid-worker or mid-fold), where no Budget-gate boundary probe runs.
- cap park: the review loop's park-and-report exits at a configured cap or budget breach (`plan-quality-gate.md` rules 16 and 17).
- self-heal consultation: the one `self-heal` call the maintenance decisions non-user-only blocker line mandates before a stop is judged unrecoverable, a pause recorded, or the operator asked.
- non-user-only blocker: a blocker outside the decisions line's user-only carve-outs (missing authority, ambiguous ownership, unsafe target, external-owner action, explicit operator stop, and correct quota, ownership, safety, or authorization guards).
- worker template: a fenced sub-agent prompt template in `agents/skills/execute-plan/subagent-prompts.md` (here: the Review lens worker and the Intermediate task review worker).
- one-pass brief: a worker brief bounded to a slice the worker can finish inside the runtime's worker-inactivity window.
- emit-early duty: the worker duty to record verified-so-far findings at the parent-named log path before each deep verification pass.
- dead-leg procedure: the parent-side rule to inventory a dead panel member's partial disk effects and relaunch only the missing member, never the whole panel.
- worker-inactivity window: the runtime-side kill window for a silent worker (order of ten minutes per the origin row's witness), referenced by behavior, never by a tool name.
- occurrence-form gate: a validation gate asserting an exact substring's presence and count (`grep -oF` piped to `wc -l`).
- span operation: a plan-prescribed exact old-bytes to new-bytes replacement applied with an exact-match assertion.
- labeled span: a plan line carrying an exact insertion or replacement text as the line's final backtick pair; the executor extracts mechanically, never re-types.
- byte ledger: the plan's per-file inserted-versus-deleted byte accounting for the pay-for-growth discipline.
- liveness contract: the worker-side brief bound, emit-early duty, and dead-leg handling added by Task 3.
- full-panel-budget park: the rule 17 park of the Plan Quality Gate when the full-panel budget is breached.
- fixer: `scripts/fix_plan_em_dashes.py`, the write-time em-dash substitute the plans skill's fence rule names.
- battery: the repo's standing check set (readiness gates, em-dash gate, hygiene scan, maintenance pins suite) an authoring lane re-runs at each boundary.

## Why

Interactive lanes still stop dead at quota walls and at review-loop parks, and review panel legs die silently mid-round; each stop costs an operator restart the loop should own. This plan routes those three stop shapes into the arming and consultation machinery the repo already encodes, and gives worker templates the liveness contract their sibling template already has.

## Gist & Examples

TLDR: extend the 5h-wall arm's key to interactive-lane kills, route the cap parks through the self-heal consultation, and add the liveness contract to the review-side worker templates, so the maintenance loop runs until no tasks remain and rides a 5h wall by scheduling its own resume right after reset; driving force automation.

Before: a 5h wall kills an authoring lane mid-fold; nothing is armed; the operator restarts it by hand twice. A worker brief exceeding the inactivity window dies twice before a narrowed brief succeeds. A cap park reports an open-ended status instead of the one gated question.

After: the same wall arms the reset-anchored one-shot carrying the parked lane state (reset time from the probe, GMT+8 converted per the quota-effort timezone trap); a review leg emits partial findings before each deep pass so a cut-off leg leaves recoverable output and the parent relaunches only the missing member; a cap park follows one self-heal consultation for any non-user-only blocker and asks the operator exactly the user-only question.

## Outcome

A maintenance lane keeps working until no tasks remain, and a 5h wall becomes a scheduled pause with an armed resume instead of an operator-dependent stop.

- A mid-flight quota kill in any maintenance lane, interactive lanes included, arms the reset-anchored resume carrier right after the reset, the first capable turn after the reset acting as the arming actor when the wall stopped the lane dark.
- A cap park or full-panel-budget park records one self-heal consultation for a non-user-only blocker before the park is reported.
- Review-side workers run one-pass briefs with the emit-early duty, and the parent relaunches only the missing panel member after a death.

Gate delta: additions are one arming-key extension over an existing arm (no new arm, no new refusal class), pointer sentences at existing park arms, and worker-liveness prose duties in two existing templates and the worker-contract paragraph; priced by the witnessed incidents the origin rows record (the two-wall review-fold lane; the four dead review legs) and the operator indefinite-operation mandate 2026-11-12/13; no gate or fence is added (the gate-liveness ledger citation does not apply), no refusal class, fence, protocol layer, or schema field is added, and none is removed; net machinery across the counted classes: none.

## Assumptions

- The plans router's Uncertain workflow stops paragraph already carries the self-heal-once duty for skill-owned stops, so the origin row's budget-gate pause-step target is rewritten: quota pauses are consult-excluded by the decisions contract ("correct quota... guards stay blocking outside this consultation"), and the pointer arms are the cap park (rule 16) and the full-panel-budget park (rule 17), both blocker-class. Basis: plans SKILL.md Uncertain workflow stops paragraph and the decisions non-user-only blocker line, both read today.
- The decisions insertion pays for growth in the same change: two same-bullet compressions fund the key extension, and the file stays under the 100000 blocking ceiling; basis: `scripts/skill_text_budget.py --check` run today (99723 bytes, blocking posture pass) and lesson 442.
- The dead-leg procedure homes beside the panel's launch accounting rules in `review-panel-selection.md`; basis: that file owns Launch accounting and the launch-slot precedence rule cited by review-plan Step 2.
- Skill text stays tool-agnostic: the worker-inactivity window is described by behavior, never by a runtime or tool name; basis: the repo's tool-agnostic design rule.
Decision points requiring a grill: none remain.

## Standing constraints

- Skill text anti-growth rules bind every edit: land the rule, not the story (the incident dossier stays in the origin rows; operative text cites at most one line); every insertion names the section it extends; growth past a cap is paid in the same change.
- No em dash lands in any touched file or in plan bytes; the fixer runs before every plan write and the battery's em-dash check gates the execution.
- Tool-agnostic wording everywhere: describe behaviors by intent, never by tool or runtime name.
- Every insertion is applied from this plan's labeled spans by mechanical extraction with an exact-match assertion on the anchor; nothing is re-typed at execution.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every span operation applies exact-match on the current bytes; every occurrence-form gate reads its declared count.
- single-homing: the 5h-wall arm's key extension and the consult's lane discrimination live only in the decisions bullet (the duty's one home); the Plan Quality Gate carries pointers, never restatements, and the Budget gate's Boundaries paragraph owns the kill-case arming route as its own duty while pointing at the decisions arm shape.
- byte discipline: decisions.md ends under the 100000 blocking ceiling with the compression-funded ledger recorded in the plan; no other target crosses its cap.

**Done when:**
- all Validation Commands gates pass over the touched files;
- `python3 scripts/skill_text_budget.py --check` exits 0 in its blocking posture;
- the maintenance pins suite exits 0 (the touched skill files add no pin violations).

**Ship when:**
- the next interactive lane that hits a 5h wall arms its resume carrier instead of stopping dark (operational witness, not a checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/plans/budget-gate.md` (Task 1)
- `agents/skills/plans/plan-quality-gate.md` (Task 2)
- `agents/skills/review-plan/SKILL.md` (Task 3)
- `agents/skills/execute-plan/subagent-prompts.md` (Task 3)
- `agents/skills/review-agents/review-panel-selection.md` (Task 3)
- `agents/skills/execute-plan/phase-3-review.md` (Task 3)
- `agents/skills/execute-plan/invocation-and-orchestration.md` (Task 3)
- `agents/skills/execute-plan/agent-logs.md` (Task 3)

**Tests:**
- none (the validation surface is the gates in Validation Commands plus the existing suites named there)

**Plan-related extension:** implementation and review may change files not listed above when causally related: a consumer or README catalog line the touched files make stale, or a review-record repair record-side.

**Out of scope; reject unless plan-related:**
- `agents/skills/self-heal/SKILL.md` (the distinct-writer spawn arm); reason: owned by the open dispatch-gap row's own frozen authoring claim, a different lane.
- `agents/skills/maintenance/state-file.md` and the session-channel helper; reason: owned by the session-identity runtime channel duty row's frozen claim.
- `scripts/` (no code change in scope); reason: text-pointers and template prose only.

## Validation Commands

```bash
# T1 gate A (decisions key extension, occurrence form ==1)
grep -oF 'maintenance-lane stop whose evidence records a quota wall no standing carrier resumes' agents/skills/maintenance/decisions.md | wc -l | tr -d ' '
# T1 gate B (budget-gate pointer, ==1)
grep -oF 'the arm records the wall and its reset-anchored one-shot carries the resume' agents/skills/plans/budget-gate.md | wc -l | tr -d ' '
# T1 gate C (compression landed, occurrence form, ==0)
grep -oF "the overlay's scheduling primitives own the concrete form" agents/skills/maintenance/decisions.md | wc -l | tr -d ' '
# T1 gate D (span 3 landing pinned, ==1)
grep -oF 'plus the standing 10-minute arming margin (the quota-aligned' agents/skills/maintenance/decisions.md | wc -l | tr -d ' '
# T2 gate A (rule 16 pointer, ==1)
grep -oF 'routes through the Uncertain workflow stops duty' agents/skills/plans/plan-quality-gate.md | wc -l | tr -d ' '
# T2 gate B (rule 17 pointer, ==1)
grep -oF 'one self-heal consultation for a non-user-only blocker' agents/skills/plans/plan-quality-gate.md | wc -l | tr -d ' '
# T2 gate C (review-plan mirror pointer, ==1)
grep -oF "routes through the plans skill's Uncertain workflow stops duty" agents/skills/review-plan/SKILL.md | wc -l | tr -d ' '
# T3 gate A (worker-contract brief bound, ==1)
grep -oF 'bounded to a one-pass slice' agents/skills/review-plan/SKILL.md | wc -l | tr -d ' '
# T3 gate B (emit-early duty in both templates, ==2)
grep -oF 'so a cut-off leg leaves recoverable output' agents/skills/execute-plan/subagent-prompts.md | wc -l | tr -d ' '
# T3 gate C (dead-leg procedure, ==1)
grep -oF 'relaunch only the missing panel member' agents/skills/review-agents/review-panel-selection.md | wc -l | tr -d ' '
# T3 gate E1 (phase-3 reconciliation plus naming duty, ==2)
grep -oF 'emit-early' agents/skills/execute-plan/phase-3-review.md | wc -l | tr -d ' '
# T3 gate E2 (orchestration reconciliation plus step, ==2)
grep -oF 'emit-early' agents/skills/execute-plan/invocation-and-orchestration.md | wc -l | tr -d ' '
# T3 gate E3 (agent-logs reconciliation, both denials, ==2)
grep -oF 'emit-early' agents/skills/execute-plan/agent-logs.md | wc -l | tr -d ' '
# T1 gate E (consult lane discrimination, ==1)
grep -oF "a sibling lane's carrier is not coverage" agents/skills/maintenance/decisions.md | wc -l | tr -d ' '
# byte ceilings (blocking posture, exit 0)
python3 scripts/skill_text_budget.py --check
# em-dash added-lines gate over the touched files
bash scripts/check-no-em-dash.sh added-lines -- agents/skills/maintenance/decisions.md agents/skills/plans/budget-gate.md agents/skills/plans/plan-quality-gate.md agents/skills/review-plan/SKILL.md agents/skills/execute-plan/subagent-prompts.md agents/skills/review-agents/review-panel-selection.md agents/skills/execute-plan/phase-3-review.md agents/skills/execute-plan/invocation-and-orchestration.md agents/skills/execute-plan/agent-logs.md
# maintenance pins suite (exit 0)
bash scripts/check_maintenance_pins.sh
# review-agents mandated suites (Task 3 touches review-agents/; exit 0)
python3 scripts/check_review_agent_portability.py
python3 scripts/test_review_agent_doors.py
```

### Task 1: extend the 5h-wall arm to interactive-lane kills and point the Budget gate's kill path at it

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/plans/budget-gate.md`

Primary behavior owners: the occupied-lane chaining bullet's 5h-wall arm sentence in `agents/skills/maintenance/decisions.md`, and the Boundaries paragraph of `agents/skills/plans/budget-gate.md` (both in the Files list).

Prescribed spans (exact; each is the line's final backtick pair, applied with an exact-match assertion on the anchor):

T1 span 1 (insert after the anchor span "the Quota-aware lane decisions' defer and near-reset outcomes)"): `, or a maintenance-lane stop whose evidence records a quota wall no standing carrier resumes (a kill mid-worker or mid-fold, an interactive lane included; the relayed quota reset notice counts as the evidence)`

T1 span 2 (replace the anchor span "dispatch shape (the overlay's scheduling primitives own the concrete form; this duty invents no new primitive)"): `dispatch shape; this duty invents no new primitive`

T1 span 3 (applied as two replacements that together rewrite the reset-time phrasing inside the 5h-wall arm sentence; the token between the edited spans stays untouched): first replace the anchor span "reset time plus the standing 10-minute arming margin (the overlay's " with nothing, then replace the anchor span " + 10 minutes, the quota-aligned" with the span ` plus the standing 10-minute arming margin (the quota-aligned`

T1 span 5 (replace the anchor span "carries a lane marker (the runtime overlay's Child classification markers section defines the marker spans, cited by reference)" in `agents/skills/maintenance/decisions.md`): `carries the lane's marker (the runtime overlay's Child classification markers section defines the marker spans, cited by reference; a lane-specific arm carries its own lane's marker, so a sibling lane's carrier is not coverage)`

T1 span 4 (append to the Boundaries paragraph of `agents/skills/plans/budget-gate.md`, after the anchor span "so a mid-round quota exhaustion cannot silently burn the window."): ` A wall that kills the run off-boundary (the backstop hook unregistered, or a provider exhaustion kill mid-worker or mid-fold) routes to the maintenance decisions' 5h-wall arm: the arm records the wall and its reset-anchored one-shot carries the resume right after the reset. Under the kill-case arming route this Boundaries paragraph owns, the first capable turn after the reset arms from the lane's recorded quota evidence (a relayed quota reset notice included, carried by the lane's stop record or an operator or peer relay) when no standing carrier covers it; the kill case's arm slot keys on the wall notice's own reset instant, never the fresh probe's next-window reset; the coverage consult's scheduler-slot leg does not satisfy this route's coverage check, only a carrier carrying this lane's own marker does; and the arm's prompt carries the lane marker the coverage consult matches; a turn capable only after that slot has passed never arms a past instant (the runtime's silent year-roll): it checks the lane live (a live lane session ends the duty as already resumed) and otherwise leaves the resume to the first fresh-probe boundary after the reset, recording the wall evidence in its decision_reason.`

- [x] Apply T1 spans 1, 2, 3 and 5 to `agents/skills/maintenance/decisions.md` by mechanical extraction with exact-match assertions; the byte ledger holds (inserted minus deleted at most 210 net bytes in that file; re-bounded to the spans' true figure, 99933 absolute with ceiling headroom verified) [class: IMPLEMENTATION_REQUIRED]
- [x] Apply T1 span 4 to `agents/skills/plans/budget-gate.md` by mechanical extraction with an exact-match assertion [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: T1 gates A, B, D, E read 0 and gate C reads 1 before the edits [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: T1 gates A, B, D, E read 1, gate C reads 0 after the edits, and the byte-ledger check passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: route off-boundary quota kills in interactive lanes into the 5h-wall arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: route the cap parks through the self-heal consultation

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/plans/plan-quality-gate.md`
- `agents/skills/review-plan/SKILL.md`

Primary behavior owners: rules 16 and 17 of the Plan Quality Gate in `agents/skills/plans/plan-quality-gate.md`, and the scope-and-complexity policy paragraph of `agents/skills/review-plan/SKILL.md` (that paragraph is the duty's owner; the plans rule beside the round-cap rule is its pinned mirror, per review-plan's own declaration).

Prescribed spans (exact; each is the line's final backtick pair, applied with an exact-match assertion on the anchor):

T2 span 1 (append to rule 16 after the anchor span "preserve any configured cap-closure terminal mechanics under their existing contract."): ` A cap-shaped stop or park routes through the Uncertain workflow stops duty before the stop is judged unrecoverable.`

T2 span 2 (insert into rule 17 between the anchor spans "an unattended lane parks and reports)" and " before another full-panel round launches"): `, the park recorded only after one self-heal consultation for a non-user-only blocker per the maintenance decisions' non-user-only blocker line`

T2 span 3 (append to `agents/skills/review-plan/SKILL.md` at the end of the physical line carrying "Cap alone does not trigger reconciliation."): ` A park under these stop conditions routes through the plans skill's Uncertain workflow stops duty before the park is recorded.`

- [x] Apply T2 spans 1 and 2 to `agents/skills/plans/plan-quality-gate.md` and T2 span 3 to `agents/skills/review-plan/SKILL.md` by mechanical extraction with exact-match assertions on the anchors; rule 17 stays one sentence ending at its original period [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: T2 gates A, B, C read 0 before the edits [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: T2 gates A, B, C read 1 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `feat: route review-loop parks through the self-heal consultation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: give the review-side worker templates the liveness contract

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/execute-plan/phase-3-review.md`
- `agents/skills/execute-plan/invocation-and-orchestration.md`
- `agents/skills/execute-plan/agent-logs.md`

Primary behavior owners: the worker-prompt paragraph in review-plan Step 2 (`agents/skills/review-plan/SKILL.md`), the two fenced worker templates in `agents/skills/execute-plan/subagent-prompts.md`, the Launch accounting section of `agents/skills/review-agents/review-panel-selection.md`, and the log-ownership sentences in `agents/skills/execute-plan/phase-3-review.md`, `agents/skills/execute-plan/invocation-and-orchestration.md`, and `agents/skills/execute-plan/agent-logs.md`.

Prescribed spans (exact; each is the line's final backtick pair, applied with an exact-match assertion on the anchor):

T3 span 1 (append to the worker-prompt paragraph after the anchor span "never a widening of an existing worker's prompt."): ` Each brief is bounded to a one-pass slice a worker can finish inside the runtime's worker-inactivity window; silence past that window is the dead-leg procedure's trigger, never left running.`

T3 span 2 (insert as a new line in the Review lens worker template after the anchor line "Base: <BASE_BRANCH>"): `Log: the emit-early path the parent names in this prompt (a per-worker path, never the Phase 3 review log); append verified-so-far findings to it before each deep verification pass, so a cut-off leg leaves recoverable output`

T3 span 3 (insert as a new line in the Intermediate task review worker template after the unique anchor line "Worker lens: <INTER_REVIEW_WORKER>"): `Log: the emit-early path the parent names in this prompt (a per-worker path, never the Phase 3 review log); append verified-so-far findings to it before each deep verification pass, so a cut-off leg leaves recoverable output`

T3 span 5 (replace the anchor span "lens workers get no log paths." in `agents/skills/execute-plan/phase-3-review.md`): `lens workers get no log paths of their own; an emit-early path the parent names for the liveness duty is the one exception, written before each deep verification pass. The parent names one emit-early path per review worker when the round launches, a per-worker file distinct from the Phase 3 review log.`

T3 span 6 (replace the anchor span "Phase 3 review lens workers return findings to the parent and do not own per-lens log paths." in `agents/skills/execute-plan/invocation-and-orchestration.md`): `Phase 3 review lens workers return findings to the parent and do not own per-lens log paths; an emit-early path the parent names for the liveness duty is the one exception, written before each deep verification pass.`

T3 span 8 (replace the anchor span "For Phase 3 lens workers, do not assign per-lens log paths." in `agents/skills/execute-plan/invocation-and-orchestration.md`): `For Phase 3 lens workers, assign no per-lens log path except the emit-early path the parent names for the liveness duty.`

T3 span 7 (replace the anchor span "Lens workers do not own a log path." in `agents/skills/execute-plan/agent-logs.md`): `Lens workers do not own a log path of their own; an emit-early path the parent names for the liveness duty (append verified-so-far findings before each deep verification pass) is the one exception.`

T3 span 9 (replace the anchor span "Phase 3 lens workers have no log path and return findings only. Step 1.2b intermediate review workers likewise have no log path and return findings only; the parent appends their pass to `task-<N>-review.log.md`." in `agents/skills/execute-plan/agent-logs.md`): `Phase 3 lens workers and Step 1.2b intermediate review workers own no log path of their own and return findings only; an emit-early path the parent names for the liveness duty (append verified-so-far findings before each deep verification pass) is the one exception. The parent appends their pass to the per-task intermediate review log.`

T3 span 4 (insert as one new paragraph immediately before the anchor line "## Focused panels" in `agents/skills/review-agents/review-panel-selection.md`, closing the Launch accounting section; the anchor matches by whole-line equality, the heading line only, never the backticked prose reference of the heading later in the file): `A worker death inside a round is a dead leg, not a panel failure: inventory the dead leg's partial disk effects (records written, commits made) before any relaunch, relaunch only the missing panel member, and never the whole panel; the declared-dead worker is not awaited, and a silent worker past the runtime's worker-inactivity window counts as dead at the next parent check. The recovery runs through the reserved-slot precedence's replacement-focused-round regime (an in-round retry proceeds only while more than one launch slot remains), never as a fresh arming of the whole panel; a relaunch names a fresh emit-early path, never the dead leg's.`

- [x] Apply T3 span 1 to `agents/skills/review-plan/SKILL.md` by mechanical extraction with an exact-match assertion [class: IMPLEMENTATION_REQUIRED]
- [x] Apply T3 spans 2 and 3 to `agents/skills/execute-plan/subagent-prompts.md` and T3 spans 5, 6, 7, 8, 9 to the log-ownership sentences by mechanical extraction with exact-match assertions; both templates keep their fenced bodies closed by the same fence count [class: IMPLEMENTATION_REQUIRED]
- [x] Apply T3 span 4 to `agents/skills/review-agents/review-panel-selection.md` by mechanical extraction with an exact-match assertion [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: T3 gates A, B, C, E1, E2, E3 read 0 before the edits [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: T3 gate A reads 1, gate B reads 2, gate C reads 1, gates E1 and E2 read 2, gate E3 reads 2 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `feat: add the liveness contract to review-side worker templates` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-13-interactive-lane-quota-wall-resume-arm.md: covered by Task 1 (the decisions bullet's key extension plus the budget-gate kill-case route, executed and gate-verified).
- docs/history/backlog/2026-11-13-lane-park-arm-self-heal-consult-pointer.md: covered by Task 2 (rule 16/17 pointers and the review-plan mirror pointer).
- docs/history/backlog/2026-11-12-review-worker-dead-leg-brief-liveness.md: covered by Task 3 (one-pass brief bound, emit-early contract across the three log-ownership homes, dead-leg procedure beside Launch accounting).
Deferred residual: concurrency#undeclared-lane-liveness-instrument (r6 certification Low, hypothesis; recorded in the r6 record pair).
