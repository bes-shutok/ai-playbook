# Backlog: anonymize private details in release archives

- **Filed:** 2026-10-18
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed release privacy-gate blocker
- **Class:** documentation / privacy

## Problem

The release privacy gate scans every regular-file blob in the rewritten result. It found private project identifiers and personal path examples in historical backlog and completed-plan records. The ordinary whole-checkout hygiene scan excludes some archive content, so it did not predict this release-only failure.

## Evidence

- `scripts/release-rewrite.sh` materializes the rewritten result and passes every regular file, plus the release-groups file, to `scripts/scan-public-hygiene.sh` in explicit-files mode.
- The release attempt failed that scan on archived records; the scanner named the offending repository-relative paths and did not move `main` or publish.
- A direct full-tree scan passed because its default traversal excludes some archive content; scanning the release's explicit regular-file set reproduced the failure.
- The release workflow's backup ref preserves the original local history while the public result is prepared.

## Expected

Make the release tree pass the exact published-result privacy scan while retaining useful technical history. Replace personal paths and foreign project identifiers with generic descriptions; keep implementation facts, repository-owned paths, and the reason each change mattered. Verify the full explicit regular-file set and groups file before moving `main`.

## Workaround assessment

Keep the privacy gate and anonymize the affected archival wording. Removing all affected archives would discard useful technical evidence; changing the deny patterns would weaken the public boundary; treating the default whole-tree pass as sufficient would leave the release path unverified.

The done landing sweep also refuses body edits to immutable completed-history documents unless the document registry carries a dated audit-note override. Use that existing override for the affected completed records, keep the gate unchanged, and clear the temporary audit notes after the redactions land.

## Why not fixed now

The hits span multiple archived records with different technical roles. A bounded pass must preserve their evidence while removing only personal or foreign identifiers, then prove that the exact release scan is clean.
