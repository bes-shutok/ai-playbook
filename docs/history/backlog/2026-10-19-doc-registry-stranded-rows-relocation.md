# Backlog: relocate stranded doc-registry rows into the parsed first table (2026-10-19)

- **Filed:** 2026-10-19, learn Step 1.9 capture from the 2026-10-19 exec-run session
- **Status:** open
- **Priority:** low
- **Workflow:** backlog
- **Origin class:** learn project-issue capture
- **Class:** fix-class
- **Driving force:** correctness (five completed-history rows registered in the file but invisible to the registry gate, so their sources read as unregistered on every validate run)

## Problem

`docs/maintenance/document-registry.md` carries five completed-state rows outside the parsed first table (after a bullet list or other non-table block), so `scripts/doc_registry_validator.py` never parses them and `validate` warns their completed-plan sources as unregistered on every run. Re-derived from disk 2026-10-19 with the validator's own helpers (parse plus the new present-but-unparsed diagnostic landed c861ee3fc):

- `plan-scope-gist-surface-1010-plan` and `plan-scope-gist-surface-1010-backlog` (2026-10-10)
- `plan-authoring-done-closeout` (2026-10-11)
- `prompt-log-deferred-origin-stale-pin` (2026-10-12)
- `done-final-only-learn-intermediate` (2026-10-19, landed today, still stranded)

The misplacement is recurring, not one-off: development-lessons #80 witnessed two occurrences on 2026-10-17, and the five standing rows include one filed today. The validator-side remedy already landed (the diagnostic names each stray row beside the unregistered-file warn and beside the check-writes refusal); what remains is the one-time data repair and whatever placement habit keeps failing.

## Suggested fix

1. Move the five stranded rows into the first table (byte-preserving cell text; keep their identities, dates, and audit cells), deleting the stray copies; the one-line-per-row shape stays a Markdown table row in every position.
2. Confirm with `validate` (warn count for those five sources drops to zero) and the full validator selftest.
3. Do not add a pre-write lint or hook for the placement habit: that alternative was already rejected as machinery without admission when the diagnostic landed (see the pruned EXEC-PROMPTS entry `doc-registry-row-outside-parsed-table-refusal`, landing c861ee3fc, rejected-alternatives list).

## Rejected alternatives

- Add a mechanical pre-write lint enforcing row placement: rejected as machinery without admission, one low-severity recurring warn class and the additive diagnostic already naming the defect (`docs/history/backlog/EXEC-PROMPTS.md`, pruned entry receipt).
- Widen the parser to read every table: rejected, the first-table contract is the documented validator behavior since introduction (`scripts/doc_registry_validator.py` module docstring).
- Leave the rows where they are: rejected because unregistered completed sources weaken the immutability gate's claimed-src set and every validate run carries five standing warns that train operators to ignore the warn tier.
