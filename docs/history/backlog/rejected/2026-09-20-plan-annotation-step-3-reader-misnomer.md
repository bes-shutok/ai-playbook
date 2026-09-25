# Backlog: plan annotation misnames the re-selection mechanism ("Step 3 reader")

Status: rejected (2026-09-26; archived-record fix: a word inside an archived plan's supersession annotation)
- **Class:** DOCUMENTATION_PRECISION
- **Discovered:** 2026-09-20, review round 3 (focused re-cert) of plan docs/plans/2026-09-19-scheduler-ops-contract-fix.md.
- **Finding:** the Task 4 supersession annotation tail says "re-selects next turn per the Step 3 reader"; the reader is the Step 1 reader (SKILL.md:181, :132); Step 3 is the decision/selection step. Substance is right; naming is a collision.
- **Driving force:** the plan file is the durable record future sessions quote; a misnamed mechanism in a supersession annotation invites a future reader to hunt for a nonexistent "Step 3 reader" or to attach the re-selection duty to the wrong step.
- **Fix shape:** word-fix the annotation tail to "the Step 1 reader" (or "next turn's Step 1 reader dispatch") in the archived plan location.
- **Trigger:** next edit touching the archived plan or the SKILL.md Step 1/Step 3 wording.
