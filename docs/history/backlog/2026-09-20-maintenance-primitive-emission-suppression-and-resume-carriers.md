# Backlog: automation-primitive action-selection loop suppresses the decided mutating emission; unattended resume carriers need env-complete launchd recipes

Status: open
Priority: medium
Workflow: backlog

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

## Witnesses

- 2026-09-19 20:45: 5x CronList, create suppressed; recovery via plans-watcher-schedule
  launchd chain (worked - the driver's own launchd bootstrap is env-complete).
- 2026-09-20 09:10: 4x CronList, create suppressed; recovery via hand-armed launchd job.
- 2026-09-20 11:00: livres20b launchd job fired and died instantly on the missing provider
  config (out.log carries the error), so the 11:00 resume silently no-op'd; detected only
  because the user prompted again at 12:00.
