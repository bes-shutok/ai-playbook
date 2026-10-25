---
name: review-loop
description: >
  Orchestrate repeat review-fix-boundary cycles on the current branch until a fresh code review
  reports zero unresolved blocking findings before any fixes: fresh review, fix if needed, then the
  light boundary (plain commit, then learn, then the record mirror), repeat; done runs once at the
  exit closeout. Use when the user asks to run a review loop, keep reviewing until clean, or repeat
  doing-code-review + receiving-review rounds.
  Trigger phrases: "review loop", "review-loop", "until clean", "keep reviewing until clean",
  "review fix done loop". Not for execute-plan Phase 3 (use execute-plan) or one-shot review
  (use doing-code-review only).
---

# Review loop

Run **fresh review → fix (if needed) → light boundary → repeat** on the **current branch** until exit criteria are met; done runs once at the exit closeout.

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

Read `{reviews_dir}`, `{tmp_dir}`, and `review_large_diff_bytes` from `.ai-playbook/facts.md` (opening TOML block; same source as `using-skills` Step 0). Absent `reviews_dir` (or the facts file) ⇒ stop and surface the gap; never guess a location. Absent `review_large_diff_bytes` ⇒ default `10240`.

**Base branch** (pick first that applies):

1. User named it (`against master`, PR base URL); unambiguous.
2. Open PR for `HEAD_BRANCH`: use PR base from `gh pr view` / `github-pr-workflow`; unambiguous.
3. Neither applies: resolve to the repo default integration branch (`main` or `master` per project `AGENTS.md`). Then, in an **interactive top-level session**, ask the user to confirm that base before round 1; in a **non-interactive / sub-agent context (risk-F1)** (invoked as a sub-agent of `execute-plan` Phase 3 or in a session with no user at the console, e.g. CI/scheduled), accept the resolved default without prompting. Either way, **record the resolved base + reason in the staging-doc Metadata** (for example `Base resolved non-interactively: main (repo default; no PR/arg, autonomous sub-agent)`) so the resolution is auditable rather than silent.

If `git diff ${BASE_BRANCH}...HEAD | wc -c` exceeds `review_large_diff_bytes` (default 10240), the round-1 `doing-code-review` launch confirms the basis with the user (interactive) or records it in Metadata (non-interactive).

**Diff scope (every review round):** `git diff ${BASE_BRANCH}...HEAD` on **committed** `HEAD` only. Do not review uncommitted fixes as proof the round is clean; commit first, then start the next round.

**Re-resolve the file set every round (required):** at the start of Step 1 in *each* round, re-run `git diff --name-only ${BASE_BRANCH}...HEAD` (committed mode) or `git status --short` (working-tree mode) and confirm the file list matches what this round intends to review. Do not cache the file set from round 1. A loop mutates the tree between rounds (fixes applied, files added by `learn` and `investigate` at the boundary, partner edits), so a round-1 snapshot goes stale and silently drops new/changed files from later rounds, which produces a false "clean" exit on a partial review. If the file count changed since the prior round, the new files are in scope for the fresh review even if they bundle a different concern than the original change; do not dismiss them as out-of-scope without recording why.

**Verdict-shape drift check (every round, before launching the review):** run `python3 scripts/plan_readiness.py --sweep`, resolving the script via the env-override, repo-local, then deployed-runtime fallback documented in `agents/hooks/plan-readiness/README.md`. A non-zero exit means the sweep failed: verdict-parse anomalies in the corpus, a missing or misconfigured reviews_dir, or a sibling compatibility failure (see agents/hooks/plan-readiness/README.md); read the stderr reason and resolve it before launching this round's workers. The sweep's coverage line is informational: it tracks how much of the corpus still predates the sidecar verdict field.

## One iteration

