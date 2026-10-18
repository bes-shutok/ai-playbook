# Backlog: generated Set erases duplicate request values before validation

- **Filed:** 2026-10-09, operator-directed investigation
- **Status:** resolved by operator decision on 2026-10-09
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** generated-model behavior mismatch
- **Class:** fix-class
- **Driving force:** correctness + maintainability

## Problem

OpenAPI Generator 7.20.0 maps array properties with `uniqueItems: true` to Java `Set` properties and initializes them with `LinkedHashSet`, even when the schema supplies `x-java-type: java.util.List<...>`. In the protected-data batch request, Jackson therefore binds a JSON array into a set before the app-owned request validator sees it. Duplicate values disappear during binding, so the validator cannot reject duplicate user IDs or field selectors as the API contract promises. A linked set retains first-seen order, but still destroys the evidence of duplicates.

The build currently repairs the generated model with four exact string replacements in the Maven `process-sources` phase. Those replacements change imports, property types, and default collection construction back to `List` and `ArrayList`. They preserve the intended duplicate-rejection and input-order behavior, but are brittle against generator output changes and are not self-validating if a token stops matching.

## Evidence

- Re-running the `generate-sources` lifecycle before `process-sources` emits `Set` fields, `LinkedHashSet` defaults, and set-based `add...Item` methods for all three request arrays.
- The schema keeps `uniqueItems: true` and declares `x-java-type` as `List`, but the generator still emits `Set`.
- The request converter explicitly rejects duplicates after binding; that check cannot detect duplicates removed by set binding.
- The generated class is not checked in; the Maven replacements run after generation to restore list semantics.

## Original expected behavior

Keep the OpenAPI uniqueness constraint and reject duplicate submitted values at the application boundary, while binding request arrays to an ordered Java `List` so duplicates remain observable. Replace unguarded exact-string rewriting with a generator-supported or template-based customization whose output is checked by a focused generated-model test or build assertion. The check must prove the three request properties are `List`-typed and that duplicate JSON elements survive binding until the app validator rejects them.

## Resolution

The operator chose to use the generated `Set` representation and accept duplicates being coalesced during binding, retaining the first occurrence. The implementation removed the four post-generation replacements and the duplicate-scanning validator. `uniqueItems: true` remains in the OpenAPI contract, and request arrays bind as `LinkedHashSet`.

## Alternatives considered before the operator decision

- Remove `uniqueItems` from the schema and depend only on app validation: rejected because the public contract would stop declaring a real uniqueness constraint, and the generator's internal collection choice would be driving the API definition.
- Keep the generated `Set` while requiring duplicate rejection: rejected for that original requirement because binding silently normalizes duplicates. The operator later chose that normalization behavior and no longer requires duplicate-specific errors.
- Upgrade OpenAPI Generator alone: not selected; the current stable Spring template still chooses `LinkedHashSet` for `uniqueItems`, and the operator accepts that generated behavior.
- Replace the four substitutions with a scoped custom template or generator extension to retain `List`: rejected for this endpoint because duplicate rejection is not required and the operator chose the simpler generated `Set` behavior.

## Source

- Investigation of the generated request model and its Maven post-processing on 2026-10-09; implementation repository paths and identifiers intentionally omitted.
