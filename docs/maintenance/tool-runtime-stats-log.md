# Tool runtime stats log

Durable aggregates-only log for the weekly measurement rider (maintenance Step 7). One section per run; created by the executing run of the `2026-09-22-tool-script-runtime-statistics` plan. Aggregates only: counts, durations, tool and script names, token sums; never prompts, message content, or foreign paths.

## 2026-09-23 run 20260923T025944 (collected date range 2026-08-24 through 2026-09-23, 31 days, full store history as of this run, host-wide)

- Top time-loss rows (window totals): Agent 4,877 calls, 261 errors, 1,717,199 s total (about 55,394 s/day host-wide across parallel sessions, mean about 352 s per call); TaskOutput 206 calls, 5 errors, 47,257 s; AskUserQuestion 61 calls, 2 errors, 42,889 s; Bash unattributed bucket 24,280 calls, 19 errors, 27,555 s; Bash/manifest.md 754 calls, 19,167 s; Bash/done-lock.sh 2,818 calls, 3 errors, 11,267 s.
- Day token summaries: about 11.68 billion input tokens and 101.1 million output tokens joined to tool turns across the window; est_no_judgment_token_share stayed between 0.00 and 0.0183 per day (single-joined-row turns are rare on this host; sessions join many tools per turn).
- Scriptable candidates: none cleared the filing threshold (total >= 300 s/day, or mean >= 10 s at >= 50 calls/day). Every high-cost row failed the judgment-free predicate (single-joined-row call ratio 0.00 to 0.05 against the 0.80 bar); unattributed Bash volume aggregates as `other` by the repo-anchor contract.
- no-action: below threshold; top row Agent measured at 1,717,199 s across the 31-day window (about 55,394 s/day, 5.4 percent error rate, single-joined-row ratio 0.00), so no replacement backlog item is filed from this run.
- Trend: baseline run for the report home; no comparable prior report exists (the two immediately preceding same-day runs were implementation calibration runs minutes earlier, not weekly measurements).
- Retention: the report home keeps the newest 8 run-stamped artifact pairs per the miner's retention line.