| Step | Skill | What happens |
|------|-------|----------------|
| 1 | `doing-code-review` | Branch review mode; staging doc **before** reporting to user |
| 2 | Triage | Count findings still `pending` with `blocking: true`; classify each finding real vs formal per receiving-review (**Triage class (real vs formal)**) before severity ranking |
| 3 | `receiving-review` | Only if step 2 count > 0; fix or `drop` each finding; update staging doc statuses; after fixes land, run the **Generalize-on-fix** step from `receiving-review`; capture valid findings not fixed in this run as durable backlog items per `receiving-review` **Backlog capture** |
| 4 | Light boundary | light boundary (plain commit, then learn, then the record mirror; the procedure is execute-plan's Light boundary section, referenced not restated) |

Fold-time staged-record duty (steps 2 and 3 own the fix and fold batches): a fold folds findings from the round's staged record per review-staging's record schema, so the round's record is staged before its findings fold; worker task outputs are panel evidence, never the record sink.

The fold-output verification duty binds every fold that introduces or rewords a mechanical artifact (command block, loop, witness sentence, gate sentence): verify that artifact by extracting it from the exact bytes it will commit and running those bytes, never a hand-typed equivalent. A substitution that leaves the file unchanged fails the fold, for every intended replacement. A locator-class witness whose dry run classifies every checked item as the benign arm runs one positive control (the locator re-run on one input known to require the non-benign arm); the fold refuses when the locator still classifies that input benign, and the benign-arm witness is never trusted without its positive control. The verification runs against the staged bytes and is re-asserted at the fold commit; a batch edit that touched a verified artifact after its run invalidates that run and re-runs the duty. Record the verification outcome (the surface as staged@ or committed@ with the 12-hex sha256 digest, what ran, pass or skip-with-reason) in the fold commit message as the additive verification outcome line; a fold with no mechanical artifact owes no run and no outcome line, and a witness-sentence artifact is never skipped (it always runs its locator).

**Do not** merge step 3 fixes into the same round's step 1 verdict. Step 1's output is **provisional findings before fixes**.

**Context budget checkpoint (round boundary):** the orchestrator applies the execute-plan `Context budget checkpoints` policy at each round boundary (after the round's step 4, before the next round's step 1): measure context size, log one telemetry record with `skill: review-loop` to the run's telemetry file `docs/tmp/review-loop/<branch-slug>/context.jsonl`, and act per that policy's threshold ladder; review-loop does not restate the ladder. Under execute-plan Phase 3 the parent's after-review-round checkpoint is authoritative for ladder actions: review-loop only logs its per-skill record and takes no ladder action of its own, and the first record review-loop appends for a run is the baseline for its own compactions_to_date comparison.

Each round boundary updates the loop's disk-truth record per the plans skill's degraded-generation disk-truth protocol: the round's staging doc and its `.stats.json` sidecar are the per-round disk artifacts, findings are read from those files (never from the loop's own prose), and a detected garble or cross-check mismatch stops the loop before the next round's fixes.

## Staging doc (required every round)

Path pattern:

```text
{reviews_dir}/YYYY-MM-DD-branch-review-<branch-slug>-r<N>.md
```

`<branch-slug>`: current branch with `/` → `-`, lowercased (e.g. `PROJ-1234-segments-docs-design-rfc`).

Before workers launch, run the record selection helper (`scripts/review_record_selection.py select`) to pick this round's record path and write only the helper-emitted paths (per `review-staging`; on a `new-round` decision run the helper's `backup` subcommand first and record the backup path in Metadata).

Records past the retention window are pruned with `scripts/review_retention.py`: run the dry run first, then prune only through its manifest-gated, pairing-aware path so each staging doc and its `.stats.json` sidecar are removed as one unit.

Each doc **must** include (full `review-staging` hierarchy; **no stub or verdict-only files**):

