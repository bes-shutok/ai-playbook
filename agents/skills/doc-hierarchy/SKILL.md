---
name: doc-hierarchy
description: >-
  Company service documentation hierarchy schema (Layer 1 overview, Layer 2
  architecture/maintenance by topic, Layer 3 history). Read-only reference for
  layout rules, path resolution, and migration completion signals. Use when
  asking what the doc layout is, where a doc type belongs, or whether a repo
  has adopted the hierarchy. Trigger phrases: "doc hierarchy", "documentation
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
| Legacy layout on disk | Use what exists; suggest **doc-hierarchy-migrate**; do not silently relocate |
| **`learn` on company service** | After migration-complete: no new `docs/examples/` or `docs/<module>/` trees |

Project `docs/maintenance/project-guidelines.md` may add **repo deltas** but must **not** redefine the three-layer folder schema without a team decision.

## Layers

| Layer | Path | Detail in |
|-------|------|-----------|
| 1 | `docs/README.md` | [company-decisions.md](company-decisions.md) Layer 1 |
| 2 | `docs/architecture/`, `docs/maintenance/` | Target layout below; seven architecture filenames in [migration-map.md](migration-map.md) |
| 3 | `docs/history/` | [company-decisions.md](company-decisions.md) Layer 3 |
| Ephemeral | `docs/tmp/` (documents only: `.md`/`.patch`), root `tmp/` (throwaway scripts + scratch data: `.py`/`.csv`/`__pycache__/`), `docs/history/reviews/` | [company-decisions.md](company-decisions.md) Ephemeral section |

**Layer 3 layout rules** (forbidden legacy roots, RFC placement, no module-split trees): [migration-map.md](migration-map.md).

## Target layout

```
docs/
├── README.md                   # Layer 1
├── architecture/               # Layer 2; exactly seven topic files
├── maintenance/                # Layer 2; guidelines, wire catalogs, optional dashboards/
│   └── dashboards/             # optional Grafana exports (index from operational-guides.md)
├── tmp/                        # Ephemeral documents only (gitignored): .md logs, .patch snapshots
├── history/                    # Layer 3 high-level tree (required)
│   ├── context/                # optional product/domain context (from legacy docs/context/)
│   ├── plans/completed/        # optional plans archive (executed plans, body-immutable)
│   ├── plans/deferred/         # optional parked plans (same convention as backlog/deferred/)
│   ├── backlog/                # durable pre-plan backlog items (YYYY-MM-DD-<slug>.md); promote via plans
│   │   ├── deferred/           # parked items (triage deferral); byte-intact content, revive deliberately
│   │   └── completed/          # archived when the implementing plan completes
│   ├── investigations/         # optional investigation notes (flat files)
│   ├── migrations/             # optional service/data migration notes
│   ├── reviews/                # optional ephemeral, gitignored staging
│   └── feature-notes/          # optional RFCs, PRDs, gap analyses; flat files plus samples/ assets
```

**Scripts vs documents split:** `docs/tmp/` is for **documents** only (`.md` logs, `.patch` diff snapshots - synced to the orphan `docs` branch). Throwaway **scripts and scratch data** (`.py` shadow/verification scripts, `.csv`/`.txt` baseline counts, `__pycache__/`) go in repo-root `tmp/` (gitignored, NOT synced to the `docs` branch). See `agent_workflow_guidelines.md` §50.3.1.

**Backlog (`history/backlog/`):** durable pre-plan work items; valid review findings deferred out of scope are captured here per `receiving-review` **Backlog capture**, one `YYYY-MM-DD-<slug>.md` per item with `Status` / `Workflow: backlog` header lines so `plans`-skill promotion applies. `Status: open` while unpromoted; the implementing plan's completion pass sets `Status: done` in the same edit that moves the item to `backlog/completed/`. Promotion to `{plans_dir}` and archival to `backlog/completed/` follow the `plans` skill. `backlog/deferred/` holds items parked by a prioritization triage (for example the 2026-09-11 efficiency/token/simplicity pass): each carries a `Priority: deferred` header line stating the triage and its revival condition, the body stays byte-intact, and revival means moving the file back to `backlog/` root before promotion — never promote or execute directly from `deferred/`. `docs/maintenance/` (Layer 2 living ops) and `docs/tmp/` (ephemeral) are never backlog destinations; when `{backlog_dir}` is unresolved, `bootstrap-ai-playbook` resolves or creates the home, else ask the user.

