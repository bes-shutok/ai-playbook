# Backlog: lessons-gate recovery must distinguish duplicate IDs from untagged lessons

Status: done (2026-09-30; legacy origin fold completed post-execution: covered by docs/history/plans/completed/2026-09-27-deferred-residual-dispositions.md)
Priority: medium
Urgency remark: witnessed: the tag-unclassified recovery remedy did nothing for a duplicate id and needed a manual fix
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)
Workflow: backlog

## Problem

The strict user-level lessons validator reported a duplicate numeric lesson identifier. The documented recovery offered `lessons_adopt.py --tag-unclassified`, but that command only adds the `Family unclassified` tag to lessons that lack a family tag. It cannot repair duplicate identifiers, so the first recovery attempt made no change and the operator had to inspect the duplicate headings and assign a unique number manually.

## Expected behavior

The blocked learn/done recovery message should branch on the validator category:

1. `untagged` or `invalid-family`: use the tagging/adoption workflow.
2. `duplicate`: inspect the colliding headings, choose a unique identifier, update any same-corpus references, and rerun the validator.
3. `multiple-tags`: remove the competing family tags after classifying the lesson.

The message should not present the unclassified-tagging command as a complete remedy for duplicate identifiers.

## Evidence

- Validator output: `UL#<number>: duplicate`.
- Tagging command output: `0 lessons rewritten (all already tagged)`.
- Manual recovery: the later colliding heading was renumbered, then the lessons validator passed.

## Scope

Update the learn/done recovery contract and add a regression test covering each validator category and its recommended recovery action. Keep the repair operator-driven; do not automatically renumber lessons or rewrite cross-references.
