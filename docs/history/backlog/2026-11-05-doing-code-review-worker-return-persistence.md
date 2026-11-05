# Backlog: doing-code-review parent-orchestrated flow never mandates persisting worker returns before synthesis

Status: open
Priority: high
Class: fence-class
Driving force: reliability
Added: 2026-11-05, memory-index-load-budget-consolidation execution run (learn Step 1.8)
Capture hygiene: `scan-public-hygiene.sh` pass.
Cluster: agents/skills/doing-code-review/SKILL.md (the parent-orchestrated panel flow; the staging synthesis it ends in)
Origin class: self-serving

## Problem

The parent-orchestrated lens-panel flow ends with the parent synthesizing worker returns into a staging record, but no step mandates persisting each return verbatim to disk on arrival. The returns live only in the parent conversation, so a context compaction between arrival and synthesis destroys the panel table's inputs: per-worker raw/solo/echo attribution is unrecoverable from any durable surface, and a round whose attribution is unrecoverable cannot be staged honestly.

Observed versus expected: witnessed this run - a two-worker dispatch returned four Low findings, the parent-side compaction fired before staging, disk grep for the attribution came back empty, and the round had to be voided as unstageable (documented in the round log; findings were re-verified against disk and addressed, but a replacement certifying round paid to re-cover the same bytes). Expected: the flow persists each return to a per-worker payload file beside the round's session logs the moment it arrives, and the staging synthesis reads those files.

## Exact location

- `agents/skills/doing-code-review/SKILL.md` (the parent-orchestrated panel / synthesis step)

## Suggested direction

One skill-text addition to the parent-orchestrated flow: after each worker return, write `<round-log-dir>/review-<round>-worker-<name>-payload.md` verbatim before any synthesis; the staging step cites the payload files as its input record. No gate, no validator - a work-durability mandate.

## Evidence

- Witnessed 2026-11-05: voided round + replacement round documented in the run's review r2 round log and staging record (session-local under `.ai-playbook/reviews/2026-11-05-memory-index-load-budget-consolidation-code-review-r2.md`, Voided attempt line)
- The remedy as practiced this run: per-worker payload files persisted on arrival for every later round; all staged cleanly
