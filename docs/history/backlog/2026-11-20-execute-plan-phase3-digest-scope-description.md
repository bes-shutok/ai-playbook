# Backlog: align execute-plan Phase 3 digest description with reviewed-scope hashing

Cluster: docs/history/backlog/2026-11-19-code-seal-verify-digest-rider-gap.md
Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Class: fix-class
Driving force: docs + efficiency
Review origin: `.ai-playbook/reviews/2026-11-20-self-heal-explicit-workaround-not-carried-through-code-review-r1.md` (digest reconciliation; no finding was staged)

## Problem

`agents/skills/execute-plan/phase-3-review.md` says the code-family `source_digest` is SHA-256 of the complete `git diff <base>...<head>` bytes. The verifier actually calls `reviewed_scope_bytes` in `scripts/corrections_record.py`, which excludes `docs/history/backlog/` at the Git pathspec layer. The completed code-family scope plan also defines that filtered byte function as canonical (`docs/history/plans/completed/2026-10-24-code-family-cert-digest-scope.md`, Terms and Task 1). A Phase 3 run following the raw-diff wording can therefore stage a record that `review_record_selection.py verify-digest` rejects as stale, creating avoidable rework despite the verifier behaving correctly.

## Trigger

A code-family review follows the Phase 3 digest-family paragraph while its branch delta includes backlog bookkeeping. The issue is documentation drift; the selector remains the authoritative freshness instrument.

## Dedupe

Searched open rows and covered records for this skill and Phase 3 digest family. `docs/history/backlog/2026-11-19-code-seal-verify-digest-rider-gap.md` covers a different failure mode: a seal-path rider makes a record stale and re-bind refuses. The completed code-family digest-scope plan defines the filtered bytes but does not update this module paragraph. Keep this wording gap separate and clustered with the rider issue.

## Suggested resolution

Update the Phase 3 digest wording and any nearby examples to name the `reviewed_scope_bytes` contract and its configured exclusions. Keep the source digest, round seal, and freshness check bound to the same bytes. Add no new validator, gate, or review step.

## Evidence

- `agents/skills/execute-plan/phase-3-review.md`, Digest-family ownership: raw complete-diff wording.
- `scripts/review_record_selection.py`, `verify_digest`: recomputes through `_reviewed_scope_bytes`.
- `scripts/corrections_record.py`, `BOOKKEEPING_PREFIXES` and `reviewed_scope_bytes`: excludes `docs/history/backlog/` and distinguishes bookkeeping-only from empty or unresolved diff results.
- `docs/history/plans/completed/2026-10-24-code-family-cert-digest-scope.md`, Terms and Task 1: canonical reviewed-scope byte function.
- Execute-plan Phase 3 r1 capture: first raw-diff digest was refused; the selector-owned filtered digest passed. The raw capture and correction are recorded in the current run's review log before its Phase 5 cleanup.

Severity: Low. The freshness gate catches the mismatch before certification and the record can be corrected, so the impact is avoidable rework rather than a stale certification.

Why not fixed now: This execution plan's explicit scope is self-heal recovery guidance and four origin rows. Editing execute-plan review machinery or its policy text is outside the plan's must-fix paths; the selector's verified behavior is already correct.

No feature-level implementer SOT exists for this skill wording issue; route through this backlog row and its investigation prompt, with no backlink task.

Capture hygiene: `bash scripts/scan-public-hygiene.sh --files docs/history/backlog/2026-11-20-execute-plan-phase3-digest-scope-description.md` pass.
