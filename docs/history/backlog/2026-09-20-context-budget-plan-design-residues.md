# Backlog: scheduler-turn exemption sentence rides every child payload but is inert to the child

Status: open
Workflow: backlog
Source: Phase 3 r1 code review of the context-budget plan execution (staging doc docs/reviews/2026-09-20-2026-09-19-context-budget-and-telemetry-long-running-skills-code-review-r1.md, design-simplicity F6; triaged deferred to this backlog item — the landed text faithfully implements the plan-prescribed sentence content (the plan's Task 4 bullet prescribes the exemption in both bodies), so the fix is a plan-design residue, not an implementation error; changing it mid-execution would deviate from the certified landing).
Severity: Low
Exact location: agents/skills/maintenance/prompt-templates.md — the sentence "The scheduler turn itself gets no checkpoints: the turn is a fresh short session each cadence, and this blueprint's final compaction step keeps payload transcripts short." in both blueprint bodies (authoring body ~line 43, execution inner block ~line 97).
Why not fixed now: the landed text faithfully implements the plan-prescribed sentence content (the plan's Task 4 bullet prescribes the sentence in both bodies), so the fix is a plan-design residue, not an implementation error; changing it mid-execution would deviate from the certified landing.
Driving force: simplicity

## Problem

The scheduler-turn exemption sentence rides every dispatched child payload but is inert to the child that reads it: it explains an exemption for a session the child neither is nor controls (the scheduler turn gets no checkpoints; the child's own duty is "every step block of this run", which the payload already states). The rationale also duplicates the deviation entries' checkpoint-duty rationale in the same file, which the bodies do not reference, giving the same explanation two homes that can drift. Cost: two permanently dispatched copies of inert text per cadence, payload tokens and attention only.

Fix: drop the sentence from the two blueprint bodies and keep the exemption rationale in the deviation entries (the single-home rule for cross-cutting rationale). This belongs to the next planned touch of agents/skills/maintenance/prompt-templates.md — not a standalone edit, since the bodies are pinned by the pins suite's blueprint-unique checkpoint-duty spans and the change should ride a planned rewrite of the duty text.

Sibling deferral (recorded here, not backlogged): the plan header's `Plan review:` line of docs/plans/2026-09-19-context-budget-and-telemetry-long-running-skills.md still points at r6 ("latest, ready") while r7 is the latest certification round, and the residual paragraph's r7 sentence reads as a pending gate ("must pass") although r7 already ran with verdict yes — both are reserved for the Phase 4 archive-prep plan edit (editing the plan mid-execution would trigger the Step 0.5 correction branch; the archive-prep edit refreshes the header anyway). Review finding F7 of the same r1 round.

Trigger: the next planned touch of agents/skills/maintenance/prompt-templates.md.
