# Backlog: facts path resolver rejects valid TOML string quoting

- **Filed:** 2026-10-07, learn Step 1.8
- **Status:** covered (docs/history/plans/2026-10-17-facts-path-resolver-valid-toml-strings.md)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** consumer projects that run the closeout workflow need the resolver to accept valid facts values; do not defer this as formal-hardening for the skills repository alone.
- **Origin class:** consumer-feedback (pet)
- **Class:** fix-class
- **Driving force:** efficiency
- **Severity:** medium
- **Skill/step:** `scripts/facts_paths.py`, `resolve_toml_key_raw` (TOML value matcher near line 139)
- **Source reference:** witnessed during a consumer project's closeout on 2026-10-07; capture hygiene: `scan-public-hygiene --files` pass
- **Why not fixed now:** This session is capturing the closeout learning; changing and validating shared runtime helpers is separate maintenance work.
- **Dedup probe:** searched open backlog filenames and problem text for `facts_paths`, `single-quoted TOML`, and `TOML string quoting`; no matching open item found.

## Problem statement

Observed: the facts resolver extracts a TOML-fenced block but matches only double-quoted strings. A valid single-quoted path value therefore resolves as absent, causing the closeout path gate to stop. Converting the local ignored facts values to double quotes was a manual workaround.

Expected: accept valid TOML string forms, or validate and clearly document a narrower facts format before any consumer relies on it.

## Exact location

`scripts/facts_paths.py`, `resolve_toml_key_raw`, the regular expression matching a key/value line.

## Suggested fix

Parse the TOML fence with a TOML parser, or extend the matcher and its coverage to the valid forms the facts contract permits. Add a regression witness proving that a single-quoted path resolves to the same value as its double-quoted form.