1. **Metadata** table (review type, base/head SHAs, round, domains, focus, `Status: STAGED`)
2. **Base / head** SHAs or branch names
3. **`## Review Statistics`** per `review-staging` (Panel with Solo/Echo, Counts, Deduplication groups, Discarded with Pattern, Severity calibration, Triage outcomes; required even on clear rounds)
4. **Findings accepted for fix** table when unresolved blocking findings exist
5. **`## Findings`** with all four severity headings (Critical, High, Medium, Low; `None` when empty) and one `### F<N>` per staged finding; each must have `#### Comment` and `#### Analysis` (not bullet-only summaries), its confidence, reachability, blast radius, pattern owner, and triage taken from review-staging's `Closed enums` line under that file's Enum authority refresh rule (workers receive current values; a stale prompt copy never serves)
6. **`## Fixes applied (r<N>)`** with commit SHA when step 3 ran
7. **Verdict for this round (before fixes):** `N blocking findings accepted for fix` OR `0 unresolved blocking findings; clear round`
8. **Loop exit criterion** (see below); never write "0 remaining after fixes" as the round verdict

New staging docs, their `.stats.json` sidecars, and new session logs reach the primary checkout homes through the boundary's record mirror (a plain copy, never blocking); the docs-branch sync is deferred to the loop's exit closeout.

**Mechanical gate (before reporting round verdict):** run the review-staging validator on the staging path and confirm the `.stats.json` sidecar exists; do not report the round complete until both pass. The invocation passes the doing-code-review gate's code-source context form (`--source-code-repo` with the repository root, `--source-code-plan` with the round's sidecar path), which is what lets the validator read the certification seal from disk, compare the sidecar's certified range, regenerate the reviewed diff, and grade a declared corrections chain; the sidecar must declare `source_kind: "code"` for that context, and a sidecar without it hard-fails the gate as a tool error. A clean exit additionally requires the round's record to be `record_kind: canonical`; a reconciliation or worker-evidence record can never certify the round (validator-enforced; the record-kind enum and the `RECORD_KIND_SIDECAR_MIN_DATE` fence live in `review-staging`). The written sidecar is a version-1 record; one dated on or after `EXTENDED_SIDECAR_MIN_DATE` must carry the freshness fields `review_mode`, `risk_signals`, `prior_findings_filter`, and `last_fix_commit`; the clean-verdict rules, the min-date fence (`EXTENDED_SIDECAR_MIN_DATE`), and the validator-copy refresh recovery live in `review-staging`; field types and the descriptor-bound values live in the validator's schema descriptor, whose structural shapes `--scaffold` renders; the remaining allowed values (the findings-row enums, the discard codes, the panel statuses) stay documented in `review-staging`. The validation classes split per review-staging's record-validation-levels subsection, so intermediate rounds run the lint-level `--preflight` pass over the staging pair with the same source context and resolve its findings before the round's triage and counter decisions are consumed, while the certification round keeps the full `--hard` source-context gate before its verdict is recorded.

```bash
VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
python3 "$VALIDATOR" --hard "$STAGING_PATH" \
  --source-code-repo "$(git rev-parse --show-toplevel)" \
  --source-code-plan "${STAGING_PATH%.md}.stats.json"
```

Cursor hooks also warn via `postToolUse` after staging writes, block review-loop commits when validation fails, and may inject a `stop` follow-up if the newest round file is still a stub.

## Soften / regression watchlist (cross-round)

Maintain a **soften watchlist** for the active loop run: the active-run watchlist is a derived working copy initialized from the latest round's record pair (the sidecar `soften_watchlist` array and its rendered `### Soften watchlist` section) and written back into each new round's record; session tmp is a cache, never the origin of record.

Add an entry when **any** of these happen after a finding was staged as `fixed` / `done`:

- A later commit **reverts** the fix (or restores the prior behavior) with rationale such as "soften", "keep X", "intentional", or partner pushback; the trigger reads commit messages as the detection input that schedules a watchlist re-check, and commit messages never hold row state
- Triage marks the finding `dropped` / `deferred` **after** a fix commit already landed
- The partner explicitly declines a fix that was already implemented

Each watchlist row: `round`, finding id or pattern, anchor path, one-line prior fix, one-line soften reason, `status` (`open` | `reaffirmed` | `restaged`).

