# Backlog: checkpoint-anchor arm 1 falsely reports a tracked non-ASCII plan path as untracked (quotePath)

- **Filed:** 2026-11-20, execute-plan Task 2 intermediate review (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** reproduced edge (tracked `plans/план-б.md` fixture; ls-files quotePath-escaped form misses the membership test)
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py` arm 1 `git ls-files` membership check
- **Dedup probe:** searched open rows for `quotePath`, `ls-files`; no existing row
- **Cluster:** the covering plan's Task 2 probe surface

## Observed versus expected

Observed: `git ls-files` prints quotePath-escaped paths, so a tracked plan with non-ASCII bytes in its name misses the tracked-set membership test and arm 1 warns "untracked". Expected: `-z --full-name` (or `core.quotePath=false`) comparison plus literal pathspec handling so tracked non-ASCII plans stay silent.

## Suggested correction

Switch the two probe git calls to `-z --full-name` output parsing (and the classifier's full-history lookup where it faces the same escaping), with a canary over a non-ASCII tracked plan path.
