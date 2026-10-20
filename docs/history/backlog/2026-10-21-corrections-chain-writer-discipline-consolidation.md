# Backlog: corrections writer load discipline and resolver consolidation

- **Filed:** 2026-10-21, from Phase 3 code review r1 of `corrections-chain-operator-ack-end-to-end`
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** duplication drift risk
- **Class:** refactor-class
- **Driving force:** simplification; secondary: correctness
- **Skill/step:** `scripts/corrections_record.py` (`record_correction_authorization`, `verify_corrections` ack loop), `scripts/validate_review_staging.py` `_resolve_primary_checkout`
- **Cluster:** docs/history/backlog/2026-10-21-corrections-chain-recursion-refusal-and-pins.md
- **Dedup probe:** design-lens findings from r1; the parity pin row in the Task 2 review covered two bodies, this row records the third.

## Problem

Four consolidation debts from Phase 3 r1 (design-simplicity and correctness lenses, all verified against code):

1. A third first-entry primary-checkout resolver body exists: staging re-implements the parse loop over `cr.git_text` instead of calling the `resolve_primary_checkout` leaf in the same sibling module it already imports, and the leaf's own copy drops the `expanduser()` the other two apply; the parity pin covers only the staging and done-sweep bodies.
2. The writer re-implements `load_correction_authorizations`' read/decode/validate sequence twice inline (pre-read and drift re-read) with three co-located copies of the refusal strings and catch tuples, while its own read-back leg calls the shared helper; the Task 3 implement log's claim that refusals ride the append leg is contradicted by the receipt-leg copies.
3. `verify_corrections`' plan-family `primary_checkout=None` leg reuses the retired turn-record wording (`no witness record path was provided`) for a condition that is actually an unresolved primary checkout, and duplicates the caller-selected-witness refusal text verbatim in a second function.
4. The staging selftest builds the 10-key authorization entry dict inline beside the same file's `_ack_entry_for` helper; the two same-file copies can drift independently.

## Expected

Wrap the staging resolver on the leaf's `resolve_primary_checkout` and extend the parity pin to all bodies; extract a `_load_state_document` leaf the writer's pre-read and drift re-read share (leg tokens unified or the shared-leg choice documented); give the None-primary plan leg a message naming the unresolved primary checkout and single-home the caller-selected-witness text; fold the inline entry dict into `_ack_entry_for`.
