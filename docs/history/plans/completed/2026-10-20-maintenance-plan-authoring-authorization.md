# Plan: Maintenance Plan Authoring Honors Standing Authorization

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-20-maintenance-plan-authoring-authorization-conflict.md`
- `docs/history/backlog/2026-10-08-plan-simplicity-challenge.md`
Driving force: efficiency
Plan review record: `.ai-playbook/reviews/2026-10-20-plan-review-maintenance-plan-authoring-authorization-r*.md`
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-20-maintenance-plan-authoring-authorization-conflict.md (session 01a15484-176a-70a1-814d-785fd68e1975)

## Terms

- **Maintenance-selected authoring:** Plan creation chosen by a maintenance turn under its active standing directive.
- **Standing authorization:** The operator's existing direction for maintenance to select work, make supported choices, and continue without confirmation questions.

## Why

Maintenance currently authorizes plan selection and asks the author to decide, while the plans skill still pauses for general confirmation. The mismatch interrupts authorized work and lets routine design choices avoid the simpler-alternative check.

## Gist & Examples

TLDR: Carry maintenance's standing authorization into plan authoring and apply the simpler-design check across authoring modes, improving efficiency while preserving direct interactive confirmation for material choices.

Before: A maintenance prompt fully specifies scope and alternatives, but Phase 1 asks the operator to confirm them. An author may also settle on a derived design without checking a simpler existing setting.

After: Authors in every mode compare simpler viable choices and record the evidence. Maintenance-selected authors use standing authorization to proceed on resolved in-scope choices without confirmation; direct interactive requests retain confirmation and ask about genuinely unresolved material decisions.

Edge cases: A fully specified maintenance prompt and source evidence for an in-scope choice proceed without a question. An unrequested extension stays out of the selected plan and creates no new backlog row. If the remaining selected scope is implementable, maintenance authors it; after it lands, the next normal maintenance turn's D2 selects the next eligible item. A genuinely unresolved direct request keeps its interview. Rejection remains an explicit user decision on the direct interactive path. The no-confirmation path applies to the active maintenance authoring-child invocation's selected item and scope, which the existing payload passes from the current D2 selection; no additional context-validation gate is introduced. A plans invocation outside that payload uses ordinary Phase 1 confirmation.

## Outcome

The shared plan-authoring contract applies its simpler-design check in every mode and consumes maintenance authorization while preserving direct interactive requirements discovery.

- Maintenance can complete an eligible plan prompt without a confirmation pause.
- Evidence-backed design choices and simpler alternatives are recorded in the plan for maintenance-selected and direct interactive authoring.
- Direct interactive authors still resolve material ambiguity with the user.
- Maintenance authors record the evidence for the best-supported in-scope choice; unrequested extensions stay out of scope.

Gate delta: remove Phase 1's mandatory confirmation pause for source-complete authoring under existing maintenance standing authorization (witness: `docs/history/backlog/2026-10-20-maintenance-plan-authoring-authorization-conflict.md` records the repeated false pause on 2026-10-20). In maintenance mode, replace the scope-extension hard gate's mandatory user question with an out-of-scope disposition: omit unrequested extensions and create no extra backlog row. Author the selected item within its existing scope; after landing, the next normal D2 turn selects the next eligible item, consistent with the origin's next-item continuation and the existing one-authoring-child-per-turn limit. Direct interactive authoring keeps the existing user decision for material choices and scope extensions. This change adds no gate, approval flag, validator, lock, ledger, or ceremony.

## Assumptions

- Assume the selected maintenance prompt and active directive define the requested plan scope; basis: the maintenance loop's standing authorization and the prompt's explicit origins, scope arms, and rejected alternatives.
- Assume maintenance may select and record the best-supported in-scope choice without an interactive confirmation; basis: the two backlog origins and the active maintenance directive.
- Assume the direct interactive confidence and scope-extension paths remain in force; basis: the existing plans Phase 1 rules and the first origin's explicit preservation boundary.
- Assume the later design-simplicity review remains independent; basis: the origin asks to retain that review unless implementation shows duplication, while this plan adds no review duty.

Decision points requiring a grill: none remain.

## Standing constraints

- Make the smallest changes within the existing plans Phase 1 and maintenance authoring payload.
- Keep unsupported scope extensions out of maintenance-authored plans; do not add a no-plan deferral or closeout lifecycle.

## Evaluation Criteria

- **Authorization:** A maintenance-selected plan with complete source requirements proceeds without a confirmation question.
- **Evidence:** A source-resolvable design choice is compared with a simpler viable option and the selected option is recorded with its evidence.
- **All-mode simplicity:** Given a direct interactive request with a low-impact, source-supported simpler viable option, expects the author to compare and record it in the requirements and assumption confirmation without adding an unnecessary question.
- **Interactive behavior:** A direct request with a genuinely unresolved material choice still asks the user.
- **Scope:** An unrequested extension remains outside the maintenance-authored plan and creates no separate backlog row; once the selected plan lands, the next normal D2 turn selects the next eligible item.
- **Extension disposition:** An unrequested extension is excluded from the selected plan and creates no separate backlog row. After the selected plan lands, the next normal D2 turn advances to the next eligible item; direct interactive authoring retains the current user decision path, including explicit rejection.
- **Authority boundary:** The maintenance authoring payload passes the current D2-selected backlog item and its scope; the no-confirmation path applies only to that invocation and keeps unrelated extensions out of scope. This documents the existing authorization boundary without adding a context-validation gate.
- **Outside maintenance authoring:** A plans invocation without the maintenance authoring payload keeps the ordinary Phase 1 confirmation path.

**Quality dimensions:**
- Efficiency: maintenance does not stop for choices its prompt and repository evidence resolve.
- Scope control: direct interactive discovery and the scope-extension boundary remain intact; maintenance resumes ordinary D2 selection after the selected plan lands.

**Done when:** Both skill texts describe the same bounded maintenance authorization contract, the simpler-design check applies across authoring modes, and all acceptance cases above have an observable expected behavior.

**Ship when:** The plan is implemented, reviewed, and landed.

## Review Scope

**Must-fix paths:**
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `docs/history/backlog/`

**Plan-related extension:** Other findings are in scope only when they are caused by these contract edits or required to keep the two skills consistent.

**Out of scope:** No-plan deferral or closeout behavior; new approval state, gates, validators, or reviewer duties; direct interactive behavior changes beyond applying the simpler-design check and preserving current confirmation for material choices.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-20-maintenance-plan-authoring-authorization.md
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh touched
```

