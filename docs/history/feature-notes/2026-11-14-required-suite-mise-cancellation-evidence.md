# Required-suite mise cancellation evidence and boundary

Date: 2026-11-19 (probe execution date; plan and task dated 2026-11-14)
Worktree: the plan execution worktree of this repository for the branch named below (branch and HEAD identify it)
Branch: 2026-11-14-required-test-suite-residual, HEAD 4a997083b26598abe73a19c485907c8653e03797
Provenance digests at probe time:

- `scripts/run_required_test_suite.py` sha256 `611d677d93108baeb1fc8353abb3cf0358ab400615a2bad29f40bff45bfc6de6` (2446 lines)
- `mise.toml` sha256 `3f007d5717f98d3d831192883671a551c867fc56b4d123e20d5f2888c1c714fd`
- mise 2026.11.10 macos-arm64; runner python from the mise env: `$HOME/.agents/venvs/ai-playbook-test/bin/python3`

Both probes answer one question with two interruption paths: when cancellation arrives through `mise run test:required`, what signal the runner received, whether captured descendant groups were reaped, whether the JSON report completed, and what exit code propagated. Each probe is evidence capture with second-scale overrides, not an acceptance run (focused-never-full policy holds: the probes reuse the mise task as mandated by the plan, with `--suite-timeout 10` bounding the run to seconds).

## Probe 1: internal suite-timeout cancellation

Command (from the worktree root):

```bash
mise run test:required --suite-timeout 10 --json-report docs/tmp/rts-mise-cancel-probe-report.json
```

Precondition (overrides ride through): the `test:required` task has `raw_args = true`, so mise appends the extra flags after its fixed command line. The probe transcript's first line shows the appended flags verbatim:

```text
[test:required] $ python3 scripts/run_required_test_suite.py --workers 8 --per-script-timeout 60 --suite-timeout 270 --json-report docs/tmp/test-suite-fast-feedback-runner-report.json --suite-timeout 10 --json-report docs/tmp/rts-mise-cancel-probe-report.json
```

Argparse last-wins applied: the report landed at the probe path (297747 bytes) and the task-default path `docs/tmp/test-suite-fast-feedback-runner-report.json` was never created (verified absent). The precondition holds; evidence capture proceeded.

Observed behavior: no OS signal was involved. The runner's internal deadline (`suite_timeout` 10s minus the 0.5s report reserve) set `cancel_reason` to `timeout` at about T+9.5s; workers were cancelled, captured groups reaped, and the report written. Full transcript after the echoed command line:

```text
{"collected": 33, "duration": 9.779689125018194, "executed": 33, "report": "docs/tmp/rts-mise-cancel-probe-report.json", "status": "timeout", "suite_count": 97}
[test:required] ERROR task failed
MISE_EXIT_STATUS=1
```

Report completeness at the probe path (all fields present):

- `status: "timeout"`, `cancellation_reason: "timeout"`, `report_complete: true`, `schema_version: 1`, `partial: true`
- inventory: 97 entries; `suite_count: 97`; suite outcomes: 2 `passed`, 95 `timeout`
- `workers: 8`, `max_active_children: 8`, `per_script_timeout: 60.0`, `cleanup_grace: 2.0`
- `started_at 1795125883.400293`, `ended_at 1795125893.167723` (9.77s wall)
- zero cleanup/snapshot warnings in any suite stderr (the runner appends `process-tree snapshot ... may remain` notes there when a snapshot fails; none appeared)

