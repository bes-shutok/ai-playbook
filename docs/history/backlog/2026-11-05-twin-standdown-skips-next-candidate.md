# Backlog: twin-standdown deconfliction skips remaining target-disjoint candidates

- **Status:** covered (docs/history/plans/completed/2026-11-05-claimed-top-target-skip-and-continue.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Quarantine:** 2026-11-05
- **Class:** fence-class
- **Driving force:** efficiency
- **Skill/step:** exec-mode plan selection in `agents/skills/maintenance/decisions.md` (D1 plans-only selection) and the operator twin-carrier deconfliction convention recorded in session memory, not in skill text
- **Catch frequency:** one witnessed run (2026-11-05 00:42 WET one-shot exec): three identical carriers fired within ~2 minutes; the session found the top plan freshly claimed by a sibling carrier and stood down 0/1 even though the mandate allowed one plan and target-disjoint candidates remained in the open-plans queue. Same-night contrast observation (2026-11-04 20:41 WET one-shot exec): a carrier stood down 0/1 on a genuinely bound fleet cap (three live peer worktrees with fresh activity), which this row's expected rule itself sanctions as a valid full stand-down — recorded so the pinned skip-and-continue arm is not read as overriding a real cap.
- **False-positive cost:** a session that consults the next candidate when the top target is taken may spend quota on a lower-urgency plan the operator would have preferred to defer; a target-disjointness consult also adds a survey read per decision.
- **Review date:** 2026-12-05
- **Dedup probe:** searched open backlog filenames for twin, deconfliction, stand-down, and queue-selection terms. The landing-disjointness machinery (target-disjointness admission consult, `scripts/dispatch_admission.py`) owns pre-dispatch target overlap for child dispatches; no open row owns the post-launch twin-deconfliction decision of an already-running session whose top target is claimed.
- **Cluster:** `docs/history/backlog/2026-11-04-execution-resume-run-identity-confusion.md` (shared fresh-foreign-claim / claimed-target surface; that row owns resume identity binding, this row owns the selection decision after a claim is found); `scripts/dispatch_admission.py` consult (the pre-dispatch analog this row's post-launch decision should reuse the vocabulary of, not duplicate)

## Problem

The 2026-11-05 00:42 WET exec session (operator mandate: plans in urgency order, one by one, at most 1, stop after the 1st) found the top-urgency plan (`docs/history/plans/2026-11-04-agent-resource-cleanup-disposition.md`) freshly claimed at 00:43:45Z by a sibling carrier of the same operator ask, with three identical one-shot carriers having fired within ~2 minutes. The session stood down 0/1, citing twin doctrine.

The doctrine actually witnessed in memory records ("twin stands down") was recorded for same-target collision avoidance: the second carrier of an identical ask is redundant for the same pick. The session generalized it to a fleet-wide stand-down, which the mandate and the existing machinery do not require: the execution-lane concurrency stance explicitly sanctions target-disjoint concurrent runs, and the dispatch-admission consult exists to admit them. The result was a wasted carrier window (a fired run that executed nothing) and no second plan executed despite operator budget for one.

The twin-standdown convention also lives only in session memory and chat precedent, not in skill text, so each session re-derives its scope from memory summaries, and the generalization error above is the natural failure mode.

## Expected

An exec-mode session that finds its selected top target claimed by a live peer records the collision and proceeds to the next eligible target-disjoint candidate under the same mandate cap (at most 1 execution), consulting the same target-disjointness admission vocabulary the pre-dispatch consult uses. A full stand-down is correct only when no eligible candidate remains, the fleet or quota cap binds, or the operator ask's wording itself scopes the run to that one target. The deconfliction rule's scope should be stated in skill text (D1 selection or the Mode enforcement/Blocker recovery neighborhood) so it stops depending on memory recall.

## Suggested direction

Small skill-text change: add the claimed-top-target skip-and-continue arm to the exec-mode selection rules with the stand-down conditions enumerated, reusing the dispatch-admission consult's target-disjointness vocabulary by reference. No new machinery, ledger, or validator: the claim surface and the survey already carry the needed facts. Price the quota cost of auto-continuing versus the wasted-carrier cost witnessed, and record the twin-standdown memory entries as superseded by the skill-text rule.

## Why not fixed now

This session is recording and investigating the selection fault; editing operative skill text (the selection rules) is plan-shaped work that needs the ordinary authoring and review flow, not an in-turn edit.
