# Company Documentation Decisions (extracted)

Source: internal team decision thread, May 18 - Jun 11, 2026. Participants: tech lead, senior engineer, staff engineer.

## Agreed principles

1. **Separate documentation by audience and purpose** — do not force one document to serve humans, onboarding, and deep AI context equally.
2. **Two doc classes** (tech lead, agreed by staff engineer):
   - Human-readable, high-level, concise.
   - Detailed project-level specs useful during development and for AI guardrails.
3. **Code is primary truth for low-level flow detail** — in-depth per-feature human docs are unnecessary; AI can derive specifics from code when Layer 2 context exists.
4. **Specs and clarifications from feature work are valuable** when they cannot be inferred from code alone — preserve in project, not only in tickets.
5. **Layer 1 lives in the repo** (team preference) so it evolves with PRs; broader team wiki/Confluence may hold even shorter overviews but repo `docs/README.md` is canonical for service-level onboarding.
6. **Same hierarchy applies to new company microservices** and other company service repos adopting the layout (team agreement).

## Three layers

### Layer 1 — Service overview (human-focused)

Per team agreement: a **high-level service overview** — not an in-depth feature catalog and **not a file index**.

**Include (prose and short bullets only):**

- What the service does
- Main responsibilities
- Key integrations / dependencies
- APIs / events exposed (categories, not every operation)
- High-level flows
- Links to dashboards / runbooks (or pointers to Layer 2 ops docs)

**Do not include:**

- Per-file tables of `architecture/` or `maintenance/` contents
- A catalog that must be updated whenever a new doc file is added
- Ticket-specific debugging detail (Layer 3)
- Duplicating Layer 2 depth (module internals, normalization rules, error matrices)

- **Concise** — a few minutes to read.
- **Living documentation** — update when **service scope** changes (role, integrations, exposed APIs, high-level flows), not when Layer 2/3 files are added or renamed.
- Location: `docs/README.md` only at `docs/` root.

**Where to find detail:** Point to stable folders (`architecture/`, `maintenance/`, `history/`) — agents and humans discover specific files there; README does not list them.

### Layer 2 — Architecture and domain knowledge (shared human + AI)

- Important business flows, architectural decisions, domain concepts, cross-service interactions, operational/troubleshooting knowledge.
- Changes less frequently than code but must stay current when behavior/contracts change.
- Locations:
  - `docs/architecture/` — seven canonical files (see [SKILL.md](SKILL.md) target layout).
  - `docs/maintenance/` — runbooks, optional Grafana dashboard exports under `docs/maintenance/dashboards/` (index from `architecture/operational-guides.md`), `project-guidelines.md`, `facts.md`, `company-guidelines.md` mirror, human best practices, wire catalogs (`api-reference.md`, BFF/sync contracts). No `docs/examples/` tree (caller catalog lives in `maintenance/api-reference.md`).

### Ephemeral / tooling (not layers)

Gitignored or optional paths documented in the schema skill — not onboarding material:

- `docs/tmp/` — LLM session scratch (gitignored)
- `docs/history/reviews/` — LLM review/plan staging (gitignored)

### Layer 3 — Historical / AI context

- Research notes, investigation results, feature plans, migration notes, historical implementation details.
- Valuable references; **not** onboarding or primary documentation.
- **No ongoing maintenance** beyond the context in which created.
- **Do not** name a subfolder `ai-generated` (tech lead — misleading).
- Suggested subfolders: `context/` (product/domain context from legacy `docs/context/` — **not** nested under `investigations/`), `plans/` (including `plans/completed/`), `investigations/` (flat investigation notes only), `migrations/` (service/data migration notes only — not doc-hierarchy move logs), `feature-notes/` (flat RFCs, PRDs, and feature design notes — **not** a separate `docs/rfcs/` root after migration).
- **LLM-only (not Layer 3 reference material):** gitignored `history/reviews/` for plan/PR/code-review staging.
- **Not** in `history/`: `doc-migration.md` or other meta “how we reorganized docs” files — use git history instead.
- Location: `docs/history/`.

## Maintenance model

| Layer | Who maintains | When |
|-------|---------------|------|
| Layer 1 | Developers | Normal feature development; same PR/session when **service scope** changes (role, integrations, exposed APIs/events, high-level flows) — not when Layer 2/3 files are added or renamed |
| Layer 2 | Developers | Same PR/session when behavior, contracts, integrations, ops, or troubleshooting change |
| Layer 3 | Author at creation | No standing upkeep |

## PR checklist (team proposal, accepted)

```markdown
Documentation impact

[ ] No documentation changes required
OR
[ ] README updated (Layer 1 — only if service overview scope changed)
[ ] Architecture/maintenance docs updated (Layer 2)
[ ] Historical docs added/updated (Layer 3)
```

## PR description rules

Applies to **doc-hierarchy-migrate** completion and doc-only PRs.

1. **Documentation impact** — use the checklist above only. Do not expand it into a layout inventory or move table unless the reviewer explicitly asks.
2. **No duplicate verify TODOs** — if the implementing session already ran `<doc-hierarchy-migrate-skill>/scripts/verify-doc-hierarchy.sh` (`step6` or `full`) with exit 0, do not add a PR **Test plan** item for that gate as an unchecked reviewer task.
3. **Verify script is not a repo artifact** — the script lives in the skill install only; service repos must not contain `scripts/verify-doc-hierarchy.sh`. Never phrase PR text as if reviewers run a repo-local copy.
4. **Optional Test plan** — the documentation impact checklist is sufficient for doc migration PRs. If you add a Test plan, mark session-verified checks `[x]` or omit them; do not leave implementer work as unchecked reviewer homework.

## Legacy service documentation (question 1 from tech lead)

Keep as-is when still useful:

- AI instructions/guidelines.
- Grafana dashboard templates.
- Historical feature notes (e.g. metrics use cases).
- Other docs valuable without restructuring.

Migrate or archive the rest per layer rules.

## Rejected or deferred ideas

- `docs/rfcs/` as a separate active-RFC root — superseded; RFCs belong in `history/feature-notes/` flat (same Layer 3 treatment as PRDs and plans under `history/plans/`).
- `docs/human/` or `docs/readme/` as separate human-only tree — superseded by Layer 1 `README.md` + Layer 2 split.
- Confluence-only Layer 1 — repo preferred for co-evolution with code.
- Single always-up-to-date doc for both humans and AI — acknowledged as impractical.
- Ticket-specific debugging docs as long-term onboarding material — deprioritized.

## Instruction enforcement

- Encode Layer 1/2 update rules in `docs/maintenance/project-guidelines.md` and `AGENTS.md`.
- Use **`doc-hierarchy-migrate`** to migrate repos and scaffold missing files; **`doc-hierarchy-upkeep`** for Layer 1/2 after migration; **`doc-hierarchy`** for schema reference.
- Company guideline #48 mirrors the cross-repo rule (`company_guidelines_master` in user facts).
