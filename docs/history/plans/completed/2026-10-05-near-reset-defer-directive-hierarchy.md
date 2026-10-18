# Plan: the quota near-reset defer yields to a live directive

Backlog origin: docs/history/backlog/2026-10-05-quota-near-reset-defer-outranks-live-directive.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-near-reset-defer-directive-hierarchy-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Near-reset branch: the Step 3 Quota-aware lane decisions paragraph's branch that defers a lane dispatch when minutes to reset is below the lane's expected runtime upper bound (execution 240 minutes, authoring 120 minutes, the Step 4 constants).
- Continue-loop condition: the Step 3 paragraph that is the condition's one home; its quota leg (leg (a)) decides whether the loop continues into the next lane decision, and its degradation arm reads the existing probe thresholds until the governor's pressure evaluator exists.
- Live directive: an operator order to continue the loop's work without stops, carried by any of three independent directive surfaces: a standing recorded directive whose text orders continuous repetition in the directives home (the D-4 row), the same continuity text in the loop_mode or authoring_cycle_gate directive field, or a live operator message in the current turn (the fields carry their own recorded wording, not a copy of the home row).
- Continuity phrasing: the reference set of wordings that make a directive's text order continuous repetition: "without stops", "one by one", "repeatedly", "continuously" (D-4's "one by one without stops" is the exemplar); a directive whose text scopes the order to a single completion never carries it.
- Covered lane: a lane whose dispatch the live directive's own text covers; D-4's recorded scope is the authoring lane, and a live message covers the lane it names or, when it names none, the lane the turn is deciding. When several surfaces carry covering text, the directives-home row is the witness of record, otherwise the state directive field, otherwise the live message.
- Dispatch-while-plausible: the degraded decision the near-reset branch makes for a covered lane: dispatch when the window fits a typical run by evidence; defer when it does not.
- Typical-run estimate: an evidence-based duration estimate for the specific decision, grounded in the at most five most recent completed same-lane runs in the state file's children[] outcome records (duration anchored at fire_at when set, otherwise created_at, the decision-time stamp, read to outcome_checked_at) weighed against the target's own declared scope (its task count and validation surface), the decision citing the specific records that grounded it; never above the lane's worst-case upper bound, which stays the ceiling; no completed same-lane record, or no scope-comparable read from the records, defers fail-closed.
- Integrity defers: the quota trips this plan preserves: the probe pause decision and the exhausted governor pressure class per the origin row's Expected block, and rate pressure, which is also carried in the User-directed override rule's never-overridable integrity list.
- Override token: the `near-reset-directive-override:<witness>` literal recorded in `decision_reason` when the carve-out fires, mirroring the `user-directed-override:<guard name>` token shape.
- Budget gate: the run-level quota-window pause and resume protocol (agents/skills/execute-plan/SKILL.md, mirrored at plan-authoring boundaries in the plans skill); it stays the boundary that observes mid-run exhaustion.
- Fresh-window rule: the Step 3 rule requiring a fresh-window D3 with dispatchable work to cite an explicit non-quota reason; unchanged by this plan.

## Why

The near-reset branch defers mechanically on a worst-case upper-bound comparison and sits outside both the deferral-class trip set and the integrity list, so no sanctioned route lets an explicit operator directive outrank it: the 2026-10-05 12:56 chaining re-run deferred with 115 minutes left against the 120-minute authoring bound, a five-minute shortfall against an estimate, while the operator's standing directive ordered continuous authoring one by one without stops, and the operator corrected the stop: a live order to continue repeatedly must not lose to a bound estimate. The daily 05:49 authoring cadence re-exposes the same defer on every fire until the ranking changes.

## Outcome

A covered lane's near-reset defer degrades to dispatch-while-plausible: the lane dispatches when the window fits a typical run by evidence and defers only on a genuine unusable-window reading (the ceiling, or no evidence-supported estimate fits), while every integrity defer, every uncovered lane, and the fresh-window rule stay byte-identical, and each fired carve-out records its override token in decision_reason.

