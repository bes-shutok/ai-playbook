---
name: transcription-cross-check
description: Cross-check duty for transcription into forms, invoices, summaries, and records. Use when filling a form from a source document, copying invoice entries, writing summary rows from raw data, or entering any extracted values into structured records. Enforces dedupe, verify-from-source, and canonical-value reuse before writing, and requires a cross-check receipt.
---

# Transcription cross-check

Transcription tasks (filling forms, entering invoices, writing summaries, updating records) carry a witnessed correction class: field swaps (a name written where a date belongs), double-fills (the same field or entry written twice), duplicate entries (the same source item listed twice), and wrong amounts carried from a neighboring row into a summary. All of these follow from one root habit: writing extracted values from memory of the source instead of from the source itself. This skill counters that habit with three duties performed in order before and during the write, and a receipt that records what was checked.

## The three duties

Perform all three duties in order. A duty is not optional because the task feels simple; the correction class recurs in simple tasks precisely because memory of the source feels reliable.

1. **Dedupe before writing.** Group the source entries on the dedupe key `amount+date+merchant` (for workflows without merchants, use the workflow's equivalent identifying fields: the fields that together make one entry distinguishable from every other entry in the same workflow). Never write two entries with the same dedupe key. If two entries share a key and every field, they are duplicates: write one. If two entries share a key but differ in some field, they are a near-duplicate: stop that entry's write (see the near-duplicate stop rule below).
2. **Verify from the source, never from memory.** Before writing each field, re-read its source region and copy the value from the re-read bytes. Do not write from what you remember the source saying, and do not write a value carried over from a neighboring row. If a field's value differs from what you expected, the re-read wins; flag the surprise in the receipt rather than silently reconciling it.
3. **Reuse canonical values.** For repeated workflows, copy canonical values (names, ids, addresses, recurring amounts, account numbers) from the facts document's canonical-values section instead of re-deriving them from the source each time. When a new value stabilizes (the same value used or confirmed across runs), extend that section so the next run reuses it. A canonical value still satisfies duty 2 if the source contradicts it: flag the conflict in the receipt and stop that field's write for the user to resolve.

## The receipt

Every run ends with a cross-check receipt listing three things:

- **Entries deduped**: each duplicate or near-duplicate found, with its dedupe key values.
- **Fields verified**: each written field confirmed against its re-read source region, with exceptions flagged (surprises, conflicts with canonical values, near-duplicate stops).
- **Canonical values**: which values were reused from the facts document's canonical-values section versus derived fresh, and any section extensions made.

The receipt is the run's observable output. A transcription run without a receipt is not done.

## Near-duplicate stop rule

A near-duplicate (same dedupe key, a differing field) is never silently merged and never written under one guess of which field is right. Stop the write for that entry, flag it in the receipt with the two differing values and their source regions, and ask the user to resolve the conflict before writing.

## Degradation without a facts document

A workflow with no facts document degrades gracefully: duties 1 and 2 still apply in full, the receipt notes canonical persistence as unavailable for that workflow, and duty 3's extension step is skipped (there is no section to extend). The other duties and the receipt are never degraded away.

## Integration Points

No first-party skill consumes this skill yet. The friction-audit lane is the measuring consumer: it samples receipts from transcription runs and measures the correction class against this skill's acceptance record below.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `facts_path` | Path of the facts document holding the canonical-values section | none (duties 1 and 2 apply without configuration) |
| `canonical_values_section` | Section name in the facts document where canonical values persist | `## Canonical values` |

Without these keys the skill still runs: only duty 3 degrades per the degradation rule above.

## Acceptance

Behavioral acceptance, measured by the follow-through friction-audit lane:

1. A sample re-run of a transcription task (for example, the witnessed duplicate-invoice correction) under this skill produces the receipt: the two source-identical entries deduped on their shared amount+date+merchant key, and each written amount verified by re-reading its source line before writing.
2. Zero new duplicate-entry or wrong-field corrections in the next corrections-mining pass after the skill is adopted, against the witnessed baseline of recurring corrections across two months and two repository families (2026-07-17 through 2026-09-19).
