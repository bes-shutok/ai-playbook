# Plan: Tool runtime stats tail (window-bounded mining, dead-parameter cleanup)

Backlog origins (scope of record):
- docs/history/backlog/2026-09-23-tool-runtime-stats-window-bounded-mining.md
- docs/history/backlog/2026-09-23-tool-runtime-stats-post-verification-cleanups.md

Driving force: efficiency + simplicity
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-p62-tool-runtime-stats-tail-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The tool runtime statistics miner gets its cost bound without changing today's behavior: an optional `--days N` window filter (default all-time) lands in the store-access layer with hermetic window tests, the dead window-day-count threading is dropped from the predicates helper, and the hermetic suite's five duplicated per-class fixture setups collapse into one shared mixin. The heavy compute legs of the window origin (streamed aggregation, join pre-filter) stay recorded deferrals behind the origin's own measured trigger.

- The miner's `run` subcommand accepts `--days N` and aggregates only rows whose `started_at` falls inside the last N days; the weekly maintenance rider's bare invocation (`agents/skills/maintenance/SKILL.md` weekly gate) is byte-identical in behavior and output.
- `_predicates` loses its unread `days_count` parameter; the report-window day count survives exactly where the digest heading and per-day rates consume it.
- The test twin's per-class setup boilerplate exists once, in a shared mixin, and the duplicated `_touch_repo_file` helper has one home.
- The streamed-aggregation and join-prefilter legs carry a recorded deferral with the origin's trigger wording, so the deferred scope is a disposition, not an open question.

## Terms

