# Backlog: dirt-regression gate blocks a reviewed correction

- **Filed:** 2026-10-05
- **Status:** closed (STORY-KEY case reclassified)
- **Workflow:** backlog
- **Priority:** superurgent (operator-marked)
- **Origin class:** observed done pre-commit gate conflict
- **Class:** fix-class
- **Driving force:** reliability

## Reassessment

The STORY-KEY instance did not establish that the dirt-regression gate blocked a valid correction. Round 6 design review found that removing the two-argument constructor from the new public `CompiledSegmentPlan` DTO was not actionable: the overload is a public construction path, has no in-repository execution consumer, and its empty-anchor default is valid when no required-property anchors exist. The implementation retained the constructor and the finding was dropped as a false positive. The gate therefore prevented an unnecessary API change in this case.

## Evidence

- Observed 2026-10-05 during STORY-KEY Round 5 closeout: removing an unused two-argument constructor from `segments/src/main/java/com/<consumer-organization>/crm/segments/api/dto/CompiledSegmentPlan.java` produced `dirt REGRESSION: ... (restores base-era text over lines HEAD gained since 7c3f32ecdd21)`, `OUTCOME: fail` against `origin/master`.
- The file is explicitly claimed by the current done manifest and the removal resolves Round 5 finding F4, which the canonical review record marked fixed.
- The preceding revert-set classifier reported the file as foreign, not an ancestor vintage; no stale-checkout evidence was found.
- `agents/skills/done/SKILL.md` Step 3 item 1 directs restoring every dirt-regression path from HEAD and forbids staging it.
- The execute-plan user directive requires continuing without further confirmation, but no documented intent receipt or narrow exemption exists for this shape.

## Disposition

Closed as a false-positive incident report. This evidence does not support changing the shared dirt-regression gate. Reopen only when a concrete, behaviorally necessary, independently reviewed correction is blocked by the gate and cannot be represented as ordinary non-regressing changes.

## Source

- Observed 2026-10-05 during STORY-KEY Phase 3 Round 5 review-fix closeout.
