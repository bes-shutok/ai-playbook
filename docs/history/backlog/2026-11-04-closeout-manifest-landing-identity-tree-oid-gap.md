# Backlog: landing identity records no tree OID while the landing-aware proof matches "its recorded tree"

- **Filed:** 2026-11-04, plan-review r2 certification residual (agent-resource-cleanup-disposition, overflow row 2)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review residual
- **Class:** fix-class
- **Dedup probe:** searched open backlog filenames and bodies for landing identity, recorded tree, and touched set. `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` owns the drift false positive and names landing commit 944cb825c as unreachable; it does not cover the recorded-evidence shape. `docs/history/backlog/2026-11-01-closeout-migrate-stale-landing-sha-comment.md` covers a stale landing SHA comment, not the manifest's landing identity record. None covers the missing tree OID inside the recorded landing identity.
- **Cluster:** `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` (owns the base-drift proof this record serves)

## Problem

Plan 2026-11-04-agent-resource-cleanup-disposition defines Landing identity as "the landing commit's object id and touched path set", but the landing-aware proof checkbox says to "match its recorded tree and touched set". The tree of the recorded landing commit is derivable from its object id only while the object survives; after base drift makes the commit unreachable, it is GC-eligible, and once collected the tree match cannot run and the branch retains (safe fallback, but the fix's effectiveness decays with time - exactly the aged-strand shape the drift incident describes).

## Expected

Record the landing commit's tree OID inside the landing identity beside the object id and touched path set (one more field on the same existing append-only record), or restate the proof to match the touched set and the recorded tree when resolvable with retention otherwise, so the recorded evidence is self-contained across garbage collection.

## Evidence

- Plan Terms, Landing identity: "the landing commit's object id and touched path set".
- Plan Task 1 checkbox: "match its recorded tree and touched set and require the branch's authored delta present at the destination".
- Unreachable commits are GC-eligible; a recorded OID alone does not guarantee tree resolvability at retry time.
