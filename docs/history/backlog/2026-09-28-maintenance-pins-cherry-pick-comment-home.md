# Maintenance pins suite: update the cherry-pick pin's operator comment to its post-fold home

Status: open
Priority: low
Workflow: backlog
Class: simplicity
Driving force: docs

## Problem

The execute-plan worktree-first consolidation (2026-09-28) folded the Step 0.4 linked-worktree bootstrap into the canonical `## Worktree-first standard` section of `agents/skills/execute-plan/SKILL.md` as the named transfer-in implementation. The pin `worktree bootstrap names the unlanded-plan remedy` still greps `'cherry-pick only the plan-authoring commit'`, which survived the fold byte-identically, so the suite is green and owed no pin edit. Only the operator comment above the pin still locates the span in the retired "linked-worktree bootstrap" home.

## Expected

The comment above that pin in `scripts/check_maintenance_pins.sh` names the span's actual home (the canonical section's transfer-in implementation), so an operator auditing a red pin is not sent to a section that no longer exists.

## Observed versus expected

- Observed: pin comment says "the linked-worktree bootstrap names the missing-plan remedy...".
- Expected: comment references the `## Worktree-first standard` transfer-in implementation.