- The near-reset branch gains the live-directive carve-out as inserted sentences after its existing defer text; the mechanical defer sentence carrying the pinned needle, the bias band, the sanctioned-exemption sentence, and the fresh-window rule are byte-untouched.
- The D2 (author) bullet's carrier-selection sentence (a different bullet of the same Step 3 decision region than the Quota-aware lane decisions paragraph) gains one reconciliation clause on its "near the pause thresholds" leg: for a covered lane it resolves to a dispatch carrier (in-session when the in-session leg's conditions hold, otherwise the idle-time queue) and never to its defer arm, recorded under the same override token; without it the witnessed defer would re-enter one site after the branch dispatches.
- The continue-loop condition's quota leg gains one inheritance sentence: its degradation arm reads the branch including the carve-out, so a chaining re-run under a covered directive continues while plausible and records the token.
- The Step 4 fire-time leg keeps its constants and rules (it owns clocked-slot fit at creation, a different boundary than the decision layer); the quota signal slug vocabulary is untouched (the slug keeps recording the near-reset observation; the override rides decision_reason); the User-directed override rule's deferral-class trip set is not extended; the state schema grows nothing.

Gate delta: one new decision arm inside an existing branch, restrictive in direction (it can only turn a defer into a dispatch, and only for a covered lane with evidence), one reconciliation clause in the carrier-selection sentence, one inheritance sentence in the condition's quota leg, and one new auditable decision_reason token. No new refusal class, no new state field, no new tool.

## Assumptions

- assume the carve-out's predicate reads the directive from three independent recorded surfaces (the directives home row, the loop_mode or authoring_cycle_gate directive field's own text, the turn's live message), decides coverage by the continuity-phrasing reference set plus the lane-naming test, and never adds a state field; basis: the directives home already records D-4 and the state fields already carry their own directive text (the live loop_mode text and the D-4 row differ in wording, so the surfaces are independent, not echoes).
- assume the three candidate mechanisms adjudicate as: arm 1 accepted (the live-directive carve-out), arm 3 folded into it (the typical-run evidence standard is the definition of "plausible", with the worst-case bound kept as the ceiling), arm 2 rejected as a new mechanism; basis: the Budget gate already owns mid-run exhaustion at the boundary that can observe it, which is arm 2's own rationale, so a pre-dispatch always-dispatch policy would only trade the auditable pre-dispatch defer for avoidable mid-run pause recovery.
- assume the typical-run estimate reads named records with a fail-closed floor rather than one rigid statistic; basis: the live children[] record set splits exactly on the witnessed decision (a clean 50-minute in-session run beside a 194-minute and an operator-pause-contaminated 339-minute run), so a fixed median re-defers the witnessed case, while a scope-comparable read over the recent completed runs grounds it; the created_at field is the decision time, so clocked children anchor at fire_at when set.
- assume the integrity defers are enumerated exhaustively as the probe pause decision, the exhausted governor pressure class, and rate pressure; basis: the origin row's Expected block for the first two and the User-directed override rule's never-overridable integrity list for rate pressure.
- assume the carve-out applies to unattended sessions when a standing directive covers the lane (the 05:49 children consume D-4) and keeps today's defer for uncovered lanes; basis: the dispatch entry's Urgency line (the cadence re-exposes the stop) and the dispatch entry's scoping sentence ("unattended lanes with no standing directive keep today's mechanical defer unchanged").
- assume the pinned Step 3 needles stay byte-intact through insert-after placement; basis: the pins suite asserts the defer sentence and the fresh-window needle inside the Step 3 region; anchors are re-derived from live bytes at execution and a moved needle re-keys its owning pin in the same edit.
- assume no scheduler-state selftest changes: the override token rides decision_reason free text exactly like the user-directed-override token; basis: no field shape grows.
- assume D-4's recorded lane scope is the authoring lane, so the witnessed stop's execution half (the fresh plan against the 240-minute bound) stays bound-governed; basis: the directives home's D-4 record scopes the directive to the authoring lane.
- assume the done and execute-plan queue-drain turn-end reporting bullets (naming "a quota pause or near-reset with the Budget gate") need no edit: they report turn-end reasons and stay true for uncovered lanes; basis: a reporting site, not a decision site.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the quota near-reset defer stops outranking an explicit operator order to continue; a code-quality re-ranking that degrades the bound comparison to dispatch-while-plausible for covered lanes, with every integrity defer and every uncovered lane unchanged.

