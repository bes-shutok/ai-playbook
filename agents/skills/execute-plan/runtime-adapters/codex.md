# Codex adapter profile

This is the adapter profile for the execute-plan runtime whose canonical
runtime ID is `codex`. The registry at
`projects/.ai-playbook/execute-plan-runtime-inventory.toml` is the only
owner of runtime identity and capability values for this runtime; this
profile is a non-authoritative projection of that registry row and the
host-specific source of launch and lifecycle mechanics.

## Registry ownership (reference only)

The registry row selected by the canonical runtime ID `codex` owns, and
this profile only references, the following values. When this prose and
the registry disagree, the registry wins and this profile is corrected:

- the adapter entrypoint (the canonical module and symbol of the adapter
  boundary selected for this runtime),
- the launch, wait, and resume operations (the registry-owned operation
  names that start one claimed worker step, wait for its result, and
  resume a persisted worker session),
- the adapter version of the contract implemented at the boundary,
- the approval policy,
- the capability states for the three receipt capabilities,
- eligibility,
- the numeric retry budget for bounded runtime errors,
- the fallback returned with a degraded or unsupported result.

This profile never restates those values and never defines a second
capability matrix.

## Host identity and activation

`scripts/execute_plan_runtime_codex.py` is the only host-specific
integration point for this profile. It verifies the installed host
activation surface before use and keeps command envelopes, session IDs,
process cancellation, and deadlines out of the provider-neutral driver
and shared skill prose. The verified command shapes are:

```text
codex exec --json [-C <repo-root>] <prompt>
codex exec resume <session-id> --json [<prompt>]
```

Launch always pins the repository root with `-C <repo-root>`; `wait`
resumes a session without appending a prompt, while `resume` appends one.

## Worker identity

One worker is the pair of the durable claim identity and the host session
identity: the claim token and generation from the durable claim record,
the host session ID returned by the launch (the anchor session for later
members of a batch claim group), and each owned host process ID captured
together with its start-time identity. The start-time capture is what
keeps a recycled process ID from ever being mistaken for the live worker
(see the timeout hook). Every receipt, hook, and witness below keys on
this identity; a receipt whose identity fields do not match the live
claim is refused as an owner mismatch before any state changes.

## Lifecycle receipt schemas

The adapter emits one machine-readable lifecycle receipt per operation
and translates each into the normalized result schema before the driver
sees it. The three schemas are:

- **Launch receipt** (one per claimed worker step): `worker` (the
  checkpoint identity), `claim_token`, `generation`, `session_id`,
  `command` (the exact launch command identity), `repo_root`,
  `deadlines` (launch and wait), `started_at`.
- **Wait receipt** (one per bounded wait): `worker`, `session_id`,
  `outcome` (one of `exit`, `timeout`, `cancelled`), `exit_status`,
  `elapsed_seconds`, `evidence` (bounded references to the captured
  output).
- **Resume receipt** (one per resumed session): `worker`, `session_id`,
  `generation`, `claim_token`, `resumed_at`, and the bounded evidence
  the resume basis was proved from.

A malformed receipt - one missing a required field, unparseable, or
carrying a value outside its closed set - fails closed as a
`malformed-result` blocked outcome; it is never repaired by inference
and never degraded into success. Recovery is a corrected re-submission
under the live claim token and generation.

## Terminal, timeout, and shutdown hooks

- **Terminal hook.** On worker exit the adapter emits the terminal
  receipt, translates it into the normalized schema, and releases the
  worker's capacity in the worker registry idempotently (the lifecycle
  and capacity reconciliation obligation). Completion before close is
  the same path: a worker that exits while the parent is closing it
  still lands its receipt, and the second close is an idempotent no-op.
