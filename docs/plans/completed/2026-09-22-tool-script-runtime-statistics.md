# Plan: tool and script runtime statistics

Backlog origin: `docs/history/backlog/2026-09-22-tool-runtime-statistics-and-scriptable-replacement.md` (scope of record). Prior qualitative triage this program replaces with measurement: the executed harness triage record (2026-09-18/20, wall-clock speedups item).

## Terms

- **Host session store**: the runtime's local SQLite session database. Its absolute path is machine-specific and lives only in the gitignored facts document; the zcode adapter default is `$HOME/.zcode/cli/db/db.sqlite` (schema measured read-only on this host 2026-09-22). Load-bearing shapes: `tool_usage(id TEXT PK, session_id, turn_id, tool_call_id, tool_name, status CHECK IN ('running','completed','error','cancelled'), started_at INTEGER epoch-ms, completed_at INTEGER, duration_ms INTEGER, error_type TEXT, ...)` and `turn_usage(session_id, turn_id, ..., tool_call_count INTEGER, input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens, computed_total_tokens, started_at INTEGER, PRIMARY KEY(session_id, turn_id))`.
- **Part table**: the store's message-part table `part(id, message_id, session_id, data TEXT JSON, ...)`; tool-call parts carry JSON `{"type": "tool", "callID": ..., "tool": ..., "state": {"input": {...}, ...}}`, and `callID` joins to `tool_usage.tool_call_id`. The Bash command string lives at `state.input.command`.
- **Miner**: the offline collector inside `scripts/tool_runtime_stats.py` that reads the store read-only and aggregates per-day rows.
- **Ranking report**: the analyzer half of the same script run: top-N rankings, the scriptable-candidate list, and the weekly trend section, emitted next to the collected table.
- **Scriptable candidate**: a measured row passing `deterministic AND frequent AND judgment-free` (the executed three-question triage test applied to measured rows).
- **Rider step**: a step inside the existing maintenance scheduler turn; it never creates an automation, never registers a hook, never adds a crontab entry.
- **No-judgment token share**: estimated share of tokens spent in turns that joined exactly one tool row (the mechanical proxy for deterministic work); a per-day figure, always labeled `est_`.
- **Report home**: the resolved tmp directory's `tool-runtime-stats/` folder holding one stamped JSON table plus Markdown digest per run, with a retention line. Newest prior report means the lexicographically greatest run-stamped filename.
- **Digest log**: `docs/maintenance/tool-runtime-stats-log.md`, the durable aggregates-only log the rider appends one section to per week.
- **Sanctioned path prefixes**: the repo root (resolved via `git rev-parse --show-toplevel` at run time) and `$HOME/.ai-playbook/`. Script slugs are emitted only for commands referencing scripts under these prefixes; every other command aggregates as `other`, so paths and script names from other projects never reach an artifact.

## Assumptions

- assume a single-file script `scripts/tool_runtime_stats.py` with one `run` subcommand (collect and report in one pass) and `--store` / `--out-root` / `--repo-root` overrides; basis: the origin allows one or two files, and repo convention pairs single-purpose scripts with a `test_` twin.
- assume the facts TOML key `session_store_path` in `.ai-playbook/facts.md` (gitignored) resolves the store, falling back to `$HOME/.zcode/cli/db/db.sqlite`; basis: the 2026-09-20 turn-usage probe verified that store read-only on this host, and `scripts/review_usage_capture.py` already reads it via a zcode-first adapter. The absolute machine path is never committed; the fallback is `$HOME`-relative.
- assume the store schema pinned in Terms (measured read-only on this host 2026-09-22); execution re-verifies it with a live probe before implementation (Task 1) because the schema is runtime-owned, not contract-owned.
- assume inclusive auto-file thresholds: a row files a candidate when total time >= 300 seconds/day, OR mean >= 10 seconds AND calls >= 50/day; basis: the origin's "~5 minutes/day aggregate, or ~10s mean at >= 50 calls/day" contract with inclusive comparisons. Arithmetic note: under `total = count x mean` the second arm is strictly subsumed by the first (calls >= 50 and mean >= 10 imply total >= 500); both arms are implemented as written so the contract stays faithful to the origin, and boundary tests are pinned where each arm is the binding one.
- assume the error-rate ranking applies a count floor of 50 calls in the report window; basis: reuse of the origin's only stated count floor, avoiding a second unpinned magic number.
- assume the weekly rider gate is: newest prior report in the report home is absent or at least 7 days old; basis: the origin's "weekly cadence, maintenance turn rider, never a new automation".
- assume the digest log home is `docs/maintenance/tool-runtime-stats-log.md`; basis: the origin requires the cadence to append the digest durably, and `docs/maintenance/` is the tracked home for maintenance-operational output. The log carries aggregates only.
- assume session scope is host-wide at the tool level and repo-anchored at the attribution level: per-tool rows aggregate every session in the store (tool names are runtime-generic), while script slugs are emitted only for commands under the sanctioned path prefixes; basis: the origin measures host wall-clock, and the plan's privacy invariant forbids other projects' identifiers in committed artifacts. The repo-anchor precedent is `scripts/review_usage_capture.py`, which filters sessions by directory before aggregating.
- assume the no-judgment token proxy is turns that joined exactly one tool row; basis: the origin's mechanical proxy wording; the share is a per-day figure labeled `est_no_judgment_token_share`.
- assume ranking top-N defaults to N=5 with a CLI override; basis: the acceptance criteria require at least the top three rows, so the default must exceed three.
- assume trend is computed against the newest prior report in the report home; basis: the origin's fourth contract metric ("Trend per week (improvement verification: did the fix move the number)"), implementable without any new persistence because the report home already accumulates stamped runs.