**Every subsequent `doing-code-review` round** (full or focused) must:

1. Pass the open watchlist into worker prompts.
2. For each open item, either **re-stage** (behavior still wrong / soften was incorrect) or **reaffirm** (still intentional; record one-line reason in the new staging doc).
3. Leave `open` items only when the owning worker was not launched this round; then the next round that launches that worker must close them.

Do **not** treat a prior soften as "already reviewed; skip." Softens are the main source of silent reintroduction (example: exception-ownership fix reverted same day).

### Budget gate (between-boundary probes)

At loop start and before every fix or fold batch and every mechanical audit pass between review rounds (the between-boundary probes), run the quota probe per the canonical Budget gate protocol (agents/skills/execute-plan/SKILL.md, Budget gate section): three-step probe resolution, thresholds from `.ai-playbook/facts.md`, and pass `--write-flag ~/.ai-playbook/runtime/budget-guard.flag`. On `pause`, run the canonical pause protocol with the current round's staging doc as the record sink, a sink usable only after the closing round's staging record and sidecar pair are written and validated (lesson 225): schedule the resume automation FIRST (reset rounded up to the whole minute plus one; self-contained prompt to re-enter this loop at the recorded next step, apply the canonical flag-clear match rules, and stand down if the loop exited clean or a peer session resumed the work), then append a `budget_pause` record to the staging doc with the runtime, reset epoch and ISO time, thresholds used, next step, and `resume_scheduled: yes|no` (at loop start, before any staging doc exists, record it in the loop's session notes). Before a usage-wall pause's armed timed resume carrier fires, the paused lane runs the governing probe (one cheap trivial sub-agent dispatch per run) once at the pause boundary, after the record above is written and before settling idle, and again before continuing at any later turn the lane receives while the pause stands; the probe schedules nothing. A clean probe lifts the pause in-session (the pause record gains a resolution line, and the lane deletes its own armed carrier as its owner before continuing at the recorded next step), and a refused probe leaves the armed carrier standing with its fire time and payload unchanged. The lane starts no governing probe once the carrier's recorded fire time has passed, and a probe still in flight at the fire is abandoned and recorded in the pause record, the fired carrier's own session being the sole resume path. Weekly `secondary` bindings stay report-only: the probe writes no flag, nothing is scheduled, and the outcome is reported for user decision; a record bound to the weekly secondary window is never scheduled by a resume path. On `wait-for-reset`, ride the boundary through in-session: wait the reported wait_minutes minutes, re-run the probe, and the fresh report governs the boundary (continue proceeds, pause runs the pause protocol above; no supersede and no watcher bookkeeping: this skill owns no watcher state). On `continue`, record one outcome line `budget-gate: continue, <binding>, <used_percent>%` in the round's staging doc (at loop start, before any staging doc exists, record it in the loop's session notes or the first round's staging doc once it exists) and proceed. Every resume path reconciles a `budget_pause` record carrying `resume_scheduled: no` by completing the scheduling step before continuing work; a record whose binding is the weekly secondary window stays report-only and is never scheduled. This skill schedules no standing resume watcher (it owns no machine-state home); the between-boundary probes and the pause protocol are its only budget-gate surface.

## Exit criteria (default)

Stop only when **all** of the following hold on a fresh review of committed `HEAD`, with one round-free path beside the fresh round: an iteration whose only fixes are corrections-carried comment-only deltas may exit on the verified record (`scripts/code_delta_classifier.py` proves the comment-only class over the certified range's committed before and after heads, and the carrying CLI-produced row on the review record re-binds the digest with zero rounds); when the carrying row verifies, the re-bound digest counts as covered for criterion 3's watchlist anchors and criterion 4's design-simplicity tip-digest anchoring:

1. Zero unresolved findings with `blocking: true`, or the residual-acceptance exit when a recorded residual policy governs the loop: under the policy the exit criteria count only blocking findings outside the recorded residual set; the named fix set reached fixed or dropped, and every out-of-set new blocking finding carries a durable backlog item with an owner and a trigger
2. No fixes were applied in that iteration, except comment-only fixes carried by verified corrections rows (the classifier CLI proves the class; the carrying row re-binds the digest with zero rounds per the preamble's round-free path)
3. Every soften-watchlist item is `reaffirmed` or `restaged` (then fixed or explicitly dropped with partner confirmation) in that same fresh round or an earlier round of this run whose tip digest for the watchlist anchors is unchanged
4. **Design-simplicity coverage before exit:** if the clear-candidate round used `panel_mode: focused` and omitted `design-simplicity`, run one more pass that includes `design-simplicity` (hybrid is enough: correctness + design-simplicity + any other owners still needed). Skip this extra pass only when the immediately preceding round in this run was a **full** panel that already completed `design-simplicity` on the same tip digest.
5. No unresolved reconciliation trigger remains. If recurring history, contradictory artifacts, or an untrusted closure witness remains, run `review-reconciliation` before reporting exit.
6. **Residual-acceptance exit mirror:** standalone loops share the same `residual-acceptance exit` shape as execute-plan Phase 3: a named fix set (from a reconciliation pass or the fix-risk triage), one address pass plus ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups, out-of-set new blocking findings become durable backlog items with an owner and a trigger, and the policy is recorded before the verification round runs.

At every `max_review_rounds` total-round interval and every `max_full_panel_rounds` full-panel interval, record the trajectory reflection in the existing round record and convergence data: classify staged findings as new-root, fold-defect, test-witness-gap, or wording, with counts and open blockers. Coincident intervals share one reflection. The interval is not a stop limit. Apply the convergence, reconciliation, and bounded self-heal decisions in `review-plan`’s Scope and complexity policy; that policy is the single owner of continuation and authorization decisions. This workflow records the reflection, the blocker counts used, and the selected continuation or pause outcome before orchestrating the resulting review path. The round record carries the counts and selected branch used to resume or pause.

Classify scope and complexity using the shared policy in `review-agents/review-panel-selection.md`; project type does not change the default or impose a hard cap.

| Signal | Valid exit? |
|--------|-------------|
| Fresh review -> 0 unresolved blocking -> no step 3 -> watchlist closed -> design-simplicity covered | **Yes** |
| Fixed issues → grep clean / "looks good" | **No** |
| Same round: review → fix → "0 open" | **No** |
| Postfix verification in the same round | **No** |
| Focused docs/risk-only clear round with open softens or no design-simplicity since last full panel | **No** |

Anti-pattern rows for coverage handling: **No full-panel relaunch after a timed-out or failed worker**: after a material worker exhausts its retry budget, the loop proceeds by replacement-lens selection (focused round per review-panel-selection) or records degraded coverage; it never relaunches the full panel and never waits unbounded. **Degraded and failed coverage actions:** degraded requires a narrowed re-run or an explicit user risk acceptance recorded in triage outcomes; failed requires repairing staging or the runner and re-running; neither state may exit the loop as clear. The exit report states the final `coverage.outcome` and any `missing` lenses alongside the existing blocking-finding accounting; the design-simplicity-before-exit rule is unchanged and a replacement round must still satisfy it.

**Before reporting loop exit:** every valid finding from this run that was not fixed (deferred, scope-dropped, or excluded by user instruction) must have a durable backlog item per `receiving-review` **Backlog capture**. When the loop exits through the residual-acceptance exit, the orchestrator diffs the address pass's changed files against the named set and routes any out-of-set change back to a normal fresh round instead of the exit (the policy sanctions only the named set's address pass; an out-of-set change is unreviewed work that re-enters the loop). Two separate returned-for-ask obligations apply at exit. First, the loop may not exit while a returned-for-ask presentation is outstanding (undischarged): an interactive run relays the ask and gets the answer before exit; a non-interactive run discharges any outstanding non-blocking ask by recording and surfaces the recorded question in the exit report; a must-stay-blocking ask is never discharged by recording and never reaches exit. Second, any recorded returned-for-ask question that has not yet been surfaced must be surfaced in the exit report (the recording discharged it for a non-blocking ask, per the discharge split in orchestration rule 4; not treated as backlogged). The same relay duty applies to non-exit user-directed stops: a run that stops to ask the user (the reconciliation-decision ask, the rule-4 fix-risk stop, and any failure, timeout, or interrupt user ask) must relay outstanding (undischarged) or recorded-but-not-yet-surfaced returned-for-ask questions alongside the other ask content. Include the fixed-vs-backlogged tally and backlog item paths in the exit report; gitignored staging docs are never the only record.

## Limits

| Limit | Default | On exceed |
|-------|---------|-----------|
| `max_review_rounds` | **5** | Reflect at every total-round interval; the interval is not a stop limit |
| `max_full_panel_rounds` | **5** | Reflect at every full-panel interval; combine coinciding intervals; continue when results converge |
| `max_escalations` | **1 per active run** | Prohibit a second escalation in the same run |

A review round is one review pass regardless of panel mode; full-panel and focused rounds both count toward `max_review_rounds`, while only full-panel rounds count toward `max_full_panel_rounds`. Both values are reflection intervals. In an execute-plan run, Phase 3 owns the shared counter and counting semantics. When the loop carries a plan's declared execution budget, the full-panel budget derives from it per the plans skill's Plan Quality Gate budget formula and breach pauses the loop for operator direction per review-plan's Scope and complexity policy duty; standalone loops keep the configured intervals. In a plan-scoped loop, delta (focused) rounds never consume the full-panel counter and the whole-plan review scope, not the panel roster, decides the full-panel count.

Never use commit subjects like `Close review loop` or `Review complete` until exit criteria are met.

## Orchestration rules

1. **Continuous iterations:** after the boundary succeeds, increment `review_round`, reflect at each configured interval, and return to step 1 unless exit criteria or an independent stop condition applies.
2. **Sub-agents:** launch `doing-code-review` with the panel from `review-panel-selection.md`; do not replace with inline grep.
3. **Targeted revisions:** after fixes, launch blind `correctness-completeness` plus every distinct worker that owned a finding or whose domain the fixes affected. If all five are selected, count a full-panel round only when the round's scope is the whole plan (plan-scoped loops); delta (focused) rounds never increment the full-panel counter regardless of roster, and standalone loops keep the roster-keyed counting unchanged. When the soften watchlist has `open` items, also launch the worker that owns each open pattern (see `review-panel-selection.md` tiered ownership). A targeted post-fix round records its findings but never carries the certifying clean verdict: when it returns zero unresolved blocking findings, the certification is a following `fresh-adversarial` round (a focused panel satisfies it; the round's `Review mode` label must read `fresh-adversarial`), because the staging mechanical gate refuses a clean verdict beside a non-null `Last fix commit` under any other mode label; plan the composition in one pass instead of discovering the refusal at the gate. Code-family rounds carry no series sweep: the sweep duty is scoped to plan-review series closes per review-staging's record-validation-levels subsection.
4. **Fix-risk triage before more folding:** when consecutive rounds' fixes keep regenerating new findings, apply the `receiving-review` **Fix-risk triage when fixes regenerate findings** section before folding further, and verify scoped fixes with the focused targeted round composed per `review-panel-selection.md` (Targeted follow-ups; orchestration rule 3 selects the set). A fix-risk stop for user direction follows the closing stop-for-direction clause of `receiving-review` **Fix-risk triage when fixes regenerate findings**. A returned-for-ask presentation outstanding takes the discharge/stop split defined by execute-plan Step 3.3 verification gate item 6 and receiving-review's Fix-risk section: an interactive run relays the ask and gets the answer before the next fold or iteration; a non-interactive run discharges a non-blocking ask by recording per review-staging's receiving-review consumer row and stops for direction on a must-stay-blocking ask (the fix-risk stop above; execute-plan Step 3.5 Fix-risk stop row when running under execute-plan); the loop never increments its round with the ask outstanding.
5. **Reconciliation before continued churn:** when the same root issue recurs, fixes regenerate findings across consecutive rounds, review artifacts or digests disagree, invoke `review-reconciliation` before another review or fix pass. A `max_full_panel_rounds` interval alone triggers reflection, not reconciliation. Pass the chronological staging artifacts, triage and fix history, current digest, counter, and mutation scope. Where fix-risk stop conditions also hold (rule 4), take the Fix-risk stop for user direction after the reconciliation runs; the reconciliation, if triggered, still runs first. Before this standalone stop, invoke `self-heal` to check for a safe recovery already within authority; it cannot replace a required user decision or reset the loop's counters, budgets, gates, or completion boundary. Fixes regenerate findings means the measured churn trigger fired: the latest round's recorded classification shows fold-defect plus wording findings that exceed half of staged findings, or total staged findings did not decrease across the two most recent rounds, or the open-blocking count did not decrease across two consecutive rounds; standalone loop rounds record the same per-round root classification (new-root, fold-defect, test-witness-gap, wording) in their round record so the signal stays evaluable, and a loop whose records carry no classification falls back to the open-ended trigger phrasing; a fired trigger mandates review-reconciliation before any further review or fix pass, even when the blocking count converges.
6. **Exit hybrid:** before accepting a focused clear round as loop exit, ensure `design-simplicity` ran on the current tip digest (see Exit criteria item 4). Do not exit on contract-docs/risk-only cleanliness alone after architecture-relevant code landed earlier in the branch.
7. **Commits:** the light boundary commits: one iteration -> one commit when fixes ran, with learn's skills-repo commits and the investigate entry commit as sanctioned rider commits recorded on the boundary row.
8. **Push:** requires explicit user instruction.
9. **PR mode:** if user gave a PR URL, still write staging docs; optional post to PR via `doing-code-review` Direct mode.
10. **Exit closeout (standalone loops):** when the loop runs standalone (not under execute-plan), reaching the exit criteria includes running the `done` skill's full sequence one time before the exit report, exactly as the Consumes `done` entry prescribes (the landing sweep, the docs-branch sync that publishes this loop's gitignored staging docs, the side-repo walk, and finalize), with learn reading the run's review and address records; under execute-plan the Phase 5 final closeout owns this and the loop takes no separate action.

