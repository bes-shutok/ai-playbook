---
name: review-loop
description: >
  Orchestrate repeat review-fix-done cycles on the current branch until a fresh code review
  reports zero unresolved blocking findings before any fixes. Use when the user asks to run a review loop,
  keep reviewing until clean, or repeat doing-code-review + receiving-review + done.
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
| | `receiving-review` (address existing PR threads) |

## Resolve scope (Step 0)

From the project git root:

```bash
HEAD_BRANCH=$(git branch --show-current)
BASE_BRANCH="${BASE_BRANCH:-}"   # user override, else detect below
```

Read `{reviews_dir}`, `{tmp_dir}`, and `review_large_diff_bytes` from `.ai-playbook/facts.md` (opening TOML block; same source as `using-skills` Step 0). Absent `review_large_diff_bytes` ⇒ default `10240`.

**Base branch** (pick first that applies):

1. User named it (`against master`, PR base URL); unambiguous.
2. Open PR for `HEAD_BRANCH`: use PR base from `gh pr view` / `github-pr-workflow`; unambiguous.
3. Neither applies: resolve to the repo default integration branch (`main` or `master` per project `AGENTS.md`). Then, in an **interactive top-level session**, ask the user to confirm that base before round 1; in a **non-interactive / sub-agent context (risk-F1)** (invoked as a sub-agent of `execute-plan` Phase 3 or in a session with no user at the console, e.g. CI/scheduled), accept the resolved default without prompting. Either way, **record the resolved base + reason in the staging-doc Metadata** (for example `Base resolved non-interactively: main (repo default; no PR/arg, autonomous sub-agent)`) so the resolution is auditable rather than silent.

If `git diff ${BASE_BRANCH}...HEAD | wc -c` exceeds `review_large_diff_bytes` (default 10240), the round-1 `doing-code-review` launch confirms the basis with the user (interactive) or records it in Metadata (non-interactive).

**Diff scope (every review round):** `git diff ${BASE_BRANCH}...HEAD` on **committed** `HEAD` only. Do not review uncommitted fixes as proof the round is clean; commit first, then start the next round.

**Re-resolve the file set every round (required):** at the start of Step 1 in *each* round, re-run `git diff --name-only ${BASE_BRANCH}...HEAD` (committed mode) or `git status --short` (working-tree mode) and confirm the file list matches what this round intends to review. Do not cache the file set from round 1. A loop mutates the tree between rounds (fixes applied, files added by `learn`/`done`, partner edits), so a round-1 snapshot goes stale and silently drops new/changed files from later rounds, which produces a false "clean" exit on a partial review. If the file count changed since the prior round, the new files are in scope for the fresh review even if they bundle a different concern than the original change; do not dismiss them as out-of-scope without recording why.

## One iteration

| Step | Skill | What happens |
|------|-------|----------------|
| 1 | `doing-code-review` | Branch review mode; staging doc **before** reporting to user |
| 2 | Triage | Count findings still `pending` with `blocking: true` |
| 3 | `receiving-review` | Only if step 2 count > 0; fix or `drop` each finding; update staging doc statuses; after fixes land, run the **Generalize-on-fix** step from `receiving-review` |
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

## Soften / regression watchlist (cross-round)

Maintain a **soften watchlist** for the active loop run (session tmp or the latest staging doc section `### Soften watchlist`).

Add an entry when **any** of these happen after a finding was staged as `fixed` / `done`:

- A later commit **reverts** the fix (or restores the prior behavior) with rationale such as "soften", "keep X", "intentional", or partner pushback
- Triage marks the finding `dropped` / `deferred` **after** a fix commit already landed
- The partner explicitly declines a fix that was already implemented

Each watchlist row: `round`, finding id or pattern, anchor path, one-line prior fix, one-line soften reason, `status` (`open` | `reaffirmed` | `restaged`).

**Every subsequent `doing-code-review` round** (full or focused) must:

1. Pass the open watchlist into worker prompts.
2. For each open item, either **re-stage** (behavior still wrong / soften was incorrect) or **reaffirm** (still intentional; record one-line reason in the new staging doc).
3. Leave `open` items only when the owning worker was not launched this round; then the next round that launches that worker must close them.

Do **not** treat a prior soften as "already reviewed; skip." Softens are the main source of silent reintroduction (example: exception-ownership fix reverted same day).

## Exit criteria (default)

Stop only when **all** of the following hold on a fresh review of committed `HEAD`:

