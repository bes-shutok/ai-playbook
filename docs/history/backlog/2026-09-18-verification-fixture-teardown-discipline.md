# Backlog: verification fixture placement and teardown discipline

Status: open
Priority: medium

Workflow: backlog
Source: 2026-09-18 fixture incident in this repo (session investigation, Andrey direction); related item: `2026-09-18-witness-append-refusal-branch-test-coverage.md` (placement and teardown line added on its branch, commit 48348e51).

## The gap, precisely

Verification recipes embedded in backlog items and review fix rounds that create scratch git repos carry no placement rule and no teardown step. Witnessed 2026-09-18 07:42-07:44: a manual run of the witness-append refusal recipe created `repoA/` and `repoB/` in the repo root (fixture identity `t <t@t>`, empty `init` commits, orphan `docs` branches, one `lesson-scope-audit` drift witness commit on repoB). They survived half a day and surfaced as detached foreign commits in the git GUI.

Aggravator: the done sweep's foreign-path refusal discipline correctly protects untracked scratch from every later pass (the pipeline's r6 launch record logged them as "Foreign tree state left untouched"), so once a fixture lands in the worktree nothing owns its cleanup. The guard under test became the reason the leftovers persisted.

## Suggested fix

1. Corpus rule (captured as a lesson 2026-09-18): any verification that creates state runs inside `mktemp -d` and ends with teardown; never create scratch repos in the repo root.
2. Recipe template rule: backlog items and plan Validation blocks that prescribe fixture creation end with an explicit teardown command, treated with the same weight as the assertions themselves; review lenses check for it.
3. Amend existing offenders as they surface; the witness-append item is already amended on its branch (2026-09-18).

## Acceptance

- Authored recipes pass review only with placement and teardown wording present.
- A sweep of open backlog items and open plans finds zero fixture recipes missing placement plus teardown.
