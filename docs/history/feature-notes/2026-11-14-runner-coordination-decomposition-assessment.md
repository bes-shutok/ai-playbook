# Required-suite runner decomposition assessment: responsibility inventory, shared-state coupling, disposition

Date: 2026-11-19 (assessment date; plan and task dated 2026-11-14)
Worktree: the plan execution worktree of this repository for the branch named below (branch and HEAD identify it)
Branch: 2026-11-14-required-test-suite-residual, HEAD 284d32978 (Task 3 commit on top of Task 2 0b697693f and Task 1 87f4ce0be)
Assessment target: `scripts/run_required_test_suite.py`, class `RequiredTestSuiteRunner`; read-only in this task, no runner edits, no refactor landed

Origin question (backlog row `docs/history/backlog/2026-11-09-required-test-suite-five-minute-residual.md`, section "Maintainability follow-up (non-acceptance)", verbatim): "`RequiredTestSuiteRunner` concentrates discovery, scheduling, deadlines, process cleanup, test accounting and reporting in a 940-line class with 28 methods. Assess whether cohesive components can reduce that coupling." The origin pins two bars: do not claim a timing improvement without a measured comparison, and do not refactor merely to satisfy the finding if extraction would split shared state poorly. This record re-derives the current shape with provenance, inventories the responsibilities and the shared state each reads or mutates, and closes with a verdict and disposition.

## Re-derived current shape with provenance

Commands run in the worktree root (2026-11-19, clean tree, Tasks 1-3 committed):

```bash
shasum -a 256 scripts/run_required_test_suite.py
wc -l scripts/run_required_test_suite.py
git log -1 --format="%cs %h %s" -- scripts/run_required_test_suite.py
git log -1 --format=%H
```

Observed outputs verbatim:

```text
611d677d93108baeb1fc8353abb3cf0358ab400615a2bad29f40bff45bfc6de6  scripts/run_required_test_suite.py
    2446 scripts/run_required_test_suite.py
2026-11-11 8b40552ff test: add required suite runner and timing results
284d32978c2fea5665b9f859cf1a76558e1d97c2
```

Class span and method inventory were derived with the Python `ast` module (command quoted in full so the reader can re-derive):

```bash
python3 -c "
import ast
src = open('scripts/run_required_test_suite.py').read()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == 'RequiredTestSuiteRunner':
        start, end = node.lineno, node.end_lineno
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        nested = []
        for m in methods:
            for sub in ast.walk(m):
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub is not m:
                    nested.append((m.name, sub.name, sub.lineno))
        print('class start/end:', start, end)
        print('class line span (inclusive):', end - start + 1)
        print('top-level methods:', len(methods))
        print('nested defs:', nested)
        print('method names:')
        for m in methods:
            kind = 'async def' if isinstance(m, ast.AsyncFunctionDef) else 'def'
            print(f'  {m.lineno:5d} {kind:9s} {m.name} (ends {m.end_lineno}, {m.end_lineno - m.lineno + 1} lines)')
"
```

Observed output verbatim:

```text
class start/end: 1175 2121
class line span (inclusive): 947
top-level methods: 28
nested defs: [('_run_shard_queue', 'consume', 1630)]
method names:
   1178 def       __init__ (ends 1209, 32 lines)
   1212 def       _configured_python (ends 1227, 16 lines)
   1229 def       _child_env (ends 1240, 12 lines)
   1242 def       _inventory (ends 1245, 4 lines)
   1247 def       _selected (ends 1268, 22 lines)
   1270 def       _git_revision (ends 1278, 9 lines)
   1280 async def _signal_group (ends 1288, 9 lines)
   1290 async def _descendant_groups (ends 1340, 51 lines)
   1343 def       _process_group_exists (ends 1352, 10 lines)
   1354 async def _cleanup_process (ends 1425, 72 lines)
   1427 async def _run_process (ends 1490, 64 lines)
   1493 def       _parse_marker (ends 1500, 8 lines)
   1502 async def _worker (ends 1513, 12 lines)
   1515 def       _shard_record (ends 1571, 57 lines)
   1573 async def _run_shard (ends 1606, 34 lines)
   1608 def       _exception_shard_record (ends 1617, 10 lines)
   1619 async def _run_shard_queue (ends 1659, 41 lines)
   1661 async def _run_suite (ends 1863, 203 lines)
   1865 def       _cancelled_shard (ends 1879, 15 lines)
   1881 def       _cancelled_suite (ends 1891, 11 lines)
   1894 def       _elapsed_seconds (ends 1912, 19 lines)
   1914 def       _process_snapshot (ends 1982, 69 lines)
   1984 async def _process_context_monitor (ends 1987, 4 lines)
   1989 async def _cancel_after_deadline (ends 1995, 7 lines)
   1997 async def run_async (ends 2099, 103 lines)
   2101 def       _receive_signal (ends 2105, 5 lines)
   2107 def       write_report (ends 2118, 12 lines)
   2120 def       run (ends 2121, 2 lines)
```

