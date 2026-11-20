# Backlog: dispatch-admission plan certification residuals

Status: open
Priority: low
Cluster: docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md
Driving force: correctness

Origin: the terminal plan-review round (r5, cap closure) over docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md; non-blocking residuals recorded in the round's overflow, carried here as the durable copy for the plan's execution.

Resolve at execution of that plan (fold into its tasks when touched, or close with a recorded reason):

- Multi-plan done boundaries: a done boundary may own several plans (`--owned-plan` is repeatable), while the plan's primary-resolution pin speaks of "the slug"; the merge arm should merge into each owned plan's admission record, or state why one suffices.
- Sweep clearing owner wording: the Task 2 clearing pin removes the record "only while the claim still names the retiring session", but the sweep retires spent claims naming foreign sessions; the sweep arm needs its own owner condition (the claim it is sweeping), not the sweeping session.
- Take-failure orphan race: the lockless take-failure cleanup can in principle interleave with a locked boundary merge and leave an orphan record after record and claim are cleared; inert because the consult passes a record only when the claim resolves and the next new-owner creation replaces it, but the clearing pin may name it.
- Wording nits: the merge-lock assumption's lead-in says "every record mutation holds the existing repo merge lock" beside its own lockless take-failure carve-out; the Standing constraints say the locked-merge pin "additionally" pins lock homes the shared `sweep_env` fixture already pins.
