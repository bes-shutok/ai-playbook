# Documentation classification map

Canonical classification and move tables — see [content-ownership.md](content-ownership.md). Use in **Step 0** of [`doc-hierarchy-migrate`](../doc-hierarchy-migrate/SKILL.md).

**Execution:** Relocations happen in **Step 2** only — not as ad-hoc fixes. See migrate SKILL *Execution contract*.

## Step 0 — classification outcomes

Assign each inventoried path exactly one outcome:

| Outcome | Meaning |
|---------|---------|
| **MERGE → architecture** | Durable knowledge → matching `architecture/*.md` topic |
| **MOVE → maintenance** | Wire contracts, guidelines, caller catalog |
| **MOVE → history** | RFCs, trackers, plans, proposals, investigations |
| **KEEP root** | `README.md` only |
| **DELETE** | Stubs/duplicates after merge |

**Do not** leave durable design in `history/feature-notes/` when it belongs in Layer 2.

## Step 2 — special cases (target repo only)

### Gitignored `reviews/` sync

1. `mkdir -p docs/history` only — do not pre-create `docs/history/reviews` before legacy move.
2. If `docs/reviews/` exists: `git ls-files docs/reviews/` — ask user before relocating tracked review content.
3. Move: if no `docs/history/reviews`, `mv docs/reviews docs/history/reviews`; else merge into existing dir.
4. Greenfield: `mkdir -p docs/history/reviews`.
5. Update `.gitignore` for `docs/history/reviews/` and `docs/tmp/`.

`docs-branch` updates are ai-playbook maintenance — not per-repo Step 2.

### Legacy `docs/rfcs/`

If `docs/rfcs/` exists at repo root, move every `*.md` file flat into `docs/history/feature-notes/` (`git mv docs/rfcs/*.md docs/history/feature-notes/`). Remove the empty `docs/rfcs/` directory. RFCs are Layer 3 reference material — not a post-migration top-level folder (same treatment as `docs/plans/` → `history/plans/`).

### Rogue `examples/`

No `examples/` folder in target schema. Classify per file; never bulk `git mv` the directory. Redact credentials before merge to `maintenance/api-reference.md`. See table below.

## Layer 2 — merge into architecture (topic-based)

| Source content | Target file | Notes |
|----------------|-------------|-------|
| Module README, dedicated-service rationale | `system-overview.md` | Include module table + platform boundaries |
| Bounded-context / module boundary doc | `system-overview.md` | Ownership + read vs write semantics |
| Domain service deep-dives | `domain-model.md` | Workflows, normalization, entities, invariants |
| Glossary identifier tables (summary) | `domain-model.md` | Full vocabulary file → `maintenance/glossary.md` |
| Integration/sync overview (not full wire spec) | `integrations.md` | Full wire contract → `maintenance/<contract>.md` |
| OpenAPI policy, properties patch, error rules | `api-contracts.md` | Wire samples → `maintenance/api-reference.md` (policy here; living samples in maintenance) |
| Migration/sync/event strategies | `event-flows.md` | Include decision/async flow diagrams |
| Metrics/alerts index, local dev summary | `operational-guides.md` | Detail → `maintenance/local-development.md` |
| Incident patterns | `troubleshooting.md` | Scaffold OK if no patterns yet |

## Layer 2 — maintenance (move whole file)

| Source | Target |
|--------|--------|
| `project-guidelines.md` | `maintenance/project-guidelines.md` |
| `project-decisions.md` | `maintenance/project-decisions.md` |
| `glossary.md` | `maintenance/glossary.md` |
| `facts.md` | `maintenance/facts.md` |
| `company-guidelines.md` | `maintenance/company-guidelines.md` |
| Root wire-contract markdown (`api-for-*.md`, `*-sync*.md`, BFF/admin FE docs) | `maintenance/<kebab-name>.md` |
| `examples/api-reference.md` (rogue `docs/examples/` or `docs/history/examples/`) | `maintenance/api-reference.md` — HTTP caller catalog when present; redact live credentials before commit |
| `BEST_PRACTICES.md` | `maintenance/best-practices.md` |
| `LOCAL_DEVELOPMENT.md` | `maintenance/local-development.md` |
| Per-feature config/runbooks | `maintenance/<topic>.md` |
| `docs/dashboards/` (legacy root) | `maintenance/dashboards/` — optional Grafana exports; index from `architecture/operational-guides.md` |

