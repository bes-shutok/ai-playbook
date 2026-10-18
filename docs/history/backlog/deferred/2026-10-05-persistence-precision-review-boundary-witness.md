# Backlog: review persisted write values at database precision boundaries

- **Filed:** 2026-10-05, consumer review follow-up
- **Status:** deferred (2026-10-06, operator adjudication: foreign-origin; the Java/PostgreSQL nanosecond-vs-microsecond precision mismatch in the consumer service belongs in the consumer repo's backlog, not here)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback (company)
- **Consumer urgency:** consumer projects using code review need persistence-boundary checks; the skills-repo personal priority profile must not defer this as formal-hardening for the skills repo alone.
- **Class:** fence-class
- **Driving force:** reliability

## Problem

A write-path review can accept a response built from the pre-persistence object without checking whether the database stores the same value. A consumer service exposed nanosecond `Instant` values in POST and PUT responses while PostgreSQL `TIMESTAMPTZ` stored microseconds. The integration assertions initially failed; the correction relaxed assertions to tolerate precision loss, leaving the response-versus-read mismatch in production. An external PR review later connected the boundary mismatch to the service implementation.

## Evidence

- The consumer's integration test failure showed nanoseconds in the returned value and microseconds after PostgreSQL persistence.
- The first test correction allowed a one-microsecond tolerance instead of normalizing server-owned write timestamps before constructing the persisted entity and response.
- The internal review series did not identify the production normalization gap. Its final round separately identified that the replacement test did not prove persistence, but it did not require comparison of the write response with a subsequent read at the database's precision.
- An external PR review on 2026-10-05 identified both insert and replacement timestamp paths. Severity: Medium. Source: receiving review of the consumer branch; exact comments remain in that repository's review system.

## Exact location

- `agents/skills/review-agents/testing.md`, persistence write witnesses and integration-test evidence.
- `agents/skills/review-agents/quality.md`, database boundary and response-value tracing.
- `agents/skills/review-agents/review-panel-selection.md`, targeted follow-up coverage for write paths backed by precision-limited scalar types.

## Suggested fix

For create and replacement flows that persist server-owned timestamps or other representation-limited values, require a witness that compares the API write response to a fresh persisted read. Drive the fixture with a value more precise than the database column and verify the chosen normalization policy at both the service and HTTP boundaries. Keep assertion tolerance only when the contract deliberately permits an unspecified difference.

## Dedup probe

Searched open backlog filenames and Problem bodies with `rg -n -i 'database precision|timestamp precision|round.trip.*precision|persistence.*round.trip' docs/history/backlog --glob '*.md'`. The nearest match is `2026-10-05-segment-rule-compiler-unknown-fields.md`, a compiler input-validation issue; no open item covers response values that differ from database-normalized values. Keep this item separate.

## Why not fixed now

The consumer implementation is being corrected in its current branch. Shared review-agent patterns need a separate change with focused fixtures and review-skill validation.

## Source

- Consumer integration-test failure and external PR review, 2026-10-05; five-lens internal review record series, rounds 1 through 8. Capture hygiene: scan-public-hygiene --files pass.
