# Docs-branch sync cannot anchor a session window with fewer than two content-confirmable run-start markers

Captured: 2026-09-28 (source: release-skill-follow-ups done closeout, docs-branch sync step)
Status: open
Priority: medium
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: self-serving
Consumer urgency: Done runs in interactive sessions routinely produce exactly one run-start marker, so their session-produced docs are silently left out of the docs-branch sync and must be re-synced by a later run that happens to have an anchorable window.

## Problem

The docs-branch sync anchors the sync window on session run-start markers and requires at least two content-confirmable markers to define the window. A done run that starts fresh (single marker) leaves the window unanchorable, and the sync conservatively skips syncing the run's own review records. The miss is observable only if the operator reads the sync output; nothing durable records that a given review record was skipped or when it might be synced.

This happened during the 2026-09-28 release-skill-follow-ups closeout: the recreated code-review r2 record stayed disk-only because the window had a single marker.

## Exact location

`agents/skills/docs-branch/SKILL.md`, session-window anchoring rule (the two-content-confirmable-markers requirement) and the conservative-gating fallback.

## Expected

- A second anchor source exists for single-marker windows: the run manifest plus the owned-commits ledger can witness which docs artifacts the run created, bounding the window without a second marker.
- When a window remains unanchorable, the sync output names the specific skipped artifacts and writes a durable skip record (e.g. a pending-sync sidecar) so a later run picks them up deterministically instead of by operator memory.

## Severity and source reference

Severity: low-medium

Source: release-skill-follow-ups done closeout, 2026-09-28; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The closeout's contract is to run the existing sync faithfully, not to redesign its anchoring. Recorded for a dedicated docs-branch skill fix.

## Dedup probe

Search terms: `docs-branch anchor`, `run-start marker window`, `unanchorable`. No open item covers the single-marker window case; the run-start-marker backlog family covers marker content and location, not anchoring sufficiency.

## Suggested fix

Extend the anchoring rule to accept a manifest-plus-ledger witness pair as an alternative second anchor, and add a durable pending-sync record whenever artifacts are skipped so the next anchored sync consumes it.
