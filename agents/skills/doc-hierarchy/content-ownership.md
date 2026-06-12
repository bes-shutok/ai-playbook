# Content ownership (doc-hierarchy skill family)

**Rule:** Each topic has one canonical file. Other skills **link** — do not copy tables, checklists, or move procedures.

| Topic | Canonical file | Consumers link only |
|-------|----------------|---------------------|
| Team rationale, Layer 1/2/3 rules, maintenance model, PR checklist | [company-decisions.md](company-decisions.md) | `doc-hierarchy`, `doc-hierarchy-upkeep`, `instruction-templates` |
| Target layout tree, skill family, migration-complete signal, precedence | [SKILL.md](SKILL.md) | `doc-hierarchy-migrate`, `_shared/doc-paths.md` |
| Classification outcomes, move/merge tables, Step 2 special cases (`examples/`, `reviews/`) | [migration-map.md](migration-map.md) | `doc-hierarchy-migrate` |
| Paste templates (project-guidelines, AGENTS, README, architecture placeholder) | [instruction-templates.md](instruction-templates.md) | `doc-hierarchy-migrate` Step 5 |
| Migration workflow steps, repair mode, execution contract | [../doc-hierarchy-migrate/SKILL.md](../doc-hierarchy-migrate/SKILL.md) | — |
| Layer 1/2 upkeep workflow (post-migration) | [../doc-hierarchy-upkeep/SKILL.md](../doc-hierarchy-upkeep/SKILL.md) | — |
| Bash gates (all phases) | [../doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh](../doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh) | migrate/upkeep skills; optional remote CI references skill path — **never** vendored into service repos |

When editing, update the **canonical** file first, then adjust links in consumers — never duplicate prose across files.

**Precedence on conflicts:** [company-decisions.md](company-decisions.md) Layer 2 placement (what belongs under `maintenance/` vs repo root) wins over stale rows in [migration-map.md](migration-map.md) (for example legacy `KEEP root` for `docs/dashboards/`). Update migration-map and `verify-doc-hierarchy.sh` together when reconciling.
