# Backlog: plan-quality-gate growth folds skip the full create-boundary gate until round-close

- **Filed:** 2026-11-15 (learn Step 1.8 skills-corpus capture, authoring lane closeout)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** skills-corpus defect (review-loop fold contract)
- **Class:** fix-class (skill-text duty addition; warning-first, no new machinery)
- **Skill/step:** agents/skills/plans/plan-quality-gate.md rule 2 (fold classification and re-review default) beside rule 6 (round-close full-gate precondition)

Cluster: docs/maintenance/development_lessons.md #457 (the corpus witness)

## Problem

A review fold that lengthens a plan criterion can breach the per-item mechanical limit the create boundary enforces (the readiness validator's UTF-8 byte cap per acceptance criterion), and no gate in the fold's own pass measures it: the delta confirm rounds run the staging validator and the name probe only, so the breach stays invisible until the round-close full gate refuses, forcing a criterion split, a fresh fold, and one more confirm round. Witnessed 2026-11-15 (one authoring lane, r6 round-close): a criterion grown to 667 bytes against the 512-byte cap across two earlier folds was caught only by the round-close full gate; the repair cost one split fold plus a full confirm round (r6).

The same lane witnessed the sibling gap three times in one loop: a fold extending a counted set corrected only the surfaces the finding named, leaving the same stale count on a sibling surface; each of three consecutive rounds staged one fold_defect for it until a fold ran an exhaustive count-bearing-surface sweep and the next confirm came back zero-finding.

## Observed versus expected

- Observed: fold passes verify the finding's named surfaces only; mechanical limits outside the focused rounds' gate set (per-criterion byte cap; sibling count surfaces) surface at round-close or in the next round's findings.
- Expected: a fold that extends a counted set re-sweeps every count-bearing surface of the artifact in the same pass (operative versus append-only history classified), and a fold that lengthens any criterion line re-runs the readiness validator's full mode (or a bounded byte-cap sweep over all criteria as its cheap proxy) before the confirm round is staged.

## Proposed fix direction

Pin both duties in rule 2's fold text (or the round-close arm they already sit beside), keeping the delta-classifier routing unchanged: the duties are fold-pass hygiene, not a new gate, and the delta classifier's fresh-round default already carries the confirm round that would verify them. The sweep text is two sentences; the gate re-run cites the existing round-close precondition as its procedure of record.

## Evidence

- Round-close full-gate refusal naming the over-cap criterion (667 UTF-8 bytes, limit 512), followed by the split fold and the r6 confirm round over the repaired digest.
- Three consecutive staging records each carrying one fold_defect of the count-propagation class, then a zero-finding confirm after the exhaustive sweep.