- Miner: `scripts/tool_runtime_stats.py`; its hermetic test twin is `scripts/test_tool_runtime_stats.py` (suite invocation `PYTHONPATH=scripts python3 -m unittest scripts.test_tool_runtime_stats`; 42 tests green on today's tree, witnessed 2026-09-28).
- Store-access layer: the origin's build-on list (`connect_read_only`, `bash_command_slugs`, `collect_day_rows`) plus `collect_day_summaries`, which filtering the origin's "filter tool rows and turns" requires; the window filter belongs here, leaving aggregation and render layers untouched.
- Window bound: `started_after_ms`, a computed lower bound on epoch-ms `started_at`; `None` means unfiltered (today's full-scan contract).
- Window day count: the `days_count` value `window_rows` derives from the aggregated day rows; consumed by the digest heading (`_render_time_ranking`) and the per-day rate denominators.
- Cohort semantics: under a window, a row's turn-token share still divides by the turn's whole-store joined count, so the even allocation stays reconciliation-exact; the degradation counter describes the collected cohort.

## Assumptions

- assume the `--days` flag is behavior-neutral at default because no live caller passes it: the weekly rider invokes the miner bare (`agents/skills/maintenance/SKILL.md` weekly gate line, verified 2026-09-28), and the flag defaults to `None` (unfiltered); basis: disk reads plus the Task 1 byte-equality test that pins a covering-window run's stdout identical to the unflagged run.
- assume the turn-token and joined-count reads stay unfiltered under a window: `collect_day_rows` allocates a turn's tokens evenly across its joined tool rows (per-row share uses the turn's whole joined count, lines validated 2026-09-28), so filtering those reads would change inside-window shares; the origin's "filter tool rows and turns" is honored by filtering the tool-row query and the summary's turn query (by each row's own `started_at`), not the join-shape reads; basis: the even-allocation comment and share logic in `collect_day_rows`.
- assume the digest heading needs no code change for windowed runs: `days_count` derives from the aggregated day rows' dates, so a windowed run naturally reports the windowed count; basis: `window_rows` and `_render_time_ranking` reads, 2026-09-28.
- assume the dead-parameter claim is exact today: `_predicates(tool, entry, days_count)` never reads `days_count` in its body (the frequent basis moved to each entry's own active days, the R6-4 change), while `days_count` occurs on exactly 8 lines in the miner (9 textual occurrences; the dead parameter and its call site account for 2 of the lines); basis: grep and body read of `_predicates`, 2026-09-28.
- assume the fixture duplication is exactly five near-identical `setUp` bodies plus two identical `_touch_repo_file` copies (ToolRuntimeStatsTests, TokenJoinTests, RankingReportTests, OutputContractTests, BashAttributionTests); basis: suite read, 2026-09-28.
- assume the streamed-aggregation and join-prefilter legs stay deferred: the window origin's Trigger section gates them on a live weekly run exceeding about 10 minutes of wall clock or the store growing past roughly 20 GB, and its own build item 2 conditions streamed aggregation on the window filter existing first; this plan lands the filter and records the deferral.

Decision points requiring a grill: the `--days` flag lands now with default all-time while the heavy compute legs stay trigger-deferred (user direction recorded in the authoring prompt: one plan owns both origins; the origin's measured trigger governs the heavy legs, and the rider's invocation is unchanged, so the full scan remains the shipped default; Task 1 and Task 4); the cleanups fold in now because the cleanup origin's trigger is exactly this plan's predicate-code change (the origin prompt records the equivalence; Task 2 and Task 3).

## Gist & Examples

TLDR: the miner learns an optional day window (default all-time, rider untouched), the predicates helper loses a dead parameter, the test suite's five copies of fixture setup become one mixin, and the origin's expensive remaining legs are recorded as trigger-gated deferrals.

Before: every run scans the whole store and the suite repeats the same four-line setup in five classes. After: `--days 7` touches only the last week's rows (hermetically proven with a mocked clock), a covering `--days` run is byte-identical to no flag at all, and `--days 0` is rejected at the parser.

Examples:

- A windowed run over the pinned fixture (tool rows on three days, one exactly at the computed bound) with `--days 2` reports three day rows, because the row exactly at the bound is included, and the digest heading reads `3 day(s) in window`.
- The same fixture with `--days 3` prints stdout JSON byte-identical to the unflagged run (behavior-neutrality witness).
- After Task 2, `grep -c days_count scripts/tool_runtime_stats.py` prints 6; the two removed occurrences are the `_predicates` parameter and its single call site.

## Evaluation Criteria

**Quality dimensions:**

- layer discipline: the window filter lives only in the store-access layer (`connect_read_only` untouched; `bash_command_slugs`, `collect_day_rows`, `collect_day_summaries` gain the bound); aggregation (`window_rows`, `build_rankings`), predicates, and render code are untouched by Task 1.
- behavior neutrality: with no `--days` (and with a `--days` covering the fixture), stdout JSON is byte-identical; SQL grows its bound clause only when the bound is not None.
- reconciliation-exact allocation: even under a window, a row's token share divides by its turn's whole joined count; the join-shape reads are never windowed.
- single-home cleanup: after Task 3 the suite defines `TemporaryDirectory` once, `_touch_repo_file` once, and `setUp` once (the mixin); all six test classes declare the mixin.
- deferral honesty: Task 4 records the streamed-aggregation and join-prefilter disposition with the origin's measured trigger, changing no bytes.

**Done when:**

- `--days N` (N at least 1 and at most `MAX_WINDOW_DAYS`, which Task 1 defines as 1,000,000) filters tool rows and summary turns by the computed `started_at` lower bound in the store-access layer; `--days 0`, negatives, and magnitudes above `MAX_WINDOW_DAYS` are rejected by the parser.
- the windowed digest heading reports the windowed day count; the unflagged run's output is unchanged.
- `_predicates` carries no `days_count` parameter; the digest heading and per-day rates still consume `days_count`.
- the suite's fixture setup is single-homed in a shared mixin and the suite is green.
- the deferral disposition for streamed aggregation and the join pre-filter is recorded in the execution landing report.
- the Validation Commands block passes end to end.

**Ship when:**

- a live weekly run's wall clock exceeds about 10 minutes or the store grows past roughly 20 GB (the origin's measured trigger): implement streamed aggregation over windowed cursors and, if the part scan still dominates, the batched join pre-filter, on the surfaces this plan's deferral names (human-owned sequencing; recorded disposition, not this plan's checklist).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/tool_runtime_stats.py`

**Tests:**

- `scripts/test_tool_runtime_stats.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- the weekly rider's invocation and the maintenance skill body (`agents/skills/maintenance/SKILL.md`); reason: the rider stays bare by design, the plan changes no caller.
- streamed aggregation and the join pre-filter implementation; reason: trigger-gated deferral recorded by Task 4, the origin's own sequencing.
- the store schema contract (`require_tables`, `PINNED_COLUMNS`) and the ranking or predicate threshold constants (`FILING_*`, `JUDGMENT_FREE_MIN_RATIO`); reason: no task changes them.
- other scripts and suites; reason: no task touches them.

## Validation Commands

RED-today witness (recorded at authoring, 2026-09-28, at leg level): commands 1, 2, 4, and 5 are RED on today's tree (`--days`, `_positive_days`, `_now_ms`, and the new signatures are absent; `days_count` occurs on 8 lines, not 6; `TemporaryDirectory()` occurs 5 times, `_touch_repo_file` is defined twice, `def setUp` five times, and no test class declares the mixin). Command 3's suite leg is GREEN today (42 tests OK) while its `DaysWindowTests` pin is RED until Task 1's RED item lands the class. Command 6's em-dash file scan is GREEN today (the plan file carries no em-dash) while its BASE guard is RED until Task 1's first item records BASE.

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. The --days flag exists on the run subcommand with its validation, clock seam, and bare-form default (Task 1).
test "$(grep -cF '"--days"' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: --days flag missing"; exit 1; }
test "$(grep -cF 'def _positive_days(value: str) -> int:' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: positive-days validation missing"; exit 1; }
test "$(grep -cF 'def _now_ms() -> int:' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: now seam missing"; exit 1; }
test "$(grep -cF 'parser.set_defaults(command="run", days=None)' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: bare-form days default missing"; exit 1; }

