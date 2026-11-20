# plan-review-gate

`check-plan-review-gate.sh` is a Claude Code `PreToolUse` (Bash) hook. It blocks a `git commit` that stages a plan file when the plan's latest review round records a No-Go verdict. It is a mechanical backstop for the plans skill rule "confirm `ready=yes` before declaring the plan ready"; the skill text stays the primary control.

## Selection rule

- Candidates are the plan's own canonical plan-review rounds under a `reviews/` directory: `<date>-plan-review-[<date>-|<KEY>-<n>-]<slug>[-p<8 hex>]-r<N>.md`, matched case-insensitively. The slug is the plan stem without its leading date or story key.
- The highest round number `N` is judged. Equal `N` (possible only across different tokens) goes to the newest mtime, then the greatest basename.
- Other review kinds (code review, exec review), backup variants, and longer slugs are ignored.
- With no canonical candidate the hook prints its no-artifact warning and allows the commit.
- The verdict grep (`No-Go|ready=no|Ready for execution: No`) is unchanged.

Accepted limit: a plan re-authored under the same slug with a new `-p<8 hex>` token restarts at round 1, so an older token's higher round can outrank it.

## Install

The live hook is a symlink to this file, so the repository copy is the one that runs. Keep the existing settings entry unchanged.

```bash
ln -sf "$(git rev-parse --show-toplevel)/agents/hooks/plan-review-gate/check-plan-review-gate.sh" ~/.claude/hooks/check-plan-review-gate.sh
```

Test: `python3 -m pytest scripts/test_plan_review_gate_hook.py -q`.
