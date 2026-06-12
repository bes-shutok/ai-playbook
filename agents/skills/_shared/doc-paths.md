# Documentation path resolution (shared)

Skills that read or write repo documentation **must not hardcode** `docs/plans/`, `docs/reviews/`, `docs/examples/`, or other layout paths. Resolve paths from **project specs and on-disk layout** at task start, then use the resolved values for the rest of the session.

**Exception:** The **`doc-hierarchy`** skill family defines the company three-layer schema. **`doc-hierarchy-migrate`** applies it when the user explicitly runs a migration or scaffold and writes canonical paths into the repo (`AGENTS.md`, `project_guidelines_rel`). **`doc-hierarchy`** (schema) and **`doc-hierarchy-upkeep`** do not relocate files. Other skills **read** paths; they do not enforce the schema themselves.

## Resolution order (mandatory before writing docs)

1. **`user_facts_path`** — `project_guidelines_rel`, `repo_facts_rel` keys (paths relative to repo root).
2. **Repo `AGENTS.md`** — `Documentation Hierarchy` subsection (if present).
3. **`project_guidelines_rel`** — Documentation Hierarchy section, plan/review/tmp path notes, caller-catalog rules.
4. **On-disk exploration** — Glob/list under `docs/` for existing `plans/`, `completed/`, `reviews/`, `tmp/`, `proposals/`, wire-catalog markdown.
5. **`doc-hierarchy` migration-complete signal** — when steps 1–4 are silent and the repo is **company-scoped** (under `company_projects_root` per `company_ownership_facts` or user confirmation), apply the [default path map](#default-path-map-post-migration) only when the full [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal) is true: project-guidelines wiring, `AGENTS.md` hierarchy subsection, **and** `<doc-hierarchy-migrate-skill>/scripts/verify-doc-hierarchy.sh full` exit 0 in the current session. Do not apply company default paths to personal projects. Do not infer adoption from folder presence alone.

**Partial migration:** When `docs/maintenance/` and/or `docs/architecture/` exist but the migration-complete signal is false (verify `audit` or `full` would fail, or `AGENTS.md` wiring is incomplete), do **not** use the default path map. Continue exploration with legacy paths allowed; suggest `doc-hierarchy-migrate` repair.

**Partial adoption:** When `docs/maintenance/` exists but `docs/architecture/` is incomplete, infer maintenance-relative paths (`docs/history/plans/`, `docs/history/reviews/`, `docs/tmp/`, `docs/maintenance/api-reference.md`) and flag repair via `doc-hierarchy-migrate`. Do not treat this as migration-complete.

**Migration-complete signal:** Canonical definition in [doc-hierarchy/SKILL.md § Migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal). When true, treat layout as migrated and use project-spec paths. Until then, exploration may use legacy paths; on company services `learn` must not create new `docs/examples/` or `docs/<module>/` trees.

**Stale facts:** When `project_guidelines_rel` from user facts points at a path that does not exist on disk, probe `docs/maintenance/project-guidelines.md` then legacy `docs/project-guidelines.md` before failing. Prefer on-disk paths declared in repo `AGENTS.md` over stale facts keys.

If multiple candidates remain, prefer the path **documented in project guidelines**; otherwise ask the user. Do not invent a new top-level `docs/` folder without confirmation.

## Typical resolved keys (session variables)

Record these once per session (names are illustrative; skills may use equivalent wording):

| Key | Purpose | Discovery hints |
|-----|---------|-----------------|
| `plans_dir` | Active implementation plans | `docs/history/plans/`, `docs/plans/` |
| `plans_completed_dir` | Archived plans | `{plans_dir}/completed/` |
| `reviews_dir` | Review staging (often gitignored) | `docs/history/reviews/`, `docs/reviews/` |
| `tmp_dir` | Session / execute-plan scratch | `docs/tmp/` |
| `proposals_dir` | Pre-canonical RFC drafts | `docs/history/feature-notes/proposals/`, `docs/proposals/` |
| `rfcs_dir` | Design RFCs (Layer 3) | `docs/history/feature-notes/` (flat); legacy `docs/rfcs/` → migrate, do not create |
| `caller_catalog` | HTTP/integration samples (if any) | Path named in project-guidelines (e.g. `docs/maintenance/api-reference.md`) |
| `guidelines_path` | Project guidelines file | `project_guidelines_rel` fact |
| `facts_path` | Repo facts file | `repo_facts_rel` fact |

## Exploration commands (read-only)

```bash
# List top-level docs layout
ls -la docs/ 2>/dev/null
# Find plan and review roots
find docs -type d \( -name plans -o -name reviews -o -name completed \) 2>/dev/null | head -20
# Gitignored review dir check
git check-ignore -v docs/history/reviews docs/reviews 2>/dev/null || true
```

## Skill behavior rules

- **Write:** Use resolved paths only. Never override tool-default plan locations (`.cursor/plans/`, etc.) with a hardcoded skill path; use `{plans_dir}/<name>.md` from resolution. Before writing to `{reviews_dir}` or `{caller_catalog}`, confirm `git check-ignore` for reviews/tmp paths; caller-catalog content must use credential placeholders only.
- **Read:** Search resolved dirs first; broaden to `docs/**` only when the spec does not pin a location.
- **Create:** If no home exists, follow project-guidelines if documented; else propose a path to the user before creating new top-level `docs/` trees.
- **Company services:** After `doc-hierarchy-migrate` completes, paths live in `project_guidelines_rel` — do not fall back to legacy `docs/examples/` or flat `docs/plans/` unless exploration shows they still exist (repair via `doc-hierarchy-migrate`).

## What this replaces

Remove per-skill enforcement of:

- `docs/examples/` for LLM playbooks
- `docs/plans/` vs `docs/history/plans/`
- `docs/reviews/` vs `docs/history/reviews/`
- Durable `docs/<module>/` trees

Replace with: resolve → use → if layout looks legacy on a company service, suggest `doc-hierarchy-migrate` (do not silently relocate files).

## Default path map (post-migration)

Use only when the [migration-complete signal](../doc-hierarchy/SKILL.md#migration-complete-signal) is fully true (including verify `full` exit 0 in the current session). Do not apply when partial migration evidence exists but the signal is false.

| Key | Default |
|-----|---------|
| `plans_dir` | `docs/history/plans/` |
| `plans_completed_dir` | `docs/history/plans/completed/` |
| `reviews_dir` | `docs/history/reviews/` |
| `tmp_dir` | `docs/tmp/` |
| `proposals_dir` | `docs/history/feature-notes/proposals/` |
| `caller_catalog` | `docs/maintenance/api-reference.md` |
| `guidelines_path` | `docs/maintenance/project-guidelines.md` |
| `facts_path` | `docs/maintenance/facts.md` |
| `rfcs_dir` | `docs/history/feature-notes/` |

## Integration Points

| Consumer / provider | Integration |
|---------------------|-------------|
| `doc-hierarchy` | Defines migration-complete signal that gates the default path map |
| `doc-hierarchy-migrate`, `doc-hierarchy-upkeep` | Write canonical paths into repo specs during migration and upkeep |
| `plans`, `execute-plan`, `doing-code-review`, `review-plan`, `learn`, `done`, `docs-branch` | Resolve `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. at task start |
| `review-confluence-doc`, `rfc-design`, `using-skills` | Read resolved doc paths; do not hardcode legacy layout |
