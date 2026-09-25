# Backlog: verify framework API and test-runner contracts during code review

Status: open
Priority: high
Consumer urgency: consumer-project external reviews caught framework-API and test-runner contract misses that full internal panels approved; shared review-agent lenses under agents/skills/review-agents/ serve consumer projects; never profile-defer
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: consumer-project failure feedback)
Workflow: backlog
Class: review-agent coverage
Driving force: correctness

## Problem

The review panel can approve source that imports a framework symbol or
annotation attribute without verifying the resolved dependency API, and it can
approve a targeted test command without checking the post-test verifier's
manifest selection. A later external review found both kinds of defects. The
same gap also lets duplicate migration versions and Docker probes on unrelated
unit tests survive review.

## Observed miss family

- library or framework annotation attributes were assumed to exist instead of
  being checked against the module's resolved artifact;
- migration versions were checked in one remapped integration location but not
  against every shared classpath consumer;
- targeted selectors and full-manifest verification were allowed to disagree;
- an auto-detected test extension performed container discovery before deciding
  whether the current class needed a container;
- a disabled empty integration test was treated as a placeholder instead of a
  release-evidence gap.

## Suggested fix

Extend the implementation and testing review contracts with a reusable
framework/build/test-runner audit. Require resolved API or compile evidence,
fresh-schema migration validation across shared consumers, selector-to-verifier
parity, early non-container fast paths, and an enabled assertion-bearing test
for each new safety boundary. Add a small helper or checklist so the panel
records the audit rather than relying on worker prose.

## Acceptance criteria

- A review worker must verify changed framework APIs against the resolved
  dependency or stage an explicit unverified-contract finding.
- A review of migrations and test runner hooks must compare targeted and full
  populations and identify shared classpath consumers.
- Disabled or empty safety-boundary tests cannot satisfy coverage claims.
- The review staging schema records the audit result or a named missing lens.

## Evidence

The originating review contained compile/API, duplicate-migration,
targeted-manifest, Docker fast-path, and disabled-integration-test findings that
were not emitted by the internal panel before external review.
