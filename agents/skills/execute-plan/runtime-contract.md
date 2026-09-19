# Execute-plan runtime contract

## Provider-neutral contract

The execution workflow uses a capability profile and a normalized result. A
runtime adapter is responsible for translating its local interface into this
contract. The shared workflow never depends on a local command shape, event
envelope, session format, or approval mechanism.

Repository-scoped edits, tests, local recovery, and the per-task commit are
authorized by an execute-plan invocation. A worker does not ask conversational
permission for those actions. Push, deploy, merge, external communication, and
access changes remain gated operations.

### Worker execution contract

The parent supplies one repository-scoped task, its allowed paths, validation
commands, evidence requirements, and the continuation driver receipt. The
worker may edit only the repository and paths in that task, run the named
tests, perform safe local recovery, and complete the per-task commit handoff.
Those actions are already authorized by the execute-plan invocation. The worker
must not ask conversational permission or call a user-question facility for
them. Push, deploy, merge, external communication, access changes, and any
network action remain gated and must be returned as `blocked`.

### Result contract

The worker returns one closed result. `success` includes evidence that proves
the task and its validation completed. `blocked` names a genuine hard gate and
the safe next action. `aborted` records an explicit stop receipt. `error`
records a runtime or tool failure. `contract-violation` records the violated
worker rule, the recovery action, and the evidence that triggered it. Natural
language hesitation is not an approval state. Unknown or malformed adapter
results fail closed as `blocked` or `error`; they are never degraded success.

The parent must read the durable machine state after every worker checkpoint,
claim the next step before launch, and continue automatically while the state is
active. A final response is allowed only after the machine state is `complete`.
Continuation and final-response enforcement are independent capabilities.

## Runtime profile data

The registry is the only owner of runtime identity and capability values. Each
eligible profile has these exact fields:

| Field | Required value |
| --- | --- |
| `id` | Canonical, normalized runtime identifier. |
| `display_name` | Human-readable runtime name. |
| `aliases` | Names accepted by identity normalization. |
| `source_catalogs` | Catalogs that document this runtime. |
| `eligibility` | `eligible` for execute-plan profiles. |
| `adapter_entrypoint` | Adapter boundary selected by the registry. |
| `launch_operation` | Operation that starts one claimed worker step. |
| `wait_operation` | Operation that waits for the worker result. |
| `resume_operation` | Operation that resumes a persisted worker session. |
| `capabilities` | States for the three receipt capabilities consumers read: `parent_continuation`, `final_response`, and `resume`. |
| `fallback` | Non-empty safe behavior for every degraded or unsupported capability. |
| `adapter_version` | Version of the adapter contract implemented at the boundary. |
| `approval_policy` | How the adapter preserves genuine approval gates. |
| `retry_budget` | Numeric profile-owned maximum for bounded runtime errors. |

Capability states are closed: `full`, `degraded`, or `unsupported`. A degraded
or unsupported capability is never interpreted as full. The profile fallback is
returned with the blocked or degraded result. Deferral rows carry the runtime
id, display name, `eligibility: "deferred"`, the accepted `aliases` list, and
the deferral `reason`; they carry no lifecycle capabilities and resolve to the
fail-closed unsupported adapter with the recorded reason.

Runtime-specific launch syntax, event envelopes, hook payloads, and session
identifiers belong in adapter references and profile data. They do not belong
in the provider-neutral section above.

## Runtime selection and activation

The shared execute-plan skill is sourced from the repository's canonical
`agents/skills/execute-plan/` tree and is exposed to hosts through their
configured skill registry or loader. A host selects exactly one eligible
profile by canonical ID or normalized alias from
`projects/.ai-playbook/execute-plan-runtime-inventory.toml`; it must not infer
capabilities from a display name, a local command, or a second capability
matrix. Deferred profiles are not eligible for execution.

Before launch, activation checks resolve the loaded skill path, verify the
registry-selected driver and adapter package bytes, and run local help probes.
Missing files, byte drift, or malformed probe output fail closed. Shared
workflow policy owns authorization, state transitions, evidence, retry budgets,
and continuation. A host-specific adapter owns only protocol translation and
bounded process interaction; it cannot widen policy, bypass approval, or turn a
degraded capability into `full`.

## Normalized result schema

Every adapter result is translated into exactly these fields:

| Field | Meaning and evidence requirement |
| --- | --- |
| `status` | One of `success`, `contract-violation`, `blocked`, `aborted`, or `error`. |
| `reason_code` | Closed reason identifying the result condition. |
| `evidence` | Non-empty, bounded references proving the result. |
| `action_scope` | The repository or gated action that was attempted. |
| `checkpoint_identity` | Stable task and worker checkpoint identity. |
| `generation` | Non-negative claim generation used for fencing. |
| `retry_policy` | Numeric retry budget and retry mode. A worker- or adapter-supplied retry policy is clamped to the profile-owned budget (a contract violation to its single rewrite-and-retry); the worker cannot re-supply attempts. |
| `recovery_action` | Next safe action for the parent or operator. |
| `resume_allowed` | Boolean stating whether the blocked receipt may resume automatically. |

`approval-required` is an input condition translated to `status: blocked` with
`reason_code: approval-required`. It is distinct from worker hesitation and has
no automatic retry. A natural-language request for permission to perform an
already-authorized repository action is a `contract-violation`, not an approval
state. Malformed results fail closed and are never treated as success.

The standard reason codes are `completed`, `worker-hesitation`,
`contract-violation`, `approval-required`, `timeout`, `dirty-worktree`,
`cleanup-required`, `cleanup-unverified`, `malformed-result`, `owner-mismatch`,
`stale-claim`, `explicit-abort`, `runtime-policy-unavailable`,
`runtime-error`, and `precondition-unverified`. The
reference driver and adapter additionally emit `authorized` (envelope
authorization success), `activation-verified` (adapter activation success),
`worktree-witness-unavailable` (broken git scope witness), and the boundary
events `done-pending` and `commit-pending`. This extended set is closed:
normalization rejects a missing or unknown reason code as a malformed result
instead of defaulting it. The CLI create operation emits `created` as its own
CLI envelope outside the adapter normalization boundary (which stays closed
over the documented adapter codes); the CLI reclaim operation emits
`reclaimed` the same way for a successful release, and the CLI readiness
operation emits its decision codes `direct-continuation`, `observe-worker`,
`recovery`, and `terminal-path` as CLI-envelope reason codes the same way.

## Durable task state machine

The normal task path is:

```text
pending -> claimed -> launched -> checkpointed
```

`blocked` is resumable only when `resume_allowed: true`. `aborted` is terminal,
and successful workflow completion is recorded as `workflow_state: complete`
with the Phase 5 checklist and archived-plan receipt only after the machine
terminal predicate passes inside `mark_terminal` (the "Staged terminal
operation (archive gate)" section owns that predicate's fixed order: the
gate clauses plus the archived-plan checks summarized here): the archived-plan path
resolves through the fail-closed path policy (repository-relative,
non-escaping, shell-marker-free under the repository root) to a non-empty
regular file read under the 1,000,000-byte bounded read (an archived plan
over that bound is refused outright as `done-pending` rather than
prefix-scanned, a FIFO or other non-regular file is refused before any open,
and a zero-byte plan is refused as empty) and carries zero unchecked
checkbox lines over its whole
length under the line-anchored reading (a mid-prose mention of the marker
does not count), and `commit_lookup` proves the commit identity.
Any missed check returns the `done-pending` block with evidence
naming the failed check and preserves the manifest unchanged (non-terminal,
no receipt written); the run stays continuable once the failed check passes
(`done-pending` is not a resumable reason, so this block never resumes
automatically). The `mark_terminal` state save is best-effort best-order:
single-machine-source reads dominate, and no lock is held across the whole
check-then-save window over the external archived-plan and commit artifacts
the checks consult, so a refused terminal call is simply re-run once the
named check passes. The terminal checkbox scan is line-anchored over the whole
file and fence-blind by spec in the fail-closed direction: a
`- [ ]` marker inside a fenced code block in the archived plan still refuses
terminal.
The durable claim record contains `token`, `generation`, `owner`, and
`timestamp`. The driver writes the claim before launch and revalidates the
generation before any mutation and before commit handoff. When no owner is
supplied, the driver derives the owner identity from the machine manifest so
separate driver processes operating on one manifest share one owner; a
per-invocation owner is used only for a manifest that has none yet.

