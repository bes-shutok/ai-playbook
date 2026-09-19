Status: open
Priority: Medium
Created: 2026-09-16

# Add a retention policy and safe pruning workflow for review artifacts

Workflow: backlog
Severity: Medium
Class: review-artifact lifecycle
Source: cross-project review corpus audit, 2026-09-16

## Problem

The configured personal and company workspaces contain 3,308 files in 17
durable review directories. Thirty-six records are dated before the proposed
three-calendar-month cutoff of 2026-06-16. They are concentrated in six
repositories and are stored as gitignored working-tree documents backed by
the permanent `docs` branch. There is no shared retention key, dry-run report,
or pairing-aware pruning command.

Without an explicit lifecycle, every cleanup is a one-off deletion decision.
That creates three risks: current review runs can be confused with historical
records, Markdown and sidecar files can be split, and the docs-branch
add-only rule can restore a file that was removed only from the live checkout.

## Exact location

- `agents/skills/review-staging/SKILL.md`, documentation paths, canonical record,
  and sidecar contract
- `agents/skills/docs-branch/SKILL.md`, add-only sync invariant and explicit
  deletion handling
- `agents/skills/review-loop/SKILL.md`, round and historical-artifact rules
- Per-repository `.ai-playbook/facts.md` TOML path configuration
- A new repository-local or shared retention/pruning helper and its tests

## Evidence

- Durable review corpus: 3,308 files.
- Review families with at least two sidecars: 205 of 510 families.
- Records before 2026-06-16: 36 dated Markdown files; one additional undated
  review file had a filesystem timestamp of 2026-05-21. No matching old
  sidecar was found by the filename-date audit.
- The review directories are gitignored and several repositories maintain a
  permanent `docs` branch, so live-file removal alone is not durable.

## Suggested fix

1. Add an optional `review_retention_months` facts key with a documented
   default of three months. Define the cutoff using the review filename date,
   not filesystem mtime, and allow an explicit override for a run.
2. Add a dry-run command that reports candidates by repository, directory,
   date, record kind, and Markdown/sidecar pairing without printing document
   bodies.
3. Make deletion pairing-aware: remove a Markdown file and its matching
   `.stats.json` sidecar together, preserve unpaired records for explicit
   review, and never touch active review-loop or execute-plan scratch paths.
4. Add a docs-branch transaction that records explicit deletes in the docs
   branch worktree, verifies the deletion, and then removes the corresponding
   live shadow files. Abort before mutation if the candidate set changes.
5. Emit a sanitized deletion manifest containing counts, cutoff, and hashes,
   not raw review text.

## Acceptance

- A dry run produces the same candidate set on two consecutive invocations
  when the corpus is unchanged.
- A three-month run identifies exactly the 36 currently stale records without
  classifying records dated 2026-06-16 or later as stale.
- A paired Markdown/sidecar record is deleted as one unit; an unpaired record
  is reported and retained until explicitly selected.
- The docs-branch snapshot and explicit-delete commit prevent the next sync
  from restoring an intentionally removed review.
- Active scratch, current-round, and reconciliation inputs are excluded by
  path and by an explicit keep rule.
- The command has a confirmation or dry-run gate and leaves a sanitized,
  PII-free manifest suitable for the backlog or audit trail.

## Current disposition

The one-off cleanup was completed after the user confirmed a three-calendar-
month cutoff. Thirty-seven live records were removed, including the one
undated record whose filesystem timestamp was before the cutoff; thirty-four
corresponding records were also removed from the local `docs` branches. The
remaining work is the reusable policy and automation, which should land as a
separately reviewed change because it modifies shared docs lifecycle behavior.
