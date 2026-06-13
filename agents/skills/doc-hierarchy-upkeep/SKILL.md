---
name: doc-hierarchy-upkeep
description: >-
  Keep Layer 1 and Layer 2 documentation current after behavior, contract,
  integration, or ops changes on a migration-complete company service repo.
  Use in the same PR/session as code changes — not for full doc migration.
  Trigger phrases — "update service docs", "sync architecture docs",
  "documentation impact", "keep layer 2 current". Requires
  doc-hierarchy migration-complete signal; otherwise use doc-hierarchy-migrate.
---

# Doc Hierarchy Upkeep (Layer 1 and Layer 2)

Schema: [`../doc-hierarchy/SKILL.md`](../doc-hierarchy/SKILL.md). Full migration: [`../doc-hierarchy-migrate/SKILL.md`](../doc-hierarchy-migrate/SKILL.md). **When-to-update table and PR checklist:** [`../doc-hierarchy/company-decisions.md`](../doc-hierarchy/company-decisions.md) (Maintenance model + PR checklist sections).

## Hard gate

**Do not run upkeep** until the repo satisfies the [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal).

If the signal is false, stop and run **doc-hierarchy-migrate** (or repair via `REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" audit` after resolving `SKILL_INSTALL` per `doc-hierarchy-migrate`).

## Workflow

1. Confirm migration-complete signal.
2. Read [company-decisions.md Maintenance model](../doc-hierarchy/company-decisions.md#maintenance-model) — apply Layer 1 vs Layer 2 triggers.
3. Identify affected Layer 2 files (contracts → `api-contracts.md` + `maintenance/api-reference.md`; domain → `domain-model.md`; etc.).
4. Edit Layer 2 in the same change set as code. Link instead of duplicating across files.
5. Update `docs/README.md` only when Layer 1 triggers apply (see maintenance model).
6. Do not create `docs/<module>/`, `docs/examples/`, or root-level guideline files.
7. Copy [PR checklist](../doc-hierarchy/company-decisions.md#pr-checklist-team-proposal-accepted) into the PR when docs changed; follow [PR description rules](../doc-hierarchy/company-decisions.md#pr-description-rules).
8. Grafana dashboard exports belong under `docs/maintenance/dashboards/` (indexed from `architecture/operational-guides.md`) — not `docs/dashboards/` at repo root.

## Repo agent facts and Jira ledger

Update **`.ai-playbook/facts.md`** (not committed `docs/maintenance/facts.md`) when repo-scoping FACT stubs or Jira ledger entries change:

1. **Re-read-before-write:** Re-read `.ai-playbook/facts.md` immediately before editing; parse only the **opening** fenced TOML block; preserve all prose below the fence unchanged.
2. **Human-canonical claims:** When a FACT carries durable claims for human PR review, update the matching Layer 2 `docs/architecture/*.md` topic in the same change set; keep only index stubs or ticket ledger lines in `.ai-playbook/facts.md`.
3. **Jira ledger:** Add or update entries under `## Related Jira tasks` in prose; do not cite `.ai-playbook/facts.md` from RFCs, PR descriptions, or code comments — restate ticket IDs inline in human-facing docs.
4. **Concurrent edits:** If another session may edit facts, re-read immediately before persist (same as bootstrap refresh).

## Anti-patterns

- Using upkeep to relocate files → **doc-hierarchy-migrate**
- Putting operational truth in `docs/history/`
- README file-catalog updates on every new architecture file
- Legacy root paths (`docs/dashboards/`, `docs/rfcs/`, `docs/examples/`, module-split trees) — see [migration-map.md](../doc-hierarchy/migration-map.md)
- In canonical Layer 2 roots (`docs/architecture/`, `docs/maintenance/`, `AGENTS.md`), deep-linking nested Layer 3 paths under `feature-notes/` (except allowed `proposals/`) — use folder-level `docs/history/feature-notes` instead; step6 flags `docs/history/feature-notes/<subdir>/` for subdirs other than `proposals/`
- On the same line, a trailing-slash folder ref (`docs/history/feature-notes/`) followed by another `` `docs/...` `` path or prose containing `/` (for example `Project/Subproject`) can false-match the step6 regex — split sentences or drop the trailing slash on folder refs

## Verification

- **Any edit** to `AGENTS.md`, `docs/README.md`, `docs/architecture/`, or `docs/maintenance/` (including routine Layer 2 paragraph or contract updates): run `full` (alias `step6`) before commit — catches step6 reference hygiene and layout gates.
- **`step5` only** when checking instruction wiring mid-session without canonical doc edits; it does not run step6 reference scans and is not sufficient alone before commit after upkeep edits.

`REPO_ROOT=<service-repo> "$SKILL_INSTALL/scripts/verify-doc-hierarchy.sh" <phase>`. Fix violations before committing.

## Integration Points

| Consumer / provider | Integration |
|---------------------|-------------|
| `doc-hierarchy` | Requires migration-complete signal before upkeep runs |
| `doc-hierarchy-migrate` | Provides verify script and repair workflow when signal is false |
| `bootstrap-ai-playbook` | Writes `.ai-playbook/facts.md`; upkeep and consumers read path keys from that file |
| `learn`, `plans`, `done`, `execute-plan` | Layer 2 edits in same PR/session as code changes |

## Related

- [`doc-hierarchy`](../doc-hierarchy/SKILL.md), [`doc-hierarchy-migrate`](../doc-hierarchy-migrate/SKILL.md)
- the `bootstrap-ai-playbook` skill, `learn`, `plans`, `done`
