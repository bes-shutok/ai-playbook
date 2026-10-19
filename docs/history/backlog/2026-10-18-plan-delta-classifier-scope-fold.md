# Backlog: Classify plan-scope corrections inside the authored-plan boundary

- **Filed:** 2026-10-18
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** authoring-tooling
- **Driving force:** efficiency
- **Source:** unclassified plan delta while resolving r5-r7 findings in `docs/history/plans/2026-10-18-done-live-owner-closeout-recovery.md`

## Problem

The plan delta classifier reports plan-scope correction prose and safety-acceptance edits as unclassified when changed spans include inline code or links. The current authoring guidance routes these hunks to a recorded operator acknowledgement and durable classifier-gap backlog row. This item records the observed gap; it does not authorize changing the classifier or relaxing that gate in the current plan.

## Evidence

The classifier ran on plan bytes from `163cd7c3a488c4d86774d0abf4fa59cb27198ce1` (before digest `01ed40b1432aed69bb5c894036bb47eee0587e9d833f36923c2ca1356449e102`) to the current plan (after digest `bf7f9777d70557a0109404567be94be364432fe5051d979a41ee3e4a638ff758`). Its six refused hunk digests were:

- `3757c026c3c279001305b09a32cf1cba5b5f91c8934ed3b82f18dc3560a82e24`
- `4a7a08c2d8926342111b87cf353ca910680e59ea0dd2e9ce85bf49de3213b04d`
- `b0af7821b27532568e0cfe9084dc64d46873725a379c1e09eaddd83d2e7052ea`
- `84ab0dccc0df35cfec55399f74e7675229d194283b0ef54cfddf494d7c99efc8`
- `dcb7498d71eff050ccefc520058bfffcd5ad8bb5a9476894560c7e4fc22c0254`
- `e685ca78872a6d6b9aa01b91c90d5ea7aedb19d70128f19f384dc15a2946aff4`

Follow-up work should determine whether an authored-plan correction category can be added without weakening the independent review requirement for semantic changes.
