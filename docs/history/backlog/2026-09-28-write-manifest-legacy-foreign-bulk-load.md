# Write-manifest claim-or-foreign gate drowns fresh runs in legacy review candidates

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md


Captured: 2026-09-28 (source: release-skill-follow-ups done closeout, manifest finalize)
Status: open
Priority: low
Workflow: backlog
Class: usability
Driving force: reliability
Origin class: self-serving
Consumer urgency: Every done run in this repo hits the same wall: the claim-or-foreign gate refuses because thousands of pre-existing review records are neither claimed nor foreign, and each operator re-derives the same bulk-load workaround by hand.

## Problem

Finalizing a run manifest with write-manifest requires every staging candidate to be owned or foreign. On the first finalize in a repository with a large pre-existing review corpus, the gate rejects the invocation with thousands of unclassified candidates. The operator must build a `--foreign-review-from` file by hand (3262 legacy candidates in this session) to bulk-load them before the manifest finalizes. The workaround works but is manual, unrepeatable, and easy to get subtly wrong (for example `--claim-none` conflicting with `--owned-review`).

This happened during the 2026-09-28 release-skill-follow-ups closeout.

## Exact location

`agents/skills/done/SKILL.md`, Step 6 manifest finalize recipe; the write-manifest claim-or-foreign gate and the `--foreign-review-from` flag documentation.

## Expected

- The skill documents the first-run legacy-corpus situation and prescribes the canonical bulk-load invocation shape (one command, deterministic candidate list), instead of leaving each operator to reconstruct it.
- A supported mode (or recipe) generates the foreign list from the diff between the staging candidates and this run's owned artifacts, so the bulk-load file is reproducible rather than hand-assembled.
- The `--claim-none` + `--owned-review` conflict is surfaced in the skill text, since the natural first attempt hits it.

## Severity and source reference

Severity: low

Source: release-skill-follow-ups done closeout manifest finalize, 2026-09-28; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The closeout completed its manifest with the existing flags. Recorded as an ergonomics fix for the done skill documentation and write-manifest recipe.

## Dedup probe

Search terms: `write-manifest`, `foreign-review-from`, `claim-or-foreign`, `owned-review`. No open item covers the legacy-candidate bulk-load ergonomics; the owned-commit ledger item covers commit attribution, a different finalize defect.

## Suggested fix

Add a "first finalize in an established repo" subsection to the done skill's Step 6 with the canonical foreign-bulk-load command sequence, and add a write-manifest helper mode that emits the deterministic legacy-candidate list for `--foreign-review-from`.
