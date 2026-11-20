# Backlog: self-heal direction still needs repeated operator prompting

- **Filed:** 2026-11-20, operator-reported recurrence after the explicit-workaround recovery change
- **Status:** covered-pending-execution (docs/history/plans/2026-11-20-self-heal-recovery-direction-continuation.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** efficiency + reliability
- **Skill/step:** `agents/skills/self-heal/SKILL.md` Recovery 1-5
- **Catch frequency:** one new reported recurrence after the completed 2026-11-20 recovery-direction plan; the user repeatedly invoked self-heal and restated the request to find a workaround.
- **False-positive cost:** extra turns and avoidable operator effort; overcorrecting could weaken real authority, safety, ownership, or landing gates.
- **Review date:** 2026-12-04
- **Dedup probe:** the completed plan `docs/history/plans/completed/2026-11-20-self-heal-explicit-workaround-not-carried-through.md` already says to carry a workaround direction into the next authorized action. This row records a recurrence after that implementation, not the original wording gap; determine whether a distinct operational clarification is justified before editing the skill again.
- **Cluster:** `docs/history/backlog/2026-11-20-self-heal-scheduled-continuation-as-stop.md` (same self-heal recovery handoff; this row owns repeated explicit-direction handling, the sibling owns the future-fire-time explanation and current-action check)

## Problem

In the current interaction, the user repeatedly invoked self-heal and expressly asked for a workaround to finish removing a named ad-hoc worktree and branch. The user later reported that the assistant still left both resources present and had to ask why the work could not happen before a scheduled continuation. The assistant subsequently did complete cleanup, learn, and investigate in the main repository. This establishes repeated prompting and eventual completion, but the original probe or decision log is unavailable; do not claim a proven internal cause or that the removal gates were satisfied earlier.

## Expected

When a user gives a current, explicit recovery direction, self-heal should immediately determine the next authorized action, test its actual prerequisites, and either carry it out or report the precise unsatisfied condition and the evidence needed. It should not ask the user to repeat the direction or treat the existence of a scheduled continuation as proof that immediate work is forbidden. Existing ownership, safety, archive, worktree, branch, retry, and landing gates remain binding.

## Suggested direction

Compare the current skill and the completed 2026-11-19 and 2026-11-20 recovery changes with the observable interaction. Separate a failure to execute an existing instruction from an actual ambiguity in the skill. If a concise action-at-the-next-step clarification would change that outcome, add it within the existing recovery section and pay for its bytes in the same file; otherwise record why more prose would not address the runtime failure. Do not add a gate, validator, log, or ceremony.

## Evidence

- The current interaction contains repeated user directions to invoke self-heal, find a workaround, and complete cleanup, followed by the user's report that the worktree and branch remained. This is direct interaction evidence; the initial assistant decision trace is unavailable.
- The user quoted the prior explanation that an armed continuation was scheduled for 17:38 UTC and asked why work could not happen immediately. Treat this as operator-reported behavior, not a verified runtime ownership state.
- The completed plan `docs/history/plans/completed/2026-11-20-self-heal-explicit-workaround-not-carried-through.md` implements explicit-direction carry-through in Recovery step 3 and evidence-backed stop reporting in step 5. The recurrence happened after that change was present in the skill.
- The subsequent main-checkout cleanup and investigation report shows the requested resource cleanup and recovery work were eventually completed; it does not establish that all removal prerequisites were satisfied at the earlier refusal.

## Why not fixed now

The skill already instructs self-heal to carry explicit workaround directions into the next authorized action. A further wording change is justified only if investigation finds a concrete interpretation gap that explains the repeated deferral without weakening the resource-cleanup protections.
