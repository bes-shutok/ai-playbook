# Checkout-flow landing mismatch guard for the maintenance payload landing tails

Status: open
Priority: low
Workflow: backlog
Class: correctness
Driving force: correctness

## Problem

The maintenance payloads' landing tails pin the repository's default branch while worktree creation follows the canonical per-project base; in a configured checkout-flow project the landing critical section has no arm comparing the resolved creation base with the landing target, so an unattended landing could sweep operator-branch commits onto the default branch (the peer-byte guard's path set tolerates them by definition).

## Observed versus expected

- Observed: no arm compares the resolved creation base with the landing target; the peer-byte guard counts foreign paths as the branch's changed paths
- Expected: a fail-closed mismatch arm in the landing critical section (defer-landing with both refs named), or landing-to-resolved-base prescribed for checkout-flow projects

Origin: round-6 residual of the worktree-first standard-only-mode execution run (plan docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md, review round r6, deferred per the run's backlog-deferral default).
