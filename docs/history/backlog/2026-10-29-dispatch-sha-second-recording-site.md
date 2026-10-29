# Backlog: the successor-dispatch recording clause is a second dispatch_plan_sha producer the echo-verify duty does not reach

- **Filed:** 2026-10-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** the covered EXEC entry `dispatch-plan-sha-recording-unverified` (landed 35595ad5, removal receipt at the top of docs/history/backlog/EXEC-PROMPTS.md; the covering landing adds the echo-verify recording duty and the consumer-side git-history adjudication; this row is the panel's second-producer residual that the entry's bounded two-arm scope deliberately left out)
- **Skill/step:** `agents/skills/maintenance/template-execution.md` (the successor-dispatch duty's self-contained recording clause, "the successor plan file's sha256 recorded at dispatch time"); `agents/skills/maintenance/scheduling.md` (the Step 6 dispatch-recording bullet that now carries the echo-verify duty)
- **Class:** fix-class
- **Origin class:** review finding (focused docs panel, correctness worker, pattern `quality#unamended-second-recording-site`, 2026-10-29)

## Finding

The landed echo-verify duty binds the scheduler's dispatch-recording bullet: the recorded `dispatch_plan_sha` must be the verbatim same-turn output of hashing the exact recorded plan path, quoted in `decision_reason`. The execution blueprint's successor-dispatch duty self-restates the recording convention ("the successor plan file's sha256 recorded at dispatch time") without referencing the Step 5/6 recording conventions, so a successor-chained dispatch can still record an unverified sha baseline. The consumer side is protected for any producer (the failure-cap conjunct's git-history adjudication names the defect), but prevention is absent at this second site.

## Expected

Either the successor-dispatch clause carries the same echo-verify sentence, or it restates itself as a pointer to the Step 5/6 recording conventions (the shape decisions.md's chaining clause already uses: "per the Step 5 conventions"), so the prevention duty textually reaches every producer of the field.

## Suggested direction

One clause at the template-execution.md successor-dispatch recording site: add the echo-verify sentence or replace the restated convention with the by-reference pointer; keep the diff bounded to that clause and run the maintenance pins suite beside the standard text gates.

## Evidence

- The panel finding over branch 2026-10-29-dispatch-sha-duties-exec head 50d0324af (the covering landing), quoting `agents/skills/maintenance/template-execution.md`'s successor-dispatch recording clause beside the landed `agents/skills/maintenance/scheduling.md` duty.
- The witnessed phantom baseline (the 2026-10-29 `(idle)` dispatch entry in `.ai-playbook/scheduler-state.json`, whose recorded sha matches no historical state of the plan file) shows the defect class the echo-verify duty prevents.