Review findings are evidence to assess, not authorization to broaden the loop's scope; findings outside the accepted scope become backlog items (per receiving-review Backlog capture) unless the user explicitly expands scope.

## Anti-patterns

- Treating post-fix cleanliness as loop exit
- Skipping staging doc on clean rounds
- **Writing abbreviated or stub staging docs** (verdict-only, themes table without per-finding Comment/Analysis, or omitting Review Statistics) to save time during autonomous loops
- Stopping after first fix pass without a **new** step 1
- Reviewing `git diff` working tree to claim round N is clean while fixes are uncommitted
- Batching multiple iterations into one commit
- Reopening a clear round because of late non-blocking noise
- **Folding every finding mechanically while fixes keep regenerating findings**; audit fix-risk per `receiving-review` **Fix-risk triage when fixes regenerate findings** first
- Exiting while soften-watchlist items remain `open` or unexamined
- Reporting loop exit with deferred or scope-dropped valid findings recorded only in the gitignored staging doc
- Declaring exit after a focused panel that never re-ran `design-simplicity` on the tip when earlier rounds only fixed docs/schema
- **Declaring CLEAR from a relaunch while the original worker may still finish.** If a worker is stuck and you relaunch, interrupt or cancel the original agent first, or wait until every originally launched worker ID is terminal. Reconcile findings from both outputs before staging exit. A late primary that overwrites a zero-finding relaunch JSON after CLEAR invalidates the exit; amend staging and treat exit criteria as unmet until a fresh clear-candidate round (or an explicit partner stop) closes the residual.

