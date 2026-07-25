---
name: done
description: >
  Finalize a development session by running the learn workflow to capture lessons, then committing
  all uncommitted changes across all repositories (project, skills, docs/facts). Use when the user
  signals a session is complete (e.g. "done", "commit", "wrap up"). This is the only skill that
  performs git commits, other skills (learn, review, etc.) make file changes but never commit.
---

# Done

Run `/learn` to capture lessons from this session, then commit all uncommitted changes across all repositories touched during the session.

## Invocation (read first)

`done`, `learn`, and `docs-branch` are **markdown skills**, not shell commands or binaries. There is no runner under `~/.ai-playbook/runtime` and no `/learn` executable.

- **Do not** run `done`, `learn`, `docs-branch`, `SKILL.md`, or `/learn` as shell commands.
- **Do not** delegate this workflow to a Task/subagent that tries to exec a skill path.
- **Do** read each skill file (`~/.agents/skills/<name>/SKILL.md`) and execute its steps in **this** agent session using normal tools (shell for scripts, Read/Write for skill logic).

**Workflow continuity:** This skill executes as a continuous sequence of steps (0 → 1 → 2.65 → 2.64 → 2 → 2.5 → 2.6 → 2.7 → 2.75 → 2.76 → 2.8 → 3 → 4 → 5 → 6 → 7). After each step or skill invocation completes, immediately proceed to the next step without stopping or waiting for user input. Only stop if a step fails, produces an error, or requires user clarification. **Exception:** Step 0 uses a short agent wait (`DONE_LOCK_AGENT_MAX_WAIT_SECS`, default 90s); on timeout return `blocked` with lock `status` instead of polling for hours. **An empty project working tree is not a stop condition:** still run Steps 2.65, 2.64, 2, and 6 and finish with Step 7.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `skills_repo_path` | Path to the skills repository | `~/.agents/scripts/commit-skills.sh` default |
| `done_lock_script` | Per-repo done lock script | `~/.ai-playbook/scripts/done-lock.sh` |
| `confluence_mirror_hygiene_script` | Confluence mirror validate + ephemeral tmp cleanup | `~/.ai-playbook/scripts/confluence-mirror-hygiene.sh` |

Script path for Step 0 / Step 6 (override with `DONE_LOCK_SCRIPT` for local testing):

```bash
"${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
```

Agent wait budget for Step 0 (override for local testing):

```bash
"${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
```

## Step 0: Acquire project done lock

Parallel agent sessions on the **same git repository** must not run `learn`, `docs-branch`, or project commits at the same time. Acquire an exclusive per-repo lock **before** Step 1.

1. From the project git root (`git rev-parse --show-toplevel`), run **`status`** first (non-blocking) so a held lock is visible before waiting.

2. Acquire with a **short agent wait** (do not use the script default 7200s in agent sessions):

   ```bash
   LABEL="$(git branch --show-current 2>/dev/null || echo unknown-branch)"
   MAX_WAIT="${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
   LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
   if ! LOCK_EXPORTS="$("$LOCK_SCRIPT" wait-acquire --label "$LABEL" --max-wait "$MAX_WAIT")"; then
     "$LOCK_SCRIPT" status >&2
     echo "done-lock: blocked after ${MAX_WAIT}s; another done holds the lock" >&2
     echo "done-lock: if holder PID is dead or lock is stale, run: $LOCK_SCRIPT stale-clean" >&2
     exit 2
   fi
   eval "$LOCK_EXPORTS"
   if [[ -z "${DONE_LOCK_DIR:-}" || -z "${DONE_LOCK_TOKEN:-}" ]]; then
     echo "done-lock: acquire succeeded without lock exports" >&2
     exit 1
   fi
   ```