Decision points requiring a grill: none remain.

## Gist & Examples

**What changes (plain language).** Today "where did the wall-clock go this week?" and "which repeated model work is deterministic enough to become a script?" are answered by reasoning alone. This plan lands an offline measurement program: one new script mines the host session store read-only, emits a per-day runtime table (JSON plus a short Markdown digest), and ranks time loss, token cost, error rate, weekly trend, and scriptable-replacement candidates from measured numbers. A weekly rider step inside the existing maintenance scheduler turn appends the digest to a durable log and files a backlog item for every candidate above the pinned threshold, so the improvement queue is fed by measurement instead of anecdote.

**Before (today).** A maintenance turn wants to rank improvement work; it has no per-tool or per-script runtime numbers, so it reasons qualitatively, exactly as the executed harness triage had to (its ranking was adjudicated without measurements, and the record explicitly deferred a language-rewrite decision until measured evidence exists).

**After (this plan).** The maintenance turn's rider step runs `python3 scripts/tool_runtime_stats.py` (offline, fail-open). A run emits, under the resolved tmp dir's `tool-runtime-stats/`, a JSON table whose rows derive from the real store columns:

```json
{"days": [{"date": "2026-09-21", "tool": "Edit", "calls": 431, "errors": 27, "mean_seconds": 9.8, "p95_seconds": 31.0, "total_seconds": 4223.8, "script_slug": null, "trend_total_seconds_delta": -310.5}],
 "day_summaries": [{"date": "2026-09-21", "tokens_in": 152340, "tokens_out": 41200, "est_no_judgment_token_share": 0.31}]}
```

and a digest whose ranking section names rows like: `Edit: 431 calls/day, 70.4 min/day total, error rate 6.3 percent; scriptable candidate: no (judgment required)`. A candidate above threshold (`Read`: mean 12.1 s at 60 calls/day) is filed by the rider as a backlog item naming the measured row, the proposed replacement shape, and the estimated saving. The trend section compares each top row against the newest prior report: `Read: 60 calls/day, total 726 s/day (delta +95 s/day vs 2026-09-14)`.

**Why these shapes.** Two examples from the origin item drive the thresholds: a tool used hundreds of times a day at about 10 seconds per call is tens of minutes of pure overhead daily regardless of what it does; model turns spent on deterministic work (counting, formatting, scanning, sorting, status arithmetic) cost tokens and reliability, and each is a replacement candidate.

**Edge cases motivating design decisions.** Missing store or missing tables: the miner reports one line and exits 0 (fail-open), because absence of data must never break a maintenance turn. Bash commands outside the sanctioned path prefixes: they aggregate as `other` instead of being dropped, so totals reconcile and other projects' identifiers never reach an artifact. Privacy: the store holds private session data, so every emitted artifact carries aggregates only (counts, durations, tool and script names, token sums); prompts, message content, and paths from other projects never appear. Command strings are read solely to derive slugs and are never emitted.

## Evaluation Criteria

**Quality dimensions:**

