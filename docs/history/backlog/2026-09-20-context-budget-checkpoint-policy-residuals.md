# Backlog: checkpoint cap-semantics cluster and residual witnesses for execute-plan's context budget checkpoints

Status: open
Workflow: backlog
Source: Phase 3 r2 code review of the context-budget plan execution (staging doc docs/reviews/2026-09-20-2026-09-19-context-budget-and-telemetry-long-running-skills-code-review-r2.md, findings F1, F3, F4, F5, F6 plus the overflow lane-coordination note; triaged deferred to this consolidated item).
Severity: Medium (one cap-semantics cluster) + Low (four witnesses/simplifications)
Exact location: agents/skills/execute-plan/SKILL.md `Context budget checkpoints` section + scripts/check_maintenance_pins.sh
Why not fixed now: the cap semantics are policy-design choices (increment timing, fall-through, escalation) needing a focused follow-up over the section rather than mid-run churn; the witnesses are fail-closed or cosmetic.
Driving force: code-quality

## Problem

1. **Cap-semantics cluster** (Medium, workers testing/risk/correctness-completeness, r2 F1): pin when `compactions_to_date` increments (define completion for a manual handoff on a primitive-less runtime); decide whether a capped rung degrades to the 70-85% shedding rung instead of log-only; pin the capped/failed record's `action` value (corpus vocabulary currently shed/compact/no-primitive only); add a terminal rung (after N consecutive capped above-85% checkpoints, stop at the safe boundary with a surfaced budget report instead of logging indefinitely).
2. **Dual-lane ladder coordination** (Low, risk, r2 F4 + the overflow lane-coordination note): one precedence sentence in review-loop's round-boundary paragraph — under execute-plan Phase 3 the parent's after-review-round checkpoint is authoritative for ladder actions; review-loop only logs its per-skill record; also define the first-record baseline for its own `compactions_to_date` comparison.
3. **Archive vocabulary unmeetable** (Low, correctness-completeness, r2 F3): review-loop and plans-authoring context.jsonl lanes have no archive step or retention owner; either extend the Phase 4 archive step to sibling-lane files for the same slug, or record the child lanes' live paths as their analysis home with a retention owner.
4. **Unpinned navigation headings** (Low, design-simplicity, r2 F5): add `pin "context checkpoints section anchored" grep -qF '### Context budget checkpoints' "$E"` and `pin "measurement primitive section anchored" grep -qF '## Context measurement primitive' "$Z"` (five cross-file references dangle if either heading is renamed after the plan's ephemeral gates archive).
5. **Archive-rationale shrink** (Low, design-simplicity, r2 F6): the Phase 4 paragraph's "because the archived telemetry file outlives the run directory" clause restates its main clause and the Phase 5 checklist parenthetical restates it again; drop the because-clause and the checklist parenthetical tail (keep the provenance half).

Trigger: the next planned touch of execute-plan's `Context budget checkpoints` section or scripts/check_maintenance_pins.sh.
   6. Residuals-item header scoping (Low, testing, r3): the Exact location and Trigger lines name only the execute-plan section and the pins script, but item 2's fix lands in agents/skills/review-loop/SKILL.md's round-boundary paragraph; add that file to both lines so a review-loop touch surfaces the item.
   7. Gate-strength header scoping (Low, testing, r3): that item's Exact location line still enumerates only the two r7 spans for its six-pin tally; generalize to "the ## Validation Commands block across the Task 2/3/4 gates and the Phase 5 checklist pin (six spans, see Problem list)" so a triager cannot close the record after the two named spans.
