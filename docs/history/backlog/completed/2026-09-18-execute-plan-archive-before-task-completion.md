# Backlog: prevent unsupported and premature execute-plan archival

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-18
Class: execute-plan plan lifecycle, archive-path safety, and completion evidence

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or machine path.

## Problem

An `execute-plan` run can move its plan out of the active plans directory before
the implementation and review lifecycle has actually finished. Two independent
defects were observed together:

1. The plan was moved to a directory named `plans_completed`, although the
   supported lifecycle destination is the resolved `{plans_completed_dir}` from
   the repository facts, for example `docs/plans/completed/`. A similarly named
   sibling directory is not a valid archive location.
2. The move happened while later implementation and review tasks were still
   incomplete. In particular, an archive operation occurred before the
   remaining task checkboxes, validation receipts, review/fix loop, and terminal
   receipt proved closure. The archive therefore looked like completion even
   though it was only a partial checkpoint.

The user had to repair the location manually and restore the plan to the
supported completed directory. This is both a path-integrity failure and a
temporal-ordering failure: archival was allowed to precede the predicate that
is supposed to authorize archival.

## Root cause

The workflow did not enforce one fail-closed transition for plan completion.
The archive action was treated as a completion step that could be performed from
the presence of implementation commits, a worker checkpoint, or a partial
review result. It did not first prove all of the following from the same current
plan and runtime state:

- the destination was resolved from `{plans_completed_dir}` rather than inferred
  from a folder name;
- every required task and acceptance checkbox was complete;
- every task had its required verification and `done` receipt;
- Phase 2 validation had passed;
- Phase 3 review/fix had reached a fresh blocking-clean result;
- the runtime manifest had a terminal state and terminal receipt; and
- the archive move and ownership-registry update completed as one lifecycle
  transition.

This is primarily Family E (temporal / ordering invariants), with Family D
(single source of truth) and Family H (verify the real thing, not the
abstraction) as secondary families.

## Required behavior

### 1. Resolve and validate the archive destination

- Read `{plans_dir}` and `{plans_completed_dir}` from the repository facts at
  runtime.
- Construct the destination only from the resolved `{plans_completed_dir}`.
- Refuse to archive when the destination is missing, ambiguous, outside the
  resolved plans root, or merely resembles a name such as `plans_completed`.
- Before moving, verify the source is the exact active plan associated with the
  current execute-plan manifest and digest.
- After moving, verify the source is absent, the destination exists at the
  resolved path, and the terminal receipt records that exact destination.

### 2. Make completion a single ordered transition

Archival must be the last lifecycle transition, not a progress marker. The
executor must remain on the active plan path while any required work remains.
The only permitted order is:

```text
implement remaining tasks
  -> verify each task and record its receipt
  -> mark only those task checkboxes complete
  -> run Phase 2 validation
  -> run Phase 3 review/fix until one fresh blocking-clean result exists
  -> verify all plan and manifest evidence agrees
  -> create the terminal receipt
  -> move to resolved {plans_completed_dir}
  -> append the ownership-registry row
  -> verify the archived path and terminal state
```

If any prerequisite is missing, the state remains active, paused, waiting for
capacity, recovering, needs-review, or needs-fix. None of those states may
archive the plan or produce a successful completion response.

### 3. Make recovery preserve unfinished work

If execution is interrupted after some tasks, resume from the active plan and
reconcile commits, checkboxes, logs, manifest, and review artifacts. Do not
move the plan merely to make a stale or abandoned run appear closed. If a bad
archive already occurred, recovery must record the relocation and restore the
plan to the supported active or completed path according to its actual evidence,
not according to the old folder name.

## Proposed implementation

Update the shared plan lifecycle and execute-plan runtime so that one
machine-checkable `archive_eligible` predicate owns the transition. Keep the
normal path simple: one resolved destination, one ordered predicate, one
terminal receipt. Do not add a recurring readiness review or a second review
ceremony for ordinary task progression.

The predicate should expose the first failed condition, for example:

```text
archive_eligible = false
reason = unchecked task: <task ordinal>
```

or:

```text
archive_eligible = false
reason = unsupported archive destination
```

The executor must not silently substitute the archive move, a clean working tree,
a commit count, or a worker summary for this predicate.

## Regression coverage

Add project-agnostic fixtures or tests for all of these cases:

1. A facts file resolves `docs/plans/completed/`; an attempted move to
   `plans_completed/` is rejected and the active plan remains in place.
2. A plan with an unchecked implementation task is rejected even when commits
   and tests exist.
3. A plan with implementation complete but no fresh blocking-clean review is
   rejected.
4. A plan with a clean review but no terminal receipt is rejected.
5. A plan with all required evidence and a valid resolved destination archives
   successfully, updates the registry once, and records the exact destination.
6. An interrupted run resumes from the active plan without creating a second
   archive or losing the unfinished task claim.
7. A recovery fixture detects a plan already placed in an unsupported sibling
   directory and reports the path-integrity failure explicitly.

Use neutral fixture names and temporary directories. Do not encode a product
repository, ticket, user, private URL, or machine-specific path in the tests.

## Acceptance criteria

- No lifecycle code or skill prose uses a hardcoded or inferred
  `plans_completed` destination.
- An archive attempt fails closed unless the destination equals resolved
  `{plans_completed_dir}`.
- An archive attempt fails closed when any required task, acceptance item,
  validation receipt, review/fix result, or terminal receipt is incomplete.
- The active plan remains available for recovery until the archive transition is
  authorized.
- Successful archival produces one registry row and a terminal receipt naming
  the exact destination path and plan digest.
- Recovery of a bad or premature archive is deterministic and does not delete
  the plan or rewrite its body merely to hide the lifecycle error.
- Regression tests cover both unsupported-path rejection and premature-archive
  rejection, plus the valid success path.
- The change remains project-agnostic and contains no sensitive or identifying
  details from the originating incident.

## Relationship to existing backlog

This item narrows the existing terminal-completion and interruption-inventory
work to the archive transition itself. It does not replace the broader state
machine, deadline, capacity, review, or terminal-receipt items. Its distinctive
scope is the invariant that an archive path is valid only when both the resolved
destination and the complete implementation/review evidence have been proven.
