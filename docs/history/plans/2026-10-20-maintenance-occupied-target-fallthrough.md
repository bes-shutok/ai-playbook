# Plan: Maintenance Occupied Target Fallthrough

Backlog origin: `docs/history/backlog/2026-10-19-maintenance-occupied-target-fallthrough.md`
Driving force: code-quality
Plan review record: `.ai-playbook/reviews/2026-10-20-plan-review-maintenance-occupied-target-fallthrough-r*.md`
Execution budget: 1.0h total, largest task 1.0h

## Terms

- **Occupied target:** A candidate whose target has a fresh foreign authoring claim or a live peer claim on that same target, per the existing claim and target-distinctness rules.
- **Eligible target:** A candidate that passes the existing coverage, claim, and lane guards; priority determines scan order.
- **Exhausted scan:** The ordered candidate list has no remaining eligible target to evaluate.
- **Multi-plan directive:** The user’s instruction to process multiple targets in sequence, one at a time.
- **Continuation summary:** The context carried into a resumed turn after compaction.
- **D2:** The maintenance decision that selects one backlog item for authoring after its guards pass.
- **Rolling prompt-log selection:** The maintenance decision that scans unfrozen PLAN-PROMPTS entries and selects at most one eligible target.
- **Next-distinct scan:** The rolling prompt-log rule that evaluates a later unfrozen entry when the leading entry has a live claim on the same target.

## Why

The authoring rules direct the priority scan past a fresh foreign claim, and the rolling prompt-log rule directs selection past a live claim on the leading entry. The open origin records a recurrence after the prior wording clarification in `629fdb0e3`. The proposed outcome is narrow: make the point at which a scan may hold explicit while preserving claims and priority order.

## Gist & Examples

TLDR: clarify the exhausted-scan stop condition for code quality, so an occupied first candidate does not end sequential authoring early.

Before: Given A as the highest-priority backlog target with a fresh foreign claim and B as the next eligible target, the rules permit skipping A but show no concrete A-to-B outcome. A resumed context can also lose the active multi-plan directive, progress, and next target.

After: Record A’s skip, select B once, and name B in the closeout report. Before compaction, the continuation summary carries the active directive, completed target, and next target; the resumed turn continues under the same ordering and guards. The selection examples hold only after exhaustion or a named guard.

Edge cases: Preserve a foreign claim untouched; retain priority order; distinguish same-target from distinct-target peers; when all candidates are occupied, record the skip reasons and hold; never require operator selection or add a blocking mechanism.

## Outcome

Maintenance authoring follows the existing fall-through rules through exhaustion.

- D2 states when the priority scan may hold after occupied targets.
- The rolling prompt-log example shows when to select a later distinct entry and when the scan is exhausted.
- The context-load guidance carries an active multi-plan directive and current progress through compaction, and the closeout report names the selected next target.
- Claim protection, candidate ordering, and the one-authoring-task limit remain unchanged.

Gate delta: no gates, validators, locks, or ledgers are added or removed; equivalent operative bytes are deleted in the same edit to keep text balance flat.

## Design Invariants

- A fresh foreign claim is a skip reason, never permission to overwrite or take over the claim.
- The scan preserves its current priority order and evaluates the next distinct eligible target before holding.
- The turn selects at most one authoring target.
- Holding is correct after scan exhaustion or another named guard, and the recorded reason identifies that outcome.
- The change adds no blocking gate, validator, state field, ledger, or required user question.

## Assumptions

