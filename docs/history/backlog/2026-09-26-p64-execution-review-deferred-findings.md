# Backlog: P64 execution review r4 deferred findings (non-blocking)

Driving force: quality

Origin: execution Phase 3 round r4 of docs/plans/2026-09-26-p64-execution-lane-liveness-long-session-continuity.md (worktree branch 2026-09-26-p64-execution-lane-liveness, commits 80001eb1, aee1ad10, 2f6f4eab; blocking finding folded in b9afb7bd, re-cert clean). All findings below were triaged valid but non-blocking and deferred out of the plan's scope.

## Findings deferred

1. `testing#self-satisfying-header-loop-pin` (Medium): the Task 3 pin `pins header existence loop covers E` (scripts/check_maintenance_pins.sh) greps the literal `for f in "$S" "$Z" "$P" "$D" "$E"` against the suite file, but the pin's own line contains the same literal, so grep always matches and the pin cannot fail for the regression it names (dropping `"$E"` from the header loop). Fix: line-anchor the needle (e.g. `grep -qE '^for f in ...; do$' "${BASH_SOURCE[0]}"`) or assert the property functionally.
2. `security#cycle-gate-armed-test-ambiguity` (Medium): the armed predicate reads "a non-null gate value" at the Step 1 reader and Step 3 enforcement sites, while the clear trace leaves the field as a non-null object carrying `gate: null`; a top-level reading of "non-null" makes every post-clear state permanently armed (permanent lane suppression). Fix: define the predicate once in the field paragraph in terms of the inner `gate` member and reference it from both read sites.
3. `testing#vacuous-em-dash-validation-command` (Low): the plan's Validation Commands line `bash scripts/check-no-em-dash.sh` runs argless (usage, exit 0, scans nothing); prescribe a real subcommand (`touched` or `added-lines`) in future Validation Commands blocks. The plan file itself is frozen post-review; fix is forward-looking guidance.
4. `testing#writer-count-absence-scope` (Low): the six/seven sanctioned-writer-classes absence pins are scoped to SKILL.md only with no corpus sweep covering the literals elsewhere; widen targets or add sweep patterns if a stale count ever lands in another live surface.
5. `documentation#prose-orphaned-precheck-parenthetical` (Low): the Task 1 append in the Step 5 ladder-precheck precondition bullet strands the pre-existing lowercase parenthetical after a new sentence-ending period; rewrap so the parenthetical stays attached to the park-persistence sentence.
6. `documentation#prose-field-paragraph-task-narration` (Low): the authoring_cycle_gate field paragraph permanently embeds plan-task narration ("in the same task", seven-to-eight movement); trim to "(the eighth sanctioned writer class)" and leave movement history to the Revisions ledger.

## Acceptance notes

- Items 1 and 2 are the ones worth a plan: both are Medium-severity latent hazards (a blind regression witness that cannot fire; a runtime misreading that silently suppresses both lanes after a normal arm-then-clear cycle).
- Items 3 to 6 are prose/pin polish; they can ride along with any future maintenance-surface plan.
- None of the six invalidates the landed P64 behavior; r4's own gates and the r5 re-cert all ran green with these deferred.
