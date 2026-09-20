# Plan: Execute-plan intermediate task reviews with driving-force backlog capture

Driving force: efficiency (defects surface at the task boundary where they are cheapest to fix, cutting Phase 3 rounds and rework); secondary: token-usage (review worker sets sized to task complexity instead of uniformly heavy end-of-plan reviews).

## Terms

- **Intermediate task review**: the new execute-plan Step 1.2b pass that reviews one completed task's changed context before that task's checkbox marking and done commit.
- **Complexity tier**: the L | M | H classification that sizes the review worker set, derived from the task's `Files:` list and changed-content risk signals per `review-panel-selection.md`.
- **Changed context**: the task's `Files:` list plus the working-tree diff of that task's changes against the pre-task HEAD, the task section text, and fresh validation output; never the whole branch diff.
- **Tier hint**: the optional `Review tier: <L|M|H>` line a plan author may write on a task; the executor derives the tier when it is absent.
- **Driving force**: the closed-tag taxonomy a captured backlog item declares so project priorities can defer or promote it; owned by `receiving-review` Backlog capture.
- **Amendment rule**: the documented procedure for adding a driving force tag (document it in the taxonomy list with a one-line scope before first use).

## Assumptions

- assume Step 1.2b sits after Step 1.2 exit verification and before Step 1.3 checkbox marking, so review fixes fold into the task's single done commit; basis: plans coherent-commits rule and the execute-plan one-commit-per-task invariant (Hard Gate 4).
- assume Phase 3 stays mandatory with its current quality bar; Step 1.2b is an early-catch net that shrinks what Phase 3 finds, not a substitute; basis: the request asks to reduce final review time and effort, not to remove the final review.
- assume per-task passes stay lightweight: no staging doc, no stats sidecar, no mutator failure-mode matrix; those remain Phase 3 obligations; basis: a per-task full staging apparatus would cost more than it saves, defeating the stated goal.
- assume the per-task loop is: one review round; on unresolved blocking findings a focused fix, then ONE focused re-review of the changed context with the owning workers; cap 2 review rounds per task, exhaustion stops for user direction; basis: consistency with existing skill caps.
- assume verdicts and caps are manifest-line bookkeeping only; `runtime_state.json` and the runtime driver are untouched; basis: Phase 3 review rounds are likewise manifest-tracked, not driver-tracked.
- assume intermediate review workers may launch in parallel within a tier and inherit the 20-minute timeout and focused-relaunch path; basis: existing Sub-Agent Launch Rules and Timeout sections.
- assume the Recovery (retroactive compliance) path does not run Step 1.2b; basis: retroactive tasks have no clean pre-task boundary to diff against.
- assume valid findings and improvement suggestions NOT causally related to the plan become durable backlog items with the Driving force line from BOTH Step 1.2b and Phase 3, instead of in-task fixes or silent one-line drops; basis: explicit user requirement covering this and final reviews.
- assume the executor derives the tier mechanically when no hint is present; post-implement risk signals may raise a hinted tier and never lower it; basis: the flexibility requirement plus the skill's fail-closed bias.
- assume no validator enforcement in `scripts/plan_readiness.py` for the tier hint or the opt-out line in this first pass; basis: same first-pass precedent as the certified driving-force metadata plan.
- assume the execute-plan edit coordinates with the in-flight uncommitted harness-triage plan that also edits `agents/skills/execute-plan/SKILL.md`; whoever executes second re-derives insertion anchors from the then-current bytes; basis: verified overlap in that plan's Files lists.
- assume the plans edit lands after, or is re-based onto, the certified-unexecuted driving-force metadata plan's `agents/skills/plans/SKILL.md` edits; both are additive to different regions (task checklist rules versus header metadata block); basis: verified overlap.
Decision points requiring a grill: plans-skill involvement: add the optional per-task Review tier authoring hint (user selection, chat 2026-09-20; affects the plans task and the tier precedence rule); backlog driving-force taxonomy: 12-force closed set with documented amendment rule and plans-taxonomy mapping (user selection, chat 2026-09-20; affects the receiving-review task); opt-out mechanism: plan-header Intermediate reviews line, default on (user selection, chat 2026-09-20; affects the execute-plan task).

## Gist & Examples

TLDR: every executed task gets a changed-context review sized to its complexity before its done commit (one cycle when clean), and every off-plan concern from intermediate or final reviews lands in the backlog tagged with a driving force, so defects surface early and deferrals stay triageable.

