# Instruction file templates

Copy/adapt when applying the hierarchy to a repo. Replace `{service-name}`. Upkeep rules and PR checklist: [company-decisions.md](company-decisions.md) only — do not duplicate here.

## `docs/maintenance/project-guidelines.md` section

Insert near the top (after Core Concepts if present) in **`docs/maintenance/project-guidelines.md`**:

```markdown
## Documentation Hierarchy

Follow the company service layout under `docs/` (company guideline #48; `doc-hierarchy` schema, `doc-hierarchy-migrate` for relocation). Start at [README.md](../README.md).

    docs/
    ├── README.md                   # Layer 1: service overview (not a file index)
    ├── architecture/               # Layer 2: seven canonical architecture files
    ├── maintenance/                # Layer 2: guidelines, facts, glossary, ADRs, wire catalogs
    ├── tmp/                        # LLM-only session scratch (gitignored where used)
    └── history/                    # Layer 3: context/, plans/completed/, investigations/, feature-notes/
        └── reviews/                # LLM-only gitignored review staging

Canonical architecture filenames (do not rename): `system-overview.md`, `domain-model.md`, `integrations.md`, `api-contracts.md`, `event-flows.md`, `operational-guides.md`, `troubleshooting.md`.

### Resolved documentation paths (mandatory after migration)

Authoritative key definitions and default map: the `resolve-vars` skill (Default Path Map section). Copy that table into the repo so other skills invoke `resolve-vars` at task start.

## Keep Layer 1 and Layer 2 Current (Mandatory)

Apply the maintenance model from `company-decisions.md` (Layer 1 vs Layer 2 triggers, PR checklist). Use `doc-hierarchy-upkeep` when unsure.

**Completion gate:** If an on-call engineer or cold-start agent would be misled, the doc update is part of done for the task.
```

## Repo instruction files (Step 5)

**Canonical (all agents):** `AGENTS.md` at repo root. **H1 title:** `# Instructions` (not `# AGENTS.md`). Codex, Copilot, Claude Code, Cursor, and other agents discover this filename by convention.

**Patch `AGENTS.md` only** — preserve existing engineering rules. Do not replace the full file with templates below.

### Optional tool adapters (when the team uses that tool)

| Tool | Adapter | Rule |
|------|---------|------|
| Claude Code | `ln -sf AGENTS.md CLAUDE.md` | Symlink only; same inode |
| Cursor | `.cursor/rules/instructions.mdc` with `@AGENTS.md` | Thin pointer; often gitignored locally |
| Other | Single pointer file documented in repo `AGENTS.md` | Must not duplicate the full body |

Cursor `instructions.mdc` skeleton:

```markdown
---
description: Repository instructions (AGENTS.md)
alwaysApply: true
---

@AGENTS.md
```

## `docs/architecture/*.md` placeholder skeleton

When scaffolding empty topic files:

```markdown
# <topic-name>

## Core Concepts

- [1–2 bullets or "Placeholder — to be filled from code review"]

## Status

Placeholder — to be filled from code review.

## Pointers

- Code: [module paths]
- Tickets: [Jira keys if known]
```

Record in `AGENTS.md` repo constraints (if not already present):

```markdown
- **Instruction files:** `AGENTS.md` is canonical (`# Instructions`) for all agents. Optional: `CLAUDE.md` → `ln -sf AGENTS.md CLAUDE.md`; Cursor → `.cursor/rules/instructions.mdc` with `@AGENTS.md` only (no full duplicate).
- **Doc hierarchy schema:** company guideline #48 (`company_guidelines_master` in user facts) + `doc-hierarchy-migrate` / `doc-hierarchy-upkeep` skills; record resolved paths here so other skills read project specs (invoke the `resolve-vars` skill at task start).
```

## `AGENTS.md` Documentation Hierarchy subsection

```markdown
## Documentation Hierarchy

- **Start here:** `docs/README.md` (Layer 1 — concise service overview; not a file catalog).
- **Facts / guidelines:** `repo_facts_rel` → `docs/maintenance/facts.md`; `project_guidelines_rel` → `docs/maintenance/project-guidelines.md`.
- **Shared knowledge:** `docs/architecture/`, `docs/maintenance/` (Layer 2) — update in the same PR/session when behavior, contracts, integrations, or ops change; see `docs/maintenance/project-guidelines.md` Documentation Hierarchy section.
- **Historical context:** `docs/history/` (Layer 3) — reference only; active plans under `docs/history/plans/`, archives under `docs/history/plans/completed/`.
- **LLM-only:** `docs/tmp/` at root; gitignored `docs/history/reviews/` — not canonical human Layer 2.
- **Wire catalogs (Layer 2):** `docs/maintenance/api-reference.md` when the service exposes HTTP APIs; other wire contracts under `docs/maintenance/` (BFF, sync, admin FE shapes). Do not recreate a separate examples tree or per-endpoint files under `maintenance/`; use `maintenance/api-reference.md` for caller samples.
- **Doc path resolution:** Other skills resolve `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, `{proposals_dir}`, `{rfcs_dir}`, `{caller_catalog}` from this file and project guidelines — not from hardcoded skill defaults.
- Use `doc-hierarchy-migrate` to relocate flat or module-split docs; use `doc-hierarchy-upkeep` for Layer 1/2 after migration; merge durable knowledge into topic-based `architecture/`, not `docs/<module>/` trees.
```

## Layer 1 `docs/README.md` skeleton

**Purpose:** High-level human onboarding (~few minutes). Per team agreement — service overview, **not** a directory index.

```markdown
# {service-name}

Short service overview for humans. **Start here (Layer 1).** Deeper material lives in Layer 2 (`architecture/`, `maintenance/`); historical context in `history/`.

## What this service does

[2–4 sentences: role in the platform, what problems it solves.]

## Main responsibilities

- [Bullet: primary capability]
- [Bullet: secondary capability]

## Key integrations and dependencies

- [Caller/system + interaction style]
- [Datastore, messaging, external APIs]
- [Platform / Confluence links where useful]

## APIs and events (high level)

- [Category: e.g. external sync or write APIs]
- [Category: e.g. operator/admin reads]
- [Category: e.g. async events or webhooks]

Normative wire contracts: `app/api/openapi.yaml` (or equivalent). Detail: `architecture/integrations.md`, `architecture/api-contracts.md`. Runnable caller samples: `maintenance/api-reference.md` (placeholders only — no live credentials).

## High-level flows

1. [One-line steady-state flow for primary callers.]
2. [One-line operator or admin flow if applicable.]
3. [Optional third flow.]

## Operations

- Local dev and build: `architecture/operational-guides.md` and `maintenance/local-development.md`
- Dashboards / runbooks: [link or “see operational-guides”]

## Where to read next

| Layer | Folder | Use for |
|-------|--------|---------|
| 2 | `architecture/` | Domain, integrations, API policy, event flows, troubleshooting patterns |
| 2 | `maintenance/` | Project guidelines, ADRs, glossary, wire-contract docs, best practices |
| 3 | `history/` | RFCs, plans, investigations (reference only) |

Do **not** duplicate Layer 2 content here. Do **not** list every file under those folders — discover files in the folder when needed.
```

**Forbidden in Layer 1:** per-file tables (`| Document | Purpose |` with links to each `architecture/*.md`); “update this index when docs change” wording; ticket debug playbooks.
