# A schedule-at ask is satisfied only by the asking session's own automation record

- Cluster: docs/history/backlog/2026-10-17-croncreate-cap-delete-own-spawner-leg.md (the operator-ordered schedule surface family; that sibling's entry landed 2026-10-17 08:08 and owns the cap-refusal ladder and the schedule-surface split; this row is the satisfaction-side sibling correction, witnessed about two hours later)
- Added: 2026-10-17
- Status: covered (docs/history/plans/2026-10-17-schedule-ask-session-owned-automation.md)
- Origin: operator correction 2026-10-17 ("these scheduled automation are from different sessions, I asked you to schedule for this session")

## Witness

2026-10-17 about 08:40, the interactive maintenance authoring session whose cycle-1 authoring had been usage-wall-stopped the prior night (authoring claim sess_9f5841ba, superseded overnight by the takeover landing 2f000806a): asked to "schedule at 11 am" with the payload "go on and restart subagents right now if needed". The session listed the automation surface, found the standing recurring scheduler (automation-7f07284b) already carrying an equivalent operator addition and a peer session's one-shot exec order (automation-5836056c) firing in the same 11:00 slot, judged the ask already satisfied, created nothing, and reported the foreign ids as the answer. The operator corrected: those records belong to different sessions; the ask binds the scheduling act to the asking session.

Mechanism: the scheduling-verb contract (AGENTS.md "Scheduling asks (verb contract)", introduced 3b05b66a6 2026-09-20) says "create or patch the automation, then report the automation id and its next fire time" but never binds the created or patched record to the asking session, so an existing record with similar payload text reads as satisfaction. The standing no-duplicate discipline ("never re-arm or duplicate an existing automation") is scoped to payload duplication inside one lineage; the session over-extended it across ownership lines, and payload-text similarity substituted for an ownership check. Session-owned records are the accountability and lifecycle unit: only the owning session updates or deletes its own record (the 2026-10-16 peer-delete incident), so only a session-owned record can carry this ask forward.

## Ask

Adjudicate and fix the contract's satisfaction semantics: an operator schedule-at ask is satisfied only by an automation record the asking session creates or patches, and the reported id is that record's id; an existing automation from another session is context, never satisfaction; deconfliction with parallel carriers rides the created payload (re-derive from disk, skip-if-done), never a create refusal.