The claim `timestamp` is written once at claim time and never renewed for a
single-task claim; a batch member's timestamp is refreshed at activation
(anchor launch, member advance), so its lease measures member liveness. The
`reclaim` operation releases an interrupted claim only once
`CLAIM_LEASE_SECONDS` (14400 seconds, four hours) have elapsed since that
timestamp - an order of magnitude above the execute-plan 20-minute per-worker
timeout, so a live worker's task normally completes well inside the lease. The
constant is driver-owned code: no environment variable and no CLI flag
overrides it, so the no-bypass property covers more than the flag surface. A
task still running past the lease keeps running, but its post-reclaim
checkpoint fails fenced as `owner-mismatch` instead of corrupting state.
Reclaim refuses closed with the resumable `stale-claim` outcome (manifest
untouched) before expiry, on unknown tasks, on closed, replaced, or aborted
claims, and on any task in the progressed set (`done-pending`,
`commit-pending`, `checkpointed`, `complete`); the CLI refuses
`--operation reclaim` without `--task-id` before any driver construction. An
explicitly aborted workflow is never released: for a reclaimable claim on a
task outside the progressed set, the reclaim returns the `explicit-abort`
preserve-and-stop outcome before any lease accounting instead of the
stale-claim refusal; a progressed-task refusal still returns `stale-claim`.
A claim that belongs to a live batch claim group is refused with the same
resumable `stale-claim` outcome naming the group (r3 F1), whatever its lease
state: a group parked at a budget pause is expected to be lease-expired, and
rotating one member away while the group stays active would wedge every
entrypoint, so batch members recover through the group path (`continue
--batch`), never through reclaim - except the one executable exit (r4 F2):
a member whose durable receipt is non-resumable (the task blocked with
`resume_allowed` false) has no group path left, because both group recovery
entries refuse a non-resumable receipt and nothing else closes a group, so
its reclaim is allowed through and atomically fails the group in the same
locked compare-and-swap, releasing the still-staged member claims so their
pending tasks re-enter the queue as individual claims. No lease wait is
re-introduced for that shape: the durable non-resumable receipt is
machine-provable and terminal, so lease freshness there only ever means the
receipt just landed. Member lease timestamps are refreshed at
activation (anchor launch and member advance), so a live member's lease
measures liveness from the moment it became active.
A successful reclaim does not wedge continuation: the replaced
claim is reconciled by rotation (it is never quarantined at startup), so the
documented next step, re-claiming and relaunching the freed task, proceeds
normally.

### Launch record and drift detection

At launch, the driver atomically writes a launch-record snapshot on the claim
together with the `launched` state transition, under the manifest lock:
`launch_record` with `baseline_revision` (the git HEAD at launch), `generation`
(the claim generation), and `launched_at` (a launch timestamp; the launch
record is the only home of that timestamp). Both drift witnesses - the worktree scope witness
on the checkpoint path and the done-boundary verification - compare the live
manifest against that snapshot through one shared helper. The comparison always
consumes a manifest snapshot read under the manifest lock, never an ambient
unlocked read.

Drift rules:

- A changed snapshot is stale: when the live claim `baseline_revision` or
  `generation` no longer matches `launch_record` (another session rewrote the
  manifest after launch - erased or changed baseline, replaced generation),
  both witnesses surface the resumable `stale-claim` outcome, preserve the
  manifest, and refuse the commit handoff. Legitimate checkpoints and checkbox
  bookkeeping do not touch the snapshot and keep both witnesses green.
- A genuinely pre-launch claim (no launch record, no recorded checkpoints,
  pending or claimed task status (or a commit-pending status recorded by the
  parent before any launch), claim state `claimed`) undergoes no drift
  checks.
- Record absence never disarms detection on a claim that has demonstrably
  launched: a claim in any post-launch state (recorded checkpoints or a
  non-pending task status) whose launch record is missing - for example a
  manifest written across the re-activation or rollback window - maps to the
  same resumable `stale-claim` outcome instead of the pre-launch exemption.
- A driver-owned relaunch or a fenced checkpoint that proves a launch on a
  claim whose manifest predates launch records backfills the snapshot from the
  claim's own live fields, keeping later done-boundary checks armed.

### Batch claim groups (Step 1.2 batch contract)

The driver supports the skill's batch implement launch: one launch may carry
up to four file-disjoint tasks as one claim group. The opt-in is default-off
and explicit at every entrypoint (`launch_next_task(batch=True)`,
`continue_parent(batch=True)`, and the CLI `--batch` flag on the `claim` and
`continue` operations). A no-flag claim, launch, or continuation is exactly
the single-task path documented above; it never creates batch fields.

Seeding canonicalizes: the `create` operation and `create_manifest` normalize
raw `Files:` entries through the fail-closed path policy and persist canonical
`allowed_paths` plus a per-task document `ordinal`. Within one task, entries
that resolve to one canonical path (lexical aliases such as `./a` versus `a`,
or an in-repository symlink and its target) are rejected at create. Cross-task
canonical overlap is retained, never rewritten: the queue uses it to stop.

An opted-in claim assembles the maximal file-disjoint prefix of the pending
queue in canonical document order (the persisted ordinal), never skipping past
an overlapping task, capped at four members and eight combined canonical
files. A zero-scope or network-flagged pending task ends the prefix and is
never staged as a member: its envelope can never be authorized, so the batch
contract excludes it up front and its single-task launch path owns the
authorization refusal (r5 F3). Every member's envelope is authorized when the
group is claimed, before any state write, so a member whose envelope cannot
be authorized refuses the batch claim cheaply instead of wedging the group at
its advance (r5 F3). A one-member prefix falls back to the single-task claim.
A
batch claim group bumps the generation exactly once and writes one
authoritative `claim_groups` record: the anchor task, the ordered member list
with explicit member ordinals, the active member, the group generation, the
group state (`active`, `closed`, or `failed`; `failed` is the terminal state
a reclaim-time group release (r4 F2) or an advance-time group failure
(r5 F3) writes, and every consumer keys on `active`, so a failed group routes
no member action), a semantic progress revision mirrored from the manifest's
authoritative `progress_revision` (no second counter), one launch-record slot,
the anchor session id, and a per-member attempt record. The group's
per-member path union is recorded for diagnostics only and never authorizes
an action.

Member claims carry their own canonical allowed paths, a member-scoped policy
token, their ordinal, their attempt, a moving baseline, and the group
reference; they never carry launch records of their own. The anchor's launch
writes the one launch record on the group; every later member resumes that
same anchor session without a second launch record or a second generation
bump. Only the active member may launch, checkpoint, resume, or close, and
member-scoped authorization covers both the action policy and done-boundary
verification: a member's worker result, checkpoint, or done commit that
touches another member's file is rejected exactly as a group-external escape
would be, even though the group contains both files.

