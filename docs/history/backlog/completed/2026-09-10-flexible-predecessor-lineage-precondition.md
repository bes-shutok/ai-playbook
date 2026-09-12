# Execute-plan predecessor lineage precondition should be flexible

Status: done
Disposition: done via execute-plan runtime guardrails (see docs/plans/completed/2026-09-11-execute-plan-runtime-guardrails.md)
Claimed by: docs/plans/2026-09-11-execute-plan-runtime-guardrails.md (2026-09-11)
Workflow: backlog
Source: user requirement clarification during execute-plan startup

## Problem

An implementation plan can require a branch to contain one exact commit SHA as
proof that prerequisite work is present. This is too brittle because equivalent
history may have been rebased, cherry-picked, squashed, or otherwise integrated
without preserving that exact object identity. The gate can therefore block
valid work even when the required predecessor task's outcome is present.

The execute-plan workflow needs to express predecessor requirements in terms of
work lineage and verifiable outcomes, not a project-specific commit identity.
The check should remain fail-closed when the required predecessor work cannot be
verified, while allowing valid histories that contain the predecessor work under
different commit identities.

## Suggested fix

Clarify the plan and execute-plan guidance so predecessor checks:

1. identify the prerequisite work by a neutral task or work item reference;
2. verify the relevant branch ancestry, changed artifacts, or other repository-
   local evidence appropriate to that prerequisite;
3. do not hardcode a single commit SHA as the only admissible proof; and
4. stop with a clear diagnostic when the prerequisite work cannot be verified.

Add tests or validation examples covering rebased, cherry-picked, and squashed
histories where the prerequisite work is present but its commit IDs differ.

## Scope

Review the execute-plan branch setup and any related plan-readiness or inclusion
guidance. Keep the rule runtime-neutral, repository-local where possible, and
free of project names, ticket identifiers, environment names, credentials,
secret values, and machine-specific paths.

## Severity

Medium: valid plan executions can be blocked by an unnecessarily strict
repository-history identity check.