Also validate both skill edits with realistic sample contexts: use the selected maintenance backlog prompt and its cited source records to proceed on a source-resolvable in-scope alternative, recording its evidence; propose an unrequested extension and expect it excluded without a new backlog row, complete the implementable selected scope, and verify the next normal D2 turn selects the next eligible item after landing; verify that the maintenance payload passes its current D2-selected item and scope and that plans authoring is limited to them; use a direct interactive request with a low-impact simpler alternative and expect comparison plus the normal assumption confirmation, then use an unresolved material choice or extension and expect the user question.

## Tasks

### Task 1: Define the maintenance authorization path in Phase 1

Files:
- `agents/skills/plans/SKILL.md`

- [x] Given a fully specified prompt, selected-item context, and repository evidence supporting a simpler viable design within the authorized scope, expects Phase 1 to record the comparison and evidence-backed choice, then proceed without confirmation. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a direct interactive request with a low-impact, source-supported simpler viable option, expects Phase 1 to record the comparison and basis in the requirements and present it in the normal assumption confirmation without adding an unnecessary question. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an unrequested extension, expects the child to exclude it from the selected plan and report `omit-extension`; when the selected item's remaining scope is implementable, the payload proceeds with that scope and the next normal D2 turn selects the next eligible item after landing. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the active maintenance authoring payload's selected item and scope, expects the no-confirmation path to apply only to that item and scope; a plans invocation without that payload uses ordinary confirmation. Given a direct interactive unresolved operator-owned decision, expects the existing question and grilling path to remain. [class: IMPLEMENTATION_REQUIRED]
- [x] The later design-simplicity review remains unchanged and independent; the update adds no approval mechanism or review duty. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `plans: honor maintenance authorization during plan authoring`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pass authorization context from the maintenance authoring payload

Files:
- `agents/skills/maintenance/template-authoring.md`
- `docs/history/backlog/`

- [x] Given a live maintenance selection and prompt, expects the payload to pass explicit standing authorization and selected-item context to plans authoring; choices within scope proceed with the evidence recorded. [class: IMPLEMENTATION_REQUIRED]
- [x] Given `omit-extension`, expects the payload to keep the extension outside the selected plan and create no separate backlog row; when the selected goal remains implementable, it proceeds, then normal D2 selects the next eligible item after landing. Omission leaves unrequested scope outside the selected plan. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a plans invocation without the maintenance authoring payload, expects the plans skill's existing confirmation path; given an unresolved direct interactive choice or extension, expects the existing user-question path to remain intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: pass standing authorization to plans authoring`. [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

- implementation#incomplete-state-transition: folded. The unsupported no-plan lifecycle is outside this plan's scope.