Shape beside the origin's figures:

| Figure | Origin (2026-11-09 authoring) | This assessment (2026-11-19) | Delta |
| --- | --- | --- | --- |
| Class line span | ~940 | 947 (lines 1175 to 2121 inclusive) | +7 |
| Top-level methods | 28 | 28 | 0 |
| Nested defs | not recorded | 1 (`consume` inside `_run_shard_queue`, line 1630) | n/a |
| File total lines | not recorded | 2446 (class is 38.7 percent) | n/a |
| Source sha256 | not recorded (wrapper source digest recorded instead) | `611d677d93108baeb1fc8353abb3cf0358ab400615a2bad29f40bff45bfc6de6` | n/a |
| Last runner commit | n/a | 2026-11-11 `8b40552ff` (predates this plan; Tasks 1-3 did not touch the runner) | n/a |

The origin's structure figures reproduce almost exactly: the class is unchanged in method count and grew 7 lines since the finding was written. Line count alone, however, is not the coupling evidence the plan asks for; the inventory below is.

## Responsibility inventory and shared-state map

The five responsibilities the origin names: discovery, scheduling gate, worker lifecycle and cleanup, accounting, reporting. Method membership, module-level support, and the instance state each responsibility reads or mutates:

| Responsibility | Class methods (line of def) | Module-level support already outside the class | Instance state read | Instance state mutated |
| --- | --- | --- | --- | --- |
| Discovery (inventory, suite selection) | `_inventory` (1242), `_selected` (1247) | `_inventory` (50), `_inventory_digest` (62), `_module_name` (68), `_module_from_path` (72), `_flatten` (84), `_unittest_collection` (94), `_policy` (682), `_pytest_collection` (717), `_load_unittest_tests` (725) | `root`, `focused_suites` | none (pure reads; returns values) |
| Scheduling gate and admission | `_run_suite` admission half (suite semaphore acquire, gate acquire/release, shard-worker reservation, lines 1667 to 1671 and the `finally` at 1857 to 1863), `_run_shard_queue` bounded pool (1619), `_cancel_after_deadline` (1989), `_receive_signal` (2101) | `_SchedulingGate` (1123, already a separate class), `_scheduling_class` (1008), `_safe_first_schedule` (1053), `_source_shards` (1073) | `cancelled`, `cancel_reason`, `global_deadline`, `report_reserve`, `workers`, `per_script_timeout`, `suite_timeout` | `gate` (its `active_read`/`active_serial`/`waiting_serial`), `suite_semaphore`, `cancelled`, `cancel_reason`, `start_monotonic`, `global_deadline` (bootstrap writes in `run_async`) |
| Worker lifecycle and cleanup | `_configured_python` (1212), `_child_env` (1229), `_worker` (1502), `_run_process` (1427), `_cleanup_process` (1354), `_signal_group` (1280), `_descendant_groups` (1290), `_process_group_exists` (1343), `_parse_marker` (1493) | `_worker_main` (962), `_worker_process_groups` (828), `_live_process_groups` (865), `_cleanup_worker_descendants` (911), `_ProcessResult` (1165), `_CountingResult` (730), `_run_unittest_shard` (772), `_run_pytest_shard` (806), `_pytest_main` (672) | `cancelled`, `cancel_reason`, `semaphore`, `cleanup_grace`, `python_executable`, `venv_bin`, `root` | `processes` registry (add on spawn, pop in `finally`), `max_active_children` peak |
| Accounting | `_shard_record` (1515), `_run_shard` (1573), `_exception_shard_record` (1608), `_cancelled_shard` (1865), `_cancelled_suite` (1881), outcome arbitration block inside `_run_suite` (lines 1814 to 1849: `accounting_ok`, `inventory_drift`, timeout precedence, outcome classification) | `_campaign_qualification` (2149), `_process_attribution_passed` (2140) (matched-campaign side, outside the class) | `cancelled`, `cancel_reason`, `focused_test_ids` (selector validation), deadlines passed as parameters | none outside the returned records (record builders are pure data construction) |
| Reporting and process context | `run_async` report assembly half (lines 2050 to 2099), `write_report` (2107), `_process_snapshot` (1914), `_process_context_monitor` (1984), `_elapsed_seconds` (1894), `_git_revision` (1270, report provenance, called once at 2004) | `_write_json_atomic` (2211) (campaign side) | `processes` (ownership walk), `capture_process_context`, `json_report`, `focused_suites`, `focused_test_ids`, plus nearly every config field echoed into the report | `process_context_samples`, `unassigned_controllers`, `peak_owned_rss_kib`, `base_report`, `start_monotonic`, `global_deadline` (bootstrap writes in `run_async`) |

