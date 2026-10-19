# Backlog: Bind from-holder release to the acquired done-lock generation

- **Filed:** 2026-10-18
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** lock lifecycle safety
- **Driving force:** safety
- **Urgency:** high
- **Source:** `.ai-playbook/reviews/2026-10-18-plan-review-done-live-owner-closeout-recovery-pe4f3ada4-r6.md`, F1; observed during authoring of `docs/history/plans/2026-10-18-done-live-owner-closeout-recovery.md`

## Problem

`scripts/done_run.sh finalize --from-holder` can select the tokenless release arm even when the current run still has its Step 0 lock witness. `scripts/done-lock.sh release_from_holder` reads the current lock metadata, then checks holder ancestry and compare-and-swap against that current image. If the original lock was stale-cleaned and reacquired by a holder in the caller's ancestry, this path can release the replacement generation.

The doc-only recovery plan changes the frozen prompt to require the original Step 0 token and witness, but does not change the runtime `--from-holder` path or fix this race. The next plan must bind every `done_run.sh` from-holder finalize call to the Step 0 generation when that witness exists, and fail closed for a recovery-owned call when it is missing. Ordinary direct lock-script callers without this run witness need a separately justified compatibility rule.

## Acceptance

- Given a replacement lock is acquired after Step 0 and its holder passes caller ancestry, `finalize --from-holder` refuses on generation mismatch and leaves the replacement lock metadata unchanged.
- Given the Step 0 generation still matches, the existing ancestry and compare-and-swap checks continue to govern release.
- Given a recovery-owned from-holder call lacks the Step 0 witness, finalization stops before tokenless release.
- The follow-up plan resolves machinery admission before introducing a new blocking refusal and names the removal or simplification and review date.

## Evidence

The r6 panel traced the explicit `from_holder` branch in `cmd_finalize` and the current-image behavior in `release_from_holder`. Its replacement fixture did not prove a generation guard; that fixture gap is part of the follow-up acceptance. The finding is a code path and race condition, not evidence that a proposed guard has already caught a live production case.
