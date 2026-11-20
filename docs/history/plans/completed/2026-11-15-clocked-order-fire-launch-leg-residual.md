# Plan: clocked order fire path records an explicit launch-failure event

Backlog origin: docs/history/backlog/2026-11-04-clocked-order-fire-launch-leg-residual.md
Driving force: reliability
Authoring claim: 2026-11-04-clocked-order-fire-launch-leg-residual.md (session sess_a619cb2b-4b18-4479-a9d7-3b58eb1afeb9)
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-clocked-order-fire-launch-leg-residual-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 1h
Executed: yes (4681da8a3)
Language guidelines: projects/.ai-playbook/python_guidelines.md

## Terms

- fire command: the shell command `build_clocked_order_fire_command` generates: provider exports, cd to the repository root, `clocked-order-begin-fire`, then the brace group that launches the payload session and, on a nonzero launcher exit, runs `clocked-order-clear-fire` before propagating the exit code
- handoff lease: the 60-minute lease `clocked-order-begin-fire` registers on the order before the launch; the discharge first action and the due scan both read it
- launch-failure event: a `launch-failed` entry in the order's ledger history carrying the launcher exit code, recorded when the fire command's clear leg runs because the launch exited nonzero and the order is still pending or armed
- clear-fire operation: the `clocked-order-clear-fire` operation; today it pops the lease, appends `handoff-lease-cleared`, and sweeps payload copies, never changing order state
- due detector: the `clocked-order-due` scan (`classify_due`), which marks a pending or armed order past its requested minute, without a live lease and without live discharge evidence, as missed
- discharge receipt: the `discharge-on-fire` success result (`status: success`, `discharged: true`) the fire prelude gates the stored payload on
- launcher exit code: the exit status the brace group captures from the payload-session launch (`fire_rc`)

## Why

A launch-failed clocked order's only ledger trail is the generic `handoff-lease-cleared` event, which carries no exit code and does not name the failure, so a fire-boundary misfire is reconstructed from surrounding events instead of read from the order. The row's structural ask (launch-before-discharge with a receipt-gated discharge, and due-detector recovery of a launch-failed order) already landed; the failure-event clause is the open remainder.

## Gist & Examples

TLDR: the clocked-order fire command records a `launch-failed` ledger event carrying the launcher exit code when the payload launch fails, so a fire-boundary misfire is readable from the order itself (driving force: reliability).

**Before:** a launch that exits nonzero clears the lease and leaves history `handoff-lease-registered` then `handoff-lease-cleared`; nothing distinguishes that trail from any other lease clear, and the exit code is lost. Recovery still works: the due scan marks the order missed once the lease is gone, but the ledger never says the launch failed or with what status.

**After:** the same failure records a `launch-failed` history event carrying the launcher exit code before the lease clears; the order still recovers through the unchanged due scan (`order-missed`), a successful launch records nothing new, and a `clocked-order-clear-fire` invocation without failure context behaves byte-identically to today.

**Edge cases:** a launcher crash after the session already discharged the order records no `launch-failed` event: the clear leg still runs (discharge never pops the lease, so the clear succeeds), but the new event's own pending-or-armed gate sees a terminal order and records nothing, because the payload was delivered and there is no launch failure to record; a lease-absent clear keeps its existing refusal shape and records no event; a refused begin-fire still starts no session and writes no event (unchanged); the exit code rides the existing payload-merge precedent, so the `--input` JSON object contract is unchanged.

## Outcome

A fired clocked order whose payload launch fails carries an explicit, self-describing failure event with the exit code in its ledger history.

- A fire-boundary misfire is readable from the order ledger alone: `launch-failed` with the exit code, followed by the unchanged `handoff-lease-cleared` and the due scan's `order-missed`.
- Successful launches and manual clear-fire invocations are unchanged; no new lock, gate, or detector is introduced.
- The row's landed structural reorder (launch-before-discharge, lease-gated discharge, due recovery) is preserved and pinned by the existing suite.

Gate delta: none (a new history event class on the ledger's existing history mechanism; no refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed; the activation posture and skill texts are unchanged per the origin entry's scope).

## Assumptions

- assume the structural reorder the origin row asked for (launch-before-discharge with the receipt-gated discharge, and due-detector recovery of a launch-failed order) already landed via commit 97331288e (the clocked-order-payload-session-execution execution landing); basis: authoring-time re-derivation of `build_clocked_order_fire_command`, `discharge_first_action`, `clear_fire`, and `classify_due` in `scripts/execute_plan_resume_watcher.py` at the authoring tip, plus the pinned tests `test_launch_refusal_or_failure_clears_lease_and_order_stays_recoverable` and `test_overdue_order_classified_missed_once` in `scripts/test_execute_plan_resume_watcher.py`
- assume the origin row's remaining open scope is the explicit launch-failure event only; basis: the row's Expected two prongs probe green against current source, and the Suggested change's "on launch failure record a failure event" clause is the unmatched remainder (today's trail is `handoff-lease-cleared` with no exit code and no failure semantics)