`run_async` is not one responsibility: it bootstraps the deadline state (scheduling), installs signal handlers (cancellation), launches the context monitor (reporting), gathers the suite tasks (orchestration), re-derives the inventory for drift, then assembles the final report dict (reporting). It is the composition root and the largest single-method coupling site (103 lines).

Shared-state usage was measured, not eyeballed. Command (run in the worktree root; attributes each `self.<attr>` occurrence to its enclosing method across the class body lines 1175 to 2121):

```bash
python3 -c "
import re
lines = open('scripts/run_required_test_suite.py').read().splitlines()
class_body = lines[1174:2121]
attrs = ['self.cancelled', 'self.cancel_reason', 'self.processes', 'self.max_active_children',
         'self.process_context_samples', 'self.unassigned_controllers', 'self.peak_owned_rss_kib',
         'self.gate', 'self.semaphore', 'self.suite_semaphore', 'self.start_monotonic',
         'self.global_deadline', 'self.report_reserve', 'self.base_report',
         'self.root', 'self.workers', 'self.per_script_timeout', 'self.suite_timeout',
         'self.cleanup_grace', 'self.focused_test_ids', 'self.focused_suites',
         'self.capture_process_context', 'self.json_report', 'self.python_executable', 'self.venv_bin']
for attr in attrs:
    methods = set()
    sites = 0
    current = None
    for i, line in enumerate(class_body):
        m = re.match(r'\s+(async )?def (\w+)', line)
        if m:
            current = m.group(2)
        if attr in line and current:
            methods.add(current)
            sites += 1
    print(f'{attr}: {sites} sites in {len(methods)} methods: {sorted(methods)}')"
```

Observed output verbatim:

