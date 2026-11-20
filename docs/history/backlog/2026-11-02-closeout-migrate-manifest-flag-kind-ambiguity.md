# Backlog: closeout migrator's --manifest flag takes different file kinds per subcommand, and a stale authoring-strand migration JSON in a reused session dir gets mis-supplied
Cluster: docs/history/backlog/2026-11-01-closeout-migrate-stale-landing-sha-comment.md (same-day review family)

- **Filed:** 2026-11-02, learn Step 1.9 over the 23:00 exec carrier session's closeout phase (landing 7364691cc)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-baseline-tracked-clobber.md (same script family, distinct class: that row owns baseline-mode tracked-clobber protection, this row owns operator-facing --manifest file-kind ambiguity across subcommands)
- **Cluster:** docs/history/backlog/2026-10-13-worktree-closeout-claims-sidecar-siblings.md (same script, covered; that row owns claim completeness, not flag input kinds)
- **Skill/step:** `scripts/worktree_closeout_migrate.py` subcommands `boundary-mirror` (reads the session `manifest.md` front-matter stable tuple) and the gate-removal adjudicator (reads the migration-shape `closeout-migration.json` transfer-out writes)
- **Class:** fix-class
- **Origin class:** session witness (exec-run closeout, 2026-11-02)

## Problem

Both subcommands expose a `--manifest` flag, but the expected file kind differs: `boundary-mirror` requires the session `manifest.md` (its front matter carries the stable run tuple: run_session_id, plan_path, run_worktree), while the adjudicator path consumes the migration-shape `closeout-migration.json`. A run directory reused across a plan's authoring strand and its exec execution carries BOTH files; in the witnessed closeout, the stale authoring-strand `closeout-migration.json` (bound to the authoring branch tuple) was supplied to `boundary-mirror` first and refused the tuple check, and the session `manifest.md` was then initially supplied with the plan's post-archive `completed/` path before the manifest's original living path cleared it. Two fail-closed refusals, each one-retry recoverable with precise messages; no data loss.

## Triage question

Whether the smallest disambiguation arm is worth its churn: a help-text clarification on `boundary-mirror`'s `--manifest` naming the expected file kind (and/or the tuple's plan_path being the manifest's original living path), versus leaving the current fail-closed refusals as the documentation. Any rename of the flag or JSON-shape acceptance is expected to churn pinned help catalogs.
