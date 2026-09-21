# Backlog: authoring dispatch slice documents whole-body payload, practice transmits the payload paragraph only

- **Status:** open
- **Priority:** high
- **Date:** 2026-09-22
- **Origin:** learn Step 1.8 capture from the automation-ae88c54e authoring run of docs/plans/2026-09-22-execution-integrity-worker-evidence.md (r4 ready=yes); skills-corpus workflow gap

## Skill and step

`agents/skills/maintenance/SKILL.md`, "Step 5: scheduling", authoring slice sentence: "for an authoring child the scheduled prompt is the authoring blueprint's fenced body with `{REPO_ROOT}` (in the re-arm duty paragraph), `{schedule_time}`, and `{backlog_item}` filled".

## Observed versus expected

Observed: the documented slice says the whole fenced body (role line, FIRST ACTION re-arm duty, AUTHORING CLAIM duty, fire-time gates, payload sentence and tail, CONTEXT CHECKPOINTS, FINAL STEP compaction) is what the scheduled authoring session receives. In observed practice the scheduled prompt carried only the "Schedule at {schedule_time} the following task:" paragraph and its tail: two independent witnesses received no re-arm duty, no AUTHORING CLAIM duty, no compaction step. Witness 1: the origin of docs/history/backlog/2026-09-22-authoring-payload-omits-claim-duty.md (the automation-197f75a7 session never learned the claim duty). Witness 2: the automation-ae88c54e session (this item's capture run) received a payload of pre-authorization, session constraints, review/landing steps, and dispatcher-added guards only; it wrote its claim file only because the dispatcher's added guard line told it to.

Expected: the Step 5 authoring slice and the actual payload assembly agree, one way or the other. Either the slice is corrected to describe the payload-paragraph assembly that practice performs (with the body's child duties moved into the transmitted region or explicitly owned elsewhere), or the dispatcher assembly is fixed to transmit the whole documented body. Until reconciled, every body-side duty (re-arm, claim lifecycle, compaction) is advisory prose the child never sees, and fixes that add duties to the blueprint body (as several ledger entries did) silently do not reach payload-born sessions.

Related: docs/history/backlog/2026-09-22-authoring-payload-omits-claim-duty.md owns the payload-omission symptom (fixed by adding the claim duty to the payload paragraph in docs/plans/2026-09-22-execution-integrity-worker-evidence.md Task 3); this item owns the root contradiction between the slice text and the assembly practice. The 2026-09-21 durability-review-residuals item owns claim-protocol internal races; neither owns this.

## Suggested fix

Reconcile in one pass: verify what the deciding turn's assembly code/recipe actually extracts from the blueprint; align the Step 5 authoring slice wording with that reality; and for every child duty that must reach the session (re-arm, claim lifecycle, compaction, context checkpoints), either move it into the transmitted region or give its ownership to the dispatcher explicitly, with the pins suite updated so the slice text and the transmitted region cannot drift apart again.

## Environment

ZCode runtime, 2026-09-22, skills repo copy (agents/skills/maintenance/); witnesses are this repository's own scheduled runs.
