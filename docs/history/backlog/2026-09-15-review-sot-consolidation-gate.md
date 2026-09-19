# Review-agent SOT consolidation gate

- **Date:** 2026-09-15
- **Status:** open
- **Workflow:** backlog
- **Plan note (2026-09-18):** the review-records-contract plan no longer
  carries this item (approved scope split); it stays a standalone
  churn-reduction origin.

## Problem

Documentation reviews can resolve one scope decision by copying the same
normative prose into many Layer 1, Layer 2, RFC, task, and decision-archive
documents. That increases drift risk and makes a historical artifact look like
a current source of truth. The review output may correctly identify the facts
while still recommending an unnecessarily broad edit set.

## Proposed review-agent behavior

When a review changes a cross-document scope decision, the documentation lens
should first identify the authority roles involved and nominate no more than
one or two current SOT owners for that decision. It should then distinguish:

- normative contract or workflow text, which belongs in the nominated owner;
- Layer 1 and Layer 2 consumer documents, which should receive a short pointer
  or audience-specific delta rather than a copied decision matrix;
- completed RFCs, plans, task ledgers, and decision archives, which should stay
  immutable when they are historical, or receive an explicit historical /
  context-only banner if readers could mistake them for current SOT.

The review should stage one consolidation finding for a duplicated normative
decision, not one finding per affected consumer. A broad synchronized edit
should be suggested only when a consumer owns an independent contract that
would otherwise become stale.

## Acceptance criteria

- The documentation review workflow asks for authority-role classification
  before recommending multi-document scope edits.
- Review staging records the nominated SOT owner or owners and the disposition
  of each affected consumer: pointer, audience-specific delta, historical
  context, or independent contract update.
- A repeated normative paragraph across living documents produces one
  consolidation finding with a proposed owner, not a fan-out of duplicate
  findings.
- Historical-path documents are not treated as current SOT by default, and a
  review can require an explicit context banner when their stale content is
  likely to mislead.
- Existing authority-role distinctions remain valid: wire schemas, workflow
  rules, ADRs, examples, glossary entries, and historical artifacts may each
  own different kinds of content without becoming duplicate SOTs.
- The behavior is covered by a realistic review fixture and the staging
  validator checks any new required metadata.

## Non-goals

- Do not make the review agent rewrite every consumer document whenever one
  source changes.
- Do not infer that a document is frozen solely from age or path; archival
  transitions still require the repository's explicit lifecycle rules.
- Do not collapse genuinely independent wire, workflow, decision, or example
  contracts into one file.

## Origin

Observed during a documentation review where a single consent-scope correction
was initially spread across many active and historical documents. The immediate
service-repository change is intentionally limited to its two current SOT
documents plus pointers and historical labels; this backlog item tracks the
cross-project review-agent improvement.
