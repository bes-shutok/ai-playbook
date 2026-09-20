# Backlog: require terminal-path and boundary-contract coverage in review panels

Status: open
Priority: medium
Workflow: backlog
Class: review-agent coverage
Driving force: correctness

## Problem

An external review can still find several accepted miss shapes after a full
internal review when the changed code crosses asynchronous lifecycle, logging,
configuration provenance, persistence binding, or paired-record boundaries.
The common failure is that the panel checks the primary path and representative
tests but does not enumerate every terminal path or preserve the contract at
each boundary.

Observed abstract miss shapes include:

1. A terminal route reached from an unexpected batch or admission-rejection
   path without acquiring the same in-flight ownership as the normal path.
2. A logging filter that validates message text but permits an attached
   throwable whose rendered cause chain can disclose unsafe data.
3. A provenance check that rejects the standard environment source used to
   materialize explicitly named deployment credentials.
4. A nullable persistence value without an explicit JDBC type for the SQL NULL
   case.
5. A paired fact normalized from the other fact's timestamp, masking a
   mismatch that should be rejected.
6. A provenance guard that validates an accepted alias instead of the exact
   value returned by the framework's effective property lookup, allowing a
   higher-precedence override to bypass the guard.
7. An audit-bearing record that relies on generated `toString()` and exposes
   operator, key, or evidence fields when diagnostics render the object.
8. A multi-fact update that persists every fact but enqueues dependencies for
   only one changed fact, leaving predicates for the omitted fact stale.
9. A packaged local-development artifact that includes an older schema or
   seed ordering than the canonical migration set.
10. A safe-logging rule that treats arbitrary string parameters as harmless
    because they match an identifier-shaped pattern, even though secrets and
    payload fragments can have the same shape.
11. A batch decision that uses the first message's retry count instead of the
    whole batch, terminal-routing messages that still have retry attempts.
12. An idempotency key that is treated as compatible after checking only a
    subset of immutable origin and representation fields.
13. A state transition update that bypasses the evidence-bearing reconciliation
    path for a recovery-required record.
14. A glossary or contract statement that still describes the old null,
    omission, or empty-object behavior after implementation semantics change.
15. A safe-log filter that handles known container types but leaves unknown
    non-null objects neutral, allowing sensitive `toString()` output through.
16. A production provenance check that validates the source of a security
    setting without validating the effective value required by the policy.
17. A provenance check that inspects the source of an unresolved placeholder
    instead of the allowed source of the effective environment value, causing
    documented deployment configuration to fail or allowing an override.
18. A terminal-only asynchronous route that passes no completion witness, so a
    timeout can release lifecycle admission while the send-back task is still
    running.
19. A transaction-manager override that performs post-begin setup and throws
    without explicitly rolling back and cleaning up the connection it already
    bound to the thread.
20. A recovery reconciliation update that accepts the already-recorded state as
    its expected state and consequently overwrites first-write audit evidence.
21. A framework-generated aggregate property source that shadows the real
    origin source during provenance inspection, causing approved configuration
    to fail or bypass effective-value checks.
22. A concurrent idempotent-retry check that compares a failed update with its
    stale pre-race snapshot instead of the complete post-race record.
23. A deduplicated job payload merge that mutates a `CLAIMED` row in place,
    allowing the current worker to complete without observing the new source.
24. A transaction-manager hook that assumes its `doBegin` argument is a
    transaction status instead of the framework's transaction object.

## Suggested fix

Extend the correctness, architecture, testing, and relevant language-overlay
review guidance with a boundary-contract pass:

1. Enumerate every terminal, fallback, rejection, callback, and batch path and
   verify that each path owns and releases the same lifecycle state around
   asynchronous work.
2. For security-sensitive filters, inspect the full rendered object including
   attached causes, not only the primary message or fields.
3. For configuration provenance, trace the deployment representation through
   the framework property source and validate the exact allowed source/key
   pairing.
4. For nullable mapper parameters, require an explicit JDBC type and a test
   that exercises the null representation.
5. For paired or correlated records, normalize each record from its own source
   fields before applying equality or ordering checks.
6. Trace security and configuration checks from the effective value back to
   its exact property source; do not accept an alias unless it controls the
   value actually consumed by the application.
7. Treat audit and recovery value objects as sensitive by default. Require an
   explicit safe `toString()` witness whenever they carry operator, evidence,
   credential, or retained-body metadata.
