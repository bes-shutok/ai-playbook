# Backlog: done sensitive-data scan must distinguish credentials from domain terms

Status: rejected (2026-09-26; superseded: the credential-shaped patterns are landed in done_sweep_gates_lib.py; verified live)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; security-scanner false-positive tuning (security defers on this pet repo). Revive on the false-positive noise is witnessed masking a real finding, or the profile flips, or a project-priority-profile change.)
Workflow: backlog
Date: 2026-09-22
Class: done workflow gate false positive

## Problem

The done pre-commit sensitive-data gate treated bare words such as `token`,
`password`, and `secret` as evidence of sensitive data. Public workflow prose
about claim ownership and policy state therefore failed the gate even when it
contained no credential value. This made the finalization path reject a valid
plan and encouraged unnecessary wording changes instead of checking the real
secret boundary.

## Exact location

- `scripts/done_sweep_gates_lib.py`, `DIFF_CONTENT_PATTERNS` and the
  `sensitive-data-scan` gate.
- `scripts/test_done_sweep_gates_lib.py`, sensitive-data gate fixtures.

## Suggested fix

Keep path, domain, email, employer-brand, and attribution checks unchanged,
but make credential checks assignment-shaped and value-shaped. Add fixtures
proving that neutral domain prose passes and that an assigned credential-like
value still fails. Keep the canonical script and the deployed runtime copy in
sync, with an explicit comparison check.

## Reproduction evidence

Before the fix, the gate reported matches for public prose containing
`claim token` and `owner/token`. After the fix, the same prose passes, while an
`access_token` assignment with a value is rejected. The regression suite
covers both cases.

## Suspected root area

The scanner encoded category names as substring patterns instead of matching
the structure that distinguishes a credential assignment from ordinary
technical vocabulary.