What changes: execute-plan gains Step 1.2b, a per-task intermediate review that sees only the task's changed context, staffed by a complexity-tiered worker set taken from the existing panel-selection machinery (Tier L: 1 worker; Tier M: 2; Tier H: the risk-signal floor set). One round when clean; blockers are fixed in-task and re-reviewed once; two rounds maximum, then the run stops for direction. Findings and improvement suggestions unrelated to the plan are never fixed in-task and never silently dropped: they become backlog items carrying a `Driving force:` line from a new amendable 12-force taxonomy, captured identically from Step 1.2b and Phase 3. Plans may declare `Intermediate reviews: off` in the header to opt out, and may hint each task's tier with `Review tier: <L|M|H>`.

Example: a three-file task that changes internal behavior with no public-API, serializer, or boundary change derives Tier M (correctness-completeness + testing); its reviewer notices the new helper duplicates a sibling module's utility. That duplication is not causally related to this task's plan, so the reviewer does not fix it and the orchestrator does not drop it: a backlog item records it with `Driving force: simplicity` and the task's done commit stays scoped. The author-hinted case: a plan marks a two-file docs task `Review tier: L`, so one `contract-docs` worker reviews only that diff; when the implemented task unexpectedly touches a public API, the detected risk signal raises the pass to the floor set and never back down.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the whole Validation Commands block exits 0 on the post-change tree; the Step order chain (1.2 before 1.2b before 1.3 before 1.4) is verified by an ordering gate, not prose.
- consistency (single source): tier policy lives only in `review-panel-selection.md`; execute-plan references it; a negative gate proves the tier table is not duplicated into the execute-plan skill.
- simplicity: no new scripts, no new facts keys, no runtime-driver or manifest-schema changes; the per-task record is one manifest line plus one session-tmp log.
- token-efficiency: worker sets are bounded by tier (L 1, M 2, H risk-signal floor) and the clean path is exactly one round per task.

