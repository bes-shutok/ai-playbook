# Execute-plan runtime contract

## Sequential native execution

The execute-plan workflow is host-native and sequential. The parent selects one
plan task, launches one native worker for it, waits for its result, verifies the
result and task checkpoint, completes the task's light boundary, and only
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

## Done-pending handoff reconciliation

When an accepted worker completion is recorded terminal (`status` `done-pending`
in that task's `runtime_state.json` record) while reviewed plan corrections
changed the plan digest or the task checkbox projection afterwards, no preflight
tool reports that handoff as such: the parent reads the task's
`runtime_state.json` record directly and observes the `done-pending` status
beside a changed reviewed plan digest or checkbox projection, with the Step 0.5
stale-digest readiness refusal the correlated signal that prompts that read.
The parent then invokes the
receipt-backed recovery operation once for that task:
`python3 scripts/reconcile_execute_plan_handoff.py reconcile --state
<runtime_state.json> --plan <plan-path> --task <N> --session <the claim-holding session id>`.
Manual `runtime_state.json` edits stay prohibited, and a refusal is never
worked around by hand or by relaunching the completed worker.

The operation owns only receipt validation and one atomic per-task
runtime-state transition. The parent remains the sole caller and keeps every
other runtime-state update, worker launch, and commit. The producer side sits
at acceptance time: when the parent accepts a worker completion, it records
the terminal handoff itself in that task's `runtime_state.json` record,
setting `status` `done-pending` and the accepted worker's terminal completion
evidence as that task's `terminal_receipt` (the per-task accepted-worker
terminal receipt, distinct from Phase 4's run-level landed-archive
`terminal_receipt`). The reconciliation
receipt binds run and plan identity, task identity, the expected manifest
generation, the exact current plan digest, the launched task-scope digest, the
accepted worker terminal receipt, the review evidence for the current bytes (a
current-shape plan-review record whose sidecar binds `source_digest` to the
current plan digest with verdict `yes`), and the observed task checkbox
projection. The repository's active execution claim must name the invoking
session; run identity, task identity, task-scope digest, and expected
generation are re-derived immediately before the write, and any drift refuses
with a named reason.

A successful reconciliation is ONE atomic `runtime_state.json` replacement
that stores, for that task only, `tasks[task_id].handoff_reconciliation` (the
receipt), `tasks[task_id].task_scope_digest` (the launched task-scope digest:
the sha256 of the complete task section with every `- [ ]` or `- [x]`
checklist marker replaced by the literal `- [#]`, each marker's leading
whitespace preserved, derived with the helper's `task_scope_digest`
derivation),
and the reconciled projection (`status` `complete`, `checkbox` per the
reviewed checklist), advancing the manifest generation by one; every other
task record and terminal receipt is preserved verbatim by the same
replacement. A retry that finds the stored receipt equal to the freshly
derived receipt on every identity field and the reconciled projection in place
returns the exact `already-reconciled` success response (`status` `success`,
the unchanged generation, the stored receipt echoed, `next_action` naming the
preflight and commit-gate rerun) without another write or generation
increment; any other difference refuses as a mismatch.

Failure outcomes are fail closed. Stale review evidence (`plan-digest-stale`,
`review-evidence-unusable`, `review-verdict-no`), changed task scope
(`task-scope-changed`), checkbox changes not covered by the reviewed bytes
(`projection-incomplete`), a legacy record without `task_scope_digest` and no
launch-scope proof (`launch-scope-unverified`: the digest derives only from
historical plan bytes whose digest equals the run's saved launch
`plan_digest`), a missing or foreign execution claim, a
missing terminal receipt, a task in any other state, and stale generation or
identity drift all refuse with the state and terminal-receipt bytes unchanged.
An interrupted write leaves either the previous state bytes or the complete
new receipt and projection, never a partial record. The accepted terminal
receipt survives every refusal; the remedy is the repair the named reason
requires (a fresh ready review for the current bytes, or state recovery),
followed by the same invocation retried.

State-shape precondition: the reconciler reads the run's
`runtime_state.json` and requires an integer `generation` plus a non-empty
`run_session_id` on the record. The parent owns both fields from run start:
initialize `generation` to a positive integer when the run's state file is
created, and advance it by one on every later parent-owned state rewrite
(the reconciled projection itself advances it by one per the atomic
replacement above); `run_session_id` is the run's immutable origin identity, retained across an authorized owner conversion; the claim's `session` field carries the current owner through the claim gateway.
A record written without them refuses `state-shape-unusable` before any
read of the task's handoff state.

