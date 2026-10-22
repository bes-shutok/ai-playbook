# Backlog: hard-mode clause pointer coverage extensions

Filed: 2026-10-23
Status: open
Driving force: usability

Origin: Task 1 intermediate review of plan 2026-10-22-review-staging-hard-validator-fail-fast-iteration (Phase 3 r1 finding F4 class). The SKILL_CLAUSE_POINTERS table landed with 20 exact mappings plus a bare `(review-staging SKILL.md)` fallback; the reviewer identified high-value families still riding the fallback although their owning sections exist:

- `version-1 sidecar field ...` (Version-1 sidecar contract)
- `extensions.cap_closure ...` (Cap-closure sidecar extension)
- `extensions.corrections ...` / `corrections verification:` (Corrections sidecar extension)
- `coverage ...` families other than "coverage attempt record" (Coverage sidecar contract)
- `mint pair field ...` (JSON sidecar usage paragraph)
- `Metadata Review mode ...` and clean-verdict/Last-fix-commit cross-field rule (Synthesis-time hard gates / Version-1 sidecar contract)
- `Superseded by link ...` (Canonical record and supersession)
- `source_digest` shape/stale (Version-1 sidecar contract)

Also a precision nit: `finding conservation: finding {fid} pattern disagrees` currently maps via the generic conservation marker to "Staged Markdown hierarchy (required)" while its clause lives in the Version-1 sidecar contract's Canonical Pattern IDs paragraph; a more specific marker ahead of the generic one would be exact.

Cluster: docs/history/plans/completed/2026-10-22-review-staging-hard-validator-fail-fast-iteration.md
