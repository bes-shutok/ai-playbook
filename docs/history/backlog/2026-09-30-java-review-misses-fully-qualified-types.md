# Backlog: Java review misses newly added fully qualified type names

- **Filed:** 2026-09-30
- **Status:** done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-java-review-fqcn-coverage.md, squash main 9e699147, exec review r1 ready=yes zero blocking)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Company projects that use the shared Java review skill need this check; do not defer it as skills-repo-only formal hardening.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** maintainability
- **Source:** learn Step 1.8 capture from a consumer Java/Spring review follow-up; low-severity style issue escaped review. Capture hygiene: scan-public-hygiene --files pass.

## Problem

The Java/Spring review checklist does not name the shared JVM import rule among its required review-wide checks. The simplification catalog only checks fully qualified names in method bodies, so it can miss annotations and other declarations. A newly added Spring configuration annotation used its fully qualified name even though a normal import was available. A branch-wide diff scan found similar new fully qualified type references in production and test sources.

## Expected behavior

For every Java/Spring review, explicitly apply jvm_guidelines.md #12 to the complete branch diff. Check added annotations, constructor calls, and type references in production and test sources; report fully qualified names when a normal import is possible, allowing only intentional clashes or metadata cases.

## Exact location

- agents/skills/doing-code-review/java-spring.md, Review-wide Java checks.
- agents/skills/review-agents/simplification.md, simplification#shrink-fqcn-import pattern.

## Suggested fix

Add jvm_guidelines.md #12 to the Java/Spring review-wide checks and broaden the simplification pattern so added fully qualified annotations and declaration-level type references are covered, not only method-body references. Keep the existing intentional-use exceptions.

## Severity and source reference

Low; consumer review follow-up. The code compiles, but the review missed an existing style rule and multiple similar candidates.

## Why not fixed now

This run was requested to analyze and capture the lesson. Editing the shared review skill is a separate implementation task.

## Suspected root area

The Java review overlay's required-check list and the simplification catalog's narrow trigger. The rule itself already exists in shared JVM guidance.

## Environment

Codex skill workflow; consumer company repository; 2026-09-30.

## Dedup probe

Searched open backlog filenames and problem text for fully qualified, FQCN, import hygiene, jvm_guidelines.md #12, and FQN annotation. No open item matched this Java review coverage gap.

## Acceptance

Java/Spring review prompts require the shared import rule and the check catches newly added fully qualified annotations and type references in both production and test code when a simple import is available.
