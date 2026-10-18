# Backlog: surface the staging-record closed vocabularies in the review-loop dispatch recipe

- **Filed:** 2026-10-10, learn Step 1.8 capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** repeated staging-validator refusals across one authoring session
- **Class:** fix-class
- **Skill/step:** `agents/skills/review-loop/SKILL.md` worker-dispatch recipe; `agents/skills/review-staging/SKILL.md` record-shape section; `scripts/validate_review_staging.py` enum owners
Cluster: docs/history/backlog/2026-10-10-review-loop-budget-exec-residuals.md (same surface: the review-loop skill's dispatch and staging contracts)

## Observed vs expected

Observed: across the review rounds of both authoring cycles in one session (2026-10-10), staged records were refused by the staging validator for vocabulary the worker prompts and sidecar-composition instructions never stated: pattern owners outside the lens-level set (`concurrency` and `premortem` proposed where only `architecture#`, `consistency#`, `documentation#`, `implementation#`, `quality#`, `security#`, `simplification#`, `testing#`, `unknown` parse), a findings section missing the four severity group headings when the section was empty, and reachability values outside the four-value enum. Each refusal was fixed forward by reading the validator error; the accepted values live only inside `validate_review_staging.py`.

Expected: the dispatch recipe carries the closed sets (or instructs extracting them from the validator before dispatch) so records compose valid on first write, and refusals stay reserved for genuine defects. The user-level corpus already holds the dispatcher-side behavior (paste the validator's closed sets into the worker prompt before dispatch); neither owning skill has adopted it, so nothing in the loaded skill surface reminds the dispatcher.

## Suggested direction

Add a closed-vocabulary step to the review-loop dispatch recipe: before dispatch, extract the pattern-owner, reachability, and triage sets plus the four-severity-group shape from `validate_review_staging.py` and paste them into every worker prompt and the sidecar-composition instructions; mirror the severity-group requirement in review-staging's record-shape section.

## Evidence

- 2026-10-10 authoring session: pattern-owner remaps in r1 sidecars of two plans (`concurrency`/`premortem` refused, remapped to `consistency#`/`architecture#`/`implementation#`), and an r4 record restructured to add empty Critical/High/Medium/Low headings before validation passed.
- Cost: at least one full fix-and-revalidate pass per cycle, recurring across consecutive cycles in the same session.
