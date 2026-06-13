---
name: resolve-vars
description: >
  Utility skill for discovering and persisting project path variables. Reads project instructions to find facts.md location, then discovers paths (reviews, plans, tmp, etc.) and persists them to the project's facts file for reuse by other skills.
---

# Resolve Variables — Path Discovery and Persistence

Utility skill for discovering and persisting project-specific path variables. Other skills call this to get resolved paths like `{reviews_dir}`, `{plans_dir}`, `{tmp_dir}` without implementing their own discovery logic.

## Core Concepts

- **facts.md**: Project-local file holding resolved path variables for this repo. Location documented in project instructions (AGENTS.md/CLAUDE.md).
- **Discovery hints**: Glob patterns, directory names, or section headers used to find paths on disk.
- **Persistence**: Once discovered, paths are written to facts.md so future calls skip discovery.
- **Single source of truth**: Each project declares its own facts location in instructions; this skill reads that declaration to find facts.md.

## When to Use

Invoke this skill at task start when another skill needs resolved path variables. Other skills call `resolve-vars` when they need:
- `{reviews_dir}{reviews_dir}` — Review staging documents (often gitignored)
- `{plans_dir}` — Active implementation plans
- `{plans_completed_dir}` — Archived plans
- `{tmp_dir}` — Session scratch space
- `{proposals_dir}` — Pre-canonical RFC drafts
- `{guidelines_path}` — Project guidelines file
- `{facts_path}` — Repo facts file itself

## Resolution Order

When `resolve-vars` runs discovery, it uses this order:

1. **`user_facts_path`** — `project_guidelines_rel`, `repo_facts_rel` keys (paths relative to repo root)
2. **Repo `AGENTS.md`** — `Documentation Hierarchy` subsection (if present)
3. **`project_guidelines_rel`** — Documentation Hierarchy section, plan/review/tmp path notes, caller-catalog rules
4. **On-disk exploration** — Glob/list under `docs/` for existing `plans/`, `completed/`, `reviews/`, `tmp/`, `proposals/`, wire-catalog markdown
5. **`doc-hierarchy` migration-complete signal** — When steps 1–4 are silent and the repo is **company-scoped** (under `company_projects_root` per `company_ownership_facts` or user confirmation), apply the default path map (see below) only when the full migration-complete signal is true

**Partial migration:** When `docs/maintenance/` and/or `docs/architecture/` exist but the migration-complete signal is false, do **not** use the default path map. Continue exploration with legacy paths allowed.

**Stale facts:** When `project_guidelines_rel` from user facts points at a path that does not exist on disk, probe `docs/maintenance/project-guidelines.md` then legacy `docs/project-guidelines.md` before failing.

## Typical Resolved Keys

| Key | Purpose | Discovery hints |
|-----|---------|-----------------|
| `plans_dir` | Active implementation plans | `docs/history/plans/`, `docs/plans/` |
| `plans_completed_dir` | Archived plans | `{plans_dir}/completed/` |
| `reviews_dir` | Review staging (often gitignored) | `docs/history/reviews/`, `docs/reviews/` |
| `tmp_dir` | Session / execute-plan scratch | `docs/tmp/` |
| `proposals_dir` | Pre-canonical RFC drafts | `docs/history/feature-notes/proposals/`, `docs/proposals/` |
| `rfcs_dir` | Design RFCs (Layer 3) | `docs/history/feature-notes/` (flat) |
| `caller_catalog` | HTTP/integration samples (if any) | Path named in project-guidelines |
| `guidelines_path` | Project guidelines file | `project_guidelines_rel` fact |
| `facts_path` | Repo facts file | `repo_facts_rel` fact |

## Default Path Map (Post-Migration)

Use only when the migration-complete signal is fully true. Do not apply when partial migration evidence exists but the signal is false.

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

## Exploration Commands (for discovery)

```bash
# List top-level docs layout
ls -la docs/ 2>/dev/null
# Find plan and review roots
find docs -type d \( -name plans -o -name reviews -o -name completed \) 2>/dev/null | head -20
# Gitignored review dir check
git check-ignore -v docs/history/reviews docs/reviews 2>/dev/null || true
```

## Skill Behavior Rules

- **Write:** Use resolved paths only. Never override tool-default plan locations (`.cursor/plans/`, etc.) with a hardcoded skill path
- **Read:** Search resolved dirs first; broaden to `docs/**` only when the spec does not pin a location
- **Create:** If no home exists, follow project-guidelines if documented; else propose a path to the user before creating new top-level `docs/` trees
- **Company services:** After `doc-hierarchy-migrate` completes, paths live in `project_guidelines_rel` — do not fall back to legacy `docs/examples/` or flat `docs/plans/`

