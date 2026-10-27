# Closeout migration: replacement failures print under legacy copy-verification labels

- Filed: 2026-10-27
- Status: open
- Priority: low
- Workflow: maintenance exec (ad-hoc-eligible)
- Class: operability / error-report clarity
- Origin class: execute-plan Step 1.2b intermediate review, closeout-migration-same-run-mirror-replace Task 1
- Skill-step: scripts/worktree_closeout_migrate.py failed-list printer and summary line
- Cluster: docs/history/backlog/2026-10-27-closeout-mirror-residuals.md; docs/history/backlog/2026-10-27-execute-plan-skill-mirror-growth-unbalanced.md (same surface: the closeout-migration boundary-mirror family landed 2026-10-27; distinct defect classes: printer labels, residuals/hardening, text growth)

## Problem

Receipt-replacement failures (staging/install class) print as "verification failed for ..." and "N file(s) failed copy verification", misnaming the failure class during closeout error triage. The per-entry error text is accurate; only the wrapper labels misname.

## Suggested direction

Branch the failed-entry printer (or summary line) on replacement failures; keep the existing copy-verification wording for the plain copy class.

Driving force: operability (misleading stderr during failure triage).
