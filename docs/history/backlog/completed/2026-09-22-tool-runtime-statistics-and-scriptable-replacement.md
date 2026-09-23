# Backlog: tool and script runtime statistics to rank time-loss and model-to-script replacement candidates

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-22
Class: harness measurement + efficiency program (user-directed 2026-09-22)

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Driving force

Today nobody can answer "where did the wall-clock go this week?" or "which
repeated model work is deterministic enough to become a script?". The
executed harness triage (2026-09-18/20) adjudicated speed questions by
reasoning alone; its wall-clock ranking (semantic-serial vs implement-loop
vs done-sweep vs hook hot path) was qualitative. The user directive: collect
runtime statistics on tools and scripts so improvements are ranked by
measured loss. Two example shapes the data should surface automatically:

- A tool used hundreds of times a day at ~10s per call is ~tens of minutes
  of pure overhead daily; that is a improvement candidate regardless of
  what the tool does.
- Model turns spent on deterministic work (counting, formatting, scanning,
  sorting, status arithmetic) cost tokens and reliability; each is a
  candidate for replacement by a script or small tool.

## What exists today (build on, do not duplicate)

- The host session store records per-tool usage (tool name, call counts,
  error counts per 30-day windows; previously mined for the edit-failure
  and breakpoint-overflow items) and per-turn token counts (input, output,
  cache read/creation, keyed by session). Read-only SQL access is
  verified working on this host.
- The repo's scripts-over-prose preference and its three-question triage
  test (executed harness-triage plan): is the step deterministic, is it
  frequent, does it need judgment. Today that test is applied ad hoc.
- The parallel-implement-groups contract (same executed plan) governs any
  concurrency work; the language-rewrite rejection (same record) rules out
  answering this with a rewrite.

## What to build

Phase 1, collector (offline mining first; zero hot-path cost by design,
per the executed hook-tax lesson):

1. An offline miner script reads the host session store and emits a
   per-day, per-tool table: call count, error count, mean and p95 duration
   where the store carries timing (or wall-clock deltas derived from event
   timestamps where it does not), and total time = count x mean.
2. Script-level attribution: Bash-tool calls whose command invokes a repo
   or runtime script are attributed to that script slug (parse the command
   line; unknown shapes aggregate as `other`), so per-script totals rank
   alongside per-tool totals.
3. Token attribution: join per-turn token usage with the tool calls in the
   same turn window, giving tokens-per-tool and an estimate of the token
   share spent on turns that produced no judgment (single-tool turns whose
   output is a mechanical transform).
4. Output lands as a durable per-run report (JSON + a short Markdown
   digest) under the resolved tmp dir with a retention line; the miner
   must fail open (missing store or tables: report and exit 0).

Phase 2, analyzer and cadence:

5. A ranking report: top-N by total time per day, top-N by total tokens
   per day, top-N by error rate (with count floor), and a candidates list
   where `scriptable = deterministic AND frequent AND judgment-free`
   (the existing triage test, now applied to measured rows). Each
   candidate row names the tool/script, the measured cost, the proposed
   replacement shape (script, cache, batch, skip), and the estimated
   saving.
6. A weekly cadence (maintenance turn rider, not a new automation) appends
   the digest and files any candidate above a stated threshold as a
   backlog item, so the improvement queue is fed by measurement instead
   of anecdote.

## Ranking metrics (the contract)

- Total time per day per tool/script: count x mean duration. Threshold to
  auto-file a candidate: any row above ~5 minutes/day aggregate, or any
  row above ~10s mean with count >= 50/day (the "hundreds x 10s" shape).
- Token cost per day per tool and the no-judgment token share.
- Error rate with a count floor (error-prone tools are both a time loss
  via retries and a reliability candidate).
- Trend per week (improvement verification: did the fix move the number).

## Acceptance criteria

- The miner produces the per-day per-tool table from the live store on
  this host without writes to the store and without a hot-path hook.
- The ranking report names at least the top three time-loss rows and the
  top three scriptable candidates with measured numbers, not estimates.
- One full loop is demonstrated end to end: measured row, candidate
  filing, replacement landed, before/after trend visible in the next
  report.
- No new always-on hook is introduced (the executed hook-tax decision
  stands); the miner is invoked offline by cadence.

## Non-goals

- No Rust/Go rewrite (rejected on the record 2026-09-18; this program
  measures whether ANY replacement pays before anything is built).
- No behavior change to gates or skills in phase 1 (measurement only).
- No per-call in-repo instrumentation where the host store already
  carries the datum.

## Siblings

- `2026-09-19-edit-failure-churn-read-discipline.md` (same store, error
  half; P40-slim) and `2026-09-19-cache-breakpoint-overflow-token-cost.md`
  (token-noise half; P40-slim) become consumers of this program's report.
- `2026-09-20-turn-usage-token-probe.md` (P37-authored) is the token
  measurement primitive this program's join builds on.
- `2026-09-18-harness-wall-clock-speedups.md` (completed) is the prior
  qualitative triage this program replaces with measurement.

## Closure note (2026-09-23)

Delivered by the executed plan `2026-09-22-tool-script-runtime-statistics`
(archived at `docs/plans/completed/2026-09-22-tool-script-runtime-statistics.md`):
offline read-only miner with per-day per-tool table, repo-anchored Bash script
attribution, per-turn token join with the no-judgment share, stamped JSON and
digest output with keep-newest-eight retention, ranking report with the three
scriptable predicates and filing thresholds, weekly trend against the newest
prior report, and the weekly measurement rider inside the maintenance
scheduler turn. One loop demonstrated end to end on the live host store with
a no-action verdict (no candidate cleared the filing threshold). The
Ship-when cadence evidence (two maintenance turns feeding the improvement
queue) accrues on the host from this point forward. The item's acceptance
criterion "replacement landed" belongs to future candidate backlog items, not
to this measurement program.
