# Backlog: pins suite lacks intra-payload ordering anchors

Status: open
Workflow: backlog
Origin: 2026-09-16-maintenance-scheduler-liveness r2 review (finding T-4, deferred to backlog by the triage)
Severity: Low (test-discrimination gap, not a product gap)
Scope: scripts/check_maintenance_pins.sh

## Problem

The pins suite anchors `SUCCESSOR DISPATCH` and the resume rule to the
execution inner payload block (the span between the
`<prompt for the scheduled session>` tags) but not to their intra-payload
positions: the successor paragraph belongs immediately after the final
squash-merge sentence and before the FINAL STEP compaction line, the resume
rule belongs immediately after the PRE-STEP block, and the done skill's
rearm-on-touch line belongs immediately before the done skill's Step 0
heading. A regression that moves any of them (for example past a gate it
must precede, or into the wrapper the dispatch slice excludes) keeps every
presence and count pin green.

## Consequence

Ordering-sensitive duties lose their placement guarantee: the pins verify
presence and multiplicity only. The done-skill line's placement is checked
as file-wide presence, so moving it below the Step 0 heading (where the lock
acquisition, not the touch, gates the check) stays green, and a successor
paragraph drifted after the FINAL STEP line would be compiled into a payload
that chains before compacting without any pin noticing.

## Fix sketch (when picked up)

Region-scoped pins or positional index checks in the pins python block: for
each ordered pair (predecessor anchor, successor anchor), assert
index(predecessor) < index(successor) within the same region. Pairs to pin:
the final squash-merge sentence before `SUCCESSOR DISPATCH` before the FINAL
STEP line (execution inner block); the end of the PRE-STEP block before
`this is a resume run`; the `Before Step 0, in a repository that resolves
the maintenance skill` line before the `## Step 0` heading in
`agents/skills/done/SKILL.md`. Verify each new pin RED by moving the
successor anchor in a scratch copy and GREEN on the current tree before
committing.

## Scope note (2026-09-17, r3 review): confinement gap, second member

The gap has a second dimension beyond ordering: confinement. The execution
carve-out span ("beyond the re-arm duty below and the single
successor-dispatch duty below") and the resume-rule span ("this is a
resume run") are pinned for presence only (the successor anchor alone has
an exactly-once count, and it is file-wide), so grafting either span into
the authoring blueprint, or into the wrapper text the dispatch slice
excludes, keeps every pin green while the compiled authoring payload gains
a duty it must not carry. Fix sketch: region-confine the checks in the
pins python block by splitting the file on the blueprint headings and the
dispatch-slice tags, then assert each span appears only in its own region:
the carve-out span and the resume rule only inside the execution inner
block, the resume rule additionally between the PRE-STEP block and the
Execute sentence. Verify RED by copying a span into the authoring
blueprint in a scratch copy, GREEN on the current tree.
