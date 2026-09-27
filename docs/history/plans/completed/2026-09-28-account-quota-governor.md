# Plan: Account-level quota governor (shared pressure state, fleet consult, log-mined metrics)

Backlog origin: docs/history/backlog/2026-09-28-account-level-quota-governor.md
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-account-quota-governor-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Turn the per-repo quota probe into an account-level governor: one shared host state file every repository's automations read and update, a four-class pressure evaluator on top of the probe's uniform limit contract, the maintenance loop's dispatch decisions consulting the pressure class, and a metrics mining pass over the daily CLI log so the thresholds are calibrated from measured quota-event data instead of guesses. After this plan lands, automation load scales with live account pressure, a standing reserve protects interactive user work, an exhausted window parks the lanes loudly with the reset time, and the maintenance-autonomous-pipeline item can consume one pinned contract instead of inventing its own.

The contract the pipeline item (and any other consumer) builds on, pinned by this plan:

- Class vocabulary: `abundant`, `tightening`, `constrained`, `exhausted`, plus `unknown` (unusable inputs; fail-open, never read as abundant).
- Shared state: `~/.ai-playbook/runtime/quota-governor-state.json`, schema version 1 (keys pinned in Task 1), written only under the lock file `~/.ai-playbook/runtime/quota-governor.lock` via pid-unique tmp plus atomic replace; a writer finding a stored version greater than its own refuses to write.
- Freshness: a state read older than 30 minutes reads as `unknown`.
- Consult CLI: `python3 scripts/quota_governor.py --consult` (repo-local copy first, then the deployed home copy `~/.ai-playbook/scripts/quota_governor.py`) prints the report JSON with per-lane `dispatch` verdicts and exits 0 on every non-usage-error path; parse the JSON, never the exit code.
- Policy ownership: the class-to-dispatch policy table lives in the script only; skill prose describes the classes qualitatively and obeys the verdicts, so the two homes cannot drift.
- Deferred with this plan: the cross-repo fleet child ledger (registration and counting of in-flight automation children across repositories) and threshold auto-tuning; both wait for mined data per the metrics-before-limits direction.

## Terms

