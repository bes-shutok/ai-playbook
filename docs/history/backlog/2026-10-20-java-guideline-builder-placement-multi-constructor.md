# Backlog: rule 27's Lombok placement sentence does not say which constructor carries `@Builder` on a multi-constructor class

Status: open
Priority: high
Class: fix-class (ambiguous instruction in a shared guideline; the fix is one clarifying clause, no new gate)
Origin class: self-serving
Consumer urgency: consumer projects that apply `java_guidelines.md` rule 27 by number read this sentence; the skills-repo personal priority profile must not park or defer it as formal-hardening for the skills repo alone.
Driving force: docs

## Skill and step

`projects/.ai-playbook/java_guidelines.md`, rule 27, the Lombok placement sentence ("put `@Builder` on the record, or on the class (on its explicit constructor when the class declares one), so the builder covers the canonical constructor").

## Observed versus expected

Observed: the sentence is correct for a record, for a class without an explicit constructor, and for a class with exactly one explicit constructor. Rule 27 itself says the threshold is judged per constructor, yet for a class that declares several explicit constructors (a sub-threshold convenience constructor beside an above-threshold full constructor) the sentence says "its explicit constructor", singular, without naming which one carries the annotation, and "the canonical constructor" is record vocabulary with no definition for classes.

Expected: one clause that names the constructor: the explicit constructor that exceeds the threshold carries `@Builder`, the builder covers that constructor, and its validation is kept; the record arm keeps the canonical-constructor wording.

## Evidence

Execution review round 2 of `docs/history/plans/2026-10-20-java-construction-and-interface-conventions.md` (record `.ai-playbook/reviews/2026-10-20-java-construction-and-interface-conventions-code-review-r2.md`, finding F1, risk lens, Low, non-blocking): two misreads are possible on a multi-constructor class, a false block (the builder does not "cover" the sub-threshold constructor) or advice to annotate both constructors with plain `@Builder`, which collides on the generated builder class name. The sentence under review is the round-1 fix wording, not the plan's mandated text, so the plan needs no amendment.

## Suggested fix

Replace the parenthetical with "(on the class itself when it declares no constructor, on the explicit constructor that exceeds the threshold when the class declares one)" and end the sentence "so the builder covers that constructor, and its validation is kept", keeping the record arm as is. The plan's Validation Commands probe only the `## 27.` heading, so the rewording cannot break a probe; re-run `bash scripts/scan-public-hygiene.sh` and `bash scripts/check-no-em-dash.sh touched` after the edit.

## Why not fixed now

The finding surfaced in the execution's round-2 clean round as a Low non-blocking residual; fixing it would mutate the reviewed digest and require a further review round for a one-clause refinement, so the Phase 3 exit captures it here per the receiving-review Backlog capture rule instead of another round.

## Dedup probe

Searched open backlog filenames and bodies for builder, Lombok, constructor placement, and rule 27. The only related item is the covered origin `2026-10-20-java-construction-and-interface-guidance.md`, which this execution closes; it does not own the multi-constructor placement wording. No merge.

Capture hygiene: scan-public-hygiene --files pass.