- correctness: aggregation math is exact against fixtures shaped like the real store columns, including the threshold boundaries (300 seconds/day; the mean/count arm's 50-call floor) and the error-rate floor (50 calls); per-day attribution reconciles to fixture totals.
- privacy: every emitted artifact carries aggregates only; the hygiene scan exits 0 on the new files; dedicated tests prove fixture prompt-like content (in a message-like field and mid-command) never reaches an artifact.
- robustness: missing store, missing tables, and empty windows produce a one-line report and exit 0; the store is provably unmodified after a full run.
- maintainability: one script file plus one hermetic test file; the rider is one additive step, one amended enumeration sentence, and one configuration row; no existing maintenance step's semantics change.
- observability: each run's artifacts are stamped, carry a retention line and a trend section, and the digest log gains one section per week.

**Done when:**

- `python3 scripts/tool_runtime_stats.py` runs against the live host store read-only, exits 0, and leaves report artifacts in the report home.
- The ranking report names at least the top three time-loss rows and at least the top three scriptable candidates with measured numbers (all rows when fewer than three exist), and carries the weekly trend section.
- One loop is demonstrated end to end: measured row, candidate disposition; if no candidate clears threshold yet, the demonstration is a no-action verdict recorded against the report's own top row, never a fabricated fix.
- No new always-on hook, automation, or crontab entry exists in the diff (witnessed by Validation Commands item 7); the only skill change is the additive rider step, the amended step-range sentence, and the configuration row.
- `python3 scripts/test_tool_runtime_stats.py` exits 0; the em-dash scan and the public-hygiene scan exit 0 on the changed files.

**Ship when:**

- The weekly rider is observed feeding the improvement queue on this host across at least two maintenance turns (digest sections appended, candidates filed or no-action verdicts recorded, trend deltas visible between sections). This is host-owned cadence evidence; prose only, not a checklist item.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/tool_runtime_stats.py` *(new)*
- `agents/skills/maintenance/SKILL.md` (additive only: the rider step, the amended step-range sentence, and the configuration row)

**Tests:**

- `scripts/test_tool_runtime_stats.py` *(new)*

**Documentation:**

- `docs/maintenance/tool-runtime-stats-log.md` *(new, created by execution on this host)*; tracked runtime artifact reviewed through the aggregates-only and hygiene contracts, not line by line.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Runtime artifacts, not line-by-line review surfaces:** execution also creates report files under the gitignored report home and filed candidate backlog items. They carry aggregates only by design; review touches them only through the privacy and thresholds contracts.

**Out of scope; reject unless plan-related:**

- `scripts/review_usage_capture.py`; reason: read-only precedent this program builds on, no edits planned.
- `docs/history/backlog/2026-09-19-edit-failure-churn-read-discipline.md` and `docs/history/backlog/2026-09-19-cache-breakpoint-overflow-token-cost.md`; reason: named consumers of this program's report, their fixes belong to their own plans.
- `docs/history/backlog/2026-09-20-turn-usage-token-probe.md`; reason: referenced measurement primitive, not an edit target.
- `agents/hooks/**`; reason: no new hook is a design invariant of this plan.

## Design Invariants (CR Guard)

- **Store is read-only.** The miner connects via the SQLite read-only URI mode and issues no write or attach statement against the store. Verified by a test asserting the store file's sha256 is identical before and after a full run against a fixture.
- **Aggregates only.** Every artifact (JSON table, digest, digest log section, filed candidate) carries counts, durations, tool and script names, and token sums. Prompts, message content, and paths from other projects never appear. Command strings are read only to derive slugs and never emitted. Enforced by dedicated tests plus the public-hygiene scan.
- **Repo-anchored attribution.** Script slugs are emitted only for commands under the sanctioned path prefixes; all other commands aggregate as `other`. Foreign projects' script names never reach an artifact.
- **No new always-on hook.** The program is offline only. The rider runs inside the existing maintenance scheduler turn; it never creates an automation, registers a hook, or adds a crontab entry. The executed hook-tax decision stands.
- **No gate or skill behavior change beyond the rider.** The only skill edits are the additive `### Step 7` rider subsection, the amended step-range sentence, and one configuration-table row; every existing step's semantics stay untouched (phase 1 measurement-only constraint from the origin).
- **No language rewrite.** The program is Python, matching repo scripting convention. The executed 2026-09-18 rewrite rejection stands; this program is how evidence to revisit that decision would ever be gathered.
- **Fail open on absent data.** Missing store, missing tables, or an empty window produce a one-line report and exit 0. Only the pinned absent-data arms are swallowed; genuine defects still raise.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1

# 1. Hermetic suite (aggregation, attribution, token join, privacy, retention, thresholds, trend, fail-open, read-only).
python3 scripts/test_tool_runtime_stats.py || { echo "FAIL: suite"; exit 1; }

# 2. CLI end-to-end against a fixture store shaped like the real schema: exit 0, both artifacts exist,
#    retention line present, slug attributed and named in the digest (the fixture's fifty single-tool
#    turns make the row a filed scriptable candidate), and the raw fixture command string absent.
VDIR="$(mktemp -d)"
python3 - "$VDIR/store.sqlite" <<'PYEOF' || { echo "FAIL: fixture build"; rm -rf "$VDIR"; exit 1; }
import sqlite3, sys, datetime, json
conn = sqlite3.connect(sys.argv[1])
conn.executescript(
    "CREATE TABLE tool_usage (id TEXT PRIMARY KEY, session_id TEXT, turn_id TEXT, tool_call_id TEXT,"
    " tool_name TEXT, status TEXT, started_at INTEGER, completed_at INTEGER, duration_ms INTEGER,"
    " error_type TEXT);"
    "CREATE TABLE turn_usage (session_id TEXT, turn_id TEXT, started_at INTEGER, status TEXT,"
    " tool_call_count INTEGER, input_tokens INTEGER, output_tokens INTEGER, computed_total_tokens INTEGER,"
    " PRIMARY KEY (session_id, turn_id));"
    "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT, sequence INTEGER);"
    "CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT, sequence INTEGER);"
)
base = int(datetime.datetime(2026, 9, 21, 10, 0, 0).timestamp() * 1000)
cmd = "python3 scripts/quota_window_probe.py PW-SYNTHETIC-MIDTOKEN secret-fixture-string"
for i in range(50):
    turn_start = base + i * 20000
    conn.execute("INSERT INTO turn_usage VALUES ('s1', ?, ?, 'completed', 1, 900, 100, 1000)", (f"t{i}", turn_start))
    conn.execute("INSERT INTO tool_usage VALUES (?, 's1', ?, ?, 'Bash', 'completed', ?, ?, 11000, NULL)",
                 (f"tu{i}", f"t{i}", f"call{i}", turn_start, turn_start + 11000))
    conn.execute("INSERT INTO part VALUES (?, 'm1', 's1', ?, ?)",
                 (f"p{i}", json.dumps({"type": "tool", "callID": f"call{i}", "tool": "Bash",
                                       "state": {"input": {"command": cmd}, "status": "completed"}}), i))
conn.execute("INSERT INTO message VALUES ('m1', 's1', ?, 1)",
             (json.dumps({"role": "user", "content": "PW-SYNTHETIC-MIDTOKEN secret-fixture-string"}),))
conn.commit(); conn.close()
PYEOF
python3 scripts/tool_runtime_stats.py run --store "$VDIR/store.sqlite" --out-root "$VDIR/out" --repo-root "$REPO" || { echo "FAIL: cli run"; rm -rf "$VDIR"; exit 1; }
JSON_FILE="$(find "$VDIR/out" -name '*.json' | head -1)"
DIGEST_FILE="$(find "$VDIR/out" -name '*.md' | head -1)"
test -n "$JSON_FILE" || { echo "FAIL: no json artifact"; rm -rf "$VDIR"; exit 1; }
test -n "$DIGEST_FILE" || { echo "FAIL: no digest artifact"; rm -rf "$VDIR"; exit 1; }
grep -q "retention:" "$DIGEST_FILE" || { echo "FAIL: no retention line"; rm -rf "$VDIR"; exit 1; }
grep -q "quota_window_probe.py" "$DIGEST_FILE" || { echo "FAIL: script slug not attributed"; rm -rf "$VDIR"; exit 1; }
if grep -q "secret-fixture-string" "$JSON_FILE" "$DIGEST_FILE"; then echo "FAIL: free text leaked into artifacts"; rm -rf "$VDIR"; exit 1; fi
rm -rf "$VDIR"

# 3. Fail-open CLI: missing store and table-less store both exit 0 with a report line.
VDIR2="$(mktemp -d)"
python3 scripts/tool_runtime_stats.py run --store "$VDIR2/absent.sqlite" --out-root "$VDIR2/out1" > "$VDIR2/rep1.txt" 2>&1
test $? -eq 0 || { echo "FAIL: missing store did not exit 0"; rm -rf "$VDIR2"; exit 1; }
test -s "$VDIR2/rep1.txt" || { echo "FAIL: missing store printed no report"; rm -rf "$VDIR2"; exit 1; }
python3 -c "import sqlite3, sys; sqlite3.connect(sys.argv[1]).close()" "$VDIR2/empty.sqlite"
python3 scripts/tool_runtime_stats.py run --store "$VDIR2/empty.sqlite" --out-root "$VDIR2/out2" > "$VDIR2/rep2.txt" 2>&1
test $? -eq 0 || { echo "FAIL: table-less store did not exit 0"; rm -rf "$VDIR2"; exit 1; }
test -s "$VDIR2/rep2.txt" || { echo "FAIL: table-less store printed no report"; rm -rf "$VDIR2"; exit 1; }
rm -rf "$VDIR2"

# 4. Rider step pins in the maintenance skill; each obligation gets its own dedicated search, exactly once.
SKILL="agents/skills/maintenance/SKILL.md"
test -f "$SKILL" || { echo "FAIL: missing SKILL.md"; exit 1; }
grep -qF "### Step 7: weekly measurement rider" "$SKILL" || { echo "FAIL: rider step heading missing"; exit 1; }
test "$(grep -cF '### Step 7: weekly measurement rider' "$SKILL")" -eq 1 || { echo "FAIL: rider heading not exactly once"; exit 1; }
grep -qF "Run Steps 0 through 7 in this order, in one pass" "$SKILL" || { echo "FAIL: step-range sentence not amended"; exit 1; }
test "$(grep -cF 'Run Steps 0 through 7 in this order, in one pass' "$SKILL")" -eq 1 || { echo "FAIL: amended range not exactly once"; exit 1; }
if grep -qF "Run Steps 0 through 6 in this order" "$SKILL"; then echo "FAIL: stale step-range sentence survives"; exit 1; fi
grep -qF "absent or at least 7 days old" "$SKILL" || { echo "FAIL: weekly gate wording missing"; exit 1; }
grep -qF "never creates an automation" "$SKILL" || { echo "FAIL: no-new-automation wording missing"; exit 1; }
grep -qF '| `session_store_path` |' "$SKILL" || { echo "FAIL: configuration row missing"; exit 1; }
test "$(grep -cF '| `session_store_path` |' "$SKILL")" -eq 1 || { echo "FAIL: configuration row not exactly once"; exit 1; }
grep -qF "aggregates only" "$SKILL" || { echo "FAIL: aggregates-only wording missing in rider"; exit 1; }

# 5. The rider step sits inside the scheduler turn, after Step 6, before the failure cap (full chain).
LINE_RIDER="$(grep -nF '### Step 7: weekly measurement rider' "$SKILL" | cut -d: -f1)"
LINE_S6="$(grep -nF '### Step 6: state update' "$SKILL" | cut -d: -f1)"
LINE_FAILCAP="$(grep -nF '## Failure detection and the failure cap' "$SKILL" | cut -d: -f1)"
test -n "$LINE_RIDER" && test -n "$LINE_S6" && test -n "$LINE_FAILCAP" || { echo "FAIL: anchor missing"; exit 1; }
test "$LINE_S6" -lt "$LINE_RIDER" && test "$LINE_RIDER" -lt "$LINE_FAILCAP" || { echo "FAIL: rider not between Step 6 and failure cap"; exit 1; }

# 6. Hygiene and em-dash scans over the changed files (anchored cwd).
( cd "$REPO" && bash scripts/scan-public-hygiene.sh --files scripts/tool_runtime_stats.py scripts/test_tool_runtime_stats.py agents/skills/maintenance/SKILL.md docs/maintenance/tool-runtime-stats-log.md ) || { echo "FAIL: hygiene scan"; exit 1; }
bash "$REPO/scripts/check-no-em-dash.sh" file scripts/tool_runtime_stats.py scripts/test_tool_runtime_stats.py agents/skills/maintenance/SKILL.md docs/maintenance/tool-runtime-stats-log.md || { echo "FAIL: em-dash scan"; exit 1; }

# 7. No-new-hook diff gate over this plan's own commits (base sha recorded by Task 1, rule 31 compliant).
BASE_FILE="docs/tmp/execute-plan/tool-script-runtime-statistics/base-sha.txt"
test -f "$BASE_FILE" || { echo "FAIL: base sha not recorded"; exit 1; }
BASE="$(cat "$BASE_FILE")"
VDIR3="$(mktemp -d)"
DIFF_RC=0
git diff --name-only "$BASE" HEAD > "$VDIR3/diffnames.txt" 2>/dev/null || DIFF_RC=$?
test "$DIFF_RC" -eq 0 || { echo "FAIL: diff against base sha errored (rc=$DIFF_RC)"; rm -rf "$VDIR3"; exit 1; }
if grep -q "^agents/hooks/" "$VDIR3/diffnames.txt"; then echo "FAIL: agents/hooks path in plan diff"; rm -rf "$VDIR3"; exit 1; fi
rm -rf "$VDIR3"
```

### Task 1: Collector: read-only per-day per-tool table

Files:
- `scripts/tool_runtime_stats.py` *(new)*
- `scripts/test_tool_runtime_stats.py` *(new)*

- [x] Record the plan's base sha for the no-new-hook diff gate: `mkdir -p docs/tmp/execute-plan/tool-script-runtime-statistics && git rev-parse HEAD > docs/tmp/execute-plan/tool-script-runtime-statistics/base-sha.txt` [class: IMPLEMENTATION_REQUIRED]
- [x] Live schema probe: with the store opened read-only, assert the Terms-pinned columns exist (`tool_usage.tool_name`, `tool_usage.status`, `tool_usage.started_at`, `tool_usage.completed_at`, `tool_usage.duration_ms`, `tool_usage.tool_call_id`; `turn_usage.session_id`, `turn_usage.turn_id`, `turn_usage.tool_call_count`, `turn_usage.input_tokens`, `turn_usage.output_tokens`, `turn_usage.computed_total_tokens`; `part.id`, `part.message_id`, `part.session_id`, `part.data`); record the probe output in the session log; a drifted schema blocks implementation (load-bearing contract), unlike the runtime fail-open arms [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_per_day_call_and_error_counts`; given a fixture with `tool_usage` rows for two tools across two local dates (epoch-ms `started_at`), expects one aggregated row per (date, tool) with exact call counts and exact error counts derived from `status='error'` [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_duration_present_uses_store_timing`; given fixture rows with positive `duration_ms`, expects mean and p95 computed from that column and total seconds equal to count times mean [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_duration_absent_derives_wallclock_delta`; given fixture rows with NULL `duration_ms` and both epoch-ms bounds present, expects duration derived as `completed_at - started_at` [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_store_opened_read_only_and_unmodified`; given a fixture store path, expects the miner connects in SQLite read-only mode and the store file's sha256 is byte-identical before and after a full run [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_missing_store_fails_open`; given a store path that does not exist, expects a one-line report on stdout and exit code 0 [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_missing_tables_fails_open`; given a store file lacking the tables, expects a one-line report and exit code 0 [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_store_path_resolves_from_facts_with_cli_override`; given a temp facts file with `session_store_path` and a `--store` override, expects the override to win and the facts value to be read when the override is absent [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_tool_runtime_stats.py` (module does not exist yet; collection error) [class: REPOSITORY_TEST]
- [x] Implement `scripts/tool_runtime_stats.py`: argparse `run` subcommand; facts TOML resolution for `session_store_path` with the `$HOME/.zcode/cli/db/db.sqlite` fallback; read-only connection; per-local-date per-tool aggregation from `tool_name`, `status`, epoch-ms `started_at`, and the duration contract above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_tool_runtime_stats.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: tool runtime stats collector with read-only fail-open mining` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Bash-call script attribution (repo-anchored)

Files: none new (validation only; extends the Task 1 files `scripts/tool_runtime_stats.py` and `scripts/test_tool_runtime_stats.py`)

- [x] `ToolRuntimeStatsTests#test_bash_command_attribution_to_script_slug`; given a fixture with `part` rows whose JSON carries `callID` matching `tool_usage.tool_call_id` and `state.input.command` invoking a repo script, expects those Bash rows attributed to that script's basename slug [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_command_outside_sanctioned_prefixes_aggregates_as_other`; given Bash commands referencing scripts under a foreign project directory, expects the `other` slug, and expects the foreign path string absent from every artifact [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_attribution_first_scripts_token_wins`; given a command mentioning two sanctioned `scripts/` paths, expects the first token's slug to own the row [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_non_bash_tools_unaffected`; given Edit and Read rows, expects attribution applied only to `tool_name='Bash'` rows [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_missing_part_rows_degrade_to_other`; given Bash rows with no matching `part` row, expects those rows under `other` and the run still exit 0 (fail-open, one-line report noting the degradation) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_tool_runtime_stats.py` (attribution tests fail; collector exists) [class: REPOSITORY_TEST]
- [x] Implement attribution: for Bash rows only, join `part` by (`session_id`, `callID` = `tool_call_id`), read `state.input.command`, tokenize, and take the first token whose path is under the sanctioned path prefixes (repo root via `--repo-root` or `git rev-parse --show-toplevel`, and `$HOME/.ai-playbook/`); emit its script basename as the slug; everything else aggregates under `other`; command strings are never emitted [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_tool_runtime_stats.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: attribute bash calls to sanctioned repo and runtime script slugs` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Token join per turn

Files: none new (validation only; extends the Task 1 files `scripts/tool_runtime_stats.py` and `scripts/test_tool_runtime_stats.py`)

- [x] `ToolRuntimeStatsTests#test_tokens_joined_by_session_and_turn`; given fixture `turn_usage` rows joined to `tool_usage` by (session_id, turn_id), expects per-tool per-day token sums allocated by the pinned rule: a turn's tokens are divided evenly across the turn's joined tool rows (no duplication) [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_no_judgment_share_is_single_tool_turns_per_day`; given days mixing turns with one joined tool row and turns with several, expects the day-level `est_no_judgment_token_share` equal to tokens of single-joined-row turns over the day's total joined tokens [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_token_join_zero_division_guards`; given a day with turns but no tool rows, and a day with tool rows but no turns, expects a zero share and no crash [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_tool_runtime_stats.py` (token tests fail) [class: REPOSITORY_TEST]
- [x] Implement the token join: `turn_usage` joined by (session_id, turn_id); even allocation across joined rows; day-level summary rows carrying token sums and the labeled `est_no_judgment_token_share` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_tool_runtime_stats.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: join per-turn tokens to tool rows with no-judgment share` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Output contract: JSON plus digest, retention, privacy

Files: none new (validation only; extends the Task 1 files `scripts/tool_runtime_stats.py` and `scripts/test_tool_runtime_stats.py`)

- [x] `ToolRuntimeStatsTests#test_run_writes_json_and_digest_under_out_root`; given a `run` invocation with `--out-root`, expects one run-stamped JSON table and one Markdown digest created under `<out-root>/tool-runtime-stats/` [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_digest_carries_retention_line`; given any successful run, expects the digest to contain a `retention:` line naming the keep-newest policy [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_retention_prunes_oldest_runs`; given an out-root seeded with nine prior runs (filenames run-stamped), expects a new run to leave exactly the newest eight, resolving newest by lexicographic filename order [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_artifacts_carry_aggregates_only`; given a fixture whose `message.data` JSON contains a distinctive synthetic prompt-like string and whose Bash command embeds the same string mid-command, expects that string absent from the JSON and the digest (witness placed in both leak channels) [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_facts_resolved_default_out_root`; given a temp facts file with `tmp_dir`, expects a run without `--out-root` to write under that directory's `tool-runtime-stats/` [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_tool_runtime_stats.py` (output tests fail) [class: REPOSITORY_TEST]
- [x] Implement the output contract: stamped artifact names, retention line, keep-newest-eight pruning with lexicographic newest resolution, and the aggregates-only emission path (no free-text store fields reach artifacts) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_tool_runtime_stats.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: stamped json and digest output with retention and aggregates-only privacy` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Ranking report, scriptable candidates, and weekly trend

Files: none new (validation only; extends the Task 1 files `scripts/tool_runtime_stats.py` and `scripts/test_tool_runtime_stats.py`)

- [x] `ToolRuntimeStatsTests#test_ranking_top_n_by_total_time_and_tokens`; given multi-row fixtures, expects the report's time ranking ordered by total seconds per day descending and token ranking by tokens per day descending, top five by default [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_error_rate_ranking_respects_count_floor`; given a row with 49 calls at a high error rate and a 6-second mean (total 294 s/day, below the aggregate arm), expects it excluded from error ranking; given exactly 50 calls, expects it included [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_filing_threshold_aggregate_boundary`; given a row at exactly 300 total seconds/day, expects a filed candidate, and given 299 expects none [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_filing_threshold_mean_count_arm_positive`; given mean exactly 10.0 seconds at exactly 50 calls/day (total 500 s/day), expects a filed candidate; the test documents that the mean/count arm is arithmetically subsumed by the aggregate arm under `total = count x mean`, so no negative witness exists for this arm in isolation and the aggregate boundary above carries the negative case [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_scriptable_requires_all_three_predicates`; given rows failing each of deterministic, frequent, and judgment-free in turn, expects none marked scriptable; given a row passing all three, expects a candidate naming tool or script, measured cost, replacement shape, and estimated saving; the judgment-free predicate is pinned as at least 80 percent of the row's calls in single-joined-row turns, with boundary witnesses at exactly 80 percent (scriptable, other predicates met) and 79 percent (not scriptable) [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_report_names_top_three_when_present`; given at least three distinct time-loss rows, expects the digest to name at least the top three time-loss rows and at least the top three scriptable candidates with measured numbers [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_digest_names_attributed_rows_by_slug`; given a successful run whose fixture rows carry attributed script slugs, expects every digest line that names such a row to print `script_slug=<basename>`, and expects a filed scriptable candidate row to name the slug [class: REPOSITORY_TEST]
- [x] `ToolRuntimeStatsTests#test_trend_compares_newest_prior_report`; given an out-root holding one prior run and a new run with a changed total for the same tool, expects the new digest's trend section to carry the per-row delta against that prior run, and given an empty out-root expects a `no prior report` line [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_tool_runtime_stats.py` (ranking and trend tests fail) [class: REPOSITORY_TEST]
- [x] Implement the report: rankings, error-rate floor, the three scriptable predicates (deterministic: attributed script slug or fixed invocation shape; frequent: calls/day floor; judgment-free: at least 80 percent of the row's calls in single-joined-row turns), replacement shapes (script, cache, batch, skip), estimated saving from measured totals, the trend section comparing the newest prior report by run-stamped filename, and slug naming: any digest line naming a row with a non-null script_slug prints `script_slug=<basename>` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_tool_runtime_stats.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: ranking report with scriptable candidates and weekly trend` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Maintenance rider step, amended step range, configuration row

Files:
- `agents/skills/maintenance/SKILL.md`

Amend the scheduler-turn enumeration sentence (currently the only occurrence, at the top of `## The scheduler turn`) to:

```markdown
Run Steps 0 through 7 in this order, in one pass. Never reorder the steps and never reorder the guards inside Step 2.
```

Add this rider subsection verbatim after `### Step 6: state update` inside `## The scheduler turn`:

```markdown
### Step 7: weekly measurement rider

- Weekly gate: when the newest prior report under the report home (`tool-runtime-stats/` under the resolved tmp directory, newest = lexicographically greatest run-stamped filename) is absent or at least 7 days old, run `python3 scripts/tool_runtime_stats.py` (offline; the store path resolves from the `session_store_path` facts key, fallback `$HOME/.zcode/cli/db/db.sqlite`). The rider never creates an automation, never registers a hook, and never adds a crontab entry.
- On success: append the digest as one new section to `docs/maintenance/tool-runtime-stats-log.md` (create-if-absent; aggregates only), and for every candidate at or above the filing threshold (total >= 300 seconds/day, or mean >= 10 seconds at >= 50 calls/day) file one backlog item under the resolved backlog directory with a header matching the newest existing backlog item's header fields (newest = the backlog item whose filename sorts last lexicographically), naming the measured row, the proposed replacement shape, and the estimated saving. When no candidate clears the threshold, record one no-action verdict line, naming the report's top row and its measured cost, in the same digest-log section as the appended digest.
- Fail open: a rider error is reported in the turn output without failing the turn; the turn's decisions and state are never blocked by measurement. Absent store or tables produce the script's own one-line report and exit 0.
```

Add this row to the `## Configuration (from facts document)` table:

```markdown
| `session_store_path` | Host session store location for the weekly measurement rider (Step 7); read-only, never written | `$HOME/.zcode/cli/db/db.sqlite` |
```

- [x] Amend the step-range sentence to "Run Steps 0 through 7 in this order, in one pass." exactly as prescribed above [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `### Step 7: weekly measurement rider` subsection verbatim as prescribed above [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `session_store_path` row to the Configuration table as prescribed above [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the rider heading and the amended range sentence each appear exactly once, the stale range phrase is gone, and the configuration-row pin passes (Validation Commands items 4 and 5) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check-no-em-dash.sh file agents/skills/maintenance/SKILL.md` and `( cd "$(git rev-parse --show-toplevel)" && bash scripts/scan-public-hygiene.sh --files agents/skills/maintenance/SKILL.md )` [class: REPOSITORY_TEST]
- [x] Commit: `feat: weekly tool runtime stats rider in maintenance turn` [class: IMPLEMENTATION_REQUIRED]

### Task 7: End-to-end loop demonstration and full validation

Files:
- `docs/maintenance/tool-runtime-stats-log.md` *(new, runtime artifact created on this host)*

- [x] Run `python3 scripts/tool_runtime_stats.py` against the live host store (read-only): expect exit 0 and artifacts in the report home; record the top time-loss row, the top scriptable candidates, and the trend deltas with measured numbers, aggregates only [class: REPOSITORY_TEST]
- [x] Loop demonstration: when no candidate clears the filing threshold, append the demonstration section to the digest log naming the report's own top row, its measured cost, and the verdict `no-action: below threshold`; when a candidate clears, file its backlog item per the rider contract and record that the replacement proceeds through the normal backlog-to-plan lifecycle, never fabricated inside this plan [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the full Validation Commands block (items 1 through 7) exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `test: demonstrate tool runtime stats end-to-end loop on live store` [class: IMPLEMENTATION_REQUIRED]

## Plan Lifecycle note

This plan is measurement and cadence only: when completed, the miner, the rider, and the demonstration artifacts exist; candidate replacements filed by the rider are future backlog items with their own lifecycle, never work of this plan.
