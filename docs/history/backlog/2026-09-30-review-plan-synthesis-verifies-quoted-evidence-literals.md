# Review-plan synthesis verifies each finding's quoted evidence literal against the reviewed artifact

- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** efficiency; secondary simplicity
- **Source:** learn Step 1.8 capture, 2026-09-30, from a plan-review panel round where a worker returned a High blocking finding whose entire evidence was a quoted command string; the string did not occur anywhere in the reviewed artifact (the worker had mis-transcribed it from memory), and the finding passed synthesis, calibration, and staging into the round's record before disk truth discarded it. The false staging cost a synthesis correction and polluted the round's staging record with a discarded High row.

## Problem

The review-plan skill's synthesis step (agents/skills/review-plan/SKILL.md, "Step 3: Synthesize Findings") deduplicates, calibrates, and records worker findings, and the skill elsewhere treats quoted evidence as self-contained. It has no check that a finding's quoted evidence literal actually occurs in the reviewed artifact. A finding whose evidence quotes a string the artifact does not contain is either mis-transcribed or fabricated, and today only downstream disk-truth checking catches it, after staging.

## Expected behavior

- One synthesis duty: before staging a finding whose evidence quotes a literal (command, anchor sentence, code span) as evidence about the artifact, the orchestrator greps the artifact for that literal; a quoted literal with zero occurrences demotes the finding to a discard row (reason `excerpt-mismatch` already exists in the staging vocabulary) or returns it to the worker for re-anchoring, never stages as-is.
- Prose-only; the existing discard vocabulary already carries the reason code, so no schema change is needed.

## Possibility space and simplifications

- **Recommended: one synthesis duty sentence in the Step 3 list, prose only.**
- **Rejected: a mechanical quoted-literal checker script.** The literals vary in shape (commands, prose anchors, code); the orchestrator's grep at synthesis time is the cheap sufficient check, and a script would re-implement staging parsing.
- **Rejected: blocking the whole round on one mismatched literal.** The remedy is per-finding (discard or re-anchor), not a panel relaunch.

## Acceptance

- A finding whose quoted evidence literal does not occur in the reviewed artifact is discarded (`excerpt-mismatch`) or re-anchored before staging; the mis-transcribed-evidence defect class is caught at synthesis instead of surfacing as a staged-then-discarded High row.
- Fix-class disposition: the block that disappears is the staged-invalid-finding cleanup; no new refusal path in any runtime flow.
