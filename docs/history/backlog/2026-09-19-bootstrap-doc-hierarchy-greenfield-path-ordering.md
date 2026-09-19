# bootstrap-ai-playbook greenfield fallback can seed paths doc-hierarchy-migrate forbids

Status: open
Priority: high

Skill/step: `agents/skills/bootstrap-ai-playbook/SKILL.md`, Path Discovery and Step 3; interplay with `doc-hierarchy-migrate` step2/step6 gates.

Observed: on a consumer repo with no `docs/` tree at all, bootstrap path discovery finds no existing homes and, with the interactive ask unanswered, falls back to top-level `docs/plans/` and `docs/reviews/`. A later doc-hierarchy-migrate on the same repo then fails step2 (plans and reviews still at docs root) and the recorded TOML keys diverge from the canonical post-migration map (`docs/history/plans/`, `docs/history/reviews/`), so the facts file must be rewritten after the migration.

Expected: when the repo has no docs tree, bootstrap should ask explicitly whether the doc-hierarchy schema is the target layout and, when it is, seed the canonical map (`docs/history/plans/`, `docs/history/reviews/`, `docs/history/backlog/completed/`) so the two skills compose in either order; at minimum the greenfield default should warn that it conflicts with doc-hierarchy-migrate step2.

Environment: consumer documentation-only repo, runtime deployment of the playbook, 2026-09-19; observed during a real bootstrap followed by a same-day migration in the same session.

Suspected root area: bootstrap-ai-playbook Path Discovery defaults vs doc-hierarchy canonical layout; the interplay is not encoded in either skill.
