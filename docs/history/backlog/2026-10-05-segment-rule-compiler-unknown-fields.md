# Backlog: segment rule compilation ignores unsupported object fields

- **Filed:** 2026-10-05, operator-directed urgency
- **Status:** completed
- **Workflow:** backlog
- **Priority:** superurgent (operator-marked)
- **Origin class:** observed contract-validation defect
- **Class:** fix-class
- **Driving force:** reliability

## Problem

The segment rule compiler derives predicate keys from selected fields but does not reject additional fields on a rule object. A payload can therefore include a valid `duration` and the retired `window` field, pass compilation, and persist JSON that does not match the compiled predicate. The saved rule can appear to express one time range while evaluation applies another.

## Evidence

- `docs/history/feature-notes/SEGMENTS_rfc.md`, section 6, business logic rule 1: requires rejecting unknown rule keys and the retired wire field `window`.
- `segments/src/main/java/com/<consumer-organization>/crm/segments/domain/segment/SegmentRuleCompiler.java`, `compileNode`: validates a derived predicate key but does not enumerate or reject fields present on the rule object.
- `app/src/main/java/com/<consumer-organization>/crm/app/transport/controller/SegmentController.java`, `rules`: passes the generated request rules into the compiler as a `JsonNode` without filtering unknown fields.
- Observed 2026-10-05 during STORY-KEY Phase 3 review: the correctness worker demonstrated that a valid event duration with retired `window` is accepted and persisted while compilation uses `duration` only.

## Expected

Validate each rule object's exact allowed field set before deriving a predicate key. Reject retired and unknown fields with the typed rule-validation error before persistence. Add compiler and endpoint witnesses proving the retired-field payload is rejected and no segment row is written.

## Resolution

Implemented exact rule-object field validation in `SegmentRuleCompiler` before catalog compilation and persistence. Compiler tests reject extra fields on AND, profile, and event shapes. `SegmentDefinitionControllerIT#rejectsUnknownRuleFieldsBeforeCreateOrReplaceWrite` verifies a rejected create inserts no row and a rejected replacement preserves the stored definition. The focused unit suite passed 9 tests, and the controller/Flyway integration verification passed in the STORY-KEY Phase 3 review fix iteration. The service fix landed in `<consumer-repository>` commit `f46190d50d5cdb68e85aa9eeee57d83639a3559c` after the execute-plan review-fix done boundary.

## Source

- Observed 2026-10-05 during STORY-KEY Phase 3 review.