Full filename list and move tables: [migration-map.md](migration-map.md).

## Migration-complete signal

A company service repo is **migration-complete** when **all** are true:

1. `docs/maintenance/project-guidelines.md` exists with a **Documentation Hierarchy** section that records resolved paths (`plans_dir`, `reviews_dir`, etc.) or equivalent literals (`docs/history/plans/`, …).
2. `repo_facts_rel` (`.ai-playbook/facts.md`, gitignored repo agent runtime) exists with a valid opening TOML fence; `AGENTS.md` has H1 `# Instructions` and a **Documentation Hierarchy** subsection pointing at `.ai-playbook/facts.md` and `docs/maintenance/project-guidelines.md`; `.ai-playbook/` is gitignored.
3. From repo root, the **doc-hierarchy-migrate skill** verify script exits 0 on `full` (`step6` is an alias):

   `REPO_ROOT=<repo> <doc-hierarchy-migrate-skill>/scripts/verify-doc-hierarchy.sh full`

   Resolve `<doc-hierarchy-migrate-skill>` from the **doc-hierarchy-migrate** skill install (directory containing `doc-hierarchy-migrate/SKILL.md`), regardless of which doc-hierarchy family skill triggered the check. Not from the service repo. **Do not** copy or vendor the script into the service repo.

Until the signal is true, other skills read `.ai-playbook/facts.md` and may explore legacy paths on disk when keys are missing. After true, project spec wins; `learn` must not create new `docs/examples/` or `docs/<module>/` trees.

## Document states

Every document is in exactly one of two states:

- **Living SOT**: the one document (or wire/schema source) that owns the current normative rule for an idea; editable while its work is active.
- **Completed history artifact**: a completed plan, investigation, proposal, RFC, or non-mirror context file recording what was known or decided at a point in time; immutable after its freeze transition.

**Freeze transition**: the explicit lifecycle action that closes a document: archive move (where applicable), registry row with date and reason, no body edits. Freeze is always **agent-prompted and user-confirmed**; never inferred from file age, last-touch time, or staleness heuristics. Superseded documents are archived, not deleted. Definitions live in `docs/maintenance/glossary.md`; binding decision in ADR-0003 (`docs/maintenance/project-decisions.md`).

**Ownership registry**: one Layer 2 Markdown table, one row per **document identity** (stable kebab-case concept identifier, independent of ticket, branch, or path). Registry location comes from the `doc_registry_rel` facts key (default `docs/maintenance/document-registry.md`). Row shape, matching `scripts/doc_registry_validator.py`:

| Column | Meaning |
|--------|---------|
| `identity` | stable kebab-case concept identifier (required) |
| `sot` | `yes` when this row declares living-SOT ownership, else `no` |
| `state` | `living` / `completed` / `superseded` (required) |
| `archived` | freeze date `YYYY-MM-DD`; empty for living rows |
| `reason` | why the freeze happened (free text) |
| `src` | repo-relative path of the registered artifact |
| `successor` | identity of the superseding document (`superseded_by`); for an accepted RFC freeze it carries the accepting document identity instead (accepted-SOT relation, per `rfc-design` Step 4) |
| `aliases` | comma-separated repo-relative paths that historically pointed at this identity |
| `audit` | optional free-text note; non-empty on a completed-history row is the explicit override licensing an otherwise immutable write. The note must begin with the dated confirmation token `user-approved YYYY-MM-DD:` (what the user confirmed) with a real, non-future calendar date (one-day clock skew tolerated); both `validate` and `check-writes` hard-fail a malformed or ill-dated note, and a self-minted note licenses nothing |

**Corruption override (ADR-0001):** the `audit` note is the sole override licensing an edit to a frozen body, and only after explicit user confirmation of a minimal edit (just the corrupt content); the note begins with the dated confirmation token `user-approved YYYY-MM-DD:` and records what changed and why, and is removed after the licensed write lands so the guard does not stay disarmed. **Identity derivation** for backfilled rows and RFC closure (the live default until RFC creation emits the identity in the Header, per `rfc-design` Step 4 and the backlog item `docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring.md`): filename minus the leading `YYYY-MM-DD-` date prefix and `.md` extension, kebab-case; collision handling is documented in the registry file's comment header.

