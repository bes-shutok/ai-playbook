---
name: doc-hierarchy
description: >-
  Company service documentation hierarchy schema (Layer 1 overview, Layer 2
  architecture/maintenance by topic, Layer 3 history). Read-only reference for
  layout rules, path resolution, and migration completion signals. Use when
  asking what the doc layout is, where a doc type belongs, or whether a repo
  has adopted the hierarchy. Trigger phrases — "doc hierarchy", "documentation
  hierarchy", "service docs hierarchy", "docs layer". For migration execution use doc-hierarchy-migrate; for
  post-migration doc updates use doc-hierarchy-upkeep.
---

# Company Service Documentation Hierarchy (schema)

Team decision: see [company-decisions.md](company-decisions.md) for rationale and participants. Canonical sources: [content-ownership.md](content-ownership.md). Classification: [migration-map.md](migration-map.md). Templates: [instruction-templates.md](instruction-templates.md).

## Skill family (do not combine in one run)

| Skill | Role | Triggers |
|-------|------|----------|
| **doc-hierarchy** (this file) | Schema, precedence, completion signal | "what is the doc layout", "where does X belong" |
| [**doc-hierarchy-migrate**](../doc-hierarchy-migrate/SKILL.md) | Steps 0→6 relocation, scaffold, repair | migrate, reorganize, scaffold, "run doc-hierarchy" |
| [**doc-hierarchy-upkeep**](../doc-hierarchy-upkeep/SKILL.md) | Layer 1/2 updates after code changes | behavior/API/ops doc sync in same PR |

## Scope

- **Applies to:** Company service repositories under `company_projects_root` (load `company_ownership_facts`).
- **Does not apply to:** Personal projects, shared libraries without service `docs/`, or repos the user exempts.

## Precedence and other skills

**Only `doc-hierarchy-migrate` writes** canonical paths into `AGENTS.md` and `project_guidelines_rel` during an explicit migration run.

**All other skills** read path keys from `.ai-playbook/facts.md` (see `using-skills` Step 0). They must **not** hardcode `docs/plans/`, `docs/examples/`, or module-split trees.

| Situation | Behavior |
|-----------|----------|
| User runs **doc-hierarchy-migrate** | Apply three-layer hierarchy; update repo instructions |
| User runs **doc-hierarchy-upkeep** | Update Layer 1/2 only when migration-complete signal is true |
| User runs **another skill** | Read paths from project specs; explore `docs/` if silent |
| Legacy layout on disk | Use what exists; suggest **doc-hierarchy-migrate** — do not silently relocate |
| **`learn` on company service** | After migration-complete: no new `docs/examples/` or `docs/<module>/` trees |

Project `docs/maintenance/project-guidelines.md` may add **repo deltas** but must **not** redefine the three-layer folder schema without a team decision.

## Layers

| Layer | Path | Detail in |
|-------|------|-----------|
| 1 | `docs/README.md` | [company-decisions.md](company-decisions.md) Layer 1 |
| 2 | `docs/architecture/`, `docs/maintenance/` | Target layout below; seven architecture filenames in [migration-map.md](migration-map.md) |
| 3 | `docs/history/` | [company-decisions.md](company-decisions.md) Layer 3 |
| Ephemeral | `docs/tmp/`, `docs/history/reviews/` | [company-decisions.md](company-decisions.md) Ephemeral section |

**Layer 3 layout rules** (forbidden legacy roots, RFC placement, no module-split trees): [migration-map.md](migration-map.md).

## Target layout

```
docs/
├── README.md                   # Layer 1
├── architecture/               # Layer 2 — exactly seven topic files
├── maintenance/                # Layer 2 — guidelines, wire catalogs, optional dashboards/
│   └── dashboards/             # optional Grafana exports (index from operational-guides.md)
├── tmp/                        # Ephemeral (gitignored)
├── history/
│   ├── context/                # Layer 3 — product/domain context (from legacy docs/context/)
│   ├── plans/completed/
│   ├── investigations/         # Layer 3 — other investigation notes (flat files)
│   ├── migrations/
│   ├── reviews/                # Ephemeral (gitignored)
│   └── feature-notes/          # Layer 3 — RFCs, PRDs, gap analyses (flat files)
```

