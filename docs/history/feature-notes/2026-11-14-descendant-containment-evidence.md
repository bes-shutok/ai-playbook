# Required-suite descendant containment evidence: reparented-grandchild repro, containment comparison, boundary

Date: 2026-11-19 (fixture execution date; plan and task dated 2026-11-14)
Worktree: the plan execution worktree of this repository for the branch named below (branch and HEAD identify it)
Branch: 2026-11-14-required-test-suite-residual, HEAD 87f4ce0beeb4f0b55287d7a4fab257588bace994
Provenance digests at fixture time:

- `scripts/run_required_test_suite.py` sha256 `611d677d93108baeb1fc8353abb3cf0358ab400615a2bad29f40bff45bfc6de6` (2446 lines)
- `scripts/test_required_test_suite.py` sha256 `d8f8f6d850bff2c9cb0e21a6544536e5d597cf2466584cc7ed4917854719c022`
- runner python: the configured test venv interpreter, quoted below as `$HOME/.agents/venvs/ai-playbook-test/bin/python3`; macOS arm64, host ps is BSD ps

Question (origin residual 2): does cleanup contain a grandchild that reparents before the cleanup snapshot? The runner's two attribution paths, the worker-side snapshot `_worker_process_groups` (line 828, lineage loop lines 854 to 861, called by `_cleanup_worker_descendants` line 911) and the coordinator-side mirror `_descendant_groups` (line 1290, lineage loop lines 1331 to 1337), both walk the live parent chain from the worker pid. A grandchild whose intermediate parent exited before the snapshot has `ppid 1` (the system initializer, launchd) and is invisible to both walks. This record reproduces that shape four ways, compares portable containment options against the transcripts, and applies the plan's pre-registered close-gap criteria.

Substitution note (applies to every quoted line in this record): the driver replaced the literal home prefix with `$HOME` in all printed values; the `cd` target in commands is shown as a placeholder naming the worktree by branch; one long ps row is quoted with its argv elided at an explicitly marked point. No other edits were made to quoted output. The raw archived report JSON copies in the run scratch carry the literal home prefix (they are raw files, not driver output); every report field quoted here comes from the driver's redacted `report=` transcript line.

## Fixture and sandbox protocol

Each scenario ran inside a fresh `mktemp -d` sandbox with explicit teardown. Fixture scripts live in the run's gitignored scratch; the durable copy of every load-bearing observation rides this record with digests.

Intermediate child (scratch `task2-fixture-intermediate.py`, sha256 `54c53eaa3ed9dff156930842a3a804d7bcb2d9b2d72100ea5d398f141972c4d1`), verbatim:

```python
import json, os, subprocess, sys
from pathlib import Path

pidfile = Path(sys.argv[1])
grandchild = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(300)"],
    start_new_session=True,
    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
identity = {
    "grandchild_pid": grandchild.pid,
    "grandchild_pgid": os.getpgid(grandchild.pid),
    "intermediate_pid": os.getpid(),
    "intermediate_pgid": os.getpgrp(),
}
with pidfile.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(identity) + "\n")
sys.exit(0)
```

The generated shard source (archived per scenario as `task2-<mode>-suite-generated.py`) makes the fixture shape hold by construction: the test spawns the intermediate, reads the grandchild identity the intermediate wrote, then asserts `ps -o ppid=` returns `1` for the grandchild before returning (baseline) or before arming the worker-hold pidfile and sleeping (cancel, sigkill). So in every scenario the intermediate has exited and the grandchild is already reparented before the worker could take any cleanup snapshot; the archived per-scenario shard source carries the assertion, and each shard passed or was cancelled/signal-killed only after arming.

Scenario driver (scratch `task2-fixture-driver.py`, sha256 `4598b777ab990e29398e1eec155dca637e637c4ce304f225520f13169160ebd5`): builds the sandbox, writes the generated suite, runs the real runner from this worktree's `scripts/` (or, for mode `direct`, a simulated worker that calls `_worker_process_groups` and `_cleanup_worker_descendants` from the real module), prints every observation, archives the generated suite and report into scratch, then tears down: SIGKILL to every recorded grandchild pgid, defensive SIGKILL to recorded intermediate pids, verification ps rows, sandbox removal. Runner invocation per scenario (mode substituted; `cd` target is the worktree root for the branch named above):

