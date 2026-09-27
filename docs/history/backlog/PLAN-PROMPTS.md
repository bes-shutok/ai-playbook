Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root.
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Entries carry repo-relative paths only and no personal or machine-specific data.
- An entry is a prompt for a later authoring turn; the write turn never executes or dispatches its payload.

Entry template (one section per entry):

```
## <short-slug>

Added: <date and provenance>

Origins:
- docs/history/backlog/<origin>.md

Urgency: <judgment: class, witness, relative queue position>

Prompt: <full ready-to-dispatch authoring prompt payload>

Rejected alternatives:
- <one line per rejected alternative, with the reason>
```


## p62-tool-runtime-stats-tail

Added: 2026-09-27 (migrated from the retired untracked prompt scratch; first filed 2026-09-23)

Origins:
- docs/history/backlog/2026-09-23-tool-runtime-stats-window-bounded-mining.md
- docs/history/backlog/2026-09-23-tool-runtime-stats-post-verification-cleanups.md

Urgency: Low; unranked tail outside the pinned dispatch order: the oldest delivered-but-unauthored prompt still open (first filed 2026-09-23), kept available after the ranked queue.

Prompt: using the plans skill, author one plan (authoring only, do not execute): tool runtime statistics tail, window-bounded mining and dead-parameter cleanup. Read each origin's full text from docs/history/backlog/ and treat the files as the scope of record.

Orientation: single-file family over scripts/tool_runtime_stats.py plus its hermetic test twin. The window-bounded origin adds a --days N bound on epoch-ms started_at, streamed aggregation replacing the unbounded fetch, and an optional join pre-filter. The cleanups origin drops the dead window-day-count threading and collapses duplicated per-class fixture setup; its own trigger (the next change touching the miner's ranking or predicate code) is exactly the window-bounded change, so one plan owns both.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Re-grouping the pair into a broader statistics program plan: rejected; the program plan is delivered and archived; these are its recorded follow-up tails.
- Doing the cleanup before the window-bounded change: rejected by the cleanup item's own next-natural-touch trigger.
