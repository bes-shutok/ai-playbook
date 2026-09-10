# Backlog: strengthen JVM review-cycle coverage

Status: open
Workflow: backlog
Source: anonymized external review follow-up from an execute-plan Phase 3 Java/Spring cycle
Severity: Medium overall; individual findings range from Low to High by reachability and data impact
Class: review-cycle coverage hardening

## Problem

A fresh five-worker review can reach a blocking-clean result while still
missing issues that cross static hygiene, boundary semantics, security, and
build configuration. The observed gap covered four reusable classes:

1. Unused imports, fields, methods, parameters, constants, and helpers in the
   changed branch. Java compilation does not reliably report unused members.
2. Null and missing-value behavior at generated request, mapper, and response
   boundaries. Omitted, explicit-null, empty, and present values can have
   different contract meaning.
3. Free-form downstream error messages or details reaching a client response
   or log without an allowlist and bounded service-owned message.
4. Changed dependency coordinates and outbound service URL configuration being
   reviewed without an advisory, compatibility, or transport-security check.

The review workflow also allowed a Java/Spring staging record to list an
overlay and project guidance without proving that the shared Java and JVM
guidelines were included and applied. The same cycle exposed additional
review cases that should be explicit rather than relying on a broad quality
label:

5. Error handling at a shared conversion boundary can silently change a
   top-level failure into a successful per-item result. Review must preserve
   each caller's raise-vs-degrade policy when a helper is reused.
6. A rollout flag can accidentally control readiness for an independent
   capability. Review must check the complete flag and configuration matrix,
   not only the default deployment mode.
7. A time budget can expire after the controller returns but before the
   serialized response is emitted. Review must check the final transport
   boundary and the lifecycle of any scheduled timeout resources.
8. A dependency API can compile successfully while rejecting a value at
   runtime because of reserved names, changed validation, or changed default
   behavior. Review must include a small executable compatibility witness for
   changed direct API usage.
9. Living documentation can describe an integration as active when the
   executable consumer or producer is absent. Review must reconcile status
   claims with implementation evidence and record explicit deferrals in a
   durable handoff.

## Location

- `agents/skills/execute-plan/SKILL.md`, Phase 3 review selection and clear-round quality bar
- `agents/skills/doing-code-review/SKILL.md`, Guideline Pack and worker prompt requirements
- `agents/skills/doing-code-review/java-spring.md`, Java/Spring review triggers
- `agents/skills/review-agents/simplification.md`, dead declaration detection
- `agents/skills/review-agents/review-panel-selection.md`, risk-signal floor
- `projects/.ai-playbook/java_guidelines.md`, shared Java review guidance

## Suggested fix

Keep the five-worker panel, but make the following evidence mandatory for
Java/Spring changes:

- Run a complete changed-source declaration census and report the search or
  static-analysis evidence.
- Enumerate nullable and generated-model states, then require a discriminating
  assertion for each state that matters to the contract.
- Trace downstream error fields to every response and log sink, preserving only
  bounded codes, messages, and explicitly safe details.
- Audit every changed dependency coordinate against a current advisory source
  and run compatibility checks for direct API usage, including values that
  may be reserved or specially validated by the library.
- Validate outbound URL schemes at the configuration boundary when encryption
  is required, with an explicit local loopback exception only.
- Trace shared conversion and persistence helpers to every caller and verify
  that infrastructure failures remain top-level failures while only
  explicitly row-local problems degrade to per-item results.
- Exercise the relevant feature-flag and configuration matrix so independent
  capabilities cannot become ready or unavailable through an unrelated flag.
- Verify time-budget enforcement at the last response/serialization boundary
  and inspect scheduled executors, callbacks, and cleanup for per-request
  resource leaks.
- Reconcile every changed living-document status claim with executable code,
  configuration, and an integration witness; when scope is intentionally
  deferred, require a durable backlog item and an explicit owner/handoff.
- Require the shared Java, JVM, and coding guideline paths plus applied rule
  hints in staging metadata before a clear round can exit.

## Acceptance

- A Java/Spring Phase 3 staging record contains the complete Guideline Pack
  paths and applied Java rule hints.
- The clear-round gate rejects missing Java review evidence when any listed
  surface is present.
- The simplification worker can stage unused changed declarations without
  treating compiler success as proof of use.
- The correctness/testing workers cover omitted, explicit-null, empty, and
  present states where the contract distinguishes them.
- The risk worker checks downstream error sinks, changed dependency coordinates,
  application-controlled outbound URL schemes, independent readiness flags,
  and resource lifecycle at timeout boundaries.
- The correctness worker checks that shared helpers preserve each caller's
  raise-vs-degrade error policy and that malformed infrastructure data cannot
  become a successful partial response.
- The compatibility witness executes changed direct library calls, including
  reserved-name and validation behavior that compilation cannot prove.
- The contract/docs worker reconciles living-document status claims with
  implementation evidence and records intentional deferrals as durable
  handoffs rather than leaving them only in review notes.
- A generic fixture or self-test demonstrates each check without using real
  service names, credentials, customer data, ticket identifiers, or internal
  URLs.

## Why not fixed now

This backlog records the reusable review-system gap separately from the product
change that exposed it. The guideline and prompt updates in this patch establish
the policy; broader executable self-tests and static-analysis support should be
implemented and reviewed as a dedicated skills-repository change.