# 2. The window bound reaches all three store-access helpers with the pinned signatures (Task 1).
test "$(grep -cF 'def bash_command_slugs(conn: sqlite3.Connection, prefixes: tuple[Path, ...], started_after_ms: int | None = None)' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: bash_command_slugs signature"; exit 1; }
test "$(grep -cF 'def collect_day_rows(conn: sqlite3.Connection, repo_root: Path, started_after_ms: int | None = None)' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: collect_day_rows signature"; exit 1; }
test "$(grep -cF 'def collect_day_summaries(conn: sqlite3.Connection, report_dates: set[str] | None = None, started_after_ms: int | None = None)' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: collect_day_summaries signature"; exit 1; }
test "$(grep -cF 'started_after_ms = None if args.days is None else _now_ms() - args.days * 86_400_000' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: run_collection bound computation missing"; exit 1; }

# 3. The hermetic suite is green (Task 1 window tests grow the count above the 42-test baseline).
( cd "$REPO" && PYTHONPATH=scripts python3 -m unittest scripts.test_tool_runtime_stats ) >/dev/null 2>&1 || { echo "FAIL: hermetic suite not green"; exit 1; }
test "$(grep -cF 'class DaysWindowTests' "$REPO/scripts/test_tool_runtime_stats.py")" -eq 1 || { echo "FAIL: window test class missing"; exit 1; }

# 4. The dead parameter is gone and the kept consumers survive (Task 2).
test "$(grep -c 'days_count' "$REPO/scripts/tool_runtime_stats.py")" -eq 6 || { echo "FAIL: days_count count not 6"; exit 1; }
test "$(grep -cF 'def _predicates(tool: str, entry: dict) -> dict:' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: _predicates signature not collapsed"; exit 1; }
if grep -qF 'def _predicates(tool: str, entry: dict, days_count: int)' "$REPO/scripts/tool_runtime_stats.py"; then echo "FAIL: dead parameter still present"; exit 1; fi
test "$(grep -cF "rankings['days_count']" "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: heading consumer lost"; exit 1; }
test "$(grep -cF 'rankings["days_count"]' "$REPO/scripts/tool_runtime_stats.py")" -eq 1 || { echo "FAIL: per-day rate consumer lost"; exit 1; }

# 5. Fixture setup is single-homed in the shared mixin (Task 3).
test "$(grep -c 'tempfile.TemporaryDirectory()' "$REPO/scripts/test_tool_runtime_stats.py")" -eq 1 || { echo "FAIL: fixture setup not single-homed"; exit 1; }
test "$(grep -cF 'def _touch_repo_file' "$REPO/scripts/test_tool_runtime_stats.py")" -eq 1 || { echo "FAIL: _touch_repo_file not single-homed"; exit 1; }
test "$(grep -c 'def setUp' "$REPO/scripts/test_tool_runtime_stats.py")" -eq 1 || { echo "FAIL: setUp not single-homed"; exit 1; }
test "$(grep -cE '^class [A-Za-z]+Tests\(StatsFixtureMixin, unittest\.TestCase\):' "$REPO/scripts/test_tool_runtime_stats.py")" -eq 6 || { echo "FAIL: test classes not on the mixin"; exit 1; }

