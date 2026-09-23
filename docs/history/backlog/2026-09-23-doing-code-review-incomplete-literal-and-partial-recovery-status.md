# Backlog: doing-code-review INCOMPLETE header literal drift and partial-recovery per-finding status

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-23
Class: review r1 deferred findings F2 + F3 of the review-post landing verification execution

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Driving force

The r1 review round of the landing-verification plan landed the posting
verification contract but deferred two Low consistency findings. Both are
record-accuracy nits with no re-post correctness loss, but each can produce an
ambiguous staging record: two writers can emit different header literals for
the same INCOMPLETE state, and a partially successful recovery pass under-states
which findings did land.

## What to build

1. In the posting step's INCOMPLETE branch and the Direct Mode bullet, reference
   the transitions paragraph's full `INCOMPLETE (posting incomplete; unlanded
   findings remain pending)` literal instead of the bare word (r1 F2).
2. In the same INCOMPLETE branch, state that findings the recovery pass did land
   carry the per-finding Status `posted` (r1 F3; the transitions paragraph
   already implies it).

## Notes

- The edits sit inside regions pinned by several exactly-once gates (the step-6
  sentences and the Direct Mode bullet); re-run the plan's whole gate block after
  the edit rather than reasoning about which pins are adjacent.
- Do not touch the validator anchor line `- Status: STAGED (not yet posted)`.

## Review r3 addendum

3. The F2 quoted literal in this item is hard-wrapped inside its code span, so
   the rendered quote misquotes the single-space literal; unwrap or reflow the
   code span when doing item 1.
