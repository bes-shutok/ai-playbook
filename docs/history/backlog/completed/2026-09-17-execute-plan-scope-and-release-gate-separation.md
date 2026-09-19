# Backlog: separate implementation scope from external release gates

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-17
Class: execute-plan scope control and release evidence

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Problem

Implementation plans can grow by absorbing broker, deployment, operations, and
release-evidence requirements into the same task checklist. This makes local
implementation depend on evidence that the repository cannot produce and turns
normal execution into repeated plan redesign.

## Required behavior

Every plan requirement must be classified as exactly one of:

- IMPLEMENTATION_REQUIRED
- REPOSITORY_TEST
- EXTERNAL_RELEASE_GATE
- OPERATIONS_FOLLOW_UP

The plan validator must reject an item that is used as an implementation
checkpoint while being classified only as an external gate. External gates may
remain required for release closure, but they must not block a repository task
checkpoint unless the plan explicitly states the local dependency.

The execute-plan skill must preserve the classification when it creates task
ownership, allowed paths, manifests, and review scope. A review finding that
only improves external evidence must become a backlog item or release-gate
entry, not a new implementation task.

## Acceptance criteria

1. Plans have a machine-readable or mechanically checkable classification for
   every checklist item.
2. Repository tasks can checkpoint with all repository-controlled evidence
   complete even when external release gates remain open.
3. External gates retain an owner, evidence source, and closure condition.
4. The validator rejects a repository task whose completion depends on an
   unavailable external witness without an explicit dependency declaration.
5. Regression fixtures cover broker, deployment, and operations requirements
   that must remain outside local implementation scope.
6. The skill and fixtures contain no project-specific identifiers or sensitive
   values.

## Prevention

At plan creation and at the first readiness review, require a scope ledger that
maps each requirement to its evidence owner and execution environment. During
execution, do not promote a release-gate concern into implementation scope
without an explicit plan change and a new digest.