A member done closes that member and advances the group in the pinned
active-member ordering under the same manifest lock: the next member is
initialized from the completed member's commit (the moving baseline) with a
freshly authorized member-scoped policy token, and the done result returns a
typed `resume_member` action naming the group, the next member ordinal, the
anchor session, the fresh policy token, and the moving baseline. When the
next member's envelope cannot be authorized at the advance (a state drift;
claim-time authorization and the prefix exclusion make it unreachable for a
well-formed group), the group fails atomically in the same locked save that
closes the completed member - the same terminal `failed` state the
reclaim-time release writes, with the staged member claims closed so their
pending tasks re-enter the queue as individuals - and the completed member's
done handoff lands; refusing the done instead would wedge the group forever,
because every retry re-fails the same authorization (r5 F3). The same
release shape fires when no member session exists anywhere for the anchor
resume (a schema-legal receipt stream that never carried a session id): the
done lands and the staged members re-enter the queue as individuals (r6 F1).
The first
member is reached through `launch`; later
members may be reached only through `resume` on the anchor session, and a
launch that would bypass that rule fails closed. The generic next-claim stays
suppressed until the group closes; the last member's done closes the group and
releases the single-task queue.

Late member receipts fail closed: a success, error, done, or checkpoint
receipt for a closed, superseded, aborted, or old-attempt member is a blocked
`stale-claim` outcome with no state mutation. An envelope carrying batch
progress (batch id, member id and ordinal, attempt, anchor session id) is
validated against the live group state, and any mismatch, stale attempt, or
cross-member token is refused. Startup reconciliation never quarantines a
live group's active member as an ambiguous worker (the dirty-worktree gates
still apply), and it never quarantines a member released by a failed group's
terminal release either (r5 F1): a failed group owns no live work, so its
closed member claims' launch evidence resolves through the group record as
history, not as a live launch window, and their tasks re-enter the queue as
individual claims; the batch continuation resolves the active member and
anchor session from the reloaded group record.

#### Group lifecycle transition table (normative)

The group record is a three-state machine over `active`, `closed`, and
`failed`. Single choke point invariant: every mutation of
`claim_groups[id]["state"]` or `active_member` routes through one private
driver primitive (`_set_group_state`); no site other than that primitive
writes group state, and the semantic progress revision mirror rides every
transition. The table below is the total lifecycle: every operation x state
cell has a defined outcome, and the driver suite's exhaustiveness test drives
every operation from every state asserting no state is wedged (every state
has an executable next action or is a documented terminal) and that after
every operation every task status agrees with its claim state.

| Operation | `active` | `closed` | `failed` |
| --- | --- | --- | --- |
| `claim` (flagged or not) | Blocked `stale-claim`: the live group holds the one implement launch. | No live group remains: the normal claim rules take the next pending task; a drained queue returns `claimed: false`. | Same as `closed`: the released members' pending tasks are claimed as fresh individual claims. |
| `launch` / `launch_next(batch=True)` | Claims nothing new while the group lives: the anchor's first launch writes the ONE group launch record and re-arms the active member through the launch fence (which requires state `active` plus the active member), and an already-claimed group routes to the member continuation; a non-anchor member launch attempt is refused `stale-claim`. | Member claims are closed: any member launch attempt is refused `stale-claim` (unknown or closed batch group) and the queue continues individually. | Same as `closed`: a terminal group routes no member action; the released tasks are claimed individually. |
| Checkpoint success (member receipt) | The named active member lands `done-pending` (its claim stays live); the group is unchanged. A receipt naming any other member is fenced `stale-claim` with no mutation. | Member fence refuses: `stale-claim`, no mutation. | Member fence refuses: `stale-claim`, no mutation. |
| Checkpoint blocked (non-retryable receipt) | The named active member persists blocked through the shared blocked-persist tail; the group stays `active` with the anchor session captured from the first receipt carrying one. Any other member: fenced `stale-claim`, no mutation. | Member fence refuses: `stale-claim`, no mutation. | Member fence refuses: `stale-claim`, no mutation. |
| Retryable-error receipt (budgeted rewrite or bounded retry) | The member retry runs through the group's own continuation primitive: with a session anywhere the anchor-session resume window opens (group unchanged, the member's task status never regresses); with no session anywhere the receipt persists as the member's blocked state and the group stays `active` for group-path recovery. | Member fence refuses: `stale-claim`, no mutation. | Member fence refuses: `stale-claim`, no mutation. |
| `done` (member handoff) | The completed member closes and the group advances under one lock: the next member is activated (state stays `active`, the active member moves), the last member closes the group (`closed`, active member cleared), or an advance-time failure fails the group atomically (`failed`, staged members released) while the done lands (r5 F3). The advance-time failure arms are the next member's envelope authorization failing (a state drift) and no member session existing anywhere for the anchor resume (r6 F1); every retry would re-fail on the same state, so refusing the done is never an outcome. | A late done replay from the closed progressed member is fenced by the member receipt fence: blocked `stale-claim`, no mutation (a terminal group routes no member action). | A late done replay from a released never-launched staged member (claim closed) is unfenced done evidence: blocked `done-pending`, no mutation; a replay from the progressed member (checkpointed, its own closed claim) fences as `stale-claim` through the same member receipt fence. |
| `resume` | Selects only the live group's active member with a resumable receipt and resumes the anchor session; a session-less blocked anchor recycles into a fresh launch through identity rotation. A member outside the active seat is refused `stale-claim`. | No active member exists: any member selection is refused `stale-claim`; with no resumable blocked task the outcome is the ordinary no-resumable-task block. | The released members' tasks sit pending or checkpointed with claims closed or replaced, so no resumable blocked task exists: the ordinary no-resumable-task block stands (`stale-claim`). |
| `continue --batch` | Advances the group through its active member: anchor-session resume, the anchor's initial launch when no session exists yet, the session-less blocked-anchor recycle, and a refused non-resumable receipt. | No live group remains: the batch opt-in re-batches the remaining queue into a NEW group when the disjoint prefix allows, else it falls through to the generic single-task continuation; with nothing pending the terminal-evidence block stands. | No live group routes the continuation: the batch opt-in assembles a NEW group from the released tasks when the disjoint prefix allows (the failed record stays terminal, never revived), else it falls through to the single queue; with nothing pending the terminal-evidence block stands. |
| `reclaim` (resumable member) | Refused `stale-claim` naming the group, whatever the lease state (r3 F1); recovery is the group path (`continue --batch`). | The claim is closed, outside the reclaimable set: refused `stale-claim` as no reclaimable claim. | Same as `closed`: the released claims (the exited member's is `replaced`, a released staged member's is `closed`) are outside the reclaimable set; no exit is needed because the group already routes nothing. |
| `reclaim` (non-resumable member, `resume_allowed: false`) | The one executable exit (r4 F2): reclaim succeeds with no lease wait and the same locked compare-and-swap fails the group (`failed`, active member cleared), closes the staged claims, and resets the member's task to pending. | Refused: the claim is closed and there is nothing to reclaim. | Refused: the released claims are outside the reclaimable set (the exit's own member is `replaced`, a released staged member is `closed`); the exit already ran. |
| Group release (atomic fail plus staged-member release) | Reached only through the three arms above (the reclaim exit, the advance-time authorization belt, and the advance-time session-less release, r6 F1): one locked save writes `failed`, clears the active member, closes the staged claims, and returns their tasks to pending. | Not reachable: every release arm is guarded by the live-group fence, so a terminal group is never re-released. | Not reachable for the same reason; `failed` is terminal. |

No cell is undefined. From `active` the run always has forward motion: the
member continuation, the reclaim exit for a durably non-resumable member,
and the done handoff itself, which lands even when the advance fails the
group (r5 F3, r6 F1). `closed` and `failed` are documented terminals whose
only forward motion is the ordinary individual queue.

### Startup reconciliation

Startup reconciliation owns crash recovery. It reloads the durable manifest,
checks the claim, logs, task identity, and exact repository commit, and records a
completed checkpoint when a commit is provably present. It never relaunches a
provably completed commit or an ambiguous live worker. A commit recovered on
this path is verified against the claim's launch baseline exactly as the done
handoff verifies it: an out-of-scope or escaping committed path blocks the
reconciliation with the same boundary outcome the done handoff produces.