Before (today): with 115 minutes left and a 120-minute authoring bound, the chaining re-run defers even though comparable authoring runs finish in well under the bound and the operator's standing directive says one by one without stops; the next cadence fire repeats the defer against a fresh but similar window.

After (this plan): the same decision reads the directive first. Covered lane: the decision cites the evidence (the recent completed same-lane runs it weighed, or the target's task count and validation surface), dispatches while the typical estimate fits the window, resolves the carrier-selection's near-thresholds leg to a dispatch carrier, and records `near-reset-directive-override:D-4` (or `:loop_mode`, `:authoring_cycle_gate`, or `:live operator message` per the witness precedence). Uncovered lane: byte-identical defer. A probe pause decision, an exhausted governor class, or rate pressure defers whatever the directive says.

Edge cases pinned: a window below every evidence-supported estimate defers under the carve-out; a typical estimate at or above the bound defers (the bound stays the ceiling); no completed same-lane record, or no scope-comparable read from the records, defers fail-closed; a directive whose text scopes the order to a single completion (a one-shot ask) never carries a continuity phrasing and never covers a lane; when several surfaces carry covering text, the directives-home row is the witness of record, otherwise the state directive field, otherwise the live message; the percent-based scarcity legs (probe-scarce readings, the primitive-selection max-percent threshold) are not touched by the carve-out, which re-ranks only the minutes-bound comparison and the carrier-selection's near-thresholds leg; the fresh-window rule's non-quota-reason duty still applies to a fresh-window D3; the 120-240 minute per-lane bias band is unchanged for uncovered lanes and the carve-out applies per covered lane inside it; a covered lane whose dispatch then trips a guard defers on that guard as today.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the carve-out fires only for a covered lane (continuity phrasing plus lane naming) with an evidence-supported typical estimate inside the window, and the covered lane's carrier selection resolves to a dispatch carrier under the same token; every integrity defer and every uncovered lane behaves byte-identically to today; the pinned needles and the slug vocabulary are byte-intact.
- fail-closed placement: missing evidence defers; the ceiling and bound arms defer; nothing in this plan can convert a defer into a dispatch without both the covering directive and the evidence.
- observability: every fired carve-out records `near-reset-directive-override:<witness>` in decision_reason beside the lane's quota_at_decision record, so the ranking override stays auditable per decision.
- maintainability: one home per site (the branch owns the carve-out; the condition's quota leg owns one inheritance sentence), no trip-set vocabulary duplication, no new state field, no new tool.

**Done when:**
- all task boxes checked; the pins suite exits 0 (OUTCOME: pass); the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-near-reset-defer-directive-hierarchy.md` exits 0 on the final bytes.

**Ship when:**
- a near-reset decision under the standing D-4 directive (or a live continue message) dispatches while plausible with the override token recorded, and an uncovered lane or an integrity trip defers unchanged in the same machinery.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (the Quota-aware lane decisions paragraph's near-reset branch span; the D2 (author) bullet's carrier-selection sentence's near-thresholds leg span in the same Step 3 decision region; the continue-loop condition paragraph's quota leg span)

**Tests:**
- `scripts/check_maintenance_pins.sh` (only if a re-derived anchor forces a pin re-key, in the same edit as the span move)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- the Step 4 fire-time leg and its zcode.md runtime-fit rule: the clocked-slot constants and rules stay unchanged (a different boundary than the decision layer).
- the User-directed override rule's deferral-class trip set and the quota signal slug vocabulary: neither grows.
- `docs/maintenance/operator-directives.md`: the directives home is read, never rewritten, by this plan.
- the percent-based scarcity legs (probe-scarce readings, the primitive-selection max-percent threshold): the witnessed defect is the minutes-bound comparison and its carrier-selection leg only.
- the state schema, and every script except the pins suite's conditional re-key named under Tests: no field grows, no tool changes.

## Validation Commands

```bash
# Pins: the authoritative mechanical check over the edited Step 3 spans
# (anchors re-derived from live bytes first; a moved needle re-keys its pin
# in the same edit)
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews, green from r1 on
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-near-reset-defer-directive-hierarchy.md
```

### Task 1: Near-reset branch live-directive carve-out

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh` (conditional, pin re-key only)

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the pinned-needles-intact criterion
- `grep -c "near-reset-directive-override" agents/skills/maintenance/SKILL.md`; covers the token presence (RED at authoring: zero hits)
- `grep -c "dispatch-while-plausible" agents/skills/maintenance/SKILL.md`; covers the degraded-decision naming (RED at authoring: zero hits)
- `grep -c "continuity phrasing" agents/skills/maintenance/SKILL.md`; covers the coverage-test naming (RED at authoring: zero hits)

- [x] Re-derive the anchors from live bytes: the near-reset branch sentences inside the Quota-aware lane decisions paragraph (the defer sentence carrying the pinned needle "D1 defers the execution dispatch past the reset and D2 defers the authoring dispatch", the bias-band sentence, the sanctioned-exemption sentence, the fresh-window rule), the carrier-selection sentence in the D2 (author) bullet of the same Step 3 decision region (the sentence carrying "resolves to the idle-time queue or defers the lane"), and the pins suite's Step 3 needle list; if any anchor moved from the bytes this plan quotes, update the owning pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Insert the carve-out sentences into the near-reset branch after the "re-decides on a later turn from the fresh post-reset snapshot" sentence and before the Fresh-window rule, keeping every existing sentence byte-intact, covering: the predicate (three independent directive surfaces: a standing recorded directive whose text carries a continuity phrasing and names the lane, per the directives home's D-4 row, the same test over the loop_mode or authoring_cycle_gate directive field's own text, or a live operator message in the current turn directing the lane's continuation; a single-completion scope never carries it); the degraded decision (dispatch-while-plausible: dispatch when minutes to reset fits a typical run by evidence, the typical estimate grounded in the at most five most recent completed same-lane runs in the state file's children[] outcome records with duration anchored at fire_at when set and otherwise created_at, weighed against the target's own declared scope, the decision citing the specific records that grounded it, the lane's worst-case upper bound staying the ceiling); the fail-closed arms (an estimate at or above the bound, a window below every evidence-supported estimate, or no completed same-lane record or no scope-comparable read, defer exactly as the mechanical branch does, the per-lane bias band included); the integrity-defers preservation (the probe pause decision and the exhausted governor class per the origin row's Expected block, and rate pressure also carried in the User-directed override rule's never-overridable list, defer whatever the directive); the audit duty (the decision records `near-reset-directive-override:<witness>` in decision_reason, the witness following the precedence: the directives-home row id, otherwise loop_mode or authoring_cycle_gate, otherwise the literal "live operator message", mirroring the user-directed-override token shape, beside the unchanged quota_at_decision record, the quota slug keeping the near-reset observation); the unattended coverage (a standing directive covers unattended sessions consuming it; an unattended lane with no covering directive keeps the mechanical defer unchanged); and the addition stamp naming this plan and the witnessed 2026-10-05 12:56 chaining stop [class: IMPLEMENTATION_REQUIRED]
- [x] Add one reconciliation clause to the carrier-selection sentence in the D2 (author) bullet of the same Step 3 decision region, immediately after the arm's mid-band parenthetical (the text following "resolves to the idle-time queue or defers the lane" through its closing parenthesis) and before the "; an unknown signal keeps the existing defaults" continuation: for a lane covered by the near-reset branch's live-directive carve-out, the near-thresholds reading resolves to a dispatch carrier instead (in-session when the in-session leg's conditions hold, otherwise the idle-time queue), recorded under the same `near-reset-directive-override` token, so the witnessed defer cannot re-enter at the carrier leg after the branch dispatches [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the untouched neighborhood byte-intact: the bias-band sentence, the sanctioned must-dispatch exemption sentence, the fresh-window rule, the quota slug vocabulary paragraph, the remainder of the D2 carrier-selection sentence beyond the one reconciliation clause (its scarce and peak-priced legs and its session-unable arm unchanged), the primitive-selection scarcity rule, the User-directed override rule's trip set, and the Step 4 fire-time leg (the maintenance SKILL.md quota leg and the zcode.md runtime-fit rule) carry no carve-out wording [class: REPOSITORY_TEST]
- [x] GREEN: the pins suite exits 0 with the final OUTCOME: pass line [class: REPOSITORY_TEST]
- [x] Commit: `feat: near-reset defer yields to a covered live directive via dispatch-while-plausible` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Continue-loop quota leg inheritance and final gates

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the region-needles and inheritance criteria
- `grep -c "including its live-directive carve-out" agents/skills/maintenance/SKILL.md`; covers the inheritance presence (RED at authoring: zero hits)
- `bash scripts/check-no-em-dash.sh added-lines --base main` and `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`; cover the standing gates over the changed set

- [x] Add one inheritance sentence to the continue-loop condition's quota leg immediately after its Degradation arm sentence: the degradation arm reads the Quota-aware lane decisions' near-reset branch including its live-directive carve-out, so a chaining re-run whose lane a directive covers continues while the window fits a typical run by the branch's evidence standard and records the branch's override token when the carve-out fires; an integrity pause decision still stops the leg unchanged; the sentence's addition stamp names this plan and the witnessed 2026-10-05 12:56 chaining stop this leg produced [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the completion-stranding detector's consult of the continue-loop stop's quota-pause reason needs no edit: a stop now records only genuine unusable-window failures, and the reset-window-carrier suppression reads the same reason literal [class: REPOSITORY_TEST]
- [x] GREEN: the pins suite exits 0, the em-dash added-lines scan exits 0, the public hygiene scan exits 0, and `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-near-reset-defer-directive-hierarchy.md` exits 0 on the final bytes [class: REPOSITORY_TEST]
- [x] Commit: `feat: continue-loop quota leg inherits the near-reset directive carve-out` [class: IMPLEMENTATION_REQUIRED]

## Disposition

- Outcome: executed and landed on main (squash commit recorded at landing).
- Tasks 1-2 complete; all ten checkboxes ticked; implementation commits a509549a (Task 1 carve-out + D2 reconciliation clause) and 3a13f641 (Task 2 inheritance sentence + ticks). No pin re-key needed (insert-after placement preserved every pinned needle).
- Exec review: r5 fresh adversarial (one Low, the expected mid-loop digest-stale state; verdict ready=yes; the digest leg resolved by this plan's r6 digest-binding probe); record + sidecar at docs/reviews/2026-10-05-plan-review-near-reset-defer-directive-hierarchy-r5.md.
- Gates on the final bytes: pins suite OUTCOME: pass; em-dash added-lines exit 0; hygiene scan OUTCOME: pass; evidence greps present (override token 2, dispatch-while-plausible 1, continuity phrasing 1, inheritance needle 1).
- Deferred residuals: none.
