# Backlog: Edit-failure churn from read-discipline gaps (6.3% of all edits fail)

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: medium

Workflow: backlog

## What was witnessed

Edit is the highest-failure tool in the corpus. tool_usage over 30 days: 820 Edit errors on 13,065 calls (6.3%), decomposing as 408 "File has not been read yet", 187 "File has been modified since read", 18 no-op edits (old_string == new_string), 15 multi-match refusals. The 7-day log window independently shows 58 not-read-yet + 49 modified-since-read. Write adds 50 not-read-yet + 19 modified-since-read of its own. Each failure costs a retry turn plus a re-read; at ~13k edits/month this is the largest mechanical turn tax after provider rate limits.

Root causes: (a) implement workers (fresh subagent context, or post-compaction) attempt edits on files their current context never Read; (b) peer/concurrent sessions mutate the working tree between a Read and its Edit - the known parallel-session hazard in this setup; (c) plan pins and prose blocks drift from the file bytes after folds.

Related: 2026-09-18-overlapping-execution-children-worktree-isolation removes much of class (b) structurally; this item covers the behavioral half.

## Suggested fix

Skill-level pins (no PreToolUse hook - the hot-path budget was explicitly rejected in the 2026-09-18 harness triage):

1. In the execute-plan implement/batch contract and the done contract: read-before-edit is mandatory per file per session; after any external-change signal (peer commit, fold, formatter), re-Read before retrying the edit.
2. Worker prompts for batch launches carry the pin explicitly so fresh subagent contexts do not inherit stale "already read" beliefs from the parent.

## Acceptance

- Edit error rate below 2% over a 7-day window (from 6.3%).
- Zero "File has not been read yet" failures inside single-owner runs (the class should be fully eliminated by the pin; only peer-interference classes remain).
