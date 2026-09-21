# Backlog: state-durability r3 design-simplification residuals (Step 0 arm density; recipe existence pin)

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; readability/pin-redundancy simplification. Revive on the bullet is next reworked under a live plan, or a project-priority-profile change.)
Origin: code review r3 of docs/plans/2026-09-21-scheduler-maintenance-state-durability.md, staging doc docs/reviews/2026-09-22-scheduler-maintenance-state-durability-code-review-r3.md, overflow manifest.

## Item 1: Step 0 rearm-on-touch bullet density (design-simplicity, architecture#god-method)
The bullet is ~1078 words carrying six contracts (cannot-decide consultation events, attempt-bound read, listing-gated bookkeeping, the full self-heal state machine, adoption guards, exemptions); cross-cutting rules must be copied inline into every clause, which is how the bound rule grew four homes in one round. Candidate fix: split into named sub-bullets (consultation, bookkeeping, self-heal) under the same check, giving cross-references targets without semantic change.

## Item 2: recipe existence pin near-redundant (design-simplicity, simplification#delete)
After the r1 directive-wording content pin and the r2 canonical literal pin, the plain 'mode appendix sourced from state' existence pin has almost no independent failure direction (a single-sentence deletion fails all three). Candidate fix: fold it into the content pin or document its residual direction the way the F14 comment does. Sibling: docs/history/backlog/2026-09-21-pins-appendix-floor-redundancy.md.
