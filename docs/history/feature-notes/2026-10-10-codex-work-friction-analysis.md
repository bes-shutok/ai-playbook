# Codex Work Friction Analysis: Plan Execution on 2026-10-10

## Purpose

Use the long-running plan-scope gist session as a concrete case study for improving Codex work with the current skill set. The goal is to keep correctness and user control while making the normal path direct, bounded, and recoverable.

## What happened

The plan declared a **1-hour total execution budget**, with the largest task budgeted at **30 minutes**. The review-to-landing path took about **9 hours 40 minutes**: the first recorded plan review started at 13:24 Europe/Lisbon and the squash landing committed at 23:04. The execute-plan runtime itself ran from 16:36 to 23:05, about **6 hours 29 minutes**. These measures differ because the first includes plan certification and the second starts at execution setup.

The run recorded **12 plan-review rounds** and **6 Phase 3 code-review rounds**. Sidecars report 52 plan-review worker launches and 29 code-review worker launches. In light of the machinery-blocker audit, this volume is a cost signal: follow the already-landed review-round budget/delta policy rather than adding a new review class or checklist. The completed plan also carries a separate archive-gate recovery slice discovered during execution. The session preserved 35 execute-plan files and 29 review files before removing the ad-hoc worktree and branch.

The total elapsed time cannot be apportioned precisely. The runtime state does not record duration per review, worker retry, validation, wait, or closeout operation. The counts below identify repeated work, not its exact wall-clock share.

## Evidence-backed causes

1. **The plan contract was not complete before implementation.** Early plan rounds found missing report channels, undefined gist content, validation that checked presence rather than behavior, incomplete task file scope, and missing closure ownership. Later rounds also found the untracked referral disposition and an implicit future authorization step. The plan accumulated an archive recovery task that was separate from its original report-surface objective. These late discoveries required plan edits and more certification rounds.

2. **The review loop kept reopening work across changing or unchanged plan snapshots.** Twelve canonical plan reviews were recorded. R10 and R11 review the same source digest; R12 reviews the digest after checklist markers changed. This is evidence that the loop sometimes spent a review round on a bookkeeping-only plan change. Several earlier rounds did identify substantive gaps, so the count alone does not justify removing review.

3. **Worker evidence and discovered verifiers were misaligned.** Task 1's verifiers checked only for the generic word `review`, while each was mapped to all five acceptance criteria. The worker omitted the required envelope and parent verification was needed. The final run nevertheless advanced through existing driver verification and corrected-submission/evidence-contract recovery; it does not establish a need for a new parent-adjudication transition. The useful fix is to align the worker prompt and existing verifier construction. A separate parent-adjudication operation, receipt, retry loop, or preflight gate would add ceremony for a path the run ultimately recovered through existing operations, so that recommendation is withdrawn.

4. **Closeout ran the existing receipt steps out of order.** The pre-archive receipt was requested after the plan had moved, so the run restored an exact temporary copy, invoked the already documented driver stage, and removed the copy before final verification. The skill already specifies receipt-before-move ordering; the evidence points to missed sequencing, not a missing closeout mechanism.

5. **The declared budget did not give the operator a useful actual-versus-estimate signal.** A one-hour plan ran for more than six hours in the execute-plan runtime. The budget machinery handled usage limits, but the session artifacts do not show a wall-clock budget checkpoint that summarized elapsed time, remaining work, and the cause of overruns. A hard stop is not the right default; a clear continuation report would have made the scale of the overrun visible earlier.

## What was not the cause

- The implementation was not left unfinished: both tasks were checkpointed, Phase 2 validation passed, the final fresh review found no blocking findings, the plan archived, and the worktree and branch were removed.
- The six code-review rounds were bound to changing source digests in the first five rounds; the records do not support treating every Phase 3 round as redundant.
- The run contains a single successful final squash landing. There is no evidence that repeated squash attempts caused the elapsed time.
- The available timestamps establish elapsed duration but do not distinguish active agent work from provider wait, user wait, or idle time.

## Changes that would reduce friction

### Before implementation

- Use the existing plan-quality review and delta-review path to fix substantive omissions. Do not add a separate readiness checklist or approval gate: the audit identifies review-loop non-convergence as the largest time sink, and this run's 12 rounds show that another review ceremony needs evidence before adoption.
- Keep the plan's declared budget visible at dispatch and in each continuation report. At a checkpoint, report elapsed wall time and the concrete remaining gates. If the estimate is exceeded, continue under the user's standing direction unless a real safety or state-integrity blocker exists; do not create a new approval gate.

### During execution and review

- Align the worker response with the existing evidence envelope and make seeded verifiers check the actual criterion. Reuse the existing `verify`, `recover-evidence-contract`, and `recover-corrected-submission` operations; do not add a parent-adjudication transition for this single incident.
- Apply the existing review-round budget and delta-review policy. The same-digest rounds are the clearest redundant work; fix the existing caller/policy path if it launches another panel on unchanged reviewed bytes. Do not add a separate metadata-exemption scheme or review panel.
- Keep blocker capture outside the implementation scope and use the ordinary backlog files after the plan lands; do not add a new execution receipt or ledger. Follow the existing pre-archive receipt-before-move and artifact-transfer sequence rather than adding a recovery command.

### At closeout

- Follow the existing pre-archive receipt and closeout transfer order. The run's temporary-copy recovery was needed only because the order was missed; do not add a new driver operation or receipt type.
- Keep the existing session manifest as the source of run state and avoid additional copied manifests unless a recovery changes the state they describe.

## Suggested priority

1. Fix the worker prompt and criterion verifiers at their existing boundary; retain current bounded recovery operations and add no special adjudication path.
2. Apply the already-landed review-round budget and delta-review policy so unchanged reviewed bytes do not trigger another panel.
3. Follow the existing pre-archive and transfer sequence; capture operator-directed blocker rows outside implementation scope without a new receipt.
4. Keep wall-clock budget reporting as an optional advisory line in existing reports, with no new state or stop condition.

## Source records

- Completed plan: `docs/history/plans/completed/2026-10-10-plan-scope-gist-surface.md`
- Execute-plan session manifest and runtime state: `docs/tmp/execute-plan/2026-10-10-plan-scope-gist-surface/manifest.md` and `runtime_state.json`
- Plan-review series: `docs/history/reviews/2026-10-10-plan-review-plan-scope-gist-surface-r1.md` through `r12.md`
- Phase 3 review series: `docs/history/reviews/2026-10-10-plan-scope-gist-surface-code-review-r1.md` through `r6.md`
- Related open backlog records: `2026-10-10-execute-plan-adjudication-recovery.md`, `2026-10-10-execute-plan-discovered-verifier-quality.md`, and `2026-10-10-simplify-execute-plan-review-rebinding.md`
