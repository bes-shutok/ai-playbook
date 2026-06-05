---
name: done
description: >
  Finalize a development session by running the learn workflow to capture lessons, then committing
  all uncommitted changes across all repositories (project, skills, docs/facts). Use when the user
  signals a session is complete (e.g. "done", "commit", "wrap up"). This is the only skill that
  performs git commits — other skills (learn, review, etc.) make file changes but never commit.
---

# Done

Run `/learn` to capture lessons from this session, then commit all uncommitted changes across all repositories touched during the session.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `skills_repo_path` | Path to the ai-playbook / skills repository | `~/.agents/scripts/commit-skills.sh` default |

## Step 1: Run Learn

Invoke the `learn` skill now to extract lessons and update the documentation corpus before committing.

## Step 2: Preserve Gitignored Docs and Instructions

Invoke the `docs-branch` skill now. It will:
1. Stash all gitignored LLM artifact paths (`docs/`, `.github/docs/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT.md`, `.claude/`) so they survive branch switches, then re-apply the stash so files remain on disk.
2. Sync those files to the permanent `docs` orphan branch, creating it if it doesn't exist.

> All implementation details, edge cases, and the full bash script live in `docs-branch/SKILL.md`. Refer there for the canonical script when executing.

**After docs-branch completes, verify gitignored files are still on disk:**
```bash
for p in docs/tmp docs/reviews docs/personal AGENTS.md CLAUDE.md; do
  [ -e "$p" ] && git check-ignore -q "$p" && echo "OK: $p" || true
done
```
If any gitignored path that existed before docs-branch is now missing, restore it immediately from the `docs` orphan branch before proceeding:
```bash
git checkout refs/heads/docs -- <missing-path>
git restore --staged <missing-path>
```

## Step 2.5: Roll Back Formatting-Only Changes

Before committing, identify and revert any **uncommitted** files where the only diff is formatting (whitespace, trailing commas, blank lines, import reordering, line wrapping, or collapsing multi-line expressions to a single line) with no logic, naming, or structural change.

**This applies to ALL uncommitted files — including pre-existing local changes not made in this session.**

1. List uncommitted changed files: `git diff --name-only && git diff --cached --name-only`.
2. For each file, visually inspect `git diff -- <file>`. Revert if **every** hunk is one of:
   - whitespace / blank line changes
   - line wrapping / unwrapping (same tokens, different line breaks)
   - trailing commas added/removed
   - import reordering
   - end-of-file newline added
   - collapsing or expanding multi-line expressions with no token change

   Do **not** rely solely on `git diff -w --ignore-blank-lines` — that flag misses ktlint reformatting such as line splits and trailing commas.
   ```bash
   git restore <file>          # unstaged changes
   git restore --staged <file> # staged changes
   ```
3. Confirm no unintended reverts: re-read the diff for any reverted file before staging.

> Formatting-only files add noise to PRs and waste reviewer time. Never include them unless the PR's explicit purpose is formatting cleanup.

## Step 2.6: Check Documentation Cross-References Added In This Session

Before committing, review whether this session created or substantially revised reusable documentation, reference material, instruction guidance, or explanatory artifacts. If yes, verify the required cross-references were added.

Check for these cases:

1. **New or expanded reusable guidance**
   - If the session added or materially expanded a guidance document that future agents or contributors are expected to consult, make sure instruction files or nearby canonical docs point to it.
   - Update both `AGENTS.md` and `CLAUDE.md` together when adding such references.

2. **New or updated reference material**
   - If the session added or relied on source manifests, mirrored references, standards, regulations, specs, external research docs, or similar reference material, verify the relevant manifest or index was updated and that dependent docs point to that reference set appropriately.

3. **New explanatory artifacts**
   - If the session added or materially revised a walkthrough, presentation artifact, decision note, or similar explanatory document, verify that any relevant authoring guidance or discoverability references were added where future agents would reasonably look for them.

4. **New instruction rules**
   - If the session added rules to instruction files, confirm any canonical docs those rules depend on are referenced explicitly instead of leaving the relationship implicit.

Do not assume the `learn` step already wired these references correctly. Re-check the final diff before staging and commit any missing cross-links as part of cleanup.

## Step 2.7: Sensitive Data and Personal Information Scan

Before committing, scan all uncommitted changes (including untracked files) for sensitive or personal information that must not appear in public repositories.

**Check for:**
- Hardcoded absolute paths containing usernames (e.g., `/Users/john/`, `/home/john/`)
- Organization-specific domains, internal URLs, or service names
- Employee names, email addresses, or identifiers
- API keys, tokens, passwords, or credentials
- Project-specific ticket prefixes or internal naming that reveals client/employer identity
- Environment names or internal infrastructure references

**How to scan:**
1. List all changed/untracked files: `git status --short`
2. For each file in the diff, grep for patterns:
   ```bash
   git diff --cached -U0 | grep -iE '/Users/|/home/|\.atlassian\.net|@[a-z]+\.(com|io|net)|api[_-]?key|token|password|secret'
   ```
3. For untracked files being staged, scan their full content.

**If found:**
- Replace personal paths with facts-document references or generic placeholders (e.g., `<your-org>.atlassian.net`, `~/Projects/<project>/`)
- Replace internal names with generic equivalents
- Move credentials to `.env` or facts documents (never commit them)
- If the information is in a skill file, externalize it to the Configuration/facts section

