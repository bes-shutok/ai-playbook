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

Before launch reservation, the driver constructs a validated structured role
contract from the active claim and manifest task. It binds `role:
single-task-worker`, task id, claim token and generation, the exact task body,
canonical allowed paths, declared validation commands and criteria, worker
evidence ownership, worker-log destination, and retained parent obligations.
Only after validation does the driver serialize that contract as provider
prompt text. Caller prose is not an identity source: omitted prose uses the
driver-built contract, prose that attempts to replace contract values cannot
change them, and an orchestrator prompt or structured role/scope mismatch
refuses before adapter invocation. The adapter requires the same task role and
scope in both the task envelope and serialized contract and launches nothing
when fields are missing or disagree.

Every task checklist action is classified as `worker` or `parent` before
claim creation. Unknown or incomplete ownership refuses seeding. Worker
criteria alone enter `required_criteria` and command coverage. A parent-owned
`Commit:` action remains in `parent_obligations` with its exact planned commit
identity; the parent done receipt must echo that identity in `planned_commit`
and independently pass the normal done boundary. Excluding a parent action
from worker evidence never removes the parent's completion duty.

Plan authoring stays on the neutral side of this boundary: a plan task names
only observable commands, paths, test identities, and acceptance criteria,
with evidence and validation criteria the selected adapter can verify. The
adapter and its profile under `agents/skills/execute-plan/runtime-adapters/`
supply host identity, worker lifecycle, capacity, and interruption receipts;
host-specific lifecycle mechanics never enter plan task prose.

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
identifiers belong in the adapter profile under
`agents/skills/execute-plan/runtime-adapters/` (see the "Adapter profile
contract" section) and registry profile data. They do not belong in the
provider-neutral sections of this contract.

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

## Adapter profile contract

An adapter profile is the host-specific declaration of how one eligible
runtime satisfies this contract. Profiles live under
`agents/skills/execute-plan/runtime-adapters/`, one file per eligible
runtime, named for the canonical runtime ID it projects. Host-specific
command shapes, event envelopes, session formats, cancellation mechanics,
and deadlines belong in the profile and never in this neutral contract.
The profile is a non-authoritative projection of the registry: it names
the registry path
`projects/.ai-playbook/execute-plan-runtime-inventory.toml` and the
canonical runtime ID it projects, and every registry-owned value - the
adapter entrypoint, the launch, wait, and resume operations, the adapter
version, the approval policy, the capability states, eligibility, the
retry budget, and the fallback - appears only as a reference to that
registry path plus canonical runtime ID. A profile that restates a
registry-owned value is a second capability owner and fails contract
review.

Each profile defines these surfaces, whatever the host names them
locally:

- **Worker identity**: the durable identity of one launched worker
  (claim token, generation, host session and process identity) that
  receipts, hooks, and the capacity witness key on.
- **Launch, wait, and resume receipt schemas**: one machine-readable
  lifecycle receipt per operation, each carrying the worker identity,
  the operation's outcome, and bounded evidence; the adapter translates
  each receipt into the normalized result schema before the driver sees
  it.
- **Terminal, timeout, and shutdown hooks**: what the host runs when a
  worker completes, exceeds its deadline, or the parent shuts down; each
  hook emits its receipt and feeds capacity release.
- **Capacity witness**: the reconciled view of live workers and
  available launch capacity, rebuilt by capacity reconciliation before
  every launch.
- **Handoff receipt**: the receipt that rotates ownership into the next
  task.
- **Evidence verifier**: the host mechanism that proves a worker's
  validation claims as machine-verifiable evidence.
- **Interruption reconciler**: the ordered reconciliation a host runs
  before any relaunch after an interruption.
- **Host fallback mechanics**: how the host applies the registry-owned
  fallback for a degraded or unsupported capability and reports a
  capability it cannot enforce.

### Incident obligations

Evidence-contract recovery of a malformed worker result also settles the
successor handoff named by that exact claim. Under the same manifest lock,
fresh matching provider-terminal evidence moves only that intent through
`launching` or `launched` to `ambiguous` and then `failed`, records a receipt
binding the intent, predecessor checkpoint and claim, successor claim and
launch, and provider terminal receipt/session, and requeues the task. Replays
preserve the failed intent and receipt. Startup may ignore a closed historical
claim only when exactly one recovery receipt binds the retired task, token,
and generation to the exact handoff successor, and the task has a current
claim at a strictly newer generation; the old launch record remains audit
evidence. The predecessor token, owner, generation, and checkpoint must match
the durable predecessor claim and checkpoint record, and the intent id must be
non-empty and unique. Terminal proof must include a non-empty provider receipt
id. Mismatched identities, stale or absent
terminal proof, and live workers leave the manifest unchanged.

Four incident obligations bind every adapter profile. Each names its
refusal witnesses and its recovery path. A profile that cannot implement
an obligation reports the affected capability as degraded or unsupported
through the registry with its fallback; it never silently skips one.

1. **Lifecycle and capacity reconciliation.** The profile's worker
   registry records every worker it launched and the launch capacity it
   consumed. Terminal, timeout, and shutdown events release that
   capacity idempotently: releasing an already-released worker succeeds
   without a second effect, and a terminal event that arrives twice
   releases once. Capacity reconciliation runs against the reconciled
   witness before every launch, never against a cached count. Refusals:
   a stale inventory entry (a worker recorded in the worker registry
   that the host cannot prove live) is neither counted live nor counted
   as free capacity; the launch is refused until the witness reconciles.
   A `not_found` close result means the worker already exited: the
   release completes idempotently and the next launch proceeds. A
   stalled worker (no heartbeat or log progress inside the profile's
   bounded liveness window) is not counted live or free; it is routed to
   the timeout hook and refused as launch capacity. Recovery: reconcile
   the worker registry against the host's live session and process
   state, then re-run the readiness decision. The inventory's process-row
   scan is quote-tolerant (quote characters in a process row's command
   text read as literal characters and prompt text is never parsed as
   shell), and its one documented limitation stays fail-closed: a prompt
   argument containing an embedded newline splits the rendered process
   row and the snapshot reports unavailable instead of guessing.

2. **Atomic handoff.** Advancing from one completed task to the next is
   an atomic handoff: one indivisible transition rotates the owner
   identity, the claim token, and the generation together with the next
   worker's launch identity, under the same lock that records the
   previous worker's terminal receipt. Refusals: an owner mismatch - a
   receipt or continuation carrying the previous task's owner or token -
   is refused before any launch and preserves the durable claim; a
   replayed handoff (the same handoff receipt delivered again) is
   idempotent: it returns the recorded outcome and never rotates a
   second time. Recovery: re-read the durable claim record and continue
   from its current owner, token, and generation.

3. **Machine-verifiable evidence.** A worker result advances a task only
   on machine-verifiable evidence: the identity of each validating
   command, its working directory, its exit status, the output identity
   of the captured result, the selected test identities, the changed
   paths measured against the launch baseline, and the plan-criterion
   coverage those changes satisfy. A log path, a narrative claim, or an
   attestation without command identity is not evidence. Refusals: a
   malformed receipt - evidence missing, unparseable, or out of shape -
   fails closed as `blocked` or `error`, never as a degraded success,
   and preserves the claim for a corrected re-submission; evidence
   naming paths outside the task scope fails closed as a contract
   violation. The envelope's plan-criterion coverage must be complete
   across the task's acceptance criteria the implement step owns
   (`Commit:` lines and done-step-owned checklist items excluded); a
   coverage set that omits an implement-owned acceptance criterion is a
   malformed receipt failing closed under the same refusal semantics.
   Recovery: re-run the validation commands and re-submit the
   evidence envelope under the live claim.

4. **Interruption reconciliation.** After any interruption, the profile
   reconciles, in order, before any relaunch: the durable task manifest,
   the worker registry (which workers the interruption orphaned), the
   latest lifecycle event per worker, and the worktree state against the
   launch baseline. Only a reconciled state relaunches. Refusals: a
   non-resumable interruption state - unverified process cleanup, an
   unresolved approval gate, or worktree drift that cannot be attributed
   to a proven source - stays blocked with `resume_allowed: false` until
   the named recovery action resolves it; the reconciler never relaunches
   into an unresolved state. Recovery: the reconciler records what it
   proved, releases the capacity of workers whose terminal events
   already closed, quarantines what it could not prove, and hands the
   parent one reconciled capacity witness to continue from.

## Normalized result schema

Every adapter result is translated into exactly these fields:

| Field | Meaning and evidence requirement |
| --- | --- |
| `status` | One of `success`, `contract-violation`, `blocked`, `aborted`, or `error`. |
| `reason_code` | Closed reason identifying the result condition. |
| `evidence` | Non-empty, bounded references proving the result; its plan-criterion coverage must be complete per the completeness obligation in the Worker execution contract (principle 3). |
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
Two legacy hesitation reason codes, `permission-request` and
`conversational-hesitation`, are translated to `worker-hesitation` with
status `contract-violation` before the closed-set check.

### Verification evidence envelope

Tasks may declare immutable `required_criteria` and `verification_commands`
when the manifest is created. The manifest stores a canonical
`evidence_contract_digest` over those fields and each task's path allowlist;
checkboxes and task status are excluded. The manifest also stores a deterministic,
immutable per-task mapping from compact criterion IDs (`c001`, `c002`, ...) to
the full criteria, and the mapping is covered by that digest. Create checks the
UTF-8 size of every receipt item and the complete envelope before writing; it
refuses an unrepresentable contract without truncating criterion text, and
enforces the receipt's 100-criterion count limit before creation. Manifest
validation accepts both the current digest shape and the prior shape that
predates compact criterion IDs, preserving in-progress runs across upgrades;
new manifests and corrected recovery contracts use the current shape. The driver runs a declared command
itself with argv execution in the repository root, records the exit status,
output digest, selected test identity, baseline and changed committed paths,
the declared allowlist, a digest of allowlisted source contents, compact criterion IDs, and the active task, token,
generation, and launch identity. Receipts are persisted under the manifest
lock. A successful worker result for a task with required criteria is
accepted only when matching driver captured receipts cover every required
criterion ID, resolve it through the digest-bound mapping, and match the active
claim, evidence contract digest, and current allowlisted source snapshot. The
full criteria remain in the task contract; receipts never duplicate their text.
Recovery revalidates the mapping before any claim, handoff, or manifest mutation. The done boundary also requires the task commit's
allowlisted source snapshot to match the captured evidence. Uncommitted
worktree paths are diagnostic only; the done boundary checks the task's own
commit path set against its allowlist.

Production `create` requests must supply non-empty criteria and verification
commands for every task. The seeded manifest enables evidence enforcement, so
a task without configured criteria cannot pass through the adapter result
path. The `verify` CLI operation accepts a task ID and declared command ID and
asks the driver to capture and persist the receipt for the active claim.

Pre-seed consistency gate. The pre-seed consistency gate refuses a
verifier that depends on a later task's artifact, refuses two or more
tasks declaring identical non-empty verification_commands lists, and
refuses a non-path token embedding a strictly later task's allowed
path. A command argv token is classified through the same fail-closed
path policy used at launch: a pure-path token (no whitespace or quote
characters, canonicalizing cleanly) keeps exact canonical equality
against strictly later tasks' `allowed_paths` entries as its whole-token
matching basis, while a non-path token embedding a strictly later
task's allowed path under the tail-boundary rule is likewise refused,
with the token elided in durable evidence; regex over payload strings
stays forbidden. The clone signature is
deep equality of the whole `verification_commands` list, so identical argv
carrying per-task-distinct embedded criteria is accepted, as are references
to same-or-earlier tasks' artifacts. Shape 3 is the literal embedded shape
only: a shell body constructing the path at runtime through variables,
encoding, or glob and selection-tool forms, a case-spelled literal on a
case-insensitive filesystem, and trailing-dot or backslash-separator
spellings on Windows-family filesystems evade the pre-seed gate by
design and still fail closed at the task boundary, with recovery as the
exit. A false-positive refusal is remedied by rewording the command or
moving the check to the task that owns the artifact; declaring the path
on the earlier task to trip the carve-out grants write scope and
creates cross-task overlap. Refusals raise before the manifest is
written, naming the task id and the offending entry. The plan's global
validation block is never seeded into tasks and remains the whole-plan gate
checked at the done boundary.

Evidence-contract recovery. The `malformed-result` refusal is read-only, so
the hold it leaves behind is the live launched shape itself: the claim and
task stay launched with the claim's durable launch reservation and no
durable receipt of the refusal. The sanctioned exit is the driver's
`recover-evidence-contract` operation, which validates its preconditions in
order and refuses with evidence, leaving the manifest byte-unchanged,
unless every one holds: the replay fence first (the manifest history must
not already carry an `evidence-contract-recovery` receipt naming the
request's task id, token, and generation), the launched hold shape, the
exact claim token and generation, no live claim-group ownership, a corrected
contract satisfying the per-task non-empty envelope rule and passing the
pre-seed gate over the merged task map (refusing only on problem shapes
that involve the corrected task, since multi-malformed old-seeded runs
recover task by task as they hold), and a fresh provider inventory obtained
through the adapter on a reservation-stripped detached view whose reconcile
leaves no registered worker of the held claim non-terminal: the reconcile
joins a live `resume` process to its registered worker through the
conversation id in the process argv, consults the adapter's
terminal-evidence port for each registered worker whose session is absent
from the inventory, and releases a worker only on a fresh, verified,
identity-matched terminal observation. Independently of the inventory
verdict, the operation refuses while any registered worker of the held
claim is not terminal or released, and that refusal's evidence naming the
worker row precedes the generic inventory reason. On acceptance
the transition applies in one locked save: the manifest generation is
bumped, the held claim's launch reservation is released inline with the
worker and capacity state reconciled, the task's evidence fields are
replaced with the corrected contract, the `evidence_contract_digest` is
recomputed, the old claim is closed as `closed`, and the task returns to
`pending`, with one fenced `evidence-contract-recovery` history receipt
appended. A late receipt from the replaced worker fences read-only as
`stale-claim` with no durable mutation, for success and non-success
receipts alike. Manual manifest edits stay prohibited. An invalid-choice argparse error for recover-evidence-contract means the vendored driver predates the operation: re-sync the driver; the manifest is untouched and manual edits remain prohibited.

Evidence envelope projection and recovery. The launch preflight projects each task's worst-case evidence receipt envelope (per-item UTF-8 byte lengths, item counts, and the whole-envelope JSON size) against the same bounded limits the receipt validator enforces, and refuses the launch before any claim state changes with the task, field, measured size, limit, and both correction paths (narrow the task's allowed_paths or split the verifier, or recover the launched claim). The projection is conservative: worker-produced path lists are projected at the full allowed_paths scope. The post-launch sanctioned exit is the driver's `recover-evidence-envelope` operation, which mirrors the recovery-transition contract: the `evidence-envelope-recovery` replay fence FIRST (its task id, token, and generation receipt names the replayed request), the launched hold, the exact live claim token and generation, and a corrected contract that is non-empty and re-projects within the bounded schema limits. One locked save: the generation is bumped once, the corrected contract replaces the task's evidence fields with the digest and criteria map recomputed, the old claim closes (a late receipt from the replaced worker fences read-only as `stale-claim`), the task returns to `pending`, and one fenced `evidence-envelope-recovery` history receipt is appended preserving the old token and generation. An invalid-choice argparse error for recover-evidence-envelope means the vendored driver predates the operation: re-sync the driver; the manifest is untouched and manual edits remain prohibited.

Run-identity migration. A manifest seeded by an older driver can record no `runtime` id: the read-only preflight correctly emits no command for it (the canonical command must pin the recorded runtime), a plain claim would stamp the runtime without activation evidence, re-creating loses the run, and hand-editing the manifest bytes stays prohibited. The sanctioned exit is the driver's `recover-run-identity` operation, which validates its preconditions in order and refuses with evidence, leaving the manifest byte-identical, unless every one holds: the replay fence first (the manifest must not already record a non-empty `runtime` field; the recorded id is named in the refusal, and the fence is evaluated before any host-state precondition), the payload `task_id` equal to the derived next incomplete task (both ids named on a mismatch; no-provable-next-task when none exists), a canonical registered payload `runtime_id` (an alias or unknown id is refused with the canonical form named), a payload `repo_root` resolving to the driver's repository root, a payload `generation` matching the manifest generation, the `token` per shape (exact match against a live claim's token, a mismatch returning the stale refusal; operator attestation validated for non-emptiness on a claim-less manifest), and the optional payload `receipt_path` loaded and fingerprinted through the shared receipt loader with its recorded runtime canonicalize-equal to the payload `runtime_id` (the same pairing cross-check the CLI flag path enforces). The one obstruction the same transition clears is the poisoned intermediate claim: the next incomplete task claimed with no launch record and no prepared handoff intent, or every member claim of a claim group in that same never-launched shape, closes per the reclaim-release precedent (claim states closed, tasks reset to pending, the matching claim group closed together with its still-staged member claims) and is recorded in the binding receipt; a live launch reservation on the task or any group member, a member claim in a launched shape, and a prepared handoff intent the readiness decision does not admit still refuse, naming the live member or the identity disagreement. After that clearing the transition evaluates the same readiness decision the preflight runs (its plan text is read from the manifest `plan_slug` through the resolved plans directory under the shared bounded-read policy, failing closed naming the plan error when unreadable) and refuses, before any binding is persisted, unless the decision admits the manifest (direct continuation, or the admitted prepared handoff successor with no failing condition left). On acceptance the transition applies in one locked save validated before persistence: the runtime id, the receipt record when supplied, any cleared claims and group, the generation bumped once, and one `run-identity-migration` history receipt (runtime id, resolved repository root, receipt identity, payload task id, the validated and post-transition generations, and for the clearing leg the cleared claims' task ids and tokens plus the closed group's id and its released-member id list). The bound manifest is then admitted by the ordinary read-only preflight, which emits the canonical continuation command. An invalid-choice argparse error for recover-run-identity means the deployed driver predates the operation: update the deployed driver first; the manifest is untouched and manual edits remain prohibited.

Reviewed scope recovery. A legitimate reviewed scope change can strand the intent-backed claimed prelaunch claim: ordinary preflight correctly refuses the stale seeded scope, and without a sanctioned exit the claim wedges until lease expiry. The sanctioned exit is the driver's `recover-task-scope` operation, whose CLI payload carries ONLY the exact prior claim identity (task id, prior claim token, prior claim generation) - the plan digest, the review evidence identity, the fresh preflight recomputation, and the replacement paths are derived from repository state, and no inventory or review evidence surface is caller-suppliable. The operation validates its preconditions in order and refuses with evidence, leaving the manifest byte-identical and appending no receipt, unless every one holds: the replay fence first, against the recorded `scope-recovery` receipts' prior identities - an identical replay re-verifies that the receipt's recorded rotated claim identity is still the live intent-backed claimed prelaunch claim (claimed state, prepared intent keyed to the claim, unconsumed prelaunch binding) and returns the recorded outcome with an explicit replay marker naming the matched receipt, any superseding state (launched, replaced, closed, reclaimed) refuses as stale identity naming that receipt, a request whose identity matches only an older receipt's prior identity falls to the stale-identity refusal naming that older receipt, any other mismatched replay naming the task is refused with the latest recorded receipt named, and a request carrying the current live claim identity is not a replay and proceeds through ordinary eligibility (a passing second correction appends a second bounded receipt); the plan file resolved directly as the facts-resolved plans directory joined with the manifest's recorded plan slug and the `.md` extension (repository-resolved, never caller-supplied; the full-stem identity is the binding, and the feature slug is only the reviews-directory discovery key); the intent-backed claimed prelaunch shape - the prepared handoff intent exists and keys to the claim with its unconsumed prelaunch binding, so a direct claimed claim refuses as not intent-backed - with no launch record, no registered worker, no launch reservation, and no live claim-group ownership; a fresh preflight recomputation through the shared lock-free check-body helper failing with EXACTLY the widening scope-drift problem for the target task whose drift entry carries a non-empty plan-path set (a passing recomputation, the declaration-parse and missing-declaration shapes, and any other problem refuse as fence-shape mismatch naming the recorded shape); readiness through the review-evidence composition (`resolve_reviews_dir`, `feature_slug`, `latest_review_round`, `evaluate_readiness`), whose evaluation is the single digest authority refusing unless the latest ready round's recorded digest equals the recomputed plan-bytes digest (the round is re-resolved and the on-disk plan bytes re-hashed before the receipt is written, refusing by name on disagreement); and replacement paths parsed ONLY from the task's structured `Files:` declaration through the landed parser (backticked prose and other path-looking text add nothing), canonicalized through the create boundary's path policy and refusing an absent declaration, an empty replacement set, a grammar-failing entry, an entry that fails canonicalization, and duplicate entries after alias resolution. The drift check is widening-only: recovery admits reviewed widenings (the drift-failure shape); a reviewed narrowing passes ordinary preflight unchanged and leaves the wider seeded scope live, so it is out of scope for this operation. A claim-group member's scope changes are refused here with the group named: the member exits through the group path (the driver `continue` operation with `--batch`), or through the blocked-member reclaim exit only when the member is blocked with `resume_allowed` false. On acceptance the transition applies in one locked save validated before persistence, and it is the whole closed mutation set: the claim row rotates to a fresh token and a bumped generation with the manifest generation bumped once alongside it (the reclaim/release rotation precedent; the owner and launch id never rotate, so the five-field parity the launch boundary enforces stays intact), the three handoff-intent identity carriers (`successor`, `outcome_action` with its `idempotency_key` re-stamped as part of the carrier, `prelaunch_binding` preserving the claim owner and launch id) are re-stamped with the new token and generation, the task's canonical allowed paths are replaced, the `evidence_contract_digest` is recomputed over the post-replacement task map, and one bounded `scope-recovery` history receipt is appended keyed on the prior claim identity, recording the plan digest, the review evidence identity (review artifact path, round number, source digest), the prior and replacement scopes, the outcome, and the rotated claim identity. This one operation supersedes the runtime's never-reads-review-sidecars posture: its review-evidence composition is a documented exception alongside the terminal gate's clean-round sidecar read. The operator then uses the ordinary sequence with no extra step in between: ordinary preflight over the post-recovery manifest (it passes and emits the successor advance command), then launch through the emitted outcome action with only the rotated claim token. Manual manifest edits stay prohibited. An invalid-choice argparse error for recover-task-scope means the deployed driver predates the operation: update the deployed driver first; the manifest is untouched and manual edits remain prohibited.

The shared recovery-transition contract. The three recovery operations
(`recover-evidence-contract` for the launched hold, `recover-task-scope` for
the reviewed scope change, and `recover-prelaunch-contract` for the stranded
prelaunch contract) satisfy one set of invariants: each validates its
preconditions in fail-closed order under the manifest lock with the replay
fence FIRST (its recorded history receipt, keyed on task id, old token, and
old generation, is named in the replay refusal); each lands its whole closed
mutation set in ONE locked save - the manifest lock is deliberately
non-reentrant, so no nested `@_locked_mutation` primitive is ever called
inside the transition (a nested call would be a silent no-op and a post-lock
call would split the transition into two saves); every refusal leaves the
manifest byte-identical; each binds the request to the claim identity (task
id, old token, old generation); and each appends its own append-only history
receipt under a DISTINCT event identity - the distinct identities are the
composition fence, so one operation's replay fence never matches another
operation's receipt. Each operation below lists only its deltas beside the
invariants above.

Prelaunch contract recovery. A claimed prelaunch claim holding a stranded
evidence contract (its seeded criteria fail the runtime evidence limit
checks; the PROJ-607 shape) has exactly one sanctioned exit: the driver's
`recover-prelaunch-contract` operation. The operator corrects the plan
through the skill-gated plan edit first, then supplies a payload carrying
the task id, the old claim token, the old claim generation, the corrected
contract (exactly `required_criteria` and `verification_commands`; any other
field, including `allowed_paths`, refuses with the named input-contract
problem before any precondition beyond the replay fence, because scope
changes are never accepted from a recovery payload), and the corrected plan
path (a payload field only; the CLI plan-path argument gate does not extend
to this operation), read through the shared bounded plan-read policy with
the safe-path requirement enabled (repository-relative, non-escaping, the
terminal gate's mode), so the receipt's plan audit anchor can only bind
in-repo bytes; the named unreadable-plan refusal is ordered after the replay
fence and the identity checks, before the corrected-contract phase.
Prelaunch-only deltas beside the shared invariants: the prior manifest loads
RAW under the manifest lock with only the structural worker and claim schema
validated (the launched-hold operation keeps its validating load), because
the stranded shape's recorded digest and criteria map cannot survive it; the
evidence digest and criteria-map consistency checks are deferred to the
post-transition state. The preconditions after the fence and input contract:
the claimed prelaunch shape (task status `claimed`, claim state `claimed`,
no group-resolved launch record, no worker row), no owning claim group in
any state, no active capacity reservation for the claim, the exact live
claim token and generation, and the prior contract actually stranded (its
stored criteria fail the same single-homed limit checks; a healthy prior
refuses as named). The corrected-contract phase runs in the scope
recovery's order: the envelope rule first, then the corrected task's digest
and map contribution with the limit helpers caught and attributed to the
corrected task (the seed-time named shape naming task, criterion, byte
count, and the split rule), then pre-seed consistency over the merged task
map (refusing only problem shapes that involve the corrected task), then the
declaration parse over the task's plan section under the one documented
declaration grammar. On acceptance the transition applies in one locked save
validated before persistence: the two evidence fields are replaced;
`evidence_contract_digest` and `evidence_criteria_map` are recomputed over
the corrected task map with sibling-strand raises caught and downgraded; the
stale claim closes (the done-pending requeue precedent, so a late receipt
fences read-only as `stale-claim`); the task returns to `pending`
preflight-passable; handoff intents bound to the stale claim identity are
invalidated (no stale successor survives); and one fenced
`prelaunch-contract-recovery` receipt is appended binding the task id, old
token, old generation, the task's seeded allowed-paths digest as the
current-scope identity, the supplied plan bytes' digest, the prior and
corrected contract identities, and the unconditional accepted-divergence
audit line comparing the corrected criteria set with the prior criteria
set - the launched-hold receipt binds claim identity only, so these
contract-identity fields are a prelaunch-only delta - plus, when a handoff
intent was invalidated, the invalidated-handoff block naming the intent id
and the stale successor claim identity (task id, token, generation).

Named decisions and residuals for the prelaunch recovery:

- Corrected-contract-versus-plan-text divergence is accepted-with-audit,
  never a refusal arm; the operator discipline is the skill-gated plan edit
  first, and the receipt's audit line and plan digest carry the evidence.
- A declaration-refused prior with healthy criteria is a residual, not an
  admission trigger: its exit is the skill-gated plan edit plus preflight,
  which compares plan tokens against the seeded scope without claim
  rotation.
- A multi-strand legacy manifest recovers task by task: while a sibling
  strand survives, the pre-recovery digest and criteria-map values persist
  unchanged for the interim manifest, and every validating driver entry
  fails closed with the unnamed limit ValueError until the last strand
  heals (the pre-transition legacy consumption path; the seed-time named
  shape covers the create boundary only). The sanctioned remedy is the
  remaining strand's raw-tolerant recovery, and the operator instruction is
  to run the remaining strand recoveries back-to-back in one session. A
  corrected contract is never misattributed a sibling strand.
- A never-claimed oversized task has no sanctioned exit until claimed: the
  recovery admits only the claimed prelaunch shape.
- Composition routing for the combined drift-plus-stranded state (verified
  against `recover-task-scope`'s landed entry steps: intent-backed claimed
  shape, fresh widening-drift preflight fence, review-evidence digest
  authority, replacement paths from the structured declaration): run the
  scope recovery FIRST. Its fence is a fresh preflight recomputation, not a
  historical preflight passage, so a claim that never reached preflight
  enters through a live widening-drift failure and the scope recovery's own
  receipt is what the fence requires; it keeps the claim and its prepared
  intent binding live. The stranded contract does not block it (the scope
  recovery never validates evidence fields), and the prelaunch recovery
  runs second on the still-claimed task. The reverse order closes the claim
  and invalidates the intent binding, after which the scope recovery
  refuses the re-claimed direct claim as not intent-backed and the scope
  half falls to the plan-edit-plus-preflight residual; the prelaunch
  recovery's own preconditions are disjoint from the sibling's, and its
  distinct receipt identity keeps the two replay fences independent either
  way.

The standard reason codes are `completed`, `worker-hesitation`,
`contract-violation`, `approval-required`, `timeout`, `dirty-worktree`,
`cleanup-required`, `cleanup-unverified`, `malformed-result`, `owner-mismatch`,
`stale-claim`, `explicit-abort`, `runtime-policy-unavailable`,
`runtime-error`, `precondition-unverified`, and `capacity-unavailable`. The
reference driver and adapter additionally emit `authorized` (envelope
authorization success), `activation-verified` (adapter activation success),
`worktree-witness-unavailable` (broken git scope witness), and the boundary
events `done-pending` and `commit-pending`. This extended set is closed:
normalization rejects a missing or unknown reason code as a malformed result
instead of defaulting it. The CLI create operation emits `created` as its own
CLI envelope outside the adapter normalization boundary (which stays closed
over the documented adapter codes); the CLI reclaim operation emits
`reclaimed` the same way for a successful release and `prelaunch-reclaim-cap`
for the exhausted prelaunch-reclaim budget, and the CLI readiness
operation emits its decision codes `direct-continuation`, `observe-worker`,
`recovery`, and `terminal-path` as CLI-envelope reason codes the same way.

## Durable task state machine

The normal task path is:

```text
pending -> claimed -> launched -> checkpointed
```

`deferred` is the terminal-ish status written only by the done-pending
recovery transition's `defer` disposition: the task is retired from the
queue - excluded from the incomplete selection and never relaunched - and
deliberately stays outside the progressed set, so plan-manifest agreement
never demands unchecked-checkbox closure for a task the operator chose not
to complete; the recorded `done-pending-recovery` receipt, not plan
checkboxes, is the deferred task's evidence. That receipt is the
append-only history event recording one done-pending recovery: the task
id, claim token and generation, disposition, the bounded terminal
evidence, and the linked backlog evidence for a defer. Its identity (task
id plus token plus generation) fences duplicate receipts.
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
an empty or whitespace-only plan is refused as empty, and a plan with zero
recognizable `### Task <N>:` task headings is refused naming the missing
task sections) and carries zero unchecked checkbox lines over its whole
length under the line-anchored reading (a line counts only when its first
non-whitespace token is an unchecked task-list marker, one of `- [ ]`,
`* [ ]`, or `+ [ ]`; a mid-prose mention of the marker does not count), and
`commit_lookup` proves the commit identity.
Any missed check returns the `done-pending` block with evidence
naming the failed check and preserves the manifest unchanged (non-terminal,
no receipt written); the run stays continuable once the failed check passes
(`done-pending` is not a resumable reason, so this block never resumes
automatically). The manifest lock fences the machine manifest only: it
does not fence the external archived-plan and commit artifacts the checks
consult, so a refused terminal call is re-run once the named check passes. The terminal checkbox scan is line-anchored over the whole
file and fence-blind by spec in the fail-closed direction: a
`- [ ]` marker inside a fenced code block in the archived plan still refuses
terminal.
A capacity receipt (reason code `capacity-unavailable`) parks a single-task
claim in the `waiting-capacity` state instead of the blocked shape: the claim
keeps its token, generation, and launch record and carries the bounded retry
policy (`mode: bounded-resume`, `max_attempts: 3`, `attempts_remaining: 3`).
The first capacity receipt parks with the full budget, each successive
capacity receipt consumes one attempt, and the receipt that arrives with the
budget exhausted transitions the claim to `blocked`, the reclaimable lease
state whose standard recovery machinery then applies. While the budget
remains, recovery is the in-place resume: a continue relaunches the same
claim under the same token and generation (no second claim row, no reclaim
rotation; the parked claim's recovery action is the literal
`resume-same-claim`, the exact value carried in the receipt's
`recovery_action` field), and reclaim refuses a parked claim with evidence
naming `waiting-capacity` while the retry budget is live; in the exhausted
window (attempts_remaining 0, before the next capacity receipt lands the
claim in `blocked`) the refusal names the exhausted budget and the pending
`blocked` transition instead. A `waiting-capacity` claim
at the queue head routes the readiness decision to `recovery` with
`preserve-and-reconcile` through the unprovable-next-task condition (the
parked task is not claimable; the condition text is unchanged). A capacity
receipt on a live batch-group member never parks: it keeps the existing
blocked shape under the group path, and the group fences are untouched.
A structured rate-limited end with an open task claim
resolves the claim per the budget-pause precedent (park or close; the
blocked-claim resume operation does not apply on resume); a claim-less
end has no receipt carrier and
its waiting-for-capacity derivation reads the recorded stop lines.
The durable claim record contains `token`, `generation`, `owner`, and
`timestamp`. The driver writes the claim before launch and revalidates the
generation before any mutation and before commit handoff. When no owner is
supplied, the driver derives the owner identity from the machine manifest so
separate driver processes operating on one manifest share one owner; a
per-invocation owner is used only for a manifest that has none yet.

Before automatic replacement after a terminal worker interruption, the
idempotent `reconcile-interruption` operation accepts an `idempotency_key`,
`task_id`, exact `claim_token`, and exact `generation`. Under the manifest
lock it accepts only a non-resumable blocked timeout, shutdown, or
interruption receipt and requires a fresh, valid provider inventory proving
no worker is live. It removes only the matching launch reservation, preserves
all worktree contents, closes the old claim as `replaced`, and returns the
task to `pending` for the normal fresh-identity claim path. Replaying the
same key returns the recorded outcome without another transition. Missing,
malformed, unavailable, or live-worker evidence preserves the claim and
reservation and refuses automatic continuation. `continue`, `resume`, and a
resume-watcher fire run reconciliation before launching or clearing watcher
guards. If the claim has a registered worker, reconciliation requires
verified terminal evidence to release its worker capacity: a matching
verified terminal lifecycle receipt, or the driver's terminal-evidence
consult of the adapter for a registered worker whose session is absent from
the inventory, which releases the worker only on a fresh, verified,
identity-matched terminal observation; an empty inventory without such
evidence cannot retire a registered worker and instead leaves it
quarantined. If the launch never registered a worker, a fresh valid empty
inventory is the provider witness that no owned process remains. The normal
`reconcile_startup` path continues to own commit recovery and follows this
interruption check on continuation.

After an initial terminal consult, inspect one fresh raw process snapshot.
The snapshot proves absence only when the process command succeeded and
returned a well-formed result. A failed, malformed, or unavailable first
snapshot preserves quarantine and does not start a re-observation. When the
successful first snapshot still contains the quarantined worker's provider
session, treat that match as suspicious and allow exactly one bounded
terminal re-observation. Both
terminal reads are bound to the same provider session and the same persisted
worker launch identity (task, claim token, owner, generation, worker id, and
process identity). The re-observation must itself be fresh, verified, and
identity-matched; terminal completion timestamps do not establish read
freshness. After it, take one more bounded raw process snapshot. Release is
allowed only when that snapshot succeeds, is well-formed, and proves no resume
for the session is visible. A visible resume, unavailable snapshot, missing or
malformed observation, stale proof, or identity mismatch preserves worker and
launch reservation quarantine. No path retries the terminal read more than
once.

The claim `timestamp` is written once at claim time and never renewed for a
single-task claim; a batch member's timestamp is refreshed at activation
(anchor launch, member advance), so its lease measures member liveness. The
`reclaim` operation releases an interrupted claim only once
`CLAIM_LEASE_SECONDS` (14400 seconds, four hours) have elapsed since that
timestamp - an order of magnitude above the execute-plan 20-minute per-worker
timeout, so a live worker's task normally completes well inside the lease -
except three identity-fenced prelaunch exits that waive the wait: the
prepared-intent done-successor exit, which reclaims a live claim backed by
a fresh `prepared` handoff intent whose recorded successor identity
matches the claim; the direct-claim prelaunch fast path, which reclaims a
blocked direct initial claim immediately under the two-attempt
prelaunch-reclaim budget when its persisted `runtime-policy-unavailable`
receipt carries the live claim identity and its approval evidence is
supplied at the invocation or already recorded (the `reclaimed` transition
row owns the full conjunct list); and the r4 F2 lease-waived live-group
exit (below). The
constant is driver-owned code: no environment variable and no CLI flag
overrides it, so the no-bypass property covers more than the flag surface. A
task still running past the lease keeps running, but its post-reclaim
checkpoint fails fenced as `owner-mismatch` instead of corrupting state.
Reclaim refuses closed with the resumable `stale-claim` outcome (manifest
untouched) before expiry, on unknown tasks, on closed, replaced, or aborted
claims, and on any task in the progressed set (`done-pending`,
`commit-pending`, `checkpointed`, `complete`); the CLI refuses
`--operation reclaim` without `--task-id` before any driver construction. A
workflow in the closed non-active set is never released: for a reclaimable
claim on a task outside the progressed set, a machine `workflow_state` of
`aborted`, `complete`, or `terminal` returns the preserve-and-stop outcome
before any lease accounting instead of the stale-claim refusal; the envelope
reason code is `explicit-abort` for all three closed states (the shared abort
envelope, so the status is `aborted` and `resume_allowed` false), and the
evidence names the finished state ("workflow was explicitly aborted before
the reclaim" under `aborted`; "workflow_state is '<state>'; the workflow
already finished" under `complete` and `terminal`); a progressed-task
refusal still returns `stale-claim`.
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

Startup reconciliation does not block on repository-wide dirty worktree
state. Manual edits and peer-session changes may coexist with execution.
Dirty worktree state does not block startup, worker checkpoints, or the done
boundary. The done boundary still verifies the paths in the task's actual
commit against its authorized paths. The done workflow stages explicit paths
and commits with an explicit pathspec, so unrelated manual changes and
peer-staged changes remain outside the current task's commit. Same-path
concurrent edits remain an attribution concern and are recorded in the
backlog for a future shared ownership mechanism.

## Transition table

Each outcome in the table names exactly one next action: take that one
action, then re-classify the state.

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
| `capacity-unavailable` | Capacity receipt with bounded evidence, on a single-task claim (a live batch-group member keeps the existing blocked shape) | Claim parks `waiting-capacity` keeping token, generation, and launch record, with the bounded retry policy on the claim; the receipt arriving with the budget exhausted moves the claim to `blocked` | bounded-resume (`attempts_remaining: 3`) | `waiting-capacity`, then `blocked` after exhaustion | Resume the same claim with `continue` (same token and generation, no second claim row); reclaim refuses the parked state while the budget is live, naming the exhausted budget and the pending `blocked` transition in the exhausted window; after exhaustion the blocked-state recovery applies. |
| `dirty-worktree` | No startup dirty-worktree refusal is emitted | No claim mutation | 0 | Not emitted by startup reconciliation | Uncommitted paths are excluded from the task commit by explicit pathspecs. |
| `cleanup-required` | No startup ambient-noise refusal is emitted | No claim mutation | 0 | Not emitted by startup reconciliation | Uncommitted paths are excluded from the task commit by explicit pathspecs. |
| `cleanup-unverified` | Owned process and failed termination evidence | Preserve claim; never take over | 0 | `blocked`, `resume_allowed: false` | Require operator cleanup verification; do not retry. |
| `reclaimed` | Expired claim lease (at least `CLAIM_LEASE_SECONDS`) - or, without the lease wait, the direct-claim prelaunch fast path defined at the end of this cell - on a claim in `claimed`, `launched`, or `blocked`, with the task outside the progressed set, with the machine `workflow_state` outside the closed non-active set (`aborted`, `complete`, `terminal` - a finished-workflow reclaim is refused with the `explicit-abort` preserve-and-stop envelope before any lease accounting, its evidence naming the finished state), and the claim not a member of a live batch claim group (a live-group member is refused with the resumable `stale-claim` outcome naming the group, r3 F1; the one exit, r4 F2: a live-group member whose task is blocked with `resume_allowed` false reclaims through with no lease wait, and the same compare-and-swap fails its group); the direct-claim prelaunch fast path: a direct initial claim (no handoff intent lineage, no registered worker, no launch residue - no launch record on the claim and no capacity reservation on the task) blocked with a receipt whose reason code is exactly `runtime-policy-unavailable` and whose embedded claim token and generation equal the live claim's, with approval evidence supplied at the invocation (`--approval-receipt` plus `--runtime`) or already recorded, and with the task-record prelaunch-reclaim count under the two-attempt budget (the initial recovery invocation plus exactly one transient retry) - at the budget, every other conjunct holding is refused as `prelaunch-reclaim-cap` before lease accounting, and the cap gates only this lease-bypass path (an expired lease rotates regardless of the count); the path's proof boundary and fencing: supplied-at-reclaim evidence
persists on success only (prelaunch-fence refusals persist nothing, so the
manifest stays byte-identical; the one post-sweep exception is the
capacity-gate refusal, which persists only the stale-reservation sweep
that ran before it and never the supplied evidence), and a claim rotated
between the block and the reclaim fails the receipt-equality fence back to
the ordinary lease wait | Replace generation and token, mark the old claim `replaced`, reset the task to `pending` with the previous session's resume fields stripped, recorded checkpoints preserved as evidence; on the r4 F2 exit the group is also marked `failed` with its active member cleared and the still-staged member claims closed | 0 | `pending` task under the `replaced` claim; the next claim takes the freed task under a fresh generation; on the r4 F2 exit the staged members' pending tasks also re-enter the individual queue | Re-claim and relaunch the freed task; a post-reclaim checkpoint or launch receipt from the replaced owner fails fenced as `owner-mismatch`, while a late done handoff refuses as unfenced done evidence; the replaced claim is reconciled by rotation and never quarantined at startup; a workflow in the closed non-active set returns `explicit-abort` (preserve-and-stop; the evidence names the finished state) and is never released. |
| `commit-pending` | Started receipt and task identity | Keep claim fenced during reconciliation | 0 | `blocked`, `checkpointed`, or `aborted` (the wedged-claim abort exit) | Inspect the exact commit before deciding whether work is complete. Abort with the current token is permitted when the recorded commit provably does not exist (the wedged-claim runtime exit; preserve-and-stop). |
| `done-pending` | Worker checkpoint plus done handoff evidence | Keep claim until done boundary closes | 0 | `blocked` or `checkpointed` | Do not launch the next task until commit (or the documented no-commit justification), checkbox, task-scoped commit-path evidence, and log evidence exist. |
| `done-pending-recovery` (the operator-invoked `recover-done-pending` operation; the single sanctioned exit from `done-pending`) | Exact claim identity (owner, token, and generation), task status `done-pending`, no live claim group (parallel or batch alike) owning the claim, bounded terminal evidence naming the claim's session or launch identity, and no `done-pending-recovery` receipt already recorded for the same task id, token, and generation | Close the claim under the manifest lock; every refusal - stale identity or wrong status returns the resumable `stale-claim` outcome, the live-group refusal names the group and leaves the sibling members untouched, and the terminal-evidence and duplicate-receipt refusals are blocked `precondition-unverified` - leaves the manifest byte-identical | 0 | `requeue`: task `pending` with the dead-session resume fields stripped under a generation bumped exactly once; `defer`: task `deferred` with the claim closed and the backlog evidence recorded; `abort`: task, claim, and `workflow_state` `aborted` | `requeue`: reconcile the plan section through the skill-gated plan edit first, then let the ordinary claim path relaunch under the fresh policy token; `defer`: continue with the next provable task, never relaunching the deferred task; `abort`: do not resume without a new explicit run. |
| `scope-recovery` (the operator-invoked `recover-task-scope` operation; the single sanctioned exit for a legitimate reviewed prelaunch scope change that ordinary preflight refuses as scope drift) | Exact prior claim identity only (task id, prior claim token, prior claim generation - every evidence surface is derived from repository state, never the payload); the intent-backed claimed prelaunch shape (the prepared handoff intent keyed to the claim with its unconsumed prelaunch binding), no launch record, registered worker, or launch reservation, no live claim-group ownership (a member exits through the group path, `continue --batch`, or the blocked-member reclaim exit when `resume_allowed` is false); the plan file binding by full-stem identity to the manifest's recorded plan slug; a fresh preflight recomputation failing with exactly the target task's widening scope drift (widening-only: a reviewed narrowing passes ordinary preflight and is out of scope); the latest ready review round's recorded digest equal to the recomputed plan-bytes digest (the single digest authority, re-verified before the receipt is written); and replacement paths parsed only from the structured `Files:` declaration with canonicalization and duplicate-alias refusals; the replay fence is evaluated first and an identical replay whose rotated identity is still the live intent-backed prelaunch claim returns the recorded outcome with a replay marker and writes nothing; every refusal leaves the manifest byte-identical and appends no receipt | Rotate the claim under the manifest lock: fresh token and bumped generation with the manifest generation bumped once (owner and launch id preserved, five-field parity intact), the three handoff-intent identity carriers re-stamped, the task's canonical allowed paths replaced from the reviewed declaration, `evidence_contract_digest` recomputed, and one `scope-recovery` receipt appended keyed on the prior identity | 0 | Claimed prelaunch claim under the rotated identity on the same task, its seeded scope replaced by the reviewed `Files:` declaration | Run ordinary preflight over the post-recovery manifest (it passes and emits the successor advance command), then launch through the emitted outcome action with only the rotated claim token; manual manifest edits stay prohibited. |
| `committed` | Commit identity, checkbox, task-scoped commit-path evidence, and log evidence | Close matching claim | 0 | `checkpointed` | Record the commit and continue once, idempotently; unrelated dirty paths do not block it. |

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
`{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json`; the machine manifest
`runtime_state.json` and its `runtime_state.json.lock` are
intentionally untracked live run state wherever they live: the canonical home is
`{tmp_dir}/execute-plan/<plan-slug>/` inside the gitignored `docs/tmp/`, and a
manifest at the repository root (a relative `--manifest` path) is live state
too, so implement workers, reviewers, and done runs must never classify or
delete these files as dirt or hygiene violations; the human-facing
`manifest.md` is an orchestrator-maintained audit receipt and is never used as
the source of truth. The runtime driver does not write or authorize from that
Markdown receipt. Machine-manifest writes are atomic, mode `0600`, and fenced
by a generation token and owner claim.

Resolution policy (normative): the driver implementation is one shared
deployed copy of `scripts/execute_plan_runtime.py`, while every run artifact
stays under the target project's facts-resolved tmp dir - the repository
root, the machine manifest, and the tmp resolution come from the target
project (`--repo-root` or the invocation working directory), never from the
checkout the shared copy itself lives in. A project-local entry point (a
copy or wrapper under the target project's own tree) is legitimate only as
a deliberate, explicitly configured override, never as an accident of path
resolution. The canonical continuation command the preflight operation
emits pins its own absolute script path, the recorded runtime id
(`--runtime`), and the repository root (`--repo-root`), every interpolated
value shell-quoted, so that command re-invoked verbatim from the shared
tooling checkout still resolves the same manifest and the same target root
and lands its artifacts under the target project's resolved tmp dir;
invocation from the shared checkout therefore cannot silently retarget
the run.

The driver accepts adapter results only after closed-result validation and
default-deny policy validation. It persists a worker checkpoint as
`done-pending`; it cannot select or launch another task until the existing
`done` workflow supplies commit identity, the completed checkbox, and the
preceding worker log evidence. For a claim with a recorded launch baseline,
the done boundary verifies the committed artifact instead of trusting the
attestation: the commit must be a descendant of the baseline, and its own
first-parent change set must stay inside the token's allowed paths. The whole
worktree need not be clean. The driver records those facts and never creates
commits itself. Replaying the same checkpoint or done
receipt is idempotent.

The driver treats worker hesitation about an already-authorized repository
operation as `contract-violation`, never as a user-question state. Genuine
approval requests preserve the exact action scope, use a zero retry budget, and
remain `blocked` until the external gate is resolved. Unknown result fields,
invalid action scope, generation mismatch, path traversal, network attempts,
protected-file attempts, and unverified process cleanup fail closed while
preserving the manifest. Dirty worktree state is not a refusal condition.

When a process ends between commit creation and checkpoint persistence,
startup reconciliation may complete the checkpoint only after an injected
repository lookup proves the exact commit identity. Ambiguous live workers,
owner mismatches, claim-before-launch interruptions, and uncommitted dirty
worktrees remain quarantined and are never relaunched automatically.

### Terminal-worker done-pending recovery

A terminal worker's claim can rest at the `done-pending` boundary with no
incomplete receipt path left: `done` refuses the incomplete done evidence,
abort refuses to regress a claim past its receipt boundary (the wedge
exception stays commit-pending-only), and `reclaim` admits only tasks
outside the progressed set behind the lease. The driver-owned
`recover-done-pending` operation is the single sanctioned exit from that
wedge; a manual machine-manifest edit never is. The transition runs under
the manifest lock like every other writer and admits exactly one shape:

- Identity fence: the live claim's owner, token, and generation must match
  the invocation exactly; any mismatch returns the resumable `stale-claim`
  outcome with the manifest byte-identical.
- Terminal-evidence requirement: the operator supplies a non-empty list of
  bounded evidence strings, at least one naming the claim's session or
  launch identity and the observed termination. Claim records carry no
  process identity, so the transition runs no process-liveness probe and
  waits out no lease - the evidence is the proof the worker ended.
  A bare evidence string is deliberately normalized to a one-element list.
  The identity anchors resolve through the claim's group launch record for
  group members, not only the claim's own record. The `requeue`
  disposition carries optional backlog evidence only through the same
  validated gate the defer disposition uses: an existing
  repository-relative path under `docs/history/backlog/`; anything else is
  refused before the receipt is recorded.
- Duplicate-receipt fence: the receipt identity (task id, claim token, and
  claim generation) is recorded in history exactly once; a replay with the
  same identity is refused with no new history event.
- Live-group refusal: a claim owned by a live claim group - parallel or
  batch alike - is refused with the group named and the sibling members
  untouched; the group protocol owns its members.
- Working-tree preservation and no relaunch: every disposition preserves
  the working tree byte-for-byte, returns no claim or launch action, and
  never relaunches the recovered claim; launching the requeued task is the
  ordinary claim path's job.

The operator chooses one durable disposition. `requeue` resets the task to
`pending` with the dead session's resume fields stripped, closes the claim,
and bumps the generation exactly once, so the next claim mints a fresh
policy token from the reconciled plan section - the plan/manifest scope
reconciliation itself happens through the skill-gated plan edit before
recovery is invoked, and the transition never edits a claim's allowed
paths. `defer` marks the task `deferred` with an existing
repository-relative backlog path under `docs/history/backlog/` recorded as
evidence; it is valid only for the next provable incomplete task (the
ordinal queue order is the only machine-provable dependency signal), the
task is excluded from the incomplete selection and never relaunched, and
the run continues with the following provable task. `abort` ends the run:
task, claim, and `workflow_state` become `aborted` (the same durable
writes the wedged-abort path makes, surfaced through the preserve-and-stop
aborted envelope), with the shared post-acceptance validation skipped
because the run is terminal. The `requeue` and `defer` dispositions
post-validate that the next provable incomplete task is pending or none
before the save; a failed check discards every in-memory mutation.

Three recovery guarantees complete the contract. First, every recovery
transition (`recover-done-pending`, handoff recovery, interrupted-task
adoption) validates its resulting manifest through the same worker-schema
validation the next launch runs BEFORE persistence; a validation failure
persists nothing - the manifest file stays byte-identical to its
pre-transition bytes (the byte-identical rollback guarantee), so recovery
can never succeed into a manifest the next launch refuses. Second, a
historical terminal worker record whose identity no longer matches its
task's claim is accepted only when a `done-pending-recovery` receipt in
history matches the record's original claim identity (task id, claim token,
launch generation); a rotation without that receipt backing is refused, and
an ambiguous handoff with no receipt still follows the existing
reconciliation path instead of the new exception. Third, the read-only
`preflight` operation proves the next task claimable before any claim is
created or rotated: it reports plan-versus-claim scope drift with the plan
paths and the machine-seeded scopes side by side, re-validates the recorded
approval receipt where one is seeded, and names one canonical continuation
command, and it never mutates state - a failing preflight leaves every
claim and handoff retryable. A `runtime-policy-unavailable` block raises
the policy-evidence problem naming both candidate causes (the claim or
continuation boundary ran without `--approval-receipt`, or the supplied
receipt failed validation) with reclaim-with-flags first among the remedies
(claim-with-flags only where a claim boundary is still ahead - a pending
task; re-create only for the genuine pre-claim case). Preflight admits the exact fresh
done-successor (a live claim backed by a `prepared` handoff intent whose
task, token, and generation agree) as authorized prelaunch state: the
admission and its exemption from the activation-evidence problem are
preflight-local, the passing preflight emits the successor's canonical
advance command under the same self-sufficiency shape, and the shared
readiness decision's returned tuple and the readiness operation's
documented closed decision set are unchanged (identity-mismatched or
already-consumed intents are never admitted). The emission is fail-closed:
the command exists only on a passing preflight (a failing preflight emits
no command), and a manifest recording no usable runtime id fails the
emission with a named problem instead of emitting a line that cannot pin
the recorded runtime. That problem's remedies are the canonical
claim-boundary remedy text: re-create the run with `--runtime` at the
create boundary, or run the `recover-run-identity` migration operation
(which requires a driver whose `--operation` table registers it; update
the deployed driver first), or supply `--runtime` together with
`--approval-receipt` at the next claim boundary; a bare `--runtime` at a
claim boundary is refused, and the manifest's recorded receipt never
substitutes for the receipt flag.

## Live-session discovery ladder

The shared skill's Live-session discovery ladder section (`agents/skills/execute-plan/SKILL.md`) owns the rung order, the stop-at-the-first-resolving-rung rule, the rung-3 report wording, and the manifest-only deviation note; this section pins only the concrete mechanism behind each rung for the driver boundary, the way the
host-scheduler maintenance overlay under `agents/skills/maintenance/` pins scheduling primitives.

- Driver claim check (rung 1): the executable driver is
  `scripts/execute_plan_runtime.py`; the claim check consults the machine
  manifest `{tmp_dir}/execute-plan/<plan-slug>/runtime_state.json` through the
  read-only `readiness` operation (`--operation readiness --plan <plan-path>`).
  Rung 1 exists for a run only when that `runtime_state.json` exists for its
  plan slug.
- Session-manifest heartbeat (rung 2): the orchestrator-maintained audit
  receipt `{tmp_dir}/execute-plan/<plan-slug>/manifest.md`; its heartbeat
  signals are fresh within the Step 3.1 20-minute window. The expected
  staging doc (`{reviews_dir}/...-code-review-r<N>.md`) counts as a heartbeat
  signal only by presence AND mtime inside that same window: presence alone
  is not a heartbeat signal (a doc left stale by a dead run proves nothing
  about liveness).
- Process scan (rung 3, last): permitted only when neither repo-scoped
  signal exists, per the shared skill's stop rule and report wording.

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

Post-launch results are checked again for valid claim identity and normalized
result shape. Dirty and untracked worktree paths do not block a checkpoint.
The done boundary validates the actual commit's first-parent path set against
the task's authorized paths. Git invocations disable `core.quotePath` so
committed path names compare literally. Uncommitted paths are not staged by
the done workflow's explicit path selection.

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
| `verify` | `capture_verification_evidence` (runs a declared verification command and persists its claim-bound receipt) |
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
| `reclaim` | `reclaim` (via `_operation_reclaim`; lease-gated interrupted-claim recovery, requires `--task-id`; the lease-waived exits reclaim a non-resumable live-group member and atomically fail its group, r4 F2, and reclaim a proven prelaunch blocked direct claim immediately under the two-attempt prelaunch-reclaim budget with `--approval-receipt` and `--runtime` supplied, the at-cap shape refused as `prelaunch-reclaim-cap`; `persist_construction=False` construction, the claim compare-and-swap is the operation's single write) |
| `diagnose` | `diagnose` (via `_operation_diagnose`; read-only first-failed-transition report; `persist_construction=False` construction, the operation writes nothing) |
| `recover-done-pending` | `recover_done_pending` (via `_operation_recover_done_pending`; operator-invoked done-pending recovery, requires the JSON payload `task_id`, `token`, `disposition`, and `terminal_evidence`, with optional `backlog_evidence` for the defer disposition; `persist_construction=False` construction, the locked recovery transition is the operation's single manifest write; see "Terminal-worker done-pending recovery") |
| `recover-run-identity` | `recover_run_identity` (via `_operation_recover_run_identity`; operator-invoked legacy-run identity migration for a manifest recording no runtime id, requires the JSON payload `task_id`, `runtime_id`, `repo_root`, `generation`, and `token`, with optional `receipt_path`; the already-bound `runtime`-field replay fence is evaluated first, the never-launched poisoned intermediate claim or claim group is cleared inside the same locked transition when that is the only obstruction, and the closed-residue readiness decision admits the post-state before anything persists; `persist_construction=False` construction, the locked recovery transition is the operation's single manifest write; see "Run-identity migration") |

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
schedules no watcher, not only for the report-only scheduling trail); when
the boundary is a supersede-class boundary superseding an armed watcher
(pause, wait-for-reset, abort, complete, unknown, weekly-secondary), the outcome also carries the
`carrier_teardown` receipt the supersede path computes (bootout plus
sentinel consume, receipt-only, same shape as the `watcher-supersede`
teardown receipt; null on install and stale boundaries)); a
receipt-validation refusal surfaces as the distinct reason code
`watcher-receipt-invalid` with `cas_applied` False and the machine trail in
evidence (machine-reason plus the unsatisfied field the ValueError names),
never as `watcher-cas-stale`, and the stale outcome's evidence gains the same
machine-reason trail; the plans boundary returns the same shape;
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
payload itself, `plan_slug`, `automation`, `job_dir`,
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
of `complete`, `archived`, or `aborted`). The schedule arm's probe report
must be the FULL probe report, never a subset: the boundary classifier
reads `status`, `binding`, `pause_decision`, and the binding window's
`reset_at_epoch` from the matching `limits[]` entry, so a subset payload
(for example one carrying a flat `reset_at_epoch` without `limits[]`)
classifies `unknown` and degrades to the report-only supersede.

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

### Checkpoint caller envelope

The Normalized result schema section owns the post-normalization field list;
this subsection documents the caller-facing checkpoint input only: the
worker-result envelope JSON the caller passes to `--operation checkpoint
--input`, which the driver method `record_worker_checkpoint` consumes. The
envelope carries these required keys:

| Key | Required value |
| --- | --- |
| `status` | One of the closed normalized statuses; a caller-supplied `approval-required` input status is translated to `blocked` with `reason_code: approval-required` before the closed-set check (see the Normalized result schema section). |
| `reason_code` | A code from the closed reason set; a missing or unknown code is refused (two legacy hesitation aliases, `permission-request` and `conversational-hesitation`, are translated to `worker-hesitation` with status `contract-violation` before the closed-set check; see Normalized result schema). |
| `evidence` | A non-empty list of non-blank strings. |
| `action_scope` | A non-blank string. |
| `checkpoint_identity` | A non-blank string whose task prefix (the part before the first `:`) selects the claim. |
| `generation` | The CLAIM generation from the live claim record, not the manifest generation. |
| `claim_token` | The token matching the live claim; the driver's claim-fencing input, consumed at `_record_checkpoint_locked` after normalization. |

Every field except `claim_token` is checked by
`runtime_capabilities.normalize_result`; `claim_token` never reaches
normalization and exists only for the driver's fence. A malformed receipt
(the envelope missing or failing any check) fails closed as a read-only refusal:
the normalization refusal surfaces as a blocked `malformed-result`
outcome carrying the caller's checkpoint identity and the manifest
generation, and the driver returns it before the claim fence, before any
latch, history append, or checkpoint record write. The claim and task keep
their pre-receipt state, so a malformed receipt never converts a healthy
claim into a blocked state; recovery is the corrected re-submission itself,
under the same live claim token and the claim's generation, with no lease
expiry, claim replacement, launch-record precondition, or manifest
recreation. When the envelope is well formed, the existing fence and
recovery semantics apply unchanged, including the drift guard that refuses a
corrected receipt on a post-launch claim without a launch record as the
resumable `stale-claim` outcome by design (anti-tamper). Copy-paste example
(substitute the live claim token; `generation` is 1, the first claim's
generation on a fresh manifest):

```json
{
  "status": "success",
  "reason_code": "completed",
  "evidence": ["worker-log: task complete"],
  "action_scope": "repository-task",
  "checkpoint_identity": "task-1:worker-1",
  "generation": 1,
  "claim_token": "REPLACE_WITH_LIVE_CLAIM_TOKEN"
}
```

### Done handoff receipt

The done handoff receipt normally carries a `commit_identity` matching a
HEAD-reachable commit, verified by the driver's commit lookup and the done
boundary witnesses. A task whose plan section carries no `Commit:` line (a
read-only verification gate with nothing to commit) records the no-commit
justification instead: `commit_identity` set to the exact literal `none`
after stripping. The driver never consults the commit lookup for `none` and
does not require a clean worktree or unchanged HEAD for a no-commit outcome.
For a real commit, it verifies the commit identity and checks only that
commit's first-parent changed paths against the task's allowed paths. The
recorded baseline must be an ancestor of that commit, or share a merge base
when concurrent checkout activity caused branch divergence; unrelated
histories remain blocked. Configured verification evidence must still match
the committed source snapshot. Other session or manual changes remain outside
the task commit. The none completion
records `none` as the task's completion identity and in the `done-commit`
history event, and hands the group advance the current HEAD revision as the
next claim's baseline.

The recovery completion identity is the exact literal `baseline-unchanged`
after stripping, recorded only by the driver's recovery completion arm: a
claim carrying `recovery_path: true` (recorded by the `--recovery` claim
flag, the execute-plan Recovery route's marker) closing a `Commit:`-line
task whose allowed-path bytes are hash-identical to the claim's recorded
baseline revision, with the task-local validation evidence envelope present
and matching the current allowed-path bytes. The driver skips the commit
lookup for the literal, proves those conjuncts under the manifest lock, and
refuses with the failed conjunct named when any of them fails: a
non-recovery claim, a task without a `Commit:` criterion, baseline drift, a
missing or mismatched validation envelope, or the identity replayed against
a different claim token or generation (the cross-claim replay fence records
the consuming token and generation per task at the first acceptance). The
recovery completion records `baseline-unchanged` as the task's completion
identity and in the `done-commit` history event, and hands the group
advance the current HEAD revision as the next claim's baseline, exactly
like the none receipt.

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

- `terminal-path` fires only when the machine manifest carries at least one
  task, every task is complete or checkpointed
  (or carrying `checkbox: true`), and the machine `workflow_state` is
  `active`, `complete`, or `terminal`; an empty manifest never lands here
  (matching `mark_terminal`'s empty-manifest refusal, it routes to recovery
  instead), while an
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
  `stop-or-recovery` for a machine state that is not `active` and for a
  plan with zero recognizable task sections,
  `recover-done-pending` for a done-pending handoff (the bounded
  operator-invoked exit detailed in "Terminal-worker done-pending
  recovery"; readiness only names the operation and never mutates),
  `preserve-and-reconcile` for a commit-pending handoff, a fenced claim, or
  an unprovable next task, and `correct-plan-through-skill-gated-plan-edit`
  for plan-manifest disagreement. When several conditions fail, the outcome
  carries the recovery action of the first failed condition in evaluation
  order: an empty manifest, then machine state, then unresolved handoff or
  fenced claim, then plan shape or plan-manifest disagreement, then
  unprovable next task.
  One envelope-level outcome sits outside that failed-condition enumeration:
  when the manifest lock is held by another owner at decision time, the
  operation returns the `recovery` decision with recovery action
  `resumable-conflict`, a transient contention envelope whose reading is to
  retry the readiness call after the lock is released; nothing is blocked
  durably and the manifest is unchanged. Transient contention is scoped
  exactly like the driver's other contention outcomes: the envelope carries
  reason code `stale-claim` with recovery action `resumable-conflict`, and
  the decision itself is carried in the outcome's `decision` field.
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
   or `commit-pending`, and no claim in state `blocked`. A `done-pending`
   handoff's failed condition names the recovery action
   `recover-done-pending`; a `commit-pending` handoff keeps
   `preserve-and-reconcile`.
4. Plan-manifest agreement. For each manifest task recorded in the
   progressed set (`done-pending`, `commit-pending`, `checkpointed`,
   `complete`), the plan's matching `### Task <N>:` section contains no
   unchecked checkbox line under the line-anchored reading (a line counts
   only when its first non-whitespace token is an unchecked task-list
   marker, one of `- [ ]`, `* [ ]`, or `+ [ ]`; a mid-prose mention of the
   marker does not count). A plan with zero recognizable `### Task <N>:`
   headings fails the plan condition outright ("plan carries no
   recognizable task sections"), so a wrong `--plan` file cannot produce a
   vacuous direct-continuation while no task has progressed. The task
   number is the id suffix after `task-`;
   the heading line matches `### Task <N>:` with the number terminated by
   its colon, so the Task 1 section never scans Task 10's heading or
   content. The heading search and the section scan share one
   CommonMark-grade fence map computed once over the whole plan's lines
   (whole-plan parity, no per-section restart): backtick and tilde fences;
   an opener is a run of three or more marker characters with an optional
   info string; a closing line uses the same character at an equal or
   greater width and is bare; fence lines carry a zero-to-three-space
   indent tolerance, so a fence-lookalike indented four or more spaces is
   literal text that toggles nothing; nested widths of different sizes keep
   parity until the matching closer (a shorter run inside a longer fence
   does not close it); an unclosed fence stays open to end of file, so a
   task heading inside it binds no section and this condition fails closed
   naming that task instead of scanning fenced content as prose. A fenced
   pseudo-heading before the real task heading is fenced content and never
   hijacks the section start. The terminal backstop still scans the whole
   archived plan fence-blind and fails closed.
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
the terminal gate's clean-round sidecar read and the reviewed scope-recovery
operation's review-evidence composition (that one operation only) are the
documented exceptions, so there is one owner per condition.

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
outcome that leaves the machine manifest untouched apart from the refusal
tail's evidence write (each stage refusal appends one `terminal-refused`
event to the append-only `history` after the outcome is composed; the
append never changes the outcome, and no other manifest state beyond
construction-time manifest writes (owner, receipts, updated_at) moves): (1) machine
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
too; then the file reads under the bounded-read policy, an empty or
whitespace-only plan refuses, and zero line-anchored unchecked checkbox
lines (first non-whitespace token one of `- [ ]`, `* [ ]`, `+ [ ]`) are
required); (3)
destination (the completed directory resolves only from the facts
TOML-fence key `plans_completed_dir` through
`facts_paths.resolve_toml_key_raw` anchored at the repository root, never
from a folder name; a missing key, a non-existent directory, or a resolved
destination escaping the repository root refuses, and a candidate
differing from the resolved destination refuses as
`unsupported archive destination`); (4) clean-round review sidecar (the terminal gate reads the clean-round review sidecar through the same bounded policy as the plan read, and an over-limit sidecar refuses with evidence naming `clean-round review sidecar exceeds the bounded read limit`; schema
version 1, `source_kind` `code`, a present verdict must be `yes` (an
absent verdict falls through to the blocking-rows check; the verdict is the only field whose absence falls through, and `last_fix_commit` is nullable (absent or null skips the ancestry check)), the findings array is required, a findings row
whose `blocking` value is missing or not boolean refuses, zero findings
rows with `blocking` true, and a non-null `last_fix_commit`
ancestor-or-self of HEAD; a present `residual_policy` input is validated in
the input shape guard (non-empty integer finding ids, a non-empty grant
source, a finite numeric recorded-at epoch) and opens an OR-branch in this clause:
the gate additionally accepts the focused verification-round sidecar when
the policy's recorded-at falls before the end of the sidecar's round `date`
(the proof is strict at day precision and anchored at machine-local midnights,
so a policy recorded on the round's own calendar day passes, the normal
record-then-round shape, and a policy recorded at or after the
following local midnight refuses) and no findings row is both `blocking: true` and a member of the
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
it differs from `archive_gate.plan_digest`), the empty-plan refusal (empty
or whitespace-only), the at-least-one-task-heading requirement (a plan
with zero recognizable `### Task <N>:` headings refuses naming the missing
task sections), zero unchecked checkbox lines (first non-whitespace token
one of `- [ ]`, `* [ ]`, `+ [ ]`), and the provable commit identity.
The terminal receipt gains `plan_digest` from the gate record only after
that equality held. Every refusal composes the blocked `done-pending`
outcome first and then appends one `terminal-refused` evidence event to
the append-only `history` (the append never changes the outcome); apart
from that event and the write timestamp the manifest is preserved and
`workflow_state` stays non-terminal.

Sidecar boundary: the sidecar boundary is owned by the readiness section's sentence above.

### Diagnose operation

The `diagnose` operation is the read-only first-failed-transition report.
Like readiness, it is read-only by construction: the driver loads and
validates the manifest under the manifest lock, releases the lock, and
returns without any write path, and the CLI operation constructs its driver
with `persist_construction=False`, so the manifest bytes are identical
before and after the operation. The walk takes the earliest classifiable
failure event in `history` order whose subject has not since reached the
progressed terminal state: a task-scoped event is superseded when its
task's current status is `complete`, and a workflow-scoped event (one that
carries no task) is superseded when the machine `workflow_state` is
`complete` or `terminal`.

The classification enum is fixed: `timeout`, `capacity-unavailable`,
`worker-failure`, `stale-evidence`, `inclusion`, `terminal-gate`,
`user-interruption`, `none`. Each class keys on its producing history
evidence:

- `timeout`: a `worker-blocked` receipt with reason code `timeout`.
- `capacity-unavailable`: a `worker-blocked` receipt with reason code
  `capacity-unavailable`.
- `worker-failure`: a `worker-blocked` receipt with reason code
  `malformed-result`, `runtime-error`, `runtime-policy-unavailable`, or
  `cleanup-unverified` (the adapter's non-resumable unverified-kill arm
  included).
- `stale-evidence`: a `worker-blocked` receipt with reason code
  `stale-claim`.
- `inclusion`: a `worker-blocked` receipt with reason code
  `precondition-unverified`.
- `terminal-gate`: the `terminal-refused` event the terminal refusal tail
  appends.
- `user-interruption`: the `user-interrupt-recorded` event.
- `none`: no classifiable failure survives the selection rule; the outcome
  names `first_failed_transition` null.

Cancellation is not a separate class: a cancelled worker's receipts already
carry the `timeout`, `malformed-result`, or `cleanup-unverified` codes, and
unverified cleanup classifies under its receipt's `worker-failure` code.
The outcome names the event as `first_failed_transition` with its
`classification`; a `none` report is a `success` outcome, a named failure
is a `blocked` outcome with recovery action `preserve-and-reconcile`. The
enum is a fixed map: a new recurring gate is a backlog decision, never a
silent extension of the table.

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

#### The one Files: declaration contract

Task scope declarations follow one documented grammar on both deciding
surfaces: the runtime parser (`_plan_declared_files` in
scripts/execute_plan_runtime.py, the sole runtime declaration-parsing
source; no second parser and no parallel declaration reader exists) at
every preflight and recovery consumption, and the pre-round readiness
check's authoring-side record collector (scripts/plan_readiness.py, the
sanctioned second grammar consumer). A declaration decides the same way
on both surfaces:

- Opener: only the exact, unindented `Files:` line opens a declaration
  block. A case-variant opener (`files:` or `FILES:` carrying entries) is
  refused with the named case-variant problem; the documented grammar
  accepts the exact `Files:` heading only. An indented `Files:` line is
  never a block opener: a task section whose only opener is indented
  produces the named missing-declaration refusal. A path-shaped bullet
  ABOVE the heading is inert prose: the recorded lookalike decision is
  that the scan starts at the opener and never looks upward, so a
  lookalike bullet neither contributes an entry nor truncates the block.
- Duplicate declaration: a second exact `Files:` heading inside one task
  section is the named `duplicate Files: heading` refusal on both
  surfaces, whether it sits adjacent to the first block or after a blank
  line; the union-collection of two blocks and the silent first-list-only
  read are both refused shapes.
- Entries: entries sit immediately under the heading (a blank line before
  a later entry keeps the existing named refusal); an indented entry
  under a valid heading is an entry like any other; a checkbox item ends
  the block. An entry may carry the planned-new annotation family (the
  `*(new` prefix with optional elaboration before the closer, for example
  a backticked path followed by `*(new)*` or by `*(new; this plan)*`): it
  records creation intent on a not-yet-created path and the parse strips
  it to the bare path, the same family the readiness record check
  recognizes. Any other trailing prose after the path token keeps the
  existing malformed-entry refusal.

The named problem strings are shared verbatim between the two surfaces so
the same shape emits the same problem family wherever it is decided.

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

### Terminal worker reservation release

Normal `done` and `recover_done_pending` use the same locked release contract.
The driver constructs a terminal receipt bound to the claim's task id, claim
token, generation, and launch id. Under the manifest lock, release proceeds
only when all four receipt fields exactly match the claim. It removes only a
reservation with that same four-field identity and releases only worker
capacity entries whose worker identity also matches the claim owner. A
reservation for another token, generation, or launch remains unchanged. The
done transition persists this cleanup with task completion before the lock is
released; recovery persists it with its recovery disposition. Ordinary
successor selection then follows the existing driver path after the lock.

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
