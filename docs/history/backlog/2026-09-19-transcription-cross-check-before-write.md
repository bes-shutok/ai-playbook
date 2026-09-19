# Backlog: transcription cross-check before writing into forms, invoices, records

Captured: 2026-09-19 (source: cross-session friction audit - user-correction mining over 1,776 typed prompts, 2026-07-17 → 09-19)
Status: open
Priority: medium

Workflow: backlog

## What was witnessed

The highest-stakes correction class: data-entry accuracy in tax-reporting, medical-data, and personal-finance workflows (~8 corrections, Jul 25 → Sep 13). Verbatim: "You filled the Residency second time. I have only one residency... country and id are now filled twice. Date of birth is slightly off in position. And the name again in the lower part where the date should be" (form field swaps and double-fills); "again these 2 invoices are the same 2026-09-10_bcp_dd_proof_46.82_a and b. DOn't you see it?" (duplicate invoice listed twice); "sorry, not 37, the one of 32.9" (wrong amount carried into a summary). The corrections-mining pass also showed personal-admin repos run ~2x the correction rate of the skill repo (7.5–10.3% vs 4.4–4.7%) - extraction-and-transcription tasks are where the agent is least reliable without a cross-check.

## Suggested fix

A cross-check-before-write step for transcription-shaped tasks: before writing extracted values into forms/summaries, (1) dedupe source-identical entries on an amount+date+merchant key, (2) verify each written field against its source region rather than from memory of the source, and (3) for repeated workflows, persist canonical values in the project facts document and copy from there instead of re-deriving. Candidate to later grow into a small verification skill if the checklist proves stable.

## Acceptance

- A sample re-run of an invoice/form task produces a dedupe+verify receipt (entries deduped, fields checked against source).
- Zero new duplicate-entry or wrong-field corrections in the next corrections-mining pass.
