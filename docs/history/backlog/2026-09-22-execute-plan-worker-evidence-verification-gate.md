# Backlog: execute-plan must verify worker evidence instead of trusting worker text

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-22
Class: execute-plan evidence contract gap

## Problem

An implementation worker can return a successful narrative with test counts
and scope claims that are not sufficient to prove the task. In the observed
session, Task 3 reported successful worker, integration, migration, and
graphify coverage. Independent review then found that the claimed coverage did
not exercise the new worker or recovery path, the migration did not implement
the stated batch-only schema transition, and several required test partitions
were absent.

The current result contract requires non-empty evidence, but a log path and
natural-language command summary are not enough to prove that the commands ran
against the final digest or that required acceptance cases were covered.

## Exact location

- `agents/skills/execute-plan/runtime-contract.md`, normalized result schema
  and worker execution contract.
- `agents/skills/execute-plan/SKILL.md`, worker log and done handoff gates.
- Session evidence: the Task 3 implementation log in the execute-plan session
  directory and the subsequent review findings.

## Suggested fix

Introduce a machine-verifiable evidence envelope:

1. Require each validation entry to include command, working directory,
   exit code, start/end time, selected test identities, and captured output
   digest.
2. Require a final changed-path manifest and compare it with the task
   allowlist before accepting success.
3. Derive required test identities from the plan checklist and reject success
   when a worker claims a broader requirement without matching evidence.
4. Have the parent or a verifier rerun a small immutable probe for every
   high-risk acceptance criterion before `done`.
5. Add a hook that blocks `done` when the worker log contains only prose or
   claims tests that are absent from the recorded command artifacts.

## Severity and source reference

Severity: high

Source: observed Task 3 review, 2026-09-22; independent review contradicted
worker evidence on migration coverage, worker integration coverage, fencing,
and recovery tests. Capture hygiene: pending until
`scan-public-hygiene.sh --files` passes.

## Why not fixed now

The required change is to the execute-plan evidence schema, verifier, and
done gate. It is intentionally not implemented inside the application repository.

## Driving force

Driving force: testability

Secondary force: observability
