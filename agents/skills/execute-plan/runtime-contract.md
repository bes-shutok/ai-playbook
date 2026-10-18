# Execute-plan runtime contract

## Sequential native execution

The execute-plan workflow is host-native and sequential. The parent selects one
plan task, launches one native worker for it, waits for its result, verifies the
result and task checkpoint, completes the task's landing boundary, and only
then selects the next task.

Parallelism remains available for independent review-panel workers. The review
panel returns findings to the parent, which owns synthesis and all accepted
changes. Review-fix work proceeds one sequential worker task at a time.

A worker receives the complete task body, canonical allowed paths, declared
validation commands, acceptance criteria, run briefing, and log destination.
The worker edits only those paths, runs the relevant checks, records the output
and changed paths in its execution log, and returns a structured result:

- `success`: implementation and validation completed, with evidence and
  criterion coverage.
- `blocked`: a named hard gate prevents safe completion; include the next safe
action.
- `aborted`: an explicit stop was requested and recorded.
- `error`: a runtime or tool failure occurred.
- `contract-violation`: a worker rule was violated; name the recovery action
  and the evidence.

A log path or narrative claim alone is not evidence. A successful result names
each validation command, its working directory and exit status, where its fresh
output was captured, selected test identities, changed paths measured against
the launch baseline, and the plan acceptance criteria satisfied by those
changes. Parent-owned commit and landing actions are not worker evidence.

## Sequential launch, timeout, and inline fallback

Launch one task at a time in plan order. Record the worker launch and task
identity in the session's `manifest.md` and execution log. Do not launch the
next task until the current worker has returned, its result has been checked,
and its task checkpoint is recorded.

Parent-inline fallback is allowed before a worker launches when native
delegation is unavailable, or after the worker is verified terminal following
a timeout. The parent uses the same task body, path scope, validation commands,
and acceptance criteria. If a timed-out worker may still be active, or its
terminal state cannot be verified, make no parent edits and do not launch a
duplicate worker. Stop and obtain operator disposition.

Use the existing bounded timeout and recovery behavior in the execute-plan
skill. A timeout does not prove worker termination. On relaunch, verify the
branch tip and expected in-flight paths against the recorded pre-restart state.
Append to existing logs; never overwrite a prior pass.

## Run-level ownership and repository placement

The run-level execution claim remains separate from task execution. Use
`scripts/execution_claim.sh` and the repository's execution-claim procedure to
prevent conflicting plan runs. Keep the claim current at the documented phase,
task, and review boundaries, and remove it at closeout or an owned stand-down.
A claim conflict stops the run without modifying another run's state.

Preserve the Worktree-first standard: a fresh run uses its provisioned ad-hoc
worktree and branch. Honor the supported `primary` placement when project
policy selects it, including branch verification and serialization. Recovery
of work already performed in the primary checkout remains in that checkout.
Do not move existing work between placements as part of execution.

Each task's `done` boundary remains parent-owned and follows successful
implementation, validation, and the required intermediate review. The normal
commit, completion, Phase 2 validation, Phase 3 review, archive, and closeout
gates remain in force. A worker result or review completion never substitutes
for them.

## Plans-authoring watchers

The three plans-authoring watcher operations remain supported:

- `plans-watcher-schedule`
- `plans-watcher-supersede`
- `plans-watcher-fire`

They use plans-authoring state and are independent of execute-plan task
execution. Preserve their existing state, identity, and resume behavior.

## Hold and cutover evidence

Before removing a legacy route or recovery surface, use the dated Task 1 survey
and its operator dispositions. Stale records are excluded only when the dated
disposition is recorded. Survey incompleteness alone does not stop route
changes. Before each removal, establish complete consumer-scope coverage or
perform an independent source-by-source check. If a relevant source is
unavailable without equivalent evidence ruling out affected live consumers,
retain the affected route or recovery surface. If evidence verifies a live/resumable affected run, resolve it through its
documented legacy route and record its terminal/completed disposition before
removing the recovery it needs. If terminal/completed evidence is absent, retain
that recovery until disposition. Task 3 repeats the read-only state check before
recovery removal.

Classify every surfaced consumer record by route ownership before any
disposition applies. A session, launcher, automation, or runtime record is an
affected consumer of the removed route only when dated evidence shows its
owning session or launcher can invoke that route; record existence,
repository co-location, or a shared configured root alone never qualifies.
The usual evidence components (record route identity, owning runtime or
project identity, launcher or automation reachability) are illustrative, not
prerequisites; directly verified invocation of the removed route is by
itself sufficient. Evidence is valid only when each cited component is read
from an artifact captured or re-validated within the cutover window, which
runs from cutover start to the check being performed.

Signals conflict when any in-window read artifact indicates invocability and
anything points otherwise. Exclusion then requires operator confirmation,
forced by any invocability artifact regardless of weighing, and is recorded
as a dated operator disposition with the entry fields defined below. A read
that fails, is partial, or yields no citable artifact counts as
uninspectable, including a complete read silent on ownership and an
ownership component with no attempted in-window read; only a complete read
artifact affirmatively identifying the owner as unable to invoke supports
default exclusion. A known-existing record whose source is uninspectable
stays in the affected-consumer set under the retain rule above unless an
operator disposition covers it; this reclassification does not alter that
retain trigger.

Ownership is the membership precondition. The stale-record sentence above
governs records carrying ownership evidence; a record without ownership
evidence, and not covered by the uninspectable-source boundary, is outside
the affected-consumer set for this cutover and needs no disposition.

An attributed dated operator disposition is recorded once in the cutover's
durable implement log, applies for the rest of that cutover only, and binds
to the route and record it classifies. Each entry records its
operator-utterance attribution (the recorded utterance itself identifies the
record and route, or it was given in the cutover's session in direct
response to the survey question about that record), the route and cutover it
was given for, the record identity, and the recording session and date.
Later checks apply the disposition after re-running the lift scan over the
record's sources within the window, re-validating per the evidence
standard. The disposition lifts when fresh dated ownership evidence valid
under the standard exists, regardless of the surfacing party: the record's
own verified launch or a newly active launcher, a newly readable source
artifact, or operator-provided evidence. Operator supersession re-enters
the record and re-applies the hold; a different record with its own
ownership evidence always re-enters; a later cutover re-runs the ownership
check regardless of prior-log dispositions.

These checks are route-removal correctness conditions, separate from the
warning-only survey machinery entry. Missing or incomplete survey evidence
alone does not promote that entry or block beginning route changes.
