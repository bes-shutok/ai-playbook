---
name: github-pr-workflow
description: >
  GitHub PR workflow and shared GitHub PR operations — use as the common GitHub PR URL protocol for active review and passive review skills, and as the primary skill for PR descriptions, PR stats, splitting a branch diff into PR chunks, creating GitHub PR branches, rebasing stacked PRs after parent squash-merge, and creating squashed PR branches. Trigger phrases — "GitHub PR URL", "write the PR description", "PR stats", "split PR", "PR chunks", "split branch", "split the diff", "create PRs", "create the branches", "rebase pr", "rebase on pre-release", "squash", "squashed branch", "squashed PR", "GitHub PR workflow".
---

# GitHub PR Workflow

**Writing:** Follow `agent_workflow_guidelines.md` §45. PR summaries use plain English (e.g. "API response shape", not "wire contract"). Add `## Terms` when using 3+ project-specific words.

Rules for PR description/stats authoring, splitting a branch diff into appropriately sized PR chunks, creating the actual GitHub PR branches, rebasing stacked PRs, and shared GitHub PR operations used by review skills.

**Prerequisite:** GitHub CLI (`gh`) installed and authenticated. Commands below use `gh` syntax.

## Routing Boundary

This skill owns **GitHub PR mechanics** and reusable GitHub API details.

Use these routing rules before acting:

| User intent | Primary skill | This skill provides |
|---|---|---|
| Fresh review, e.g. "let's review <PR URL>" | `doing-code-review` | Fetch PR metadata, files, diff, existing comments, and post review |
| Existing feedback, e.g. "address comments in <PR URL>" | `receiving-code-review` | Fetch review threads, reply to threads, resolve bot threads |
| PR administration, e.g. description, stats, split, create, squash, rebase | `github-pr-workflow` | Owns the full task |

Do not use this skill alone to judge review feedback or produce review findings. Delegate judgment to `doing-code-review` for active review and `receiving-code-review` for passive review feedback.

## Doc migration PR descriptions

When the PR is a doc-hierarchy migration or doc-only Layer 1/2/3 update on a company service repo:

1. Use the [documentation impact checklist](../doc-hierarchy/company-decisions.md#pr-checklist-team-proposal-accepted) only — do not expand into a layout inventory unless the reviewer asks.
2. Follow [PR description rules](../doc-hierarchy/company-decisions.md#pr-description-rules): no duplicate unchecked verify-gate TODOs when the session already ran `verify-doc-hierarchy.sh full` from the skill install; never imply a repo-local verify script.
3. `done` skill applies the same rules when updating PR bodies after implementation.

## Shared GitHub PR Operations

Use these primitives from review skills instead of duplicating GitHub details there.

### Resolve PR context
```bash
# Current branch PR
gh pr list --head $(git branch --show-current) --json number,title,url,baseRefName,headRefName

# PR URL or number
gh pr view <PR_URL_OR_NUMBER> --json number,title,url,baseRefName,headRefName,author,state,mergeable,headRefOid
```

### Fetch changed files and diff
```bash
gh pr view <PR_URL_OR_NUMBER> --json files --jq '.files[].path'
gh pr diff <PR_URL_OR_NUMBER>
```

For local branch work, use:
```bash
git diff --name-only <base>...<work>
git diff <base>...<work>
```

### Fetch existing review comments before active review
Use this before posting new active-review findings so duplicate findings can be dropped:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate
```

### Post active review comments
Use this after `doing-code-review` has produced assessed, deduplicated findings:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/reviews \
  --method POST \
  --input review.json
```

`review.json` shape:
```json
{
  "event": "COMMENT",
  "body": "",
  "comments": [
    {
      "path": "src/File.java",
      "line": 123,
      "side": "RIGHT",
      "body": "Finding text"
    }
  ]
}
```

Post with `event: "COMMENT"` unless `doing-code-review` marks a Critical or High severity issue with clear production risk.

### Fetch review threads for passive review feedback
Use this when `receiving-code-review` needs to triage existing Copilot or human reviewer threads:
```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 20) {
            nodes {
              id
              author { login }
              body
              path
              line
              outdated
              createdAt
            }
          }
        }
      }
    }
  }
}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
threads = data['data']['repository']['pullRequest']['reviewThreads']['nodes']
for i, thread in enumerate(threads):
    comments = thread['comments']['nodes']
    if not comments:
        continue
    first = comments[0]
    print(f'=== Thread {i+1} | id={thread[\"id\"]} | resolved={thread[\"isResolved\"]} | outdated={first.get(\"outdated\")} ===')
    print(f'Author: {first[\"author\"][\"login\"]} | Path: {first.get(\"path\")} | Line: {first.get(\"line\")}')
    print(f'Comment ID: {first[\"id\"]}')
    print(f'Body: {first[\"body\"][:500]}')
    print()
"
```

Replace `OWNER`, `REPO`, and `PR_NUMBER` with values from the PR context.

### Reply to review threads
Reply in the thread, not as a top-level PR comment:
```bash
gh api graphql -f query='mutation {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: "PRRT_...",
    body: "Fixed: <one-sentence description of the change made, or why no change was needed>"
  }) { comment { id } }
}'
```

Reply guidelines:
- Write in plain, direct language.
- Do not use bullet points, numbered lists, em dashes, or AI-typical phrasing in reply text.
- For fixes: describe what changed and reference the file/line if useful.
- For false positives: explain why the code is correct, citing API signatures, versions, or guidelines as evidence.
- For PR-description-only updates: state that the description was updated to match the implementation.

### Resolve review threads
Resolve only bot or automated threads after replying:
```bash
gh api graphql -f query='mutation {
  resolveReviewThread(input: { threadId: "PRRT_..." }) {
    thread { isResolved }
  }
}'
```

Never resolve threads opened by human reviewers. The author resolves their own threads. Never silently resolve any thread; every resolved bot thread must have a reply first.

To get all unresolved thread IDs at once:
```bash
gh api graphql -f query='{ repository(owner:"OWNER", name:"REPO") { pullRequest(number:N) { reviewThreads(first:100) { nodes { id isResolved } } } } }' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved==false)) | .[].id'
```

## Creating a Squashed PR Branch

Use when the user asks to squash a multi-commit feature branch into a single clean commit for PR review (e.g. with a `-squashed` postfix).

**Scope:** squash only commits ahead of the remote base (`origin/<base>..HEAD`). On the current branch, `git reset --soft origin/<base>` then one commit is the default. Do not rewrite the entire repository history with `git checkout --orphan` unless the user explicitly asks for a full history squash.

### Steps
1. Identify the base branch (check `git branch -a`; default may be `master` not `main`). Fetch and confirm the remote tip before squashing.
   - **Stacked PRs:** the soft-reset parent must be the **immediate parent feature branch** (the branch the story PR will target), not `pre-release` or an older ancestor. Before committing, verify scope: `git diff --stat origin/<parent>..HEAD` should match the current story only (file count/order-of-magnitude lines), not sibling work from another stacked branch.
   - If `git reset --hard` is blocked by workspace policy, reparent with `git commit-tree <tree> -p origin/<parent>` instead.
2. Detect format-only files — exclude them from the commit to avoid cluttering the PR:
   ```bash
   git diff -w --ignore-blank-lines <base>..HEAD -- <file>
   # empty output = formatting only; non-empty = real change
   ```
3. Identify gitignored LLM artifacts (`docs/`, `AGENTS.md`, `CLAUDE.md`, `.claude/`): must NOT be committed; restore to working tree after branch creation.
4. Create the new branch from the base: `git checkout -b <new-branch> origin/<base>`.
5. Cherry-pick only real-change files: `git checkout <source-branch> -- <file1> <file2> ...`.
6. Apply any `.gitignore` updates (e.g. add `### LLM Agent Artifacts ###` block) and stage them.
7. Commit everything in a single squashed commit with a clean, feature-focused message.
8. Push and open a PR against the base branch with `gh pr create --base <base>`.
9. When the user names teammates for a PR, default to **`gh pr edit --add-reviewer`** (or `--reviewer` on create). Use `--assignee` only when they explicitly say assignee/owner.

### Gitignore block for LLM artifacts
```
### LLM Agent Artifacts ###
/docs/
/AGENTS.md
/CLAUDE.md
.claude/
```

## Rebasing a Stacked Child PR After Parent Squash-Merge
When the parent PR has been squash-merged into the target branch, use `git rebase --onto <target> <parent-branch>` — NOT `git rebase <target>` — to exclude already-squashed parent commits and replay only the child's own commits.

If conflicts remain (squash diff ≠ cumulative individual diffs), resolve by taking HEAD (`git checkout --ours`): the squash already contains the correct final state. For `modify/delete` conflicts on files deleted by the squash, `git rm` them. Empty commits (whose changes are fully covered by the squash) are dropped automatically by git and can be ignored.

## Project-Specific PR Templates That Gate Automation

Some repos use PR templates whose fields are parsed by downstream CI to decide whether to take additional automated actions (redeploy, restart, notify). Custom PR descriptions that skip the template can silently disable that automation: the field defaults to "off" and the PR merges with no downstream effect, while the author assumes the action took place.

Before writing a custom description against an unfamiliar repo:

1. Check `.github/pull_request_template.md` and any default body the new-PR page pre-populates.
2. Identify which fields drive automation (typically a "Restart Required?" checkbox and a machine-readable metadata block at the bottom of the body).
3. Either use the template directly, or, if a custom human-readable description is necessary, preserve the machine-readable metadata block verbatim. The block is the canonical input the pipeline parses; the visible checkbox is the fallback.

For company work repositories, see `company_projects_root/.ai-playbook/redeploy_and_restart_workflow.md` (path in `~/.ai-playbook/facts.md`) for the full mechanism: `config-repo-prod` PR template fields, the `configRedeployPipeline` Jenkins flow, Argo CD reconciliation semantics, and the failure modes (custom description silently bypassing the pipeline; manual autodeploy-misc UI returning success without committing yaml; squash-merge with a cleaned commit body stripping the template metadata).

### Warn at PR creation and at merge time

For PRs against repos with PR-metadata-driven CI (notably `config-repo-prod`), the pipeline reads the template fields from the **merge commit body**, not the PR description via API. A squash-merge with a cleaned commit body silently disables the automation even when the PR template was filled correctly. The assistant must:

1. At PR creation: when you create or recommend opening a PR against `config-repo-prod` (or any repo where the user has indicated the merge commit body drives CI), tell the user in plain text: **do not squash-merge with a cleaned commit message body**. Either use a regular merge, or in the squash-merge dialog leave the body intact so the metadata block survives.
2. At merge time: if the user signals they are about to merge such a PR ("I'll merge now", "merging this", asking for the merge URL, etc.), repeat the warning before they click. The warning is load-bearing for users who squash-merge by habit; it is not optional.

## PR Descriptions and Stats
- Write the summary section in plain prose, not bullet lists. Explain what the PR does in one paragraph as if talking to a teammate: what the change enables, why it was needed, and how it fits the existing system. Use simple language. Avoid jargon.
- Follow the prose summary with a "flow in one line" sentence showing the data/control path end-to-end (e.g. `trigger → fetch phone → format → send`). This makes the purpose immediately clear without reading the full diff.
- Only use bullet lists for enumerated specifics (files changed, config keys added, API endpoints). Do not use bullets for the main description.
- For PR descriptions against a non-default base branch (for example stacked PRs), describe only the delta visible from that base; do not frame changes as restorations or mention work that exists only below the base branch.
- When drafting a PR description, omit verification sections unless the user explicitly asks for verification details or the repository template requires them.
- When a user asks for PR stats, prefer concise branch-vs-base counts (for example commits plus doc/non-doc file counts) over full file-change or insertion/deletion totals unless the user explicitly asks for churn metrics.
- Never reference gitignored files (e.g. `AGENTS.md`, `CLAUDE.md`, `docs/`) in PR descriptions, commit messages, or review replies — they do not appear in the diff and cause spurious review comments. Only mention files that are tracked and visible in the PR.

## PR Chunk Splitting
When asked to split a branch diff against a base branch (for example `pre-release`) into multiple PRs:

### Sizing Rules
- Target fewer than 10 non-doc files per chunk; hard max is 15 non-doc files.
- Doc-only files (`docs/**`, `AGENTS.md`, `README.md`) do not count toward the file limit but should be distributed to the chunk that owns the behavior they document.
- Distribute chunks as evenly as possible — avoid one oversized chunk paired with several tiny ones.

### Grouping Rules
- Each chunk must have a single clear change reason (feature addition, refactor, infra/config, dependency upgrade, etc.).
- Minimize file overlap between chunks — no file should appear in two chunks.
- Identify "ride-along" changes (infrastructure, refactoring, dependency upgrades not tied to a specific feature) and group them into their own dedicated chunk.
- When a core feature set is tightly coupled and cannot be split below the hard max without breaking the feature, say so explicitly and recommend opening a single PR rather than splitting artificially.

### Output Format
When presenting a split plan:
1. List each chunk with: chunk number, change reason, non-doc file count, and file list.
2. Show chunk sizes side-by-side so the user can judge evenness at a glance.
3. If chunks form a dependency order (stacked PRs targeting each other rather than the base), state the recommended merge order explicitly.
4. Flag any files that could reasonably fit in multiple chunks and explain the placement choice.

## PR Branch Creation
When the user asks to actually create the PR branches (not just plan them):

### Pre-flight Checklist
- Run `git diff --name-only <base>...<work>` and build a complete file inventory. Every file — including `README.md` and other root-level tracked files — must be assigned to exactly one chunk. Do not skip files simply because they are documentation or because the plan omitted them.
- Identify deleted files separately: `git diff --diff-filter=D --name-only <base>...<work>`. `git checkout <branch> -- <files>` aborts on the first deleted file and silently skips all remaining files in the list — deleted files must be staged via `git rm` in a separate step.
- Check for compile-time dependencies between chunks: if a file in chunk N+1 references types generated from a file in chunk N+1's plan but that generator lives in chunk N, move the generator to chunk N. Verify this by running the project's compile command after checking out each chunk's files.
- Verify GitHub CLI authentication before starting: `gh auth status`. If not authenticated, surface this immediately rather than discovering it at PR creation time.

### Execution Steps (per chunk)
1. Create the branch from its base (`git checkout -b <branch> <base>`).
2. Check out non-deleted files: `git checkout <work> -- <file1> <file2> ...`.
3. Stage deleted files: `git rm <deleted-file>` for each file deleted in the work branch.
4. Compile: run the project's compile command. Fix dependency issues before proceeding.
5. Run fast unit tests to validate.
6. Commit and push.

### Completion Gate
- All K PR branches must be pushed AND all K GitHub PRs must be created before the task is reported complete.
- After creating PRs, verify `git diff <base>...<work> -- .` shows no remaining unaccounted files.