Both a fresh `reconciled` result and an `already-reconciled` retry require
ordinary preflight and the existing done commit gate to pass before the run
advances to the next task; the recovery never substitutes for either gate.
Scope or digest mismatches that surface before a task launch
route to their existing prelaunch remedies (a reviewed task-scope change to the execute-plan
skill's `Reviewed task-scope change` Active-plan referral procedure, a
reviewed digest mismatch to the Step 0.5 readiness gate's fresh-review path);
this transition reconciles only
accepted `done-pending` handoffs and never touches a task that has not reached
`done-pending`.

## Run-level ownership and repository placement

Every execution-claim `take`, `claim`, and `refresh` passes `--runtime` with the invoking runtime's canonical ID from `projects/.ai-playbook/execute-plan-runtime-inventory.toml` (for example, `codex` or `zcode`); absent or invalid IDs use `unknown` (never infer). The claim persists `runtime_id`, and refresh preserves it; unknown and legacy claims remain shared.

Resume selection binds to the requested plan's own execution identity: start from the plan's exact repository-relative path and saved execution manifest, cross-checked against the plan's execution claim and registered placement, before any saved-manifest refresh or worktree provisioning. An authoring claim, even a same-session one for another item, never selects an execution checkout; missing or conflicting identity evidence preserves the existing work and reports the conflicting plan, owner, or placement, never supplied by an unrelated authoring claim, branch-name resemblance, or newest timestamp.

Dead-run conversion contract (recovery routing lives in the sole recovery
procedure, agents/skills/maintenance/template-execution.md): the Phase 0
gateway owns the exact registered worktree's done-lock only around the
conversion, releasing its own token after every handled success or refusal in
reverse acquisition order (the merge-lock before the done-lock) beside the
repository-wide merge-lock that serializes claim commands from every linked
worktree; abrupt process death leaves a gateway lock in place for the
existing verified-dead-holder recovery only. `sweep` preserves a
claim while a manifest file remains at its exact registered-worktree path,
whatever the branch state, and `take` preserves it through the conversion
arm's evidence-gated refusals: a take whose target is not the manifest's
registered worktree (branch switched, unregistered target) refuses with the
claim preserved instead of reaching the historical stale takeover. With no
registered manifest anywhere, every registered worktree's facts resolved
and no manifest file present, the branch-occupant rule stands, and an
unreadable facts document makes the preservation scan inconclusive (the
claim is preserved, never deleted or taken over). The gateway queries the configured
session status provider for the literal prior-owner ID under a 10-second
bound (paused and unresolved are nonterminal) and converts only after the
parent-owned final review and archive-preparation boundary; every refusal
arm leaves the claim and manifest bytes unchanged, and the gateway accepts
only its own verified lock records. The run log records the owner transition
and the gateway-owned lock disposition but never authorizes conversion.

Preserve the Worktree-first standard: a fresh run uses its provisioned ad-hoc
worktree and branch. Honor the supported `primary` placement when project
policy selects it, including branch verification and serialization. Recovery
of work already performed in the primary checkout remains in that checkout.
Do not move existing work between placements as part of execution.

Each task's boundary is the parent-owned light boundary and follows successful
implementation, validation, and the required intermediate review: the parent
commits plainly by explicit pathspec, runs learn, mirrors new review and
session records to the primary checkout homes, and records one `task_boundary:`
manifest row; the done skill runs only once per run at the final closeout. The
normal commit, completion, Phase 2 validation, Phase 3 review, archive, and
closeout gates remain in force. A worker result or review completion never
substitutes for them.

## Stack-task entry point

The explicit `--stack-task <plan-path> --task <N>` mode first follows ordinary Phase 0 placement, manifest, and execution-claim setup and the selected task's Inclusion Hard Gate. A caller with an existing stack run passes its registered worktree, exact task branch, and run context under the worktrees resolution, or its recorded primary placement (the primary checkout, company task branch, and no-worktree `run_worktree` form) under the primary resolution; accept the recorded primary placement beside the registered worktree form without resetting to base or creating a conflicting claim, so the entry's "ordinary Phase 0 placement" language and the adoption arm cover both resolutions. The stack orchestrator must first record a `stack_branch_transition:` row, refresh the claim's `branch`, update the manifest identity's `run_branch`, and pass the continuity probe against that exact branch. When that transition receipt is present and the claim and manifest agree, the stack-task adoption arm accepts the intentional branch change; it does not apply the ordinary resume refusal for a stale prior branch. A missing receipt or disagreement remains a hard stop. The mode runs exactly one selected task through its implement worker, required intermediate review, task-specific and scope-intersecting plan validation, repository-standard suite, and parent-owned light boundary. The worker records validation evidence before commit; the parent binds it to the resulting commit SHA and branch head in the post-boundary return. The boundary requires both sets to pass, with complete command identities, working directories, exit statuses, and fresh output identities. This explicit one-boundary mode then exits, overriding whole-plan continuous-execution and terminal-response gates; it does not enter Phase 2, Phase 3, archive, or closeout and performs no PR operation.

The ordinary full-plan lifecycle remains unchanged except that Phase 2 runs the plan validation commands and the complete repository-standard suite after all tasks pass and before Phase 3. Resolve the suite from authoritative repository test guidance and inventory. Incomplete guidance or inventory, unavailable commands, or any failure leaves the applicable boundary incomplete; after repair, rerun the complete standard set, and in stack-task mode rerun task-specific validation too.

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
