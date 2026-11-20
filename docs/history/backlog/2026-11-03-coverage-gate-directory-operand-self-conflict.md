# Backlog: coverage gate directory operand inside the active surface still self-conflicts

Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Class: fix-class
Driving force: correctness

## Problem

A well-formed directory-shaped declaring plan (PLAN.md charter plus tasks/) that lives inside the active plans surface makes the duplicate-origin coverage gate report its own charter as a covering citer: the declaring-bytes read raises IsADirectoryError, so only the path-only exemption applies, and the rglob scan yields `<slug>/PLAN.md` whose path differs from the directory operand. The gate exits 1 on a correct certification, the same false self-conflict class plan docs/history/plans/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md removed for file twins.

Pre-existing at the twin plan's base (worker-verified through the real CLI on both head and base, exit 1 identically) and deliberately scoped out by that plan's implementation notes, which record the IsADirectoryError fallback as a decision. Deferred from the run's code review r1 (record `.ai-playbook/reviews/2026-11-03-coverage-gate-checkpoint-twin-self-exemption-code-review-r1.md`, finding 9, pattern implementation#directory-operand-self-conflict-remains).

## Expected

A directory-shaped declaring plan at its natural location under the active plans surface passes its own coverage run.

## Suggested change

Exempt the declaring directory plan's own member files at the path-equality skip: before `if plan.resolve() == declaring.resolve(): continue`, after `if plan.resolve() == declaring.resolve() or (declaring.is_dir() and plan.parent.resolve() == declaring.resolve()): continue`, plus a twin test with the directory operand inside the active surface.

Cluster: docs/history/backlog/2026-11-03-twin-plan-note-resolution-site-drift.md (same gate's deferred captures from the twin plan's run)
