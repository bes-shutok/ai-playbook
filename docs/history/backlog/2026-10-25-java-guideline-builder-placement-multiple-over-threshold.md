# Backlog: rule 27 names no `@Builder` target for a class with two or more over-threshold constructors

Status: open
Priority: low
Class: fix-class (one clarifying clause in a shared guideline; no new gate)
Origin class: review-residual
Driving force: code-quality (docs clarity for guideline consumers)
Cluster: java-rule-27-builder-placement (sibling: the covered 2026-10-20 one-over-threshold row, served by docs/history/plans/2026-10-23-java-guideline-builder-placement-multi-constructor.md)
Cluster: docs/history/backlog/2026-10-15-guidelines-rule-27-verify-line-convention.md (same surface: rule 27 of projects/.ai-playbook/java_guidelines.md)

## Skill and step

`projects/.ai-playbook/java_guidelines.md`, rule 27, the Lombok placement sentences.

## Observed versus expected

Observed: after the 2026-10-25 clarification, rule 27 names the `@Builder` target for a class with exactly one over-threshold constructor beside below-threshold convenience constructors. For a class declaring two or more constructors above the strict more-than-three threshold, the clarified sentence does not fire and the general class arm still reads "on its explicit constructor when the class declares one", singular, so no constructor is named and annotating both would collide on Lombok's generated builder class name.

Expected: one clause that settles the multi-over-threshold arrangement (name the target, or require distinct `builderClassName` values, or redirect the class to a hand-written builder), scoped so the one-over-threshold wording and the record arm stay as landed.

## Evidence

Execution review r1 of the covering plan (`.ai-playbook/reviews/2026-10-25-java-guideline-builder-placement-multi-constructor-code-review-r1.md`, F1, Low, non-blocking, reported by both the contract-docs and correctness-completeness lenses as out-of-scope-adjudicated): the plan's Edge cases exclude this arrangement by design, and no row tracked the residual.
