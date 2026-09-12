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
over the documented adapter codes).

## Durable task state machine

The normal task path is:

```text
pending -> claimed -> launched -> checkpointed
```

`blocked` is resumable only when `resume_allowed: true`. `aborted` is terminal,
and successful workflow completion is recorded as `workflow_state: complete`
with the Phase 5 checklist and archived-plan receipt.
The durable claim record contains `token`, `generation`, `owner`, and
`timestamp`. The driver writes the claim before launch and revalidates the
generation before any mutation and before commit handoff. When no owner is
supplied, the driver derives the owner identity from the machine manifest so
separate driver processes operating on one manifest share one owner; a
per-invocation owner is used only for a manifest that has none yet.

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

Startup reconciliation owns crash recovery. It reloads the durable manifest,
checks the claim, logs, task identity, and exact repository commit, and records a
completed checkpoint when a commit is provably present. It never relaunches a
provably completed commit or an ambiguous live worker. A commit recovered on
this path is verified against the claim's launch baseline exactly as the done
handoff verifies it: an out-of-scope or escaping committed path blocks the
reconciliation with the same boundary outcome the done handoff produces.

Before launch only, the startup dirty-worktree gate tolerates ambient noise: a
dirty worktree consisting purely of untracked allowlisted entries (`.DS_Store`
variants and editor swap files such as `.#*`, `#*#`, `*.swp`, `*.swo`,
`*.swpx`, `*~`) blocks with the resumable `cleanup-required` reason instead of
the non-resumable `dirty-worktree`. Anything outside the allowlist, including
tracked modifications, keeps the hard block on the same path. File mtime is
never the ambient-versus-worker discriminator because a worker can forge it:
after the claim's launch record exists, ambient noise is indistinguishable
from a worker-caused escape and stays non-resumably blocked, and the
checkpoint scope witness never consults the allowlist. Tasks already
progressed past launch (done-pending, checkpointed, complete) defer the
startup dirty-worktree check; ambient or worker dirt in that window is
enforced by the done-boundary clean-state witness instead.

## Transition table

| Event or condition | Required evidence | Claim handling | Retry budget | Resulting state | Recovery action |
| --- | --- | --- | --- | --- | --- |
| `started` | Claim record and launch receipt | Create token and generation before launch | 0 | `launched` | Wait for a bounded result. |
| `success` | Normalized result plus checkpoint evidence | Keep generation and persist checkpoint once | 0 | `checkpointed` | Refresh manifest and select the next incomplete step. |
| `contract-violation` | Violated rule and worker evidence | Keep claim fenced | 1 rewrite-and-retry | `blocked` until retry succeeds | Rewrite the worker instruction once, then retry; stop after one retry. |
| `blocked` | Reason code, action scope, and safe next action | Preserve claim unless takeover is proven safe | 0 unless profile declares a bounded recovery | `blocked` with `resume_allowed` | Preserve manifest and wait for the named gate or operator action. |
| `approval-required` | Exact requested action scope and approval evidence | Preserve claim and generation | 0 | `blocked`, `resume_allowed: true` | Await approval; never retry automatically. |
| `aborted` | Explicit stop receipt and owner | Release only the matching claim | 0 | `aborted` | Do not resume without a new explicit run. |
| `error` | Runtime error code and bounded evidence | Preserve generation for reconciliation | Numeric profile budget | `blocked` or terminal after budget exhaustion | Reconcile, then retry only within the numeric budget. |
| `timeout` | Deadline, operation, and cancellation evidence | Do not take over an ambiguous live claim | 0 | `blocked`, `resume_allowed: true` | Verify process cleanup before any later claim. |
| `dirty-worktree` | Paths and clean-state evidence | Preserve claim and quarantine generation | 0 | `blocked`, `resume_allowed: false` | Require explicit reconciliation before relaunch. |
| `cleanup-required` | Ambient noise paths on the pre-launch startup path | Preserve claim and quarantine generation | 0 | `blocked`, `resume_allowed: true` | Remove allowlisted ambient entries or resume after cleanup. |
| `cleanup-unverified` | Owned process and failed termination evidence | Preserve claim; never take over | 0 | `blocked`, `resume_allowed: false` | Require operator cleanup verification; do not retry. |
| `commit-pending` | Started receipt and task identity | Keep claim fenced during reconciliation | 0 | `blocked` or `checkpointed` | Inspect the exact commit before deciding whether work is complete. |
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
| `resume` | `resume` |
| `continue` | `continue_parent` (also surfaces `terminal_result` on a complete manifest) |
| `terminal` | `mark_terminal` (the terminal receipt itself is read back through `continue`/`resume` on the completed manifest) |
| `precondition` | `verify_preconditions` (manifest-free: requires `--predecessors-file` instead of `--manifest`; never loads a machine manifest) |

The driver, not the shared prose or the adapter, owns these transitions. A
reload resumes from the first incomplete step and never relaunches a
checkpoint whose exact commit is already proven.

The structured `runtime_state.json` is the sole machine-state source. The
orchestrator-maintained Markdown `manifest.md` is a human audit receipt, and
`agent-logs.md` is append-only telemetry. The orchestrator synchronizes those
documents from structured-state reads; neither document can authorize a
transition by itself. Machine-state writes are atomic, locked,
generation-fenced, and revalidated after every checkpoint.

### Seeding boundary and resume reconciliation

The `create` operation is the only documented seeding path that translates
plan checkboxes into machine manifest state. It wraps `create_manifest` (the
same seeding routine the selftest uses), refuses to overwrite an existing
manifest, persists the supplied owner identity, and is the seeding producer
for per-task `allowed_paths`: every task's entries are validated through the
same fail-closed path policy the launch envelope enforces, so the non-empty
`allowed_paths` requirement that feeds the empty-scope fail-closed gate is
established at seeding time. A missing or directory-valued entry (including a
trailing-slash entry) is rejected at `create` and again at envelope
validation with an actionable error naming the entry; directory prefix
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
  fail-closed safe-path policy, exists, and its content contains the pinned
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
worker output.

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
finite and positive. A timed-out operation cancels its owned process tree and
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
policy fingerprint; a missing config file, an absent non-interactive approval
policy, or a recomputed fingerprint that differs from the recorded
`policy_fingerprint` is rejected as an approval-receipt policy cross-check
failure (only the mismatch case names the fingerprint mismatch). A relative
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