## Quick prompt (user-facing)

```text
review-loop on current branch vs <base>. Run a full review, then targeted follow-ups after fixes, until one fresh review finds zero unresolved blocking findings (or a verified comment-only corrections re-bind closes the delta per the Exit criteria), the soften watchlist is closed, and design-simplicity covered the tip. Reflect at every configured total-round and full-panel interval; intervals are checkpoints, not stop limits.
If no base is named or the diff is large (>10 kB), the loop asks you to confirm the comparison base before round 1 (skipped silently in non-interactive sub-agent runs, with the resolution recorded).
```

## Integration Points

### Consumes `doing-code-review` skill
Step 1 each round: branch review mode; staging doc before reporting. Diff scope is committed `BASE...HEAD` only.

### Consumes `receiving-review` skill
Step 3 when blocking findings remain: triage and fix; update staging statuses. Valid findings not fixed in the run are captured as durable backlog items per its **Backlog capture** rule; the exit report includes the fixed-vs-backlogged tally. Orchestration rule 4 applies its **Fix-risk triage when fixes regenerate findings** section before further folding in a regenerating loop. The step-3 triage pass applies the class step before the fix-vs-defer decision, and formal findings follow the class routing instead of the fix-everything default.

When invoked under execute-plan, Step 3 receiving-review work proceeds one worker at a time under execute-plan Step 3.3; the parent merges each result before launching the next review-fix worker. Independent review-panel workers may still run in parallel. The standalone default stays the single Step 3 pass.

