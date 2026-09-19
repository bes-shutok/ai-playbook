# Backlog: reconcile graphify skill and package versions

**Captured:** 2026-09-16
Status: done
**Priority:** medium
**Origin:** skill-use verification during a codebase comparison

## Finding

The installed `graphify` package reported that the available graphify skill was
version `0.9.25` while the package was `0.9.51`, and recommended running
`graphify install`. The workflow therefore depends on skill instructions that
may not describe the installed command behavior.

## Suggested fix

Define and document one supported update path for the graphify skill and its
installed package. Add a compatibility check or versioning rule so a normal
graphify query either runs with matching guidance or reports a clear,
actionable incompatibility. Keep a host-neutral fallback for workflow steps
that assume a sub-agent or other optional runtime capability.

## Acceptance criteria

- The standard graphify workflow does not silently pair mismatched skill and
  package versions.
- The documented update procedure is executable on supported hosts and does
  not require an unavailable agent-specific tool.
- A regression check covers the version mismatch and the documented fallback.
