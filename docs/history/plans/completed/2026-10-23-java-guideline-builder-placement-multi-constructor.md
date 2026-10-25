# Plan: Clarify Java Rule 27 Builder Placement for Multiple Constructors

Backlog origin: `docs/history/backlog/2026-10-20-java-guideline-builder-placement-multi-constructor.md`
Driving force: code-quality
Plan review record: `.ai-playbook/reviews/2026-10-23-plan-review-java-guideline-builder-placement-multi-constructor-r*.md`
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: `docs/tmp/authoring-claims/2026-10-20-java-guideline-builder-placement-multi-constructor.md` (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Selected multi-constructor case:** a class with one explicit constructor over the strict more-than-three threshold and one or more below-threshold convenience constructors.
- **Over-threshold constructor:** an explicit constructor with more than three parameters.

## Why

Rule 27 counts parameters per constructor, but its Lombok sentence does not name which constructor receives `@Builder` in the backlog's case: one full constructor above the threshold beside a below-threshold convenience constructor. Naming that constructor makes this guidance clear without expanding the change to other constructor arrangements.

## Gist & Examples

TLDR: Name the `@Builder` target for the backlog case, improving code-quality by making rule 27 clear for one above-threshold constructor beside a below-threshold convenience constructor.

**Before (today):** A class has one four-parameter constructor and a two-parameter convenience constructor. Rule 27 counts parameters per constructor but leaves unclear which one receives `@Builder`, so a reader may think the builder must also cover the convenience constructor.

**After (this plan):** For this case, the four-parameter constructor alone receives `@Builder`; its builder covers that constructor and its validation remains. The record arm keeps its canonical-constructor wording.

**Edge cases:** A class with more than one above-threshold constructor is outside this backlog item's scope. The class-level no-constructor arm, record wording, and framework exemptions remain unchanged.

## Outcome

For the backlog's one-above-threshold case, rule 27 tells readers which explicit constructor receives Lombok `@Builder`.

- Readers can apply the strict more-than-three-parameters threshold to the constructors in this case.
- The builder target and the constructor whose validation remains are explicit for this case.
- The record arm and existing framework construction exemptions retain their current meaning.

Gate delta: runtime refusal classes: none; hard gates: none; fences: none; protocol layers: none; schema fields: none; task conditions that pause dispatch or later work: none; blocking review-layer duties added: none (the plan adds no review role, gate, or review artifact).

## Assumptions

- Keep the change to the Lombok placement sentence in rule 27 and scope its clarified class case to one above-threshold constructor beside below-threshold convenience constructors; basis: the selected backlog describes exactly that arrangement and the completed plan already covers the surrounding rule. Classes with multiple above-threshold constructors remain outside this plan.
- Preserve the record, no-constructor, and framework-construction wording; basis: the backlog identifies these existing shapes as correct and limits the expected change to the class constructor target.
- Sources inspected: the backlog origin, rule 27 in `projects/.ai-playbook/java_guidelines.md`, Task 1 of `docs/history/plans/completed/2026-10-20-java-construction-and-interface-conventions.md`, and F1 in `.ai-playbook/reviews/2026-10-20-java-construction-and-interface-conventions-code-review-r2.md`; not a tracker-linked request.
Decision points requiring a grill: target cardinality: clarify the backlog's case of one above-threshold constructor beside below-threshold convenience constructors; the origin and prior F1 identify this case, while other arrangements would expand scope; resolved under maintenance-selected authorization on 2026-10-23, affecting Terms, Gist, Outcome, and Task 1; plan boundary: limit the edit to the Lombok placement sentence and leave the completed rule's other behavior untouched; the backlog separates this residual from the completed plan; resolved under maintenance-selected authorization on 2026-10-23, affecting Task 1.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the rule names the explicit constructor that receives `@Builder` in the backlog's one-above-threshold case and says the builder covers it while its validation remains.
- Clarity: readers can identify the `@Builder` target and understand that the below-threshold convenience constructor is not the builder target in the selected case.
- Scope control: the edit clarifies the affected sentence and preserves the record and framework exemptions.

**Done when:**
- The implementation updates only the Lombok placement sentence in rule 27.
- `bash scripts/scan-public-hygiene.sh` and `bash scripts/check-no-em-dash.sh touched` pass.

**Ship when:**
- The repository change is merged and available to guideline consumers; there is no separate deployment or cross-team release in scope.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:** none.

**Tests:** none.

**Documentation:**
- `projects/.ai-playbook/java_guidelines.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Code, tests, new gates, broader rewrites of rule 27, and unrelated guideline rules; the selected backlog item asks for one clarifying clause only.

## Validation Commands

```bash
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh touched
```

### Task 1: Clarify the Lombok builder target in rule 27

Context surface: the plan's Terms, this task, and the stated assumptions.

Files:
- `projects/.ai-playbook/java_guidelines.md`

- [x] Clarify only the class arm for the selected case: given a class with one above-threshold constructor and one or more below-threshold convenience constructors, expect rule 27 to place `@Builder` on the above-threshold constructor, say the builder covers that constructor and its validation remains, and keep the record arm's canonical-constructor wording and existing class-level no-constructor arm. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands and expect both to pass. [class: REPOSITORY_TEST]
- [x] Commit: `docs: clarify Java rule 27 builder placement`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-20-java-guideline-builder-placement-multi-constructor.md`: implemented by this plan (rule 27 names the `@Builder` target for one over-threshold constructor beside below-threshold convenience constructors); the origin row carried `Status: covered` and is deleted in this landing change, this archived plan being the witness. The excluded multi-over-threshold arrangement is tracked by `docs/history/backlog/2026-10-25-java-guideline-builder-placement-multiple-over-threshold.md`.