3. Keep `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` in scope when the same shell session runs multiple steps. **Across separate Shell tool calls**, re-export those two values from your Step 0 acquire stdout (chat context). The file `<repo>/.ai-playbook/done-lock.session` is a **fence/status** signal only; Step 6 `release-repo` requires env vars and will **not** source that file (confused-deputy guard after stale-clean / peer acquire).
4. If **wait-acquire** times out, run `status`, report the holder (`label`, `age_secs`, `holder_pid`, `holder_alive`, `stealable` / `abandoned`), return `blocked`, and **do not** commit. Do not bypass an active lock. Do **not** run `stale-clean` unless `status` shows the lock is stale/abandoned **and** you intend to take over; after `stale-clean`, only the chat that successfully re-acquires may release (using that acquire's token).
5. **Stealable locks** (auto-stolen on the next `acquire` / `wait-acquire` poll):
   - **Stale:** age ≥ `DONE_LOCK_STALE_SECS` (default 1800 = 30m) **and** no matching session fence.
   - **Abandoned:** lock metadata records `holder_pid` and that process is not running **and** there is no matching `<repo>/.ai-playbook/done-lock.session` for the lock token.
   - **Session fence:** a dead `holder_pid` with a live matching session file is **not** auto-stealable, even after stale TTL (normal after one-shot Shell tool exits). Operator escape: `stale-clean` may remove a fenced lock when it is also stale. Step 6 releases only with the env token from **your** acquire.
6. Optional: pass a richer `--label` (plan slug, task id, review round) when the orchestrator provides context.

**After the lock is acquired, immediately continue to Step 1.** Do not run learn, docs-branch, or project commits before Step 0 succeeds.

## Step 1: Run Learn

Invoke the `learn` skill now to extract lessons and update the documentation corpus before committing.

**If `learn` reports a blocked state** (Step 6.6 user-corpus violation: a strict-tagged `UL#N` lesson is missing its `**Principle:** Family X` tag, or the gate script returned non-zero on the adopted corpus), release the lock via Step 6 and return `blocked` WITHOUT proceeding to Step 2 commit. `learn` is invoked here as a SKILL (a sub-procedure), not as a subprocess whose exit code this step checks, so the gate's block decision lives in `learn`'s Step 6.6 text and propagates here through `learn`'s returned state. The operator fixes the user corpus out-of-band (classify the listed `UL#N` via learn/generalize, or run `lessons_adopt.py --tag-unclassified <user_corpus>` manually) before the next `done`.

**After learn completes, immediately continue to Step 2.65.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

## Step 2.65: Confluence mirror and ephemeral tmp hygiene

Before `docs-branch`, validate Confluence mirror state and handle ephemeral publish snapshots under `docs/tmp/`. **Never delete `*-cf-out.md` until audit confirms the content is already represented in the docs hierarchy or is a stale duplicate.**

**Run when any of these are true:**

- `docs/maintenance/confluence-sync-manifest.json` exists in the project repo
- This session created or updated files under `docs/history/context/confluence/`
- This session pushed or restored Confluence pages via Atlassian MCP
- Ephemeral files exist under `docs/tmp/` (`*-cf-out.md`, `__pycache__`)

**Skip** when none apply and `docs/tmp/` has no ephemeral publish snapshots.

```bash
HYGIENE="${CONFLUENCE_MIRROR_HYGIENE_SCRIPT:-${HOME}/.ai-playbook/scripts/confluence-mirror-hygiene.sh}"
```

1. **Audit before delete.** Classify each `docs/tmp/*-cf-out.md`:

   ```bash
   "$HYGIENE" audit-cf-out
   ```

   - **NEEDS_UPGRADE:** promote content into the docs hierarchy first:
     1. `docs/history/context/confluence/{page_id}-{slug}.md` with standard mirror frontmatter (verbatim wiki body)
     2. `layer2_targets` from `confluence-sync-manifest.json` when curated Layer 2 is authoritative
     3. Engineering spike sync ledgers (for example ADR-46 §Confluence sync ledger) when versions changed
   - **UNMAPPED:** route manually (new manifest entry, mirror file, or Layer 2 doc); do not delete.
   - **STALE:** safe to remove after promotion pass (older publish snapshot, subset of mirror, or superseded wording).

   Re-run `audit-cf-out` until exit 0 before cleanup.

2. When a manifest exists, run validation:

   ```bash
   "$HYGIENE" validate
   ```

   On failure, fix before `docs-branch` and re-run until exit 0:

   - Mirror files use standard YAML frontmatter (`confluence_page_id`, `confluence_title`, `confluence_version`, `confluence_url`, `space_key`, `synced_at`, `sync_status`, `layer2_targets`). Do not use a bare `path:` key.
   - Mirror filenames follow `{page_id}-{slug}.md`.
   - `docs/maintenance/confluence-sync-manifest.json` lists every mirror with matching `local_path`, versions, and `layer2_targets`.
   - `docs/history/context/confluence/README.md` indexes manifest pages.
   - Engineering spike docs with a Confluence sync ledger (for example ADR-46) match manifest `confluence_version` after an intentional wiki push (`sync_status: synced`). Use `pending` when repo mirrors are ahead of wiki per project-guidelines #92.

3. After a live Confluence push, refresh mirror bodies from the published wiki content (or authoritative repo spike sections), bump manifest versions, and set `sync_status: synced` in the same session. Do not leave truncated wiki pages; republish the full body before marking synced.

4. **Cleanup only after audit passes:**

   ```bash
   "$HYGIENE" cleanup
   ```

   Removes `__pycache__` always; removes `*-cf-out.md` only when step 1 marked them STALE. Aborts when promotion is still pending.

**After Step 2.65 completes, immediately continue to Step 2.64.**

## Step 2.64: Review staging hygiene

When this session wrote or updated review staging docs under `{reviews_dir}/` (resolve from `.ai-playbook/facts.md` via `using-skills` Step 0), validate each session-touched staging file before `docs-branch` sync. Cover every review-staging kind: basename matches `*review*.md`, or PR staging names (`*-PR-*` / `PR-<n>-...` per `review-staging`), or any path accepted by the validator's `is_staging_review_path`. Do not filter to `*review*.md` alone; that misses PR staging.

```bash
VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
# Only paths this session created or edited (do not glob all historical rounds)
for f in <session-touched-staging-paths>; do
  [ -f "$f" ] || continue
  python3 "$VALIDATOR" --hard "$f" || exit 1
done
```

On failure: complete the staging doc per `review-staging` (Metadata, Review Statistics, Findings with Comment/Analysis) before continuing. Do not sync stub staging docs to the orphan `docs` branch.

**After Step 2.64 completes, immediately continue to Step 2.**

## Step 2: Preserve Gitignored Docs and Instructions

Invoke the `docs-branch` skill now. It will:
1. Snapshot all configured gitignored shadow paths (`docs/`, `.github/docs/`, `.ai-playbook/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT.md`, plus repo `extra_shadow_dirs`) while leaving the live checkout on the current branch.
2. Sync those files to the permanent `docs` orphan branch through a temporary `git worktree`, creating it if it doesn't exist.

**After docs-branch completes, immediately continue to Step 2.5.** Do not stop or wait for user input; the workflow is continuous and all steps should execute in sequence.

> All implementation details, edge cases, and the full bash script live in `docs-branch/SKILL.md`. Refer there for the canonical script when executing.

**After docs-branch completes, verify gitignored files are still on disk:**
```bash
# Read gitignored doc paths from .ai-playbook/facts.md TOML (using-skills Step 0); include common candidates:
for p in docs/tmp docs/history/reviews docs/reviews docs/personal .ai-playbook/facts.md AGENTS.md CLAUDE.md GEMINI.md COPILOT.md; do
  [ -e "$p" ] && git check-ignore -q "$p" && echo "OK: $p" || true
done
```

**Verify untracked WIP survived** (docs-branch keeps the live checkout on the current branch):

```bash
# Before docs-branch (optional but recommended):
git ls-files --others --exclude-standard > /tmp/docs-branch-untracked-manifest.$$
# After docs-branch:
while IFS= read -r f; do
  [ -e "$f" ] || echo "MISSING untracked: $f"
done < /tmp/docs-branch-untracked-manifest.$$
rm -f /tmp/docs-branch-untracked-manifest.$$
```

If any path is missing, restore from docs-branch `UNTRACKED_BACKUP` or Cursor Local History before committing.

If any gitignored path that existed before docs-branch is now missing, restore it immediately from the `docs` orphan branch before proceeding (docs-branch add-only sync restores missing shadow files automatically, including reviews; use manual restore only when that step did not run):
```bash
git checkout refs/heads/docs -- <missing-path>
git restore --staged <missing-path>
```

## Step 2.5: Roll Back Formatting-Only Changes

Before committing, identify and revert any **uncommitted** files where the only diff is formatting (whitespace, trailing commas, blank lines, import reordering, line wrapping, or collapsing multi-line expressions to a single line) with no logic, naming, or structural change.

**This applies to ALL uncommitted files, including pre-existing local changes not made in this session.**

1. List uncommitted changed files: `git diff --name-only && git diff --cached --name-only`.
2. For each file, visually inspect `git diff -- <file>`. Revert if **every** hunk is one of:
   - whitespace / blank line changes
   - line wrapping / unwrapping (same tokens, different line breaks)
   - trailing commas added/removed
   - import reordering
   - end-of-file newline added
   - collapsing or expanding multi-line expressions with no token change

   Do **not** rely solely on `git diff -w --ignore-blank-lines`; that flag misses ktlint reformatting such as line splits and trailing commas.
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

5. **Doc-hierarchy migration or doc-only PRs**
   - If the session ran **doc-hierarchy-migrate** verify (`step6` or `full`) successfully, do not add PR **Test plan** items for that gate as unchecked reviewer tasks. The gate is an implementer checkpoint from the skill install, not a repo-local script.
   - When updating the PR description, use the [PR checklist](../doc-hierarchy/company-decisions.md#pr-checklist-team-proposal-accepted) only unless the reviewer asked for more; follow [PR description rules](../doc-hierarchy/company-decisions.md#pr-description-rules).
   - Mark session-verified checks `[x]` or omit them; never leave implementer-completed verification as unchecked homework.

Do not assume the `learn` step already wired these references correctly. Re-check the final diff before staging and commit any missing cross-links as part of cleanup.

## Step 2.7: Sensitive Data and Personal Information Scan

Before committing, scan all uncommitted changes (including untracked files) for sensitive or personal information that must not appear in public repositories.

**Check for:**
- Hardcoded absolute paths containing usernames (e.g., `<home>/username/` paths)
- Organization-specific domains, internal URLs, or service names
- Employee names, email addresses, or identifiers (except copyright lines in `LICENSE.txt`)
- API keys, tokens, passwords, or credentials
- Project-specific ticket prefixes or internal naming that reveals client/employer identity
- Environment names or internal infrastructure references
- `Co-authored-by:` / `Co-Authored-By:` trailers in commit messages being pushed
- Employer or client brand names in commit subjects (especially in vendored skills)

**How to scan:**
1. List all changed/untracked files: `git status --short`
2. For each file in the diff, grep for patterns:
   ```bash
   git diff --cached -U0 | grep -iE '/Users/|/home/|\.atlassian\.net|@[a-z]+\.(com|io|net)|api[_-]?key|token|password|secret'
   ```
   Also run `public_hygiene_scan_script` from user facts (deny patterns: `public_hygiene_patterns_file`).
3. For untracked files being staged, scan their full content.
4. When a push is planned, audit commits in the push range (`origin/<branch>..HEAD` or the squashed commit about to be pushed):
   ```bash
   git log origin/<branch>..HEAD --format='%B---' | grep -iE 'Co-authored-by|Co-Authored-By|<employer-brand-from-facts>'
   git log origin/<branch>..HEAD --format='%s' | grep -iE '<employer-brand-from-facts>'
   rg -i '<employer-brand-from-facts>' --glob '!**/LICENSE.txt' agents/skills/
   ```
   Resolve employer-brand patterns from the user's facts document; never hardcode them in skill files.

**If found:**
- Replace personal paths with facts-document references or generic placeholders (e.g., `<your-org>.atlassian.net`, `~/Projects/<project>/`)
- Replace internal names with generic equivalents
- Move credentials to `.env` or facts documents (never commit them)
- If the information is in a skill file, externalize **machine-specific** values to facts documents; keep **portable policy constants and workflow thresholds** in the skill body (see `learn` Step 2, Facts vs skill configuration; `agent_workflow_guidelines.md` §50).

**When committing this repository (`skills_repo_path`) or vendored skills:** run `public_hygiene_scan_script` from user facts at the instructions repo root and fix all failures before staging.

**Do NOT commit until all sensitive data is resolved.**

## Step 2.75: Unused import scan (all touched source files)

Before committing, verify every changed or new **source file** from this session has no unused-import diagnostics (or the language equivalent: `using`, `require`, type-only imports, and so on).

1. List touched paths from unstaged, staged, and untracked diffs:
   ```bash
   { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u
   ```
2. From that list, keep paths the IDE or language server can lint. Exclude obvious non-source artifacts (markdown, plain YAML/JSON config, lockfiles, images, binaries, generated stubs under build output). When unsure whether a path is lintable, include it; `ReadLints` skips what it cannot analyze.
3. Run IDE or language-server diagnostics on **every remaining touched path** (for example Cursor `ReadLints` per file or batched by directory). Fix every unused-import-class diagnostic before staging. Common cases:
   - **Java / Kotlin:** unused `import` or static import (including static imports shadowed by instance calls such as `lenient().doAnswer()` vs `import static … doAnswer`).
   - **Python:** unused `import` / `from … import`.
   - **TypeScript / JavaScript:** unused value or type-only `import`.
   - **C#:** unused `using`.
   - **Go / Rust:** unused imports (still run diagnostics even when `go build` / `cargo check` also enforces).
4. When no linter is configured for a touched language, eyeball new or changed import blocks in the diff and remove lines with no references in the file.
5. Re-run diagnostics after fixes until clean on all touched lintable source paths.

Do not stage source files for commit while unused-import diagnostics remain on any touched path from this session.

**After Step 2.75 completes, immediately continue to Step 2.76.**

## Step 2.76: No em dash scan (touched prose files)

Before committing, scan touched prose and instruction files for em dash (U+2014). Policy: `agent_workflow_guidelines.md` §39.

1. From the repo root (or each repo you will commit), run:
   ```bash
   "${CHECK_NO_EM_DASH_SCRIPT:-${HOME}/.ai-playbook/scripts/check-no-em-dash.sh}" touched
   ```
2. The script scans `*.md`, `*.mdc`, and instruction entrypoint filenames among touched paths. Fix every reported line: use a comma, colon, semicolon, period, or parentheses instead of a long dash.
3. Re-run until exit code 0.

Do not stage prose or instruction files while the scan fails.

**After Step 2.76 completes, immediately continue to Step 2.8.**

## Step 2.8: Instruction Size Gate (before commit)

When uncommitted changes touch always-loaded instruction entrypoints (`AGENTS.md`, `CLAUDE.md`, and others listed in `user_facts_path` when present), verify they still fit the context budget after learn compaction.

**Budget:** **30,720 bytes** per instruction entrypoint (same constant as learn Step 6.5).

1. From the repo root, run:
   ```bash
   "${HOME}/.ai-playbook/scripts/check-instruction-size.sh" gate
   ```
   (Override script path only for local testing via `INSTRUCTION_SIZE_CHECK_SCRIPT`.)
2. **Gate behavior:** exits non-zero when an instruction file exceeds the budget **and** has uncommitted changes. Grandfathered over-budget files with no pending edits do not block unrelated commits.
3. On failure: return to learn Step 6.5, compact hybrid bullets to cross-references, move infrequent rules to skills, then re-run **gate** before staging instruction files.

Do not stage instruction entrypoints for commit while **gate** fails.

**After Step 2.8 completes, immediately continue to Step 3.**

## Step 3: Commit Uncommitted Changes

After learn and stash steps complete:

0. **Distinguish session changes from pre-existing local changes.** Only commit changes that were made during this session. If `git status` shows uncommitted files that were not touched by you in this session, ask the user before staging them; they may be in-progress work the user does not want committed yet.
1. Run `git status` and `git diff` (staged + unstaged) to see all changes.
   **Pre-commit guard (post sub-agent git op):** Step 2 `docs-branch` (and any prior sub-agent `git worktree`/`git checkout`/`git stash` operation) can leave the main repo's index/worktree in a REVERTED state relative to HEAD while HEAD stays correct. Before staging, run `git diff --cached --stat`: if it shows large deletions across files you did not edit this iteration (e.g. +73/-1062 across 14 files) OR the test count dropped vs the last known-good count on HEAD, a leaked revert is staged. Run `git reset --hard HEAD`, re-stage only your intended edits, then re-verify. Never use `git add -A`/`git add .` here, or the rollback is swept into the commit. (Witness: 2026-07-23 group-leftover-crypto-warnings r6; see project `development_lessons.md` lesson on this family.)
2. Run `git log --oneline -5` to match existing commit message style.
3. Derive the story key from the current branch name (e.g. `feature/PROJ-1234-...` → `PROJ-1234`). If the branch name contains no story key, use a plain descriptive commit message without a ticket prefix on branches such as `main` or `master`. Ask the user only if the repository convention is unclear and there is no obvious non-ticket fallback.
4. **Before staging any file, verify it is not gitignored:**
   ```bash
   git check-ignore -q <file> && echo "IGNORED, do not stage"
   ```
   If a file appears in `git diff` but is gitignored, it was previously force-tracked. Remove it from tracking first and do **not** commit it on the feature branch:
   ```bash
   git rm --cached <file>
   ```
   Gitignored files belong on the `docs` branch only (handled in Step 2), not on the working feature branch.
4b. **Session-touched project lessons corpus (non-ignored):** After Step 1 (`learn`), if this session created or updated the project lessons file (`docs/maintenance/development_lessons.md`, or `PROJECT_CORPUS_REL` from `lessons_recall.py`) and `git check-ignore` does **not** match it, **stage and commit it on the feature branch** with the other session changes. Untracked (`??`) is not a skip reason. Syncing the same path to the orphan `docs` branch in Step 2 does **not** replace the feature-branch commit. Only gitignored corpora stay docs-branch-only.
5. Stage relevant non-ignored files (including 4b when it applies). Prefer adding specific files by name; never use `git add -A` or `git add .` unless the user explicitly requests it.
6. Write a concise commit message. If there is a story key, prefix with `[<STORY-KEY>]`; otherwise use a plain descriptive subject. Focus on the "why" not the "what".
7. Commit using a HEREDOC. **Never** add `Co-Authored-By:` or `Co-authored-by:` trailers or use `git commit --trailer` for agent attribution. See user `AGENTS.md` (Git Commit Trailer Policy). If your IDE adds co-author trailers automatically, disable agent attribution in its settings.
8. Run `git status` after the commit to confirm success.

### Commit message format

With a story key:

```
git commit -m "$(cat <<'EOF'
[PROJ-1234] <concise description of what and why>
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

This commits any pending skill edits in the skills repository with an auto-generated message. You may pass a custom message as the first argument if the default is not descriptive enough.

## Step 5: Commit Pending Facts and Docs Changes

After committing skills, check whether any facts documents or docs repositories were modified during this session. Each docs directory is its own git repo and must be committed independently.

Resolve paths from the user's facts document:
- `shared_docs_dir`, cross-project guidelines and shared facts
- Project-specific docs directories are determined from the current working project

For each docs git repo that has uncommitted changes:

```bash
cd <docs_dir> && git status --short
```

If there are changes:

```bash
cd <docs_dir> && git add -A && git commit -m "docs: <brief description of what was added/updated>"
```

Do not push. These are local-only docs repositories.

**Common docs repos to check:**
- Shared docs (from facts `shared_docs_dir`)
- Current project's `docs/` directory (if it is a separate git repo)

## Step 6: Release project done lock

**Always run Step 6 before Step 7**, including when Steps 1–5 failed or returned early. This lets a waiting parallel `done` resume.

From the project git root, release with **`DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` from your Step 0 acquire** (re-export from that tool output if the shell lost env). `release-repo` requires those env vars and refuses to load the shared session file:

```bash
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release-repo
```

Equivalent:

```bash
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" \
  "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release
```

If release fails (token mismatch, env missing), run `status` from the project root. When `status` shows free, your hold is already gone (peer `stale-clean` or release); do not source `.ai-playbook/done-lock.session` to “fix” env. When `status` shows `abandoned: yes` with no session fence, run `stale-clean` only if you will re-acquire; ask the user before forcing removal of an **active** lock.

## Step 7: Report outcome to the user

**Never end `/done` silently after diagnostics.** Always send a short summary:

- Project repo: commit hash(es) created, or **working tree clean** at `HEAD` (include `git log -1 --oneline`).
- Skills / shared docs repos: commits created or none.
- Lock: confirm `status` shows **free** after Step 6.
- If `blocked` at Step 0 or learn: state why and what the user should run (`stale-clean`, fix corpus, retry).

## Integration Points

### With `bootstrap-ai-playbook` skill
Writes and refreshes `.ai-playbook/facts.md` when Terms triggers fire (`using-skills` Step 0). This skill reads `{tmp_dir}` and other gitignored doc paths from that file for Step 2.1 (`docs-branch`).

### With `execute-plan` skill
Invoked as a sub-agent after **each** completed plan task (per-task commit) and after **each** review/fix iteration (per-iteration commit). The orchestrator passes the plan path, task or review-round context, suggested commit subject, and **sub-agent log paths** under resolved `{tmp_dir}/execute-plan/<plan-slug>/`.

**Before Step 1 (learn):** read only the **preceding-step** log(s) the orchestrator listed: for per-task `done`, the implement log from Step 1.2; for review-iteration `done`, the current round's review log (Step 3.1) and address log (Step 3.3) when it ran. Do not read full session history. Use log content as primary input for `learn`, not the orchestrator chat summary. If a required preceding-step log is missing, release the Step 0 lock (Step 6), return `blocked`, and do not commit. See `execute-plan/agent-logs.md`.

Each execute-plan `done` sub-agent still runs Step 0 and Step 6. Sequential tasks in one orchestrator usually acquire immediately after the prior release; parallel chats on the same repo wait on **wait-acquire**.

### With `review-staging` skill
Step 2.64 validates session-touched staging docs under `{reviews_dir}/` before docs-branch sync. Include `*review*.md`, PR staging (`*-PR-*` / `PR-<n>-...`), and any path accepted by `is_staging_review_path` (not only `*review*.md` or `*-r*.md`). Complete Metadata, Review Statistics, and Findings with Comment/Analysis before continuing; do not sync stub staging docs.

## Rules

- Always acquire the Step 0 project lock before learn or any project-side commit steps; always release it in Step 6 (`release-repo` from project git root).
- Never skip Step 6 or Step 7, even for "just commit" or empty working tree runs.
- Always run learn before committing; lessons must be captured first.
- Never skip the learn step even if the user says "just commit".
- Invoke `docs-branch` skill for all docs/instructions preservation; do not inline the stash or branch logic here.
- Run Step 2.65 (Confluence mirror validate, audit-cf-out promotion gate, ephemeral `docs/tmp` cleanup) before `docs-branch` when the manifest exists or the session touched Confluence mirrors, wiki pages, or ephemeral publish snapshots.
- Always verify that new or revised reusable docs, reference material, and explanatory artifacts added in the session are referenced from instructions or related canonical docs where future agents will need them.
- Never stage or commit a file that is gitignored, even if it appears in `git diff` (it was previously force-tracked). Use `git rm --cached` to remove it from tracking; do not commit it on the feature branch.
- Never skip a session-touched, non-gitignored project lessons corpus (`development_lessons.md`) just because it is untracked or already synced to the orphan `docs` branch; commit it on the feature branch (Step 3 item 4b).
- Never add `Co-Authored-By:` or `Co-authored-by:` trailers or use `git commit --trailer` for agent attribution. See user `AGENTS.md` (Git Commit Trailer Policy). Disable automatic agent attribution in IDE settings when present.
- Never use `--no-verify`.
- Never commit secrets, PII files (`.env`, credential files), or personal/org-specific information into public repositories.
- Never hardcode personal paths, org domains, or project-specific identifiers in skill files; externalize those to facts documents. Portable workflow policy and numeric thresholds stay in the skill (see `learn` Step 2, Facts vs skill configuration).
- If the branch has no story key, use a plain descriptive commit message on branches such as `main` or `master`; ask only when the repository convention is unclear.