Decision points requiring a grill: launch-failure event transport: selected an explicit CLI operand on the `clocked-order-clear-fire` operation following the `--session-id` payload-merge precedent in `scripts/execute_plan_runtime.py` (source-resolved in-scope choice; simpler-design comparison: an environment-variable channel was rejected as hidden and untestable at the command surface, JSON template substitution into the fixed clear-leg input was rejected for shell-escaping risk on the generated command; the `--input` JSON object contract stays unchanged); recorded under the maintenance-selected standing authorization; date 2026-11-15; affected sections Terms, Gist & Examples, Tasks

## Standing constraints

- Keep the chain's activation posture and all skill texts unchanged (the origin entry's scope sentence); no task edits any file under `agents/skills/`.
- The due detector's marking behavior is unchanged; the event is recorded inside the existing single ledger critical section and introduces no lock, gate, or ledger schema field.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the event records only a true launch failure (order still pending or armed at clear time, exit code present); a post-discharge launcher crash on a terminal order records none
- reliability: the event lands inside the existing single ledger critical section shared with begin-fire and the due scan; no new lock or gate
- maintainability: `clocked-order-clear-fire` invoked without failure context behaves byte-identically to today (same events, same refusals)

**Done when:**
- the focused watcher suite passes including the new fixtures: event recorded with the exit code on a launch failure; no event when the clear leg is refused (lease absent) or the order is terminal; no event when no failure context is passed
- the generated fire command's clear leg carries the launcher exit code captured by the brace group
- `python3 scripts/plan_readiness.py <plan-path>` exits 0 over the assembled series

**Ship when:** none stated (repository-verifiable only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_resume_watcher.py` (Task 1)
- `scripts/execute_plan_runtime.py` (Task 1)

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/**`; reason: the origin entry's scope sentence keeps skill texts unchanged
- `scripts/execute_plan_resume_watcher.py` methods other than the clear-fire, fire-command, and clocked-order handler surfaces named in Task 1; reason: the ledger's discharge, schedule, cancel, and migration surfaces are frozen by this plan's invariants (partially-in-scope file freeze note: in `scripts/execute_plan_resume_watcher.py` only `build_clocked_order_fire_command`, `build_clocked_order_fire_prompt` docstring references to the clear leg, `clear_fire`/`_clear_fire_locked`, the `clear-fire` handler arm in the clocked-order operation dispatcher, and the runtime CLI argument surface are open; all other methods are frozen; reject any review finding that touches them)

## Validation Commands

Authoring preflight (rule 29, 2026-11-15, plan digest at wip checkpoint 84036701e): focused watcher suite 279 passed + 78 subtests (green; the plan is authoring-only, no production bytes changed); em-dash added-lines gate exit 0 over base 33c8bfa5f; public hygiene scan exit 0; pins suite not run (no pinned files touched).

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q
```

### Task 1: Record the launch-failed event on the fire path

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `ClockedOrderLedger` in `scripts/execute_plan_resume_watcher.py`
- `build_clocked_order_fire_command` in `scripts/execute_plan_resume_watcher.py`
- `main` in `scripts/execute_plan_runtime.py`

- [x] `ClockedOrderLedger.clear_fire` delivers the launch-failure event: given a clear-fire invocation carrying a launcher exit code whose order is pending or armed, expects one `launch-failed` history entry carrying that exit code, appended before the unchanged `handoff-lease-cleared` entry, with the lease still popped and the state unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a clear-fire invocation carrying a launcher exit code whose order is in a terminal state (discharged, cancelled, missed), expects the clear itself unchanged (it succeeds, the lease pops) and no `launch-failed` entry recorded, the event's own pending-or-armed gate being the mechanism; given a lease-absent clear carrying the operand, expects the existing refusal shape unchanged and no `launch-failed` entry recorded [class: REPOSITORY_TEST]
- [x] `main` in `scripts/execute_plan_runtime.py` delivers the failure-context operand: given `clocked-order-clear-fire` invoked with the explicit launcher exit code operand, expects the value merged into the operation payload per the `--session-id` precedent, and `--input`'s JSON object contract unchanged; given the operand absent, expects the payload without the key [class: IMPLEMENTATION_REQUIRED]
- [x] `build_clocked_order_fire_command` delivers the wired clear leg: given a generated fire command whose launch exits nonzero, expects the brace group to capture the launcher exit status and pass it to the clear leg, with a zero-exit launch still running no clear leg [class: IMPLEMENTATION_REQUIRED]
- [x] Exit-code value fidelity fixture: given a generated fire command run under `/bin/sh` against a fake launcher exiting with a known nonzero status, expects the recorded `launch-failed` history entry's exit code to equal the launcher's actual status, pinning value fidelity across the shell-to-CLI-to-ledger path [class: REPOSITORY_TEST]
- [x] Run the focused watcher suite -> expect RED on the new fixtures first [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused watcher suite -> expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: clocked order fire path records an explicit launch-failed event` [class: IMPLEMENTATION_REQUIRED]