Non-vacuousness: a concurrent `ps -axo pid=,ppid=,pgid=,command=` sampler (0.4s cadence, 40 samples) observed eight worker processes before cancellation, all children of the runner coordinator pid 49145: collection workers pids 49221 and 49228, run workers pids 49248, 49249, 49250, 49253, 49256, 49259. Seven of the eight were sampled in their own process group (`pgid == pid`, consistent with the runner's `start_new_session=True` spawns); worker 49259 appeared once with `pgid 49145`, the coordinator's group, so that sample caught it outside its own group at that instant. The post-exit leak check covered every observed pgid, including both 49145 and 49259's own group, and found no survivors, so the cleanup conclusion is unchanged. The report's own accounting agrees (`max_active_children: 8`).

Cleanup evidence: the actively running suite `scripts/test_base_reflog_audit.py` carries shard record `shard: test_base_reflog_audit.BaseReflogAuditTest, outcome: timeout, returncode: -15`, showing the cleanup path delivered SIGTERM to the worker's captured process group. Post-exit leak scans found no live process with the worktree path in its argv and no live process in any observed worker pgid set (49145, 49221, 49228, 49248, 49249, 49250, 49253, 49256, 49259).

Exit status verbatim: `MISE_EXIT_STATUS=1` (mise propagates the runner's exit 1 because report status `timeout` is not `passed`).

## Probe 2: external SIGTERM into the running mise process tree

Same command shape, relaunched with mise as the direct background job of the probe call, so the mise pid is known without any process-listing detection (`$!` in the launching shell). After a fixed 5-second sleep, once child workers were observably active (probe 1's timeline and the report's own `max_active_children` accounting both show workers live from about T+1s), the probe sent SIGTERM from outside. Exact launch-and-signal one-liner, verbatim except the leading `cd` target, kept as a placeholder so no personal absolute path enters this record (the target is the worktree root identified above):

```bash
cd <worktree root for branch 2026-11-14-required-test-suite-residual> && SCRATCH=docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch && LOG="$SCRATCH/probe2-attempt5-kill-log.txt" && : > "$LOG" && mise run test:required --suite-timeout 10 --json-report docs/tmp/rts-mise-cancel-probe-report.json > "$SCRATCH/probe2-attempt5-transcript.txt" 2>&1 & MPID=$! && echo "probe_bg_pid=$MPID launched_at=$(date +%H:%M:%S.%N)" >> "$LOG" && sleep 5 && MCMD=$(ps -p "$MPID" -o command=) && echo "SIGTERM_SENT_TO_MISE pid=$MPID cmd=$MCMD at $(date +%H:%M:%S.%N)" >> "$LOG" && kill -TERM "$MPID" && wait "$MPID"; KRC=$?; echo "MISE_EXIT_STATUS_AFTER_SIGTERM=$KRC at $(date +%H:%M:%S.%N)" >> "$LOG"; echo "MISE_EXIT_STATUS=$KRC" >> "$SCRATCH/probe2-attempt5-transcript.txt"; for i in 1 2 3 4 5 6 7 8; do echo "== aftermath $i $(date +%H:%M:%S.%N) ==" >> "$LOG"; ps -axo pid=,ppid=,pgid=,stat=,command= | LC_ALL=C /usr/bin/grep -E "run_required_test_suite|test:required" | LC_ALL=C /usr/bin/grep -v "grep -E" >> "$LOG" || true; sleep 0.4; done; echo "AFTERMATH_DONE" >> "$LOG"; echo "wrapper_done"
```

Kill log verbatim:

```text
probe_bg_pid=91151 launched_at=22:20:14.411011000
SIGTERM_SENT_TO_MISE pid=91151 cmd=mise run test:required --suite-timeout 10 --json-report docs/tmp/rts-mise-cancel-probe-report.json at 22:20:19.426052000
MISE_EXIT_STATUS_AFTER_SIGTERM=1 at 22:20:21.364520000
```

Which process received the signal: the `mise` CLI process itself, pid 91151, command line `mise run test:required --suite-timeout 10 --json-report docs/tmp/rts-mise-cancel-probe-report.json`, at T+5.015s after launch.

What the runner did: mise did not die on the signal; it surfaced the signal to its task and waited for the child. The runner's installed SIGTERM handler (asyncio signal handler, `cancel_reason = "signal"`) fired: workers were cancelled through the cleanup path (capture descendant groups, SIGTERM each, bounded wait within `cleanup_grace` 2.0s, SIGKILL survivors), and the runner completed its exit sequence about 1.93s after the signal. Transcript verbatim (signal landed at runner T+4.78s; runner exited at runner T+6.71s):

```text
{"collected": 0, "duration": 6.707347209012369, "executed": 0, "report": "docs/tmp/rts-mise-cancel-probe-report.json", "status": "cancelled", "suite_count": 97}
[test:required] ERROR task failed
MISE_EXIT_STATUS=1
```

Report state: a report was written, once, at exit, at the probe path (117376 bytes). Completeness: `status: "cancelled"`, `cancellation_reason: "signal"`, `report_complete: true`, `schema_version: 1`, `partial: true`, inventory 97 entries, all 97 suites carry `outcome: "cancelled"`, `workers: 8`, `max_active_children: 8`, zero cleanup/snapshot warnings. `collected: 0, executed: 0` is consistent with the timing: at T+4.8s every suite was still inside its collection or first shard, and the cancellation recorded all of them as cancelled.

Cleanup evidence: the runner's own accounting shows the eight live worker children were captured and reaped inside the cleanup window (exit about 1.93s after the signal, within `cleanup_grace` 2.0s), with zero snapshot warnings. Post-exit leak scans, repeated 3 seconds apart, found no live process with the worktree path in its argv and no process with the probe report path in its argv; the eight 0.4s aftermath samples taken after `wait` returned saw no probe processes either.

Exit status verbatim: `MISE_EXIT_STATUS_AFTER_SIGTERM=1` recorded 1.94s after the signal; the transcript's `MISE_EXIT_STATUS=1` agrees. Not 143: mise itself was not killed by the signal; it propagated the cancelled task's exit 1.

## Safety witness (leaked descendant groups)

No descendant process group from either probe survived the runner's exit. Evidence: the per-probe argv scans named above (worktree path and probe path as the search keys, repeated over several seconds after each run) returned empty, and probe 1 additionally checked every observed worker pgid individually. One defunct process exists on the host, `pid 24656, ppid 24648, stat Z+ (<defunct>)`, started 2026-11-16 13:49:45, child of `.../@openai/codex-darwin-arm64/.../bin/codex` (pid 24648): it predates the probes by three days and is unrelated to the runner. Repro command for any future leak check: `ps -axo pid=,ppid=,pgid=,stat=,command= | grep worktrees/exec/2026-11-14-required-test-suite-residual` plus `pgrep -f rts-mise-cancel-probe`.

## Probe execution notes (attempts 1 through 4, kept for re-derivation)

The signal probe took five attempts; the first four aborted the kill before signaling and each run then reached its natural internal timeout, producing a fourth and fifth natural-cancellation observation. Their artifacts (transcripts, process samples, reports) are archived in the run scratch with digests. Three environment findings worth keeping:

- A concurrent foreign `mise run test:required` from another worktree (`ai-playbook-worktrees/2026-11-19-maintenance-foreign-idle-child-outcome`, plain args) was live during attempt 2, and its processes appeared in samples alongside the probe's. Any external kill targeting "the mise process tree" on this host needs guards keyed to probe-unique argv (the probe report path worked here); the attempt-2 abort guard (which additionally required a `worktrees` substring the probe's own coordinator does not carry, because mise runs the task with a relative script path) is what prevented signaling the foreign session's run.
- The session's `grep` command is a ugrep wrapper carrying `-I` (skip binary input) that silently drops `ps` output containing non-text bytes, and misparses dash-leading patterns as options; deterministic process scanning on this host needs `/usr/bin/grep` (BSD grep) with `-e` for dash-leading patterns.
- Process-listing visibility of the background probe's processes proved intermittent across attempts (full in probe 1 and attempt 2, partial in attempt 3, first-samples-only in attempt 4 despite the run spanning 9.6s). The attempt-5 design removed the dependency: launch mise as the probe call's own background job (`$!` gives the pid) and signal on a fixed delay instead of on detection.

One artifact note: attempt 2's report file was overwritten by attempt 3 before archiving; its transcript and process samples are preserved, and its report carried the same natural-timeout shape (`collected: 2, executed: 2, status: "timeout"`).

## Scratch artifacts (gitignored run scratch, `docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch/`)

- `probe1-report.json` (from the probe path after verification) sha256 `3af159520142090aa31c6677d214f53f5d650f9abdee7ada687c69523554e050`, plus `probe1-transcript.txt`, `probe1-process-samples.txt`
- `probe2-attempt5-report.json` sha256 `bfdfefd8a956b86bfb9f354d8c3f4587c1320b34067684f8595adf9200399c63`, plus `probe2-attempt5-transcript.txt`, `probe2-attempt5-kill-log.txt`
- natural-timeout duplicates from aborted attempts: `probe2-attempt1-report.json` sha256 `aaea18a1646a730744b830ffe4e984fd4fc3a19467635bd7c4265a5366b6930c`, `probe2-attempt3-report.json` sha256 `f6659284425702707c6ebdc331740d54e4349e3e2132dcdacc67c8985032af62`, `probe2-attempt4-report.json` sha256 `5bdf84fb5aad93a0319816337570e2bb3300d39039218d2c0621a212859c72cb`, each with its transcript and sample log; attempt 2 has transcript and samples only (see artifact note above)

## Disposition

Supported cancellation boundary, as recorded:

- Verified end to end: cancellation through mise with second-scale overrides works on both exercised paths. (1) Internal deadline cancellation: at `suite_timeout` 10 the runner cancels workers, reaps captured descendant groups (SIGTERM, bounded grace, SIGKILL survivors; observed as shard `returncode: -15` and zero snapshot warnings), writes a complete `schema_version` 1 JSON report at the overridden path with `cancellation_reason: "timeout"`, and exits 1; mise prints `ERROR task failed` and propagates exit 1. (2) External SIGTERM delivered to the mise process mid-run with workers active: the runner's handler converts it to `cancel_reason: "signal"`, the same cleanup path reaps the captured groups within the 2.0s cleanup grace, a complete report with `cancellation_reason: "signal"` is written once at exit, and mise propagates exit 1 about 1.9s after the signal.
- Not exercised here and therefore outside this record's boundary: the SIGINT path through mise (only SIGTERM was sent); external SIGKILL of the runner or of a worker (Task 2's externally-killed-worker scope); reparented-grandchild attribution after a worker's death (Task 2's scope); interaction with mise's own outer 295s task timeout (the probes finished in 7 to 12 seconds, far under it); host-level process-observation reliability (ps visibility proved intermittent in this session, so cleanup conclusions rest on the runner's report accounting, shard returncodes, and post-exit argv scans rather than on continuous external observation).
- No defect finding: five natural-timeout cancellations and one mid-run SIGTERM all produced complete reports, nonzero exit statuses, and no leaked descendant groups.

Disposition: supported-as-recorded. The record above is the durable answer to the origin's cancellation question; no follow-up row is filed.
