# Backlog: checkpoint-anchor arm 2 merge-shaped cells — diff-body pollution and unpinned merge behavior

- **Filed:** 2026-11-20, Phase 3 code-review r1 (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), findings correctness#1 + testing#F-T-1 + design-simplicity#F-DS-5, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** git-output-shape assumption (with `--diff-merges=first-parent`, merge diffs land in stdout even under `--format=%s`; the `any(line.startswith("wip:"))` scan reads diff body lines, so a merge touching the plan with a context line starting `wip:` falsely silences the missing-anchor warning) + unpinned merge behavior (no merge-shaped canary; first-parent simplification can hide a side-branch `wip:` commit)
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py` arm 2 subject scan (lines ~1544-1553); `scripts/test_plan_readiness.py` PlanCheckpointAnchorWarningsTest (no merge-shaped cell)
- **Dedup probe:** searched open rows for `merge`, `diff-merges`, `wip scan`; no existing row
- **Cluster:** the checkpoint-anchor probe family (landing-prefix-set, plumbing-error-cells rows)

## Observed versus expected

Observed (empirically verified): merge output pollutes the subject-only scan (false silence) and the merge path is uncanaried. Expected: the arm scans only true commit subjects (e.g. `--no-diff-merges` or subject-only plumbing), and canaries pin both the merge-delivered-`wip:` silence and the first-parent simplification behavior.

## Suggested correction

Switch arm 2 to subject-only output (or filter diff lines), add merge-shaped canaries (silent when `wip:` arrives via --no-ff merge; documented first-parent simplification behavior).