1. Zero unresolved findings with `blocking: true`
2. No fixes were applied in that iteration
3. Every soften-watchlist item is `reaffirmed` or `restaged` (then fixed or explicitly dropped with partner confirmation) in that same fresh round or an earlier round of this run whose tip digest for the watchlist anchors is unchanged
4. **Design-simplicity coverage before exit:** if the clear-candidate round used `panel_mode: focused` and omitted `design-simplicity`, run one more pass that includes `design-simplicity` (hybrid is enough: correctness + design-simplicity + any other owners still needed). Skip this extra pass only when the immediately preceding round in this run was a **full** panel that already completed `design-simplicity` on the same tip digest.

| Signal | Valid exit? |
|--------|-------------|
| Fresh review -> 0 unresolved blocking -> no step 3 -> watchlist closed -> design-simplicity covered | **Yes** |
| Fixed issues → grep clean / "looks good" | **No** |
| Same round: review → fix → "0 open" | **No** |
| Postfix verification in the same round | **No** |
| Focused docs/risk-only clear round with open softens or no design-simplicity since last full panel | **No** |

## Limits

| Limit | Default | On exceed |
|-------|---------|-----------|
| `max_full_panel_rounds` | **5** | Stop; list unresolved blocking findings; ask user before a sixth |
| `max_escalations` | **1 per active run** | Prohibit a second escalation in the same run |

Never use commit subjects like `Close review loop` or `Review complete` until exit criteria are met.

## Orchestration rules

1. **Continuous iterations:** after `done` succeeds, increment `review_round` and return to step 1 unless exit criteria or `max_rounds` hit.
2. **Sub-agents:** launch `doing-code-review` with the panel from `review-panel-selection.md`; do not replace with inline grep.
3. **Targeted revisions:** after fixes, launch blind `correctness-completeness` plus every distinct worker that owned a finding or whose domain the fixes affected. If all five are selected, count a full-panel round. When the soften watchlist has `open` items, also launch the worker that owns each open pattern (see `review-panel-selection.md` tiered ownership).
4. **Exit hybrid:** before accepting a focused clear round as loop exit, ensure `design-simplicity` ran on the current tip digest (see Exit criteria item 4). Do not exit on contract-docs/risk-only cleanliness alone after architecture-relevant code landed earlier in the branch.
5. **Commits:** only `done` commits; one iteration -> one commit when fixes ran.
6. **Push:** requires explicit user instruction.
7. **PR mode:** if user gave a PR URL, still write staging docs; optional post to PR via `doing-code-review` Direct mode.

## Anti-patterns

- Treating post-fix cleanliness as loop exit
- Skipping staging doc on clean rounds
- **Writing abbreviated or stub staging docs** (verdict-only, themes table without per-finding Comment/Analysis, or omitting Review Statistics) to save time during autonomous loops
- Stopping after first fix pass without a **new** step 1
- Reviewing `git diff` working tree to claim round N is clean while fixes are uncommitted
- Batching multiple iterations into one commit
- Reopening a clear round because of late non-blocking noise
- Exiting while soften-watchlist items remain `open` or unexamined
- Declaring exit after a focused panel that never re-ran `design-simplicity` on the tip when earlier rounds only fixed docs/schema
- **Declaring CLEAR from a relaunch while the original worker may still finish.** If a worker is stuck and you relaunch, interrupt or cancel the original agent first, or wait until every originally launched worker ID is terminal. Reconcile findings from both outputs before staging exit. A late primary that overwrites a zero-finding relaunch JSON after CLEAR invalidates the exit; amend staging and treat exit criteria as unmet until a fresh clear-candidate round (or an explicit partner stop) closes the residual.

## Quick prompt (user-facing)

```text
review-loop on current branch vs <base>. Run a full review, then targeted follow-ups after fixes, until one fresh review finds zero unresolved blocking findings, the soften watchlist is closed, and design-simplicity covered the tip. Max 5 full-panel rounds.
If no base is named or the diff is large (>10 kB), the loop asks you to confirm the comparison base before round 1 (skipped silently in non-interactive sub-agent runs, with the resolution recorded).
```

## Integration Points

### Consumes `doing-code-review` skill
Step 1 each round: branch review mode; staging doc before reporting. Diff scope is committed `BASE...HEAD` only.

### Consumes `receiving-review` skill
Step 3 when blocking findings remain: triage and fix; update staging statuses.

### Consumes `done` skill
Step 4 each iteration: learn → docs-branch → commit (authorized per iteration). Syncs gitignored staging via docs-branch.

### Consumes `review-staging` skill
Every round writes a full staging doc (Metadata, Review Statistics, Findings with Comment/Analysis). Clear rounds still require statistics. Run the review-staging validator before reporting the round verdict.

### Boundary vs `execute-plan` skill
Use this skill for standalone branch hygiene until one fresh blocking-clean review. Use `execute-plan` Phase 3 for plan-scoped loops.