```text
self.cancelled: 15 sites in 6 methods: ['__init__', '_cancel_after_deadline', '_receive_signal', '_run_process', '_run_shard', '_run_suite']
self.cancel_reason: 13 sites in 6 methods: ['__init__', '_cancel_after_deadline', '_receive_signal', '_run_process', '_run_suite', 'run_async']
self.processes: 5 sites in 3 methods: ['__init__', '_process_snapshot', '_run_process']
self.max_active_children: 4 sites in 3 methods: ['__init__', '_run_process', 'run_async']
self.process_context_samples: 4 sites in 3 methods: ['__init__', '_process_context_monitor', 'run_async']
self.unassigned_controllers: 3 sites in 3 methods: ['__init__', '_process_snapshot', 'run_async']
self.peak_owned_rss_kib: 3 sites in 3 methods: ['__init__', '_process_snapshot', 'run_async']
self.gate: 5 sites in 4 methods: ['__init__', '_cancel_after_deadline', '_receive_signal', '_run_suite']
self.semaphore: 2 sites in 2 methods: ['__init__', '_run_process']
self.suite_semaphore: 4 sites in 2 methods: ['__init__', '_run_suite']
self.start_monotonic: 4 sites in 2 methods: ['__init__', 'run_async']
self.global_deadline: 4 sites in 4 methods: ['__init__', '_cancel_after_deadline', '_run_suite', 'run_async']
self.report_reserve: 3 sites in 3 methods: ['__init__', '_cancel_after_deadline', '_run_suite']
self.base_report: 5 sites in 2 methods: ['__init__', 'run_async']
self.root: 18 sites in 14 methods: ['__init__', '_cancelled_shard', '_cancelled_suite', '_child_env', '_git_revision', '_inventory', '_run_process', '_run_shard', '_run_suite', '_selected', '_shard_record', '_worker', 'run_async', 'write_report']
self.workers: 5 sites in 3 methods: ['__init__', '_run_suite', 'run_async']
self.per_script_timeout: 3 sites in 3 methods: ['__init__', '_run_suite', 'run_async']
self.suite_timeout: 3 sites in 2 methods: ['__init__', 'run_async']
self.cleanup_grace: 7 sites in 4 methods: ['__init__', '_run_process', '_worker', 'run_async']
self.focused_test_ids: 6 sites in 3 methods: ['__init__', '_run_suite', 'run_async']
self.focused_suites: 5 sites in 3 methods: ['__init__', '_selected', 'run_async']
self.capture_process_context: 3 sites in 2 methods: ['__init__', 'run_async']
self.json_report: 4 sites in 2 methods: ['__init__', 'write_report']
self.python_executable: 4 sites in 4 methods: ['__init__', '_run_process', '_run_suite', 'run_async']
self.venv_bin: 6 sites in 4 methods: ['__init__', '_child_env', '_run_suite', 'run_async']
```

Reading of the measurements: configuration-only fields (`root`, `json_report`, `focused_suites`, `cleanup_grace`) are wide but shallow, value-style reads that a constructor parameter or module constant can replace; they are not the coupling. The coupling is the four state families below, each shared across three or more of the five responsibilities.

## Coupling evidence

### Shared state that would split poorly

1. Cancellation pair: `cancelled` (asyncio Event, 15 sites) and `cancel_reason` (13 sites), each spanning 6 methods across four responsibilities. Writes happen in exactly two places (`_receive_signal` sets `"signal"`, `_cancel_after_deadline` sets `"timeout"`), but every write must wake the scheduling gate (`gate.wake()`) so a blocked serial admission re-checks; reads happen in worker launch short-circuits (`_run_process`), shard and suite cancellation records (`_run_shard`, `_cancelled_shard`, `_cancelled_suite`, `_run_suite` outcome arbitration), and final status derivation (`run_async`). An extracted worker-lifecycle or accounting component must either receive this pair (and the wake protocol) as a shared context object, making it a parameter threaded through everything, or the coordinator must keep it and expose a query surface; neither reduces the coupling, both move it.
2. Deadline chain: `start_monotonic`, `global_deadline`, `report_reserve` are written once at bootstrap (`run_async`) and read by the per-suite deadline computation in `_run_suite` (`source_deadline = min(started + per_script_timeout, global_deadline - report_reserve)`), the suite timeout enforcer (`_cancel_after_deadline`), and the report echo. Scheduling and accounting both consume derived deadlines as plain parameters, so the chain itself would survive extraction, but the enforcer and the scheduler share its write point; splitting them splits the invariant that the report reserve is subtracted exactly once.
3. Admission slot interlock: `suite_semaphore` and `gate` are acquired in strict order inside `_run_suite` (semaphore first, then `gate.acquire(serial, cancelled)`), and both are released in the same `finally` (lines 1857 to 1863); `_run_process` separately holds `semaphore` across each worker spawn. The serial-first admission rule, the cancellation wakeup, and the `shard_workers = max(1, self.workers - 1)` reservation (line 1764 (the sibling branch at 1750; lines 1776 to 1785 are the shard split consuming the reservation), coupling the worker cap into per-suite shard topology) form one protocol. Extracting "worker lifecycle" or "accounting" as components while this protocol stays in the coordinator leaves them called only from inside one coordinator method; extracting the protocol too means every component shares the gate object, which is the same coupling under another name.
4. Process registry: `self.processes` is written by `_run_process` (insert on spawn, pop in `finally`) and read by `_process_snapshot` (`active_groups`, the pid-to-group ownership walk feeding `unassigned_controllers` and `peak_owned_rss_kib`) and by the `max_active_children` peak. This is a direct lifecycle-to-reporting bridge: the diagnostic sampler's correctness depends on the lifecycle layer's bookkeeping discipline. A component split must define who owns the registry; both ownership choices cross a responsibility boundary.
5. Two interleaving bodies: `_run_suite` (203 lines) walks admission, collection handling, focused-test-id selection, shard topology, shard execution, and outcome arbitration in one try/finally whose release contract is correctness-critical; `run_async` (103 lines) is orchestration and report assembly at once. Any decomposition has to cut through these two bodies; there is no seam that separates responsibilities without rewriting them first.