**Done when:**
- Every task gate passes fail-closed and the full Validation Commands block exits 0.
- The no-em-dash scan and the public-hygiene scan pass over the six changed files at authoring and at commit time.
- No file under `scripts/` changes bytes in any task commit.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] Across the next several executed plans, Phase 3 first-round finding counts on reviewed scopes drop versus recent history, and at least one intermediate-captured backlog item is promoted into a later plan. Evidence owner: Andrey; closure: observation recorded in a maintenance turn or a follow-up plan. Step 1.2b stays prose-only until that observation justifies scripting it (three-question triage).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py` and every other file under `scripts/`; reason: validator and driver enforcement explicitly out of scope for this first pass.
- `agents/skills/execute-plan/runtime-contract.md` and `scripts/execute_plan_runtime.py`; reason: the machine manifest and driver are untouched by design (Assumptions).
- `agents/skills/review-loop/SKILL.md`; reason: the standalone loop inherits the backlog-capture change through `receiving-review` with no edits of its own.
- `agents/skills/doing-code-review/SKILL.md`; reason: Phase 3 panel machinery is unchanged.
- The in-flight plans `docs/plans/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md` and `docs/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md`; reason: peer-authored artifacts, coordination only per Assumptions.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
RPS=agents/skills/review-agents/review-panel-selection.md
RR=agents/skills/receiving-review/SKILL.md
SP=agents/skills/execute-plan/subagent-prompts.md
AL=agents/skills/execute-plan/agent-logs.md
EP=agents/skills/execute-plan/SKILL.md
PL=agents/skills/plans/SKILL.md
fail() { echo "VALIDATION FAILED: $1"; exit 1; }
test -f "$RPS" && test -f "$RR" && test -f "$SP" && test -f "$AL" && test -f "$EP" && test -f "$PL" || fail "precondition: run from the skills repository root"

# V1 per-task selection subsection (single source for tier policy)
grep -qF '### Per-task intermediate review selection' "$RPS" || fail "V1 selection heading missing"
test "$(grep -cF '### Per-task intermediate review selection' "$RPS")" -eq 1 || fail "V1 selection heading not unique"
grep -qF 'may raise it and never lower it' "$RPS" || fail "V1 tier precedence rule missing"
grep -qF 'Tier L' "$RPS" || fail "V1 Tier L definition missing"
grep -qF 'Tier M' "$RPS" || fail "V1 Tier M definition missing"
grep -qF 'Tier H' "$RPS" || fail "V1 Tier H definition missing"
grep -qF 'separate pass from Phase 3 rounds' "$RPS" || fail "V1 pass-accounting clause missing"
grep -qF '| Tier | Trigger | Workers |' "$RPS" || fail "V1 tier table header missing"

# V2 backlog driving-force taxonomy in receiving-review (pins scoped to the
# extracted region so a line outside the taxonomy block cannot satisfy them)
grep -qF '### Backlog driving-force taxonomy' "$RR" || fail "V2 taxonomy heading missing"
test "$(grep -cF '### Backlog driving-force taxonomy' "$RR")" -eq 1 || fail "V2 taxonomy heading not unique"
REGION="$(awk '/^### Backlog driving-force taxonomy/{f=1;next} f&&/^Amendment rule:/{f=0} f' "$RR")"
test -n "$REGION" || fail "V2 taxonomy region extracted empty"
for frag in \
  'security: vulnerabilities, authorization or injection gaps' \
  'performance: run-time speed, latency, throughput' \
  'scalability: behavior under growth in data volume' \
  'reliability: failure handling, retries and idempotency' \
  'maintainability: structure that slows future change' \
  'simplicity: unnecessary abstraction or structure' \
  'testability: coverage gaps, hermeticity, flake resistance' \
  'observability: logging, metrics, tracing, and debuggability gaps' \
  'docs: documentation debt or source-of-truth drift' \
  'token-usage: agent context or token cost' \
  'new-capability: improvement suggestion that adds functionality' \
  'external: mandated from outside current project priorities'; do
  printf '%s' "$REGION" | grep -qF "$frag" || fail "V2 taxonomy line missing: $frag"
done
printf '%s' "$REGION" | grep -qF 'plans efficiency tag reads as performance or token-usage' || fail "V2 plans-taxonomy mapping missing"
grep -q '^Amendment rule: adding a force requires documenting it in this list' "$RR" || fail "V2 amendment rule missing at column 0"
grep -qF 'Driving force: the primary force tag from the Backlog driving-force taxonomy' "$RR" || fail "V2 required-content bullet missing"
grep -qF 'Capture sources: review-fix cycles and execute-plan Step 1.2b intermediate task reviews' "$RR" || fail "V2 capture-sources note missing"

# V3 region hygiene: no em-dash inside the taxonomy block
if printf '%s' "$REGION" | grep -q "$(printf '\342\200\224')"; then fail "V3 em-dash inside taxonomy block"; fi

# V4 worker template and log conventions
grep -qF '## Intermediate task review worker (Step 1.2b)' "$SP" || fail "V4 worker template heading missing"
grep -qF 'task-<N>-review.log.md' "$SP" || fail "V4 done-template review-log reference missing"
grep -qF 'backlog items this task'"'"'s Step 1.2b captured' "$SP" || fail "V4 done-template backlog commit-scope clause missing"
grep -qF 'required only when Step 1.2b ran for the task' "$SP" || fail "V4 done-template review-log carve-out missing"
grep -qF 'task-<N>-review.log.md' "$AL" || fail "V4 agent-logs review-log path missing"

# V5 execute-plan step, gates, and wiring
grep -qF '### Step 1.2b: Intermediate task review' "$EP" || fail "V5 step heading missing"
grep -qF 'Intermediate reviews: off' "$EP" || fail "V5 opt-out line missing"
grep -qF '25. **Intermediate review before done**' "$EP" || fail "V5 hard gate missing"
grep -qF '| Intermediate task review workers | Yes (parallel within the tier) |' "$EP" || fail "V5 launch-rules row missing"
grep -qF 'inherit the 20-minute timeout' "$EP" || fail "V5 timeout clause missing"
grep -qF 'inter_review task' "$EP" || fail "V5 manifest tracking line missing"
grep -qF 'per member under a Step 1.2 batch launch' "$EP" || fail "V5 batch-member clause missing"
grep -qF 'cap 2 rounds then stop for user direction' "$EP" || fail "V5 round-cap clause missing"
grep -qF 'the Recovery path does not run this step' "$EP" || fail "V5 recovery-exclusion clause missing"
grep -qF "captured items ride the task's done commit" "$EP" || fail "V5 backlog commit-path clause missing"
grep -qF 'Skip Step 1.2b and launch done directly' "$EP" || fail "V5 skip anti-pattern row missing"
grep -qF 'Fix off-plan review findings in-task instead of backlogging' "$EP" || fail "V5 off-plan-fix anti-pattern row missing"
grep -qF 'Step 1.2b is not a budget-gate boundary' "$EP" || fail "V5 budget non-boundary sentence missing"
grep -qF 'Driving force line per receiving-review Backlog capture' "$EP" || fail "V5 Phase 3 capture touch missing"
grep -qF '### Consumes `review-panel-selection` skill (per-task intermediate tiers)' "$EP" || fail "V5 integration point missing"

# V6 step order chain: 1.2 < 1.2b < 1.3 < 1.4 (full chain, not pairwise)
O12="$(grep -n '^### Step 1.2: Launch implement sub-agent' "$EP" | cut -d: -f1)"
O12B="$(grep -n '^### Step 1.2b: Intermediate task review' "$EP" | cut -d: -f1)"
O13="$(grep -n '^### Step 1.3: Mark plan progress' "$EP" | cut -d: -f1)"
O14="$(grep -n '^### Step 1.4: Launch done sub-agent' "$EP" | cut -d: -f1)"
test -n "$O12" && test -n "$O12B" && test -n "$O13" && test -n "$O14" || fail "V6 order-chain anchors missing"
test "$O12" -lt "$O12B" && test "$O12B" -lt "$O13" && test "$O13" -lt "$O14" || fail "V6 step order wrong"

# V7 negative: tier table must not be duplicated into execute-plan
if grep -qF '| Tier | Trigger |' "$EP"; then fail "V7 tier table duplicated into execute-plan; reference the selection file instead"; fi

# V8 plans authoring tier hint
grep -qF 'Review tier: <L|M|H>' "$PL" || fail "V8 tier hint line missing"
grep -qF 'post-implement risk signals may raise the tier and never lower it' "$PL" || fail "V8 tier hint precedence missing"

echo "ALL VALIDATION GATES PASSED"
```

