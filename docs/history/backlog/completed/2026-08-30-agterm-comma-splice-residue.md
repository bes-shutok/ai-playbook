# agterm skill: comma-splice residue from the em-dash normalization pass

Status: resolved (2026-08-30)
Workflow: backlog
Source: docs/reviews/2026-08-30-branch-review-agterm-agent-runtimes-r4.md, reconciliation record (rounds r2-r4); review-reconciliation run 2026-08-30

## Problem

The r1-fix commit (5f93e5b) replaced 462 spaced em dashes with commas across the agterm skill files.
Where the original dash joined two independent clauses, the comma leaves a grammar-only comma splice.
Every found instance was fixed in its round (r2: one meaning-risk site plus five grammar sites and
eight join artifacts; r3: nine grammar sites; r4: four grammar sites), but the class keeps
regenerating under detection: each round's worker used a different method (targeted list, full-text
reading, random sampling) and found surviving siblings. A mechanical enumeration was attempted in
r4 and is not reliable: the candidate pattern space overlaps hundreds of legitimate appositive and
subordinate constructions, so a regex cannot separate real splices without reading.

Severity is uniformly grammar-only: the reviewing worker stated "no meaning risk", "no behavior
impact" at every site. The repo's enforceable policy (no em dashes) is satisfied; splices are
prose polish on upstream-style vendored prose. A full human-quality read of roughly 3,400 lines is
the only exhaustive witness, which is disproportionate to the severity.

## Reconciliation disposition

Sibling residual plus a verification gap: the class's root cause is one completed transform; found
members are all fixed; the unknown-depth residue is accepted rather than chased by sampling.
Closure witness for a future pass: a full manual prose read of the six agterm Markdown files that
logs every splice it finds, run together with another substantive rewrite of those files (not
standalone).

## Suggested fix

When the agterm skill files next get a substantive rewrite (an upstream sync with manual merging or
a content revision), run a full-read splice pass in the same session: read each file end to end,
replace clause-joining bare commas with semicolons or colons, and keep the repo's em-dash gate
green. Do not run sampling-based review rounds for this class alone; they find two to four sites
per round indefinitely without converging to zero.

## Location

- `agents/skills/agterm/*.md` (all six Markdown files; densest in reference.md and SKILL.md)

Update (r5, 2026-08-30): the reference.md:1156 site named in the r4 record was initially claimed fixed but the repair had not landed; it was applied with an asserted occurrence count in r5. The accepted-residue class remains as described.

## Resolution (2026-08-30)

Executed standalone per user request, ahead of the next substantive rewrite. Method: a full read of
all six agterm Markdown files; every clause-joining bare comma left by the normalization was replaced
with a semicolon or colon (130 fixes; cookbook 6, agent-runtimes 9, troubleshooting 15, SKILL 23,
examples 22, reference 55). The suite (46 checks), the em-dash gate, and the hygiene scan stayed
green throughout. A diff-scoped documentation-verification pass checked the result before this item
was closed.
