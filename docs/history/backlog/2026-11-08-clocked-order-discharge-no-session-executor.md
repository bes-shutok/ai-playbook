# Backlog: clocked-order discharge-on-fire marks the order discharged without ever executing its payload in a session

- **Filed:** 2026-11-08, interactive investigation after the 2026-11-07 23:12Z exec dispatch produced no execution
- **Status:** covered-pending-execution (docs/history/plans/2026-11-08-clocked-order-payload-session-execution.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed defect (execution lane, silent loss of one mandated execution)
- **Class:** fix-class
- **Surface:** `scripts/execute_plan_resume_watcher.py` (`build_clocked_order_fire_command`, the `discharge-on-fire` handler in `run_clocked_order_operation`), `scripts/execute_plan_runtime.py` (`_clocked_order_operation`); consumers: the maintenance overlay's clocked-order chain legs (`agents/skills/maintenance/zcode.md`, Child dispatch ladder + Re-arm hygiene chain default), the execution blueprint's ZCODE SUCCESSOR DISPATCH chain route, `docs/maintenance/recurring-tasks/` clocked-order consults
- **Dedup probe:** searched open backlog bodies and the watcher script history for `discharge`, `chain`, `clocked-order`, `headless session`; the landed `f3894756d` owns the fire-command builder as introduced; no open row owns the missing session-executor leg
- **Cluster:** `docs/history/backlog/2026-11-08-clocked-order-discharge-no-session-executor.md` (this row)

## Observed versus expected

Observed: a user-directed one-shot exec payload (automation-40615ca2, fired 2026-11-07 23:00Z) selected `docs/history/plans/2026-11-05-claimed-top-target-skip-and-continue.md`, passed all guards/probe/admission, and dispatched through the bound-session default chain leg (`clocked-order-schedule`, order `co-694c706ba27c4e3686abb5db8d0b827b`, arming proof verified). launchd fired the job at 23:12:05 (`sentinel.fired`, `late_by_seconds: 5`), and `clocked-order-discharge-on-fire` flipped the ledger to `discharged` — and stopped. The fire command built by `build_clocked_order_fire_command` runs only `python3 scripts/execute_plan_runtime.py --operation clocked-order-discharge-on-fire`: it never launches a headless ZCode session with the order's payload text. Result: no execution claim, no worktree, no task-index session row, plan untouched, and the state file's `children[]` entry left `pending` forever. The discharge is bookkeeping-only; the chain leg — which the 2026-11-03 promotion review made the operative default for every bound-session dispatch (loop re-arm, successor chaining, lane dispatches) — has **no executor leg at all**. Historical discharged orders (e.g. `co-10ea834e` 2026-10-28 auth-pick1-r2-resume) are suspect for the same silent loss; the `verify-successor` stall classification exists but treats this as darkness to re-arm around, never as a broken executor.

Expected: firing a clocked order executes its payload — the discharge runs inside (or alongside) a headless session whose prompt is the order's payload copy, so the mandated work actually happens and the ledger's `discharged` state attests a real run, not a consumed sentinel.

## Evidence

- `~/.ai-playbook/runtime/launchd/clocked-order-a25342389f8f/` plist `ProgramArguments`: `/bin/sh -c` sentinel guards + provider-config exports + `python3 execute_plan_runtime.py --operation clocked-order-discharge-on-fire --input '{...}'` — no ZCode CLI invocation, no payload prompt anywhere in the command.
- Out log records `{"discharged": true, "late": true, "late_by_seconds": 5, ...}`; ledger history ends at `order-discharged`.
- `git show f3894756d` (2026-10-18 "streamline gates and recovery tooling") introduces both the builder and the handler with exactly this shape; no later commit added a session-launch leg.
- Post-fire survey 2026-11-08: no `docs/tmp/execution-claims/claimed-top-target-skip-and-continue.md`, no matching worktree, no `automation_runs` row other than the spawner's own, plan still `Executed: no` and open.
- The maintenance overlay's own text (Launchd resume carrier bullet: "the payload invokes the `clocked-order-discharge-on-fire` operation over the recorded order identity") reads as if the payload session invokes discharge; the landed builder inverts that — discharge runs with no payload session.

## Fix direction (not a design)

One executor leg, bounded: the discharge path (or the plist command) launches the env-complete headless session with the recorded payload copy as the prompt, first action being the existing `clocked-order-discharge-on-fire` identity check (keeping the exactly-once fence), with a discharge-failure branch that leaves the order re-armable (`missed`/`pending`) instead of silently consumed; the `children[]` entry writer records the executor's session id so the failure cap can see the run. Machinery admission: this closes a witnessed silent-loss defect; no new gate — a repair to the activated chain default's executor half.
