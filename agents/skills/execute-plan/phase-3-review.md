## Phase 3: Review / Fix Loop

**Mandatory, not optional:** All tasks `[x]` and green Phase 2 validation do **not** complete execute-plan. Phase 3 must run before Phase 4 archive unless the user **explicitly aborts** after Phase 2 with documented acceptance of skipping review (preserve tmp logs; do not run Phase 5 cleanup).

Run after all tasks are implemented and final validation passes.

**One review iteration** = Steps 3.1 -> 3.2 -> (3.3 if needed) -> 3.4 (light boundary) -> **3.5** exit check.

**Review end condition (aligned with `plans` skill Plan Quality Gate):**

| Gate | Rule |
|------|------|
| **Blocking** | Zero unresolved findings with `blocking: true` after triage; when a recorded residual policy is satisfied, the gate instead accepts the exit report's backlogged-residual tally in place of zero blocking findings (see the Residual-acceptance exit row) |
| **Freshness** | The clean result reviews the current source digest after the latest fix |
| **Full-panel reflection interval** | Reflect at every `max_full_panel_rounds` interval; the interval is not a stop limit. The full-panel round budget derives from the plan's declared execution budget (plans without a declared line keep the flat default 3); delta (focused) rounds never consume it; breach pauses the loop for operator direction per review-plan's Scope and complexity policy pause duty and its breach mechanics before another full-panel round. |
| **Total-round reflection interval** | Reflect at every `max_review_rounds` interval, counting full-panel and focused rounds alike; the interval is not a stop limit |
| **Escalation budget** | At most one escalation worker in the active review run |
| **Residual-acceptance exit** | When a reconciliation pass or the fix-risk triage produces a named fix set, the orchestrator may propose the bounded exit; a standing instruction or explicit user grant records `residual_policy:` in the manifest BEFORE the verification round runs (the named finding set, the grant's source, and the date), same-day recording sanctioned (the pre-archive ordering proof witnesses the ordering at day precision, so only a policy recorded later than the round's day refuses); the exit is one address pass for the named set plus ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups; findings in the named set must reach fixed or dropped; any NEW blocking finding outside the set becomes a durable backlog item with an owner and a trigger instead of another round; the exit report lists the backlogged residuals with their item paths. **Do not** record a blanket `Medium→backlog` residual policy for the lost-work family: `concurrency#*` (which subsumes the currently enumerated `concurrency#cleanup-gated-on-update`, `concurrency#permit-finally`, and `concurrency#terminal-not-partial` entries), `quality#addressable-domain-door`, `quality#port-api-truth`, `quality#typed-catalog-enumeration-door`, and `implementation#typed-enqueue-door`; the family stays fix-or-block unless the user names each finding id in the residual set |

Track in `manifest.md`: review-round number, scope summary, full-panel count, escalation and re-entry counts, source digest, digest-freshness result, last fix commit, recurrence-group dispositions, and the budget reflection.