Before launch only, the startup dirty-worktree gate tolerates ambient noise: a
dirty worktree consisting purely of untracked allowlisted entries (the
`.DS_Store` family: `.DS_Store`, `.DS_Store?`, `._.DS_Store`) blocks with the
resumable `cleanup-required` reason instead of the non-resumable
`dirty-worktree`. Anything outside the allowlist, including
tracked modifications, keeps the hard block on the same path. File mtime is
never the ambient-versus-worker discriminator because a worker can forge it:
after the claim's launch record exists, a tracked out-of-scope change is
indistinguishable from a worker-caused escape and stays non-resumably
blocked even when it wears an ambient name (r2 F2). The checkpoint scope
witness consults the allowlist only as a resumable downgrade when every
out-of-scope path is proven untracked by the same porcelain witness
(``??`` status) and matches the allowlist; a tracked out-of-scope
modification, a quoted or malformed path rendering, or any witness failure
keeps the non-resumable contract violation. Tasks already
progressed past launch (done-pending, checkpointed, complete) defer the
startup dirty-worktree check; ambient or worker dirt in that window is
enforced by the done-boundary clean-state witness instead.

## Transition table

| Event or condition | Required evidence | Claim handling | Retry budget | Resulting state | Recovery action |
| --- | --- | --- | --- | --- | --- |
| `started` | Claim record and launch receipt | Create token and generation before launch | 0 | `launched` | Wait for a bounded result. |
| `success` | Normalized result plus checkpoint evidence | Keep generation and persist checkpoint once | 0 | `done-pending` (the done handoff closes it as `checkpointed`) | Refresh manifest and select the next incomplete step. |
| `contract-violation` | Violated rule and worker evidence | Keep claim fenced | 1 rewrite-and-retry | `blocked` until retry succeeds | Rewrite the worker instruction once, then retry; stop after one retry. |
| `blocked` | Reason code, action scope, and safe next action | Preserve claim unless takeover is proven safe | 0 unless profile declares a bounded recovery | `blocked` with `resume_allowed` | Preserve manifest and wait for the named gate or operator action. |
| `approval-required` | Exact requested action scope and approval evidence | Preserve claim and generation | 0 | `blocked`, `resume_allowed: true` | Await approval; never retry automatically. |
| `aborted` | Explicit stop receipt and owner | Release only the matching claim | 0 | `aborted` | Do not resume without a new explicit run. |
| `error` | Runtime error code and bounded evidence | Preserve generation for reconciliation | Numeric profile budget | `blocked` or terminal after budget exhaustion | Reconcile, then retry only within the numeric budget. |
| `timeout` | Deadline, operation, and cancellation evidence | Do not take over an ambiguous live claim | 0 | `blocked`, `resume_allowed: true` | Verify process cleanup before any later claim. |
| `dirty-worktree` | Paths and clean-state evidence | Preserve claim and quarantine generation | 0 | `blocked`, `resume_allowed: false` | Require explicit reconciliation before relaunch. |
| `cleanup-required` | Ambient noise paths on the pre-launch startup path | Preserve claim and quarantine generation | 0 | `blocked`, `resume_allowed: true` | Remove allowlisted ambient entries or resume after cleanup. |
| `cleanup-unverified` | Owned process and failed termination evidence | Preserve claim; never take over | 0 | `blocked`, `resume_allowed: false` | Require operator cleanup verification; do not retry. |
| `reclaimed` | Expired claim lease (at least `CLAIM_LEASE_SECONDS`) on a claim in `claimed`, `launched`, or `blocked`, with the task outside the progressed set and the claim not a member of a live batch claim group (a live-group member is refused with the resumable `stale-claim` outcome naming the group, r3 F1; the one exit, r4 F2: a live-group member whose task is blocked with `resume_allowed` false reclaims through with no lease wait, and the same compare-and-swap fails its group) | Replace generation and token, mark the old claim `replaced`, reset the task to `pending` with the previous session's resume fields stripped, recorded checkpoints preserved as evidence; on the r4 F2 exit the group is also marked `failed` with its active member cleared and the still-staged member claims closed | 0 | `pending` task under the `replaced` claim; the next claim takes the freed task under a fresh generation; on the r4 F2 exit the staged members' pending tasks also re-enter the individual queue | Re-claim and relaunch the freed task; a post-reclaim checkpoint or launch receipt from the replaced owner fails fenced as `owner-mismatch`, while a late done handoff refuses as unfenced done evidence; the replaced claim is reconciled by rotation and never quarantined at startup; an explicitly aborted workflow returns `explicit-abort` and is never released. |
| `commit-pending` | Started receipt and task identity | Keep claim fenced during reconciliation | 0 | `blocked`, `checkpointed`, or `aborted` (the wedged-claim abort exit) | Inspect the exact commit before deciding whether work is complete. Abort with the current token is permitted when the recorded commit provably does not exist (the wedged-claim runtime exit; preserve-and-stop). |
| `done-pending` | Worker checkpoint plus done handoff evidence | Keep claim until done boundary closes | 0 | `blocked` or `checkpointed` | Do not launch the next task until commit, checkbox, clean state, and log evidence exist. |
| `committed` | Commit identity, checkbox, clean state, and log evidence | Close matching claim | 0 | `checkpointed` | Record the commit and continue once, idempotently. |

Illegal transitions, unknown statuses, missing evidence, generation mismatch,
malformed approval data, and cleanup uncertainty fail closed. The transition
table is part of the contract, not an instruction to bypass a missing
capability or a real approval gate.

## Registry and adapter ownership

The machine-readable registry owns canonical IDs, aliases, profile fields, and
capability states. The driver consumes the registry and owns state transitions.
An adapter owns only protocol translation and bounded process interaction. A
probe validates parity with the registry but does not declare a second capability
matrix. Tests use an independent expected-ID fixture so a missing profile cannot
silently redefine the documented runtime set.

## Durable driver boundary

The executable driver is `scripts/execute_plan_runtime.py`. It is intentionally
small and standard-library-only so every supported host can use the same state
machine. The authoritative machine manifest is
`{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json`; the human-facing
`manifest.md` is an orchestrator-maintained audit receipt and is never used as
the source of truth. The runtime driver does not write or authorize from that
Markdown receipt. Machine-manifest writes are atomic, mode `0600`, and fenced
by a generation token and owner claim.

The driver accepts adapter results only after closed-result validation and
default-deny policy validation. It persists a worker checkpoint as
`done-pending`; it cannot select or launch another task until the existing
`done` workflow supplies commit identity, the completed checkbox, clean-state
evidence, and the preceding worker log evidence. For a claim with a recorded
launch baseline, the done boundary verifies the committed artifact instead of
trusting the attestation: the commit must be a descendant of the baseline,
`git diff --name-only <baseline> <commit>` must stay inside the token's
allowed paths, and the worktree must be clean per the git witness rather than
the worker-asserted `clean_state`; a violation refuses with `commit-pending`
semantics and `resume_allowed: false`. The driver records those
facts and never creates commits itself. Replaying the same checkpoint or done
receipt is idempotent.

The driver treats worker hesitation about an already-authorized repository
operation as `contract-violation`, never as a user-question state. Genuine
approval requests preserve the exact action scope, use a zero retry budget, and
remain `blocked` until the external gate is resolved. Unknown result fields,
invalid action scope, generation mismatch, path traversal, network attempts,
protected-file attempts, dirty worktrees, and unverified process cleanup fail
closed while preserving the manifest.

When a process ends between commit creation and checkpoint persistence,
startup reconciliation may complete the checkpoint only after an injected
repository lookup proves the exact commit identity. Ambiguous live workers,
owner mismatches, claim-before-launch interruptions, and uncommitted dirty
worktrees remain quarantined and are never relaunched automatically.

## Action envelope and policy token

Before launch, the driver validates one typed action envelope:

