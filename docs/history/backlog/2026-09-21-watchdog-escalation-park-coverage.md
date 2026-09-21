# Backlog: watchdog level-2 escalation predates the pending_rearm park step

Status: open
Priority: low
Driving force: primary durability (the watchdog is "the only out-of-lineage detector for a child that dies before its re-arm"; if its escalation stays note-only, the suppressed re-arm of exactly that actor never parks, and if it inherits the park, its writer class is unnamed: either reading is a defect against the sanctioned-writer closedness invariant).
Origin: code review r1 of docs/plans/2026-09-21-scheduler-maintenance-state-durability.md, staging doc docs/reviews/2026-09-21-scheduler-maintenance-state-durability-code-review-r1.md, finding F11 (Medium, non-blocking; moved to overflow per the per-worker non-blocking budget; implementation#watchdog-escalation-park-coverage-hole).

The watchdog bullet's parenthetical escalation summary ("record rearm_note, write the repo-keyed loop-parent-missing memory note, continue") predates the child duty's park step, and the SKILL.md watchdog writer class names rearm_note, parent_automation_id, and a pending_rearm recovery clear, but no escalation park write. The address pass fixed the direct child-duty paths; the watchdog's route was left unresolved pending this item.

Candidate fix (pick one): update the parenthetical to "(record rearm_note, write pending_rearm plus the assembled parent payload copy, write the repo-keyed loop-parent-missing memory note, continue)" and add the park write to the watchdog writer class; or state explicitly that the watchdog's escalation is note-only and why.
