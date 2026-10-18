Status: open

Priority: high

Class: fence-class

Origin class: learn Step 1.8 skill-usage issue capture (exec-run session 2026-10-17, playbook repo)

## Observed versus expected

Observed: during a landing rider, an executing-session registry row was
placed after a bullet list in `docs/maintenance/document-registry.md`.
`scripts/doc_registry_validator.py` parses only the FIRST Markdown table
and ignores rows after any non-table line, so the row was silently
unparsed and the gate refused with a row-count delta reported on both
sides of the edit, without naming that the row text exists in the file
but outside the parsed table region. Resolving the refusal required
empirically re-deriving the parser's boundary from the script (two extra
refusal cycles in the landing's critical section).

Expected: when a check fails for an identity whose row text IS present in
the registry file but outside the parsed first-table region, the refusal
says so in one line (row present but unparsed; rows after the first
non-table line are ignored), so the remedy is named rather than
re-derived under landing pressure.

## Reproduction (trimmed)

Place a well-formed registry row immediately after a bullet list in the
registry file and run the validator's registry-check mode against the
edit: refusal reports a row-count mismatch; nothing in the output points
at the un-parsed row's location.

## Environment

Playbook repo, 2026-10-17, vendored copy equals repo copy at the time of
the run; validator at `scripts/doc_registry_validator.py` (first-table
parse documented in its module docstring, lines ~90-95).

## Suspected root area

`scripts/doc_registry_validator.py` refusal-message construction: it
reports the aggregate row-count delta but never inspects whether the
failing identity's row text appears elsewhere in the file (outside the
parsed table). Bounded fix class: diagnostic message narrowing only; no
new gate, no parse-behavior change.