### Consumes `review-plan` skill
Consumer: review-plan's Step 5 fold-discipline rule (the consumer rule added by the fold-verification plan) references this skill's fold-output verification duty paragraph as the bar's home; the rule names the bar and this paragraph owns the how, so neither skill voices a different fold verification bar.

### Consumes `done` skill
Consumed at the exit closeout only: once the exit criteria are met, the run's final closeout invokes the done skill's full sequence one time (the landing sweep, the docs-branch sync that publishes this loop's gitignored staging docs, the side-repo walk, and finalize); the per-round boundaries never invoke it.

### Consumes `learn` skill (via the boundary procedure)
Step 4's light boundary invokes learn after the boundary's plain commit, over the round's review and fix records; learn's capture contract (placement, scope, dedupe, and its Step 1.9 project-backlog arm with the investigate routing) applies unchanged, and its commit receipts are recorded on the boundary row (the boundary manifest row in an execute-plan lane; a standalone loop records the whole boundary record, the boundary commit and the record-mirror outcome included, in its round's staging doc, the loop's per-round disk artifact). The boundary procedure is owned by execute-plan's Light boundary section; this entry references it and never restates it.

### Consumes `review-staging` skill
Every round writes a full staging doc (Metadata, Review Statistics, Findings with Comment/Analysis). Clear rounds still require statistics. Run the review-staging validator before reporting the round verdict. The fold-time staged-record duty above is the consuming side of the same contract: folding reads the round's staged record, so a round whose record was not staged gets it staged before its findings fold.

### Consumes `self-heal` skill
Before a standalone fix-risk stop for operator direction in orchestration rule 5, self-heal checks for a safe recovery already authorized by the caller. The loop's review-round, escalation, budget, and authorization limits remain authoritative; self-heal does not replace a required user decision.

### Consumes `review-reconciliation` skill
Use it at orchestration rule 5's trigger. `review-loop` remains the original orchestrator: after any reconciliation refactor, it launches the next normal fresh review of the current digest (the graded exit's corrections re-bind is the only round-free path, and a reconciliation refactor is never one) and does not treat the reconciliation result as a clear round.

### Boundary vs `execute-plan` skill
Use this skill for standalone branch hygiene until one fresh blocking-clean review or its verified comment-only corrections re-bind (`scripts/code_delta_classifier.py` proves the comment-only class; the Exit criteria own the round-free path and the graded owner text is execute-plan's Phase 3 accepted-fix rule). Use `execute-plan` Phase 3 for plan-scoped loops.
