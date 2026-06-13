---
name: bootstrap-ai-playbook
description: >
  Bootstraps the gitignored repo agent runtime directory on a target project: gitignore gate,
  on-disk path discovery, and `.ai-playbook/facts.md` creation or refresh. Runs once per project
  when missing or stale — not every session. Renamed from `resolve-vars`.
---

# Bootstrap AI Playbook — Repo Agent Runtime

Bootstraps the gitignored repo agent runtime directory (`.ai-playbook/`) on a target project. Writes path keys and agent context to `.ai-playbook/facts.md` so other skills read resolved `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. without per-skill discovery logic.

## Two Layers (Do Not Conflate)

| Layer | Location | Committed? |
|-------|----------|------------|
| Skill spec (this file) | `agents/skills/bootstrap-ai-playbook/SKILL.md` in the instructions repo | Yes |
| Bootstrap output | `<target-repo>/.ai-playbook/*` | No — always gitignored |

All invocation artifacts live under the target repo's `.ai-playbook/` only. Do not create committed runtime copies, `*.example` files, or `docs/facts.md` for bootstrap output.

## Core Concepts

- **Repo agent runtime dir**: `<repo>/.ai-playbook/` — whole directory must be gitignored before any write.
- **Repo agent facts**: `<repo>/.ai-playbook/facts.md` — fenced TOML path keys plus prose below (Jira ledger, scoping notes).
- **Required TOML keys**: `plans_dir`, `reviews_dir`, `tmp_dir`, `facts_path`, `bootstrap_version` — absence means keys incomplete; refresh discovery.
- **On-disk discovery first**: Prefer the shallowest existing directory matching hints. Never seed path values from plan text, doc-hierarchy literals, or skill defaults without verifying the path exists on disk.
- **Re-read-before-write**: Re-read `.ai-playbook/facts.md` immediately before persisting; merge TOML keys without clobbering prose below the opening fence.

## When to Use

Invoke when **Terms triggers** fire (at most once per session, except **recovery rerun** below):

- `.ai-playbook/facts.md` missing
- Opening TOML fence invalid or unparsable
- Any required key missing or empty
- `.ai-playbook/` or `.ai-playbook/facts.md` not gitignored
- Cached path keys point at directories that no longer exist on disk (stale)

When the file exists, TOML is valid, required keys are present, paths exist on disk, and gitignore passes — **no-op**; return cached values.

**Recovery rerun (same session):** If bootstrap already ran this session but post-write validation fails (missing required key, directory absent, unparsable opening fence), or a consumer cannot resolve a required path key after reading `.ai-playbook/facts.md`, run bootstrap again once for recovery. Do not cap recovery reruns when validation still fails after the first write.

Other skills **read** TOML keys from `.ai-playbook/facts.md`; they do not invoke this skill every task unless a trigger fires (see `using-skills` Step 0).

## Hard Gates (Before Any Write)

### 1. Legacy committed facts — hard fail

If `docs/maintenance/facts.md` or legacy root `docs/facts.md` is tracked:

```bash
git ls-files --error-unmatch docs/maintenance/facts.md 2>/dev/null
git ls-files --error-unmatch docs/facts.md 2>/dev/null
```

When either command exits 0, **stop**. Do not write `.ai-playbook/facts.md`. Tell the user to run **`doc-hierarchy-migrate` Step 5b** (promote FACT bodies to Layer 2, index stubs in `.ai-playbook/facts.md`, gitignore `/.ai-playbook/`, `git rm` legacy committed facts).

### 2. Gitignore gate — block until ignored

Before creating or updating anything under `.ai-playbook/`:

```bash
git check-ignore -q .ai-playbook/facts.md && git check-ignore -q .ai-playbook/
```

If either check fails, **ask the user** how to ignore the runtime dir:

1. **Repo `.gitignore` (recommended)** — add `/.ai-playbook/` (repo root only) and commit the ignore rule.
2. **Local exclude only** — when `.gitignore` cannot be committed, add `/.ai-playbook/` to `.git/info/exclude`.

Do not write until both checks pass. Confirm nothing under `.ai-playbook/` is tracked:

```bash
! git ls-files --error-unmatch .ai-playbook/ 2>/dev/null
```

## Facts File Shape

`.ai-playbook/facts.md` is Markdown with a **single opening fenced TOML block** followed by prose sections (for example `## Related Jira tasks`).

**Parse rule:** Read only the **first** ` ```toml ` … ` ``` ` fence. Ignore TOML-like lines inside later prose or inline code fences.

Example (values must come from **on-disk discovery** on the target repo, not copied from this skill):

````markdown
```toml
plans_dir = "docs/plans/"
reviews_dir = "docs/reviews/"
tmp_dir = "docs/tmp/"
facts_path = ".ai-playbook/facts.md"
bootstrap_version = "1"
```

## Related Jira tasks
...
````

Optional keys (discover when present; omit when not found):

| Key | Purpose | Discovery hints |
|-----|---------|-----------------|
| `plans_completed_dir` | Archived plans | `{plans_dir}/completed/`, `**/completed/` under plans root |
| `proposals_dir` | Pre-canonical RFC drafts | `docs/history/feature-notes/proposals/`, `docs/proposals/` |
| `rfcs_dir` | Design RFCs (Layer 3) | `docs/history/feature-notes/` |
| `caller_catalog` | HTTP/integration samples | Path named in `project_guidelines_rel` |
| `guidelines_path` | Project guidelines | `project_guidelines_rel` from user facts, then on-disk probe |

## Path Discovery

### Order

1. **Load cached TOML** from `.ai-playbook/facts.md` when valid and paths still exist on disk.
2. **`user_facts_path`** — `project_guidelines_rel`, `repo_facts_rel` (`.ai-playbook/facts.md` only; never `docs/facts.md`).
3. **Repo `AGENTS.md` / `CLAUDE.md`** — Documentation Hierarchy subsection if present.
4. **`project_guidelines_rel` on disk** — plan/review/tmp path notes (probe `docs/maintenance/project-guidelines.md`, then legacy `docs/project-guidelines.md` when user-facts path missing).
5. **On-disk exploration** — list/glob under `docs/` for existing `plans/`, `reviews/`, `tmp/`, `completed/`, `proposals/`, wire-catalog markdown.

**Partial migration:** When `docs/maintenance/` or `docs/architecture/` exists but doc-hierarchy migration-complete signal is false, continue exploration with legacy paths allowed; do not apply post-migration defaults without verification.

### Discovery rules

- For each hint, check whether the path exists as a directory (trailing slash normalized).
- When multiple matches, prefer the **shallowest** path.
- **Never** write a path key from doc-hierarchy default tables or plan examples unless that exact path exists on disk.
- If no home exists, follow `project_guidelines_rel` if documented; else ask the user before creating new top-level `docs/` trees.

### Exploration commands

```bash
ls -la docs/ 2>/dev/null
find docs -type d \( -name plans -o -name reviews -o -name tmp -o -name completed \) 2>/dev/null | head -20
git check-ignore -v .ai-playbook/ .ai-playbook/facts.md 2>/dev/null || true
```

## Implementation Workflow

### Step 1: Preconditions

Run hard gates (legacy committed facts, gitignore). Resolve `facts_path` as `.ai-playbook/facts.md` (from `repo_facts_rel` in user facts).

### Step 2: Load or refresh

1. If `.ai-playbook/facts.md` exists, parse the **opening** TOML fence only.
2. For each required key missing or pointing at a non-existent path, run discovery (Step 3).
3. Set `bootstrap_version = "1"` on create; bump only when this skill's persistence format changes.

### Step 3: Discover uncached keys

For each key the caller needs:

1. Use cached value when the directory exists on disk.
2. Otherwise run hints; prefer shallowest match.
3. If not found, return nothing and let the caller ask the user.

### Step 4: Persist (re-read-before-write)

1. Re-read `.ai-playbook/facts.md` if it exists.
2. Preserve all prose below the opening TOML fence unchanged.
3. Rewrite the opening TOML block with merged keys (required + any optional keys discovered).
4. Create `.ai-playbook/` if needed; write only under `.ai-playbook/`.
5. **Atomic replace:** write to a temp file in the same directory (for example `.ai-playbook/facts.md.refresh.$$`), then `mv` over the target. Match the pattern in `verify-doc-hierarchy.sh` `refresh_opening_toml_preserve_prose` so concurrent sessions do not clobber each other's prose with a stale read snapshot.
6. **Post-write validation:** confirm required keys and that `plans_dir`, `reviews_dir`, and `tmp_dir` directories exist. On failure, treat as a recovery rerun trigger (see **Recovery rerun** above).

### Step 5: Return resolved paths

Return each resolved path to the caller. Substitute `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. in downstream steps.

