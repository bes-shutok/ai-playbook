# Rejected backlog items

Archive for backlog items rejected by explicit decision: a decision against doing the work, distinct from completed (`Status: done`) or superseded items. Files arrive here through the backlog lifecycle (a `git mv` from the backlog top level), never by deletion; the move itself stays visible in git history.

Rules for every rejected item:

- Preserve the full source content: the body moves verbatim, and the only expected edit is the header status line the archive move rewrites, which records the decision inline as `Status: rejected (YYYY-MM-DD; reason)`. Everything below the header keeps its historical wording.
- Record the decision metadata in the ownership-registry row appended in the same pass (`doc-hierarchy` row shape): `state: rejected`, `archived: <rejection date YYYY-MM-DD>`, and a non-empty `reason` cell stating why the work was rejected. `scripts/doc_registry_validator.py` accepts a rejected row only with that real calendar date and reason, and reports a HARD finding for a rejected row missing either.
- A rejected item is closed surface: the origins-closure gate classifies it as closed, and the docs-branch backlog dedupe sweep applies the same twin rules under this directory as under `completed/` and `deferred/` (a matching stale top-level copy is removed from the overlay; mismatched content is retained and surfaced, never deleted).

Revival is a new decision: promote the item back to the backlog top level (or into a plan header origin) and re-run the normal lifecycle from there. Never delete the rejection record; the registry row and this archive are permanent history.
