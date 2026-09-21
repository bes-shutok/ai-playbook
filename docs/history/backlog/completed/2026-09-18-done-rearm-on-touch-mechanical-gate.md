# Backlog: done's rearm-on-touch duty is prose-only and was skipped by a full done run

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-18
Class: done/maintenance harness legibility gap (the one done-boundary duty with no mechanical gate)

## Problem

Every done-boundary duty is script-enforced: the learn corpus gate, the plan readiness gate, the review
staging validator, the backlog inbox gate, the doc-registry gates, and the instruction size gate all
fail loudly inside the done flow. The maintenance rearm-on-touch check is the exception: it survives
only as prose in the done skill's preamble and in the maintenance skill's Step 0, and nothing in the
done sequence runs it or records its outcome.

Witness 2026-09-18: an automation-born plan-authoring session ran done end to end (done lock, learn,
all gates, docs-branch sync, scoped commit, lock release) and skipped the rearm-on-touch preamble
entirely. The repository's maintenance parent had been dark since roughly 12:45Z (two dispatched
children tripped their own re-arm guards, and the idle-time watchdog was quota-refused), so the loop
stayed dark for hours past the darkness mark until the user's direct nudge prompted a manual re-arm per
the runtime overlay recipe. The skip left no trace in the done outcome report, while any gated duty
would have failed loudly in the same report.

## Expected behavior

The rearm-on-touch check becomes mechanical inside the done flow, comparable to its sibling gates: a
small script that reads the scheduler state file, classifies the loop state per maintenance Step 0
(parent adopt, darkness re-arm decision, the three bookkeeping edits), performs the automation
primitives through the runtime boundary (or accepts the listing as input), and emits either the applied
edits or an explicit skipped-reason line. done's Step 0 preamble invokes it and the Step 7 report echoes
its outcome, so a skipped or failed check is visible in the run's own record. An alternative shape: fold
the check into the done-lock script's status path so every lock acquire surfaces the loop state without
a separate invocation.

## Suspected root area

`agents/skills/done/SKILL.md` (the preamble duty is prose, outside the gated step sequence);
`agents/skills/maintenance/SKILL.md` Step 0 (defines the check but no consumer script exists);
`agents/skills/maintenance/zcode.md` (the recipe a script would encode). Environment: repo-local
skills checkout, 2026-09-18; the re-arm itself was completed manually in the same session per the
recipe (parent id recorded, absent-since and rearm-note cleared).

Witness 2026-09-20 (a direct done run in this repo): the Step 0 cannot-decide enumeration proved
ambiguous for the freshly-unexplained-absence case - a recorded parent id with `parent_absent_since`
about 19 minutes old and no live pending child. One same-session reading ran the listing (an
unexplained absence younger than one cadence is enumerated as a cannot-decide case, so the listing
runs and the darkness threshold gates only the re-arm decision); a second reading resolved
state-first with no listing (absence younger than the cadence is not darkness, so no classification
needs listing confirmation). The run proceeded on the second reading without a listing and without
bookkeeping, which is exactly the silent-outcome class this item exists to mechanize. The codified
classification classes in the certified plan covering this origin
(`docs/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md`, the rearm_on_touch
task: `listing-required` reasons `fresh-absence`/`null-parent-id` vs `stale-state-listing-required`)
are the fix path; until that plan executes, the ambiguity stands and every manual reading of the
enumeration is a coin flip.
