# Done owned-commit ledger can claim concurrent worktree commits

Captured: 2026-09-28 (source: skills-repo done closeout, owned-commits ledger append)
Status: open
Priority: high
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: self-serving
Consumer urgency: Consumer projects running done in linked worktrees need accurate commit ownership records; the skills-repo personal priority profile must not defer this shared-skill fix as formal-hardening for the skills repo alone.

## Problem

The done workflow builds `owned-commits-<run_id>.txt` by enumerating every commit from the last recorded SHA (or Step 0 `start_commit`) to `HEAD`. A linked worktree can land its own commit during that interval because done locks are per worktree and shared landing commits are separately serialized. The range then includes commits this done run did not create.

This happened during a closeout: concurrent worktree commits landed after Step 0 but before the first ledger append. The range recorded those commits as owned by the closeout. The commit ledger is an audit input, so false ownership can misclassify changes during closeout review.

## Exact location

`agents/skills/done/SKILL.md`, Step 1 owned-commits ledger append and Step 3 item 9; the `git rev-list --reverse BASE..HEAD` recipe.

## Expected

- Record each commit SHA at the point this run creates it, rather than infer ownership from all commits reachable after a baseline.
- Preserve multi-commit learn runs by recording every SHA that learn reports it created, in order.
- When a peer commit appears between this run's commits, ensure it is absent from this run's owned ledger.
- Add a fixture or scripted self-test that interleaves a peer commit between two owned commits and verifies exact ownership attribution.

## Severity and source reference

Severity: medium

Source: done closeout, first ledger append included concurrent worktree commits after Step 0; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The user requested running the done workflow, not changing its ownership-recording implementation. The current closeout records the observed ledger attribution defect for a later skill fix.

## Dedup probe

Search terms: `owned-commit ledger`, `git rev-list`, `peer worktree commit attribution`. Nearest open items concern worktree closeout baseline capture and done-manifest root identity, but neither tracks commits by run ownership. No open item covers interleaved commits in the owned-commit ledger range.

## Suggested fix

Change commit ownership tracking to consume exact commit SHAs returned by each owned commit operation, with a defined multi-commit handoff from learn. Add an interleaving test proving a concurrent commit is never appended to this run's ledger.
