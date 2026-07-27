---
name: review-loop
description: >
  Orchestrate repeat review-fix-done cycles on the current branch until a fresh code review
  reports zero unresolved blocking findings before any fixes. Use when the user asks to run a review loop,
  keep reviewing until clean, or repeat doing-code-review + receiving-code-review + done.
  Trigger phrases: "review loop", "review-loop", "until clean", "keep reviewing until clean",
  "review fix done loop". Not for execute-plan Phase 3 (use execute-plan) or one-shot review
  (use doing-code-review only).
---

# Review loop

Run **fresh review → fix (if needed) → done → repeat** on the **current branch** until exit criteria are met.

## Boundary

| Use this skill | Use instead |
|----------------|-------------|
| Standalone "loop until clean" on current branch | `execute-plan` Phase 3 (plan-scoped only) |
| | `doing-code-review` (one-shot review, no loop) |
| | `receiving-code-review` (address existing PR threads) |

## Resolve scope (Step 0)

From the project git root:

```bash
HEAD_BRANCH=$(git branch --show-current)
BASE_BRANCH="${BASE_BRANCH:-}"   # user override, else detect below
```

**Base branch** (pick first that applies):

1. User named it (`against master`, `vs pre-release`, PR base URL).
2. Open PR for `HEAD_BRANCH`: use PR base from `gh pr view` / `github-pr-workflow`.
3. Repo default integration branch (`pre-release`, `main`, or `master` per project `AGENTS.md`).

**Diff scope (every review round):** `git diff ${BASE_BRANCH}...HEAD` on **committed** `HEAD` only. Do not review uncommitted fixes as proof the round is clean; commit first, then start the next round.

Read `{reviews_dir}` and `{tmp_dir}` from `.ai-playbook/facts.md` (see `using-skills` Step 0).

## One iteration

| Step | Skill | What happens |
|------|-------|----------------|
| 1 | `doing-code-review` | Branch review mode; staging doc **before** reporting to user |
| 2 | Triage | Count findings still `pending` with `blocking: true` |
| 3 | `receiving-code-review` | Only if step 2 count > 0; fix or `drop` each finding; update staging doc statuses |
| 4 | `done` | learn → docs-branch → commit (authorized per iteration) |

**Do not** merge step 3 fixes into the same round's step 1 verdict. Step 1's output is **provisional findings before fixes**.

## Staging doc (required every round)

Path pattern:

```text
{reviews_dir}/YYYY-MM-DD-branch-review-<branch-slug>-r<N>.md
```

`<branch-slug>`: current branch with `/` → `-`, lowercased (e.g. `PROJ-1234-segments-docs-design-rfc`).

Each doc **must** include (full `review-staging` hierarchy; **no stub or verdict-only files**):

1. **Metadata** table (review type, base/head SHAs, round, domains, focus, `Status: STAGED`)
2. **Base / head** SHAs or branch names
3. **`## Review Statistics`** per `review-staging` (Panel with Solo/Echo, Counts, Deduplication groups, Discarded with Pattern, Severity calibration, Triage outcomes; required even on clear rounds)
4. **Findings accepted for fix** table when unresolved blocking findings exist
5. **`## Findings`** with one `### F<N>` per staged finding; each must have `#### Comment` and `#### Analysis` (not bullet-only summaries)
6. **`## Fixes applied (r<N>)`** with commit SHA when step 3 ran
7. **Verdict for this round (before fixes):** `N blocking findings accepted for fix` OR `0 unresolved blocking findings; clear round`
8. **Loop exit criterion** (see below); never write "0 remaining after fixes" as the round verdict

Sync gitignored staging to `docs` branch via `done` → `docs-branch` (same as other reviews).

**Mechanical gate (before reporting round verdict):** run the review-staging validator on the staging path and confirm the `.stats.json` sidecar exists; do not report the round complete until both pass:

```bash
VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
python3 "$VALIDATOR" --hard "$STAGING_PATH"
```

Cursor hooks also warn via `postToolUse` after staging writes, block review-loop commits when validation fails, and may inject a `stop` follow-up if the newest round file is still a stub.

## Exit criteria (default)

Stop only when a fresh review of committed `HEAD` reports zero unresolved blocking findings and no fixes were applied in that iteration.

| Signal | Valid exit? |
|--------|-------------|
| Fresh review -> 0 unresolved blocking -> no step 3 needed | **Yes** |
| Fixed issues → grep clean / "looks good" | **No** |
| Same round: review → fix → "0 open" | **No** |
| Postfix verification in the same round | **No** |

## Limits

| Limit | Default | On exceed |
|-------|---------|-----------|
| `max_full_panel_rounds` | **5** | Stop; list unresolved blocking findings; ask user before a sixth |
| `max_escalations` | **1 per active run** | Prohibit a second escalation in the same run |

Never use commit subjects like `Close review loop` or `Review complete` until exit criteria are met.

## Orchestration rules

1. **Continuous iterations:** after `done` succeeds, increment `review_round` and return to step 1 unless exit criteria or `max_rounds` hit.
2. **Sub-agents:** launch `doing-code-review` with the panel from `review-panel-selection.md`; do not replace with inline grep.
3. **Targeted revisions:** after fixes, launch blind `correctness-completeness` plus every distinct worker that owned a finding or whose domain the fixes affected. If all five are selected, count a full-panel round.
4. **Commits:** only `done` commits; one iteration -> one commit when fixes ran.
5. **Push:** requires explicit user instruction.
6. **PR mode:** if user gave a PR URL, still write staging docs; optional post to PR via `doing-code-review` Direct mode.

## Anti-patterns

- Treating post-fix cleanliness as loop exit
- Skipping staging doc on clean rounds
- **Writing abbreviated or stub staging docs** (verdict-only, themes table without per-finding Comment/Analysis, or omitting Review Statistics) to save time during autonomous loops
- Stopping after first fix pass without a **new** step 1
- Reviewing `git diff` working tree to claim round N is clean while fixes are uncommitted
- Batching multiple iterations into one commit
- Reopening a clear round because of late non-blocking noise.

## Quick prompt (user-facing)

```text
review-loop on current branch vs <base>. Run a full review, then targeted follow-ups after fixes, until one fresh review finds zero unresolved blocking findings. Max 5 full-panel rounds.
```

## Integration Points

### Consumes `doing-code-review` skill
Step 1 each round: branch review mode; staging doc before reporting. Diff scope is committed `BASE...HEAD` only.

### Consumes `receiving-code-review` skill
Step 3 when blocking findings remain: triage and fix; update staging statuses.

### Consumes `done` skill
Step 4 each iteration: learn → docs-branch → commit (authorized per iteration). Syncs gitignored staging via docs-branch.

### Consumes `review-staging` skill
Every round writes a full staging doc (Metadata, Review Statistics, Findings with Comment/Analysis). Clear rounds still require statistics. Run the review-staging validator before reporting the round verdict.

### Boundary vs `execute-plan` skill
Use this skill for standalone branch hygiene until one fresh blocking-clean review. Use `execute-plan` Phase 3 for plan-scoped loops.