- Pressure class: the governor's account-level load classification computed from the probe reading plus mined log evidence; the four origin classes plus explicit `unknown`.
- Episode: one provider rate-limit incident, deduplicated by the bracket-tail token, the third bracket of `context.statusMessage` (measured shape `[1302][Rate limit reached for requests][202609281553418e46a712858843d8]`); a trace id is a long-lived trace context spanning many sessions and dozens of incidents (measured 2026-09-28: 627 all-event status-429 records share 5 trace ids while carrying 126 distinct incident tokens), so raw 429 event counts overstate pressure and trace-id dedup would understate it; failure-family 429 records without a bracket token fall back to a `sessionId:turnId:second-precision-timestamp` key. Episodes are the unit that calibrates thresholds.
- Exhaustion evidence: a failure-family log record citing a usage-quota window (`TOKENS_LIMIT`, the 5-hour primary window; `TIME_LIMIT`, the weekly secondary window the probe's kind map documents) or carrying surfaced provider code 1308 in a sanctioned structured carrier, scoped per surface: the JSONL miner's only reachable carrier is the bracket prefix of `context.statusMessage` on `model.request.failed`/`model.network.failed` records (the measured real shape, today reading `[1302][Rate limit reached for requests][...]` for the sibling code), while the overlay's `tool_usage.error_code` field is the overlay-DB surface's carrier for the same code and is never wired into the JSONL miner (zero occurrences across the seven day files, measured); a bare `1308` substring elsewhere in a record payload is never a carrier (measured: hundreds of incidental numeric payload hits per day). Per the overlay's provider-code-meanings rule, code 1302 (per-request 429) stays in the episode family and the two are never conflated. Measured calibration note: the 7-day log corpus carries zero window citations (no `TOKENS_LIMIT` or `TIME_LIMIT` occurrence) and 25 positive 1308-carrier records on the two failure event types, reading `[1308][Usage limit reached for 5 hour. Your limit will reset at <provider-rendered timestamp>][token]` (10 on 2026-09-22, 4 on 2026-09-24, 11 on 2026-09-25), so the exhaustion arm is measured but rare and its thresholds stay provisional; the measured 1308 records also carry statusCode 429 and reason `rate_limited`, so they satisfy the episode family too and count in both families. The episode family is measured: 258 failure-family records carry status 429 on 2026-09-28 (129 on each failure event type).
- Headroom: 100 minus the primary window's used_percent, in percent.
- Reserve: the standing percent of the primary window held back for interactive user work; the script's named constants are the single home of the verdict floors (the tightening execution verdict requires headroom at or above `RESERVE_PERCENT + 10`, the constrained authoring verdict at or above `CONSTRAINED_AUTHORING_FLOOR_PERCENT`).
- Refresh: probe reading plus same-window mining, evaluated, then written into the shared state; the exclusive lock covers only the read-merge-stage-replace window (the probe transport and the log mining stay outside it), and a lock-timeout write skips without blocking the turn. Consult: a read-only state read plus policy evaluation, no writes.

## Assumptions

- assume the shared state lives at `~/.ai-playbook/runtime/quota-governor-state.json`, outside every repository; basis: that runtime directory already hosts the host-global budget-guard lock and the resume sentinels, and `~/.ai-playbook/scripts/` is the established deployed-home script root, so both the state and the deployed twin have existing homes.
- assume the policy table lives only in the script while the skill paragraphs name classes qualitatively; basis: duplicated numeric tables in skill prose and script code are the drift pattern the active-simplicity doctrine removes, and the verdicts-are-binding rule keeps the skill's text mechanically decidable without restating numbers.
- assume the fleet concurrency ledger (cross-repo in-flight child registration) is deferred to a metrics-cited follow-up; basis: lessons 443 measure-before-limits and the origin's own "thresholds calibrated from data, not guesses" mandate; the initial classes still regulate load (per-repo lane deferral under tightening and constrained), and the deferred decision is recorded in the Outcome for the pipeline item's contract.
- assume reset-time display derives only from provider epochs via the probe (which normalizes to the host zone); the governor never parses provider-rendered timestamp strings, which absorbs the unlabeled GMT+8 reset-timestamp trap at the probe layer where it is already handled.
- assume the probe script is consumed through import (`quota_window_probe.run_probe`) and never edited by this plan; basis: the probe's uniform limit contract is this plan's input, and the probe's own suite is the compatibility gate.

Decision points requiring a grill: state file home = the host-global runtime directory over a per-repo or XDG path; source: the budget-guard lock and resume-sentinel precedent already living there, 2026-09-28, Task 1; policy table home = the script alone over duplicated skill prose; source: drift risk between two number homes witnessed across the corpus's pin suites, 2026-09-28, Task 3; fleet concurrency ledger = deferred to a metrics-cited follow-up over building it now; source: lessons 443 measure-before-limits plus the origin's calibration mandate, 2026-09-28, Assumptions; exhaustion evidence anchoring = the primary window's reset epoch minus one cadence over a fixed wall-clock lookback; source: an exhaustion line from the previous window must not exhaust the live one, 2026-09-28, Task 1

## Gist & Examples

TLDR: two new scripts give the account one shared, lock-protected pressure state with a four-class evaluator and a log-mining feed, the maintenance skill's dispatch decisions consult the class and obey per-lane verdicts, an exhausted window parks the lanes loudly with the reset time, and the thresholds stay provisional until the mined data justifies tuning them.

**Before (today).** Every automation plans as if it were alone: `scripts/quota_window_probe.py` reads the same account-wide window per repo with no shared state, so repos race one window; the 429 retry-storm shaping and the `rate_pressure` per-repo count react only after a limit response surfaces inside one repo; nothing reserves headroom for interactive work, so maintenance children can consume the window the user's company work needs; the daily CLI log carries rich quota evidence (258 failure-family status-429 records on 2026-09-28 alone, 126 distinct provider incidents) that nothing aggregates; and the pipeline item has no pressure contract to consume.

**After (this plan).** `scripts/quota_governor.py` evaluates `abundant`/`tightening`/`constrained`/`exhausted` from the probe report plus mined evidence, writes the versioned state under `quota-governor.lock`, and answers `--consult` with per-lane verdicts: `abundant` allows both lanes, `tightening` allows authoring and holds execution above the reserve floor, `constrained` defers execution and gates authoring behind its floor, `exhausted` defers both with the host-local reset time, `unknown` (or stale) keeps existing defaults. `scripts/quota_pressure_stats.py` streams the day's log into episode counts (deduplicated by the measured incident token), source splits, and exhaustion events carried only in sanctioned structured carriers, feeding both the evaluator and the state's per-day metrics; refresh mines the previous and current local days and evaluates over their union, so the trailing-hour and window-anchored lookbacks stay correct across local midnight. The maintenance skill's survey snapshot runs the refresh once per turn and records the class per lane; the runtime overlay's Quota leg mirrors the same duty. Example: at 83 percent used with 12 episodes in the trailing hour, the class reads `constrained`, execution defers with the reset time recorded, and an authoring child may run only while headroom stays at or above 30 percent.

**Edge cases.** A probe transport failure fails open: the refresh records `unknown` and the turn keeps its existing defaults, never blocking on quota data. A future schema (stored version greater than the script's) refuses writes instead of clobbering. An exhaustion line logged in the previous window does not exhaust the live window: evidence anchors to the primary window's start (reset epoch minus one 5-hour cadence; probe-less, a trailing-cadence lookback). A stale shared state (older than 30 minutes, for example a host asleep across the window) reads `unknown`, and the fleet degrades to today's per-repo behavior rather than acting on old pressure.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the class boundaries (60/80/95, pause arm, episode rate, window-anchored exhaustion) are each witnessed by a dedicated test; `unknown` is the fail-open answer for every unusable-input combination and never reads as `abundant`.
- consistency: the state schema is version 1 with the exact key set pinned by tests; the policy table exists in exactly one home (the script); the skill's `pressure_class` key is additive under schema 4 with no version bump.
- compatibility: the probe's own suite stays green with the probe untouched; the maintenance skill's existing quota machinery (slugs, `rate_pressure` count, `rate_limited_events`, runtime-fit rule) is unchanged and the governor layers on top.

**Done when:**
- Both new scripts and their hermetic suites exist and pass via the test venv.
- The maintenance skill's three amended spans and the inserted policy paragraph are present at their anchors, and the overlay's Quota leg bullet is present.
- The deployed home twins match the repo copies byte for byte.
- All Validation Commands below exit 0.

**Ship when:**
- None as a release gate; all criteria are repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Tests:**
- `scripts/test_quota_governor.py` *(new; the whole file)*
- `scripts/test_quota_pressure_stats.py` *(new; the whole file)*

**Production code:**
- `scripts/quota_governor.py` *(new; the whole file)*
- `scripts/quota_pressure_stats.py` *(new; the whole file)*
- `agents/skills/maintenance/SKILL.md` *(only the three appended sentences and the inserted Account governor policy paragraph named in Task 3; every other paragraph, guard, and state-field rule is frozen)*
- `agents/skills/maintenance/zcode.md` *(only the inserted Quota leg bullet named in Task 4; frozen otherwise)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/quota_window_probe.py` and its suite; reason: the probe is consumed through import and its uniform contract is this plan's input; probe edits belong to the probe's own plans.
- `scripts/execute_plan_resume_watcher.py` and the budget-guard flag machinery; reason: the guard flag backstop is a separate mechanism with its own lock and lifecycle; this plan adds a state file beside it, not into it.
- The per-repo `rate_limited_events` / `rate_pressure` machinery in the maintenance skill; reason: it stays as the local proxy and defense in depth when the shared state is unreadable; the origin regulates fleet load additively and does not retire local reactive arms.
- Threshold values other than the provisional constants this plan documents; reason: calibration waits for mined data per the recorded deferred decision.

## Validation Commands

Stage note: the authoring-time records this plan requires are recorded here: the pre-round structural gate ran clean before round 1 (pre-round exit 0), the RED-today executions ran against current bytes with measured outcomes (G1, G1b RED-today: all four new script and test paths are absent today; G2 RED-today: the string `quota_governor` occurs zero times in both skill files today, so all three appended sentences and the inserted paragraph are absent; G2b RED-today for the same reason; G4 RED-today: the consult CLI cannot exist before Task 1), and the mechanical audit (pinned spans once each in their target files, bash -n over this block) ran before round 1. The venv python resolves the test venv the lib suites use.

```bash
# G1: the governor core exists and its suite is green.
test -f scripts/quota_governor.py || { echo "G1 fail: quota_governor.py missing"; exit 1; }
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_quota_governor.py -q || { echo "G1 fail: governor suite red"; exit 1; }

# G1b: the log miner exists and its suite is green.
test -f scripts/quota_pressure_stats.py || { echo "G1b fail: quota_pressure_stats.py missing"; exit 1; }
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_quota_pressure_stats.py -q || { echo "G1b fail: miner suite red"; exit 1; }

# G2: the maintenance skill carries the three sentences AT THEIR ANCHORS plus
# the policy paragraph AT ITS POSITION (adjacency pins; presence anywhere is
# not enough: the policy paragraph's neighbors are witnessed by the same
# python probe style as G2b).
grep -qF "the state shape's percent_used and minutes_to_reset are this snapshot's transcription of those two keys. Account governor refresh (2026-09-28, account-quota-governor plan): when the harness is supported" agents/skills/maintenance/SKILL.md || { echo "G2 fail: snapshot refresh sentence not at its anchor"; exit 1; }
grep -qF "the records are written with the turn's \`decision\` / \`decision_reason\` in the Step 6 rewrite; the field is additive under schema 4 (no version bump). Each lane additionally carries the additive \`pressure_class\` key" agents/skills/maintenance/SKILL.md || { echo "G2 fail: pressure_class key sentence not at its anchor"; exit 1; }
grep -qF "the decision_reason token remaining the authoritative record. The account governor's pressure class is an additional quota-signal source" agents/skills/maintenance/SKILL.md || { echo "G2 fail: quota-signal source sentence not at its anchor"; exit 1; }
grep -qF "Account governor policy (2026-09-28, account-quota-governor plan): the account-level governor owns one shared host state file" agents/skills/maintenance/SKILL.md || { echo "G2 fail: policy paragraph missing"; exit 1; }
python3 - <<'PY'
import pathlib
lines = pathlib.Path("agents/skills/maintenance/SKILL.md").read_text(encoding="utf-8").splitlines()
nonblank = [j for j, l in enumerate(lines) if l.strip()]
for i in nonblank:
    if lines[i].startswith("Account governor policy (2026-09-28, account-quota-governor plan):"):
        before = [j for j in nonblank if j < i]
        after = [j for j in nonblank if j > i]
        prev_ok = bool(before) and lines[before[-1]].endswith("parks both lanes regardless of slug.")
        nxt_ok = bool(after) and lines[after[0]].startswith("- Run `python3 scripts/quota_window_probe.py`.")
        raise SystemExit(0 if (prev_ok and nxt_ok) else "G2 fail: policy paragraph not between the quota-signal paragraph and the probe bullet")
raise SystemExit("G2 fail: policy paragraph not found")
PY

# G2b: the overlay's Quota leg carries the governor bullet after the probe bullet.
python3 - <<'PY'
import pathlib
lines = pathlib.Path("agents/skills/maintenance/zcode.md").read_text(encoding="utf-8").splitlines()
for i, line in enumerate(lines):
    if line.startswith("- Run `python3 scripts/quota_window_probe.py` and parse its JSON."):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        raise SystemExit(0 if nxt.startswith("- Account governor (2026-09-28, account-quota-governor plan):") else "G2b fail: governor bullet not adjacent to the probe bullet")
raise SystemExit("G2b fail: probe bullet not found")
PY

# G2c: the deployed home twins match the repo copies byte for byte.
shasum -a 256 -c <(shasum -a 256 scripts/quota_governor.py scripts/quota_pressure_stats.py | sed "s|  scripts/|  $HOME/.ai-playbook/scripts/|") >/dev/null || { echo "G2c fail: deployed twins differ"; exit 1; }

# G3: the probe suite stays green with the probe untouched (compatibility).
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_quota_window_probe.py -q || { echo "G3 fail: probe suite red"; exit 1; }

# G4: the consult CLI fails open on an absent state file (exit 0, class unknown).
CONSULT_OUT="$(mktemp -d)/consult.json"
python3 scripts/quota_governor.py --consult --state-path "$(mktemp -d)/governor-state.json" > "$CONSULT_OUT" || { echo "G4 fail: consult exited nonzero on absent state"; exit 1; }
grep -q '"class": "unknown"' "$CONSULT_OUT" || { echo "G4 fail: absent state did not read unknown"; exit 1; }

# G5: the run introduced no em dashes anywhere.
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
```

### Task 1: governor core with the shared pressure state

Files:
- `scripts/quota_governor.py` *(new)*
- `scripts/test_quota_governor.py` *(new)*

- [ ] Implement `scripts/quota_governor.py` (stdlib only, mirroring the probe's pure-core-then-CLI shape): module constants `TIGHTENING_PERCENT = 60.0`, `CONSTRAINED_PERCENT = 80.0`, `EXHAUSTED_PERCENT = 95.0`, `RATE_EPISODES_CONSTRAINED_PER_HOUR = 20`, `RESERVE_PERCENT = 15.0`, `TIGHTENING_EXECUTION_FLOOR_PERCENT = RESERVE_PERCENT + 10`, `CONSTRAINED_AUTHORING_FLOOR_PERCENT = 30.0`, `LOCK_TIMEOUT_SECONDS = 2.0`, `STATE_STALE_SECONDS = 1800`, `STATE_VERSION = 1`, `CADENCE_SECONDS = 5 * 3600`; `evaluate_pressure(probe_report, mining, now)` returns the class: `exhausted` when the probe's `pause_decision` is `pause` with the primary window as the binding, or the primary window's `used_percent` is at or above 95.0, or a mined exhaustion event falls inside the live window (its last timestamp at or after the primary `reset_at_epoch` minus `CADENCE_SECONDS`; with no usable probe, exhaustion events whose last timestamp is within the trailing `CADENCE_SECONDS` count); `constrained` when the primary window's `used_percent` is at or above 80.0 or the trailing-hour episode count reaches 20; `tightening` when the primary window's `used_percent` is at or above 60.0; `abundant` otherwise; all three percent arms and the pause arm classify from the primary window only: a secondary-binding report contributes report-only context to the inputs and reasons and never produces a class by itself (the overlay's defer rule: only a primary-window pause defers; a weekly-scale park is never armed from a secondary reading), and a report with no usable primary window leaves the percent and pause arms inert with the episode and exhaustion arms and the unknown rule governing; `unknown` when the probe report is unusable and the mining is unusable, where mining is usable only when a readable day file yielded at least one parsed record (a missing, empty, or record-free day file is not usable evidence: absence of log data never reads as `abundant`); when episode or exhaustion evidence produces a class on a turn with no usable probe reading, the class still applies and every headroom-gated policy cell resolves as allow with its reason naming the absent reading (fail-open lane behavior over missing numbers) [class: IMPLEMENTATION_REQUIRED]
- [ ] Shared state read/write with the version-1 schema (exact keys: `version`, `updated_at_epoch`, `updated_by`, `pressure` carrying `class`, `computed_at_epoch`, `inputs` with `primary_used_percent`, `primary_minutes_remaining`, `rate_limited_episodes_trailing_hour`, `exhaustion_event_count`, plus `reset_at_epoch`, `reset_at_iso`; `reserve_percent`; `window_samples` as a list of `ts_epoch`/`used_percent` pairs capped at 24 oldest-evicted; `metrics.by_day` capped at the 7 newest days); writes take an fcntl exclusive lock on `<state-dir>/quota-governor.lock` (a re-implementation of the probe's bounded-acquire lock pattern under this pinned name; the probe's private `_shared_guard_lock` helper is never imported, its lock filename is fixed to `budget-guard.lock` inside the probe module), hold that lock only around the read-merge-stage-replace window (the probe transport and the log mining run outside it), stage a pid-unique tmp, and `os.replace` atomically; the state file is written with mode 0600 (the probe's flag precedent: the file carries per-repo attribution); a lock that cannot be acquired within `LOCK_TIMEOUT_SECONDS` skips the write without blocking the turn (not writing is the fail-open direction); a stored `version` greater than `STATE_VERSION` fails closed on both paths: the writer refuses to write and the consult reports `unknown` with that reason (mixed repo-local and deployed-copy deployments must never let an older script clobber or misread a newer schema) [class: IMPLEMENTATION_REQUIRED]
- [ ] `refresh(...)` imports `quota_window_probe.run_probe` for the reading (never forks the transport) with the runtime selected through `quota_window_probe.detect_runtime()` (the probe's own main-path convention; a none or unknown detection degrades the refresh to the fail-open `unknown` class rather than defaulting to a hardcoded runtime), mines the previous and current local days through `quota_pressure_stats.mine_day` and evaluates over the union of the two days' episode timestamps and exhaustion evidence so the trailing-hour and window-anchored lookbacks stay correct across local midnight, appends the binding percent into `window_samples`, merges the current day's mined summary into `metrics.by_day`, evaluates, writes, and prints the consult report (the merge happens inside the same locked read-merge-stage-replace window, so the per-day metrics have a wired producer and `--merge-state` stays as the manual backfill path); the consult builds per-lane `dispatch` verdicts from the policy map: `abundant` allows both lanes; `tightening` allows authoring and allows execution only when headroom is at or above `TIGHTENING_EXECUTION_FLOOR_PERCENT`; `constrained` defers execution and allows authoring only when headroom is at or above `CONSTRAINED_AUTHORING_FLOOR_PERCENT`; `exhausted` defers both lanes with the host-local reset time in the reason; `unknown` allows both lanes with a reason naming the fail-open; a state older than `STATE_STALE_SECONDS` reads `unknown`; CLI flags `--refresh`, `--consult`, `--state-path` (default `~/.ai-playbook/runtime/quota-governor-state.json`), `--log-dir`, `--updated-by` (default `<cwd basename>:<the runtime session identifier when discoverable in the process environment, else the literal unknown>`; no environment variable name is pinned because none exists today, and `--updated-by` is the sanctioned explicit override); exit 0 on every non-usage-error path with the verdict parsed from stdout JSON [class: IMPLEMENTATION_REQUIRED]
- [ ] Tests in `scripts/test_quota_governor.py` (hermetic: injected probe reports, injected mining payloads, temp state paths): one test per class boundary (60/80/95 and the pause arm), exhaustion window anchoring (inside the live window counts, the previous window's line does not, the probe-less trailing-cadence fallback counts), cross-midnight evaluation (evidence logged on the previous local day, evaluated just after local midnight, counts through the union), `unknown` fail-open for unusable probe plus unusable mining (including the missing-day-file cell), episodes-only `constrained` with an unusable probe exercising the headroom-gated cells' allow-with-absent-reading reasons, a none-runtime detection degrading refresh to `unknown`, stale-state `unknown`, corrupt-state `unknown` (invalid JSON, non-mapping, missing version), version-skew on both paths (a greater-version state fails the write and reads `unknown` on consult), a secondary-binding pause with a low binding percent never reading `exhausted` (report-only), a secondary-binding report at 97 percent with no primary window never producing a class from the percent arms, a refresh run merging the mined summary into `metrics.by_day` and appending `window_samples` with a lock-timeout write skipping cleanly (state unchanged), version-refusal refusal, episode-rate `constrained`, every policy verdict cell, the 24-sample and 7-day caps, a two-refresh interlock cell (concurrent refreshes serialize on the lock and both complete), and the consult CLI contract on an absent state file (exit 0, class `unknown`) [class: REPOSITORY_TEST]
- [ ] Run, expect GREEN: `"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_quota_governor.py -q` [class: REPOSITORY_TEST]
- [ ] Commit: `automation: add account-level quota governor core with shared pressure state` [class: IMPLEMENTATION_REQUIRED]

### Task 2: daily-log mining pass for episodes and exhaustion

Files:
- `scripts/quota_pressure_stats.py` *(new)*
- `scripts/test_quota_pressure_stats.py` *(new)*

- [ ] Implement `scripts/quota_pressure_stats.py` (stdlib only): `mine_day(day, log_dir)` streams `zcode-<day>.jsonl` line by line (never loading the file whole); rate-limited episodes are `model.request.failed` or `model.network.failed` records whose `context.statusCode` is 429 or whose `context.reason` is `rate_limited`, deduplicated by the incident-grade bracket-tail token (the third bracket of `context.statusMessage`) with a `sessionId:turnId:second-precision-timestamp` fallback key for records without a bracket token, never by `traceId` (a trace context spans sessions and incidents), each episode keeping its first `timestamp` and its `context.querySource` bucketed `main_turn` | `subagent` | `other`; exhaustion events are the two failure event types (`model.request.failed`, `model.network.failed`) whose payload cites `TOKENS_LIMIT` or `TIME_LIMIT`, or whose surfaced provider code 1308 arrives in the miner's only reachable structured carrier, the bracket prefix of `context.statusMessage` on `model.request.failed`/`model.network.failed` records (measured 1308 message: `[1308][Usage limit reached for 5 hour. Your limit will reset at <provider-rendered timestamp>][token]`; the overlay's `tool_usage.error_code` field is the overlay-DB surface's carrier and is never read by this miner); a bare `1308` substring elsewhere in a record payload never counts (measured: hundreds of incidental numeric payload hits per day); the overlay's provider-code-meanings rule holds: 1302 stays in the episode family, the two codes are never conflated, and a 1308 record that also carries statusCode 429 counts in both families; output JSON `{"day", "rate_limited_episodes", "episodes_by_source", "episode_timestamps" (capped at the 500 newest), "exhaustion_event_count", "last_exhaustion_ts"}`; CLI flags `--day` (default today, host-local), `--log-dir` (default `~/.zcode/cli/log`), `--merge-state` writing the summary into the shared state's `metrics.by_day` under the governor lock with the 7-day pruning, printing the same summary to stdout; a missing day file is an empty summary, never an error (fresh hosts and rotated logs mine to zeros) [class: IMPLEMENTATION_REQUIRED]
- [ ] Tests in `scripts/test_quota_pressure_stats.py` (hermetic fixture log written to a temp dir): two 429 records sharing one trace id but carrying distinct bracket-tail tokens count as two episodes, while eleven records sharing one bracket-tail token stay one episode (the trace id is never the dedup key); a bracket-token-less 429 record deduplicates on the fallback key; the querySource split buckets `main_turn`, `subagent`, and an unknown source into `other`; exhaustion cells carry the measured shapes: a failure record with the measured `[1308][Usage limit reached for 5 hour. ...]` statusMessage bracket prefix counts, a `TOKENS_LIMIT` citation in a failure record counts, a `TIME_LIMIT` citation counts (the weekly secondary window), a failure record whose bracket prefix carries a non-1308 provider code does not count as exhaustion, a record whose payload merely contains the digits 1308 in an unrelated field does not, while a bare 1302 record stays in the episode family; a 1308-carrier record counts in both families (one episode and one exhaustion event); the missing-day file mines to zeros; `--merge-state` prunes to the 7 newest days and is atomic [class: REPOSITORY_TEST]
- [ ] Run, expect GREEN: `"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_quota_pressure_stats.py -q` [class: REPOSITORY_TEST]
- [ ] Commit: `automation: mine rate-limit episodes and exhaustion events from the daily CLI log` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the maintenance skill consults the governor

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] In the Step 1 quota snapshot paragraph, immediately after the sentence ending `the state shape's percent_used and minutes_to_reset are this snapshot's transcription of those two keys.`, append exactly: `Account governor refresh (2026-09-28, account-quota-governor plan): when the harness is supported, the turn additionally runs the account governor refresh once (\`python3 scripts/quota_governor.py --refresh\`, repo-local copy first, then the deployed home copy \`~/.ai-playbook/scripts/quota_governor.py\`; a failed or unusable refresh records the class \`unknown\` and continues, fail-open) and carries the report's \`pressure.class\` into this snapshot and into every lane's \`quota_at_decision\` additive \`pressure_class\` key.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the `quota_at_decision` State-file paragraph, immediately after the sentence ending `the field is additive under schema 4 (no version bump).`, append exactly: `Each lane additionally carries the additive \`pressure_class\` key (the account governor's pressure class at the reading; null when the class itself is unknown, from unusable refresh inputs or an unsupported harness; additive under schema 4, no version bump).` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Quota signal definition paragraph, immediately after the sentence ending `the decision_reason token remaining the authoritative record.`, append exactly: `The account governor's pressure class is an additional quota-signal source recorded through \`pressure_class\`: it never replaces the probe-derived slugs (the probe stays the per-window truth); its load shaping runs through the Account governor policy paragraph below, where the class \`exhausted\` parks both lanes regardless of slug.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert a new paragraph between the Quota signal definition paragraph and the `Run \`python3 scripts/quota_window_probe.py\`.` bullet, reading exactly: `Account governor policy (2026-09-28, account-quota-governor plan): the account-level governor owns one shared host state file (\`~/.ai-playbook/runtime/quota-governor-state.json\`, lock-protected atomic replace, schema version 1) that every repository's automations read and update, so the fleet cooperates on the account-wide window instead of racing it. The turn consults the class through the refresh report or \`python3 scripts/quota_governor.py --consult\` and obeys the returned per-lane \`dispatch\` verdicts; the policy table is owned by the script and never re-stated here, so skill and script cannot drift: \`abundant\` allows both lanes, \`tightening\` holds the execution lane above the reserve headroom floor, \`constrained\` defers execution and gates authoring behind its floor, \`exhausted\` defers both lanes with the reset time (displayed in the host's local zone) recorded in \`decision_reason\`, and \`unknown\` (unusable or stale-past-30-minutes state) keeps the existing defaults, fail-open. A deferred lane parks through the existing \`pending_dispatch\` path with the class and reset time in the record; the standing reserve protects interactive user work, which outranks all automation load by default.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G2's four pins → expect all found [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: consult the account quota governor in dispatch decisions` [class: IMPLEMENTATION_REQUIRED]

### Task 4: runtime overlay bullet and deployed home twins

Files:
- `agents/skills/maintenance/zcode.md`

- [ ] In the Quota leg, immediately after the bullet `- Run \`python3 scripts/quota_window_probe.py\` and parse its JSON.`, insert exactly: `- Account governor (2026-09-28, account-quota-governor plan): after the probe, when the harness is supported, run the account governor refresh once (\`python3 scripts/quota_governor.py --refresh\`, repo-local copy first, then the deployed home copy \`~/.ai-playbook/scripts/quota_governor.py\`) and obey its per-lane \`dispatch\` verdicts; a class \`exhausted\` parks the turn's lanes with the reset time in the record (state: \`~/.ai-playbook/runtime/quota-governor-state.json\`; an unusable refresh keeps the existing defaults, fail-open).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Deploy the home twins and verify byte identity: `cp scripts/quota_governor.py scripts/quota_pressure_stats.py ~/.ai-playbook/scripts/` then `shasum -a 256 scripts/quota_governor.py scripts/quota_pressure_stats.py ~/.ai-playbook/scripts/quota_governor.py ~/.ai-playbook/scripts/quota_pressure_stats.py` expecting each repo copy and its twin to carry the identical digest (host-side deployment; nothing to commit for it) [class: REPOSITORY_TEST]
- [ ] Run G2b's adjacency probe → expect the bullet found at its anchor; run G2c's digest check → expect match [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: wire the account governor into the runtime overlay quota leg` [class: IMPLEMENTATION_REQUIRED]

### Task 5: final validation

- [ ] Run the full Validation Commands block from the repo root → expect every gate green; record the output in the task log [class: REPOSITORY_TEST]

## Origins dispositions

- `docs/history/backlog/2026-09-28-account-level-quota-governor.md` — folded into this plan at execution (squash main 1f404537); origin file deleted.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-28-account-level-quota-governor.md` was deliberately folded into this plan and its per-item file deleted at execution (squash main 1f404537).
