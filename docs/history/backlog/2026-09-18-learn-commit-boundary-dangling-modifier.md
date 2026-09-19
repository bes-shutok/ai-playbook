# Backlog: fix the dangling "including the whole project repository" modifier in learn's commit-boundary sentence

Status: open
Priority: low

Workflow: backlog
Severity: low
Source: code review r5 of plan `docs/plans/2026-09-16-learn-done-workflow-updates.md` (2026-09-18); staging doc `docs/reviews/2026-09-16-learn-done-workflow-updates-code-review-r5.md`.

## Finding

`agents/skills/learn/SKILL.md` line 23 (When to Use) reads: "the `done` skill owns every other commit (done may stage learn-authored artifacts whose Step 1.8 commit learn reported as failed, after asking) except the docs-branch skill's orphan-branch commits, including the whole project repository." After the r2 exception insertion, the trailing participial phrase "including the whole project repository" attaches most naturally to the nearest noun phrase ("the docs-branch skill's orphan-branch commits"), which is false (docs-branch commits carry only gitignored docs); the intended head is done's ownership clause. done's frontmatter states the same contract without the trailing modifier, so the two summary surfaces also diverge structurally.

## Suggested fix

Reposition the modifier next to its head (for example "...owns every other commit, including every commit in the whole project repository, except the docs-branch skill's orphan-branch commits (...)") or drop the trailing clause. No Validation gate pins the tail (the G2 pin ends at "...in the skills repository").

## Why not fixed now

Raised by the final review round (r5) at the run's five-round cap; a digest-mutating fix would have required a sixth round, which the run's budget forbids. Prose-clarity only; the wrong parse is domain-absurd, so no plausible misbehavior follows.
