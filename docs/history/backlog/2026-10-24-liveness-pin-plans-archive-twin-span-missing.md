# Backlog: authoring-plans liveness pin names a done/SKILL.md span a later landing removed

- **Filed:** 2026-10-24, exec carrier automation-eda2e2ee (Task 2 intermediate review of plan ignored-audit-home-tracked-index-fence, off-plan capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** self-serving
- **Class:** fix-class (a red suite on main with no owner; the pin and its living surface disagree and neither names the sanctioned repair)
- **Driving force:** correctness
- **Skill/step:** `scripts/test_authoring_plans_liveness.py` (`test_preserved_anchors_stay_pinned`, the `plans-archive-twin` span) against `agents/skills/done/SKILL.md`
- **Cluster:** docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md (same suite, cosmetic polish items)

## Problem

`PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_authoring_plans_liveness.py -q` fails on main at `15b114519` with `missing span in done/SKILL.md: plans-archive-twin`. The span left done/SKILL.md in landing `0eb7d617b` (the done dirt-regression valid-correction path), whose own gates did not run this suite, so the liveness declaration now pins a referent its living surface no longer carries. Two independent review workers reproduced the red on an untouched done/SKILL.md.

## Outcome sought

Either restore the referent clause in done/SKILL.md (when the landing dropped it by accident) or retarget the pin at the clause that replaced it (when the drop was deliberate), with the decision recorded in the commit; the suite is green on main afterwards.

## Rejected alternatives

- Delete the pin: rejected until the drop is classified, because the pin exists to catch exactly this class of silent referent loss (`scripts/test_authoring_plans_liveness.py`).
- Fix it inside an unrelated plan's execution run: rejected, done/SKILL.md sits outside every task's Files list there and the landing would widen past its plan (`docs/history/plans/2026-10-23-ignored-audit-home-tracked-index-fence.md`).
