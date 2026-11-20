# Backlog: checkpoint-anchor arm 1 false "untracked" on directory-shaped plan operands (gate asymmetry)

- **Filed:** 2026-11-20, Phase 3 code-review r1 (plan 2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement), finding contract-docs#F1, backlog capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** external-boundary exact-membership test vs operand shape (empirically demonstrated: `git ls-files -- <dir>` lists contained tracked files, so the directory operand itself misses the membership set; pre-round warns, full gate is silent — sibling-gate disagreement)
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py:1534` arm 1 membership test; call sites ~3042 (pre-round) vs ~3577 (full gate)
- **Dedup probe:** searched open rows for `directory operand`, `ls-files`; the quotePath row covers non-ASCII names only
- **Cluster:** the checkpoint-anchor probe family (quotePath row is the nearest sibling)

## Observed versus expected

Observed: a directory operand whose plan files are all tracked gets "plan file `<dir>` is untracked in git" from pre-round while the full gate stays silent. Expected: the arm either treats directory operands as tracked when their contents are tracked, or skips with a distinct silent reason.

## Suggested correction

Normalize the operand (resolve directory to its tracked contents) or skip non-file operands with the plumbing-silence path; canary the directory shape.