### Task 1: Per-task selection subsection in review-panel-selection.md

Files:
- `agents/skills/review-agents/review-panel-selection.md`

- [x] Add subsection `### Per-task intermediate review selection` after `### Risk-signal floor`, containing: the tier table (header row exactly `| Tier | Trigger | Workers |`) with Tier L (docs/skill-only or at most 2 files and no risk signals: one worker, `correctness-completeness`, or `contract-docs` for docs-only), Tier M (3 or more files or behavior change, no risk signals: `correctness-completeness` plus `testing`), Tier H (any risk signal, concurrency or transactional mutator marker, or public-contract change: the existing risk-signal floor set, full five at two or more signals); the precedence sentence `The plan's Review tier hint sets the starting tier; post-implement risk signals may raise it and never lower it.`; the derivation note (tier derived from the task's `Files:` list and the post-implement diff when no hint is present); and the accounting clause that a per-task pass is a `separate pass from Phase 3 rounds` with its own launch accounting under the six-launch ceiling [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `grep -qF '### Per-task intermediate review selection' agents/skills/review-agents/review-panel-selection.md && grep -qF 'may raise it and never lower it' agents/skills/review-agents/review-panel-selection.md` [class: REPOSITORY_TEST]
- [x] Commit: `skills: per-task intermediate review selection tiers in panel selection` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Backlog driving-force taxonomy in receiving-review

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] In `## Backlog capture for valid findings not fixed in scope`, add the required-content bullet `- Driving force: the primary force tag from the Backlog driving-force taxonomy (compound forces ranked primary then secondary)` [class: IMPLEMENTATION_REQUIRED]
- [x] Add subsection `### Backlog driving-force taxonomy` listing the 12 closed tags with one-line scopes exactly as pinned by V2 (security, performance, scalability, reliability, maintainability, simplicity, testability, observability, docs, token-usage, new-capability, external; maintainability and simplicity carry their plans-taxonomy counterpart notes inline), plus the mapping sentence ending `plans efficiency tag reads as performance or token-usage`, plus the `Amendment rule: adding a force requires documenting it in this list` rule (rename or removal requires a plan; an item fitting no force uses `external` with the concern named in its Problem statement) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the capture-sources note `Capture sources: review-fix cycles and execute-plan Step 1.2b intermediate task reviews; both record the Driving force line on every captured item.` and list the execute-plan intermediate pass in the Integration Points section as a consumer [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the V2 and V3 gates scoped to `agents/skills/receiving-review/SKILL.md` [class: REPOSITORY_TEST]
- [x] Commit: `skills: amendable driving-force taxonomy for backlog capture` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Worker template and log conventions

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`

- [x] Add template `## Intermediate task review worker (Step 1.2b)` to subagent-prompts.md: scope passes the task section text, the task's `Files:` list, the changed-context diff command (`git diff <pre-task-sha> -- <task files>` plus new untracked Files entries), and fresh validation output; adversarial framing with severity-calibration loaded; return format declares verdict `clean | blocking | backlogged-candidates`, findings with severity, blocking flag, plan-related yes/no, and for off-plan candidates a suggested driving force; rules state no staging doc and no sidecar, findings outside the changed context only when causally tied to the task or plan [class: IMPLEMENTATION_REQUIRED]
- [x] In the Done (per task) template preceding-step list, add `<TASK_REVIEW_LOG_PATH>` (`task-<N>-review.log.md`) alongside the implement log, `required only when Step 1.2b ran for the task` (omitted under the `Intermediate reviews: off` opt-out and on the Recovery path, where Step 1.2b does not run, so the missing-log stop rule cannot deadlock those done launches), and extend the template's commit-scope rule with the clause `the commit scope additionally includes any Driving-force backlog items this task's Step 1.2b captured` (the backlog home is git-tracked; a captured item left out of the task's done commit defeats the durability guarantee); add the same path convention to agent-logs.md [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `grep -qF '## Intermediate task review worker (Step 1.2b)' agents/skills/execute-plan/subagent-prompts.md && grep -qF 'task-<N>-review.log.md' agents/skills/execute-plan/agent-logs.md` [class: REPOSITORY_TEST]
- [x] Commit: `skills: intermediate task review worker template and review log convention` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Step 1.2b and wiring in execute-plan

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Insert `### Step 1.2b: Intermediate task review` between Step 1.2 and Step 1.3: runs for every task and per member under a Step 1.2 batch launch at that member's checkpoint; changed context only per Terms; worker set resolved from the Task 1 subsection; one round when clean, focused fix plus one focused re-review on unresolved blocking findings, cap 2 rounds then stop for user direction; off-plan valid findings and improvement suggestions become backlog items with the Driving force line before Step 1.4 launches, never fixed in-task, and captured items ride the task's done commit; lightweight record appended to `task-<N>-review.log.md`; orchestrator appends one `inter_review task <N>:` manifest line (tier, workers, rounds, verdict, backlog paths) before Step 1.4; the Recovery path does not run this step [class: IMPLEMENTATION_REQUIRED]
- [x] Add the header opt-out: a plan may declare `Intermediate reviews: off` to skip Step 1.2b; default is on [class: IMPLEMENTATION_REQUIRED]
- [x] Add Hard Gate `25. **Intermediate review before done**`: no Step 1.4 done launch while the task's Step 1.2b verdict is unresolved-blocking or its off-plan backlog items are uncaptured; add anti-pattern rows with lead-ins exactly `Skip Step 1.2b and launch done directly` and `Fix off-plan review findings in-task instead of backlogging`; add launch-rules row exactly `| Intermediate task review workers | Yes (parallel within the tier) |`; state intermediate panels `inherit the 20-minute timeout` and focused-relaunch path; add one sentence to the Budget gate section containing `Step 1.2b is not a budget-gate boundary` (the following Step 1.5 probe bounds the cycle); add integration point heading exactly ``### Consumes `review-panel-selection` skill (per-task intermediate tiers)``; extend the Phase 3 backlog routing (Step 3.3 verification gate item 4) so every durable backlog item records its `Driving force line per receiving-review Backlog capture` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the V5 and V6 gates scoped to `agents/skills/execute-plan/SKILL.md`, and V7 must stay quiet [class: REPOSITORY_TEST]
- [x] Commit: `skills: execute-plan intermediate task review step with backlog funnel` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Authoring tier hint in plans

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the Plan Format rules after the Classification tag rule bullet, add the optional task line `Review tier: <L|M|H>` with guidance: the author sets it when they know the expected review weight; omitting it lets the executor derive the tier from the task's files and changed-content signals; `post-implement risk signals may raise the tier and never lower it`, pointing at the review-panel-selection Task 1 subsection [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the V8 gates scoped to `agents/skills/plans/SKILL.md` [class: REPOSITORY_TEST]
- [x] Commit: `skills: optional per-task review tier hint for plan authors` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Full validation and scans

- [x] Run the whole `## Validation Commands` block → expect exit 0 with `ALL VALIDATION GATES PASSED` [class: REPOSITORY_TEST]
- [x] Run the no-em-dash scan and the public-hygiene scan over the six changed files → expect pass [class: REPOSITORY_TEST]