```json
{
  "repo_root": "/canonical/repository/root",
  "allowed_paths": ["path/to/task/file"],
  "operation_kind": "repository-task",
  "network": false,
  "evidence": ["task identity and scope receipt"]
}
```

The driver canonicalizes `repo_root` and every relative allowed path, rejects
absolute paths, parent traversal, NUL bytes, shell substitution, command
chaining, option-like paths, and symlink escapes, and verifies that policy-file
changes are listed. An empty `allowed_paths` list is rejected: empty scope is
the widest possible scope and fails closed, mirroring the adapter's token
validation. Operation kinds default-deny to repository task, read,
write, done handoff, and checkpoint. Network is false unless a separate gated
operation is explicitly handled, and gated operations never receive a task
token.

The driver issues an opaque policy token containing the canonical root, allowed
paths, operation kind, network decision, generation, and bounded evidence. The
adapter accepts that token as its only authorization input and binds the same
token to the process runner invocation. The runner must reject a launch or
resume without the validated token and receive the canonical repository root
and allowed-path policy as execution-boundary data. It must not receive raw
unmediated commands. A runtime that cannot enforce the envelope and token
boundary returns `blocked: runtime-policy-unavailable` before launch.

Post-launch results are checked again. Direct shell operations and indirect
shell or path traversal attempts fail closed as `contract-violation`. An action
target outside the token's allowed paths, or an unlisted policy-file change,
cannot be converted into a successful checkpoint. The driver enforces this
with a git witness: it records a baseline revision on the claim at launch
(blocking with `worktree-witness-unavailable` when HEAD cannot be resolved,
never storing an empty baseline) and, before accepting a success checkpoint,
compares the union of `git diff --name-only` against that baseline and the
untracked entries of `git status --porcelain --untracked-files=all` with the
token's allowed paths, resolving symlinks so an in-scope path replaced by an
out-of-repository symlink is a violation. Git invocations disable
`core.quotePath` so names compare literally. An out-of-scope change returns
`blocked: contract-violation`; a broken witness, or a recorded baseline with
an empty scope, returns `blocked: worktree-witness-unavailable`. Both fail
closed.

## Driver entrypoint and reload contract

The parent continuation calls the driver entrypoint in this order:

1. Reload and validate the structured machine manifest.
2. Reconcile `started` and `commit-pending` claims against task identity,
   append-only telemetry, and the exact repository commit.
3. Select the first incomplete task and atomically claim it before launch.
4. Issue the typed action envelope and launch through the registry-selected
   adapter.
5. Normalize the result, persist the checkpoint, refresh and validate the
   manifest, then select the next defined step only after the done boundary.

The executable interface is `scripts/execute_plan_runtime.py` with
`--operation <name>`. The CLI operations and the driver methods they map to
are:

| CLI operation | Driver method |
| --- | --- |
| `create` | `create_manifest` (via `_operation_create`; seeding only, runs before any driver construction) |
| `claim` | `claim_next_task` |
| `checkpoint` | `record_worker_checkpoint` |
| `done` | `record_done` |
| `resume` | `resume` (also writes the peer-resume marker a scheduled watcher stands down on) |
| `continue` | `continue_parent` (also surfaces `terminal_result` on a complete manifest; also writes the peer-resume marker) |
| `terminal` | `mark_terminal` (the terminal receipt itself is read back through `continue`/`resume` on the completed manifest) |
| `precondition` | `verify_preconditions` (manifest-free: requires `--predecessors-file` instead of `--manifest`; never loads a machine manifest) |
| `interrupt` | `record_interrupt` (persists `user_interrupt` under the manifest lock; keeps `workflow_state`) |
| `progress` | `record_progress` (advances the monotonic semantic progress revision) |
| `watcher-schedule` | `record_budget_boundary` over `RuntimeResumeWatcherAdapter` (takes the probe report; runs the CLI fallback chain: echoed automation create, launchd one-shot, report-only; the schedule arm alone resolves the launchd carrier identity, passes that one resolution to the chain it arms, and persists the outcome-stamped record into the receipt, r6 F5, r6 F7) |
| `watcher-supersede` | `build_supersede_transition` + `record_resume_watcher` (clears a pending watcher under compare-and-swap; the outgoing receipt's armed carrier is torn down in the same operation, r6 F3) |
| `watcher-fire` | `fire_watcher` over `RuntimeResumeWatcherAdapter` (the automation prompt's fire entry: evaluates the fences and four stand-down checks, clears the guard flag and fired marker only on a resume decision, and consumes the launchd one-shot carrier from the receipt alone) |
| `readiness` | `readiness` (via `_operation_readiness`; read-only decision, requires `--plan`; `persist_construction=False` construction, the operation writes nothing) |
| `reclaim` | `reclaim` (via `_operation_reclaim`; lease-gated interrupted-claim recovery, requires `--task-id`; the one lease-waived exit reclaims a non-resumable live-group member and atomically fails its group, r4 F2; `persist_construction=False` construction, the claim compare-and-swap is the operation's single write) |

The address fan-out parent surface is a separate executable boundary (r2
F9): `python3 scripts/execute_plan_address_fanout.py --operation <op>
--input '<json>'` exposes the parent-side pure operations `plan` (the
deterministic file-affinity grouping over a `finding_files` document),
`issue-token` (worker scope token plus its digest for one round, worker,
and attempt), and `verify-submission` (the production patch witness over a
submission JSON document against `--repo-root`, returning the violation
list and the accept decision). The full parent loop (`run_address_fanout`)
stays the in-process entrypoint: its worker and cancellation ports are the
parent's own launch and cancellation machinery and cannot be supplied
through a shell command; the lifecycle machine-state writes it drives stay
the driver's `record_address_fanout` under the manifest lock.

The three `watcher-*` operations return three distinct envelope shapes
(r2 O22), all JSON objects on stdout: `watcher-schedule` returns the
normalized outcome envelope (status, `reason_code` of
`resume-watcher-scheduled` on an install, `resume-watcher-superseded` on a
boundary supersede that cleared a watcher, or `watcher-cas-stale` when the
compare-and-swap was refused and any pending watcher is still armed (r3 F7,
with `cas_applied` False on the stale outcome), evidence naming
the boundary, classification, and scheduling trail, plus the
`resume_watcher` receipt, the full `scheduling` object with its per-scheduler
trail, the rendered `projection`, and `manual_command` on every supersede
outcome (the exact manual resume command, emitted because the boundary
schedules no watcher, not only for the report-only scheduling trail));
`watcher-supersede` returns the driver's compare-and-swap
outcome (status, reason code, evidence, `resume_watcher` after the clear,
and `cas_applied`); `watcher-fire` returns the fire decision itself
(`decision` of `resume`, `stand_down`, or `refuse`, the stand-down
`reason` or the `mismatches` list, `guards_cleared` on every decision -
False on refuse or stand-down and whenever the configured cleanup did not
end cleared, the three prompt outcomes being cleared, attempted but not
achieved, and not configured (r3 F4, r5 F5) - `relaunch`, the
`guard_cleanup` receipt whenever a guard cleanup is configured (its outcome
names cleared, refused, or absent), the rendered `prompt` on
a resume decision, and the `sentinel` consumption receipt for the
launchd one-shot when the receipt records an armed carrier, or when the
payload names an explicit `sentinel_path` override - the operator's
manual-recovery input, which takes precedence over the receipt's carrier
record for that consume and is refused, with nothing consumed and no spent
marker written, for a path outside the sanctioned runtime directory (r6 F6);
on a supersede whose outgoing receipt recorded an armed carrier the
`watcher-supersede` outcome additionally carries the `carrier_teardown`
receipt (bootout plus sentinel consume, receipt-only, r6 F3)), augmented with
`checkpoint_identity`, `action_scope`,
and `watcher_id`.

Receipt-is-the-only-carrier-identity invariant (G2): the schedule arm alone
resolves the launchd carrier identity - once, and it passes the same
resolution to the chain it arms (r6 F7) - and persists the carrier record
into the receipt under `armed_launchd` (on an armed record: `armed: true`,
`label`, `job_dir`, `plist_path`, `sentinel_path`, `fired_marker_path`). The
record states the arm's actual outcome, not merely its intent (r6 F5): a
schedule that arms no launchd records an explicit `armed: false` record
naming why - an automation echo, or a reachable launchd link that refused
(sentinel self-disable, spent-pair cleanup refusal, label conflict, plist
write failure, bootstrap failure, rectified into the persisted receipt
before the schedule result returns). Every fire, clean, and consume path
reads the carrier from the receipt and from nothing else, with one
documented exception: the fire payload's explicit `sentinel_path` override
is the operator's manual-recovery input, takes precedence over the receipt's
carrier record for that consume, and is scoped to the sanctioned runtime
directory exactly like the scheduler's spent-pair cleanup (r6 F6). No code
outside the arm/schedule path calls an identity-derivation helper, a receipt
without a carrier record consumes nothing, and a structural test pins the
whole derivation surface (including the record builder, the plist-path
derivation, and the chain builder's own callers) so no fire-path derivation
can regenerate (r6 F9, r6 F10). A supersede whose outgoing receipt records
an armed carrier tears that carrier down in the same operation: the
recorded plist is booted out and the recorded sentinel/fired pair is
consumed, receipt-only, so the orphan job's later fire cannot leave a bare
sentinel that refuses every subsequent arm (r6 F3).

The plans authoring watcher mirror is a manifest-free executable boundary
(r2 F11): the same `--operation` CLI drives the `PlansAuthoringWatcherAdapter`
over the authoring machine-state JSON named by the payload `state_path`
(`{tmp_dir}/plan-requirements-<slug>.json`), so no `--manifest` is passed
and no runtime driver is constructed: `plans-watcher-schedule` (payload
`state_path`, `plan_path`, the probe report as `probe_report` or the
payload itself, optional `plan_slug`, `automation`, `job_dir`,
`sentinel_path`, `boundary_kind`; returns the same envelope shape as
`watcher-schedule`), `plans-watcher-supersede` (payload `state_path` plus
`reason`; returns the authoring compare-and-swap outcome with
`superseded_watcher_id` and `cas_applied`), `plans-watcher-fire` (payload
`state_path`, optional `watcher_id`, `flag_path`, `fired_path`; returns
the same fire-decision shape as `watcher-fire`; `flag_path` defaults to
the canonical guard flag path like the runtime boundary (r3 F4), so omit
it only where this boundary armed no flag, such as the weekly secondary),
`plans-resume-marker` (payload `state_path` plus optional `evidence`
lines; records the resume-path re-entry the shared peer fence stands down
on), `plans-progress` (advances the authoring progress revision),
`plans-interrupt` (payload `state_path` plus optional ISO-8601
`user_interrupt`), and `plans-terminal` (payload `state_path` plus `kind`
of `complete`, `archived`, or `aborted`).

This table is the closed CLI operation boundary (r1 F22: `interrupt`,
`progress`, the three `watcher-*` operations, and the `plans-*` authoring
operations are part of it); the
standing resume watcher's pause-protocol invocation lives in the SKILL.md
Budget gate pause protocol and its Standing resume watcher subsection.

The `claim` and `continue` operations accept an explicit `--batch` flag that
opts that invocation into the batch claim-group protocol (see the batch claim
groups section); without the flag both operations keep the single-task
behavior documented here.

The driver, not the shared prose or the adapter, owns these transitions. A
reload resumes from the first incomplete step and never relaunches a
checkpoint whose exact commit is already proven.

### Readiness decision

The `readiness` operation answers one question for the orchestrator: can the
run continue directly, or must it observe, recover, or terminate? The
decision is read-only over exactly one manifest snapshot: the driver
acquires the manifest lock, loads and validates the machine manifest (fail
closed on a missing or malformed manifest), releases the lock, and returns
without any write path. The CLI operation constructs its driver with
`persist_construction=False`: owner backfill and capability receipts are
never persisted at construction, so the manifest bytes are identical before
and after the operation on an already-owned manifest, and the decision
itself still writes nothing. All five machine-owned conditions are
evaluated
against that one snapshot, so the decision is internally consistent even
under concurrent claim or checkpoint writes; the plan file is read outside
the lock because the lock fences the machine manifest only.

The closed decision set is `direct-continuation`, `observe-worker`,
`recovery`, and `terminal-path`. The evaluation order is fixed and is
independent of that enumeration: `terminal-path` first, then
`observe-worker`, then `recovery`, then `direct-continuation`; the first
decision whose predicate holds is returned:

- `terminal-path` fires only when every task is complete or checkpointed
  (or carrying `checkbox: true`) and the machine `workflow_state` is
  `active`, `complete`, or `terminal`; an
  already complete manifest lands here rather than in recovery. The
  `terminal-path` outcome reports an empty failed-conditions list by
  design; advisory condition failures evaluated before it are dropped.
- `observe-worker` fires when a claim in state `claimed` or `launched`
  exists on a task outside the progressed set; the decision names that task
  id and the caller observes that live worker with a bounded repeatable wait
  instead of launching anything. The claim token, generation, and task
  status are byte-identical after the call.
- `recovery` fires when any failed condition remains. Each failed condition
  names its witness, and the outcome carries one recovery action:
  `stop-or-recovery` for a machine state that is not `active`,
  `preserve-and-reconcile` for an unresolved handoff, a fenced claim, or an
  unprovable next task, and `correct-plan-through-skill-gated-plan-edit` for
  plan-manifest disagreement. When several conditions fail, the outcome
  carries the recovery action of the first failed condition in evaluation
  order: an empty manifest, then machine state, then unresolved handoff or
  fenced claim, then plan shape or plan-manifest disagreement, then
  unprovable next task.
  One envelope-level outcome sits outside that failed-condition enumeration:
  when the manifest lock is held by another owner at decision time, the
  operation returns the `recovery` decision with recovery action
  `resumable-conflict`, a transient contention envelope whose reading is to
  retry the readiness call after the lock is released; nothing is blocked
  durably and the manifest is unchanged.
- `direct-continuation` fires when all five conditions pass.

The five machine-owned conditions:

1. The machine manifest carries at least one task. An empty manifest
   continues nothing: the failed condition names it ("machine manifest
   carries no tasks") with a stop-or-recovery action instead of a
   direct-continuation whose next task is undefined.
2. Manifest schema and ownership validation passes and the machine
   `workflow_state` is `active`. An already `complete` manifest is handled
   first by the terminal-path decision; `aborted` or `blocked` is a failed
   condition naming the machine state with a stop-or-recovery action.
3. No unresolved handoff or fenced claim exists: no task in `done-pending`
   or `commit-pending`, and no claim in state `blocked`.
4. Plan-manifest agreement. For each manifest task recorded in the
   progressed set (`done-pending`, `commit-pending`, `checkpointed`,
   `complete`), the plan's matching `### Task <N>:` section contains no
   unchecked checkbox line. A plan with zero recognizable `### Task <N>:`
   headings fails the plan condition outright ("plan carries no
   recognizable task sections"), so a wrong `--plan` file cannot produce a
   vacuous direct-continuation while no task has progressed. The task
   number is the id suffix after `task-`;
   the heading line matches `### Task <N>:` with the number terminated by
   its colon, so the Task 1 section never scans Task 10's heading or
   content. The section scan is fence-aware for single-level triple-backtick
   fences: a `## ` or `### Task <N>:` line inside one such fence is fenced
   content, not a break marker, so a fenced example cannot truncate the
   section and hide an unchecked checkbox after it. Residual fence shapes
   (tilde fences, indented fence-lookalikes, nested fences of different
   widths, unclosed fences, or a
   fenced pseudo-heading before the real task heading) can still truncate or
   shift the mid-run readiness scan and degrade that detection to the
   terminal backstop, which scans the whole archived plan fence-blind and
   fails closed (residual tracked as
   `docs/history/backlog/2026-09-17-fence-robust-checkbox-scanning.md`).
   Any unchecked line in a
   progressed task's section is disagreement, and the manifest wins per the
   seeding boundary: the plan is corrected through the skill-gated
   plan-edit step, never by mutating the machine manifest. A pending task's
   unchecked boxes agree with the manifest.
5. The next incomplete task is provable: the first incomplete task in plan
   order exists and its status is `pending`, so a claim can take it.

A missing, unreadable, or over-limit `--plan` file (over the 1,000,000-byte
bounded read) is a fail-closed blocked outcome
(reason `precondition-unverified`, decision `recovery`) naming the plan path
and leaving the manifest untouched; the CLI refuses `--operation readiness`
without `--plan` before any driver construction. The digest, review-scope,
and unresolved-finding conditions stay delegated to the Step 0.5 validator
and the review artifacts; the readiness operation never reads review sidecars;
the terminal gate's clean-round sidecar read is the only documented
extension, so there is one owner per condition.

The structured `runtime_state.json` is the sole machine-state source. The
orchestrator-maintained Markdown `manifest.md` is a human audit receipt, and
`agent-logs.md` is append-only telemetry. The orchestrator synchronizes those
documents from structured-state reads; neither document can authorize a
transition by itself. Machine-state writes are atomic, locked,
generation-fenced, and revalidated after every checkpoint.

### Staged terminal operation (archive gate)

The `terminal` operation is staged: the payload `stage` field selects
`pre-archive` or `final`, `final` is the default, and the default preserves
the original input contract (archived plan path, commit identity, Phase 5
checklist). An unknown stage refuses as blocked `done-pending`. The two
stages own the archive gate ordering: the pre-archive stage proves
eligibility before any move, and the final stage verifies the landed
archive before completion.

The `pre-archive` stage input carries the active `plan_path`, an optional
candidate `destination`, the `review_sidecar` path, `last_commit_sha`,
`phase5_checklist`, and an optional structured `residual_policy` (the named
finding ids as integers matching the version-1 sidecar's integer finding
ids, the grant source, and the recorded-at epoch); the policy is omitted on
a blocking-clean exit. Its eligibility predicate evaluates in one fixed order
and returns the `first failed condition` only, as a blocked `done-pending`
outcome that leaves the machine manifest untouched (no manifest state
beyond construction-time manifest writes (owner, receipts, updated_at)): (1) machine
completeness (non-empty task map, every task complete, every claim record
closed, no pending done handoff); (2) input shape guard and active-plan
integrity and identity (a non-empty `plan_path`, `review_sidecar`, and
`phase5_checklist`, a well-formed `last_commit_sha`, and string checklist
items are required before any filesystem work; the plan path then resolves
under the resolved plans directory through the fail-closed path policy,
and a path under any other directory is refused as `unsupported archive
location` naming the offending path before any read; its filename matches
the manifest `plan_slug`, and when a resume watcher record with a
canonical plan path exists, that recorded path must equal the plan path
too; then the file reads under the bounded-read policy, an empty plan
refuses, and zero line-anchored unchecked checkbox lines are required); (3)
destination (the completed directory resolves only from the facts
TOML-fence key `plans_completed_dir` through
`facts_paths.resolve_toml_key_raw` anchored at the repository root, never
from a folder name; a missing key, a non-existent directory, or a resolved
destination escaping the repository root refuses, and a candidate
differing from the resolved destination refuses as
`unsupported archive destination`); (4) clean-round review sidecar (schema
version 1, `source_kind` `code`, a present verdict must be `yes` (an
absent verdict falls through to the blocking-rows check; the verdict is
the only optional field), the findings array is required, a findings row
whose `blocking` value is missing or not boolean refuses, zero findings
rows with `blocking` true, and a non-null `last_fix_commit`
ancestor-or-self of HEAD; a present `residual_policy` input is validated in
the input shape guard (non-empty integer finding ids, a non-empty grant
source, a finite numeric recorded-at epoch) and opens an OR-branch in this clause:
the gate additionally accepts the focused verification-round sidecar when
the policy's recorded-at predates the sidecar's round `date` (the proof is
strict at day precision, so a policy recorded at or after the round day
refuses) and no findings row is both `blocking: true` and a member of the
policy's finding ids; blocking rows outside the set are the backlogged
residuals and are permitted, a blocking row inside the set still refuses,
under this branch a present verdict must be `yes` or `no` (the sidecar verdict
may be `no` precisely because the out-of-set residuals are staged; any
other value refuses), and the
membership rule replaces the zero-blocking rule; a blocking findings row
whose `id` is not an integer refuses under this branch, because membership
against the policy's integer finding ids cannot prove such a row outside
the named set and id-type drift must never reclassify a blocking row as a
permitted residual); (5) commit identity
through the existing
`commit_lookup`. After (5), the plan digest is computed over the active
plan bytes and a digest-computation failure refuses before the
`archive_gate` receipt is written.

On success the pre-archive stage writes the `archive_gate` receipt under
the manifest lock with the fields `plan_path` (the recorded source active
plan path), `declared_destination`, `plan_digest` (sha256 over the plan
file bytes), `last_commit_sha`, `phase5_checklist`, and `recorded_at`.
Re-running the stage overwrites the receipt in place with the identity
fields stable and `recorded_at` refreshed. The stage never sets
`workflow_state` and never writes a `terminal_receipt`.

The `final` stage runs after the move. Its checks evaluate in one fixed
order and it refuses at the first miss: (1) machine completeness (a
non-empty task map, every task complete), which precedes every gate clause
so an incomplete run is never refused on gate evidence; (2) the gate
clauses: the `archive_gate` receipt must be present (a move attempted
without a gate receipt is refused as blocked `done-pending`), the supplied
archived path must equal `archive_gate.declared_destination` exactly, and
the gate-recorded source plan path must be absent from the filesystem; (3)
the archived-plan checks in order: the shape guard, the fail-closed
bounded read, the digest recompute over the archived bytes (refusing when
it differs from `archive_gate.plan_digest`), the empty-plan refusal, zero
unchecked checkbox lines, and the provable commit identity.
The terminal receipt gains `plan_digest` from the gate record only after
that equality held. Every refusal preserves the manifest (no manifest
state beyond construction-time manifest writes (owner, receipts, updated_at)) and leaves
`workflow_state` non-terminal.

Sidecar boundary: the terminal operation reads the clean-round review
sidecar as a `terminal-gate-only` boundary extension; the readiness operation never reads review sidecars.

### Seeding boundary and resume reconciliation

The `create` operation is the only documented seeding path that translates
plan checkboxes into machine manifest state. It wraps `create_manifest` (the
same seeding routine the selftest uses), refuses to overwrite an existing
manifest, persists the supplied owner identity, and is the seeding producer
for per-task `allowed_paths`: every task's entries are validated through the
same fail-closed path policy the launch envelope enforces; entry validation
at create covers each listed path's shape, while an empty `allowed_paths`
list seeds successfully and fails closed later, at envelope authorization,
where the empty-scope gate rejects it. A missing or directory-valued entry
(including a trailing-slash entry) is rejected at `create` and again at
envelope validation with an actionable error naming the entry; directory prefix
matching is explicitly out of scope because a directory-valued entry would
silently never match the file-level scope witnesses - failing closed beats a
silent never-matching entry.

On resume, the manifest wins over the plan file's checkboxes. Divergent plan
checkboxes (for example a `- [x]` whose task is not `checkpointed`/
`complete` in the machine manifest) are corrected by rewriting the plan file
through the skill-gated plan-edit step, never by mutating the machine
manifest to match the plan; the manifest's task statuses, claims, and
generation fence every transition.

## Predecessor verification

Before a plan step whose work depends on predecessor work starts, the
orchestrator verifies each declared predecessor through the manifest-free
`precondition` CLI operation: `--operation precondition` with a
`--predecessors-file` JSON document and the repository root (cwd-based
default, `--repo-root` override). No `--manifest` is supplied or loaded; the
operation runs end to end without the machine manifest. The declaration
shape is:

```json
{"predecessors": [{"ref": "example-crm-123", "outcomes": [{"kind": "history-ref", "value": "example-crm-123"}, {"kind": "ancestry", "value": "v1.2-tag"}, {"kind": "artifact", "path": "scripts/quota_window_probe.py", "contains": "pause_decision"}]}]}
```

Each predecessor carries a non-empty `ref` and a non-empty `outcomes` list.
Outcomes are OR-combined per reference: one verifying outcome verifies the
predecessor. The driver evaluates exactly three repository-local kinds:

- `history-ref`: a HEAD-reachable commit message contains the reference as a
  fixed string (`git log -F --grep`; never a basic regex, so a `.` in a
  reference is never a wildcard). This is deliberately identity-agnostic:
  rebased, cherry-picked, or squashed history still verifies when the
  reference survives in a commit message.
- `ancestry`: the named base commit is an ancestor of HEAD (the same
  descendant witness the done boundary uses).
- `artifact`: the path resolves under the repository root through the
  fail-closed path policy, exists, and its content contains the pinned
  `contains` span.

The plan-declared `validator` kind is orchestrator-run, not driver-run: the
orchestrator executes the declared validation command and records its exit
evidence in `manifest.md`. The orchestrator resolves validator outcomes first
and excludes validator-verified predecessors from the predecessors document
handed to the driver; the driver call covers the remaining predecessors only,
so a predecessor carrying only validator outcomes never reaches the driver.
The driver never executes plan-declared commands;
at the driver boundary a `validator` outcome contributes no verification.

The success verdict carries per-predecessor evidence naming which outcome
verified each reference. The operation fails closed: a malformed declaration
(unknown outcome kind, empty outcome list, missing `ref`, malformed
document-level shape, or a missing repository root) or a predecessor
whose every outcome fails returns `blocked` with reason code
`precondition-unverified`, `resume_allowed: true`, and a diagnostic naming
the reference and every outcome tried.

## Hook capability boundary

Shared hook cores remain agent-neutral. Thin runtime adapters translate each
host's input and decision envelope, while the runtime profile registry owns the
capability tier and fallback. A host hook cannot enforce a policy when its event
cannot block the operation or cannot carry the payload needed to evaluate the
policy. The capability probe reports missing adapter, missing registration,
unsupported event, and degraded fallback as separate diagnostics. It must fail
closed for malformed adapter data and must never report `PASS` for a missing
registration.

## Lock liveness and generation fencing

The done lock metadata records a unique generation, holder PID, holder process
identity, start time, and the repository session fence. A matching session fence
is non-expiring for automatic recovery: age alone never reclaims it. Automatic
takeover requires independent verification that the recorded holder is dead,
the holder identity is not ambiguous, the dead-holder grace period has elapsed,
and the generation still matches at compare-and-swap removal time. A live holder
with a missing or invalid fence, or an ambiguous holder identity, returns a
blocked recovery result. `stale-clean` is the explicit operator action for a
stale lock.

Every mutating phase revalidates the generation before child work, after child
work, and immediately before commit. Release and takeover use compare-and-swap
removal and trap-based cleanup; a former holder can never mutate a replacement
generation. Fence-write failure removes the incomplete generation rather than
leaving a lock that appears live.

Terminal state and final-response enforcement are separate. A missing
final-response hook may be represented as degraded while in-process
continuation remains available. `terminal_result` returns no final receipt
while the machine manifest is active, regardless of any natural-language
worker output, because `mark_terminal` writes the receipt only after the
ordered predicate of the "Staged terminal operation (archive gate)"
section passes (its gate clauses plus its archived-plan checks). A
refused terminal call preserves the manifest and leaves `workflow_state`
non-terminal.

## Codex adapter boundary

`scripts/execute_plan_runtime_codex.py` is the only Codex-specific integration
point. It verifies the installed host activation surface before use and keeps
Codex JSONL envelopes, session IDs, process cancellation, and deadlines out of
the provider-neutral driver and shared skill prose. The verified command shapes
are:

```text
codex exec --json [-C <repo-root>] <prompt>
codex exec resume <session-id> --json [<prompt>]
```

Launch always pins the repository root with `-C <repo-root>`; `wait` resumes a
session without appending a prompt, while `resume` appends one.

Launch is bounded to 30 seconds and wait/resume to 300 seconds by default.
Profiles may lower or raise those values only when the resulting deadline is
finite and positive. The shipped package manifest pins the cross-runtime
baseline `launch_deadline_seconds = 900` (wait 300); the in-code defaults
apply only when a manifest omits the key (r3 F20). A timed-out operation
cancels its owned process tree and
must verify termination; failed verification becomes
`cleanup-unverified` with no retry or claim takeover.

Timeout cleanup consults each owned PID's captured start-time identity
immediately before escalating to `SIGKILL`, so a recycled foreign process is
treated as exited instead of signalled. This identity check is a best-effort
narrowing of the PID-recycle race; the kernel-level race itself is closed only
by a pidfd-based signal where the platform provides one.

The adapter never passes `--approve-for-me`,
`--dangerously-bypass-approvals-and-sandbox`, or any equivalent bypass flag.
The verified non-interactive approval configuration has exactly one production
source: an auditable approval receipt file naming the runtime and recording
`approval = "verified"`, passed to the driver CLI (`--approval-receipt`),
validated at adapter construction, and quoted in the activation receipt.
If the target host has no such receipt, the adapter
returns `blocked: runtime-policy-unavailable` and preserves the machine
manifest. Host results are translated into the normalized schema before the
driver sees them.

The approval receipt is owner-only evidence: the file must have mode `0600`
(any group- or other-readable mode is rejected), and it must record two
mandatory cross-check fields: `config_path` (the host config file the
operator attested, for codex the host codex config) and `policy_fingerprint`
(the fingerprint of the non-interactive approval policy recorded in that
config, for codex its `approval_policy` value). Both fields are
operator-attested evidence, not a cryptographic credential. Loading the
receipt re-reads the recorded config path from the host and recomputes the
policy fingerprint; a missing or unreadable config file, a config file that
is not valid TOML, an absent non-interactive approval policy, or a recomputed
fingerprint that differs from the recorded `policy_fingerprint` is rejected
as an approval-receipt policy cross-check failure (only the mismatch case
names the fingerprint mismatch); a config file holding non-UTF-8 bytes
surfaces the raw decode error (`UnicodeDecodeError`, caught fail-closed at
the CLI boundary) and is not a named cross-check class. A relative
`config_path` resolves only against an injected config
root and must be absolute when none is injected; a relative path without an
injected root is rejected as an invalid receipt, a failure distinct from the
cross-check rejection. Each failure prints its specific message on stderr. A rejected receipt fails closed before driver
construction: the driver CLI exits non-zero with an "approval receipt"
failure message on stderr (no normalized result is emitted) and preserves the
machine manifest, so the run stays resumable. Remediation is operator re-attestation: re-activate the
host runtime, confirm its non-interactive approval policy, and issue a fresh
mode-0600 receipt recording the current config path and fingerprint; this is the
same remediation as any other failed activation attestation. Pre-upgrade
receipts lacking `config_path` or `policy_fingerprint` (or carrying a looser
file mode) fail closed under this reading by design; re-attesting them after
host re-activation is a documented migration step, not an unplanned break.
