# Backlog: pin gate-precedence outside Step 2.76

Driving force: Phase 3 r1 risk-lens findings (2 Medium + 2 Low) on the no-silent-gate-satisfying-prose-rewrites execution; the pin's stop clause and the host contracts' remedy-and-continue imperatives conflict at every gate site other than Step 2.76, where the annex resolves it.

Suggested fix (one or more of):
1. General precedence line in the done Rules bullet (or a short annex at done Step 2.8): at any gate other than Step 2.76, the stop-and-surface clause suspends surrounding remedy-and-continue imperatives (including the learn Step 6.5 compaction remedy) until the user adjudicates, or scope the Rules bullet's stop clause explicitly to Step 2.76 so the surfaces cannot conflict.
2. Except-clause on Implement Task rule 5 ("fix ALL test failures") deferring to the pin's stop clause.
3. Exclusion arm after user adjudication: when the user says "leave the prose as is", permit Steps 2.8 and 3 to proceed with the failing prose path excluded from staging/commit, instead of halting the whole run.

Status: rejected (2026-09-26; unwitnessed hardening: gate-precedence machinery between rules; no witnessed conflict)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; gate precedence machinery between rules. Revive on a witnessed rule conflict stalling a run, or a project-priority-profile change.)