### Components that would extract cleanly

1. Process-tree attribution and cleanup helpers: class side `_signal_group` (9), `_descendant_groups` (51), `_process_group_exists` (10), `_cleanup_process` (72), about 142 lines; module side `_worker_process_groups` (828 to 863), `_live_process_groups` (865 to 909), `_cleanup_worker_descendants` (911 to 960), about 131 lines. Near-stateless: pid in, group set out, plus grace and timeout parameters; no instance state beyond sibling calls. Extraction would also merge two parallel parent-chain walkers that must stay behaviorally in sync (the Task 2 record names both as sharing the same pre-reparented-grandchild blind spot). This is the strongest candidate and the only one where extraction reduces a live duplication risk rather than only moving lines.
2. Record builders: `_shard_record` (57), `_exception_shard_record` (10), `_cancelled_shard` (15), `_cancelled_suite` (11), `_parse_marker` (8), `_elapsed_seconds` (19), about 120 lines. Read `root` plus their arguments; pure data construction; move as free functions taking `root` as a parameter.
3. Worker environment preparation: `_configured_python` (16), `_child_env` (12), about 28 lines; depends only on interpreter selection and `root`.
4. Report persistence: `write_report` (12 lines); reads only `json_report`; called once from `main` (line 2432) after `run()`; already a self-contained tail method.

Extraction ceiling: candidates 1 to 4 total roughly 300 of the 947 class lines. What remains is still a roughly 650-line coordinator holding the cancellation pair, the deadline chain, the admission interlock, the process registry, and the two interleaving bodies. The origin's five responsibilities do not map to five independently instantiable components; they map to method clusters sharing one event-loop-scoped state machine. Decomposing along the five-responsibility boundary would therefore either leave extracted components as parameter-passing shells around coordinator-owned state or push that state into module globals, which is the "split shared state poorly" outcome the origin warns against.

## Verdict

Keep: no decomposition now, and none is recommended by this plan. The finding is confirmed as stated (five responsibilities in one 947-line, 28-method class, figures essentially unchanged since authoring), but the measured shared-state map shows the responsibilities interlock through four state families (cancellation pair, deadline chain, admission interlock, process registry) that a component boundary cannot cut without either splitting that state or globalizing it. The cleanly extractable surface (about 300 near-stateless lines, already partly mirrored at module level) is periphery; extracting it would shrink the file without reducing the coordination coupling that the finding actually points at. No triggering cost is recorded: the runner has not changed since 2026-11-11, Tasks 1 through 3 of this plan read and extended adjacent surfaces (cancellation boundary, descendant containment, wrapper setup) without requiring a structural change, and Task 2 resolved through the document-boundary branch with zero runner edits. A refactor here would exist to satisfy the structure finding, which the origin explicitly bars when extraction would split shared state poorly; the evidence above says it would.

## Disposition

Keep, with the recorded rationale above. No backlog row is filed: the decomposition verdict is not affirmative, so the Outcome's follow-up disposition routing (backlog row with a ready-to-dispatch prompt) does not apply. The assessment is complete as evidence; no runner change is made in this task.

Revisit triggers, recorded so a future session re-derives the decision rather than re-litigating it:

- A second consumer needs the attribution helpers: extract the process-tree attribution module (candidate 1) and point both the worker-side and coordinator-side paths at it; that seam is stateless and merges the two walkers.
- The class gains a sixth responsibility or a defect shows the two-walker sync cost: re-run this inventory; at that point extraction starts from candidate 1 and leaves the coordination core whole.
- Any future extraction must preserve the two write-to-wake invariants named above (every cancellation-pair write wakes the gate; `_run_suite`'s finally releases the suite semaphore and the gate in its current order) and must keep termination scope bounded to attributed descendant groups, per the Task 2 boundary record.