After move, fix internal links in relocated files (`../README.md` for Layer 1, `../architecture/` for topics).

## Layer 3 — history (move, do not merge into Layer 2)

| Source | Target |
|--------|--------|
| `*_rfc.md` (service-prefixed) | `history/feature-notes/` (flat) |
| `docs/rfcs/` (legacy root directory) | `history/feature-notes/` (flat files; remove empty dir) |
| `*-service-high-level-tasks.md` | `history/feature-notes/` (flat) |
| Progress trackers | `history/feature-notes/` (flat) |
| `docs/plans/` | `history/plans/` |
| `docs/proposals/` | `history/feature-notes/proposals/` |
| `docs/context/` | `history/context/` — product/domain context materials (not under `investigations/`) |
| `history/investigations/context/` (legacy bad path) | `history/context/` — repair: move up one level |
| Wrong-repo or superseded investigation notes | `history/investigations/` (flat files only, no `context/` subdir) |
| Service/data migration notes (domain content) | `history/migrations/` if the repo already has them |
| Doc-hierarchy move logs, `doc-migration.md` | **Do not create** — git history on the migration branch is sufficient |
| `docs/reviews/` (entire directory) | `history/reviews/` — **gitignored** (see Step 2 special cases above) |

| Source | Action |
|--------|--------|
| `examples/api-reference.md` | **MOVE** → `maintenance/api-reference.md` |
| `examples/*.md` (other than catalog + index) | **MERGE** into `api-reference.md` or matching architecture topic; then **DELETE** source |
| `examples/README.md` (index stub) | **DELETE** after merging pointers into `api-contracts.md` + `api-reference.md` intro |
| `docs/examples/` or `docs/history/examples/` (empty after above) | **Remove** directory — never bulk `git mv` the folder |

After `examples/` disposition: fix path references in Step 6 (`verify-doc-hierarchy.sh full`). Document resolved paths in Step 5.

## Keep at docs root

- `README.md` — Layer 1 only
- `tmp/` — LLM-only session scratch (gitignored where applicable)
- Grafana dashboard exports live under `maintenance/dashboards/` — not at `docs/` root

**Not** at `docs/` root after migration: `rfcs/`, `plans/`, `dashboards/`, `examples/`, or other legacy typed folders — those belong under `history/` or `maintenance/` per the tables above.

## Agent facts paths (after migration)

| Facts key | Path |
|-----------|------|
| `repo_facts_rel` | `docs/maintenance/facts.md` |
| `project_guidelines_rel` | `docs/maintenance/project-guidelines.md` |
| `company_guidelines_repo_mirror_rel` | `docs/maintenance/company-guidelines.md` (when mirror exists) |

Update `user_facts_path` (resolve path from the `user_facts_path` key) when adopting hierarchy in a repo; document in repo `AGENTS.md`. Do not copy machine-specific paths from user facts into repo `docs/maintenance/facts.md`.

## Module-split `docs/<module>/` trees (any service)

| Old path | Action |
|----------|--------|
| `docs/<module>/*` durable design | **MERGE** into architecture topics; **DELETE** source tree |
| `docs/<module>/*` RFC | **MOVE** → `history/feature-notes/{SERVICE}_rfc.md` or `{module}-rfc.md` (flat) |
| `docs/<module>/*` task tracker | **MOVE** → `history/feature-notes/{module}-service-high-level-tasks.md` (flat) |
| `history/feature-notes/<module>/` nested dirs | **Flatten** to flat `feature-notes/` files |

Record each `<module>` name in the Step 0 classification table. Code modules (`src/`, Maven modules) are unrelated; only **documentation** trees under `docs/<name>/` are in scope.

## Delete after migration

- `docs/` tree stub `README.md` index files (not Java/module `README.md` in source trees), stub redirects, merged architecture duplicates, merged source files.

## Verify (Step 6)

Canonical gates: [`doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh`](../doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh) — run from the skill install with `REPO_ROOT` set to the service repo; **do not** copy into the service repo. Run `full` after every migration or repair.
