# Backlog: bulk deferral/disposition sweeps must cross-check claimed origins before moving items

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-22
Class: backlog/maintenance workflow gap (witnessed during the 2026-09-22 formal-deferral full sweep)

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Observed vs expected

Observed: a one-session sweep classified all open backlog items and moved 72
formal ones to `deferred/` by triage verdict alone. Three moved items were
claim-encumbered and had to be un-deferred after the fact: one was a listed
origin (scope of record) of a certified, pending-execution plan, and two were
closure-pending items that another certified plan's validation gate requires to
read `Status: closed (fixed by batch-2 phase-2)`. Deferring them contradicted
the certified plans' scopes and gates.

Expected: a disposition sweep (defer, close, or reopen in bulk) cross-checks
every candidate slug against claim surfaces BEFORE moving it: grep the slug
over the plans directory's non-completed plan files (origin lists and
validation-gate literals). A hit means the item is claimed: skip and annotate,
never defer. Ownership beats triage verdict. The reverse direction (an
executed plan leaving origins open) is already tracked; this item is the
triage-side mirror.

## Suggested fix

- One mechanical pre-move check per candidate: grep the slug over root plan
  files and treat hits as claimed.
- Encode the check in the maintenance skill's selection/grouping duty when the
  project-priority-profiles plan executes, and in any future manual sweep
  prompt template.