## Skill Behavior Rules

- **Write:** Use resolved paths only. Never override tool-default plan locations (`.cursor/plans/`, etc.) with hardcoded skill paths.
- **Read:** Search resolved dirs first; broaden to `docs/**` only when the spec does not pin a location.
- **Create:** Do not create `docs/facts.md`, `docs/maintenance/facts.md`, or committed bootstrap templates.
- **Company services:** After `doc-hierarchy-migrate` completes, canonical path **names** live in `project_guidelines_rel`; resolved `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. are read from gitignored `.ai-playbook/facts.md` TOML via `using-skills` Step 0. Do not fall back to legacy `docs/examples/` without on-disk evidence.

## Integration Points

| Consumer / Provider | Integration |
|---------------------|-------------|
| `using-skills` | Step 0 reads `.ai-playbook/facts.md`; invokes this skill only when Terms triggers fire |
| `doc-hierarchy`, `doc-hierarchy-migrate`, `doc-hierarchy-upkeep` | Migration-complete signal and Step 5b for legacy committed facts |
| `plans`, `execute-plan`, `doing-code-review`, `review-plan`, `learn`, `done`, `docs-branch` | Read TOML keys from `.ai-playbook/facts.md` |
| `review-confluence-doc`, `rfc-design` | Read `{tmp_dir}` and caller catalog from repo agent facts |

## Related

- `doc-hierarchy` — schema reference and migration-complete signal
- `doc-hierarchy-migrate` — Step 5b promotes legacy `docs/maintenance/facts.md` before bootstrap
