# Backlog: archive ceremony misses legacy execution-review filenames

- **Filed:** 2026-10-09
- **Status:** deferred (2026-10-09, operator routing: disposition rides the closeout-gate demotion program in docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md; warning-only conversion of archive-ceremony removes the blocking shape this row witnesses; the legacy filename grammar fix becomes cosmetic and folds into the same conversion if trivial)
- **Cluster:** docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed archive-gate compatibility blocker
- **Class:** closeout reliability
- **Driving force:** reliability + recoverability
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, archive-ceremony gate

## Problem

The archive-ceremony gate recognizes execution-review records only in the `*-plan-review-<slug>-exec-r<N>` filename form. An existing valid execution-review pair using the earlier `*-exec-review-<slug>-r<N>` form is present in the reviews home but is reported missing, blocking an unrelated local landing that scans the completed-plan corpus.

## Evidence

- During the 2026-10-09 landing of the review-policy plan, `bash scripts/done_sweep_gates.sh pre-commit` failed on completed plan `docs/history/plans/completed/2026-10-08-plan-directory-shape.md`, naming the absent `*-plan-review-plan-directory-shape-exec-r<N>` series.
- The primary reviews home already contained `docs/history/reviews/2026-10-08-exec-review-plan-directory-shape-r1.md` and its stats sidecar, with `Type: Execution Review`, `artifact_slug: plan-directory-shape`, and zero unresolved blocking findings.
- The receipt was retained but its older filename does not match the gate's current discovery grammar. This is distinct from a genuinely missing or stranded execution review.

## Expected

Make archive discovery recognize the supported legacy execution-review naming form, or provide a deterministic one-time migration that preserves the original record bytes and keeps the record's type, artifact, round, and sidecar binding intact. A valid legacy receipt should satisfy discovery without inventing review evidence.

## Rejected alternatives

- Reconstruct a new review panel for this plan: rejected because the original execution-review pair is present and records its real panel and findings.
- Treat every missing canonical filename as a genuinely missing review: rejected because the observed receipt exists in the primary reviews home under the earlier documented name.
- Hand-copy aliases for each encounter: retained only as a closeout workaround; rejected as the permanent mechanism because the gate should resolve compatible record names consistently.

## Source

- Observed during the 2026-10-09 local landing of `review-policy-scope-complexity-cap-checkpoints`.