- The current wording in `agents/skills/maintenance/decisions.md` is the policy source: D2 owns backlog-item authoring, while Rolling prompt log duties own PLAN-PROMPTS selection.
- The source change is justified by the recurrence documented in the origin after `629fdb0e3`; it adds the missing explicit exhaustion outcome and one compact example instead of repeating the same skip rule.
- The two selection homes need their own short example because they select different candidate types and use different occupancy predicates; a new top-level section cannot absorb either decision without duplicating their selection context.
- No machinery is warranted. A blocking or required evaluation would cost more than the observed catch justifies and risks holding valid unclaimed work.
- The origin backlog uses `reliability`; the plans taxonomy maps that force to `code-quality` for this documentation-only contract clarification.
- The maintenance context-load section is the correct home for continuation-summary content; the existing operator-directives file remains the source for standing directives, and the change adds no persisted state.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Backlog fallthrough:** Given candidates ordered A then B, with A blocked by a fresh foreign claim and B eligible, the example states that the turn records A's skip and selects B without changing A's claim.
- **Backlog exhaustion:** Given every remaining candidate blocked by a fresh foreign claim, the example states that the turn records the skips and holds only after the scan is exhausted.
- **Rolling prompt-log fallthrough:** Given a top unfrozen entry whose target matches a live peer claim, a later unfrozen entry with a distinct eligible target, where the turn has not yet selected an authoring target and guards pass, the example expects the monitor to select the later entry; if a guard prevents selection, it records that guard as the hold reason.
- **Directive continuity and report:** Given a user instruction to process multiple targets, the continuation summary records the directive, completed target, and next target; the resumed turn follows that target order and guards, and the Mode visibility closing report names the selected target path.
- **Rolling-log exhaustion:** Given no later distinct eligible entry, the example states that the lane may hold with the recorded reason only after the scan is exhausted.
- **Boundaries:** Priority order, live-claim protection, one-at-a-time selection, and the existing named-guard behavior stay intact; no new gate or required operator question appears.
- **Text balance:** The edit replaces or trims equivalent bytes in the same file, with no net growth for the operative instruction text.

## Done when

The two selection paragraphs and the context-load guidance cover exhaustion, compaction continuity, and target reporting; the current maintenance pins and public-hygiene checks pass, and review confirms no blocker or new machinery was introduced.

## Ship when

The reviewed text change lands on the default branch with its origin disposition and authoring artifacts handled through the normal plan closeout.

## Review Scope

- In scope: `agents/skills/maintenance/decisions.md`, specifically D2's fresh-foreign-claim consult and the Rolling prompt log duties' next-distinct-entry scan; `agents/skills/maintenance/SKILL.md` Step 0 context load and Mode visibility closing-report clause.
- Review concerns: correct selection home for each example, claim-safety and ordering preservation, explicit exhaustion condition, directive/progress/next-target carry through compaction, selected-target report, text balance, and no blocking machinery.
- Out of scope: changing claim lifetime or takeover semantics, candidate ranking, scheduler state, dispatch limits, or the maintenance tooling and validators.

## Validation Commands

- `bash scripts/check_maintenance_pins.sh`
- `bash scripts/scan-public-hygiene.sh`

### Task 1: State the scan-exhaustion outcome at both selection homes

Context surface: D2's fresh-foreign-claim consult and the Rolling prompt log duties' next-distinct-entry scan.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/SKILL.md`

- [ ] Replace or tighten the current D2 skip sentence so it explicitly says to record the occupied skip, continue in the same priority order, and hold only after no eligible candidate remains or another named guard applies; include the compact A-then-B example. [class: IMPLEMENTATION_REQUIRED]
- [ ] Tighten the next-distinct-entry clause with a compact top-entry/later-distinct-entry example and its exhausted-scan hold outcome; retain the existing same-target test and all current guards. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update context-load guidance so the continuation summary carries the active multi-plan directive, completed target, and next target through compaction, then the resumed turn follows the same ordering and guards. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the Mode visibility closing-report clause to name the selected next target path. [class: IMPLEMENTATION_REQUIRED]
- [ ] Remove equivalent instruction bytes in the same file so operative skill text has no net growth; do not add incident dates or witness narrative to skill text. [class: IMPLEMENTATION_REQUIRED]
- [ ] Confirm the examples select at most one target, preserve every foreign claim, and record the scan's skip or hold reason. [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: make occupied-target scan exhaustion explicit`. [class: IMPLEMENTATION_REQUIRED]