The **registry validator** (`scripts/doc_registry_validator.py`) validates registry integrity, gates writes to immutable completed-history paths (`check-writes`), and inventories completed-history files lacking a registry row. It reports; it never auto-reclassifies. The registered-src exemption in `check-writes` is bounded to the transition, not the artifact's life: the `src` of a `completed`/`superseded` row is a licensed lifecycle write only when the change type is an add or rename (`A`/`R`, the one-time freeze move); the same src written with a modify/delete change type, and every write without an `audit`-noted override otherwise, stays a hard gate failure.

**Scope:** company service repos bind this lifecycle via the **migration-complete signal** above (schema binding); this instructions repo adopts it **by convention** for its own `docs/` tree without the signal (ADR-0003). The validator works on any repo with resolved facts paths.

## Agent-agnostic instructions

- **Canonical:** repo root `AGENTS.md` (`# Instructions`).
- **Optional adapters:** `CLAUDE.md` → symlink to `AGENTS.md`; Cursor `.cursor/rules/instructions.mdc` → `@AGENTS.md` only.

Templates: [instruction-templates.md](instruction-templates.md).

## Integration Points

| Consumer | Integration |
|----------|-------------|
| `bootstrap-ai-playbook` | Resolution order and default path map; links here for migration-complete signal; creates `history/backlog/` under an existing Layer 3 root for `{backlog_dir}` |
| `doc-hierarchy-migrate` | Applies schema; writes canonical paths into repo instructions |
| `doc-hierarchy-upkeep` | Layer 1/2 updates when migration-complete signal is true |
| `plans`, `execute-plan` | Read `{plans_dir}`, `{backlog_dir}`, `{backlog_completed_dir}`, `{reviews_dir}`, `{tmp_dir}` from `.ai-playbook/facts.md`; `plans` completion transition writes the registry row (freeze) for the completed plan and promoted backlog items |
| `receiving-review` | Backlog capture writes pre-plan items under `{backlog_dir}` (`history/backlog/`); promotion and archival follow `plans` |
| `learn` | Placement rules; no new `docs/examples/` or `docs/<module>/` after migration |
| `done`, `docs-branch` | PR checklist; gitignored doc paths via resolved `{reviews_dir}`; `done` Step 2.648 runs the registry validator (`validate` plus `check-writes`) |
| `doing-code-review`, `review-plan` | Staging docs under resolved `{reviews_dir}` |
| `github-pr-workflow` | Doc migration PR description rules from `company-decisions.md` |
| `review-confluence-doc` | Reads `{reviews_dir}` (and `{tmp_dir}` for scratch only) from `.ai-playbook/facts.md`; review staging under `{reviews_dir}/` per `review-staging` |
| `rfc-design` | Reads `{reviews_dir}`, `{rfcs_dir}`, `{proposals_dir}`, `{tmp_dir}` from `.ai-playbook/facts.md`; saves RFCs under `{rfcs_dir}` (Layer 3 `history/feature-notes/`); review staging under `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` (never `{tmp_dir}/rfc-review/`); closure transition applies the freeze (registry row with date, reason, successor) instead of body edits |
| `tdd-design` | Reads `{rfcs_dir}`, `{proposals_dir}` from `.ai-playbook/facts.md`; finished TDDs are Layer 3 history files under `{rfcs_dir}` like `rfc-design`; drafts under `{proposals_dir}` when present |
| `confluence-page-sync` | Reads `{tmp_dir}` (page-fetch and HTML scratch) from `.ai-playbook/facts.md`; writes the sync manifest under `docs/maintenance/`; writes or refreshes page mirrors under `docs/history/context/confluence/` and the README page-id index for the pages it publishes (Step 4) per `confluence-mirror-hygiene.sh` |
| `how-to-write-skills` | Bidirectional Integration Points requirement for skill family consumers |
| `using-skills` | Step 0 reads `.ai-playbook/facts.md`; invokes bootstrap only when Terms triggers fire |

## Related

- [content-ownership.md](content-ownership.md); which file owns each topic (no duplicate prose)
- the `bootstrap-ai-playbook` skill; writes `.ai-playbook/facts.md`; consumers read TOML keys via `using-skills` Step 0
- [`../doc-hierarchy-migrate/SKILL.md`](../doc-hierarchy-migrate/SKILL.md); migration workflow
- [`../doc-hierarchy-upkeep/SKILL.md`](../doc-hierarchy-upkeep/SKILL.md); Layer 1/2 upkeep
- `learn`, `plans`, `execute-plan`, `docs-branch`, `done`
