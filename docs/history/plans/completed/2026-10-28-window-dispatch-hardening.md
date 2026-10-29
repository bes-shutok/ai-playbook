# Plan: Window dispatch hardening (stop-before-exhaustion, distribution cap 3, effort carve-out)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-28-stop-before-exhaustion-enforcement.md
- docs/history/backlog/2026-10-28-window-distribution-parallel-cap.md
- docs/history/backlog/2026-10-28-child-effort-policy-clocked-gap.md

```toml
date = "2026-10-28"
backlog_origins = [
  "docs/history/backlog/2026-10-28-stop-before-exhaustion-enforcement.md",
  "docs/history/backlog/2026-10-28-window-distribution-parallel-cap.md",
  "docs/history/backlog/2026-10-28-child-effort-policy-clocked-gap.md",
]
driving_force = "automation + efficiency"
execution_budget = "2.25 hours"
review_full_panel_rounds = "2"
```

Driving force: automation + efficiency (ranked primary + secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-10-28-plan-review-window-dispatch-hardening-p39bd49ba-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.25h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-28-stop-before-exhaustion-enforcement.md (session 95cf45b85a43da04e42c337127c8400a0117268a7588758078a7a81c64e03e30)

## Terms

- **Window**: the account's 5-hour GLM quota window; the probe's binding limit is the earliest-resetting one.
- **Probe**: a run of `scripts/quota_window_probe.py`; the report carries per-limit `used_percent` and names the binding window.
- **Quota leg**: the maintenance skill's Step 4 module section (`agents/skills/maintenance/quota-policy.md`) that owns probe, fire-time, and pause semantics; where the runtime overlay's pause vocabulary is cited, zcode.md's same-named section that quota-policy.md defers the naming to (the secondary-binding report-only defer rule lives there).
- **Fresh probe**: a probe executed at the consuming boundary or since the previous boundary; a reading from before the previous boundary, or older than one cadence period (2 hours), is never fresh.
- **Stop threshold**: primary-window `used_percent` at or above 95 (the operator's stop-while-remaining-drops-below-about-5-percent doctrine, 2026-10-12); a secondary-binding reading follows the Quota leg's existing report-only rule.
- **Paying fold**: the in-place rewrite of an existing sentence that carries a new duty without adding a parallel sentence (the anti-growth pay-for-growth discipline applied to one sentence).
- **Witness bar**: the evidence standard a machinery addition must meet for admission (a recorded incident, a red test, or an explicit user decision, per the Machinery admission protocol).
- **Hard park arm**: the duty converting a stop-threshold reading into an immediate park of the remaining mandate through the existing budget_pause machinery, with a timed resume at window start.
- **budget_pause**: the existing pause record and resume machinery (the plans and execute-plan budget gates; the quota leg's pause vocabulary).
- **Reason token**: the recorded `stop-before-exhaustion` value on a park record, distinguishing an enforcement park from a stranding.
- **Fleet cap**: the guards Step 2 repo-wide live-children count bound (was 4, becomes 3).
- **Distribution rule**: the Step 5 fire-time clause spreading armed child fires across the window by a 30-minute minimum spacing.
- **Effort pairing**: the Child model and effort policy mapping work class, lane, and mode to effort level (authoring High; exec-lane routine scheduled plan execution Low; EXEC-PROMPTS/ad-hoc execution High; dual-mode per-lane defaults unchanged).
- **Effort-naming arm**: the pairing section's runtime-limitation sentence (the deciding turn names the required model/effort in its turn output when a dispatch deviates from the host default).
- **Dispatch slice**: scheduling.md Step 5's payload-assembly rule enumerating the blueprint's fills.
- **Effort pin**: the execution blueprint's directive line naming the child session's required effort, filled by the deciding turn per the pairing; successor payloads inherit the value.
- **EXEC-PROMPTS entry**: a ready execution item in `docs/history/backlog/EXEC-PROMPTS.md`, executed under the exec-mode selection rule's EXEC-PROMPTS leg (beside the Ad-hoc backlog arm).
- **Clocked dispatch**: a delay-scheduled automation child; its scheduling primitive carries no model/effort fields.
- **Dual-mode**: a session bound to both lanes; per-lane effort defaults per the Child model and effort policy.
- **Exec-mode**: a session bound to the execution lane.
- **Budget gates**: the plans and execute-plan percent-and-minutes pause gates whose budget_pause vocabulary the hard park arm extends.
- **Carrier**: an armed automation that fires a scheduler or resume turn.
- **Guard liveness ledger**: the catches-to-incidents ledger `scripts/gate_liveness_ledger.py` records.
- **D3**: the maintenance Step 3 lane no-op decision (schedule nothing for that lane, reason recorded in `decision_reason`).
- **Pick**: one D1-selected plan execution target in a session's mandate.
- **Lane**: the execution or authoring dispatch lane the guards count.
- **Mandate**: the queue of work a committed session still intends to run (for example an exec mandate with unstarted picks remaining).
- **Ad-hoc dispatch**: an in-session execution of a directly ad-hoc-eligible backlog item (the Ad-hoc backlog arm).
- **Execution blueprint**: the `<prompt for the scheduled session>` payload template in `agents/skills/maintenance/template-execution.md`.

## Why

Sessions routinely exhaust their token budget mid-run because nothing re-reads the quota probe after the dispatch-time read, while fire times stack at the earliest legal slot and every clocked child inherits the host-default effort. The operator asked on 2026-10-28 for enforced stops before exhaustion, a deliberately filled window with at most 3 parallel sessions, and High effort for authoring and EXEC-PROMPTS work.

## Gist & Examples

TLDR: the maintenance dispatch lane gains an enforced stop-before-exhaustion arm, a window-distribution rule with a parallel ceiling of 3, and an EXEC-PROMPTS/High effort carve-out, so the loop parks before exhaustion and fills the 5h window deliberately instead of dying mid-run (automation + efficiency).

Before: five user-directed one-shots stacked between 00:21 and 05:22 local (2026-10-27/28); sessions died mid-run at token exhaustion, before or during payload work (the 2026-10-24 pick-2 resume holder, the 2026-10-27 21:00 carrier, the 19:53 carrier); EXEC-PROMPTS/ad-hoc runs are in-session, so their effort was the deciding session's launch-fixed pairing (exec-mode Low) and no surface named the High pairing the operator asked for.
After: a session about to start a new pick, lane decision, or EXEC-PROMPTS item transition (authoring phases and review rounds ride the budget gates' own probes) reads a fresh probe first and parks the remaining mandate at the stop threshold (timed resume at window start, reason token recorded); a new fire time sits at least 30 minutes after the last armed fire in its window; the live-children ceiling is 3; EXEC-PROMPTS/ad-hoc in-session runs carry the High pairing through the deciding turn's effort-naming arm (recorded at the boundary; binding where the runtime exposes an effort control), and execution-child scheduled payloads carry an effort directive filled per pairing (Low for exec-mode routine plan targets, High for dual-mode routine targets whose per-lane default is unchanged).

## Outcome

The maintenance dispatch lane stops, spreads, and effort-matches its children by rule instead of by accident.

- A session committed to new work reads a fresh probe at the boundary and parks the remaining mandate at the stop threshold, resuming at window start, so dispatch work stops before exhaustion instead of dying mid-run (review rounds keep riding the budget gates' own pauses).
- Armed child fires spread across the window and never more than 3 children run live.
- EXEC-PROMPTS/ad-hoc executions carry the High pairing through the deciding turn's effort-naming arm, execution-child scheduled payloads carry an explicit effort directive filled per pairing, and the pairing is written in one home.

Gate delta: +1 pause/refusal path (the hard park arm: a prose-only duty plus a condition that halts dispatch and later work, bound to the maintenance-owned boundaries the budget gates do not already cover, Task 1); +1 prose-only distribution constraint on fire times whose spacing violation resolves the lane to D3 (Task 2); 1 existing bound retightened in place (fleet cap value 4 to 3, same counting arms, no new check, Task 2); 1 existing conservation rule reshaped in place (probe once-per-turn becomes boundary-scoped sharing across its restatements, Task 1); +1 prose-only effort-pairing carve-out and template placeholder, the mode-coupled pairing sentence rewritten in place as the paying fold (Task 3); removals: none; the prose additions fold into existing sentences rather than parallel bullets (the cadence duty extends the Quota leg's probe sentence, the distribution rule extends scheduling.md's final-fire-time bullet, the carve-out rewrites the pairing sentence in place). Admission (Machinery admission protocol): the park arm's expected catch frequency is every post-90-percent mandate boundary under the witnessed 2026-10-24/28 exhaustion rate, its false-positive cost is one window of idle automation on a mis-read probe, and it is reviewed at the first false park or after one month of operation, whichever comes first; the distribution constraint and the ceiling carry the same review date. Pricing: the park arm's witness bar is met by recorded completed-integrity failures (the quota-dead sessions the origin row cites); the distribution and ceiling changes cite the witnessed five-carrier stacking; the effort carve-out cites the operator ask and the 22:00 run's unset effort. Byte-budget posture: decisions.md, guards.md, state-file.md, and survey-arms.md already sit over their advisory Part 4 targets at baseline; the additions ride the paying folds with no parallel text, and the advisory --check line is recorded at execution without raising any cap. Guard liveness ledger at authoring time: TOTAL catches=29 incidents=48, ratio 29:48.

## Assumptions

- assume one plan covers all three origins with tasks in urgency order; basis: user selection, AskUserQuestion, 2026-10-28.
- assume event-based probe cadence (each lane decision, new pick, authoring phase, review round), no staleness timer, with one backstop: a read older than one cadence period (2 hours) never counts as fresh, adopting the origin row's staleness bound; basis: simpler-design check plus the r3 freshness reconciliation.
- assume stop threshold binding-window `used_percent` at or above 95; basis: operator correction 2026-10-12 and the probe's `used_percent` contract.
- assume the park arm reuses budget_pause with a timed resume at window start; basis: the machinery exists and the origin row forbids a new state file.
- assume 30-minute minimum spacing between armed child fire times in one window; basis: 5h window with observed 1-4h runs and ceiling 3; an adjustable parameter, cheap to correct.
- assume effort enforcement rides the template pin plus the pairing text, upgrading to runtime fields if the clocked primitive exposes them; basis: the verified CronCreate limitation and the origin row's either-or outcome wording.
- assume the ceiling change edits the fleet cap value with unchanged counting arms; basis: the origin row's expected outcome.
- assume the hard park arm binds the maintenance-owned boundaries (lane decisions, mandate picks, EXEC-PROMPTS item transitions); authoring phases and review rounds already run the budget gates' own probes and pause at the gates' stricter threshold first (the 90 default sits below the 95 stop threshold); basis: r1 finding F1; retuning the budget gates' shared facts knob to 95 would loosen authoring-side pauses, so the arm adds coverage instead of moving the knob.
- assume the effort carve-out is exec-lane-scoped: exec-mode routine scheduled plan executions pair to Low; dual-mode per-lane defaults are unchanged (dual-mode routine dispatches pair High per their default); EXEC-PROMPTS/ad-hoc runs are in-session, so their High pairing rides the deciding turn's effort-naming arm rather than a payload pin; basis: r2 findings (the carriage-surface and dual-default reconciliations); the origin ask is framed in exec-mode terms.
- assume the effort pin reaches the scheduled payload carriers (execution, unblock, and authoring dispatch-outs) and the idle-time dispatch legs: the idle leg consumes the same dispatch-slice payload (scheduling.md's idle fill sentence), so the deciding turn fills the effort fill for idle dispatches per the pairing; the idle lane's model/effort binding rides the primitive's native fields per Child model and effort policy; basis: the shared dispatch-slice payload and that policy of record.

Decision points requiring a grill: plan topology resolved, one combined plan with three urgency-ordered tasks; user selection, AskUserQuestion, 2026-10-28; affects plan scope and task ordering.

## Standing constraints

- Skill-text anti-growth rules (repository AGENTS.md) bind every edit: land the rule, not the story; each origin row is cited in operative text at most one line; name the home or the absence when adding a rule.
- Module discipline: the maintenance modules are extracted whole-section units with byte-verbatim headings; extend existing bullets or add sub-bullets inside the owning section; do not rename or reorder existing headings (the router references them).
- Tool-agnostic wording per the Skill Design Guidelines: describe behavior by intent, never by tool-specific names.
- Every changed file carries no em dashes and passes the public hygiene scan at execution time.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each new duty homes in the module its router step already loads; vocabulary matches existing surfaces (`used_percent`, budget_pause, `decision_reason`, `children[]`); no duplicate or contradictory rule homes.
- maintainability: no witness narratives in operative text; each origin row cited at most one line.
- verifiability: every duty has a checkable witness (a distinctive quoted span grep, the cap value, the spacing number, the placeholder name).

**Done when:**
- quota-policy.md carries the in-run cadence duty and the hard park arm; template-execution.md carries the child-side per-pick and successor-dispatch duty; state-file.md documents the reason token; zcode.md's Quota leg names the new pause.
- scheduling.md carries the distribution rule; guards.md fleet cap reads 3; a repo-wide sweep finds no operative statement of the 4-children bound outside dated historical citations (guards.md, zcode.md, SKILL.md, and README.md's operative sentences all restated to the 3 ceiling; the supersession chain's dated quotes stay).
- zcode.md's pairing section carries the EXEC-PROMPTS/ad-hoc High carve-out; the execution blueprint carries the effort pin filled per pairing and enumerated as the dispatch slice's third fill; the unblock and authoring dispatch payloads carry the same pin.
- The hygiene scan passes over the changed set; all three origin rows are deleted in the completion fold.

**Ship when:**
Over subsequent scheduled runs the operator observes fires spread across the window, never more than 3 live children, and sessions parking with the reason token instead of dying mid-run. [class: OPERATIONS_FOLLOW_UP] Closes when observed across five scheduled runs or one week of operation, whichever comes first; evidence owner: the operator.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/quota-policy.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1, Task 3)
- `agents/skills/maintenance/state-file.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1, Task 2; the D2 probe-once and survey-start snapshot sentences; the D1 exemption enumeration)
- `agents/skills/maintenance/survey-arms.md` (Task 1; the Quota snapshot bullet's probe-once sentence and its verbatim cross-reference)
- `agents/skills/maintenance/zcode.md` (Task 1, Task 2, Task 3)
- `agents/skills/maintenance/scheduling.md` (Task 2, Task 3)
- `agents/skills/maintenance/guards.md` (Task 1, Task 2; the User-directed override rule's deferral-class trip enumeration in Task 1)
- `agents/skills/maintenance/SKILL.md` (Task 2; the Invariants fleet-cap bullet and the execution-lane stance section's operative sentences; the supersession chain's dated citations stay intact)
- `README.md` (Task 2; the maintenance catalog row's fleet-cap sentence)
- `scripts/check_maintenance_pins.sh` (Task 1 constraint on the count pin and the Step 3 quota needles; Task 2 the execution-lane stance span pin restated; Task 3 the two placeholder-set pins restated and the pairing-marker pin preserved)
- `agents/skills/maintenance/template-unblock.md` (Task 3; the unblock dispatch payload's effort directive line)
- `agents/skills/maintenance/template-authoring.md` (Task 3; the authoring dispatch-out payload's effort directive line)
- `agents/skills/maintenance/templates-CHANGELOG.md` (Task 3; the dated deviation entry for the blueprint effort-directive addition)
- `agents/skills/maintenance/CHANGELOG.md` (Task 3; the Revisions ledger entry for the blueprint change class)

**Tests:**
- none planned; verification is grep and hygiene based over the changed set; execution discovers validator coverage from repository evidence

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; lessons are captured by the learn flow, not by this plan
- sibling 2026-10-28 backlog rows (rebind-*, clocked-order, closeout-migrate); separate origins owned by other sessions

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
# Task 1 obligations (new-duty positive spans absent at baseline; the preservation literals `never blocks scheduling` and `binds every clocked child dispatch, from any session type` are present at baseline by design; the inverted checks fail on presence; fail closed throughout)
grep -q "fresh probe" agents/skills/maintenance/quota-policy.md || { echo "FAIL: in-run cadence duty missing"; exit 1; }
grep -q "binds every clocked child dispatch, from any session type" agents/skills/maintenance/quota-policy.md || { echo "FAIL: quota leg opening pin lost"; exit 1; }
grep -q "stop-before-exhaustion" agents/skills/maintenance/quota-policy.md || { echo "FAIL: park arm token missing"; exit 1; }
grep -q "at or above 95" agents/skills/maintenance/quota-policy.md || { echo "FAIL: stop threshold missing"; exit 1; }
sed -n '/<prompt for the scheduled session>/,/<\/prompt>/p' agents/skills/maintenance/template-execution.md | grep -q "fresh probe" || { echo "FAIL: child-side cadence duty missing inside the payload block"; exit 1; }
grep -q "stop-before-exhaustion" agents/skills/maintenance/state-file.md || { echo "FAIL: reason token undocumented"; exit 1; }
grep -q "stop-threshold park" agents/skills/maintenance/zcode.md || { echo "FAIL: quota leg pause naming missing"; exit 1; }
if grep -q "one invocation per turn" agents/skills/maintenance/quota-policy.md; then echo "FAIL: once-per-turn pin survives"; exit 1; fi
if grep -q "the probe runs once per turn" agents/skills/maintenance/quota-policy.md; then echo "FAIL: once-per-turn lead clause survives"; exit 1; fi
if grep -q "never a second probe run" agents/skills/maintenance/quota-policy.md; then echo "FAIL: sharing sentence pin survives"; exit 1; fi
if grep -q "not already run the probe" agents/skills/maintenance/zcode.md; then echo "FAIL: ladder once-per-turn pin survives"; exit 1; fi
if grep -q "already run the window probe" agents/skills/maintenance/decisions.md; then echo "FAIL: decisions.md once-per-turn pin survives"; exit 1; fi
if grep -q "taken at survey start" agents/skills/maintenance/decisions.md; then echo "FAIL: survey-start snapshot pin survives"; exit 1; fi
if grep -q "stay verbatim" agents/skills/maintenance/survey-arms.md; then echo "FAIL: survey-arms verbatim pin survives"; exit 1; fi
grep -q "never blocks scheduling" agents/skills/maintenance/quota-policy.md || { echo "FAIL: dead-probe posture literal lost"; exit 1; }
grep -q "stop-threshold park" agents/skills/maintenance/guards.md || { echo "FAIL: override enumeration park missing"; exit 1; }
grep -q "stop-threshold park" agents/skills/maintenance/decisions.md || { echo "FAIL: D3 mirror park missing"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins suite broken by a Task 1 amend"; exit 1; }
# Task 2 obligations
grep -q "reaches 3" agents/skills/maintenance/guards.md || { echo "FAIL: fleet cap ceiling not 3"; exit 1; }
if grep -q "reaches 4" agents/skills/maintenance/guards.md; then echo "FAIL: stale 4-children bound"; exit 1; fi
if grep -q "cap of four" agents/skills/maintenance/guards.md; then echo "FAIL: stale guards.md bound sentence"; exit 1; fi
if grep -q "capped at four" agents/skills/maintenance/zcode.md; then echo "FAIL: stale zcode.md bound sentence"; exit 1; fi
if grep -q "at most 4 concurrent" agents/skills/maintenance/SKILL.md; then echo "FAIL: stale SKILL.md invariant bound"; exit 1; fi
if grep -q "now read: up to four" agents/skills/maintenance/SKILL.md; then echo "FAIL: stale SKILL.md stance bound"; exit 1; fi
if grep -q "fleet cap of four" README.md; then echo "FAIL: stale README.md bound"; exit 1; fi
tr '\n' ' ' < agents/skills/maintenance/scheduling.md | tr -s ' ' | grep -q "at least 30 minutes after the last armed fire" || { echo "FAIL: distribution rule missing"; exit 1; }
grep -q "distribution-spacing" agents/skills/maintenance/decisions.md || { echo "FAIL: D1 spacing exemption missing"; exit 1; }
grep -q "automation listing" agents/skills/maintenance/scheduling.md || { echo "FAIL: deconfliction discovery surface missing"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins suite broken by an amend"; exit 1; }
# Task 3 obligations
grep -q "EXEC-PROMPTS execution pairs to High effort" agents/skills/maintenance/zcode.md || { echo "FAIL: effort carve-out missing"; exit 1; }
grep -F -q "{EFFORT_DIRECTIVE}" agents/skills/maintenance/template-execution.md || { echo "FAIL: effort pin placeholder missing"; exit 1; }
grep -F -q "{EFFORT_DIRECTIVE}" agents/skills/maintenance/scheduling.md || { echo "FAIL: dispatch slice third fill missing"; exit 1; }
grep -F -q "{EFFORT_DIRECTIVE}" agents/skills/maintenance/template-unblock.md || { echo "FAIL: unblock payload effort pin missing"; exit 1; }
grep -F -q "{EFFORT_DIRECTIVE}" agents/skills/maintenance/template-authoring.md || { echo "FAIL: authoring payload effort pin missing"; exit 1; }
grep -q "supersede the template pin" agents/skills/maintenance/zcode.md || { echo "FAIL: once-exposed supersession missing"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins suite broken by a Task 3 amend"; exit 1; }
python3 scripts/skill_text_budget.py --check || { echo "FAIL: byte-budget gate tool error"; exit 1; }
# hygiene over the tree, the changed set included
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh || { echo "FAIL: hygiene scan"; exit 1; }
```

### Task 1: Stop-before-exhaustion enforcement (in-run probe cadence, hard park arm, reason token)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/quota-policy.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/zcode.md` (Quota leg section and the Child dispatch ladder's probe-read sentence)
- `agents/skills/maintenance/guards.md` (the User-directed override rule's deferral-class trip enumeration)
- `agents/skills/maintenance/decisions.md` (the D2 probe-once sentence, the D1 near-reset snapshot pin `taken at survey start`, and the D3 mirror)
- `agents/skills/maintenance/survey-arms.md` (the Quota snapshot bullet's probe-once sentence and its `stay verbatim` cross-reference)
- `scripts/check_maintenance_pins.sh` (run at the Task 1 boundary; the State file region's exactly-2 `execute|author|audit|retriage` count pin constrains how the token documentation may restate the kind enum; the Step 3 quota needles constrain the decisions.md amendment to the snapshot-basis clause, preserving `D1 defers the execution dispatch past the reset and D2 defers the authoring dispatch` and `must cite an explicit non-quota reason` verbatim)

Primary class anchors: `Step 4: quota leg` in `agents/skills/maintenance/quota-policy.md`; `Execution child (execute-plan skill)` in `agents/skills/maintenance/template-execution.md`; `Quota leg` in `agents/skills/maintenance/zcode.md`; `Step 6: state update` in `agents/skills/maintenance/state-file.md`.

- [x] quota-policy.md Quota leg carries the in-run cadence duty, pinned by `fresh probe`: at a maintenance-owned boundary (lane decision, mandate pick, EXEC-PROMPTS item transition) a deciding turn or execution child expects a fresh probe read before the work starts; a read since the previous boundary counts as fresh; a read older than 2 hours always re-runs the probe [class: IMPLEMENTATION_REQUIRED]
- [x] The duty excludes boundaries a budget gate already probes and single-homes the probe economy in the same edit, verified by the absence greps; the sites: `the probe runs once per turn` with its `never a second probe run` tail, the `one invocation per turn` parenthetical, and zcode.md's ladder sentence `not already run the probe` [class: IMPLEMENTATION_REQUIRED]
- [x] Covers decisions.md's `already run the window probe` sentence and its `taken at survey start` snapshot pin, and survey-arms.md's probe-once sentence with its `stay verbatim` cross-reference; the decisions.md reword preserves the near-reset comparison basis and start-offset exclusions or names their supersession [class: IMPLEMENTATION_REQUIRED]
- [x] The amendment re-homes the snapshot provenance siblings: state-file.md's `quota_at_decision` paragraph and zcode.md's Decision-time snapshot bullet point at the duty, freshness single-homed [class: IMPLEMENTATION_REQUIRED]
- [x] quota-policy.md carries the hard park arm: at a primary-binding `used_percent` at or above 95 (secondary-binding readings stay report-only per the defer rule), the remaining mandate parks via budget_pause, timed resume at window start, reason token `stop-before-exhaustion` on the park's existing surface, never a continuation [class: IMPLEMENTATION_REQUIRED]
- [x] Routing by remainder kind: parkable kinds (execute, author, audit, retriage) park on the pending_dispatch path (no new writer class or field); EXEC-PROMPTS/ad-hoc boundaries take the Ad-hoc arm's hold-with-recorded-reason vocabulary plus the boundary's budget_pause record, never a pending_dispatch write [class: IMPLEMENTATION_REQUIRED]
- [x] The pending_dispatch park write rides the successor duty's decision-first park-first shape, and state-file.md's writer enumeration names the stop-threshold trigger in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] The park is deferral-class: guards.md's override rule's deferral-class trip enumeration gains the stop-threshold park in the same edit, decisions.md's D3 mirror following; a user-directed override proceeds past it, unattended sessions park, operator-named dispatches keep their minute; zcode.md's Quota leg defer vocabulary lists the park [class: IMPLEMENTATION_REQUIRED]
- [x] state-file.md documents the `stop-before-exhaustion` token on the pending_dispatch park path per the writer enumeration (budget_pause records are named by reference to the Budget gate protocol's sink, never state-file surfaces): an enforcement park is distinguishable from a stranding by the token alone [class: IMPLEMENTATION_REQUIRED]
- [x] template-execution.md carries the child-side duty inside the `<prompt for the scheduled session>` payload block, pinned by `fresh probe`: an execution child between mandate picks or before a successor dispatch applies the same boundary probe and park arm; an unsupported harness proceeds under zcode.md's Unsupported-harness budget skip arm [class: IMPLEMENTATION_REQUIRED]
- [x] Same-sentence pins preserved verbatim: decisions.md's `the signal is derived at decision time` lead, guards.md's `like the authoring, audit, and re-triage kinds`, zcode.md's `authoring, audit, re-triage, ad-hoc, and execution children are fleet members` [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: a probe erroring or reporting unknown keeps the dead-probe posture (downgraded precision, never a block), the boundary recorded unknown, not skipped; pinned by `never blocks scheduling` remaining in quota-policy.md [class: REPOSITORY_TEST]
- [x] Run the Task 1 scoped Validation Commands greps → expect all pass [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: enforce stop-before-exhaustion probe cadence and hard park arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Window distribution rule and parallel ceiling 3

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/zcode.md` (Scheduling primitives section, markers bullet)
- `agents/skills/maintenance/SKILL.md` (Invariants fleet-cap bullet and the execution-lane stance section's operative sentences)
- `README.md` (maintenance catalog row's fleet-cap sentence)
- `scripts/check_maintenance_pins.sh` (the execution-lane stance span pin restated to the new wording in the same edit)
- `agents/skills/maintenance/decisions.md` (the D1 dispatch-defect exemption enumeration gains the spacing reason)

Primary class anchors: `Step 5: scheduling` in `agents/skills/maintenance/scheduling.md`; `Fleet cap` in `agents/skills/maintenance/guards.md`; `Scheduling primitives` in `agents/skills/maintenance/zcode.md`; `Execution-lane concurrency stance (supersession chain)` in `agents/skills/maintenance/SKILL.md`.

- [x] scheduling.md Step 5 carries the distribution rule, pinned by the distinctive span `at least 30 minutes after the last armed fire`: given a final fire time chosen inside a window that already holds armed child fires, expects the new fire time at least 30 minutes after the last armed fire in that window, still subject to the 5-minute floor, the runtime-fit rule, and pricing deferral [class: IMPLEMENTATION_REQUIRED]
- [x] The spacing is evaluated on the final fire time after all deferral legs, and a spacing violation at that point resolves the lane to D3 (schedule nothing; the next turn re-decides against the updated armed-fire set) [class: IMPLEMENTATION_REQUIRED]
- [x] When consecutive turns dispatch children into the same window, their fire times spread across the window's remaining minutes with the 30-minute spacing as the floor, and an operator-named wall-clock minute keeps its requested minute (the order's fire stays at its requested minute, the existing exemption convention) [class: IMPLEMENTATION_REQUIRED]
- [x] Armed-fire discovery reads the two fire-time surfaces (the automation listing's armed child fire times, the state file's pending children[] fire times); the fleet cap's discovery arms stay counting context, never spacing inputs, and decisions.md's D1 dispatch-defect exemption enumeration gains the spacing reason (`distribution-spacing`) in the same edit so the D3 branch never trips the failure cap [class: IMPLEMENTATION_REQUIRED]
- [x] guards.md fleet cap ceiling changes 4 to 3 as the operative repo-wide live-children bound, same counting arms; the Fleet cap bullet's trip clause reads `reaches 3` after the edit, replacing `reaches 4`, preserving the bullet's pinned `execution children run in per-execution ad-hoc worktrees per the Worktree-first standard` span and zcode.md's pinned `execution children in their per-execution worktrees, P57` span [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep-edit every operative statement of the old bound, pinned by the spans `cap of four` (guards.md Fleet cap bullet's isolation sentence), `capped at four` (zcode.md markers bullet), `at most 4 concurrent` (SKILL.md Invariants fleet-cap bullet), `now read: up to four` (SKILL.md execution-lane stance closing), and `fleet cap of four` (README.md's maintenance catalog row): given the cap change landed, expects all five sites stating the 3 ceiling in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] The sweep leaves the SKILL.md supersession chain's dated citations intact (the 2026-09-23 directive quote and the REWORK entry's dated witness spans stay byte-verbatim) while restating the REWORK entry's present-tense policy sentence (the `repo-wide cap of four` span) to the 3 ceiling keeping its date, and restates the pins suite's execution-lane stance span pin to the new wording in `scripts/check_maintenance_pins.sh` so the suite stays green [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep: a repo-wide search over agents/ and docs/ maintenance surfaces for operative statements of the 4-children bound expects only historical or witness citations remaining [class: REPOSITORY_TEST]
- [x] Safety witness: given a foreign one-shot carrier the state file does not own (the witnessed stacking shape), expects the rule to name the automation listing arm as its discovery surface for deconfliction, never a claim of control over foreign carriers; pinned by the span `automation listing` adjacent to the spacing sentence in scheduling.md [class: REPOSITORY_TEST]
- [x] Run the Task 2 scoped Validation Commands greps → expect all pass [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: distribute child fires across the window and cap live children at 3` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Effort pairing carve-out and template effort pin

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md` (Child model and effort policy section)
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/scheduling.md` (dispatch slice, Unblock-dispatch slice, and Authoring slice fill enumerations)
- `agents/skills/maintenance/template-unblock.md` (the unblock dispatch payload gains the same effort directive line)
- `agents/skills/maintenance/template-authoring.md` (the authoring dispatch-out payload gains the same effort directive line)
- `agents/skills/maintenance/templates-CHANGELOG.md` (a dated deviation entry paraphrasing the effort-directive addition to the blueprints)
- `agents/skills/maintenance/CHANGELOG.md` (the module Revisions ledger entry for the blueprint change class)
- `scripts/check_maintenance_pins.sh` (the execution-blueprint placeholder-set pin and the authoring-body placeholder-set pin restated; the pairing-marker pin preserved)

Primary class anchors: `Child model and effort policy (2026-09-15, user request)` in `agents/skills/maintenance/zcode.md`; `Execution child (execute-plan skill)` in `agents/skills/maintenance/template-execution.md`; `Step 5: scheduling` in `agents/skills/maintenance/scheduling.md`.

- [x] zcode.md pairing section carries the carve-out by rewriting the existing mode-coupled sentence in place (the paying fold; no parallel sentence added), pinned by the distinctive span `EXEC-PROMPTS execution pairs to High effort`, preserving the `Mode-coupled effort pairing:` lead-in verbatim so the pins-suite marker pin holds [class: IMPLEMENTATION_REQUIRED]
- [x] The carve-out's pairing content: given an EXEC-PROMPTS or ad-hoc execution under the exec lane (the Ad-hoc backlog arm or the ready-EXEC-PROMPTS leg, both in-session runs), expects the High effort pairing carried by the deciding turn's existing effort-naming arm extended to in-session ad-hoc runs, with exec-mode routine scheduled plan executions paired Low and dual-mode per-lane defaults unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] template-execution.md execution blueprint carries an effort pin placeholder `{EFFORT_DIRECTIVE}` as a directive line inside the `<prompt for the scheduled session>` payload block (the legend block's `{EFFORT_DIRECTIVE}` line is its fill spec, never the placement), the deciding turn filling it per the pairing for scheduled payloads [class: IMPLEMENTATION_REQUIRED]
- [x] The pins suite's execution-blueprint placeholder-set pin is restated to the three-placeholder set, and the authoring-body placeholder-set pin (the `## Authoring child` span) to the four-placeholder set, in the same edit: given a filled dispatch payload, expects the directive naming the pairing result per its qualifiers (defaults: Low exec-mode routine, High dual-mode routine; escalation and simple-plan qualifiers unchanged) [class: IMPLEMENTATION_REQUIRED]
- [x] template-execution.md SUCCESSOR DISPATCH paragraph: the reshape leg's fill enumeration names `{EFFORT_DIRECTIVE}` as a third fill inherited from the run's own payload, and the delete-plus-create fallback carries the payload forward unchanged (it enumerates no fills; the child never re-derives the value from the pairing section, which is outside its load contract) [class: IMPLEMENTATION_REQUIRED]
- [x] The blueprint's placeholder legend block gains the matching `{EFFORT_DIRECTIVE}` line beside `{some_plan}`: given a successor-chained dispatch, expects the payload carrying the same explicit effort as a first-generation dispatch [class: IMPLEMENTATION_REQUIRED]
- [x] scheduling.md dispatch slice enumerates the third fill: given the assembly rule that fills `{REPO_ROOT}` and `{some_plan}`, expects `{EFFORT_DIRECTIVE}` named as a third fill the deciding turn sets per the pairing, with the slice's idle-time dispatch named as filling the same effort fill per the pairing beside its schedule_time idle literal [class: IMPLEMENTATION_REQUIRED]
- [x] scheduling.md Unblock-dispatch slice and both sibling blueprints carry the effort fill: given an unblock dispatch or a clocked authoring dispatch-out, expects the payload carrying the explicit effort per the pairing (the effort directive is the execution dispatch slice's third fill and an added by-name fill of the Unblock-dispatch and Authoring slices); both sibling blueprints' legend blocks gain the `{EFFORT_DIRECTIVE}` line [class: IMPLEMENTATION_REQUIRED]
- [x] The pairing section's once-exposed arm extends to the pin: given a clocked primitive that exposes model or effort fields, expects the fields to supersede the template pin [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 3 scoped Validation Commands greps → expect all pass [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: pair EXEC-PROMPTS and ad-hoc executions to High effort via template pin` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-28-stop-before-exhaustion-enforcement.md: covered by Task 1 (commit da67df988301d014945dee6442a247fc2a1dc404, the in-run fresh-probe cadence, the hard park arm at a primary-binding used_percent at or above 95, and the stop-before-exhaustion reason token).
- docs/history/backlog/2026-10-28-window-distribution-parallel-cap.md: covered by Task 2 (commit 275157ebda937e182e281479568279b9e5e64acc, the 30-minute distribution spacing rule and the fleet cap retightened from 4 to 3).
- docs/history/backlog/2026-10-28-child-effort-policy-clocked-gap.md: covered by Task 3 (commit 73dc82713585b5178ccd7bcae14d904c329c1d53, the EXEC-PROMPTS/ad-hoc High-effort pairing carve-out and the {EFFORT_DIRECTIVE} template pin across the three dispatch payloads).
