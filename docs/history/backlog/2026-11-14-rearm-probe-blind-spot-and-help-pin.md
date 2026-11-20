# Backlog: rearm validation probe blind spot and unnamed help-text fixture

- **Filed:** 2026-11-14, certification-residual capture from plan review r5 (machinery-cli-operand-self-description)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (the focused suite is the discriminating witness; the probe is a secondary channel and the help pin a fixture-inventory gap)
- **Origin class:** review-residual (certification overflow, two Low findings)
- **Class:** design-class
- **Skill/step:** `scripts/rearm_on_touch.py` (Task 2 of the covering plan below): the plan's Validation Commands smoke probe and the `--listing-json` help-text requirement
- **Cluster:** covering plan `docs/history/plans/2026-11-13-machinery-cli-operand-self-description.md` (Task 2) (the origin row was deleted covered by the execution landing c313fcd18)
- **Source reference:** two residuals. (1) The smoke probe asserts only the exit channel: with the seeded three-field state, a Task 2 implementation that parses the inline literal but discards it returns the state-first `listing-required` verdict, which also exits 0, so the probe cannot distinguish acceptance from parse-but-drop; capturing stdout and asserting the verdict's `listing_used: true` marker closes the blind spot (the focused suite already carries the discriminating assertion). (2) The `--listing-json` help naming the three accepted forms is the only priced self-description surface whose GREEN line names no pin (Tasks 1 and 4 name theirs), so the help text is implementable without a failing-today fixture; a help-output containment fixture in the rearm suite closes it.
- **Dedup probe:** the covering plan pins the acceptance via its focused suite and the smoke probe's exit channel; no open row owns the probe's stdout blind spot or the missing help-text fixture; the sibling insert-forward-compat row covers a different defect class on the same script
- **Why not fixed now:** certification-residual routing records non-blocking residuals beside the certified bytes without forcing a re-round or fold; both remedies are one fixture each, foldable into any later plan touching that surface
