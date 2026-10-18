# Backlog: make the review-evidence handoff resumable

- **Filed:** 2026-10-17, after execute-plan Task 1 stopped for its missing input
- **Status:** open
- **Workflow:** plan-worthy evidence-contract follow-up
- **Priority:** high
- **Driving force:** reliability + simplicity
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, Task 1 input contract for `docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md`
- **Origin:** `docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md`
- **Cluster:** docs/history/backlog/2026-10-17-investigate-user-directed-gate-workaround.md (same defect class: a blocked lane's recovery path needs an explicit continuation contract); docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md (same surface: worktree run-artifact homes and the closeout migration); docs/history/plans/2026-10-18-plan-declared-missing-input-fallback.md (covered: the landed plan-declared missing-input fallback plan)
- **Witness:** the current execute-plan session's `input-gate.md` and `manifest.md` under `docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/`; the plan requires an operator-provided anonymized finding-to-review summary but provides no durable handoff location or retained source artifact.

## Problem

The review-gap investigation is blocked before its first task because the required anonymized summary is not available in the repository's run inputs. The origin backlog row describes the later lock-ordering and terminal-dedupe findings and an earlier deferred progress invariant, but does not carry the review-round digests, owning stages, or per-finding triage needed to classify those reports. Reconstructing those missing fields from the summary prose would violate the plan's explicit no-inference rule.

## Expected

Make the evidence input reproducible without weakening the finding-to-review classification. A follow-up should name where the sanitized summary is delivered, who supplies it, and how the run verifies that it covers each finding and review digest. If it cannot be recovered, provide a bounded disposition that records unavailable classifications as indeterminate and leaves unsupported lens or triage changes untouched.

## Scope arms

- Keep the original review-gap question and add a durable, anonymized summary handoff before execution.
- Keep the original question but narrow the investigation to repository evidence, explicitly recording findings whose digest or triage history is unavailable as indeterminate.
- Remove the summary prerequisite and infer classifications from the origin row and plan-review records.
- Close or remove the original origin because its required evidence was not available in this run.

## Recommendation

Keep the original origin and its scope. The missing artifact blocks classification but does not disprove the underlying review gap, so do not remove or simplify the origin based on this run. The operator directed the second scope arm for the current run: revise the certified plan, obtain a fresh plan review, and use repository evidence while recording unsupported classifications as indeterminate. Retain the durable summary handoff as the preferred path when the source review can supply it; reject inference because repository plan-review records do not contain the consumer implementation digests or full per-finding dispositions.

## Immediate continuation path

For this run, resume from the preserved worktree only after the explicit plan revision passes fresh review. Use the tracked origin and handoff rows; plan-review records are gitignored supplemental context and cannot establish incident classifications. Record missing stage, digest, changed-path, triage, or finding-to-concern relationship evidence as unavailable, and leave unsupported classifications indeterminate with no associated lens or triage edit. Do not access the consumer repository or infer a matrix row. For future runs, deliver the complete anonymized summary in the run-scoped gitignored input area, one entry per finding with owning stage, covered digests, related earlier records, and triage disposition, with identifiers, code, reviewer identities, and review quotes removed.

## Rejected alternatives

- Infer buckets from the origin row: rejected because it reports finding themes but does not bind each finding to the reviewed implementation digests or complete triage history; witnessed in this origin's `Problem` and `Evidence` sections.
- Remove the original origin: rejected because the missing input says nothing about whether the shared lenses missed a real invariant; witnessed in the active plan's `Terms` and the origin's `Expected` section.
- Add a new review gate or checklist: rejected because the blocker is missing evidence and handoff, not a demonstrated failure of the existing review stages; witnessed in the active plan's `Gate delta` and the origin's `Rejected directions`.

## Investigation update (2026-10-17)

The remove-or-keep review found that the blocker originates in the certified plan's evidence contract: the four-bucket classification requires per-finding digest and triage evidence, and the missing-summary stop prevents guessed classifications. The underlying review-gap origin remains valid because the missing artifact does not disprove the reported correctness findings or the earlier deferred progress invariant. Keep that origin marked covered by its investigation plan; do not delete or weaken it. Simplify only this run's response by using the plan-reviewed repository-only fallback, with unsupported finding-to-concern relationships and classifications explicitly indeterminate and no resulting lens or triage edits.

The existing `PLAN-PROMPTS.md` investigation entry already records this recommendation, the rejected generic bypass and origin-removal arms, and the missing delivery contract. No duplicate investigation entry is needed. Keep this follow-up open until a durable summary location, supplier, coverage verification, and parked-run resume contract are decided. Evidence: the origin row's `Problem`/`Expected` sections, the active plan's r2-certified no-inference contract, this run's `input-gate.md`, and the existing investigation entry.
