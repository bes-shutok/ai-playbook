# Plan: Normalize Agent Rate-Limit Message Classes

Backlog origin: docs/history/backlog/2026-10-09-friction-audit-quant-message-class-normalization.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-friction-audit-quant-message-class-normalization-p04877750-r*.md
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Agent rate-limit form:** A bracketed error message beginning with code 1302 or 1308, followed by its description and an optional trailing bracketed request identifier.
- **Message class:** The normalized label counted in the quant report's per-tool message-class table.

## Why

The 2026-10-08 friction-audit digest showed hundreds of singleton message classes for one request-limit family. Current `_message_class` redacts every digit run, removing the 1302/1308 distinction, but leaves letters in request IDs, fragmenting counts. A live probe on the current function reproduces both effects.

## Gist & Examples

TLDR: Normalize the known Agent rate-limit forms so the digest is readable and preserves the provider code.

**Before:** `[1302][Rate limit reached for requests][req-abc123]` becomes `[<n>][rate limit reached for requests][req-abc<n>]`, splitting request IDs into distinct classes and losing the code.

**After:** The 1302 label retains the code and description, drops the trailing request ID, and aggregates variants together. A corresponding 1308 quota label remains distinct.

**Edge cases:** Messages outside these recognized forms keep the existing whitespace, case, and digit-run normalization.

## Outcome

Normalize the recognized Agent rate-limit messages while preserving the existing behavior for other messages.

- 1302 request-limit variants share a readable class label.
- 1308 quota variants share a distinct readable class label.
- Unrelated numeric messages keep their existing `<n>` normalization.

Gate delta: no machinery, gates, fences, protocol layers, schema fields, or task pause conditions are added or removed.

## Assumptions

- Assume only the known Agent 1302 and 1308 forms need special handling; basis: the origin evidence and live probe show both codes share a bracketed format.
- Assume the existing aggregation consumes `_message_class` output without additional normalization; basis: the current call path in `scripts/friction_audit_quant.py`.
- The maintenance-selected authoring arm records narrow form-specific handling as the simplest viable option; broad digit or identifier rewriting risks altering unrelated classes.

Decision points requiring a grill: none remain.

## Design Invariants (CR Guard)

- Keep 1302 and 1308 visible and distinct in message-class labels.
- Remove variable trailing request identifiers for recognized forms.
- Keep normalization of unrelated messages and provider 429-code counts unchanged.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: different request IDs for one recognized code produce the same class label, and the two codes remain distinct.
- Compatibility: an unrelated numeric message retains digit-run normalization to `<n>`.

**Done when:** The focused behavior checks for 1302, 1308, and an unrelated numeric message pass, and the script compiles.

**Ship when:** none; this is a local report-formatting fix with no deployment gate.

## Review Scope

**Explicit must-fix:** findings on the listed path are in scope.

**Production code:**
- `scripts/friction_audit_quant.py` (Task 1)

**Tests:**
- No test path is prescribed; select focused behavior validation from repository evidence during implementation.

**Plan-related extension:** Add another path only when implementation evidence shows it is required to satisfy the task's behavior.

**Out of scope:**
- Provider 429-code counting and other message families.
- Digest layout and historical audit artifacts.

## Tasks

### Task 1: Normalize recognized Agent rate-limit forms

Files:
- `scripts/friction_audit_quant.py`

Primary class anchors:
- `_message_class` in `scripts/friction_audit_quant.py`, which normalizes error text before message-class aggregation.

- [ ] Given two 1302 messages that differ only in their trailing bracketed request ID, `_message_class` returns the same class label retaining `1302` and the lowercase description without the ID. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given equivalent 1308 quota messages, `_message_class` returns the same class label retaining `1308`, distinct from the 1302 label. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an unrelated numeric message, normalization still collapses its digit run to `<n>`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `scripts: normalize Agent rate-limit message classes` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```bash
python3 -m py_compile scripts/friction_audit_quant.py
```

During implementation, select and run the repository's focused behavioral validation for `_message_class`; keep supporting test paths and exact test commands in the execution record, not this plan.
