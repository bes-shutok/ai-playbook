# Backlog: Implement Task template lacks long-command liveness guidance for workers

- **Filed:** 2026-11-05, execute-plan Step 1.4 boundary learn pass (second witness of the failure shape; first witnessed 2026-10-25, corpus lesson #230)
- **Status:** open
- **Priority:** high
- **Class:** fix-class
- **Origin class:** execution-run witness, repeated across runs

## Skill and step

- `~/.agents/skills/execute-plan/subagent-prompts.md`: the **Implement Task** worker template (its `## Validation Commands` section and Rules list).
- Secondarily: the orchestrating parent's worker-prompt assembly, which appends run-specific validation commands into the template.

## Observed versus expected

**Observed:** the template requires every bound validation command to pass before the worker returns, but says nothing about how a worker survives a validation command that outlasts the agent runtime's worker-inactivity window. On two witnessed runs the implement worker launched a serial hermetic test suite (tens of minutes, no parallel runner available) in the foreground and was killed by the runtime's inactivity cutoff mid-run. The 2026-11-05 pass had finished all its edits correctly but died before validating and logging, so the run paid a full relaunch including a ~40-minute suite re-run; a post-death rerun also stalled on stale fixture state and needed a process-CPU-time diagnosis plus kill-and-retry before it progressed.

**Expected:** the template (or the dispatch guidance that fills it) carries the liveness contract as worker-facing rules: launch any command expected to run longer than the inactivity window in the background writing to a log file, poll it on a cadence shorter than the window (each poll is a keep-alive), never wait silently longer than the window, append a progress entry to the execution log as each verification step completes, and treat a silent long command as a death risk per corpus lesson #230 (pre-restart record before the span, resumable spans).

## Reproduction evidence (trimmed)

- Exec run, plan execution Task 1: worker made all edits (later verified correct by a relaunch audit), ran the full wrapper suite in the foreground, produced no tool activity beyond the runtime's inactivity window, and was reaped. No execution log entry existed; the return was lost. Relaunch with a pre-restart record plus explicit background-and-poll discipline (binding "Long-suite discipline" prompt section) completed the same task with zero edits needed and both suites green.
- Corroborating corpus witness: `docs/maintenance/development_lessons.md` #230 (2026-10-25 witness: worker died inside a multi-minute full-suite run at the inactivity cutoff).

## Environment context

- Agent runtime with a worker-inactivity kill window on the order of ten minutes; test venv without a parallel-runner plugin, so the hermetic wrapper suite runs serially for tens of minutes. Repo copy and vendored runtime copy of the skill match.
- Date of witness: 2026-11-05.

## Suspected root area

The worker template encodes the corpus lesson's record-keeping half (pre-restart record line in the template's relaunch clause) but not its liveness half (background-plus-poll execution and progress logging for long silent commands). The fix is one rules-block addition to the Implement Task template (and the same sentences mirrored wherever validation commands are injected), not a workflow change.
