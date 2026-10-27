# Backlog: Bind from-holder release to the acquired done-lock generation

- **Filed:** 2026-10-18
- **Status:** open
Quarantine: 2026-10-27
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** lock lifecycle safety
- **Driving force:** safety
- **Urgency:** high
- **Cluster:** `docs/history/backlog/2026-10-26-done-lock-context-recovery-after-compaction.md`
- **Cluster:** `docs/history/backlog/2026-10-27-done-finalize-release-leg-failed-despite-env.md` (same surface - `done_run.sh` finalize's done-lock release - different defect: this row owns the `--from-holder` generation-binding risk, that row witnesses the plain env-based release leg failing in the manifest-complete first pass)
- **Source:** `.ai-playbook/reviews/2026-10-18-plan-review-done-live-owner-closeout-recovery-pe4f3ada4-r6.md`, F1; observed during authoring of `docs/history/plans/2026-10-18-done-live-owner-closeout-recovery.md`

## Problem

`scripts/done_run.sh finalize --from-holder` can select the tokenless release arm even when the current run still has its Step 0 lock witness. `scripts/done-lock.sh release_from_holder` reads the current lock metadata, then checks holder ancestry and compare-and-swap against that current image. If the original lock was stale-cleaned and reacquired by a holder in the caller's ancestry, this path can release the replacement generation.

The doc-only recovery plan changes the frozen prompt to require the original Step 0 token and witness, but does not change the runtime `--from-holder` path or fix this race. The next plan must bind every `done_run.sh` from-holder finalize call to the Step 0 generation when that witness exists, and fail closed for a recovery-owned call when it is missing. Ordinary direct lock-script callers without this run witness need a separately justified compatibility rule.

## Acceptance

- First add a read-only or warning-only witness that distinguishes a matching Step 0 generation from a replacement generation on the recovery-owned from-holder route; it must never release or alter the replacement lock.
- Keep the existing ancestry and compare-and-swap checks for every release path.
- Do not add a new blocking refusal while the evidence remains a review finding rather than a true catch. If a true catch is observed, a later plan may propose promotion only with the incident link, expected catch frequency, false-positive cost, a review date, and a pre-registered registry-removal row naming sunset and promotion criteria.
- Keep the origin open for the warning-only/read-only investigation; do not delete it as moot because the current runtime route remains unbound to the original generation.

## Evidence

The r6 panel traced the explicit `from_holder` branch in `cmd_finalize` and the current-image behavior in `release_from_holder`. Its replacement fixture did not prove a generation guard. The finding is a code path and race condition, not evidence that a proposed guard has caught a live case; repository policy therefore admits only warning-only or read-only work until a true catch is witnessed.
