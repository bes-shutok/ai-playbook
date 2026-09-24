---
name: bootstrap-ai-playbook
description: >
  Bootstraps the gitignored repo agent runtime directory on a target project: gitignore gate,
  on-disk path discovery, and `.ai-playbook/facts.md` creation or refresh. Runs once per project
  when missing or stale; not every session. Renamed from `resolve-vars`.
---

# Bootstrap AI Playbook; Repo Agent Runtime

Bootstraps the gitignored repo agent runtime directory (`.ai-playbook/`) on a target project. Writes path keys and agent context to `.ai-playbook/facts.md` so other skills read resolved `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. without per-skill discovery logic.

## Two Layers (Do Not Conflate)

| Layer | Location | Committed? |
|-------|----------|------------|
| Skill spec (this file) | `agents/skills/bootstrap-ai-playbook/SKILL.md` in the instructions repo | Yes |
| Bootstrap output | `<target-repo>/.ai-playbook/*` | No; always gitignored |

All invocation artifacts live under the target repo's `.ai-playbook/` only. Do not create committed runtime copies, `*.example` files, or `docs/facts.md` for bootstrap output.

## Core Concepts

- **Repo agent runtime dir**: `<repo>/.ai-playbook/`; whole directory must be gitignored before any write.
- **Repo agent facts**: `<repo>/.ai-playbook/facts.md`; fenced TOML path keys plus prose below (Jira ledger, scoping notes).
- **Required TOML keys**: `plans_dir`, `reviews_dir`, `tmp_dir`, `backlog_dir`, `backlog_completed_dir`, `facts_path`, `bootstrap_version`; absence means keys incomplete; refresh discovery.
- **On-disk discovery first**: Prefer the shallowest existing directory matching hints. Never seed path values from plan text, doc-hierarchy literals, or skill defaults without verifying the path exists on disk.
- **Re-read-before-write**: Re-read `.ai-playbook/facts.md` immediately before persisting; merge TOML keys without clobbering prose below the opening fence.

## When to Use

Invoke when **Terms triggers** fire (at most once per session, except **recovery rerun** below):

- `.ai-playbook/facts.md` missing
- Opening TOML fence invalid or unparsable
- Any required key missing or empty
- `.ai-playbook/` or `.ai-playbook/facts.md` not gitignored
- Cached path keys point at directories that no longer exist on disk (stale)

When the file exists, TOML is valid, required keys are present, paths exist on disk, and gitignore passes; **no-op**; return cached values.

**Recovery rerun (same session):** If bootstrap already ran this session but post-write validation fails (missing required key, directory absent, unparsable opening fence), or a consumer cannot resolve a required path key after reading `.ai-playbook/facts.md`, run bootstrap again once for recovery. Do not cap recovery reruns when validation still fails after the first write. Exception: a `{backlog_dir}` / `{backlog_completed_dir}` ask awaiting the user, or a greenfield doc-layout ask awaiting the user, is not a validation failure; re-ask once per session instead of rerunning bootstrap, so the persist-no-keys greenfield behavior cannot compose with the missing-required-key trigger into an unbounded non-interactive rerun loop.

Other skills **read** TOML keys from `.ai-playbook/facts.md`; they do not invoke this skill every task unless a trigger fires (see `using-skills` Step 0).

## Hard Gates (Before Any Write)

### 1. Legacy committed facts; hard fail

If `docs/maintenance/facts.md` or legacy root `docs/facts.md` is tracked:

```bash
git ls-files --error-unmatch docs/maintenance/facts.md 2>/dev/null
git ls-files --error-unmatch docs/facts.md 2>/dev/null
```

When either command exits 0, **stop**. Do not write `.ai-playbook/facts.md`. Tell the user to run **`doc-hierarchy-migrate` Step 5b** (promote FACT bodies to Layer 2, index stubs in `.ai-playbook/facts.md`, gitignore `/.ai-playbook/`, `git rm` legacy committed facts).

### 2. Gitignore gate; block until ignored

Before creating or updating anything under `.ai-playbook/`:

```bash
git check-ignore -q .ai-playbook/facts.md && git check-ignore -q .ai-playbook/
```

If either check fails, **ask the user** how to ignore the runtime dir:

1. **Repo `.gitignore` (recommended)**; add `/.ai-playbook/` (repo root only) and commit the ignore rule.
2. **Local exclude only**; when `.gitignore` cannot be committed, add `/.ai-playbook/` to `.git/info/exclude`.

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
backlog_dir = "docs/history/backlog/"
backlog_completed_dir = "docs/history/backlog/completed/"
facts_path = ".ai-playbook/facts.md"
bootstrap_version = "1"
# tmp_dir is for DOCUMENTS only (.md logs, .patch diff snapshots) - synced to the orphan docs branch.
# Throwaway SCRIPTS and scratch data (.py shadow/verification scripts, .csv/.txt, __pycache__/) go
# in repo-root tmp/ (gitignored, NOT synced to docs branch). See agent_workflow_guidelines.md §50.3.1.
```

## Related Jira tasks
...
````

The `docs/plans/` and `docs/reviews/` values in this example are legacy-layout examples, not greenfield defaults; for the canonical history map, see the greenfield rule in Path Discovery.

Optional keys (discover when present; omit when not found):

| Key | Purpose | Discovery hints |
|-----|---------|-----------------|
| `plans_completed_dir` | Archived plans | `{plans_dir}/completed/`, `**/completed/` under plans root |
| `proposals_dir` | Pre-canonical RFC drafts | `docs/history/feature-notes/proposals/`, `docs/proposals/` |
| `rfcs_dir` | Design RFCs (Layer 3) | `docs/history/feature-notes/` |
| `caller_catalog` | HTTP/integration samples | Path named in `project_guidelines_rel` |
| `guidelines_path` | Project guidelines | `project_guidelines_rel` from user facts, then on-disk probe |
| `team_references_project` | Local project containing team profiles and team/Slack context | User or ownership facts when company-scoped; persist only when the resolved path exists |
| `friction_audit_dir` | Friction-audit watermark state and digests for the maintenance audit lane | Falls back to `.ai-playbook/friction-audit/` when absent (same resolution pattern as `tmp_dir`); under `.ai-playbook/`, gitignored by the existing `/.ai-playbook/` rule |

## Path Discovery

### Order

1. **Load cached TOML** from `.ai-playbook/facts.md` when valid and paths still exist on disk.
2. **`user_facts_path`**; `project_guidelines_rel`, `repo_facts_rel` (`.ai-playbook/facts.md` only; never `docs/facts.md`).
3. **Repo `AGENTS.md` / `CLAUDE.md`**; Documentation Hierarchy subsection if present.
4. **`project_guidelines_rel` on disk**; plan/review/tmp path notes (probe `docs/maintenance/project-guidelines.md`, then legacy `docs/project-guidelines.md` when user-facts path missing).
5. **On-disk exploration**; list/glob under `docs/` for existing `plans/`, `reviews/`, `tmp/`, `completed/`, `backlog/`, `proposals/`, wire-catalog markdown.

**Partial migration:** When `docs/maintenance/` or `docs/architecture/` exists but doc-hierarchy migration-complete signal is false, continue exploration with legacy paths allowed; do not apply post-migration defaults without verification.

### Discovery rules

- For each hint, check whether the path exists as a directory (trailing slash normalized).
- When multiple matches, prefer the **shallowest** path.
- **Never** write a path key from doc-hierarchy default tables or plan examples unless that exact path exists on disk.
- `backlog_dir` / `backlog_completed_dir`: discover `docs/history/backlog/` and `docs/history/backlog/completed/` (Layer 3 backlog per `doc-hierarchy`). When `docs/history/` exists but `backlog/` does not, create `docs/history/backlog/completed/` and persist both keys. The `completed/` directory exists for tooling compatibility and should stay empty of dated item files (completion folds disposition into `{plans_completed_dir}` then deletes the backlog file; see `plans` **Plan Lifecycle**). When `docs/history/` is absent, ask the user (or return the ask to the orchestrator in a non-interactive run) for the backlog home and persist the confirmed path; do not invent one (`docs/maintenance/` is Layer 2 living ops and `docs/tmp/` is ephemeral; neither is a backlog home).
- For company-scoped repos, when user or ownership facts provide `team_references_project` and the directory exists, persist that optional key in the repo facts. Do not invent the path or copy a concrete team alias into this portable skill.
- **Greenfield (no `docs/` tree at all):** when the repo has no `docs/` tree at all, ask explicitly whether the doc-hierarchy schema is the target layout before any doc-key discovery. When confirmed, skip discovery for the doc keys and seed the canonical map directly: `plans_dir = "docs/history/plans/"`, `plans_completed_dir = "docs/history/plans/completed/"`, `reviews_dir = "docs/history/reviews/"`, `backlog_dir = "docs/history/backlog/"`, `backlog_completed_dir = "docs/history/backlog/completed/"`, `tmp_dir = "docs/tmp/"`; create every seeded directory before persisting (satisfying the on-disk rule in Core Concepts), and add `docs/history/reviews/` and `docs/tmp/` to `.gitignore` when no existing rule ignores them, committing the ignore rule so it survives fresh clones. Bootstrap and `doc-hierarchy-migrate` then compose in either order, because a later migration finds the layout already canonical and no-ops on the doc keys. When the ask goes unanswered in a non-interactive run, record the open ask (per **Recovery rerun**) and persist no invented doc keys. When the ask is explicitly declined, do not seed doc keys and do not run the default hint discovery: fall through to the no-home policy in the final Discovery rule below (which composes with the residual legacy fallback for any caller-directed legacy layout); a declined ask persists no doc keys of its own and counts as the ask for this session's once-per-session re-ask budget.
- **Residual legacy fallback:** when top-level `docs/plans/` and `docs/reviews/` keys get persisted anyway (a caller-directed legacy layout or an older runtime default), warn that this is a conflict with the doc-hierarchy-migrate step2 gate, which fails while plans and reviews sit at the `docs/` root, and that the keys must be re-pointed to the canonical history map after any later migration.
- If no home exists, follow `project_guidelines_rel` if documented; else ask the user before creating new top-level `docs/` trees. On a repo with no `docs/` tree at all and no answered greenfield ask, this defers to the greenfield ask above; an unanswered ask persists no path keys (see the greenfield rule); a declined ask lands here, so follow `project_guidelines_rel` if documented, else ask before creating new top-level `docs/` trees.

### Exploration commands

```bash
ls -la docs/ 2>/dev/null
find docs -type d \( -name plans -o -name reviews -o -name tmp -o -name completed -o -name backlog \) 2>/dev/null | head -20
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
6. **Post-write validation:** confirm required keys and that `plans_dir`, `reviews_dir`, and `tmp_dir` directories exist; when `backlog_dir` / `backlog_completed_dir` are persisted, confirm those directories exist too. On failure, treat as a recovery rerun trigger (see **Recovery rerun** above).

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
| `doc-hierarchy`, `doc-hierarchy-migrate`, `doc-hierarchy-upkeep` | Migration-complete signal and Step 5b for legacy committed facts; on a repo with no `docs/` tree, the greenfield ask seeds the canonical history map when it is confirmed as the target layout |
| `plans`, `execute-plan`, `doing-code-review`, `review-plan`, `learn`, `done`, `docs-branch` | Read TOML keys from `.ai-playbook/facts.md` |
| `receiving-review` | Backlog capture reads `{backlog_dir}` / `{backlog_completed_dir}`; the recovery rerun resolves or creates the backlog home when the keys are missing |
| `review-confluence-doc`, `rfc-design` | Read `{reviews_dir}` and `{tmp_dir}` from repo agent facts; primary review staging under `{reviews_dir}/` per `review-staging` (`rfc-design` never uses `{tmp_dir}/rfc-review/`) |
| `confluence-page-sync` | Reads `{tmp_dir}` from repo agent facts for page-fetch and HTML scratch |
| `tdd-design` | Reads `{rfcs_dir}` / `{proposals_dir}` from repo agent facts; finished TDDs are Layer 3 history files like RFCs; drafts under `{proposals_dir}` when present |
| `maintenance` | Reads `friction_audit_dir` and `friction_audit_cadence_days` from repo agent facts for the audit lane; absent keys fall back to the documented defaults |

## Related

- `doc-hierarchy`; schema reference and migration-complete signal
- `doc-hierarchy-migrate`; Step 5b promotes legacy `docs/maintenance/facts.md` before bootstrap