```bash
cd <worktree root for branch 2026-11-14-required-test-suite-residual> && SCRATCH=docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch && "$HOME/.agents/venvs/ai-playbook-test/bin/python3" "$SCRATCH/task2-fixture-driver.py" <mode> scripts "$SCRATCH" > "$SCRATCH/task2-<mode>-transcript.txt" 2>&1
```

Runner argv in every runner scenario (from the transcripts, `$HOME`-redacted): `[<venv python>, "scripts/run_required_test_suite.py", "--repo-root", "<mktemp repo>", "--suite", "test_repro.py", "--workers", "1", "--per-script-timeout", "<15 baseline | 25 cancel/sigkill>", "--suite-timeout", "<40 baseline | 35 cancel/sigkill>", "--cleanup-grace", "1.0", "--json-report", "<mktemp report>"]`.

## Transcript 1: baseline, worker completes normally

Driver exit 0. Runner exit 0, status `passed`, stderr empty. Runner stdout verbatim:

```text
{"collected": 1, "duration": 0.4902843750023749, "executed": 1, "report": "/var/folders/bt/zqtn178979vgplbd70bv1cg00000gp/T/tmp.mwQ9kLQhAy/report.json", "status": "passed", "suite_count": 1}
```

Report completeness (from the redacted `report=` line; full report archived, digest below): `report_complete: true`, `schema_version: 1`, suite outcome `passed`, shard outcome `passed`, `returncode: 0`, no `cleanup_error` field anywhere, `max_active_children: 1`.

Probe window after runner exit, verbatim:

```text
probe_window grandchild_pid=50343: 50343     1 50343 Ss   /opt/homebrew/Cellar/python@3.14/3.14.10/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python -c import time; time.sleep(300)
```

Observed outcome: the runner exited 0 with `status: "passed"` while the grandchild stayed live, reparented to the system initializer (`ppid 1`), in its own session and process group (`pgid == pid`, state `Ss`). No group was ever attributed or terminated; no cleanup error or snapshot warning was surfaced; the leak is silent on the success path.

Evidence-quality note: the same report's scheduling evidence carries `child_effects: ["child process groups are captured, terminated and reaped by the runner"]`. That claim holds only for groups visible in the snapshot-time parent chain; this transcript is the counterexample for the pre-reparented shape.

## Transcript 2: direct probe of the worker-side snapshot (no group returned)