Full filename list and move tables: [migration-map.md](migration-map.md).

## Migration-complete signal

A company service repo is **migration-complete** when **all** are true:

1. `docs/maintenance/project-guidelines.md` exists with a **Documentation Hierarchy** section that records resolved paths (`plans_dir`, `reviews_dir`, etc.) or equivalent literals (`docs/history/plans/`, …).
2. `repo_facts_rel` (`.ai-playbook/facts.md`, gitignored repo agent runtime) exists with a valid opening TOML fence; `AGENTS.md` has H1 `# Instructions` and a **Documentation Hierarchy** subsection pointing at `.ai-playbook/facts.md` and `docs/maintenance/project-guidelines.md`; `.ai-playbook/` is gitignored.
3. From repo root, the **doc-hierarchy-migrate skill** verify script exits 0 on `full` (`step6` is an alias):

   `REPO_ROOT=<repo> <doc-hierarchy-migrate-skill>/scripts/verify-doc-hierarchy.sh full`

   Resolve `<doc-hierarchy-migrate-skill>` from the **doc-hierarchy-migrate** skill install (directory containing `doc-hierarchy-migrate/SKILL.md`), regardless of which doc-hierarchy family skill triggered the check. Not from the service repo. **Do not** copy or vendor the script into the service repo.

Until the signal is true, other skills read `.ai-playbook/facts.md` and may explore legacy paths on disk when keys are missing. After true, project spec wins; `learn` must not create new `docs/examples/` or `docs/<module>/` trees.

## Agent-agnostic instructions

- **Canonical:** repo root `AGENTS.md` (`# Instructions`).
- **Optional adapters:** `CLAUDE.md` → symlink to `AGENTS.md`; Cursor `.cursor/rules/instructions.mdc` → `@AGENTS.md` only.

Templates: [instruction-templates.md](instruction-templates.md).

## Integration Points

| Consumer | Integration |
|----------|-------------|
| `bootstrap-ai-playbook` | Resolution order and default path map; links here for migration-complete signal |
| `doc-hierarchy-migrate` | Applies schema; writes canonical paths into repo instructions |
| `doc-hierarchy-upkeep` | Layer 1/2 updates when migration-complete signal is true |
| `plans`, `execute-plan` | Read `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}` from `.ai-playbook/facts.md` |
| `learn` | Placement rules; no new `docs/examples/` or `docs/<module>/` after migration |
| `done`, `docs-branch` | PR checklist; gitignored doc paths via resolved `{reviews_dir}` |
| `doing-code-review`, `review-plan` | Staging docs under resolved `{reviews_dir}` |
| `github-pr-workflow` | Doc migration PR description rules from `company-decisions.md` |
| `review-confluence-doc` | Reads `{tmp_dir}` from `.ai-playbook/facts.md` for review output files |
| `rfc-design` | Reads caller catalog and `{tmp_dir}` from `.ai-playbook/facts.md` |
| `how-to-write-skills` | Bidirectional Integration Points requirement for skill family consumers |
| `using-skills` | Step 0 reads `.ai-playbook/facts.md`; invokes bootstrap only when Terms triggers fire |

## Related

- [content-ownership.md](content-ownership.md) — which file owns each topic (no duplicate prose)
- the `bootstrap-ai-playbook` skill — writes `.ai-playbook/facts.md`; consumers read TOML keys via `using-skills` Step 0
- [`../doc-hierarchy-migrate/SKILL.md`](../doc-hierarchy-migrate/SKILL.md) — migration workflow
- [`../doc-hierarchy-upkeep/SKILL.md`](../doc-hierarchy-upkeep/SKILL.md) — Layer 1/2 upkeep
- `learn`, `plans`, `execute-plan`, `docs-branch`, `done`
