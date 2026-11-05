# Backlog: pruning the first prompt entry removed the shared rolling-log contract

Status: open
Workflow: backlog
Priority: high
Class: fence-class
Driving force: reliability
Origin class: self-serving
Added: 2026-11-05, learn Step 1.8 from maintenance closeout analysis
Environment context: ai-playbook repository, primary rolling-log source and repository skills
Skill/step: `agents/skills/investigate/SKILL.md` Stage 4; `agents/skills/plans/SKILL.md` Entry freeze; `agents/skills/maintenance/decisions.md` rolling-log write duties
Severity and source: High, current HEAD no longer contains the `Write boundary rule`, `Freeze rule`, or shared prune rules, while these consumers still refer to those labels; history shows the first entry prune removed the rules block with it
Capture hygiene: `bash scripts/scan-public-hygiene.sh --files docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md` passed; `bash scripts/check-no-em-dash.sh file docs/history/backlog/2026-11-05-done-finalized-manifest-shadow.md docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md` passed
Cluster: docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md (same PLAN-PROMPTS contract surface; that row owns a narrower freeze-rule placement citation residual, this row owns loss of the shared rules block)
Dedup probe: surveyed 343 open top-level backlog rows and searched both rolling logs plus prompt-log history for missing shared rules, prune ranges, and write-boundary loss. Completed plans `docs/history/plans/completed/2026-10-13-prompt-log-origin-and-prune-boundaries.md` and `docs/history/plans/completed/2026-10-20-plan-prompts-prune-range-content-inventory.md` own correct prune semantics and range inventory, but not the current deletion of the standing rules block. `docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md` covers a narrower existing freeze-rule placement citation residual; `docs/history/backlog/2026-11-03-plan-prompts-wrong-location-disposition-marker.md` owns one rejected-alternative marker violation. Neither covers the rules block being pruned with the first entry.

## Problem

The shared `Standing rules` block was located after the first `PLAN-PROMPTS.md` dispatch entry and before the next `##` heading, so the range was treated as part of that entry. Commit `dd1803d2c8` pruned the entry after its plan landed and removed the rules block with it. At current HEAD, `agents/skills/investigate/SKILL.md`, `agents/skills/plans/SKILL.md`, and maintenance still reference the missing `Write boundary rule` and related log rules. A writer can no longer resolve the authoritative lock, staging, recovery, freeze, and prune contract from the referenced source.

## Exact location

- `docs/history/backlog/PLAN-PROMPTS.md` no longer contains the shared `Standing rules` block at HEAD
- `dd1803d2c8` removes the first entry range that contained that block
- `agents/skills/investigate/SKILL.md` Stage 4 and `agents/skills/plans/SKILL.md` Entry freeze still point to the missing `Write boundary rule`
- `agents/skills/maintenance/decisions.md` still points to the missing prune, freeze, and write rules

## Suggested direction

Restore the shared prompt-log contract from repository history in a stable location outside every dispatch-entry range. Then point all consumers to that one canonical home and add focused regression coverage proving that pruning the first entry preserves the shared contract. Keep the investigation log's repo-relative path rule and the established lock and recovery semantics.

Machinery admission: the initial fix can restore and relocate existing instructions without adding a gate, validator, lock, or ceremony. A new structural checker is not recommended until a repeat shows the placement can drift again; any later checker starts warning-only and names the removal path it would replace.

## Why not fixed now

This request authorized session analysis, backlog capture, and investigation only. Restoring and relocating a shared workflow contract changes the authoring and landing rules and needs an independently reviewed plan.
