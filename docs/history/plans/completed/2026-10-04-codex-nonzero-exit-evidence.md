# Plan: Codex nonzero-exit evidence preservation and the fenced terminal-exit recovery

Backlog origin: docs/history/backlog/2026-10-04-execute-plan-codex-nonzero-exit-evidence.md
Driving force: reliability (primary, the witnessed evidence loss and the capacity wedge), consistency (secondary, the recovery-operation family parity)
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-codex-nonzero-exit-evidence-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A nonzero Codex host exit no longer discards the terminal evidence already captured from stdout, and a receipt-proven terminal worker wedged by that exit has a driver-owned recovery exit. The adapter classifies every nonzero exit against the parsed JSONL stream into four explicit outcome classes (provider-reported task failure, completed turn plus nonzero exit, malformed output, no envelope), and the driver gains a fenced terminal-exit recovery transition that releases only the matching reservation and claim identity for a receipt-proven terminal worker, without waiting for a lease and without touching another task's capacity.

- The witnessed 2026-10-03 shape (a completed worker response behind `wait exit=1`, the claim fenced `runtime-error`, the launch reservation left behind, and an expired-lease `reclaim` returning `capacity-unavailable` with evidence `launch-reservation` behind that surviving reservation) becomes two named outcomes instead of a generic refusal plus a wedge that only a lease cycle clears.
- Fail-closed is preserved: a completed envelope behind a nonzero exit is never a success by itself, and the recovery releases capacity and claim identity only; task completion still requires the driver-validated verification evidence path, and natural-language completion alone never satisfies a task.

Gate delta: additions are two adapter reason codes (`provider-failed`, `completed-nonzero-exit`) registered in `runtime_capabilities.REASON_CODES` (the closed vocabulary fails closed on unknown codes, so registration is a named step, not an accident), with `completed-nonzero-exit` pinned to the blocked status and a `recover-terminal-exit` recovery-action hint, one fenced driver recovery operation carrying the sixth member of the append-only recovery-event family (`terminal-exit-recovery`, replay fence evaluated first, per the family's house discipline) with its operator-facing CLI registration, and two rows added to `DIAGNOSE_REASON_CLASSIFICATIONS` owned by this plan (the table's own comment defers new recurring gates to a backlog decision; this plan is that decision). Paying siblings: the recovery operation mirrors the existing reclaim lease-bypass arms (the precedent for a release that never waits for a lease) and reuses the existing identity-triple reservation pop, so no new mutation primitive is introduced; the blocked-persist path already preserves the raw adapter receipt under the stamped claim identity, so the routing change is a gate-set extension plus one tail carve-out, never a new persistence shape. Removals: none. Zero-exit adapter paths and the existing reclaim, resume, and validation flows are byte-stable.

## Terms

