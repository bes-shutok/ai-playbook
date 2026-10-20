# Tool runtime stats log

Durable aggregates-only log for the weekly measurement rider (maintenance Step 7). One section per run; created by the executing run of the `2026-09-22-tool-script-runtime-statistics` plan. Aggregates only: counts, durations, tool and script names, token sums; never prompts, message content, or foreign paths.

## 2026-09-23 run 20260923T025944 (collected date range 2026-08-24 through 2026-09-23, 31 days, full store history as of this run, host-wide)

- Top time-loss rows (window totals): Agent 4,877 calls, 261 errors, 1,717,199 s total (about 55,394 s/day host-wide across parallel sessions, mean about 352 s per call); TaskOutput 206 calls, 5 errors, 47,257 s; AskUserQuestion 61 calls, 2 errors, 42,889 s; Bash unattributed bucket 24,280 calls, 19 errors, 27,555 s; Bash/manifest.md 754 calls, 19,167 s; Bash/done-lock.sh 2,818 calls, 3 errors, 11,267 s.
- Day token summaries: about 11.68 billion input tokens and 101.1 million output tokens joined to tool turns across the window; est_no_judgment_token_share stayed between 0.00 and 0.0183 per day (single-joined-row turns are rare on this host; sessions join many tools per turn).
- Scriptable candidates: none cleared the filing threshold (total >= 300 s/day, or mean >= 10 s at >= 50 calls/day). Every high-cost row failed the judgment-free predicate (single-joined-row call ratio 0.00 to 0.05 against the 0.80 bar); unattributed Bash volume aggregates as `other` by the repo-anchor contract.
- no-action: below threshold; top row Agent measured at 1,717,199 s across the 31-day window (about 55,394 s/day, 5.4 percent error rate, single-joined-row ratio 0.00), so no replacement backlog item is filed from this run.
- Trend: baseline run for the report home; no comparable prior report exists (the two immediately preceding same-day runs were implementation calibration runs minutes earlier, not weekly measurements).
- Retention: the report home keeps the newest 8 run-stamped artifact pairs per the miner's retention line.

## 2026-10-04 run 20261004T183348 (weekly-measurement-rider, scheduler turn 2026-10-04)

- Window: 31 days (2026-09-04 through 2026-10-04); report at docs/tmp/tool-runtime-stats/tool-runtime-stats-20261004T183348.md (retention keeps the newest 8 pairs).
- Time ranking (total seconds per active day): Agent 3,228,937 s (6,306 calls, 104,159 s/day, 8.1 percent error rate, judgment required); TaskOutput 114,854 s; unattributed Bash/other 81,653 s (53,157 calls); test_execute_plan_runtime.py 13,093 s; test_release_skill_selftest.py 1,042 s.
- Token ranking: Bash/other 4.23B, Read 2.65B, Edit 1.80B, Bash/SKILL.md 1.08B, Agent 1.06B (estimated no-judgment share per day summaries).
- Error ranking (calls >= 50): CronUpdate 19.7 percent (12/61), CronCreate 10.7 percent (45/419), Agent 8.1 percent (513/6306), Edit 6.3 percent (1110/17495), Skill 2.6 percent.
- Scriptable candidates: none cleared the filing threshold (total >= 300 s/day, or mean >= 10 s at >= 50 calls/day).
- no-action: below threshold; top row Agent measured at 3,228,937 s across the 31-day window (about 104,159 s/day, 8.1 percent error rate, judgment required), so no replacement backlog item is filed from this run.
- Review-metrics pass: FAILED this run (scripts/summarize_review_stats.py raised TypeError: 'int' object is not iterable over a sidecar findings field); fail-open, no metrics-log section appended; the rider state record carries last_result and the consult's one-day failure advance.

### Throughput

