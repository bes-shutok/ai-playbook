# Rejected plans

Archive for plans rejected by explicit decision: a decision against doing the work, distinct from superseded (replaced by a successor) or completed plans. Files arrive here through the plans skill lifecycle (a `git mv` from `docs/plans/`), never by deletion; the move itself stays visible in git history.

Rules for every rejected plan:

- Preserve the full source content verbatim: do not edit, truncate, or annotate the plan body on the way in. The rejected plan stays readable as history exactly as it was last reviewed.
- Record the decision metadata in the ownership-registry row appended in the same pass (`doc-hierarchy` row shape): `state: rejected`, `archived: <rejection date YYYY-MM-DD>`, and a non-empty `reason` cell stating why the work was rejected. `scripts/doc_registry_validator.py` accepts a rejected row only with that real calendar date and reason, and reports a HARD finding for a rejected row missing either.
- A rejected plan is closed surface: plan readiness excludes it from active gating, the done sweep prunes only its own `plan-deliverables.txt` entries, and the docs-branch certified-plan guard treats it as archived (never compared against a certified digest).

Revival is a new decision: move the plan back under `docs/plans/` and re-run the normal readiness path before execution. Never delete the rejection record to make room; the registry row and this archive are permanent history.
