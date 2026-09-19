# Backlog: dedupe the plan-section/Files parser pair in plan_readiness.py

Status: open
Origin: P11 execution review r1 (F5, design-simplicity)
Date: 2026-09-19

`_plan_task_sections`/`_plan_files_items`/`_plan_path_shaped` (added for `plan_ownership_problem`) re-implement the section splitter and Files-collection state machine owned by `_review_scope_task_files`. The two parsers must stay in sync so review-scope clause (c) and the ownership check inventory the same Files lists; a one-sided future fix silently diverges them.

Fix shape: express `_review_scope_task_files` as a wrapper over `_plan_task_sections` + `_plan_files_items` (token normalization is already shared), keeping all existing selftest arms green (review_scope + plan_ownership families are the regression net).

Trigger: any future edit to either parser.
