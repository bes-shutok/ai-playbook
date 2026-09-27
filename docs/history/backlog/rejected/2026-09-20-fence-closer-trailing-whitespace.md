# Backlog: fence closer with trailing whitespace does not close

- Status: rejected (2026-09-27; contract-matching nuance fix; unwitnessed hypothetical-author-input hardening on a fail-closed check)
Priority: medium
Urgency remark: plausible false refusal: CommonMark trailing-whitespace tolerance on the live plan fence map
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)
- **Origin:** execute-plan task 8 intermediate review (Step 1.2b, correctness-completeness lens, 2026-09-20)

## Finding

`_plan_fence_map` (scripts/execute_plan_runtime.py:806) requires the closing-fence line body to be exactly the character run; a closer carrying trailing spaces or tabs (`"```   "`) leaves the fence open. CommonMark reference implementations permit trailing whitespace after the closing run. Failure direction is fail-closed (a false "section is missing" refusal, never a silent prose scan), and the contract text as written matches the implementation, so this is a nuance fix, not a defect.

## Driving force

A plan author whose example-fence closer carries trailing whitespace gets a misleading fail-closed refusal that names the wrong cause; matching CommonMark's trailing-whitespace tolerance removes a class of false refusals from the readiness gate.

## Suggested fix

Strip trailing spaces/tabs before the bare-closer check in `_plan_fence_map`, with a witness for the trailing-space closer and one for trailing whitespace on a lookalike that must not close.
