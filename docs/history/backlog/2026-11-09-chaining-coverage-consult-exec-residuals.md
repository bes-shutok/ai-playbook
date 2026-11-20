# Backlog: chaining coverage consult execution-run residual advisories

Driving force: code-quality

Origin: the Phase 3 review panel of the chaining-retry-arm-blind-to-operator-carriers
execution run (session interactive-exec-20261109-chaining, branch
2026-11-09-chaining-retry-arm). Zero blocking findings; these are the recorded
valid unfixed advisories on the landed consult text and its plan record.

- Plan-witness record accuracy: Task 2's pins checkbox reads "expect exit 0 on
  both" and the changed-file-set item reads "names decisions.md only", but the
  execution run's pins gate exits 1 on the pre-existing baseline-red cell
  (identical failure set to base) and the changed set necessarily includes the
  plan's own checkbox flips. The adjudications live in the boundary commit
  messages; the plan text was not updated in place. Any future re-read of the
  plan record face-value contradicts the run.
- Unpinned recognition-span literal: the inserted consult quotes "You are the
  maintenance scheduler for the repository at" verbatim in decisions.md; the
  sibling surfaces cite the opening line by reference and the span-count pin
  does not cover decisions.md, so a template first-line change would drift the
  copy silently. A by-reference form (guards.md style) closes it.
- Missing inline provenance tag: the consult sub-rule carries no
  "(added <date>, <plan>)" tag, deviating from decisions.md's convention for
  later-added sub-rules in the same bullet family.
- Cross-lane matching residual: the matching predicate counts any lane's
  marker, so an other-lane child inside the coverage window suppresses this
  lane's retry arm; the in-window child's first-action re-arm restores the
  loop, but an operator-armed payload without that first action would extend
  darkness past the window. Same-lane matching would force a marker-to-lane
  mapping against the runtime-agnostic constraint; track as accepted residual.