Driver mode `direct` (no runner; a simulated worker process runs the fixture, then calls the real functions from this worktree's runner module). Worker-sim stdout verbatim:

```text
fixture_reparented=True
worker_process_groups_result=[] error=None
cleanup_worker_descendants_result=None
grandchild_after_cleanup_rc=0 50373     1 50373 Ss
```

Observed outcome, verbatim from the plan's expected shape: no group returned (`worker_process_groups_result=[] error=None`); `_cleanup_worker_descendants(1.0)` returned `None`, a vacuous success, because the empty snapshot leaves nothing to terminate or verify; the grandchild was still live immediately after cleanup (`ppid 1`, own pgid, state `Ss`). This is the worker-side blind spot demonstrated against today's `_worker_process_groups` code.

## Transcript 3: cancellation while the worker owns the detached grandchild

Precondition evidence: worker 50409 armed in its own group (worker row, argv elided after the script path for length; the elided argv is the runner module's `--_worker run` command as in the runner_argv line above):

```text
worker_before_signal: 50409 50401 50409 Ss   <python> $HOME/.../scripts/run_required_test_suite.py ...[argv elided]... --_policy pytest --_cleanup-grace 1.0 --_test-ids ["scripts/test_repro.py::test_reparented_grandchild"]
pre_signal grandchild_pid=50411: 50411     1 50411 Ss   <python> -c import time; time.sleep(300)
```

The grandchild was already reparented (`ppid 1`) before the signal. Driver sent `SIGTERM` to the runner coordinator pid 50401. Runner stdout verbatim:

```text
{"collected": 0, "duration": 1.0754216669884045, "executed": 0, "report": "/var/folders/bt/zqtn178979vgplbd70bv1cg00000gp/T/tmp.I0qBlczSD1/report.json", "status": "cancelled", "suite_count": 1}
```

Report completeness: `status: "cancelled"`, `cancellation_reason: "signal"`, `report_complete: true`, shard outcome `cancelled`, shard `returncode: -15` (the coordinator's cancellation path terminated the worker's own captured group), runner exit 1, stderr empty (no snapshot warning: the coordinator-side snapshot succeeded and still found nothing beyond the worker's own group).

Probe window after runner exit, verbatim:

```text
probe_window grandchild_pid=50411: 50411     1 50411 Ss   /opt/homebrew/Cellar/python@3.14/3.14.10/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python -c import time; time.sleep(300)
```

Attribution/termination outcome, verbatim: the grandchild's group was NOT attributed and NOT terminated. The coordinator-side `_descendant_groups` walk (line 1290) ran on this cancellation path (line 1480, `capture_descendants=True`) and returned only the worker's own group, because the grandchild's live parent chain no longer reaches the worker.

## Transcript 4: external SIGKILL of the worker

Precondition evidence: worker 51399 armed in its own group, grandchild 51420 already reparented (`ppid 1`), same row shapes as transcript 3 (rows archived verbatim in the transcript, digest below). Driver sent `SIGKILL` to worker pid 51399. Verbatim:

```text
sending SIGKILL to worker pid=51399
worker_after_signal: (no ps row; rc=1 stderr='')
{"collected": 0, "duration": 1.010072416975163, "executed": 0, "report": "/var/folders/bt/zqtn178979vgplbd70bv1cg00000gp/T/tmp.6zGs38czFY/report.json", "status": "failed", "suite_count": 1}
```

Report completeness: `status: "failed"`, `report_complete: true`, suite and shard outcome `accounting_error`, shard `returncode: -9`, runner exit 1, stderr empty. Probe window after runner exit, verbatim:

```text
probe_window grandchild_pid=51420: 51420     1 51420 Ss   /opt/homebrew/Cellar/python@3.14/3.14.10/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python -c import time; time.sleep(300)
```

Containment outcome, verbatim: no containment and no attribution. The worker died on SIGKILL without running any cleanup (no worker-side path can run after SIGKILL); the coordinator's completed-communicate branch (line 1467) calls `_cleanup_process` without `capture_descendants`, so no descendant walk ran on this path at all; the grandchild survived. Unlike the baseline, the failure was surfaced (exit 1, `accounting_error`, `returncode: -9`), but the detached grandchild leaked silently.

Teardown witness for all four scenarios: the driver SIGKILLed every recorded grandchild pgid (baseline 50343, direct 50373, cancel 50411, sigkill 51420) and every teardown-verify ps row returned no row; recorded intermediates were already gone; each sandbox was removed (`exists=False` printed per scenario).

## Containment options compared against the transcripts

Host fact observed 2026-11-19: `ps -axo pid=,ppid=,pgid=,sid=` fails on macOS with `ps: sid: keyword not found` (row form `ps -o ... sid= -p <pid>` exits 1 with the same message); the shipped `pid=,ppid=,pgid=` row set is the portable common denominator.

| Candidate | Sketch | macOS compatible | CI-representable primitives | Deterministic vs the pinned fixture | Kill-set bounded to attributed groups | Lands inside Task 2's frozen scope | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Live parent-chain walk (shipped) | BFS over `ps` pid/ppid/pgid rows from the worker pid | yes | yes | no: attributes nothing for the pre-reparented grandchild (transcripts 1 to 4) | yes | shipped | retained; it defines the boundary |
| Snapshot-time session bookkeeping | worker-side poller thread samples the tree from shard start; cleanup terminates the union of observed pgids | yes | yes | no: the pinned intermediate exits immediately after the setsid launch, so polls can miss the parented window entirely; no lower bound exists | yes | no: the monitor must start around shard execution in frozen `_worker_main`/shard paths | rejected: nondeterministic for exactly the pinned shape, and out of scope |
| PGID inheritance mapping | terminate attributed ancestor groups; non-setsid descendants stay in them | yes | yes | no: cannot see a setsid escape by construction; covers only children that never left the ancestor group | yes | shipped | retained as today's real coverage; does not close this gap |
| Session-ID attribution walk | walk parent and session relations via `ps -o sid` | no: `sid` keyword absent from macOS ps (observed above) | yes on Linux procps only | no: the setsid grandchild's session is its own, unrelated to the worker's; the sid-sharing intermediate is gone | yes | n/a | rejected: not expressible on macOS, and no causal link remains even where expressible |
| Recently-orphaned heuristic | kill ppid-1 session leaders whose start time falls inside the run window | yes (`lstart`) | yes | probably yes | no: any unrelated launchd child started during the run matches; kill-set grows over unattributed groups | yes | rejected: violates the bounded-termination criterion |
| Launch-time registration | shard execution registers each spawned descendant's pid/pgid at spawn; cleanup extends the kill set with registrations | yes | yes | yes for Python-level spawns | yes | no: patch/wrapper layer inside frozen shard execution paths; collides with the standing no-persistent-wrapper constraint | rejected here; the only deterministic route, viable only as a separate witnessed proposal |
| Platform-specific primitives | Linux pidfd; macOS/BSD kqueue `EVFILT_PROC` exit notifications | pidfd: no / kqueue: yes | splits by platform, one CI class always uncovered | yes per platform | yes | no | rejected: pre-registered portability criterion |

## Decision per the pre-registered criteria

Criteria result, evaluated one by one:

1. Mechanism attributes AND terminates the reparented grandchild: no candidate does so deterministically. The two bookkeeping-style candidates either miss the pinned shape (snapshot-time polling, option 2) or need a spawn-time registration layer (option 6) that cannot land in this task's scope.
2. Focused runner contract suite stays green: trivially satisfiable (no code change lands); verified below.
3. CI-representable primitives: options 2 and 6 qualify, but each fails another criterion.
4. No gate, lock, or persistent wrapper: option 6 requires a spawn-interception wrapper layer; standing constraints bar it, and the machinery admission protocol would own any revival.
5. Termination scope bounded to attributed descendant groups: option 5 grows the kill set over unattributed groups; rejected.

Which attribution path or paths the mechanism fixes: none land, so zero paths are fixed. The blind spot is shared by both attribution paths: the worker-side snapshot `_worker_process_groups` under `_cleanup_worker_descendants` (line 828 under line 911, lineage loop 854 to 861) and the coordinator-side mirror `_descendant_groups` (line 1290, lineage loop 1331 to 1337); both walk live parent chains at snapshot time. Transcript 2 demonstrates the worker-side miss on the direct function call; transcript 3 demonstrates the coordinator-side miss on the cancellation path; transcript 4 shows the externally-killed-worker path where neither walk runs (line 1467 passes no `capture_descendants`); transcript 1 shows the silent end-to-end leak with exit 0.

## Supported child-lifecycle boundary (document-boundary branch)

Supported, as recorded: cleanup covers detached children and grandchildren whose lineage is still visible in the snapshot-time parent chain. A worker that launches a child in its own process group or session is contained on every exit path (worker-side snapshot on normal shard completion; coordinator-side snapshot with `capture_descendants=True` on timeout and cancellation paths), and any descendant that still has a live ancestor chain back to the worker at snapshot time is attributed through that chain and terminated. Existing focused-suite coverage pins exactly this boundary (`test_successful_child_exit_reaps_detached_descendant`, `test_child_timeout_kills_a_term_ignoring_new_session_descendant`, `test_worker_exception_still_cleans_detached_child`).

Out of the supported boundary: a grandchild whose intermediate parent exits before the cleanup snapshot. It reparents to the system initializer (`ppid 1` observed in all four transcripts), carries no portable, queryable link to the worker, and survives every cleanup path exercised here: normal completion (runner exit 0, status `passed`, silent leak), cancellation (worker's own group reaped, grandchild live), and external SIGKILL of the worker (no cleanup runs at all). Re-derivation from this record alone: rebuild the intermediate and generated suite from the archived scratch copies, run the driver command above with mode `baseline`, and expect the same three observations (empty snapshot result, vacuous cleanup success, live ppid-1 grandchild in the probe window).

Severity asymmetry worth keeping: on the success path the leak is silent (exit 0, no cleanup error); on cancellation and SIGKILL paths the run itself fails visibly (exit 1), but the reparented grandchild still leaks in both.

## Follow-up candidate disposition

The only deterministic portable mechanism identified is launch-time registration (option 6). It is recorded here as a rejected disposition, not promoted, because landing it requires a spawn-interception wrapper in shard execution and an unfreeze of `_worker_main`/shard-runner paths, both barred by this plan's standing constraints (no persistent tool wrapper; frozen scope) and owned by the machinery admission protocol as a separate witnessed proposal. Revival is an operator decision; this record is the routing artifact, and no backlog row is filed from this task (out of this task's file scope).

## Scratch artifacts (gitignored run scratch, `docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch/`)

- `task2-fixture-driver.py` sha256 `4598b777ab990e29398e1eec155dca637e637c4ce304f225520f13169160ebd5`
- `task2-fixture-intermediate.py` sha256 `54c53eaa3ed9dff156930842a3a804d7bcb2d9b2d72100ea5d398f141972c4d1`
- baseline: `task2-baseline-transcript.txt` sha256 `8306e25183b37793e27e6943630998d0b7b12bec628c352774f70a14e53cfd36`, `task2-baseline-report.json` sha256 `eec012efbb2ddacf08bdd5e87a805c96bc5d27fcf9e8b31afa703328970c0a21`, `task2-baseline-suite-generated.py` sha256 `52ed1fb6492fdb11ed6ffcf5d3b11b40d6da05848a92042b11262719c9f593f9`
- direct: `task2-direct-transcript.txt` sha256 `8f8198abfcb08bde7ac496431542d70a15e7dabee9761fbd3fe638a6f0b172a4`, `task2-direct-report-absent.note` sha256 `2458d6bd7ba6f4b97ab703fda6a210c314ec3cc4641b0c690637bb7ebee46943`
- cancel: `task2-cancel-transcript.txt` sha256 `3e01c33a787dd71f0a26de66182c594b2f1d3dc1e8ae9badd6ccdc572d5aa7e8`, `task2-cancel-report.json` sha256 `81e50e2d5c04e2e04bbb87625d43be44fc463b64f9c9d2a041b3a71a521d07d2`, `task2-cancel-suite-generated.py` sha256 `5e60069a46555d0072cf98e73e56b578ff791cc6e7bc4e7a707b192cbf51fe81`
- sigkill: `task2-sigkill-transcript.txt` sha256 `19432589a062e96550e69422ec4a3cb31e4cda7af67642833c5d5d132ef52603`, `task2-sigkill-report.json` sha256 `dccfb173b92f2ff48e78217c52ef96615dd9b14af537f1d99596e0478798d833`, `task2-sigkill-suite-generated.py` sha256 `b06b3b81ac63466deaa63940bd346295dbf81a3a5332462a7cb3deafa3b7d89a`

Post-fixture validation: focused runner contract suite run unchanged, `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_required_test_suite.py -q` from the worktree root: 39 passed, 8 subtests passed in 22.26s. No runner or test file was edited for this task (document-boundary branch), so `git status` over tracked files stays clean except this record.

## Disposition

Branch taken: document-boundary. The pre-registered close-gap criteria were applied to seven candidate mechanisms scored against four recorded transcripts; no candidate attributes and terminates the pre-reparented grandchild deterministically while staying inside the frozen descendant-snapshot scope, using CI-representable primitives, adding no wrapper machinery, and keeping the kill set bounded to attributed groups. The supported child-lifecycle boundary is stated above with the repro transcripts as evidence; the worker-side and coordinator-side attribution paths share the blind spot and both retain their current live-parent-chain semantics unchanged. The viable deterministic route (launch-time registration) is recorded as a rejected candidate with its ruling constraints; no defect claim is filed against the existing cleanup paths for the shapes they do cover, and the cancellation/SIGKILL records of Task 1 compose with this boundary: cancellation containment holds for snapshot-time-visible groups only.
