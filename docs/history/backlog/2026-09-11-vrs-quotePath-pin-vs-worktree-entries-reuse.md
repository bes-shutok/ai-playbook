# Backlog: quotePath pin vs worktree-entries reuse in _git_changed_paths

Status: open
Workflow: backlog
Source: 2026-09-10-execute-plan-runtime-residuals code review r1, finding DS-4 (design-simplicity, Low), deferred by the review round's triage
Severity: Low (blocked by a plan Validation pin)
Scope: scripts/execute_plan_runtime.py

## Problem

`_git_changed_paths` (scripts/execute_plan_runtime.py) re-inlines the
`git status --porcelain -z --untracked-files=all` invocation that
`_git_worktree_entries` already owns. The duplication is a deliberate
consequence of the plan's Validation pin: the plan requires exactly 5
`"-c", "core.quotePath=false"` invocation sites in
`scripts/execute_plan_runtime.py`, asserted by

```bash
python3 -c 'import pathlib,re; t=pathlib.Path("scripts/execute_plan_runtime.py").read_text(); n=len(re.findall(r"\"-c\",\s+\"core[.]quotePath=false\"", t)); assert n == 5, n'
```

Reusing `_git_worktree_entries` from `_git_changed_paths` would drop the
count to 4 and break the pin without a plan amendment.

## Suggested fix

Only if the pin is ever amended: have `_git_changed_paths` call
`_git_worktree_entries` for the untracked-files union instead of running
its own status invocation, and update the plan Validation pin (and any
derived verify-script fingerprints) from 5 to 4 in the same pass.

## Why not fixed now

The duplication is the cheaper evil: changing the invocation count
requires a plan amendment (scope the review round did not authorize), and
the duplicated call is already parsed by the shared `_parse_porcelain_z`
helper, so parsing logic is not duplicated. Deferred by the r1 triage
(review doc
`docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r1.md`,
triage summary section).
