# Backlog: normalize plan identity slug in handoff reconciliation

Status: open
Workflow: backlog
Priority: high
Origin class: self-serving
Class: fix-class
Skill/step: `agents/skills/execute-plan/implementation-loop.md`, Done-pending handoff reconciliation
Driving force: reliability (primary), maintainability (secondary)

## Problem

When runtime state stores the canonical lowercase slug used by claims and review artifacts, a plan filename with uppercase letters can make the handoff reconciler refuse with `plan-identity-mismatch`. The artifact-slug derivation lowercases the plan identity, while the handoff helper's `feature_slug` comparison only strips a date prefix and preserves case. The completed date-prefix correction does not cover this case. This prevents the normal receipt-backed transition for an accepted worker result.

## Expected

The reconciler compares runtime state and the plan using one canonical slug derivation, while retaining the exact resolved plan path and current reviewed bytes as the receipt and review identity.

## Evidence

The refusal was reproduced with an uppercase plan filename and a lowercase runtime slug. Calling the unchanged reconciler through a lowercase symlink to the same resolved plan path passed its claim, review, digest, scope, and receipt checks; the receipt recorded the original resolved plan path. This demonstrates that the remaining refusal is caused by inconsistent slug normalization.

## Remedy

Align the handoff helper's identity comparison with the canonical artifact or session slug used to create runtime state, and add a regression covering uppercase filename characters while keeping the exact resolved plan path binding.

## Dedup probe

The completed date-prefix identity correction covers dated path stripping. Its residual refusal item covers artifact-slug and review-evidence test gaps only. Neither covers case normalization in the handoff helper's plan identity comparison.

Capture hygiene: `scan-public-hygiene --files` pass; `check-no-em-dash file` pass.
