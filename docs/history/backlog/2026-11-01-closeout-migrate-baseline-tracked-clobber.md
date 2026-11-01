# Closeout migrate baseline mode can clobber the destination's newer tracked files

Status: open
Priority: high
Class: fix-class
Cluster: docs/history/backlog/2026-10-31-closeout-zero-delta-report-arm-coverage.md, docs/history/backlog/2026-10-31-malformed-closeout-baseline-json-refusal.md
Origin class: execution-run closeout defect witness (session learn, 2026-11-01)

## Observed vs expected

Observed: a run invoked the closeout migrate (`scripts/worktree_closeout_migrate.py migrate`) with a foreign ad-hoc worktree as its baseline near the end of the run. The migrate carried whole-file bytes for shared tracked corpus surfaces (the project lessons corpus and the document registry) from the baseline checkout, whose copies predated peer landings made on the primary mid-run, and staged the rewound versions in the primary checkout. Expected: a baseline-relative carry must not move a shared tracked file backward; the staged set should contain only the migration manifest's own outputs (session-dir records), never rewound tracked corpus bytes.

## Reproduction evidence (trimmed)

- Baseline worktree branch predated a peer landing that edited `docs/maintenance/development_lessons.md` and `docs/maintenance/document-registry.md` on the primary.
- After `migrate --baseline <worktree>`, the primary's index held stale staged entries for both files; the worktree bytes overwrote the primary's newer content.
- Repair: `git restore --staged` plus `git restore` from HEAD on the affected paths, then re-validation that the registry still held the run's landed rows.

## Environment

- Playbook repo, 2026-11-01, exec-run closeout phase; migrate run from the primary checkout with a worktree baseline path.

## Suspected root area

`scripts/worktree_closeout_migrate.py` baseline mode lacks a pre-flight guard (diff baseline vs destination HEAD for shared tracked files, refuse or re-capture on an older baseline) and lacks a post-run staged-set ownership check (revert tracked-file hunks outside the manifest's own outputs). Related corpus witness: lesson 354; sibling family: the zero-delta silence row's warning-only report arm (covered, see `docs/history/backlog/completed/` twins and the covering plans).

## Suggested fix shape

1. Pre-flight: when a baseline checkout is given, `git diff --stat` the baseline's tracked files against the destination HEAD for the registry/lessons surfaces; refuse with a named remediation when any differ in the backward direction.
2. Post-run: after the carry, list staged entries and revert any tracked-path hunk the manifest's outputs do not own, reporting each as a prevented clobber.