- Terminal envelope: the final JSONL stream item selected by the adapter's consult-grade final-selection rule (an item carrying a top-level `status`, or type `turn.completed`/`result`, or a payload mapping carrying the same keys or the `task_complete` type normalized to `turn.completed`), translated by `translate_host_result`; Task 1's classification reuses this richer rule, not the narrower live-prompt-only form, so a payload-nested completed turn classifies identically at the adapter and at the terminal-evidence consult.
- Provider-reported task failure (`provider-failed`): a parsed stream whose selected envelope carries type `turn.failed` or `error` (top-level or payload-nested, the adapter's only live failure classification); outcome stays blocked with `resume_allowed` pinned to `False`, evidence carries the provider reason beside the host exit.
- Completed turn plus nonzero exit (`completed-nonzero-exit`): a parsed stream whose translated terminal envelope proves the turn completed while the host process exited nonzero; outcome is the blocked status with the new reason code, the completion receipt beside the host exit in evidence, and the `recover-terminal-exit` recovery-action hint; never a success classification.
- Malformed output: a nonzero-exit stream with parseable envelopes whose selected envelope translates to neither a completed turn nor one of the two failure types (approval-required translations, bare `status` values without a recognized type, unknown statuses, and streams proving no terminal item); the existing `malformed-result` class with the host exit in evidence, except that a stream with no envelopes at all keeps the existing `runtime-error` class.
- No envelope: a nonzero-exit stream with no parseable JSONL envelopes; the existing `runtime-error` class unchanged.
- Receipt-proven terminal: the adapter's provider-terminal-evidence consult returns a proof with `verified: true` and kind `provider-terminal` for the session identity named in the blocked receipt.
- Terminal-exit recovery: the fenced driver operation that releases one wedged `completed-nonzero-exit` claim (the witnessed `runtime-error` shape's new reason code; reservation plus claim identity) under the receipt-proven-terminal precondition, recording the sixth recovery-event family member.
- Identity triple: `(task_id, claim token, generation)`, the matching key the existing reservation pop already uses.

## Assumptions

- Anchors were re-derived from the live bytes at authoring time (2026-10-04, HEAD a58f98ef): the adapter's nonzero-returncode arm in `_invoke_and_translate` returns before `_jsonl()`; the final-selection rule and the identity-field attachment live in the zero-exit continuation of the same method; `_blocked`/`_success` pin the result shape including the `recovery_action` field; the driver's recovery-event constants sit in one block; `DIAGNOSE_REASON_CLASSIFICATIONS` maps reason codes to families; the reclaim body carries the lease-bypass precedents and the batch-member refusal rule. Tasks anchor to those byte shapes, never to line numbers; execution re-derives each anchor before editing.
- The row's witnessed session (2026-10-03 CV plan, session `01a1038b-1591-7311-b6f6-9947eefd21be`) lives in a consumer repository, so its run artifacts are not re-derivable here; the fixtures synthesize equivalent shapes (a completed-turn envelope stream plus a nonzero exit; a wedged reservation keyed to a blocked claim's identity triple) per the row's Evidence section, and execution records the fixture-to-witness mapping in the session notes.
- Both new reason codes classify under the existing `worker-failure` diagnose family: the run did not produce an accepted completion, so diagnostics treat it as a worker-class failure; no new family is introduced.
- The recovery operation's lease freedom is bounded by its preconditions: it never reads `CLAIM_LEASE_SECONDS` and never refuses on claim age; its only time dependency is the terminal-evidence consult's own existing deadline.
- The batch-member fence is deliberately stricter than reclaim, not a mirror: every member of a live batch claim group refuses with the group named, including non-resumable members; reclaim's one executable exit (a non-resumable member's group-failing release) is not replicated here, and a live-group member's recovery stays bounded by the existing group-member reclaim exits (both lease-free).
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the Codex adapter preserves and classifies terminal evidence behind nonzero exits and the driver gains a fenced recovery that unwedges receipt-proven terminal workers without lease waits, why: one witnessed run lost a completed worker response to a generic `runtime-error` and wedged its launch reservation for a lease period, driving force reliability.

The adapter's `_invoke_and_translate` checks the host returncode before parsing stdout, so the bounded JSONL terminal envelope the run already captured is discarded exactly when the host fails: the driver sees only `nonzero host exit`, latches the claim blocked, and the launch reservation keyed to that claim's identity triple stays in the manifest. The ordinary expired-lease reclaim then refuses behind that reservation (`capacity-unavailable`, evidence `launch-reservation`), and no recovery operation matches the shape: the witnessed task stayed wedged until the four-hour lease elapsed even after the worker registry proved the provider session terminal. After this plan, the same exit parses the stream first and reports which of the four classes fired, with the completion receipt and session identity preserved when the stream proves them; the driver's persist routing keeps the identity-bearing receipt and deliberately holds the matching reservation as the durable wedge for the `completed-nonzero-exit` class; and the driver's terminal-exit recovery, preconditioned on that receipt plus a live provider-terminal proof, releases the matching reservation and rotates the claim out of the blocked state in one locked transition, telling the operator whether to `retry`, `repair-evidence`, or `preserve` the claim for investigation.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: each of the four nonzero-exit classes fires on exactly its fixture shape with the pinned reason codes, evidence composition, and recovery-action hints; the zero-exit classification paths are byte-stable.
- Fail-closed: `completed-nonzero-exit` never carries a success status and never satisfies verification by itself; the recovery refuses to release anything when the terminal proof is unverified, and a replayed recovery is refused by the family's replay fence.
- Identity containment: the recovery mutates only the reservation and claim matching the blocked receipt's identity triple; another task's reservation, capacity entries, and claims are untouched in every fixture.
- Non-regression: the existing reclaim, resume, validation, and blocked-persist flows keep their behavior on the final bytes; both suites stay green including all pre-existing fixtures.
- Family parity: the new recovery operation follows the recovery-event house discipline (append-only event constant beside the existing block, replay fence evaluated first, locked compare-and-swap, named dispositions).

**Done when:**