**Do NOT commit until all sensitive data is resolved.**

## Step 3: Commit Uncommitted Changes

After learn and stash steps complete:

0. **Distinguish session changes from pre-existing local changes.** Only commit changes that were made during this session. If `git status` shows uncommitted files that were not touched by you in this session, ask the user before staging them — they may be in-progress work the user does not want committed yet.
1. Run `git status` and `git diff` (staged + unstaged) to see all changes.
2. Run `git log --oneline -5` to match existing commit message style.
3. Derive the story key from the current branch name (e.g. `feature/CRM-325-...` → `CRM-325`). If the branch name contains no story key, use a plain descriptive commit message without a ticket prefix on branches such as `main` or `master`. Ask the user only if the repository convention is unclear and there is no obvious non-ticket fallback.
4. **Before staging any file, verify it is not gitignored:**
   ```bash
   git check-ignore -q <file> && echo "IGNORED — do not stage"
   ```
   If a file appears in `git diff` but is gitignored, it was previously force-tracked. Remove it from tracking first and do **not** commit it on the feature branch:
   ```bash
   git rm --cached <file>
   ```
   Gitignored files belong on the `docs` branch only (handled in Step 2.1), not on the working feature branch.
5. Stage relevant non-ignored files. Prefer adding specific files by name; never use `git add -A` or `git add .` unless the user explicitly requests it.
6. Write a concise commit message. If there is a story key, prefix with `[<STORY-KEY>]`; otherwise use a plain descriptive subject. Focus on the "why" not the "what".
7. Commit using a HEREDOC. **Never** add `Co-Authored-By:` or `Co-authored-by:` trailers (including `Co-authored-by: Cursor <cursoragent@cursor.com>`). Do not use `git commit --trailer`. In Cursor IDE, Attribution must be off (**Settings → Agent → Attribution**).
8. Run `git status` after the commit to confirm success.

### Commit message format

With a story key:

```
git commit -m "$(cat <<'EOF'
[CRM-XXX] <concise description of what and why>
EOF
)"
```

Without a story key:

```
git commit -m "$(cat <<'EOF'
<concise description of what and why>
EOF
)"
```

## Step 4: Commit Pending Skill Changes

After committing the current project, check whether any skills were modified during this session:

```bash
cd <skills_repo_path> && git diff --name-only -- agents/skills/
```

Resolve `<skills_repo_path>` from the user's facts document (key: `skills_repo_path`). If not found, check `~/.agents/scripts/commit-skills.sh` for the default path, or ask the user.

If there are changes, run:

```bash
<skills_repo_path>/scripts/commit-skills.sh
```

This commits any pending skill edits to the ai-playbook repo with an auto-generated message. You may pass a custom message as the first argument if the default is not descriptive enough.

## Step 5: Commit Pending Facts and Docs Changes

After committing skills, check whether any facts documents or docs repositories were modified during this session. Each docs directory is its own git repo and must be committed independently.

Resolve paths from the user's facts document:
- `shared_docs_dir` — cross-project guidelines and shared facts
- Project-specific docs directories are determined from the current working project

For each docs git repo that has uncommitted changes:

```bash
cd <docs_dir> && git status --short
```

If there are changes:

```bash
cd <docs_dir> && git add -A && git commit -m "docs: <brief description of what was added/updated>"
```

Do not push — these are local-only docs repositories.

**Common docs repos to check:**
- Shared docs (from facts `shared_docs_dir`)
- Current project's `docs/` directory (if it is a separate git repo)

## Integration Points

### With `execute-plan` skill
Invoked as a sub-agent after **each** completed plan task (per-task commit) and after **each** review/fix iteration (per-iteration commit). The orchestrator passes the plan path, task or review-round context, suggested commit subject, and **sub-agent log paths** under `docs/tmp/execute-plan/<plan-slug>/`.

**Before Step 1 (learn):** read only the **preceding-step** log(s) the orchestrator listed — for per-task `done`, the implement log from Step 1.2; for review-iteration `done`, the current round's review log (Step 3.1) and address log (Step 3.3) when it ran. Do not read full session history. Use log content as primary input for `learn`, not the orchestrator chat summary. If a required preceding-step log is missing, return `blocked` and do not commit. See `execute-plan/agent-logs.md`.

## Rules

- Always run learn before committing — lessons must be captured first.
- Never skip the learn step even if the user says "just commit".
- Invoke `docs-branch` skill for all docs/instructions preservation — do not inline the stash or branch logic here.
- Always verify that new or revised reusable docs, reference material, and explanatory artifacts added in the session are referenced from instructions or related canonical docs where future agents will need them.
- Never stage or commit a file that is gitignored, even if it appears in `git diff` (it was previously force-tracked). Use `git rm --cached` to remove it from tracking; do not commit it on the feature branch.
- Never add `Co-Authored-By:` or `Co-authored-by:` trailers (including Cursor's `cursoragent@cursor.com` trailer). Do not use `git commit --trailer`; disable Cursor **Agent → Attribution**.
- Never use `--no-verify`.
- Never commit secrets, PII files (`.env`, credential files), or personal/org-specific information into public repositories.
- Never hardcode personal paths, org domains, or project-specific identifiers in skill files — externalize to facts documents.
- If the branch has no story key, use a plain descriptive commit message on branches such as `main` or `master`; ask only when the repository convention is unclear.
