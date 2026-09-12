Status: deferred
Priority: low
Created: 2026-09-11
Origin: user threat-model decision 2026-09-11 (guidelines section 64); re-cert loop r9-r14 findings

# Deferred: malicious-worker hardening for the execute-plan runtime

Deferred until a trigger condition fires: a realistic tampering incident, or deployment to a shared/multi-user host. Not blocked on a schedule; do not fold these into plans or reviews while deferred.

## What is deferred (the whole anti-adversarial-worker apparatus)

- Out-of-tree policy-anchor digest fence (`~/.execute-plan/<repo-hash>/.../policy-anchor.json`): keying, write-once rules, permission hierarchy (0600/0700), crash-window anchor-first ordering, HOME pinning for anchor writes, the `policy-anchor-mismatch`/`policy-anchor-missing` reason codes and their witnesses.
- Anti-spoof seed recognition: sentinel-conjunction exemptions, out-of-tree seed tokens, seed-marked anchors.
- Launch-path sibling-anchor sweep / any GC of security state; age-based pruning.
- Pre-upgrade trust-on-first-use re-anchoring migration and its merge-base sanity check.
- Receipt-rejection and lock migration hardening framed against a forking/adversarial operator (keep the plain fail-closed error paths).

## What stays in scope (correctness, not malice)

- Launch record snapshot (baseline_revision, generation, timestamp) at claim launch and the witnesses that block when the baseline or generation changed under two honest sessions.
- Structural non-reentrant manifest lock with post-adapter-window re-read and `stale-claim` on change.
- Existing functional scope enforcement (allowed_paths), fail-closed error handling, closed reason-code registry.

## Trigger to revisit

A real incident of manifest tampering, a shared-host deployment, or the user reopening the threat model. On trigger: start from the r9-r14 review artifacts (docs/reviews/2026-09-11-plan-review-execute-plan-runtime-residuals-r9..r14*) which contain the full design space (anchor keying, seed tokens, sweep, TOFU migration) already reviewed six times.