# 6. Em-dash cleanliness, scoped to what this plan creates and adds (rule 28). BASE is
# recorded by Task 1's first item before any task commit; the unset guard keeps a
# missing base from silently scanning nothing.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-p62-tool-runtime-stats-tail.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
test -n "$BASE" || { echo "FAIL: BASE not recorded (Task 1 first item)"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE" ) || { echo "FAIL: em-dash in added lines"; exit 1; }
```

### Task 1: Add the --days window bound to the store-access layer

Files:

- `scripts/tool_runtime_stats.py`
- `scripts/test_tool_runtime_stats.py`

- [ ] Record the base revision for validation command 6 in the run notes: `BASE="$(git rev-parse HEAD)"`, executed before any task commit of this run. [class: REPOSITORY_TEST]
- [ ] RED: add a plain `class DaysWindowTests(unittest.TestCase)` with today's setup style (module, tmp dir, tmpdir, base; the mixin collapse is Task 3's job) and four tests; every invocation passes `--facts` pointing at an absent path inside the test tmp dir and an explicit `--repo-root` (a scratch dir inside the tmp dir), so the new tests read no ambient facts document and spawn no git subprocess. Each clock-dependent test mocks the clock with `mock.patch.object(module, "_now_ms", lambda: <fixed ms>)` where the fixed now is `_ms(2026, 9, 23, 18)`; all four tests mock it, including the covering-window test (b), and the fixed now is deliberately off every row's `started_at` timestamps (the one deliberate bound collision is the at-bound row below, which pins the inclusive clause). (a) `test_days_window_filters_older_rows`: the store carries tool rows at day1 noon `_ms(2026, 9, 21)` with tool Read (below the bound, absent; this row completes at day2 noon, making it the completed-at straddler the absent-pairs assertion kills the column mutant with), exactly at the bound `_ms(2026, 9, 21, 18)` with tool Edit (present; the computed bound for `--days 2` equals this value), one millisecond below the bound with tool Grep (absent), day2 noon with tool Edit (present), and day3 noon with tool Edit (present); every row completes at its `started_at` plus one second except the day1-noon Read straddler above; run with `["run", "--store", ..., "--out-root", ..., "--facts", ..., "--repo-root", ..., "--days", "2"]` and assert the report's (date, tool) pair set is exactly {(day1, Edit), (day2, Edit), (day3, Edit)} (the boundary row included, pinning the inclusive `>=`), the absent rows' pairs (day1, Read), (day1, Grep), and any straddler-derived pair disjoint from that set (their tool names are pinned so the absent-pairs assertion is writable), and the digest artifact's time-ranking heading contains `3 day(s) in window`; (b) `test_days_window_covering_is_behavior_identical`: the same store run with `--days 3` into a fresh out-root prints stdout JSON byte-identical to an unflagged run into another fresh out-root; (c) `test_days_rejects_invalid_values`: `module.main(["run", "--days", "0"])` raises `SystemExit` with code 2 AND the parser error text names the days validation (capture stderr; this assertion fails today because the unrecognized-argument text names nothing), and `module.main(["run", "--days", "1000001"])` fails the same way (above `MAX_WINDOW_DAYS`); (d) `test_days_window_summary_and_share_cohort`: a fresh minimal store whose in-window tool rows exist only on day3, plus an out-of-window turn (started day1 noon) carrying tokens and a straddling turn with two joined tool rows, one below the bound and one on day3; the summary keys equal exactly {day3} (the no-summary-filter mutant adds day1 and fails), the day3 row's token share equals half the straddling turn's tokens (the whole-store joined count), and the day3 summary's token sums exclude the out-of-window turn's tokens, pinning the cohort semantics. Run → expect RED (no `--days` support yet; test (c) is RED today on its error-text assertion, not its exit code). [class: REPOSITORY_TEST]
- [ ] In `scripts/tool_runtime_stats.py`: add `import time` to the import block; add `def _now_ms() -> int:` returning `int(time.time() * 1000)`; add `def _positive_days(value: str) -> int:` parsing the int and raising `argparse.ArgumentTypeError` for values below 1 or above the named module constant `MAX_WINDOW_DAYS = 1_000_000` (comfortably inside the sqlite int64 range, so the bound can never reach the bind overflow); the error message refers to the day window in prose and must not contain the literal `"--days"` (validation command 1 counts that literal); add the argument on the `run` subparser only in `build_parser` (`run.add_argument("--days", type=_positive_days, default=None, help="optional day window: aggregate only rows started within the last N days (default: all time)")`) and extend the top-level defaults line to `parser.set_defaults(command="run", days=None)` so the rider's bare no-subcommand form still resolves `args.days` to `None`; every misplaced position (including `--days` before the subcommand) then fails loudly as an unrecognized-argument error instead of silently no-opping. [class: IMPLEMENTATION_REQUIRED]
- [ ] Thread the bound through the store-access layer with exactly the pinned signatures from validation command 2: `run_collection` computes `started_after_ms = None if args.days is None else _now_ms() - args.days * 86_400_000` once and passes it to `collect_day_rows` and `collect_day_summaries`; `collect_day_rows` passes it to `bash_command_slugs`; `bash_command_slugs` appends ` AND tu.started_at >= ?` with the bound parameter to its tool-usage query only when the bound is not None; `collect_day_rows` appends ` WHERE started_at IS NOT NULL AND started_at >= ?` to its tool_usage query only when the bound is not None; `collect_day_summaries` appends the same clause shape to its turn_usage query only when the bound is not None. The turn-token read and both joined-count reads stay unfiltered (cohort semantics: a row's share divides by its turn's whole joined count). Keep the python-side `started_at is None` skip guard. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation commands 1, 2, and 3 (flag and seams present, signatures pinned, suite green with the four new window tests) [class: REPOSITORY_TEST]
- [ ] Commit: `stats: add --days window bound to the tool runtime stats miner` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Drop the dead window-day-count threading from the predicates helper

Files:

- `scripts/tool_runtime_stats.py`

- [ ] Change `_predicates` to `def _predicates(tool: str, entry: dict) -> dict:` (drop the `days_count` parameter; the body is unchanged, the frequent predicate already reads each entry's own active days) and drop the argument from the single call site in `build_rankings`. `window_rows` keeps returning `(window, days_count)` and `build_rankings` keeps `days_count` in its returned rankings dict: the digest heading and the per-day rate denominators are the kept consumers (validation command 4 pins both). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 4 (count exactly 6, collapsed signature once, dead signature absent, both digest consumers present one per pin) and command 3 (suite green; the existing predicate tests exercise the new signature) [class: REPOSITORY_TEST]
- [ ] Commit: `stats: drop the dead window-day-count threading from predicates` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Collapse the duplicated per-class fixture setup into a shared mixin

Files:

- `scripts/test_tool_runtime_stats.py`

- [ ] Add `class StatsFixtureMixin` above the test classes: a `setUp` that loads the script module, creates one `TemporaryDirectory` with `addCleanup`, sets `self.tmpdir` and `self.base = _ms(2026, 9, 21)`, and creates `self.repo` unconditionally (an empty scratch repo dir harms no class and deletes a config knob with zero behavioral difference); plus the single `_touch_repo_file` helper (body identical to today's two copies). Convert all six test classes (the five existing plus `DaysWindowTests`) to `class <Name>Tests(StatsFixtureMixin, unittest.TestCase):` with no per-class `setUp`; `OutputContractTests` carries its leak canary as the class attribute `leak = "PW-SYNTHETIC-LEAK-CANARY"`; replace `Path(self.tmp.name)` reads with `self.tmpdir` where the classes used the longer form; per-class counter attributes (`_store_counter`, `_fixture_counter`) stay per-class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 5 (four single-home pins: `TemporaryDirectory()` once, `_touch_repo_file` once, `setUp` once, six classes on the mixin) and command 3 (suite green, no behavior change) [class: REPOSITORY_TEST]
- [ ] Commit: `stats: collapse duplicated fixture setup into shared test helpers` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Record the heavy-leg deferral and run the full block

Files:

- none (record-only task; no bytes change)

- [ ] Record in the run log and the final landing report: streamed aggregation and the join pre-filter stay deferred behind the window origin's measured trigger (live weekly wall clock above about 10 minutes, or the store above roughly 20 GB, whichever comes first); when the trigger fires, the surfaces are the miner's `collect_day_rows` row loop (streamed cursor aggregation) and `bash_command_slugs` (batched join pre-filter), and the weekly rider's invocation remains unchanged until a caller deliberately passes `--days`. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the full Validation Commands block (rule 21 interim expectation: every command passes at this point) [class: REPOSITORY_TEST]
