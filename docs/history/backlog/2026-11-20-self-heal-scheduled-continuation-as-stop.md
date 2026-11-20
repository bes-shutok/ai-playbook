# Backlog: scheduled continuation is mistaken for an immediate stop

- **Filed:** 2026-11-20, operator-reported deferral to a future continuation
- **Status:** covered-pending-execution (docs/history/plans/2026-11-20-self-heal-recovery-direction-continuation.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** efficiency + clarity
- **Skill/step:** `agents/skills/self-heal/SKILL.md` Recovery 1-5 and Resource cleanup disposition
- **Catch frequency:** one reported instance in the current interaction; the user asked why work could not proceed before the quoted 17:38 UTC continuation.
- **False-positive cost:** waiting for a future run when safe work is available; treating a scheduled timestamp as permission to remove resources could destroy live work.
- **Review date:** 2026-12-04
- **Dedup probe:** the completed 2026-11-20 recovery-direction plan already covers explicit workaround carry-through. The resource-cleanup contract separately requires ownership and writer quiescence, verified destinations, and an authorized closeout. This row isolates whether the scheduling explanation obscured those current-action checks or reflected a genuine owner/closeout boundary.
- **Cluster:** `docs/history/backlog/2026-11-20-self-heal-explicit-recovery-direction-recurrence.md` (same self-heal recovery handoff; this row owns the future-fire-time explanation and current-action check, the sibling owns repeated explicit-direction handling)

## Problem

The user reports being told that a continuation was armed for 17:38 UTC, then asked why the named worktree and branch could not be dealt with immediately. The interaction does not preserve the assistant's underlying state inspection, so the record cannot establish whether a live owner, writer, untransferred artifact, or closeout gate actually required waiting. The issue is that the future fire time was presented without the concrete current blocker or an immediate-action assessment.

## Expected

An armed continuation is scheduling context, not by itself a reason to stop current authorized work. On a user's renewed direction, re-derive the current owner, writer state, worktree contents, artifact destinations, and applicable closeout gate. Proceed with any currently authorized independent or cleanup action that passes its source-defined prerequisites; otherwise report the exact failing prerequisite and route the remainder through the owning continuation. Never remove a live or ambiguous resource merely because the user asks to act now.

## Suggested direction

Inspect the scheduling and ownership contracts alongside self-heal's resource-cleanup and execute-plan/done closeout rules. Decide whether self-heal needs a short cross-reference stating that a future fire time alone does not answer the immediate-action question, or whether the existing per-resource and ownership language already covers it and the defect was a missed check/report. Preserve the rule that only the owning closeout removes protected resources. Add no scheduling machinery or new state.

## Evidence

- The user quoted the explanation that the armed continuation was scheduled for 17:38 UTC and asked why the worktree and branch could not be handled immediately. This is the operator's direct report; the assistant's original state probes are unavailable.
- The user's repeated requests named the worktree and branch and explicitly asked self-heal to find a workaround. This shows the user's desired outcome and timing, not proof that resource-removal gates passed.
- `agents/skills/self-heal/SKILL.md` Resource cleanup disposition requires a named resource, quiesced owner/writers, and verified destinations; Recovery step 4 requires re-deriving ownership and resource state before terminal disposition.
- `agents/skills/execute-plan/` and `agents/skills/done/` assign cleanup to an authorized owning closeout and preserve resources when its gates refuse. The investigation must verify their active-stage triggers before recommending immediate removal.

## Why not fixed now

The scheduled continuation may have represented a real ownership or closeout boundary. Investigation must separate that evidence-backed boundary from an unexplained wait before deciding whether another sentence in self-heal would help.
