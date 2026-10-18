# Backlog: collapse rate-limit request-id residue in friction-audit message classes

- **Filed:** 2026-10-09, session retrospective learn capture (folds the dated friction-audit finding)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** friction-audit run 2026-10-08 finding 1 (Medium, tooling), folded by an authorized turn per the run's report-only dispatch contract
- **Class:** fix-class
- **Skill/step:** `scripts/friction_audit_quant.py`, Agent message-class normalization
- **Severity:** medium; the digest's message-class section becomes unreadable for the dominant error family, though the correct counts exist elsewhere in the same output

## Problem

The quant script normalizes Agent rate-limit errors by redacting digit runs to `<n>` but leaves each request-id's alphabetic residue, so one semantic class (`[1302][Rate limit reached for requests][<request-id>]`) fragments into roughly 300 distinct classes of one occurrence each, burying the digest's message-class section under hundreds of singleton lines (~550 lines for one semantic class). The leading error code is redacted away too, so the class table also conflates per-request 429s with 5-hour quota walls; the provider 429-codes section counts the two correctly, so the information exists in the same run's output, just not in the class table.

## Evidence

- Run 2026-10-08: digest message-class section lines 16 through 568 versus the provider 429-codes section showing 287 per-request 429s against 27 quota walls (gitignored artifacts; re-derive from the next run's digest after the fix).

## Exact location

`scripts/friction_audit_quant.py`, the message-class normalization applied to Agent error messages.

## Suggested fix

Collapse the trailing bracketed request id entirely in the class label and keep the leading error code un-redacted, so classes read like `[1302][rate limit reached for requests]`; leave the provider 429-codes section unchanged.

Acceptance: the next run's digest message-class section carries one class per semantic form with counts in the hundreds instead of hundreds of singletons, and the 1302 versus 1308 distinction is readable straight from the class table.
