# Deploy check_lesson_scope.py to runtime scripts dirs

Status: open
Workflow: backlog
Source: execute-plan Phase 3 r1 review of the learn-company-scope-placement plan (finding F4, security#validator-not-deployed-to-default-path)
Severity: Medium
Class: release-gate deployment, machine-local

## Problem

The `done` Step 3 item 4a pre-commit lesson scope audit resolves the validator
at `${LESSON_SCOPE_SCRIPT:-${HOME}/.ai-playbook/scripts/check_lesson_scope.py}`.
The script exists only at `scripts/check_lesson_scope.py` in the skills repo;
the per-file symlink into `~/.ai-playbook/scripts/` (the registry sync model)
is not deployed, so the audit takes the documented warn-and-continue cold start
on every machine until the symlink exists. The mechanical duplicate guard the
plan adds is inert by default.

This boundary is intentional plan scope (Ship when; machine-local work outside
the plan), but it stays invisible once the plan archives, so it needs a durable
tracker.

## Location

- `~/.ai-playbook/scripts/check_lesson_scope.py` (missing; deploy a per-file
  symlink to the repo copy, keep symlink semantics, `cp -P`-style, never a
  second copy)
- `agents/skills/done/SKILL.md` Step 3 item 4a (cold-start warn-and-continue
  is the designed fallback and needs no change)

## Suggested fix

On each machine that runs `done` against a repo with a project lessons corpus,
create the symlink, then verify with:
`python3 ~/.ai-playbook/scripts/check_lesson_scope.py <corpus> <master>` on a
fixture pair (exit codes 0/1/2). Re-check after any registry re-sync.
