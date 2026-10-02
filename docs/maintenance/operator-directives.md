# Operator directives (lane lifecycle home)

This file is the directive-lifecycle home of record for the scheduler loop and every lane it dispatches: an operator directive's issue, lift, supersession, or expiry is valid only when recorded here. Where a carrier prompt, loop directive, or state-file note carries directive text, the payload reads this home at turn start and the home's record wins on conflict; a directive lift or supersession is a one-file commit to this file. Automation payloads lift directive text from this home at dispatch instead of baking aging clauses: the 2026-10-02 carrier clause that outlived two in-chat lifts across 87 armed runs is the anti-shape (witness: the stray-close incident dossier, archived beside its plan at completion).

Record format (one `## D-<n>: <title>` section per directive):

- `issued`: the date the operator issued the directive.
- `status`: active, superseded, lifted, or expired.
- `expiry`: a date or none.
- the directive text, verbatim when operator-issued.
- `scope`: the lanes the directive binds.
- `superseded_by`: the superseding record's id, when not active.
- `witness`: the commit or document that proves issuance.

## D-1: execution-lane state

- issued: 2026-10-03
- status: active
- expiry: none
- scope: all lanes of the maintenance loop
- directive: the execution lane is reopened; plans at the plans root dispatch for execution.
- superseded_by: none (this record supersedes the 2026-10-02 execution-lane closure, which was recorded only in a carrier prompt and the state file's survey notes and outlived two in-chat lifts)
- witness: the day's execution landings on main (27717b6a, cdeed760, 11460cf5, b18a5aba, 6cda8ee2, c0d26b88 and successors) and the dossier's directive history.

## D-2: archiving policy

- issued: 2026-10-03
- status: active
- expiry: none
- scope: every lane and turn that can archive a plan
- directive: archiving plans without any real changes is not allowed unless the operator specifically asks each time. Every ad-hoc fix made during the incident response must be validated or replaced through a proper plan with review, so the situation cannot happen again.
- superseded_by: none
- witness: the dossier's Operator policy section (verbatim) and the maintenance survey's landed-plan disposition fence.