- Retention bound: the scheduler state file keeps the last 20 children[] entries; per-kind counts below are a lower bound over that window, not a true period total.
- Entries by recorded kind over the window: author/authoring-family entries 12 (of which 10 record a completed landing with worktree+branch+claim cleanup, 1 is the in-session authoring run of this turn recorded pending at survey time and completed at closeout, 1 survey-only); execute-family entries 0 in the window (the window's execution completions predate it); legacy free-text kind/outcome forms 18 entries carried verbatim from before the enum convention; formally-enumerated kinds 2.
- Authoring completions in the window (evidenced by the certification oracle over the landed plan bytes): 6 (landing receipts 160e85a5, b32dfc64, 083d0db3, 9f6981e4, 9de75c8b, 2c94d008). Execution completions in the window (evidenced by target plan archived): 0 in-window (mrbf/docs-branch/cnxe landing receipts d06cb8f1/a58f98ef/3032e750 sit outside the 20-entry window and are cited from the git log, not counted).
- Failure and park entries: entries whose outcome records failed 0; entries whose outcome_reason records a park 0; standing state at report time: turn_error null, pending_dispatch SET (registry task friction-audit parked: a live peer authoring session held the authoring lane for audit purposes at decision time), pending_rearm null, alert null, consecutive_failures 0.
- Queue depth at report time: ready prompt-log entries 10, plan-uncovered open backlog items 20, open top-level plans 1 (live counts, no retention bound).

## 2026-10-12T132741 run (weekly rider, sess_9f5841ba)

- Window: 31 active day(s) through 2026-10-12; report docs/tmp/tool-runtime-stats/tool-runtime-stats-20261012T132741.md
- Time ranking top row: Agent total=3,694,997 s (6,147 calls, 198.3 calls/day, error rate 10.2 percent; judgment required, not scriptable)
- No-action verdict: no candidate cleared the filing threshold (total >= 300 s/day, or mean >= 10 s at >= 50 calls/day); the top measured row (Agent, above) requires judgment, so no replacement shape is filed this week.
- Review-metrics pass: report review-metrics-20261012T132741.md under ~/.ai-playbook/review-telemetry/reports/; 1,977 loops, 2,519 legacy-bucket sidecars, 57 malformed-finding skips; ready rate r1 0.16, r2 0.26, r3 0.24, decaying to 0.00 by r16.

### Throughput

Lower bound over the scheduler state file's last-20 children[] retention window:

- By kind: authoring-kind 9 (authoring 5, author 3, authoring-landing-drain 1), execute 6, untyped legacy entries 5; audit/retriage 0 in window.
- Evidenced outcomes: complete (including complete-authoring-pending-landing and executed-landed-in-session) 10; progress 2; stood-down (evidenced stop) 1; pending 1 (this turn's in-session authoring entry).
- Failure/park proxy: 0 failed entries in the window; standing state at report time: turn_error=interrupted-manifest-census-growth (drain alarm, 5 dispositions executed this turn), pending_dispatch=memory-index-audit (retained per D-5), pending_rearm null. Proxy decision: the state file keeps no per-turn error ledger, so the retention-window failure and park entries stand in for the manual-interventions measure.
- Queue depth: ready prompt-log entries 15 (12 PLAN-PROMPTS + 3 EXEC-PROMPTS), plan-uncovered open backlog items 163, open top-level plans 1 (live reads, no retention bound).

## 20261020T121209 run (weekly rider)

- Window: 31 active day(s) through 2026-10-20; report docs/tmp/tool-runtime-stats/tool-runtime-stats-20261020T121209.md
- Time ranking top row: Agent total=3,479,804 s (6,007 calls, 193.8 calls/day, 112,251.7 s/day, error rate 9.9 percent; judgment required, not scriptable)
- Token ranking: Bash/other 5.32B, Read 2.94B, Edit 1.77B, Bash/SKILL.md 1.40B, Agent 1.15B (estimated no-judgment share per day summaries).
- Error ranking (calls >= 50): CronCreate 13.7 percent (48/351), Agent 9.9 percent (596/6007), Edit 6.8 percent (991/14499), Skill 3.9 percent (38/982), TaskOutput 2.5 percent (15/600).
- Scriptable candidates: none cleared the filing threshold (total >= 300 s/day, or mean >= 10 s at >= 50 calls/day).
- no-action: below threshold; top row Agent measured at 3,479,804 s across the 31-day window (about 112,252 s/day, 9.9 percent error rate, judgment required), so no replacement backlog item is filed from this run.
- Review-metrics pass: report review-metrics-20261020T121209.md under ~/.ai-playbook/review-telemetry/reports/; 1,270 loops, 1,532 legacy-bucket sidecars, 41 malformed-finding skips.

### Throughput

Lower bound over the scheduler state file's children[] retention window (the documented bound is the last 20 entries; the array currently holds 46 entries, so the counts below are over the retained window and remain a lower bound over the true period total):

- By kind: author 24, exec 14, authoring 1, adhoc 2, scheduler 1, untyped legacy status-only entries 4 (LANDED x3, HELD x1).
- Evidenced outcomes: authoring completions 15 (14 evidenced by the certification oracle over landed plan bytes, 1 close-origins completion evidenced by its adjudication review ready=yes with no landed plan); execution completions 11 (target plan archived); legacy status-only LANDED entries 3; adhoc landing 1; scheduler restart sweep 1; unevidenced complete entries 4; evidenced stops (stood-down/superseded/retired) 5; failure 1; progress 1; pending/in-flight 2 (live peer entries at report time); empty entry 1; legacy HELD 1.
- Failure and park entries: entries whose outcome records failed 1 (headless model-creation failure at fire; mandate discharged in-session by the operator); entries recording a parked recovery 3 (two gate-removal teardown parks standing on the series-token gap row, one ad-hoc run stood down before landing with its entry reopened); standing state at report time: turn_error null, pending_dispatch null, pending_rearm null, alert null, consecutive_failures 0. Proxy decision: the state file keeps no per-turn error ledger, so the retention-window failure and park entries stand in for the origin's manual-interventions measure.
- Queue depth at report time: ready prompt-log entries 12 (7 PLAN-PROMPTS of 8 with 1 frozen + 5 EXEC-PROMPTS), plan-uncovered open backlog items 84 (90 open top-level, 6 covered by open plans), open top-level plans 13 (live counts, no retention bound).
