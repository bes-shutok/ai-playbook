# Backlog: plans skill needs a replacement-span boundary rule (name the tail, guarantee its survival)

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-18
Class: plan-authoring rule gap (review-plan staged the same defect class in three consecutive rounds)

Origin: P12 authoring loop (docs/plans/2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording.md, rounds r3-r5). Three staged findings, one pattern (`consistency#replacement-boundary-ambiguity`): r3 F1 (a quoted anchor was a prefix of a longer sentence, so the replacement boundary was ambiguous), r4 F1 (the prescribed replacement text duplicated the continuation clause the prescription told the executor to keep), r5 F1 (the quoted replaced span ends mid-sentence, leaving the tail ` and re-arm per the runtime overlay's recipe only when they classify darkness.` outside both the replaced span and the verbatim guarantee, so a harmful literal reading silently drops the trigger's re-arm action clause).

## Problem

When a plan task prescribes replacing a quoted span inside a live sentence, nothing in the plans skill's authoring rules forces the prescription to bound the span at a sentence terminator or to name the exact tail bytes that must survive the replacement. Reviewers caught the resulting ambiguity three rounds running, each time on a different boundary defect (prefix-vs-full-sentence, replacement-duplicates-continuation, mid-sentence boundary), and no validation gate distinguishes the readings.

## Required behavior

A plans-skill authoring rule (and, if mechanically enforceable, a validation-block pattern): a task that prescribes replacing a quoted span must either (a) quote the span ending at a sentence terminator, or (b) name the exact tail text that follows the span and assert verbatim that the tail survives the replacement; a prescription whose replacement text overlaps the quoted span's continuation clauses is invalid. The r5 F1 instance on the P12 plan (Task 2's Step 0 opening) is the standing witness; fix it when the plan is next touched, folding the tail clause into the verbatim guarantee.

## Evidence

docs/reviews/2026-09-18-plan-review-maintenance-loop-residuals-occupancy-anchors-rearm-wording-r{3,4,5}.md, findings F1 in each; the P12 plan's Task 2 first checkbox carries the r5 boundary as written.
