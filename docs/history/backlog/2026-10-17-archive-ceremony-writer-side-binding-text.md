# Backlog: writer-side binding-text standardization for archive receipts

- **Filed:** 2026-10-17
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding residue
- **Class:** docs consistency
- **Driving force:** simplicity
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, completion evidence
- **Cluster:** docs/history/backlog/2026-10-18-acrem-certification-residuals.md (same surface: residuals tracked against the landed archive-ceremony plan)

## Problem

Execute-plan's completion-evidence text does not ask the writer side to record the staging binding fields (`extensions.plan_identity`, `source_digest`, `verdict`) when a receipt or a marked reconstruction is produced. The archive-ceremony bound-receipt acceptance plan adjudicated the writer side out of scope: the acceptance universe reads staged plan-review sidecars, which already carry the fields through the staging flow, and exec-series receipts keep their filename path, so no landing dependency exists. This row tracks the optional standardization so the adjudicated residual has a named home instead of silent silence.

Dedup probe: searched `docs/history/backlog/` and `docs/history/plans/` for completion-evidence binding-text rows on 2026-10-17 (rg "completion-evidence" plus "binding fields"); no duplicate row exists, and the deferred legacy-filename sibling owns a different defect class.

## Evidence

- `agents/skills/execute-plan/SKILL.md`, completion-evidence paragraph: the reconstruction remedy is recorded as a note naming the missing exec-review record and the re-verification evidence, with no binding-field clause anywhere in the skill (verified 2026-10-17 by the archive-ceremony plan's r2 contract-docs worker).
- `docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md`, Assumptions and Review Scope: the writer side is out of scope with this row named as the residual home.
- Staged plan-review records carry the binding fields through the staging validator, so the gate-side acceptance never depends on this row.

## Expected

Decide whether the completion-evidence text should standardize recording the binding fields when a receipt or marked reconstruction is produced (one clause), or record the decision to keep the text unchanged. Either outcome closes the residual the archive-ceremony plan named.

## Immediate workaround

None needed: the acceptance path reads the staging sidecar, not writer-side text.
