# Backlog: Document-registry rows appended after the first prose break are invisible to the gate parser

- **Status:** open
- **Driving force:** code-quality (Phase 3 r1 deferred finding, plan docs/history/plans/completed/2026-11-08-backlog-completed-dir-regrowth.md review record 2026-11-09-backlog-completed-dir-regrowth-code-review-r1)
- Cluster: doc-registry-gate-placement

`parse_registry` (scripts/doc_registry_validator.py) stops at the first non-table line after
the header, so rows appended after the prose sections that past archive steps left inside
docs/maintenance/document-registry.md are physically present but gate-invisible: they take no
licensing overrides, gate reads silently ignore them, and the population grows with every
archive that appends past the break (witnessed during the 2026-11-09 completed-corpus sweep,
which had to place its 51 licensing rows inside the first contiguous block to be licensed).

Remedy: reconcile the existing invisible rows into the visible block (or re-home the prose
sections below the table), then add a placement guard to the archive step so new rows cannot
land past the break.
