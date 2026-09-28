# Incidents classify as fix-class or fence-class at origin filing time

- **Filed:** 2026-09-29
- **Status:** done (2026-09-30; executed by plan completed/2026-09-29-plans-machinery-delta-doctrine.md, landed main 32aba2dd, impl review r1 zero findings)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Driving force:** simplicity; secondary efficiency
- **Source:** operator direction, 2026-09-29 (Andrey): find the root cause of "it gets worse, not simpler". Witnessed conversion: a consumer execute-plan run's scope-drift block (stoppable, prelaunch, recoverable by design) was filed with reliability force and grew into a full hardening arm (worker-lifecycle Task 7: snapshot capture, replay fences, actor provenance) when the witnessed need was one sanctioned exit (the narrow receipt-fenced recovery plan). Also witnessed 2026-09-28: a plan authoring pass had to remap the reliability driving force into the plans closed taxonomy, so friction-driven hardening files under code-quality by default with no counter-force.

## Problem

At filing time, two very different incidents enter the same pipeline with the same default shape: add a gate. One kind is an integrity failure: a wrong result, corrupted state, or lost evidence that a refusal would have prevented. The other kind is a friction event: the system behaved correctly (fail-closed), but lacked a sanctioned exit, over-refused on a false positive, or forced a manual workaround. Converting friction events into new refusal classes punishes correct behavior and grows the ceremony that slows every future run. No classification step exists that asks which kind an incident is before it becomes an origin, so the default is hardening, and the origin-to-gate conversion ratchets.

## Expected behavior

- At backlog filing, the origin header gains one classification line: `fix-class` or `fence-class`.
- fix-class: a block, stall, or false positive where the system behaved correctly but lacked a sanctioned exit or refused something legitimate. Default fix shape: add the sanctioned exit, remove the false positive, or simplify the flow; driving force simplicity or efficiency. Acceptance names the block that disappears. A fix-class origin must not add refusal paths unless no exit or false-positive removal is possible.
- fence-class: a wrong result, corrupted state, or integrity failure. Default fix shape: a new refusal, gate, or fence; driving force code-quality or reliability. The origin must cite the completed failure it would have prevented (state left wrong, evidence lost), not a saved manual step.
- The classification is consumed downstream: plan authoring shapes arms by class, and the gate-delta symmetry rule (docs/history/backlog/2026-09-29-plans-gate-delta-symmetry-pay-to-play.md) prices fence-class additions against the declared delta.

## Issue archaeology

The plans skill's closed driving-force taxonomy already forces an honest mapping at plan time (p79 remapped reliability to code-quality plus token-usage), but the same discipline is absent at origin time, one step earlier in the pipeline, where the reliability force still routes every incident toward hardening. The failed-preflight design itself records the distinction this origin formalizes: preflight refusing scope drift is the system working; the missing reviewed-scope recovery was the actual defect.

## Possibility space

- **Recommended: filing-time annotation plus authoring consumption, both prose.** One header line in the origin template, one rule in the plans skill's authoring rules.
- **Rejected: deriving the class automatically from the runtime's refusal history events.** Telemetry can inform the classification but must not gate it; that would be new machinery doing what one honest line at filing time does.
- **Rejected: forbidding fence-class origins.** Some incidents are real integrity failures; the rule prices them with a completed-failure citation, it does not ban them.
- **Rejected: folding this into the gate-delta origin.** They are two different intervention points (filing time versus plan review) with different owners; each stays a one-rule change.

## Dedup probe

The 2026-09-28 machinery cost-benefit adjudication issued the verdict this operationalizes but created no filing rule. The machinery-elimination-pass origin governs existing-machinery witnesses. The gate-delta symmetry origin (same day) governs plan-time addition accounting. No open origin classifies incidents at filing time.

## Location

- The origin template and the filing flows that create backlog entries (learn lessons-to-backlog flows, done closeout origin filing, session-analysis filings): the classification line joins the header convention. The implementing plan must pin the canonical template location from disk before authoring; this origin observed the convention across docs/history/backlog/ headers rather than naming its owning file.
- `agents/skills/plans/SKILL.md`: authoring consumes the class (fix-class defaults to exit and false-positive arms; fence-class defaults to fenced refusal arms).
- Cross-reference and Integration Points with docs/history/backlog/2026-09-29-plans-gate-delta-symmetry-pay-to-play.md.

## Acceptance

- Origins filed after landing carry the classification line; fix-class origins' plans remove blocks rather than add refusals; fence-class origins cite completed failures; a sample of ten post-landing origins shows the line present and consumed at authoring.