- **Timeout hook.** The cross-runtime deadline baseline is
  `launch_deadline_seconds = 900` and `wait_deadline_seconds = 1500`,
  pinned in the shipped package manifest. The in-code adapter defaults
  equal this baseline and apply only when a manifest omits the deadline
  keys. A profile may lower or raise those values only when the
  resulting deadline is finite and positive. The wait baseline is sized
  to cover a legitimate 20-minute worker body of work (the same
  per-worker budget the driver's claim lease is sized against), finite
  and bounded, so an ordinary long worker or review panel completes
  inside the baseline instead of being terminated at an arbitrary short
  default. A timed-out operation cancels its owned process tree and must
  verify termination; failed verification becomes `cleanup-unverified`
  with no retry or claim takeover.
- **Cancellation mechanics.** Timeout cleanup consults each owned PID's
  captured start-time identity immediately before escalating to
  `SIGKILL`, so a recycled foreign process is treated as exited instead
  of signalled. This identity check is a best-effort narrowing of the
  PID-recycle race; the kernel-level race itself is closed only by a
  pidfd-based signal where the platform provides one.
- **Shutdown hook.** On parent shutdown the adapter attempts bounded,
  verified termination of every owned worker, records which workers it
  could and could not verify, and leaves the unverifiable ones
  quarantined for the interruption reconciler; it never records an
  unverified kill as a clean release.

## Capacity witness

The worker registry is this profile's record of launched workers and the
launch capacity they consume. Before every launch, capacity
reconciliation rebuilds the capacity witness from the worker registry,
the terminal receipts received, and the host's live session and process
state. The witness, not a cached count, decides whether a launch
proceeds or returns `capacity-unavailable`.

Refusal semantics (mirroring the neutral contract):

- **Stale inventory**: a worker recorded in the worker registry that the
  host cannot prove live is neither counted live nor counted as free
  capacity; the launch is refused until the witness reconciles. A
  `not_found` close result is the one proof of exit the host accepts for
  a missing entry: the release completes idempotently and the next
  launch proceeds.
- **Stalled worker**: a worker with no heartbeat or log progress inside
  the profile's bounded liveness window is routed to the timeout hook
  and refused as launch capacity; it is never counted live or free.

## Handoff receipt

Advancing to the next task is an atomic handoff: one locked transition
writes the previous worker's terminal receipt and rotates the owner
identity, the claim token, and the generation together with the next
worker's launch identity. The handoff receipt carries the previous
owner, the new owner, the new claim token, the new generation, and the
next launch identity (session ID and command identity).

- **Owner mismatch**: a handoff or continuation receipt carrying the
  previous task's owner or token is refused before any launch; the
  durable claim is preserved and the refusal names the mismatched
  identity fields.
- **Replayed handoff**: the same handoff receipt delivered again is
  idempotent - it returns the recorded outcome and never rotates owner,
  token, or generation a second time.

## Evidence verifier

Success requires machine-verifiable evidence. The verifier accepts a
worker result only when the evidence envelope names the identity of each
validating command, the working directory it ran in, its exit status,
the output identity of the captured result, the selected test
identities, the changed paths measured against the launch baseline and
contained in the token's allowed paths, and the plan-criterion coverage
the changes satisfy. A log path, a narrative claim, or an attestation
without command identity is refused as a malformed receipt and fails
closed; changed paths outside the task scope fail closed as a contract
violation. Recovery: re-run the validation commands and re-submit the
evidence envelope under the live claim.

## Interruption reconciler

Interruption reconciliation runs in this fixed order before any
relaunch:

1. Load and validate the durable task manifest.
2. Reconcile the worker registry: which workers the interruption
   orphaned, which terminal receipts already landed, and which releases
   are still owed.
3. Read the latest lifecycle event per worker (launch, wait, resume,
   terminal, timeout, or shutdown receipt) and prove each live worker's
   session and process state against it.
4. Witness the worktree against the claim's launch baseline.

Only a reconciled state relaunches. A non-resumable interruption state -
unverified process cleanup, an unresolved approval gate, or worktree
drift that cannot be attributed to a proven source - stays blocked with
`resume_allowed: false` until the named recovery action resolves it. The
reconciler records what it proved, releases the capacity of workers
whose terminal events closed, quarantines what it could not prove, and
hands the parent one reconciled capacity witness.

## Approval boundary

The adapter never passes `--approve-for-me`,
`--dangerously-bypass-approvals-and-sandbox`, or any equivalent bypass
flag. The verified non-interactive approval configuration has exactly one
production source: an auditable approval receipt file naming the runtime
and recording `approval = "verified"`, passed to the driver CLI
(`--approval-receipt`), validated at adapter construction, and quoted in
the activation receipt. If the target host has no such receipt, the
adapter returns `blocked: runtime-policy-unavailable` and preserves the
machine manifest. Host results are translated into the normalized schema
before the driver sees them.

The approval receipt is owner-only evidence: the file must have mode
`0600` (any group- or other-readable mode is rejected), and it must
record two mandatory cross-check fields: `config_path` (the host config
file the operator attested) and `policy_fingerprint` (the fingerprint of
the non-interactive approval policy recorded in that config). Both
fields are operator-attested evidence, not a cryptographic credential.
Loading the receipt re-reads the recorded config path from the host and
recomputes the policy fingerprint; a missing or unreadable config file, a
config file that is not valid TOML, an absent non-interactive approval
policy, or a recomputed fingerprint that differs from the recorded
`policy_fingerprint` is rejected as an approval-receipt policy
cross-check failure (only the mismatch case names the fingerprint
mismatch); a config file holding non-UTF-8 bytes surfaces the raw decode
error (`UnicodeDecodeError`, caught fail-closed at the CLI boundary) and
is not a named cross-check class. A relative `config_path` resolves only
against an injected config root and must be absolute when none is
injected; a relative path without an injected root is rejected as an
invalid receipt, a failure distinct from the cross-check rejection. Each
failure prints its specific message on stderr. A rejected receipt fails
closed before driver construction: the driver CLI exits non-zero with an
"approval receipt" failure message on stderr (no normalized result is
emitted) and preserves the machine manifest, so the run stays resumable.
Remediation is operator re-attestation: re-activate the host runtime,
confirm its non-interactive approval policy, and issue a fresh mode-0600
receipt recording the current config path and fingerprint; this is the
same remediation as any other failed activation attestation. Pre-upgrade
receipts lacking `config_path` or `policy_fingerprint` (or carrying a
looser file mode) fail closed under this reading by design; re-attesting
them after host re-activation is a documented migration step, not an
unplanned break.

## Fallback mechanics

The registry owns this profile's capability states and fallback; this
section defines only how the host applies them. A degraded or
unsupported capability returns the registry-owned fallback text with the
blocked or degraded result, never a widened capability: the host cannot
turn a degraded capability into full, bypass approval, or enforce policy
its event surface cannot carry. A host that cannot enforce the action
envelope and policy-token boundary returns
`blocked: runtime-policy-unavailable` before launch. Every fallback
outcome is a durable receipt the parent can reconcile, so a degraded
host degrades visibly instead of silently.