8. Enumerate every fact written by a multi-fact transaction and compare that
   set with the dependency sources passed to downstream job coordination.
9. Compare packaged deployment and local-development manifests against the
   canonical migration and seed inventory, including ordering.
10. Treat arbitrary logging strings as unsafe unless an explicit allowlist
    proves the field is non-sensitive; add a secret-shaped regression witness.
11. For batch retry and terminal decisions, evaluate all records and test a
    mixed-exhaustion batch, not only uniform batches.
12. Compare every immutable idempotency identity field, or a stored digest,
    before returning an already-reserved result.
13. Model state transitions as a closed table and require sensitive recovery
    states to pass through their evidence-bearing reconciliation operation.
14. Search canonical and peer documentation for old semantics whenever a
    null, omission, or empty-object contract changes.
15. Make security-sensitive logging filters fail closed for unknown non-null
    objects, and add object/container `toString()` regression witnesses.
16. Separate provenance validation from value validation: test both the
    approved source and every production-safe effective value constraint.
17. Resolve placeholders through the framework's effective lookup, verify the
    exact placeholder-to-environment-key mapping, and test both documented
    deployment success and higher-precedence override rejection.
18. For every asynchronous terminal path, carry an explicit completion witness
    through the deadline helper and release lifecycle admission only from the
    completion callback, including non-cooperative timeout tests.
19. When extending transaction-manager begin hooks, audit the superclass
    cleanup contract and test setup failure after binding; rollback and clean
    up before propagating the failure.
20. Treat recovery audit fields as first-write-wins once a record is
    `RECOVERY_REQUIRED`; permit only an identical retry and reject conflicting
    operator, evidence, disposition, or timestamp values at the atomic update.
21. Identify and skip framework aggregate property sources, then verify the
    effective value and its real underlying origin, including higher-precedence
    override rejection.
22. For every compare-after-zero update, re-read the complete persisted tuple
    after the race and compare every idempotency field, including timestamps.
23. For job dedupe merges, explicitly model the `CLAIMED` case: invalidate or
    requeue the active claim so newly merged payload sources receive a worker
    turn instead of being completed by the stale worker.
24. Treat transaction callback arguments as framework-specific handles; verify
    their runtime type before invoking rollback or cleanup hooks and use the
    bound resource directly when the hook has no transaction status.
25. For asynchronous completion callbacks that release lifecycle ownership,
    distinguish task completion from decision completion; require the release
    witness to be gated until the enclosing route or acknowledgement decision
    has inspected the task result.

26. For configuration, persistence, logging, and lifecycle changes, require a
    changed-code family inventory before accepting a representative witness.
    The inventory must cover direct callers, sibling mappers, aliases and
    placeholders, all terminal exits, all derived fan-out keys, and every
    rendered logging input. An explicit not-applicable result is required when
    a family is absent.
27. For first-write-wins SQL updates whose audit tuple starts as NULL, model
    the fresh-claim, identical-retry, and conflicting-retry predicates
    explicitly. SQL equality against NULL never matches, so the empty-tuple
    branch must use `IS NULL` for every field and tests must cover all three
    outcomes.

The panel should require at least one adversarial witness for each boundary
class exercised by the diff, and should treat an unenumerated terminal path as
an incomplete review rather than as an untested edge case.

## Acceptance criteria

- Review guidance names the boundary classes above without
  product-specific identifiers.
- The testing lens requires terminal-path and null/boundary witnesses when the
  diff changes lifecycle, mapping, or validation behavior.
- The architecture/correctness lens requires a path inventory for asynchronous
  terminal routing and paired-record invariants.
- A review can record an explicit not-applicable disposition when none of the
  boundary classes is present.
- The review panel has a reusable checklist or helper for effective property
  source, sensitive `toString()`, multi-fact fan-out, and packaged-schema
  parity checks.
- The panel records a changed-code family inventory and does not report a
  boundary-sensitive round clear while an applicable family lacks a witness.
- Persistence review guidance checks nullable first-claim predicates for SQL
  three-valued logic and requires fresh-claim, idempotent-retry, and
  conflicting-retry witnesses.

## Non-goals

- Do not require every review to inspect unrelated infrastructure or enumerate
  every code path in the repository.
- Do not duplicate the existing passive-review reply and resolution completion
  gate.
