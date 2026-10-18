# Backlog: segment validation errors can expose caller input

- **Filed:** 2026-10-05, operator-directed maximum urgency
- **Status:** resolved in STORY-KEY execution
- **Workflow:** backlog
- **Priority:** superurgent (operator-marked)
- **Origin class:** observed client-visible data exposure
- **Class:** fix-class
- **Driving force:** security

## Problem

The segment definition error handler copies a `PredicateCatalogValidationException` message into the public `ApiError.message`. Rule compilation builds that message using caller-supplied predicate fields and values. Invalid input can therefore be reflected into an HTTP error response, contrary to the project's client-visible error safety rule.

## Evidence

- Observed 2026-10-05 in STORY-KEY Phase 3 Round 5 correctness review.
- `TransportExceptionHandler.handlePredicateCatalogValidation` calls `invalidArgument(exception.getMessage(), details)`.
- `SegmentRuleCompiler.compileNode` includes the rejected request-derived predicate key in the exception message.
- `docs/maintenance/project-guidelines.md` #6 prohibits copying raw exception messages into client-visible fields.

## Expected

Return a curated service-owned message for catalog validation failures and retain the stable machine-readable error details. Add an HTTP-level witness that sends a unique marker in invalid rule input and asserts the complete response body omits that marker while preserving the expected status and error key.

## Resolution

Fixed in the STORY-KEY branch by returning the curated message `Invalid segment definition.` from `TransportExceptionHandler.handlePredicateCatalogValidation`. The HTTP integration test now sends a unique invalid value and asserts that the response body omits it while retaining the existing 400 status and catalog validation key.

Verification: `mvn -pl app -am -Dit.test=SegmentDefinitionControllerIT#rejectsUnsupportedCatalogRuleWithContractError -Dfailsafe.failIfNoSpecifiedTests=false verify` passed on 2026-10-05. App fix commit and targeted review reference will be added when the review iteration closes.

## Source

- Observed 2026-10-05 during STORY-KEY Phase 3 Round 5.
