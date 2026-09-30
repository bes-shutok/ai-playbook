- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (registry hygiene; a systemic prune gap witnessed across a whole evening exec batch)
- **Origin class:** self-serving (found during the 2026-09-30 audit of the survey-mode lifecycle)
- **Driving force:** efficiency
- **Class:** fence-class

Cluster: docs/history/backlog/2026-09-30-investigate-prompt-possibility-space-review.md

# PLAN-PROMPTS entries are not pruned when their plans land

Witness: the investigate-cluster-survey-mode entry (emitted 18:14 as superurgent queue top) was still live and dispatchable in the registry past 22:00 even though its plan landed 19:37, executed, and archived 19:40. The 2026-09-30 prune sweep then found the same state across the whole evening batch: entries whose plans had landed AND executed hours earlier, still sitting at their urgency positions (p90-invocation-scope-revalidation, p80-baseline-satisfied-task-closeout, p92-park-discharge, p93-review-posting-landing-evidence, p94-skill-description-length-gate, p84-sut-naming, p85-user-directed-override, p86-secret-scan). The freeze rule's prune clause ("the entry is pruned outright per the prune rule when its plan file lands") has no owner at landing time and no mechanical check, so pruning waits for a reader to notice. A dispatch consult consulting the registry before that read would attempt to author an already-completed plan; the only stopgaps are each origin's done Status line and the origin-coverage landing gate.

Asked changes:

1. Machinery: give the prune clause a mechanical home. Either the landing/archive flow prunes the emitting entry in the same pass as its landing receipt duty, or the done sweep's pre-docs gate fails when a live registry entry's Origins intersect the archived plan's origins.
2. Pin: extend the verify-script pins so the state "a live registry entry names an origin whose Status is done" is mechanically checkable (grep-level: no entry Origins line may name a done origin), so the next drift is caught by a suite instead of by an operator question.
3. Record: the 2026-09-30 sweep commit is the baseline receipt; this item owns the enforcement, not the backlog cleanup.