## What This Replaces

Remove per-skill enforcement of:
- `docs/examples/` for LLM playbooks
- `docs/plans/` vs `docs/history/plans/`
- `docs/reviews/` vs `docs/history/reviews/`
- Durable `docs/<module>/` trees

Replace with: resolve → use → if layout looks legacy on a company service, suggest `doc-hierarchy-migrate` (do not silently relocate files).

## Exception: doc-hierarchy Skills

The **`doc-hierarchy`** skill family defines the company three-layer schema. **`doc-hierarchy-migrate`** applies it when the user explicitly runs a migration or scaffold and writes canonical paths into the repo (`AGENTS.md`, `project_guidelines_rel`). **`doc-hierarchy`** (schema) and **`doc-hierarchy-upkeep`** do not relocate files. Other skills **read** paths; they do not enforce the schema themselves.

## Integration Points

| Consumer / Provider | Integration |
|---------------------|-------------|
| `doc-hierarchy` | Defines migration-complete signal that gates the default path map |
| `doc-hierarchy-migrate`, `doc-hierarchy-upkeep` | Write canonical paths into repo specs during migration and upkeep |
| `plans`, `execute-plan`, `doing-code-review`, `review-plan`, `learn`, `done`, `docs-branch` | Resolve `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. at task start |
| `review-confluence-doc`, `rfc-design`, `using-skills` | Read resolved doc paths; do not hardcode legacy layout |

## Implementation Steps

At task start, resolve each needed key using this workflow.

### Step 1: Find facts.md Location

Read project instructions to discover where facts.md lives:

1. Try `AGENTS.md` — look for "Facts file location:" or similar
2. Try `CLAUDE.md` — look for same marker
3. Fall back to common locations: `docs/facts.md`, `docs/maintenance/facts.md`
4. If none exist, create `docs/facts.md` as default

### Step 2: Load Existing Variables

If facts.md exists, parse it for existing key=value pairs. Format is flexible:
- TOML-like: `reviews_dir = "docs/reviews/"`
- YAML-like: `reviews_dir: docs/reviews/`
- Simple: `reviews_dir=docs/reviews/`

To read all cached variables, parse every key=value pair from facts.md.

### Step 3: Resolve a Key (if not cached)

For each uncached key the calling skill needs:

1. Check facts.md for a cached value — if present, use it
2. If absent, run discovery using hints (glob patterns or directory names under `docs/`)
3. For each hint:
   - If hint starts with `**/` (glob pattern): search with `find` or glob
   - If hint is a directory name: search under `docs/`
4. If multiple matches, prefer the shallowest path
5. If found, persist to facts.md and return the resolved path
6. If not found, return nothing and let the calling skill decide next steps

**Common hint sets:**

| Key | Hints |
|-----|-------|
| `reviews_dir` | `**/reviews/`, `docs/history/reviews`, `docs/reviews` |
| `plans_dir` | `**/plans/`, `docs/history/plans`, `docs/plans` |
| `tmp_dir` | `**/tmp/`, `docs/tmp` |

### Step 4: Persist Direct Values (optional)

When the caller already knows the correct path, write the key=value pair to facts.md without running discovery.

### Step 5: Return Resolved Paths

Return each resolved path to the calling skill. Substitute resolved values everywhere the caller shows `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc.

## Agent Workflow Example

1. At task start, invoke this skill before reading or writing repo docs.
2. Resolve `reviews_dir` using hints `**/reviews/`, `docs/history/reviews`, `docs/reviews`.
3. If resolution fails, ask the user or stop with a clear error — do not hardcode a fallback path.
4. Write staging output to `{reviews_dir}/YYYY-MM-DD-review-<slug>.md` using the resolved path.

## Facts.md Format

The facts.md file uses a simple key=value format that's easy to parse and edit:

```toml
# Project facts — resolved paths and configuration

reviews_dir = "docs/reviews/"
plans_dir = "docs/plans/"
plans_completed_dir = "docs/plans/completed/"
tmp_dir = "docs/tmp/"
guidelines_path = "docs/project-guidelines.md"
facts_path = "docs/facts.md"
```

## Integration with Existing Skills

Skills that currently do their own path resolution should:
1. Remove local discovery logic
2. Call `resolve-vars` instead
3. Document the variable names they need

## Rules

- Always read project instructions to find facts.md location — never assume a fixed path
- Prefer cached values in facts.md over re-running discovery
- Use glob hints that match common project layouts (doc-hierarchy, legacy, etc.)
- Create `docs/facts.md` when no facts file exists — default location per Step 1
- If discovery fails, return `None` and let the calling skill decide how to handle it
