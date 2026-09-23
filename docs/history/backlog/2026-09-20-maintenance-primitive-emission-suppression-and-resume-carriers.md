# Backlog: automation-primitive action-selection loop suppresses the decided mutating emission; unattended resume carriers need env-complete launchd recipes

Status: open
Priority: medium
Workflow: backlog
Disposition: 2026-09-22 (annotated via docs/plans/2026-09-22-p36-scheduler-durability-audit.md, origin ledger): owned-elsewhere, the work lives in docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md Task 7 "Emission-suppression discipline and headless resume recipe" (certified, pending execution): the overlay dispatch-discipline witness, the headless resume recipe, the one-sentence budget-gate additions.

## Observed vs expected

Two fresh-session witnesses (2026-09-19 ~20:45 and 2026-09-20 ~09:10, different sessions,
both mid-authoring on legitimate non-dispatch work): after two or more identical read-only
primitive listings (CronList), the session's emission channel kept repeating the listing
and never emitted the already-decided `CronCreate` - the mutating call was suppressed
entirely, not merely delayed. The overlay's dispatch discipline (decide first, emit the
mutation in the same turn, stand down via Bash on the loop signature) was known and the
sessions still could not emit the create. Expected: a decided mutating call either fires or
the stand-down path carries the intent durably; the stand-down DID work both times (Bash +
driver CLI + launchd carrier completed the resume), so the gap is narrower: the discipline
text assumes the agent can always choose to emit the mutation, which is falsified on this
runtime.

Second, adjacent witness (2026-09-20 11:00): a hand-armed launchd resume job running
`zcode --prompt ... --cwd <repo> --mode yolo` died instantly with "cannot locate CLI ZCode
Built-in Provider Config" - the launchd environment lacks the `ZCODE_*` provider-config
env vars the desktop app supplies. A working headless resume recipe must export
`ZCODE_BUILTIN_PROVIDER_CONFIG_FILE` (and siblings) explicitly in the job script.

## Suggested fix

1. Extend the overlay's dispatch-discipline text (agents/skills/maintenance/zcode.md) with
   the emission-suppression witness: when a read-only primitive listing repeats twice with
   no mutation between, do not attempt a third listing OR a narrated create; stand down via
   a Bash state write immediately, and name the launchd + headless-CLI recipe as the
   sanctioned resume-carrier fallback when a scheduled resume must survive the session.
2. Document the env-complete headless recipe (provider-config env vars exported in the job
   script) wherever the overlay or the budget-gate pause protocols name launchd fallbacks.
3. Both budget-gate pause protocols (plans + execute-plan) reference automation-first
   carriers; note the suppression risk so a pause-boundary resume is not lost to it.
4. The guard-remedy redesign (one recorded mutation carve-out, operator override, dark-case
   mechanical carrier) is its own item, sequenced after this item's plan lands (same
   zcode.md dispatch-discipline region): 2026-09-21-loop-guard-one-recorded-mutation-carve-out.md.

## Witnesses

- 2026-09-19 20:45: 5x CronList, create suppressed; recovery via plans-watcher-schedule
  launchd chain (worked - the driver's own launchd bootstrap is env-complete).
- 2026-09-20 09:10: 4x CronList, create suppressed; recovery via hand-armed launchd job.
- 2026-09-20 11:00: livres20b launchd job fired and died instantly on the missing provider
  config (out.log carries the error), so the 11:00 resume silently no-op'd; detected only
  because the user prompted again at 12:00.
- 2026-09-20 23:53 (scheduler-turn re-arm variant, highest blast radius yet): the 23:51
  authoring-lane start one-shot (operator-dispatched maintenance turn) had the parent
  re-arm CronCreate decided and narrated but suppressed; a second CronList went out
  instead, the rearm loop guard fired (correctly, mechanically), and the turn stood down
  via the Bash rearm_note write. Unlike witnesses 1-2 the suppressed call was the loop's
  own liveness mutation, so the stand-down left the loop DARK (no parent, no further
  ticks) and the decided intent survived only as prose in rearm_note - nothing mechanical
  executed it, and recovery needed a fresh session the next morning. The durable-intent
  half of this gap is owned by `2026-09-21-successor-duty-primitive-absence-park-fallback.md`,
  whose re-arm park path was promoted to a first-class fix on the same day (two witnesses).
- 2026-09-21 ~16:41 (resume one-shot variant, supersedes the fresh-session confinement
  for payload-mandated creates too): the authoring-resume one-shot's payload mandated the
  parent re-arm create as its FIRST ACTION with the decision recorded state-first in the
  scheduler state file BEFORE any primitive call; the session still emitted four CronList
  calls instead of the decided create, then honored the guard stand-down (rearm_note +
  repo-matching loop-parent-missing note) without ever mutating. Same dark-loop consequence
  as the 23:53 witness, and a new detail: decision-first recording does not immunize the
  emission channel - the recorded decision survived intact (the escalation note instructed
  recovery), but no scheduled actor exists to read it while the parent is dark, so
  recovery again waited on an interactive touch. Confirms both fix directions: a
  non-automation-primitive re-arm carrier, and treating the guard's escalation note as a
  park path a later touch session mechanically executes.
