Status: open
Priority: medium
Class: fix-class
Origin class: skills-corpus defect (2026-11-07 cross-session 24h harvest over the prior day's maintenance fleet)
Cluster: docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md (same dispatch-surface contract family; that row owns the rolling logs' shared contract block, this row owns the ask payloads baking duties the templates already own); docs/history/backlog/2026-11-06-backlog-batch-lands-without-survey-selector.md (same family; that row owns the backlog rows' survey-selector shape)

# Standing exec/author schedule asks re-bake the full selection algorithm and report contract the maintenance templates already own

## Problem

The operator's standing exec and author schedule asks carry the complete selection algorithm, availability test, report contract, and cleanup duty verbatim in every payload: ten payloads fired in the 2026-11-06 window, each about 450 words restating walk PLAN-PROMPTS.md top to bottom in file order, the FIRST-available rule, the two unavailability clauses, the compact-between-executions rule, the final-report phrasing prohibition, and the worktree-and-branch cleanup duty. The skills own every one of those duties already: the authoring template's pre-work gate owns the walk-and-create ordering and the availability test, the execution template owns its lane's ordering and report shape, and the runtime overlay's user-directed payload duties own the report and re-arm contract. The duplication is not inert: payloads drift from the templates they predate (the raced-pick continuation arm landed template-side in the 0cde7606c landing and older baked payloads never carried it), each new schedule ask restarts from the long form and re-diffs against skill text the receiver loads anyway, and the operator asked twice in-window for a more succinct prompt on exactly this ground. The overlay's Directive-lift rule (the raced-pick blueprint lift paragraph) already owns the mechanism for retiring per-payload wording; what is missing is the sanctioned short ask form, so no schedule ask can shrink.

## Observed vs expected

Observed: every standing ask re-bakes the algorithm; two operator correction rounds in one day asked for the succinct form; payload and template wording diverge as the templates evolve.
Expected: a standing ask carries mode and cap only (author/exec, max 1, stop after the first); the receiving session resolves selection, report, and cleanup duties from the template payloads it is already bound to load; template-side changes reach every future ask without payload edits.

## Evidence (trimmed)

- Ten windowed payloads carry the long form (session transcript extraction, 2026-11-06 13:02 through 2026-11-07 02:03 firings); two operator corrections in-window asked to refactor the prompt to "pick the first available in the list by urgency" and to drop content "already in skills".
- The templates own the duties: agents/skills/maintenance/template-authoring.md pre-work gate paragraph; agents/skills/maintenance/template-execution.md; agents/skills/maintenance/zcode.md user-directed payload duties paragraph.
- The lift precedent: agents/skills/maintenance/zcode.md "Raced-pick blueprint lift" paragraph (lifted from the blueprint per the Directive lift rule instead of baked per-payload wording).

## Suspected root area

The overlay's user-directed payload section never names a short ask form or its resolution path, so the long form remains the only written ask surface and every new ask copies it.

## Ship when

agents/skills/maintenance/zcode.md's user-directed payload duties paragraph names the short ask form and states that the receiving session resolves the walk, availability, report, and cleanup duties from the template payloads; no template text changes; hygiene scan exit 0; no machinery added. The operator-side adoption (issuing future schedule asks in the short form) is an operator action noted here, not repo machinery.

Capture hygiene: `bash scripts/scan-public-hygiene.sh --files` pass and `bash scripts/check-no-em-dash.sh file` pass over this row and the sibling cluster edits (2026-11-07)