- `launch-wave`; the launch ledger line (the Quota-wall dispatch doctrine's visibility receipt), one line per dispatch wave per worker role in `manifest.md`'s free-text lines: `launch-wave: <n> <launched|transient|usage-wall> died-at <ISO timestamp|active>`, where `<n>` is that role's 1-based launch sequence at the boundary, equal to that role's existing per-path pass number for single-role waves; a multi-role wave writes one line per role as `launch-wave: <role> <n> <launched|transient|usage-wall> died-at <ISO timestamp|active>` so the lines never collide across roles (the per-role ordinals may repeat); a refused attempt consumes no ordinal and writes no wave line, the `transient` class line being written at the retry's outcome (`died-at active` when the retry launches), and when a usage-wall probe hardens, the probe's single ledger line is written beside the `pre_restart:`/`pre_restart_paths:` pair after the probe's outcome, never a second copy of the wave's line; the ledger rides the existing per-path pass numbering so the manifest alone reconstructs every wave's outcome

- `dispatch_failed`; the typed pre-start dispatch-failure record, one line per pre-start dispatch failure in `manifest.md`'s free-text lines: `dispatch_failed: <ISO timestamp> <worker role> <reason code> pre-start`, its closed reason-code set, the two-line `pre_restart:`/`pre_restart_paths:` state pair, and the bounded-retry budget owned by the Sub-Agent Launch Rules paragraph (the Quota-wall dispatch doctrine block beside it), never restated here

**Dispatch-blocked panel fallback:** when the launch-rules bounded-retry budget is exhausted with every worker dispatch attempt in a round still refused by the provider (a provider-side dispatch block, distinct from a worker timeout or a usage-wall park; the session stays alive and authorized and each refused attempt is recorded per the `dispatch_failed` line above), run the planned lenses inline in the parent session: keep mutation evidence per guarded mechanism the plan actually carries (neuter it, watch a named test fail, restore, cite the pair; a plan without guarded mechanisms owes none), and record the round as a focused panel whose fields describe what actually ran - the dispatch block named in the `selection_reason`, workers launched equal to the lenses executed, and the material lens set scoped to those lenses. Never accept the record producer's full-panel default over what actually ran; the record's honesty grammar (panel mode, coverage vocabulary, lens coverage, and verdict coupling) is owned by `scripts/validate_review_staging.py` and is not restated here, and this route's focused record stays valid notwithstanding the risk-signal floor's focused-validity override, because the record describes what ran.

At every configured reflection interval, record the trajectory and open-blocker counts in the round record, then apply the continuation policy from `review-plan`. A cap alone does not authorize another review round or an operator ask.

**Digest freshness:** At continuation boundaries and before terminal evaluation, verify the latest review record against the current source digest using the repository review-record selector. Record the check's command and outcome. A stale record is not current evidence: run a fresh adversarial round or follow the accepted corrections re-bind process; for the additive class whose delta touches zero record-scope paths and whose changed content the re-bind grading accepts (comment-only script deltas, with seal-path captures beside them), the mechanical route is the re-bind subcommand of `scripts/review_record_selection.py`, and every other staleness class keeps the fresh-round default.

**Digest-family ownership:** the freshness instruments split by family: `scripts/produce_exec_review_record.py` emits plan-family records only (the `-plan-review-` series whose source digest hashes the plan bytes; the Phase 4 exec receipt shares that plan-bytes digest domain), and plan-review record freshness stays owned by the review-plan mechanical gate's `--source-plan` check, while `scripts/review_record_selection.py verify-digest` checks code-family records (the SHA-256 of the `git diff <base>...<head>` bytes) and never accepts a producer record; an exec round reviewing the code delta records freshness through the code-family seal (the Round-close seal duty below), never by running verify-digest over a producer record.

**Provisional vs accepted findings:** dropped false positives do not block. An accepted fix that is proven comment-only may re-bind through a verified corrections row. Any other accepted code change requires a fresh adversarial review. Missing or failed classification takes the fresh-review path.

### Verify-fix vs fresh review (do not conflate)

After Step 3.3 address-review mutates code with anything other than a verified comment-only correction, the **next** Step 3.1 is a **fresh adversarial review**, not a confirmation pass; a corrections-carried comment-only re-bind launches no round per the graded accepted-fix rule above.

| Pass type | When | Prompt framing |
|-----------|------|----------------|
| **Verify-fix** (optional, inline in address-review) | Inside Step 3.3 after fixes | Confirm each fixed finding's executable artifact; re-run validation commands |
| **Fresh review** (every Step 3.1) | Initial full panel or post-fix targeted panel | Current full branch diff; prior findings are context, not a filter |

Every Step 3.1 launched after an accepted fix is labeled in the staging Metadata with the exact line `Review mode: fresh-adversarial`, and its worker prompt must contain the sentence `Prior findings are context, not a review filter; re-derive findings from a first-principles traversal of the complete current diff.`

**Forbidden in Step 3.1 prompts:** verification-only framing that steers workers to rubber-stamp a revision. A verify-fix pass, a unit-only pass, or a verification-only pass never substitutes for the fresh-adversarial round and never satisfies Step 3.4's clean condition.

**Rationale:** A Phase 3 clear streak after a FOR UPDATE fix still missed a High `promoteToActive` miss-path wipe and Medium ensure-then-promote success semantics on explicit must-fix paths. Confirmation framing caused the miss.

### Step 3.1: Parent-orchestrated code review (default)

**Budget gate at this wave boundary:** run the Budget gate and record its fresh decision in `manifest.md` before launching the panel. The probe runs only after the closing round's staging record and sidecar pair are written and validated; the pair, not the manifest summary, is the input (lesson 225). A pause decision stops the wave.

**Before launching:** read the review counters from `manifest.md`. Refuse to launch on an `un-run triggered reconciliation instance`; run review-reconciliation first (Hard Gate 24), then relaunch. If a second escalation would be required, stop at Step 3.5 for user direction. At every configured `max_review_rounds` or `max_full_panel_rounds` interval, record the reflection before deciding whether to continue; coinciding intervals produce one reflection.

**Scope summary (per round, before the first lens launches):** assemble the round's scope summary from the plan's scope declarations, recorded user decisions, and the backlog origins the plan cites as owners of deferred work: the must-fix versus out-of-scope list, naming the owning backlog reference per deferred capability, together with its recorded SOT disposition as reviewer input. Record it in `manifest.md` beside the round entry, stated once per round, and pass it unchanged as every lens worker's `<SCOPE_SUMMARY>` input (Review lens worker template in [subagent-prompts.md](subagent-prompts.md)). A round with no deferred content records an empty summary rather than omitting the block.

**Default (required when the parent can fan out workers):** the execute-plan **parent** is the `doing-code-review` orchestrator. Do **not** wrap Phase 3 in a nested "Code Review" sub-agent that re-reads `doing-code-review` and launches its own panel (double nesting). That hop loses session context, hides progress, and has hung without producing a staging doc.

1. Read `~/.agents/skills/doing-code-review/SKILL.md` and run it in **branch review** mode (not PR mode unless the user supplied a PR URL).
2. Resolve worker set from `review-panel-selection.md` and `<REVIEW_MODE_NOTES>`:
   - Initial pass: per `review-panel-selection.md`; Focused panels arm if all tasks Tier L, no cumulative risk signal (docs-only/test-only).
   - After fixes: blind `correctness-completeness` plus every distinct worker that owned an accepted finding or whose domain the fixes affected.
   - Derive risk signals from the plan's explicit must-fix paths and the current diff, then apply the `risk-signal floor` from `review-panel-selection.md`; record the detected signals in the staging Metadata `Changed-risk signals` field.
   - When concurrency signals exist: load premortem and concurrency inside `risk`; do not launch persona children.
   - For plans whose changed scope is covered by a language overlay, require the Guideline Pack paths and applied rule hints that the `doing-code-review` Step 2.5 mandatory-evidence rules require for that overlay: for Java/Spring plans, the rules the `java-spring.md` overlay's Review-wide Java checks list names; for Kotlin/Spring and Python plans, the rules the overlay trigger tables map to the changed scope. The shared changed-scope trigger surfaces are enumerated once in Step 2.5 and are not restated here. Record `Java guideline checks: #<rules>` (or `Kotlin guideline checks: #<rules>` / `Python guideline checks: #<rules>`) in staging Metadata; a path-only listing without applied rule hints is not sufficient for a clear round.
3. Before launching the round's workers, mint the usage pair per the review-staging skill's "Usage capture (production write path)" section (mint at staging start; if a launch has already preceded the mint, mint late anyway and carry the printed pair verbatim: a late mint still completes the canonical record, with pre-mint worker usage falling outside the attribution window, while the bare-capture fallback cannot complete a post-fence canonical record).
4. Launch **lens worker** sub-agents in parallel, within the host launch limit, using the **Review lens worker** template from [subagent-prompts.md](subagent-prompts.md). Workers analyze; the parent synthesizes the staging doc (orchestrator / sub-agent boundary).
5. Diff scope is **`git diff <BASE_BRANCH>...HEAD`** (all commits on the feature branch for this plan); not the latest commit alone. Apply the plan's **two-tier Review Scope**: findings on **explicit must-fix** paths are always in scope; for unlisted paths, keep findings only when **plan-related** (causally tied to a plan task, explicit change, or contract the plan altered); drop unrelated findings with a one-line reason.
6. **Doc/skill-only plans:** when explicit must-fix paths are Markdown/skills/guidelines and `## Validation Commands` are grep/hygiene (no production mutators), the `testing` worker treats those commands as the primary evidence. Do **not** invent mutation trees, scratch validators, or throwaway harnesses under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`.

**Partial panel:** if a required lens cannot start, record the launched and missing lenses in the review log. Retry the missing lens within the bounded launch allowance; do not synthesize its findings or treat an incomplete required panel as clean.

**Panel completion:** continue triage only after every required lens has returned or the bounded retry has ended in an explicit stop for operator disposition (a provider dispatch block that exhausts the budget is not an operator stop: the Dispatch-blocked panel fallback above is the arm). A partial panel is not a clean result.

**Heartbeat (before waiting on workers):** create or append `<REVIEW_LOG_PATH>` immediately with Pass status `in_progress`: panel worker list, base/head digests, launch time, and the current review round and launch time. A silent multi-hour wait with no log is a skill violation. See [agent-logs.md](agent-logs.md) Heartbeat.

**Timeout (operational):** wall-clock from Step 3.1 start. If **20 minutes** elapse without both (a) a non-empty staging doc at the expected `{reviews_dir}/...-code-review-r<N>.md` path and (b) a non-empty `<REVIEW_LOG_PATH>`, automatically stop the stalled worker, preserve its append-only log, and relaunch a focused panel or continue with bounded parent-inline recovery. Do not ask for routine restart confirmation. Escalate only when the recovery budget or another independent hard gate is reached; never leave a nested or parent-orchestrated review running indefinitely.

**Mutator failure-mode matrix (required in staging doc):** list every new or changed public mutating API on explicit must-fix paths. Missing rows make the round not clean even when no blocking finding remains. For doc/skill-only plans: `N/A: no mutating APIs in this plan`. Matrix rows and the staging doc's Witness ledger rows (per `review-staging`) carry the same evidence obligation: each row names the exact discriminating assertion or structural guard that would fail for the most likely implementation mistake; a row citing only a test name, list position, status code, or manually configured fixture fails that obligation when the invariant at risk is index preservation, wire serialization, downstream response, or mode preservation.

Review output: `{reviews_dir}/YYYY-MM-DD-<plan-slug>-code-review-r<N>.md` (increment `N` each round; use `-code-review-r` prefix to distinguish from pre-execution **plan** reviews at `…-plan-review-r<N>.md`).

**No forward references to unwritten staging paths:** do not cite a staging-doc path in the manifest, `<REVIEW_LOG_PATH>`, worker prompts, or user reports before the file exists at that exact path; write the doc first, then reference it. When re-synthesis or re-entry changes a staging path (new `-r<N>` number, renamed slug), grep the session logs and manifest for the old path and update every reference in the same turn. Stale pre-writes drift into phantom references that later steps and reviewers chase.

**Default:** the parent owns `<REVIEW_LOG_PATH>` per the log-assignment rules above; lens workers get no log paths of their own; an emit-early path the parent names for the liveness duty is the one exception, written before each deep verification pass. The parent names one emit-early path per review worker when the round launches, a per-worker file distinct from the Phase 3 review log. For a sequential address round, the receiving-review worker owns and closes the address log; the parent verifies it (a heartbeat-only log fails Step 3.4). **Recovery:** the Code Review (recovery) template's nested orchestrator owns `<REVIEW_LOG_PATH>`. Pass `review_round` / `<REVIEW_ROUND>` = current `review_round` from manifest. Worker returns append their findings to the round log on return, so a record owed at resume is composed from logged output; the WIP checkpoint commit does not cover gitignored records (lesson 225). A consolidated round record written at any path outside agent-logs.md's path table never substitutes for the per-step contract paths.

**Diff snapshots (optional):** If the parent materializes diff files for parallel workers, they must live only under `{tmp_dir}/execute-plan/<PLAN_SLUG>/` as `diff-r<R>.patch` and `src-diff-r<R>.patch` per `doing-code-review` **Diff access**. Phase 5 cleanup removes session diff snapshots with review logs.

**Recovery only (parent cannot launch review workers in parallel):** use the **Code Review (recovery)** template from [subagent-prompts.md](subagent-prompts.md). That template requires a **Session handoff** block (digest, commits, validation status, known run incidents / intentional deviations, Review Scope excerpt). Prefer restoring direct parent orchestration when the host supports it. Never use recovery to reintroduce silent double nesting when the parent can launch workers.

**Step 3.1 verification gate (orchestrator, before Step 3.2):**

1. Staging doc exists at the exact `{reviews_dir}/...-code-review-r<N>.md` path and is non-empty (chat summary alone does not satisfy Step 3.1).
2. `<REVIEW_LOG_PATH>` exists and is non-empty AND its final Pass block records terminal Status `success` or `blocked`, never `in_progress`.
3. Doc follows `doing-code-review` staging format sufficiently for Step 3.2 parsing (findings with Severity/Status/Triage) and includes populated `## Review Statistics` per `review-staging` (including Solo/Echo, Pattern, Severity calibration).
4. Doc includes `## Mutator failure-mode matrix` with a row per new/changed public mutator on explicit must-fix paths (or an explicit `N/A: no mutating APIs in this plan` line). Incomplete matrix → relaunch Step 3.1.
5. On post-fix rounds (a non-null `last_fix_commit`), the staging doc carries either a populated `### Witness ledger` or the Metadata `Witness ledger: N/A (no public mutators)` empty shape per `review-staging`; a post-fix round with neither fails this gate. Incomplete ledger → relaunch Step 3.1.
6. When concurrency signals exist, the `risk` row records `concurrency` and `premortem` as loaded lenses unless the user explicitly skipped premortem. Escalation carve-out (the counterpart of item 7's partial-panel arm): when the round is an escalated partial panel per the partial-panel completion rule and the refused lens is `risk`, no `risk` row exists and a provider refusal is not the user-skip exception, so this item is satisfied by the recorded escalation naming the missing lens (the premortem duty attaches to the later boundary that deliberately completes the panel with the risk lens launched), and the round proceeds to triage per the completion rule; on any round whose `risk` lens launched, this item still applies unchanged.
7. **Panel actually ran:** a full-panel pass has complete rows for `correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, and `risk`. A focused follow-up records its selection reason. An incomplete panel cannot be reported as clean; record missing lenses and stop for operator disposition after the bounded retry.
8. The staged record and its `.stats.json` sidecar pass the existing staging validator (mechanical evidence for item 3's format criterion): run `python3 scripts/validate_review_staging.py --hard <record>` and continue only when the command succeeds and its final outcome line is `OUTCOME: pass`; exit code zero alone is insufficient because soft mode (without `--hard`) can report `OUTCOME: fail` at exit 0. A validator `tool_error` or `indeterminate` outcome stops the gate for re-derivation from disk (the invocation or record surface is the defect), never a worker relaunch.

If any check fails, relaunch the missing workers or re-synthesize the staging doc; do **not** enter Step 3.2 or launch address-review. An escalated partial-panel round that passes through item 6's escalation carve-out and item 7's partial-panel arm does not fail into this relaunch fallback; it proceeds to triage per the partial-panel completion rule.

### Step 3.2: Triage input (doing-code-review)

Parse the staging doc at the verified path. Count unresolved findings with `blocking: true`.

| Finding | Action |
|---------|--------|
| `blocking: true` and unresolved | Launch Step 3.3 (`receiving-review`) |
| `blocking: false` | Triage by consequence; does not by itself block completion. Valid ones not fixed on this branch get durable backlog items per `receiving-review` **Backlog capture** |

**Do not use Step 3.2 counts for loop exit.** They only decide whether Step 3.3 runs. Exit criteria are evaluated in Step 3.4 after triage.

Compare rounds: if a finding is identical to a prior round and was already fixed, downgrade to duplicate and drop; do not loop forever on stale comments.

Class membership in the two backlog-by-default classes defined by `receiving-review` (sibling-doc restatement, duplicate unit witness) is decided by the receiving-review pass (sub-agent or inline) during Step 3.3 triage, never by the orchestrator here; a blocking candidate still takes the Fix-risk blocking re-evaluation and is never silently backlogged.

When Step 3.2 shows no unresolved blocking findings and Step 3.3 is skipped, the orchestrator still routes non-blocking residuals through a receiving-review pass (which may run inline) applying the owner rules per `receiving-review`; the pass fixes findings it does not defer (mutating the digest and restarting the fresh-review rule), and deferred findings (the two classes, user-deferred, scope-dropped) become durable backlog items per `receiving-review` **Backlog capture** (for the two classes, pointer-cleanup and family-completeness items) before the clean row may exit. Deferrals of the two classes are classify-and-record only, with evidence per `receiving-review`.

**Out-of-scope adjudication (scope summary):** a staged finding whose subject the round's scope summary marks out of scope triages as `dropped` in the sidecar triage field (the staging Status token spells the same disposition, `drop`), and is never promoted to a blocking gate for this execution. The finding's consequence and the round's synthesis record the owning backlog reference and the residual risk. That owning reference satisfies the backlog-capture requirement of the not-fixed `blocking: false` table row above and of the skip-path paragraph above; never create a duplicate backlog row where the cited owner exists. Only a finding whose out-of-scope subject has no cited owner takes the ordinary durable-backlog-item path, and residual risk stays recorded in the consequence in both arms. Plan-review rounds sit outside this rule: the review-plan loop's rounds receive the full plan and no scope summary, so they carry nothing to adjudicate against.

##### Recurrence evaluation (mechanical, every round)

Normalize each unresolved blocking finding in the current staging doc to a root group per review-reconciliation `"Reconciliation method" step 1`; the normalization semantics are owned there and are not restated here. Update the `recurrence_groups` manifest line with one entry per group carrying the normalized root, the rounds it appeared in, and the change relation. The evaluation runs every round: round 1 records groups without comparing because no prior round's line exists, and from round 2 on the comparison runs against the previous round's recorded groups. The trigger fires when the same root group appears in two consecutive rounds, or when any blocking finding's files intersect the changed files of `last_fix_commit` (`git show --name-only --pretty=format: <sha>`); record the trigger status `triggered` with the group names, or `clear`, on the same line.

The two mechanical arms are a witnessed subset, not a replacement: shapes neither arm catches (cross-file regeneration under a brand-new root group, artifact contradiction) remain owned by the Step 3.5 reconciliation row; configured reflection intervals alone do not trigger reconciliation.

### Step 3.3: Address review findings sequentially

When Step 3.2 leaves unresolved blocking findings, launch one address-review worker for the current finding set using the receiving-review contract. Pass the finding data, canonical affected paths, round context, and log destination. Do not fan out address workers. The parent verifies each proposed change against review scope, applies accepted changes, updates the staging doc, and records every valid unfixed finding in the backlog before the iteration's light boundary.

Use bounded retry only after verifying the prior worker is terminal. If terminal status is unknown, make no edits from that worker's task and launch no duplicate. When Step 3.2 leaves no blocking findings, skip the worker and continue to Step 3.4; record any valid non-blocking residuals through the normal backlog process.

### Step 3.4: Evaluate the current digest and run the light boundary

**Clear round (code-mutation gate, graded):** A round is only "clear" if no code changes were made to fix issues, except a corrections-carried comment-only delta: findings marked `drop` (false positives) do not mutate code, and findings marked `done` (fixed) mutate code and require a fresh review unless the fix's delta is proven comment-only by `scripts/code_delta_classifier.py` and carried by a verified corrections row, which re-binds with zero rounds per the graded accepted-fix rule above.

Backlog items, manifest updates, and disposition notes are bookkeeping, not digest mutations; only changes to reviewed source scope count.

| An address pass ran (Step 3.3 launch or the Step 3.2 skip-path receiving-review pass)? | Result |
|---------------|--------|
| No (no address pass ran, or the pass neither accepted fixes nor mutated the digest) | Clean when zero unresolved blocking findings and the quality bar passes |
| Yes, via the skip-path pass with accepted fixes | Not clean unless the accepted fixes' delta is a verified comment-only correction per the graded accepted-fix rule; otherwise the changed digest requires a fresh targeted review (a same-pass pointer conversion counts as accepted fixes) |
| Yes, via the Step 3.3 address pass with accepted fixes | Not clean unless the accepted fixes' delta is a verified comment-only correction per the graded accepted-fix rule; otherwise the changed digest requires a fresh targeted review |
| Yes with drops and/or two-class deferrals only (no accepted fixes, no digest mutation) | Clean when zero unresolved blocking findings and the quality bar passes |

**Clear-round quality bar:**

1. **Mutator failure-mode matrix** present and complete (Step 3.1 gate #4); every mutator row has IT evidence, a staged finding, or `checked: yes` with a concrete pointer.
2. **Not a discard-only quiet round without adversarial depth:** If raw findings were non-zero and **all** were discarded as `noise` / `already-mitigated` / `prior-review`, the review log or staging Analysis must still show the failure-mode matrix was filled from code/IT evidence (not left empty). An empty matrix plus "no findings" after a fix round is **unclear**; relaunch Step 3.1 with fresh-review framing.
3. Required conditional risk lenses were loaded.
4. For Java/Spring plans, the staging Metadata records the required shared
   Java/JVM/coding guideline paths and applied rule hints. The review evidence
   covers changed declarations, nullable boundary states, downstream error
   payload sinks, changed dependency coordinates, outbound URL transport
   configuration, shared-helper raise-versus-degrade tracing,
   feature-flag and configuration matrix coverage, timeout transport
   boundaries and scheduled timeout resource lifecycles,
   executable compatibility witnesses for changed direct API usage (or the
   guideline #24 static-analysis fallback with its durable-record residual), and
   living-documentation status reconciliation, when those surfaces are present.
   For Kotlin/Spring or Python plans, the staging Metadata likewise records the
   overlay guideline paths and applied rule hints per Step 2.5, and the review
   evidence covers the evidence surfaces of the applied hints.
5. **Last-fix ordering:** the clean round's reviewed head includes the last accepted-fix commit as ancestor-or-self (`git merge-base --is-ancestor <last_fix_commit> <clean-round-head>`; in the canonical loop the post-fix review runs at HEAD equal to the fix commit, which satisfies ancestor-or-self). The manifest records `last_fix_commit` when any address pass accepted fixes, and the orchestrator runs that check before treating the round as clean.
6. **Release-gate ledger complete (per `review-staging`):** when the plan explicitly assigns a boundary to later work, the staging doc's `## Release-gate ledger` records every required field for each deferred boundary (missing capability and owner, unsafe current path and configuration, permitted deployment mode, shippability condition, classification, accepted-residual rationale); an incomplete ledger is not clean. The ledger is a handoff artifact only and never authorizes expanding the plan's scope.

Record the current source digest and panel counters in `manifest.md`.

**Round-close seal (code family):** closing any round that certified code bytes records the certification seal entry in the local seal file `.ai-playbook/review-certs/<artifact-slug>.md` as part of the round-close step: the seal block grammar and plan-family example documented in the review-plan skill. Code-family entries carry `family: code`, `staging_round: rN`, and the certified range as `reviewed_base:`, `reviewed_head:`, and `range_digest:`; lookup uses family and staging round. The seal is the producer the code family's validator context consumes (`--source-code-repo` reads it, compares the sidecar's recorded range against it, and grades a declared corrections chain through it), and the seal path is excluded from diff classification. For code-review records, the boundary freshness instrument beside this seal duty is the Phase 3 `verify-digest` check (the digest-freshness duty and digest-family ownership above).

**Loop exit condition:** one fresh clean review of the current digest, or a re-bind through verified comment-only corrections rows per the graded accepted-fix rule above (each pointing at that graded Phase 3 text instead of restating its mechanics). Do not run a second clean full panel on the same digest.

**Escalation limit:** do not launch a second escalation within the active run without stopping for user direction. Full-panel and total-round settings are reflection intervals, not launch caps.

**Launch validation (before the boundary):** for every preceding-step log path this boundary will read, verify the file exists at its exact contract path and its final Pass block's Status is not `in_progress`; a missing or heartbeat-only log stops the boundary; the parent finalizes the log from the round's durable records that actually exist (the staging doc, the worker returns), marking the reconstruction and any missing raw worker evidence in the log body, and where no durable record carries a worker's findings the log is not reconstructed: the round re-runs per the review-round contract and the refusal stands until a genuinely produced log exists; worker output is never synthesized; the required set is the review log and, when Step 3.3 ran, its single sequential address-review log

Run the light boundary of Step 1.4 for this iteration; the parent runs it itself, no boundary sub-agent is launched. The boundary's `learn` leg **reads the round's preceding-step logs only**; not implement logs or prior review rounds; per the review-round log handoff in [agent-logs.md](agent-logs.md), which is unchanged:

- `<REVIEW_LOG_PATH>` from Step 3.1 (required)
- `<ADDRESS_LOG_PATH>` from Step 3.3 (required only if the sequential address-review worker ran; otherwise omit)

The run briefing path and `manifest.md` are run context and traceability, not preceding-step logs; neither is a required read that blocks the boundary commit. The plain commit carries this iteration's accepted fix paths, the captured backlog items, and the previous boundary's learn-authored corpus paths, with the why-first message (suggested subject: `fix: address plan review r<REVIEW_ROUND> findings`; when address-review did not run, the commit carries whatever else the iteration produced, and when the candidate set is empty the boundary records the explicit justified `nothing to commit` outcome instead of composing a commit).

**Do not return to Step 3.5 until the light boundary completes.**

The parent must then execute Step 3.5 in the same active run. Do not send a final response merely because the boundary completed; it is an iteration checkpoint, not an execute-plan terminal state.

**Boundary verification gate (orchestrator, before Step 3.5):**

1. the boundary's learn confirmed it read preceding-step logs only (review log; address log if the sequential Step 3.3 worker ran).
2. the boundary returned a commit SHA, or an explicit justified `nothing to commit`.
3. `git log -1 --oneline` reflects that commit when one was expected (address-review ran with file changes).
4. `git status` has no unstaged files from this iteration's fix scope.

### Step 3.5: Continue or exit loop

Update `manifest.md` with `review_round`, `full_panel_rounds`, `escalation_count`, `re_entry_count` (reset each round), the `standing_continue` state, and `source_digest`.

| Condition | Action |
|-----------|--------|
| Current digest has a fresh clean review satisfying the clear-round quality bar, including exit coverage per `review-panel-selection` | Proceed to Phase 4; the loop may not exit with a returned-for-ask presentation outstanding: an interactive run performs or gets the fix-risk ask answered before proceeding; a non-interactive run discharges any outstanding non-blocking ask by recording and surfaces the recorded question in the exit report (the recording discharged it for a non-blocking ask; not treated as backlogged); where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts, the clean review is no longer fresh and the loop returns to Step 3.1 with the standing_continue line left open |
| A recorded residual policy is satisfied (the exit's one address pass and ONE focused targeted round composed per `review-panel-selection` Targeted follow-ups completed, the named set reached fixed or dropped, and every out-of-set new blocking finding carries its durable backlog item with an owner and a trigger) | Proceed to Phase 4 under the Residual-acceptance exit: the clear row's blocking-clean requirement does not apply under the recorded policy; before routing, the orchestrator diffs the address pass's changed files against the named set and routes any out-of-set change back to a normal fresh round instead of the exit (return to Step 3.1 with the targeted worker set); the exit report lists the backlogged residuals with their item paths |
| Configured reflection interval is reached | Record the trajectory reflection as specified above; continue without a cap-only prompt when results converge. For non-convergence, reconcile and apply the single automatic simplification/refactor attempt before deciding whether another review can run |
| Recurring root, contradictory review artifacts, or configured non-monotonic-cycle cap is reached | The trigger is evaluated mechanically every round (Step 3.2) from the `recurrence_groups` line, not only at the cap: when an instance is `triggered` and no reconciliation ledger path is recorded for it, invoke `review-reconciliation` in-loop before the next panel (the outstanding-ask wait before any next Step 3.1 launch, Step 3.3 gate item 6, still applies), record the ledger path on the `recurrence_groups` line, and return to Step 3.1 through the normal parent-orchestrated panel; reset the affected groups' counters only after the fresh post-reconciliation review completes clean, and when the same root group reappears after the reset, retain the recurrence chain and escalate per review-reconciliation "Return control to the original orchestrator"; where fix-risk stop conditions also hold, take the Fix-risk direction per Hard Gate 23 (any such reconciliation still runs first) |
| A second escalation is required | Stop; report unresolved blocking findings and ask the user |
| Fix-risk stop conditions met (must-stay-blocking finding with no additive path or user; Hard Gate 23) | Stop; ask the user for direction per `receiving-review` **Fix-risk triage when fixes regenerate findings** |
| Otherwise | Return to Step 3.1 with the targeted worker set |

Either Proceed-to-Phase-4 row (the fresh blocking-clean row and the satisfied residual-acceptance row alike, accepted named findings included) carries a receipt-production duty: before the loop hands off, Step 3.5 writes one dated execution receipt under `{reviews_dir}` named `<date>-plan-review-<plan-slug>-exec-r<N>.md` carrying the SHA-256 of the final Phase 3 plan bytes plus pointers to the run's own Phase 3 `-code-review-r<N>` staging record pair. `scripts/produce_exec_review_record.py` is the repeatable minter only for plan-review-family records (for example the Phase 2 progress-tick re-bind round), whose output name grammar and identity token differ from the `-code-review-r<N>` family the receipt cites. A continue decision (any return to Step 3.1 for another round) writes no receipt; the next exit writes exactly one.

Any stop for user direction from the rows above or the counting paragraph below (the reflection/non-convergence stop, the escalation row, the Fix-risk stop row, and the re-entry mid-round stop) must relay outstanding (undischarged) or recorded-but-not-yet-surfaced returned-for-ask questions alongside the other ask content and any failure, timeout, or interrupt user ask, and, where a session note applies (the re-entry mid-round stop waives it), the short session note lists them among the unresolved residuals by class.

Every launch of a Step 3.1 review panel increments `review_round`, except a verification-gate or timeout re-entry that re-checks or re-synthesizes the same round's staging doc without re-running workers. `review_round` starts at 0, so the initial review is round 1. A relaunch that starts a new review round (a next `-r<N>` staging doc) counts as a launch. A re-entry that re-runs workers within the same round counts as a launch too: it advances `review_round`, is tracked as `re_entry_count` in the manifest (the counter resets each round; the launch itself does not reset it), and continues the same round's `-r<N>` staging doc as an appended pass, so staging-doc numbering and `review_round` may diverge after a counted re-entry. An uncounted re-entry (re-checking or re-synthesizing without re-running workers) advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`. When `re_entry_count` reaches 3 within the same round, stop the loop and ask the user before any further re-entry (a mid-round stop: no session note is required, and a standing continue instruction does not lift this stop). The configured `max_review_rounds` and `max_full_panel_rounds` values are reflection intervals, not launch limits. Counted launches continue to advance `review_round`; the re-entry stop above remains a separate guard.

Retain any `standing_continue` record for its existing session-scope and exit bookkeeping; it does not govern reflection intervals or lift any independent stop condition.

The escalation limit and all independent timeout, re-entry, material-user-decision, and no-progress reconciliation stops remain in force. The Step 3.5 manifest update records the round just completed and never advances the counter. Any loop exit, including a user-directed stop from a stop row, closes any standing_continue line as `standing_continue: ended` with the exit reason.

**Budget gate:** run the Budget gate here per the Budget gate section; on a pause the run stops at this boundary.

