# Java/Spring review applies the shared import rule to the whole diff, and the simplification catalog covers declaration-level FQNs

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-30-java-review-misses-fully-qualified-types.md

Plan review: docs/reviews/2026-09-30-plan-review-java-review-fqcn-coverage-r1.md (r1 verdict ready=yes, zero blocking) (the highest round of the staging series is the authoritative record)

## Gist TLDR

The shared import rule already exists (`jvm_guidelines.md` #12: prefer a normal import over fully qualified type names in annotations, constructor calls, and type references), but the Java/Spring review overlay's Review-wide Java checks list never names it, and the simplification catalog's `simplification#shrink-fqcn-import` trigger only mentions method bodies. A consumer Spring review therefore let a newly added fully qualified annotation through, and a branch-wide scan found more of the same shape. Fix: add rule #12 to the overlay's review-wide checks (complete-branch-diff scope, production and test sources, the guideline's own intentional-clash and metadata exceptions), and widen the catalog bullet from method bodies to also cover added annotations and declaration-level type references in the PR diff. No new rule is invented; both edits point at existing guidance.

## Outcome + Gate delta

Witnessed 2026-09-30 (consumer Java/Spring review follow-up, learn Step 1.8 capture): a newly added Spring configuration annotation used its fully qualified name where a normal import was possible; the review reported nothing; a branch-wide diff scan found similar new fully qualified type references in production and test sources. The code compiles, so unused-import tooling cannot catch it; the miss is a coverage gap in the review checklist and the catalog trigger, not a missing rule.

After this plan:

- The Java/Spring overlay's Review-wide Java checks list gains the `jvm_guidelines.md` #12 entry with the same shape as its siblings: what to check (added annotations, constructor calls, and type references), where (the complete branch diff, production and test sources), and the only allowed exceptions (the guideline's own intentional simple-name-clash and package/module-metadata cases). The list's closing count sentence ("These two `jvm_guidelines.md` rules are applied on every Java review") updates to three, so the list cannot drift against itself.
- The simplification catalog's `simplification#shrink-fqcn-import` bullet stops scoping the pattern to method bodies: added annotations and declaration-level type references in PR-touched files are in scope, with the bullet's existing default severity, its guard against inventing language-specific import rules beyond the overlay and local file style, and the guideline's pre-existing-style carve-out unchanged.

Out of scope: `jvm_guidelines.md` itself (the rule text is correct as written), the review-wide assignment paragraph's owner mapping (an FQN finding already lands on simplification via the catalog), every other review overlay (`general.md`, `python.md`, `kotlin-spring.md` picks the rule up through its own JVM guidance when a consumer needs it), and any change to finding severities.

## Terms

- **Review-wide Java checks**: the overlay section in `agents/skills/doing-code-review/java-spring.md` listing the guidelines workers must apply to the complete branch diff on every Java/Spring review.
- **FQN finding**: a reported use of a fully qualified type name where a simple-name import is possible, owned by simplification under the slug `simplification#shrink-fqcn-import`.
- **Declaration-level type reference**: a fully qualified name used on a declaration or annotation site (annotation usage, extends/implements clauses, field types, constructor `new` expressions) rather than inside a method body.

## Assumptions

- Two edits, no third home: the overlay is where per-review required checks live, and the catalog is where the finding's slug, trigger, and default severity live; both must change or reviewers still miss the check and stagings still misclassify it. The guideline pack (`projects/.ai-playbook/jvm_guidelines.md`) is referenced read-only and stays untouched.
- The overlay bullet cites the guideline number rather than restating the rule, matching how every sibling entry is written; the exceptions are named by their intent (intentional simple-name clash, package/module metadata) so a worker needs the guideline pack it is already required to include.
- Kotlin: `kotlin-spring.md` does not get a parallel edit. The catalog bullet is language-neutral after this plan, and the JVM guideline already covers Kotlin imports; widening a Kotlin overlay's required checks is a consumer demand that has not been witnessed.

Decision points requiring a grill: none - the origin item names both exact locations and prescribes both edits; the count-sentence update is a mechanical consequence of the list edit.

### Task 1 - Overlay: the review-wide checks list applies jvm_guidelines.md #12

- [ ] In `agents/skills/doing-code-review/java-spring.md`, the Review-wide Java checks section: add one bullet to the `jvm_guidelines.md` group, in the sibling style: `jvm_guidelines.md` #12, fully qualified type names replaced by a normal import in added annotations, constructor calls, and type references across the complete branch diff in production and test sources, with only the guideline's intentional exceptions (simple-name clashes, package/module metadata) kept. Update the section's closing sentence that counts the always-applied `jvm_guidelines.md` rules from two to three. Do not touch any other bullet or the assignment paragraph. [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Catalog: the shrink-fqcn-import trigger covers declarations, not only method bodies

- [ ] In `agents/skills/review-agents/simplification.md`, the `simplification#shrink-fqcn-import` bullet in the catalog: widen the trigger from "Fully-qualified type names in method bodies" to fully qualified type names in the PR diff's added annotations, constructor calls, and declaration-level type references (method bodies included), keeping the existing when-a-normal-import-matches-local-style condition, the default **Low** severity, and the guard against inventing language-specific import rules. State the pre-existing-style carve-out (do not rewrite FQN style outside the PR diff for uniformity) in the same bullet. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [ ] All checks in Validation Commands pass from the worktree root, including the review-agents portability and doors suites that this corpus change requires. [class: REPOSITORY_TEST]

## Evaluation Criteria

- The Review-wide Java checks list contains the `jvm_guidelines.md` #12 entry scoped to the complete branch diff with the intentional-exception carve-out, and the section's count sentence names three always-applied `jvm_guidelines.md` rules.
- The catalog's `simplification#shrink-fqcn-import` bullet covers added annotations and declaration-level type references alongside method bodies, keeps the local-style condition, the Low default, the no-invented-rules guard, and the pre-existing-style carve-out.
- No other overlay bullet, catalog entry, or guideline file changes.

## Review Scope

Files: `agents/skills/doing-code-review/java-spring.md` (the Review-wide Java checks list and its count sentence only), `agents/skills/review-agents/simplification.md` (the `simplification#shrink-fqcn-import` bullet only). Contract files referenced read-only: `projects/.ai-playbook/jvm_guidelines.md` (rule #12), the origin backlog item, `agents/skills/doing-code-review/kotlin-spring.md` (read-only, the declared non-goal).

## Validation Commands

Run from the worktree root:

1. `grep -n "jvm_guidelines.md. #12" agents/skills/doing-code-review/java-spring.md` - the overlay bullet exists in the review-wide list.
2. `grep -n "three" agents/skills/doing-code-review/java-spring.md | grep -i "jvm_guidelines"` - the count sentence says three.
3. `grep -n "shrink-fqcn-import" agents/skills/review-agents/simplification.md` - the slug survives; the bullet's line no longer begins the trigger with "in method bodies" scoping alone (`grep -c "Fully-qualified type names in method bodies" agents/skills/review-agents/simplification.md` prints 0).
4. `git diff --stat main -- agents/skills/doing-code-review/java-spring.md agents/skills/review-agents/simplification.md projects/.ai-playbook/jvm_guidelines.md` - only the two skill files changed; the guideline pack is untouched.
5. `python3 scripts/check_review_agent_portability.py && python3 scripts/test_review_agent_doors.py` - both exit 0 (the repository rule for every `review-agents/` change).
6. `bash scripts/scan-public-hygiene.sh && bash scripts/check-no-em-dash.sh touched` - both exit 0.