- `python3 scripts/test_execute_plan_runtime_codex.py` and `python3 scripts/test_execute_plan_runtime.py` pass on the final bytes, including the new fixture families (four adapter classes plus the consult-grade selection fixture; recovery happy path, replay refusal, lease-free proof, identity mismatch, unproven-terminal preserve, batch-member refusal, foreign-reservation containment, and the persist-routing pair), with `python3 scripts/test_runtime_capabilities.py` green on the registration.
- `python3 scripts/machinery_inventory.py --check` exits 1 on the pre-existing unrelated baseline; the recorded receipt asserts none of its rows name this plan's files (no new script files were added).

**Ship when:**

- The next nonzero-exit run preserves and classifies its terminal envelope, and a receipt-proven terminal wedge is cleared by the recovery transition without lease waiting on a routine run (loop-owned condition; the suites' own fixtures hold).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/execute_plan_runtime_codex.py` (the nonzero arm of `_invoke_and_translate` gains the envelope-preserving classification; module docstring)
- `scripts/execute_plan_runtime.py` (the fenced terminal-exit recovery operation, its event constant and CLI registration, the blocked-persist routing extension, the two `DIAGNOSE_REASON_CLASSIFICATIONS` rows, and the reason-class documentation)
- `scripts/runtime_capabilities.py` (the closed `REASON_CODES` set registers the two new codes)

**Tests:**

- `scripts/test_execute_plan_runtime_codex.py` (the four-class fixture family on the injected runner seam)
- `scripts/test_execute_plan_runtime.py` (the recovery fixture family on a synthetic manifest, and the persist-routing fixtures)
- `scripts/test_runtime_capabilities.py` (the reason-code registration fixtures)

**Contract files:**

- `scripts/OUTCOME_CONTRACT.md` (consulted, no change required: no outcome-contract rows exist for these scripts today, and this plan adds none)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- Treating a completed envelope as success on a nonzero exit, or weakening `validate_adapter_result`'s verification-criteria and claim-identity checks; reason: rejected alternatives in the dispatch entry; the path fails closed today and stays fail-closed.
- A global reclaim sweep for mismatched reservations, or extending the expired-lease reclaim's own semantics; reason: rejected alternative; the recovery releases only its own matching identity, and reclaim is byte-stable.
- Silent automatic retry of `runtime-error` tasks inside the recovery; reason: rejected alternative; the recovery is evidence-adjudicated and operator-visible, and any retry re-enters through the ordinary claim path.
- The resume path's session continuation behavior and the worker registry's own capacity reconciliation; reason: no witnessed defect in them; the registry's provider-terminal receipt is consumed as evidence, not modified.

## Validation Commands

```bash
python3 scripts/test_execute_plan_runtime_codex.py
python3 scripts/test_execute_plan_runtime.py
python3 scripts/machinery_inventory.py --check
bash scripts/check-no-em-dash.sh added-lines --base <merge-base at landing>
```

### Task 1: the adapter classifies nonzero exits against the parsed envelope stream

Files:
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/runtime_capabilities.py`
- `scripts/test_runtime_capabilities.py`

Write the RED fixture first on the suite's existing injection seam (a runner callable returning `{"returncode": 1, "stdout": <stream>}`): a completed-turn envelope stream behind exit 1, the row's witnessed shape; assert the current outcome is the generic `runtime-error` with the envelope discarded, and record that run as the RED receipt. Then:

- Register both new reason codes in `runtime_capabilities.REASON_CODES` with companion fixtures in its suite: the set is closed and `normalize_result` fails closed on unknown codes, so an unregistered code cannot cross the driver boundary; this step lands before any classification that emits the codes.
- In the nonzero-returncode arm of `_invoke_and_translate`, parse the captured stdout before classifying: `envelopes, malformed = self._jsonl(str(result.get("stdout", "")))` runs first; the exit evidence lines (`<operation> exit=<code>`, `nonzero host exit`) are composed once and reused by every class below.
- No envelopes: return the existing `_blocked("runtime-error", [exit evidence])` shape unchanged (the no-envelope class; the generic unclassified process exit keeps its name and shape).
- Envelopes present: select the terminal envelope with the consult-grade rule (a top-level `status` key, type `turn.completed`/`result`, or a payload mapping carrying the same keys, with `task_complete` normalized to `turn.completed`), so a payload-nested completed turn classifies identically here and at the terminal-evidence consult.
- A selected envelope that translates to a completed turn (`status == "success"` and `reason_code == "completed"`): build the translated result exactly as the zero-exit path does, including every identity field attachment (`session_id`, `provider_session_id`, `worker_id`, `launch_id`, `capacity_entry_id`, `command_identity`, `process_identity`, `observed_at`), then set `status` to `"blocked"`, `reason_code` to `"completed-nonzero-exit"`, prepend the exit evidence to the result's evidence, and set `recovery_action` to `"recover-terminal-exit"` (the completed-turn-plus-nonzero-exit class; never a success classification).
- A selected envelope carrying type `turn.failed` or `error` (top-level or payload-nested, the adapter's only live failure classification): return the translated result with `reason_code` set to `"provider-failed"`, `resume_allowed` explicitly set to `False` (the translated result otherwise inherits a resumable default from the runtime-error family, which would persist the receipt auto-resumable and defeat the pop treatment), the exit evidence prepended, and `recovery_action` left at the blocked default `"preserve-and-reconcile"` (the provider-reported task failure class).
- Anything else with envelopes present (approval-required translations, bare `status` values without a recognized type, unknown statuses, streams proving no terminal item): return `_blocked("malformed-result", [exit evidence plus the no-terminal-envelope wording])` (the malformed-output class as the deterministic fallback).
- Boundedness: only the final envelope's translated fields plus the identity fields are preserved; the raw stream is never attached, and evidence passes through `bounded_evidence`.
- Every byte of the zero-exit paths (including the no-envelope and malformed classifications there) is unchanged.

Evidence: `python3 scripts/test_execute_plan_runtime_codex.py` (the four RED-to-GREEN fixtures: provider-failed, completed-nonzero-exit with identity fields present and status blocked, malformed-output fallback, no-envelope; a payload-nested completed-turn fixture asserting the consult-grade selection; zero-exit regression fixtures asserting the unchanged classes) and `python3 scripts/test_runtime_capabilities.py` (both codes accepted by `normalize_result`; an unknown code still fails closed); the full existing suites stay green.

### Task 2: the fenced terminal-exit recovery transition

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Write the RED fixture first on a synthetic manifest: a task blocked with a `blocked_receipt` shaped like Task 1's `completed-nonzero-exit` result (session identity and `launch_id` present), a live claim matching the receipt's identity triple, and a launch reservation keyed to that triple; assert that today no operation releases that wedge without lease expiry, and record the run as the RED receipt. Then implement, in this order:

- The blocked-persist routing, pinned before the recovery exists to consume it, on BOTH persist routes: every driver-side gate that routes nonzero receipts into the blocked persist admits the two new codes identically (the launch-path gate whose set names `runtime-policy-unavailable`, `runtime-error`, `timeout` is the anchor and the only gate-set literal in the driver; execution re-derives the census before editing), and the checkpoint route (the wait receipt's actual path: the checkpoint operation into the record-checkpoint chain's blocked arm, the witnessed shape's route) persists the two new classes through the locked persist variant under its already-held manifest lock, never the re-entrant wrapper, so the persisted receipt is the raw identity-bearing result with the stamped claim identity on every route. `_persist_blocked_claim_locked` stores that raw receipt with the identity fields intact and the claim token and generation stamped (existing behavior, unchanged), and its non-resumable tail gains one carve-out keyed on the reason code: a `completed-nonzero-exit` receipt keeps its launch reservation and launch record (the receipt is the recovery-pending wedge and the reservation is its durable placeholder; the tail's residue rationale is updated to name this class), while `provider-failed` keeps the existing pop treatment (a genuinely failed task leaves no recovery leg; its `resume_allowed` is `False` per Task 1, so the existing pop branch fires).
- The event constant `TERMINAL_EXIT_RECOVERY_EVENT = "terminal-exit-recovery"` beside the existing recovery-event constants, with the same append-only and replay-fence discipline the family documents.
- The recovery operation (one public method) evaluates, in order: the replay fence first (a recorded `terminal-exit-recovery` event for the same identity triple refuses); the task is blocked with `blocked_receipt.reason_code == "completed-nonzero-exit"`; the live claim's token and generation match the receipt's identity triple (a rotated claim refuses); the claim is not a member of a live batch claim group (every member refuses with the group named, deliberately stricter than reclaim, whose non-resumable-member executable exit is not replicated here); the terminal-evidence consult (the adapter's provider-terminal-evidence path reached through the driver's consult wrapper, `verified: true`, kind `provider-terminal`) proves the receipt's session identity terminal.
- Any failed precondition returns the fail-closed outcome with nothing mutated; the unproven-terminal case returns the `preserve` disposition for investigation.
- The action runs under one manifest lock as a single compare-and-swap: the launch reservation matching the identity triple is popped via the existing locked pop helper; the claim rotates per the reclaim release shape (generation and token rotate, the old claim is marked replaced, the task resets to pending with resume fields stripped and recorded checkpoints preserved); the `terminal-exit-recovery` history event appends with the receipt, the proof, and the disposition.
- The operation never reads `CLAIM_LEASE_SECONDS` and never refuses on claim age; a fresh-claim fixture (blocked moments ago) recovers where reclaim would refuse before expiry.
- The result's guidance names one of three dispositions: `retry` (proof verified, no recorded verification evidence: safe to re-claim through the ordinary path), `repair-evidence` (proof verified with partial verification evidence recorded: reconcile before retrying), `preserve` (proof unproven: nothing released).
- The operator-facing CLI registration: the operation name joins the CLI's operation choices with a payload handler beside the existing recover-* siblings, so the transition is reachable on a routine run, not only as a library method.
- Task-completion authority is untouched: the recovery releases capacity and claim identity only; any later completion still passes the driver's verification-criteria and claim-identity checks, and natural-language completion alone never satisfies a task.
- `DIAGNOSE_REASON_CLASSIFICATIONS` gains `"completed-nonzero-exit": "worker-failure"` and `"provider-failed": "worker-failure"` beside the existing rows, and the reason-class documentation region naming the worker-failure members gains both codes.

Evidence: `python3 scripts/test_execute_plan_runtime.py` (the persist-routing fixtures on both routes: a `completed-nonzero-exit` launch receipt persists the raw identity-bearing receipt and keeps its reservation; the same receipt persisted through the checkpoint route keeps its identity and reservation; a `provider-failed` receipt persists and pops on the launch route; the recovery happy path: reservation popped, claim rotated, task pending, event appended, disposition `retry`; the replayed recovery refused; the fresh-claim lease-free proof; the identity-mismatch refusal; the unproven-terminal preserve with a byte-identical manifest afterward; the batch-member refusal naming the group; a foreign task's reservation untouched in every fixture; the full existing suite stays green).

### Task 3: docstring and inventory alignment

Files:
- `scripts/execute_plan_runtime_codex.py` (module docstring)
- `scripts/execute_plan_runtime.py` (the recovery-event family comment block)

Evidence:
- The adapter module docstring names the four nonzero-exit classes with the witnessed shape cited by date and session id from the origin row.
- The recovery-event family comment names `terminal-exit-recovery` as the sixth member with its precondition one-liner.
- `python3 scripts/machinery_inventory.py --check` exits 1 today on pre-existing unrelated rows; the receipt asserts none of the reported rows name this plan's files (no new script files were added), and both suites are green on the final bytes.

## Disposition

Executed 2026-10-04 in worktree ai-playbook-wt-cnxe (branch plan-cnxe-exec) under the merge lock; implementation commits 83e9126c (Task 1), 545bf551 (Task 2), c9fb6999 (Task 3), fold commit 67657951. Exec review: r1 ready=no (1 blocking, 3 Low), all four folded, r2 focused re-certification ready=yes zero findings (records: docs/reviews/2026-10-04-plan-review-codex-nonzero-exit-evidence-exec-r{1,2}.md, gitignored home). Suites on the final bytes: test_execute_plan_runtime.py 702 OK, test_execute_plan_runtime_codex.py 58 OK, test_runtime_capabilities.py 44 OK; machinery_inventory --check exits 1 on 5 pre-existing unrelated baseline rows, none naming this plan's files (no new script files were added).

RED receipts recorded in-session: Task 1's completed-nonzero-exit fixture first asserted the generic runtime-error classification (7 tests run, 4 failing pre-implementation); Task 2's wedge fixture first proved no operation releases a fresh completed-nonzero-exit claim without lease expiry (12 tests run, 2 failures + 8 errors pre-implementation). The pin that today no operation releases the fresh wedge without lease expiry remains in the suite as test_red_no_operation_releases_fresh_wedge_without_lease.

Execution deviations of record: the machinery-inventory baseline carries 5 unregistered rows at execution time (4 script files from peer landings, 1 state field from the recurring-task-registry landing); per the standing disposition doctrine these are peer debt, none were registered here, and the plan's own diff adds zero scripts/*.py entries. The r1 blocking finding B1 (the fold of an earlier decorator collision had stripped reclaim's manifest-lock fence) was introduced and repaired within this execution; reclaim is byte-stable on the final bytes.
