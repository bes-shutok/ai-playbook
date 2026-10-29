# Done final-only plan validation residuals

- **Filed:** 2026-10-29, during maintenance authoring of the light-boundary stale-directive follow-up
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** review finding
- **Class:** fix-class
- **Skill/step:** completed plan validation block; `scripts/check_maintenance_pins.sh`; done and review-loop prose
- **Driving force:** correctness + maintainability
- **Dedup probe:** searched open backlog filenames and problem bodies for "done final-only", "light boundary", "plan validation residuals", and "preservation pins"; the nearest matches are docs/history/backlog/2026-10-19-light-boundary-review-followups.md, the parent origin that records these accepted deviations, and docs/history/backlog/2026-10-06-done-boundary-review-candidates.md, a distinct evidence-gate cluster that does not own these archived-plan validation residuals.

## Observed versus expected

Observed: the completed plan `docs/history/plans/completed/2026-10-18-done-final-only-learn-intermediate.md` has accepted validation residuals. The plan is archived, and the plans lifecycle permits only a disposition section or an explicitly evidenced backfill there, not edits to its checklist or rationale. The plan's review evidence records: preservation pins miss frozen Steps 5-7; negative bookkeeping greps accept grep exit 2 as clean; the em-dash claim omits lessons and plan-added lines; Task 3 leaves the failure-semantics item unfenced; `check_maintenance_pins.sh` anchors a stale placement phrase; done's frontmatter summary omits the Step 1.9 off-tree backlog row; the maintenance template changelog lacks the blueprint reword; and review-loop repeats the done closeout leg list.

Expected: create a new, reviewable plan for these residuals at a legal plan-edit boundary. Keep the completed plan bytes unchanged. Widen the preservation and failure pins, make negative scans distinguish no-match from tool error, cover the correct em-dash surface, and resolve the four later-round prose/pin residues with the owning files' current gates.

## Evidence

- `docs/history/backlog/2026-10-19-light-boundary-review-followups.md`
- `.ai-playbook/reviews/2026-10-19-done-final-only-learn-intermediate-code-review-r1.md`, testing findings F7-F10 (the six wording shrinks F11-F16 are handled by the covering plan)
- `.ai-playbook/reviews/2026-10-19-done-final-only-learn-intermediate-code-review-r2.md`, residuals R1-R4
- `agents/skills/plans/SKILL.md`, Plan Lifecycle archive-edit boundary

## Suggested next step

Author and review a focused follow-up plan for the validation and later-round residues. Do not modify the archived source plan's checklist or rationale; record its disposition in the new plan and leave this row open until that follow-up lands.
