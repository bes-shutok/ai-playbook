# Backlog: promote the Task 2 learn captures to their shared-corpus canonical homes

- **Filed:** 2026-10-21
- **Status:** open
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class (two placement landings in existing shared-corpus files; no new gate)
- **Driving force:** docs (Task 2 light-boundary learn leg, docs/history/plans/2026-10-18-review-runtime-sibling-module-deployment.md)

## Problem

The Task 2 boundary's learn leg captured two lessons full-text in this repo's project corpus (`docs/maintenance/development_lessons.md` #142 stdlib directory-provenance leg, #143 mutation-matrix pin grading) because the learn run is checkout-bounded to this worktree and both canonical homes resolve outside it:

1. `projects/.ai-playbook/python_guidelines.md` (shared_docs_dir): the Python-ecosystem restatement of #142, the three-legged stdlib classification (name set, builtins, stdlib-directory provenance). Fork (2) home per learn's placement ladder.
2. `projects/.ai-playbook/development_lessons.md` (user-level corpus): the cross-project restatement of #143, grade a review's pin claims with a mutation matrix, as a new `UL#N` with a `Family H` tag, deduped at landing time against UL#71, UL#330, and UL#405.

## Suggested fix

In a primary-checkout session (shared_docs_dir resolves through `~/Projects/.ai-playbook/` into the instructions repo working tree): add the two restatements, then slim #142 and #143 here to witness pointers per fork (2)'s thin-witness ceiling, keeping the playbook-machinery witnesses in this corpus (Homebrew CPython 3.14/3.15 importing `_missing_stdlib_info`; the 4/5 matrix whose surviving `-S` mutant named the unpinned flag).
