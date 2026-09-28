Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root.
- Freeze rule: when authoring for an entry has started (a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory, or a live authoring worktree or branch for its plan), the entry is marked frozen before any further log processing: a `Frozen:` line naming the witness and date goes directly under the entry's heading. A frozen entry accepts no origin additions, no prompt rewrites, no repositioning, and is never a dispatch candidate; the mark is removed when the authoring aborts without a plan file in the plans root (the entry reopens), and the entry is pruned outright per the prune rule when its plan file lands.
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Entries carry repo-relative paths only and no personal or machine-specific data.
- An entry is a prompt for a later authoring turn; the write turn never executes or dispatches its payload.

Entry template (one section per entry):

```
## <short-slug>

Added: <date and provenance>

Origins:
- docs/history/backlog/<origin>.md

Urgency: <judgment: class, witness, relative queue position>

Prompt: <full ready-to-dispatch authoring prompt payload>

Rejected alternatives:
- <one line per rejected alternative, with the reason>
```

## p90-execute-plan-invocation-scope-revalidation

Added: 2026-09-29 (investigate skill, interactive scope-correction witness)

Origins:
- docs/history/backlog/2026-09-29-execute-plan-prior-invocation-scope-leak.md

Urgency: High; a prior execute-plan selection was carried from one plan objective into a later authoring-and-merge request, causing an implement worker and runtime claim to start before the user corrected the scope.

Prompt: using the plans skill, author one focused implementation plan (authoring only, do not execute) to bind execute-plan continuation intent to the active plan and objective. Read the origin backlog in full and inspect the current execute-plan invocation detector, its change history, and any tests or evals that cover prior gate choices. Preserve seamless continuation within a single explicitly selected plan run. Specify that every new user message is checked for a clear objective or plan switch before prior invocation state is reused, and that a current authoring, review, or branch-landing request supersedes stale execution intent unless execution is explicitly resumed in the current request. Include deterministic positive and negative witnesses: same-plan explicit continuation remains invoked; author-and-merge after a prior execute choice remains authoring-only; a bare plan reference follows the plan-path gate when no active matching execution run exists; and explicit user narrowing immediately stops implementation activity. Keep commit, merge, and push authorization separate from plan execution. Do not broaden the change into a general session-memory redesign.

Rejected alternatives:
- Removing prior-choice continuation entirely: rejected because it would reintroduce repeated gates within one active plan execution.
- Treating "finish the plan" as execution by default: rejected because it conflates plan authoring with task implementation.
- Reusing any earlier session choice regardless of current objective: rejected because current user intent can replace prior scope.

## p80-execute-plan-baseline-satisfied-task-closeout

Added: 2026-09-28 (investigate skill, consumer execute-plan blocker)

Origins:
- docs/history/backlog/2026-09-28-execute-plan-preimplemented-task-closeout.md

Urgency: High; witnessed active execution is fenced at `done-pending` despite terminal worker evidence, a passing task-local validation, and implementation already present at the claim baseline. This is a distinct completion-boundary gap from p78's claim admission and terminal reservation defects, though the runtime code and tests overlap.

Prompt: using the plans skill, author one implementation plan (authoring only, do not execute) to close out execute-plan recovery tasks whose implementation already exists at their claim baseline. Read the origin backlog in full and re-verify current code, contracts, tests, and the completed recovery plan before fixing scope. The witnessed consumer case had source paths unchanged from the task baseline, valid task-local test evidence and terminal worker evidence, but the driver's done handoff rejected the only closeout commit because it changed the plan checklist outside `allowed_paths`; `commit_identity: none` is intentionally unavailable to a plan task with a `Commit:` criterion, and the baseline implementation commit is not new work. Specify a driver-owned, receipt-fenced recovery completion arm for this exact shape: bind task id, token, generation, plan digest, current allowed paths, exact source snapshot, verification command identity and result, terminal worker receipt, checklist state, and done log; prove source equals the claimed baseline and satisfies the task's required criteria; use a distinct auditable recovery completion identity; atomically close the claim and advance. Preserve ordinary task done commits and the existing `none` arm unchanged. Include negative cases for changed source, missing/stale validation, plan or allowlist drift, foreign/stale identity, replay, and any task whose implementation is not demonstrably complete at baseline. Recovery-mode orchestration must use this arm without manufacturing edits, loosening path boundaries, or editing the manifest directly. Add acceptance tests for the complete unchanged-baseline case and each refusal, and update the skill/runtime contract to route only that proven shape. Include the consumer workaround path in scope only if it can be completed through supported driver transitions without weakening fencing; otherwise document it as a separately bounded limitation. Keep this a focused runtime-contract plan, not a broad redesign of claim fencing or done commit policy.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Marking the task complete from the plan checkbox or worker prose alone: rejected; neither proves the source snapshot or driver-owned validation/terminal evidence.
- Reusing `commit_identity: none` for implementation tasks: rejected; its current contract is explicitly reserved for tasks with no `Commit:` line.
- Expanding task allowlists to include the plan file: rejected; checklist closeout is not implementation evidence and would weaken task-scoped commit boundaries.
- Creating an unrelated source edit only to mint an allowed commit: rejected; it manufactures code churn and can conceal missing criteria.
- Editing `runtime_state.json` directly or bypassing the claim fence: rejected; recovery must remain a locked driver transition with exact receipt identity.

## p92-authoring-payload-park-discharge-explicit-root

Added: 2026-09-29 (grouping pass, single-origin carry from the unassigned backlog)

Origins:
- docs/history/backlog/2026-09-28-maintenance-authoring-park-discharge-cwd-relative.md

Urgency: High; consumer urgency witnessed class. The authoring payload's CLOSING PARK DISCHARGE DUTY paragraph (agents/skills/maintenance/prompt-templates.md, "read .ai-playbook/scheduler-state.json" bare) still reads the state file cwd-relative, so an authoring child running in its ad-hoc worktree discharges parked intents against the per-worktree gitignored state copy no reader reads: the discharge silently no-ops and the parked intent survives unowned. The execution and unblock-child discharge twins were rooted by the worktree-first r4 fix; the authoring twin was missed, so the once-identical paragraphs have already diverged once.

Prompt: using the plans skill, author one small plan (authoring only, do not execute) rooting every cross-checkout scheduler-state access in the maintenance payload bodies. Read the origin's full text and treat it as the scope of record. Re-verify on disk before pinning: the r4 fix's explicit-rooted clause sits on four sites (authoring successor-carrier closeout verification, execution successor dispatch, execution closing park discharge, unblock-child closing park discharge), and the authoring body's CLOSING PARK DISCHARGE DUTY paragraph is the remaining bare read. Scope arms: (1) apply the same explicit-rooted clause (read and write the primary checkout's `.ai-playbook/scheduler-state.json`, explicit-rooted form per the claim duty's precedent) to the authoring body's discharge paragraph; (2) honor the origin's round-5 refinement: the FIRST ACTION re-arm state probes stay bare-by-design (they fire pre-worktree, in the primary checkout where the bare read resolves the real state file) -- record that half as withdrawn in the plan, never rooted; (3) a mechanical guard (a pins-suite grep arm or a test) fails when any post-worktree scheduler-state access inside either payload body lacks the explicit-rooted clause, so the twins cannot silently diverge again; (4) re-run the pins suite and re-key any shifted anchor in the same edit; (5) the vendored twin (runtime-side agents/skills/maintenance/) carries the same bytes in the same run or a tracked landing path.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Rooting the FIRST ACTION re-arm probes too: rejected by the round-5 re-derivation; those probes run before the ad-hoc worktree exists, where the bare read is correct.
- Editing only the discharge line and trusting the twins to stay in sync: rejected; the r4 fix already diverged the once-identical paragraphs, so the guard arm is the fix, not the line edit.
- Moving discharge duties out of the payload bodies: rejected; scope creep beyond the witnessed defect, and the discharge duty's home is the payload closeout.

## p93-review-posting-landing-evidence

Added: 2026-09-29 (grouping pass, two-origin review-workflow group)

Origins:
- docs/history/backlog/2026-09-28-review-posting-completion-evidence.md
- docs/history/backlog/2026-09-28-review-staging-integration-points-review-plan-row-stale.md

Grouping: one group over the review workflow's reporting-truth surfaces: a consumer-company witnessed gap where the completion report and the POSTED state ran ahead of live PR comments (doing-code-review posting flow plus the staging validator), beside the now-due companion landing row the completed sidecar-schema-drift plan left stale (review-staging's Integration Points table still advertises "inlines sidecar schema (Step 3)" while the completed plan shrank Step 3 to a stable-core summary; verified stale on disk 2026-09-29). Shared surface: the review skills' completion and reporting contracts and their validators; both fixes are truth-in-reporting, and neither changes review verdicts.

Urgency: High; the first origin is consumer-company witnessed (the user saw only the approval while the agent reported four inline findings landed; the existing post-submission verification requirement was skipped and nothing mechanical caught it), and the second is a tracked landing path already owed by a landed plan.

Prompt: using the plans skill, author one plan (authoring only, do not execute) over review completion evidence and staging-row sync. Read each origin's full text and treat the files as the scope of record. Scope arms: (1) posting receipt: trace the doing-code-review posting flow (Posting Staged Findings and Direct Mode) and add the smallest machine-checkable receipt that binds each intended finding identity to a live PR comment fetched after submission, matching by path, line, and a distinctive body fragment; the completion report and the staging record's POSTED transition are both allowed only when the full intended set matches; (2) a missing or mismatched comment routes through the existing individual-repost recovery followed by full-set re-verification, and an incomplete outcome is recorded, never smoothed over; (3) keep the existing live-verification rule and incomplete-status behavior intact -- the receipt enforces them, never replaces or weakens them; (4) focused coverage: a successful batch, a silently dropped finding, a mismatched comment (path/line/body), and a successful recovery; (5) the review-staging row: re-verify the completed drift plan's landed bytes, then reword the `review-plan` row of the Integration Points table to the stable-core-summary form (the enforced contract is the validator and review-staging's authoritative copy; the `--hard` validator gate stays named), a one-line edit touching nothing else in the file; (6) integration points land in both directions per the corpus convention (doing-code-review names the receipt's staging counterpart; review-staging's row matches the landed reality).

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Treating the provider's submission success response as landing evidence: rejected; that trust is the witnessed failure.
- Batch-reposting all findings when one is missing: rejected; it duplicates live PR comments, and the individual-repost recovery path already exists.
- Editing review-staging inside the drift plan retroactively: rejected by that plan's scope decision; the row lands as the tracked companion item it was filed to be.
- Blocking POSTED on a human eyeball check: rejected; the requirement already says verify live -- the gap is that nothing mechanical fails the skip, so the fix is a machine-checkable receipt.

## p94-skill-description-length-gate

Added: 2026-09-29 (grouping pass, single-origin carry; witnessed the same day in this repository)

Origins:
- docs/history/backlog/2026-09-29-skill-description-length-gate.md

Urgency: High; witnessed 2026-09-29 in this repository: execute-plan's folded description reached 1167 characters and the runtime silently dropped the skill from the registry (recovered by the trim landing f6a135a6); agterm sits at 956 as the next candidate, and the 1024-character cap exists only as prose in how-to-write-skills with no mechanical check anywhere (re-verified 2026-09-29: no scan arm, no validator, no script).

Prompt: using the plans skill, author one focused tooling plan (authoring only, do not execute) adding a mechanical SKILL.md description-length gate. Read the origin's full text and treat it as the scope of record. Scope arms: (1) extend the public hygiene scan (or a sibling check wired into the done pre-commit sweep gate) with a description-length arm: parse each SKILL.md frontmatter bounded to the closing `---` fence, fold `>`/`|` block scalars to single-spaced text, measure the folded description, fail over 1024 characters, and warn over about 950 so chronic growers are visible before they trip; (2) the parse bound is load-bearing and tested: a greedy indented-line match swallows fenced code blocks in the body, so the fixture set includes a skill whose body carries fenced blocks containing dashed lines and indented text, asserting the measured length stays bounded to the frontmatter; (3) the gate runs green over the whole corpus at landing (execute-plan trimmed to 922, agterm 956 warned); (4) the cap and warn thresholds are named constants, and how-to-write-skills' Frontmatter Requirements names the gate in both directions per the Integration Points convention, so the rule text and the enforcer cannot drift apart.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Fixing only the two witnessed skills: rejected; the failure mode is silent, so only a corpus-wide gate closes the class.
- A warn-only gate: rejected; a warning is exactly how the 1167-character drop shipped.
- Enforcing at runtime registration: rejected; the runtime is an external host surface this repository does not own, and the drop happens before any repo-side code runs.
- Measuring raw (unfolded) description bytes: rejected; the runtime folds block scalars before applying the cap, so unfolded length misclassifies.

## p95-interrupted-run-stranded-work-prevention

Added: 2026-09-29 (grouping pass, single-origin carry of the six-idea prevention set)

Origins:
- docs/history/backlog/2026-09-29-interrupted-run-and-stranded-work-prevention-ideas.md

Grouping: single origin carrying six witness-gated prevention ideas (A-F) from one day's three witnessed failure classes: teardown before closeout (the unadoptable interrupted manifest 20260929T023532Z-3fb1c11bb98b), killed sessions stranding finished captures (landed only after 13 hours as ee0b2e15), and one-shot shell lock-token loss eating a live run's lock. Family cross-references: facet A extends the worktree-closeout-baseline-capture origin (logged in p80-worktree), facet B the done-manifest-root-identity origin (plan-covered), facet F the done-lock-one-shot-reclaim docs origin (plan-covered); loop darkness is owned by the executed maintenance-autonomous-pipeline plan and is out of scope.

Urgency: High; all three witnesses are same-day, each left work stranded or noisy for later sessions, and the cheap half (B+D) kills a perpetual advisory that every later Step 0 re-reports.

Prompt: using the plans skill, author one plan (authoring only, do not execute) implementing the prevention idea set in the origin file's value order, re-verifying each idea's witness and current machinery at authoring time. Read the origin's full text and treat it as the scope of record. Scope arms, in the file's order: (1) B+D first: a sanctioned disposition record for unadoptable manifests (a finalize variant accepting a verified-deliverables witness -- each owned plan, review, and owned path checked landed -- or a disposition sidecar the Step 0 reader honors), plus the maintenance survey arm classifying complete=false manifests by root liveness (a live root proposes a resume dispatch parked like other intents; a dead root proposes the disposition once), so the report reads "dispositioned: work verified landed, owner root gone" instead of re-reporting the interruption forever; (2) E: generalize the rolling prompt log's same-turn commit rule to all backlog-file writes, with a parked recovery note naming any file left uncommitted at turn end; (3) A: the closeout-before-teardown gate (worktree and branch removal refused while any complete=false manifest binds the worktree's root digest), coordinated with the p80-worktree-closeout log entry that owns the same surface -- if that entry's plan has landed by authoring time, fold A as a delta there or absorb its origin; if not yet authored, keep A here and record the split in both surfaces; (4) C: the done-tail resume carrier extending the budget-gate resume watcher to the write-manifest-to-finalize span; (5) F: lock-token durability (holder-PID pin detection for one-shot shell callers with a warn-or-refuse, and acquire exports recorded as a release backup), additive to the p79-plan-covered docs origin -- re-verify that plan's execution state first; (6) keep every addition witness-gated per the active-elimination doctrine, and strike any idea the executed pipeline plan's stall-recovery tasks already absorb.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- One flat six-idea pass without the value order: rejected by the origin's own ordering; B+D retire the perpetual advisory cheapest and de-risk the rest.
- Auto-deleting interrupted manifests as the disposition: rejected; the witnessed disposition requires verified-deliverables evidence, never silent deletion of an unresolvable record.
- Re-implementing loop-darkness recovery inside this plan: rejected; the executed maintenance-autonomous-pipeline plan owns that class.
- Splitting the ideas file into six separate backlog items: rejected; the file is the origin of record with its own cross-references, and one plan keeps the value order coherent.

## p80-worktree-closeout-artifact-migration-and-residue

Added: 2026-09-28 (investigate skill, user-directed three-origin group investigation); amended 2026-09-29 with a consumer-run duplicate-worktree and double-landing witness.

Origins:
- docs/history/backlog/2026-09-28-review-record-destroyed-with-exec-worktree.md
- docs/history/backlog/2026-09-28-machinery-deletion-primary-checkout-orphans.md
- docs/history/backlog/2026-09-28-worktree-closeout-baseline-capture.md
- docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md

Grouping: one group over the worktree lifecycle boundary; shared surfaces are the execute-plan ad-hoc-worktree recipe (Phase 0 run/worktree identity and baseline capture, Phase 5 migration, landing and teardown guards) in agents/skills/execute-plan/SKILL.md, scripts/worktree_closeout_migrate.py (capture and migrate, introduced 2026-09-22 fe61c847), the landing discipline that moves main's ref from a worktree without reconciling the primary checkout's disk, and the done Step 0 recovery arms in agents/skills/done/SKILL.md. The original three origins were witnessed 2026-09-28 in worktree-first runs; the new consumer witness was observed 2026-09-29 in a consumer execute-plan session. Near-siblings examined and left out: 2026-09-28-done-manifest-root-identity-contract.md and the p79 group (done state machinery, not worktree selection/teardown), the stale-worktree teardown audit (completed memory record, not an open defect).

Urgency: High; a worktree removal destroyed the only copy of a review record (r1/r2 for the release-skill-follow-ups run), forcing an after-the-fact reconstruction with no source artifact, and machinery-deletion landings left byte-identical orphan files in the primary checkout that every later session re-adjudicated as foreign dirt. Position: third, beside the p79 closeout group (both High, same-day witnesses; p79 carries two high-priority origins).

Prompt: using the plans skill, author one plan (authoring only, do not execute): worktree closeout artifact migration, post-landing orphan reconciliation, baseline-capture enforcement, and single-run worktree/branch identity. Read each origin's full text from docs/history/backlog/ and treat the files as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): scripts/worktree_closeout_migrate.py already implements capture (a JSON baseline of path plus SHA-256) and migrate (copies new-or-modified files versus the baseline; its implicit-empty-baseline guard at the migrate boundary refuses to continue without a baseline file, so pre-existing artifacts cannot be silently skipped); the execute-plan Phase 0 recipe runs capture and Phase 5 runs migrate with a do-NOT-remove-the-worktree guard on migration failure; done Step 0 already instructs the worktree session to migrate review staging docs before docs-branch sync and worktree removal. The existing Worktree-first standard also says worktrees are unique per run and permits adoption of a dispatch-provisioned worktree, but it does not persist one canonical run-to-worktree/branch binding for subsequent corrections and closeout. The defects are enforcement and coverage gaps on top of that machinery: the witnessed exec run skipped Phase 0 capture and fell back to an unverified scoped copy; the witnessed release-skill-follow-ups run lost review records to worktree removal; deletion landings left byte-identical primary-checkout orphans; and consumer-run Task 5's implementation branch was integrated both by cherry-picks and later by a true merge, after which a second branch/worktree at the same commit was created solely for two checklist edits. That second worktree was the same execution run, not a concurrent task: no independent task scope or parallel integration contract justified it. Its archive was initially refused while the active chat was pinned, then succeeded after the supported sidebar move. Scope arms: (1) pre-teardown migration is verified, not assumed: enumerate every gitignored artifact the run created, migrate or verify each in the primary checkout by digest, then archive; (2) a done Step 0 recovery arm detects a missing review record for a landed plan and records a reconstruction duty with a witness note; (3) a baseline-less run records the skip and scoped-copy artifact list while retaining the implicit-empty-baseline guard; (4) deletion landings reconcile only exactly proven byte-identical deleted paths, never blanket-cleaning unknown or modified files; (5) bind each execution run to one canonical repository root, worktree, branch, and base at Phase 0, inspect existing local/attached worktrees before creation, and resume run-level progress edits in that canonical checkout; create another worktree only for a distinct run or a task with an explicit concurrency/merge contract; (6) choose exactly one landing operation per source branch and check ancestry before applying commits, refusing a cherry-pick-plus-merge duplicate; (7) after artifact verification and landing, archive through the managed app workflow and delete the local branch only after reachability verification; when pin protection blocks archival, use the supported unpin/move and retry path, preserving the managed snapshot.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Tracking docs/reviews so records cannot be lost: rejected; staging docs are working artifacts tracked selectively at landings, and tracking them changes review-staging semantics wholesale.
- Blanket git clean after landings to remove orphans: rejected; it sweeps live peer dirt, violating the never-touch-foreign-dirt discipline.
- Removing the implicit-empty-baseline guard so closeout proceeds without capture: rejected; the guard's refusal prevented an unverified full-dir sweep that would have carried done-session markers into the primary checkout's session window (witnessed).
- Making teardown proceed despite migration failure: rejected; the existing do-NOT-remove stance is correct, the gap is upstream enforcement and the done-side recovery arm.
- Applying worktree landing changes to the primary checkout at landing time instead of sweeping orphans after: rejected; the checkout is deliberately left to live peers during landings, and re-applying changes under them would race active sessions.
- Removing run worktree isolation: rejected; the incident was duplicate run identity, not a failure of isolation.
- Creating separate worktrees for every task or checklist edit: rejected as the default; this same-run correction had no independent concurrency or merge contract and created competing branch state.
- Cherry-picking Task 5 and later merging its original branch: rejected; one landing method must preserve each source commit exactly once.
- Deleting a protected worktree directory directly: rejected; managed archival preserves a recoverable snapshot and enforces workspace protection.

## p96-worktree-first-standard-hardening

Added: 2026-09-29 (grouping pass, six-origin group over the worktree-first run's correctness residuals)

Origins:
- docs/history/backlog/2026-09-28-adoption-gitignored-state-conjunct.md
- docs/history/backlog/2026-09-28-bootstrap-test-env-hermeticity.md
- docs/history/backlog/2026-09-28-execute-plan-resume-reentry-arm.md
- docs/history/backlog/2026-09-28-reverse-squash-guard-absent-skips-tracked-dirt-check.md
- docs/history/backlog/2026-09-28-worktree-branch-naming-single-home.md
- docs/history/backlog/2026-09-28-worktree-creation-record-phantom-referent.md

Grouping: one group over the Worktree-first standard's run-lifecycle surfaces in agents/skills/execute-plan/SKILL.md and its machinery: adoption predicate contents (r4 F13), resume re-entry routing (r4 F12), the removal gate's guard-absent fail-open branch (r1 F15), the severed-ancestry fork-point record referent (r6), the branch-naming design decision (r2 F11), and the bootstrap smoke test's environment hermeticity (r3) -- all residuals of the worktree-first standard-only-mode run's review rounds, all correctness-or-decision class on the same skill surfaces plus their keyed pins and test suite. Near-sibling: the p80-worktree log entry owns the teardown-side surfaces (closeout artifact migration, orphan sweep, baseline capture); this group owns entry, adoption, resume, and the removal gate's failure direction, so the two stay separate review surfaces.

Urgency: Medium; no live-run blocker, but two of the six are silent-hazard class (an adopted worktree's stale facts snapshot passes the noclobber guard untouched; a consumer repo without the deployed guard script removes worktrees over unverified tracked dirt), and the naming decision leaves downstream durable records without a checkable convention.

Prompt: using the plans skill, author one plan (authoring only, do not execute) hardening the Worktree-first standard's run lifecycle. Read each origin's full text and treat the files as the scope of record; re-verify every mechanism fact on disk before pinning. Scope arms: (1) adoption conjunct: the adopted worktree's pre-existing gitignored state (facts file, reviews directory) must be absent or byte-identical to the primary checkout's sources, standing the run down on anything else; the start-empty invariant is restated as fresh-worktree-only with adoption as the verified exception; (2) resume re-entry: the run's worktree path becomes a recorded session-manifest field at Step 0.4 (not only the log row), the Step 0.1 recognition arm and the Live-session discovery ladder consult it before any second worktree is created, a recorded live worktree routes through the canonical provisioned-worktree adoption rule, and the execution payload's resume rule in prompt-templates.md reads the field and re-enters before continuing; (3) the reverse-squash guard-absent branch becomes stop-and-report (name the missing script, exit non-zero, removal refused), mirroring the readiness gate's missing-validator treatment, unless the plan records an explicit no-guard repo decision with its rationale; (4) the severed-ancestry fork point: record the branch start-point sha under an explicit named field at run setup and cite that field, or delete the phantom secondary source keeping the reflog arm plus the fail-closed stand-down; (5) the branch-naming decision is made, not deferred: either one canonical naming rule stated once in the canonical section with both lanes reduced to references, or the recorded free-form authoring-lane decision with the dispatch-witness arm named as the authoring lane's matching arm; (6) bootstrap test hermeticity: one sanitized_env() helper (minimal PATH, scratch HOME, GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE/GIT_CONFIG_GLOBAL/GIT_CONFIG_SYSTEM unset or pinned to the fixture) used by the validator subprocess, the recipe invocation, and the _git helper, with the validator's override kept on top. Pins keyed on any reworded span are re-keyed in the same edit; the pins suite and the touched suites run green at landing.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Folding the p80-worktree closeout origins into this group: rejected; entry/adoption/resume and teardown/closeout are different halves of the lifecycle with different witnesses, and the closeout group is already logged and scoped.
- Keeping the guard-absent skip with a louder message: rejected by the corpus's fail-closed convention; a missing validator elsewhere is stop-and-report, and a silent skip in a removal gate is the one direction that destroys evidence.
- Deciding branch naming inside passing prose without the recorded decision: rejected by the origin; the two options are a design choice the plan must make explicitly, either as a stated rule or a recorded free-form decision.
- Sanitizing only the recipe subprocess and leaving the validator call ambient: rejected; the validator runs git plumbing against the same fixture and inherits the same leak class.

## p81-execute-plan-worker-identity-and-terminal-evidence-edges

Added: 2026-09-28 (investigate skill, user-directed three-origin group investigation)

Origins:
- docs/history/backlog/2026-09-22-execute-plan-empty-process-identity.md
- docs/history/backlog/2026-09-28-terminal-evidence-forced-available-recovery-action-remnant.md
- docs/history/backlog/2026-09-28-terminal-evidence-reobserve-fail-open.md

Grouping: one group over the driver's worker identity and reconciliation machinery in scripts/execute_plan_runtime.py; the two terminal-evidence items were deferred findings of the same r1 review of the executed codex-worker-terminal-recovery plan (squash 2c16096d, 2026-09-28), and the process-identity item is the same launch-identity contract one layer earlier (`_record_worker_launch`). Near-siblings examined and left out: the p78 group (claim lifecycle and preflight, already logged), 2026-09-28-done-manifest-root-identity-contract.md (repository identity, not worker identity), 2026-09-27-execute-plan-task-scoped-verification-contract.md (manifest seeding gate; its demand already exists as the pre-seed consistency gate and it is dispositioned in the p84 closure group).

Urgency: Medium; correctness edges in recovery paths, none blocking a live run: an incoherent audit label on a reconciled worker, a fail-open edge that lets a terminal release stand when the guard's own re-observation errors, and an adapter contract violation concealed by identity synthesis. Position: fourth, behind the two High groups.

Prompt: using the plans skill, author one plan (authoring only, do not execute): worker identity validation and terminal-evidence reconciliation edges in the execute-plan driver. Read each origin's full text from docs/history/backlog/ and treat the files as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): `_record_worker_launch` (around line 2342) reads `receipt.get("process_identity")` and synthesizes the documented compatibility identity (`{"provider": ..., "session_id": session}`) whenever the value is falsy, so an explicitly supplied empty, null, or malformed identity is indistinguishable from an omitted one in the persisted receipt; the forced-available override after a terminal-evidence release rewrites the worker state but the `worker-reconciled` history append (around line 1457) records `recovery_action` straight from the result, so a refused-path action label can survive onto a reconciled event; and the post-consult release-window guard (around lines 1556-1565) downgrades a release to absence-quarantine only when `_conversation_id_raw_visible` returns true, so an erroring re-observation (ps failure, timeout) reads as not-visible and the release stands. Scope arms: (1) `_record_worker_launch` checks key presence separately from value validity: synthesize the compatibility identity only when the adapter omitted `process_identity`, and refuse an explicitly supplied empty, null, or malformed value before persistence, with omitted-versus-invalid tests; (2) the forced-available override clears or rewrites `recovery_action` so the `worker-reconciled` history event records a coherent result, witnessed by a test; (3) a failed post-consult re-observation is guard-undecided: it produces the same absence-quarantine downgrade as a positive raw-token sighting, witnessed by a canary; no release path treats tooling failure as evidence of absence.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Keeping synthesis for all falsy identities: rejected; the receipt must distinguish omitted from invalid, otherwise an adapter contract violation is concealed at persistence.
- Refusing omitted identities too: rejected; the compatibility identity for omitted values is documented behavior adapters rely on.
- Leaving the stale recovery_action label: rejected; the history event is an audit input and a refused-path label on a reconciled outcome misstates what happened.
- Letting the release stand on a failed re-observation: rejected; the guard exists precisely to not release over a live resumed conversation, and tooling failure is not evidence of absence, so the downgrade is the only safe direction.

## p84-plans-sut-naming-and-lessons-recovery-branching

Added: 2026-09-28 (investigate skill, user-directed two-origin group investigation)

Origins:
- docs/history/backlog/2026-09-28-plans-sut-naming-rule-for-wrapper-converted-results.md
- docs/history/backlog/2026-09-21-lessons-gate-recovery-distinguish-duplicate-ids.md

Grouping: one group by defect class over the skills corpus: a witnessed failure class whose skill text lacks the branching rule or named remedy, so the operator or reviewer is misdirected (a plans Validation gap that cost three review rounds five staged findings, and a lessons recovery message whose offered command does nothing for the witnessed failure category). Shared surfaces are the skill bodies plus their regression witnesses, and both fixes must respect the vendored-twin rule (the runtime-side catalog twin lands in the same run or carries a tracked landing path). Near-siblings examined and left out: the p83 residual sweep (recorded findings on executed plans, not missing rules in living skills), the p88 closure group.

Urgency: High; the plans rule's witness is recurring review churn (the terminal-recovery plan's r2-r4 re-derived the same defect five times across four workers before pinning the system under test), and the Validation Commands rules are consumed by every future plan in every project, so the rule pays back immediately. Position: after the p81 driver-edge group, before the Medium singles.

Prompt: using the plans skill, author one plan (authoring only, do not execute): a system-under-test naming rule for the plans skill and category-branched lessons recovery text. Read each origin's full text from docs/history/backlog/ and treat the files as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): the plans skill's Validation Commands authoring rules end at rule 41 (file around line 570), so the new rule is 42; the existing rules cover task-coupling (25) and whole-tree gate states (21) but nothing requires naming WHERE a behavior is observed when a wrapper sits between the tested unit and the outcome (the witnessed seam: a pure reducer returns `available` while the driver wrapper structurally downgrades it to `capacity-live` under a live worker, so a test written against the reducer layer is unreachable at the wrapper). The lessons recovery text in BOTH agents/skills/learn/SKILL.md (around line 532) and agents/skills/done/SKILL.md (around line 194) offers only the `untagged / invalid-family` branch with `lessons.py adopt --tag-unclassified`, while the validator also reports duplicate and multiple-tags categories, and the witnessed duplicate-id recovery attempt returned "0 lessons rewritten (all already tagged)". Scope arms: (1) plans rule 42: when a wrapper transforms or can veto a lower layer's result, every test item names its system under test; the wrapper's post-conversion outcome gets its own named assertion, and any reducer-level expectation today's wrapper already satisfies is labeled a green-at-RED regression pin rather than a RED target; (2) a matching lens pattern lands in the review-agents catalog the same run (the panel cannot flag what no lens owns; the iteration-discipline rule requires the catalog gap close before re-review); (3) the learn and done recovery texts branch on the validator category: untagged/invalid-family keeps the tagging workflow, duplicate gets inspect-colliding-headings-choose-unique-number-update-references-rerun, multiple-tags gets remove-competing-tags-after-classifying; (4) regression witnesses per category (a validator-output-shaped fixture per branch), repair stays operator-driven (no automatic renumbering or reference rewriting); (5) both runtime-side skill twins carry the same text in the same run or a tracked vendored-sync landing path.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Teaching the wrapper seam only in the review lens catalog without the plans rule: rejected; authoring-time prevention beats review-time detection, and the witness shows reviewers re-derive the defect without a rule to cite, so both surfaces land together.
- Automatically renumbering duplicate lesson ids: rejected by the origin; cross-references are semantic, so repair stays operator-driven.
- Extending --tag-unclassified to also resolve duplicates: rejected; a tagging command renumbering identifiers would silently rewrite the corpus, the opposite of the operator-driven scope.
- Fixing only the vendored repo copy and leaving the runtime twin to drift: rejected; the vendored-sync rule requires the twin landed or tracked, never orphaned.

## p85-user-directed-override-for-interactive-guard-standdowns

Added: 2026-09-28 (investigate skill, single-origin investigation)

Origins:
- docs/history/backlog/2026-09-28-user-direct-request-overrides-standdown.md

Grouping: single origin over the maintenance skill's guard precedence for interactive sessions (agents/skills/maintenance/SKILL.md Step 2 guards and Step 3 decisions, mirrored in agents/skills/maintenance/zcode.md). Related rules that already landed and are left out of scope: the authoring-lane target-distinctness carve-out with the 09:32 witness (landed by the executed maintenance-autonomous-pipeline plan; the sibling origin docs/history/backlog/2026-09-28-authoring-lane-guard-precedence.md is satisfied by it and dispositioned in the closure group), and the continue-loop condition. What does not exist anywhere (verified by search): a user-directed-override rule for interactive sessions.

Urgency: High; the operator corrected this twice in one day (the 09:32 authoring stand-down and the 18:21 execution stand-down), and the 18:21 correction proved the stand-down bought nothing (the peer had already landed both runs by re-survey). An interactive session carrying a live user directive has the operator present; the guards were written for unattended sessions that share the same code path.

Prompt: using the plans skill, author one plan (authoring only, do not execute): a user-directed override rule for interactive guard stand-downs. Read the origin's full text from docs/history/backlog/ and treat the file as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): the maintenance skill's G3 stands the whole turn down when a merge or rebase is in progress or the done lock is held (D3 recorded), G1e/G1a occupancy resolves to stand-down or deferral, and the landing gate defers dispatch while outstanding unlanded runs survive; none of these texts distinguishes an interactive session carrying a live user directive from an automation-born turn. The state file's children ledger records the override happening in practice (the 2026-09-28 19:14 execution entry carries "override of 18:21 stand-down"), so the practice exists but the rule does not. Scope arms: (1) a User-directed override rule in the maintenance skill, mirrored in the runtime overlay: when the session is interactive (the current directive came from a live user message) and a guard that would only defer or stand down trips (G1e/G1a occupancy, the G3 done-lock hold, the landing gate), the session states the tripped guard and its evidence in one line, chooses a non-colliding execution surface (its own per-execution worktree, landing-completion work for a completed unlanded run, or a target verified disjoint from the peer's in-flight one), and proceeds instead of standing down; (2) integrity guards are never overridable (the G2 failure cap, corrupted merge-lock metadata, foreign-dirt gates); (3) the override records the literal `user-directed-override` plus the tripped guard's name in decision_reason; (4) unattended sessions keep today's stand-down semantics unchanged (the predicate is user presence, never confidence); (5) a witness-based self-test or review checklist item verifies the override predicate stays user-presence-based.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Removing the deferral-class guards for all sessions: rejected; unattended turns share the code path and have no operator to accept the risk, so the guards keep protecting them.
- A confidence-based override ("the session judges the peer stalled"): rejected by the origin's own predicate; the override binds to user presence, not to the session's mood, and a dead-PID probe is not crash evidence (the 18:21 witness).
- Documentation-only guidance without the recorded literal: rejected; the practice already happened without a rule, so the rule must carry the auditable `user-directed-override` marker the state reader can surface.

## p86-secret-scan-visibility-scoped-domain-redaction

Added: 2026-09-28 (investigate skill, single-origin investigation)

Origins:
- docs/history/backlog/2026-09-28-secret-scan-preserve-valid-service-links.md

Grouping: single origin over the done skill's sensitive-data-scan gate policy (agents/skills/done/SKILL.md pre-commit gates and the resolved hygiene scanner's employer-domain patterns). Near-siblings examined and left out: the rejected 2026-09-22 credential-shaped-patterns item (bare credential vocabulary false positives; it explicitly deferred domain changes without a consumer witness, which this origin now supplies), and the 2026-09-27 release-gate adjudication (result-only scanning for the release skill's own gate; a scope decision for a different surface, not a visibility policy).

Urgency: High; consumer-company witnessed: a valid internal Jira link was redacted to a bare ticket id in a private company repository, which made the plan less useful and changed its digest, forcing a fresh full review round that found nothing. The skills-repo personal profile must not defer this as formal-hardening because the gate and scanner are shared done-workflow machinery.

Prompt: using the plans skill, author one plan (authoring only, do not execute): repository-visibility-scoped domain redaction for the done sensitive-data scan. Read the origin's full text from docs/history/backlog/ and treat the file as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): the done skill's sensitive-data-scan gate (around line 376) runs a diff-content pattern grep plus a full-content scan of untracked files with employer-brand patterns resolved from the facts document, and its remediation guidance (around line 381) instructs replacing internal hostnames with generic placeholders such as `<your-org>.atlassian.net` unconditionally; the hygiene patterns file matches the employer org as a word (domain OR path segment), and the scanner receives no repository-visibility or confidentiality input, so a private company repository is scanned under public-artifact rules. Scope arms: (1) the gate learns a visibility or explicit confidentiality classification (facts-derived, never a global hostname allowlist) and applies employer-domain redaction only to public artifacts; (2) credential, token, secret-query-parameter, and known-secret-format checks stay active in both private and public contexts, and the whole URL is still inspected for secrets before any link is preserved; (3) focused fixtures: a valid internal service link in a private-repository scan (preserved), the same link in a public-artifact scan (redacted), and credential-bearing URLs in both contexts (flagged); (4) the done skill's remediation guidance is updated to state the scoping so an operator does not hand-redact a valid link again.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- A global Jira-host allowlist: rejected by the origin; the decision must depend on repository visibility or an explicit confidentiality policy, and an allowlist neither generalizes nor protects public artifacts.
- Dropping employer-domain patterns everywhere: rejected; public-artifact hygiene genuinely needs them (the release-gate witness), so the patterns stay and the scope narrows.
- Leaving remediation to operator judgment without gate support: rejected; the witnessed failure was a hand-redaction made to pass the gate, so the gate itself must carry the policy.

## p82-codex-model-guard-activation-probe-and-recovery

Added: 2026-09-28 (investigate skill, single-origin investigation)

Origins:
- docs/history/backlog/2026-09-23-codex-model-guard-runtime-alignment.md

Grouping: single origin over the Codex model-guard activation and recovery contract (agents/hooks/codex-model-guard/). Partially fixed since filing: the September 22 reconciliation workstream (5b414ee3) landed model-guard alignment and the September 25 reliability wave (9fa80dc1) landed the exact worker-creation tool identities with near-miss tests and the README decision table. Near-siblings examined and left out: the p78 group (driver preflight mandate; the guard's refusal arm extends that boundary for the model-policy dimension but is a separate surface and a separate plan), the p81 group (worker identity receipt validation, not host policy alignment).

Urgency: Medium; witnessed deadlock class: during a 2026-09-23 recovery the guard's own policy source was reverted by a stash, the next PreToolUse call was denied, and the denial prevented the parent from running the diagnostics or restoring the saved edits, so the session could not recover through normal tools. The fail-closed checks are correct; the missing complement is a way to detect and fix a mismatched policy from outside the blocked session.

Prompt: using the plans skill, author one plan (authoring only, do not execute): model-guard activation probe, prelaunch alignment refusal, and a safe recovery path. Read the origin's full text from docs/history/backlog/ and treat the file as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): agents/hooks/codex-model-guard/require-luna.py enforces the selected subagent model from the host config ([agents].default_subagent_model), recognizes worker launches only by exact worker-creation tool identities (agent, spawn_agent, spawn-agent, subagent), and fails closed on missing or malformed policy, missing event model, or a mismatch, so a denied launch cannot be authorized by transcript history or the parent's active model; scripts/test_codex_model_guard.py carries the hermetic suite. What does not exist anywhere (verified by search): an activation probe that reports the resolved guard path and selected policy before execute-plan claims or launches work, a preflight-adjacent refusal naming `runtime-policy-unavailable` when the active hook target or configured default differs from the versioned policy source, and a documented recovery procedure that restores policy alignment without requiring the blocked session to edit or execute the guard itself. Scope arms: (1) one verified policy value across the versioned guard source, the active hook target, the host config default, and the launch contract, with a hermetic test that detects disagreement among them; (2) an activation probe (invocable read-only, reporting resolved guard path and policy without transcript contents) consulted before claims or launches; (3) a mismatch blocks plan launch before task claim or handoff mutation and returns an actionable recovery path; (4) the recovery procedure is documented and tested to preserve the fail-closed gate, and never requires the blocked session to modify the guard.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Weakening the guard to permit the blocked session's recovery edits: rejected; fail-closed on mismatch is the guard's purpose, and the witnessed deadlock is resolved by an out-of-band probe and procedure, not by loosening the gate.
- Host-side auto-sync of the active hook from the versioned source: rejected; silently rewriting host wiring masks the drift the probe must surface, and host wiring is an operator-owned surface.
- Documentation-only recovery guidance: rejected; the witnessed failure is procedural deadlock under an active denial, so the detection must be mechanical (the probe) and the refusal must carry the remedy, not prose alone.

## p87-docs-branch-single-marker-window-witness

Added: 2026-09-28 (investigate skill, single-origin investigation)

Origins:
- docs/history/backlog/2026-09-28-docs-branch-sync-single-marker-unanchorable-window.md

Grouping: single origin over the done-session window anchoring that gates the docs-branch sync. Location correction discovered in investigation: the origin cites agents/skills/docs-branch/SKILL.md, but the two-content-confirmable-markers rule lives in agents/skills/done/SKILL.md (the Step 0 sweep-gates window derivation around line 163 and the gate-order paragraph around line 207, with the docs-branch invocation consuming it around line 223); the docs-branch skill carries no marker vocabulary of its own. Near-siblings examined and left out: the p79 group (marker content and location self-check; this origin is about anchoring sufficiency, not marker validity), the p80 group (worktree artifact migration at closeout, not sync windowing).

Urgency: Medium; silent data-miss class: a done run that starts fresh produces exactly one content-confirmable marker, the window is unanchorable, and the run's own review records are silently left out of the docs-branch sync (witnessed 2026-09-28: the recreated code-review r2 record stayed disk-only). Nothing durable records the skip, so recovery depends on operator memory.

Prompt: using the plans skill, author one plan (authoring only, do not execute): a second anchor source and a durable skip record for single-marker sync windows. Read the origin's full text from docs/history/backlog/ and treat the file as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): the done skill derives the session window mechanically from `run-start-*` markers under the done-session directory (the newest content-confirmed marker is the current run, the newest strictly older one is the previous-run anchor; content confirmation compares the marker's recorded repo-root digest against the recomputed Step 0 digest), and when fewer than two markers are content-confirmable the window is unanchorable under conservative gating, so the sweep prunes nothing and the sync skips the run's own artifacts; the run manifest plus the owned-commits ledger already record which docs artifacts the run created (plan paths, review staging docs, ledger shas), so the data for a witness-based window exists. Scope arms: (1) a manifest-plus-ledger witness pair is accepted as an alternative second anchor for a single-marker window, bounding the sync window to the artifacts the run itself recorded; (2) when a window remains unanchorable, the sync output names the specific skipped artifacts and writes a durable pending-sync record (a sidecar the next anchored sync consumes deterministically), replacing recovery-by-operator-memory; (3) conservative gating stays the fallback of the fallback: the witness path only widens what the two-marker rule can anchor today, never loosens content confirmation; (4) a test per window shape (two markers, single marker with witness pair, single marker without) pins which artifacts sync and which are recorded skipped.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Syncing unconditionally when the window is unanchorable: rejected; conservative gating exists because an unanchored window cannot bound what the run produced, and syncing unbound would sweep peer runs' artifacts.
- Treating the single-marker case as expected and documenting manual re-sync: rejected by the origin; interactive done runs routinely produce exactly one marker, so the "rare" case is the common case, and manual re-sync by memory is the defect.
- Lowering the content-confirmation bar to make recent markers confirmable: rejected; content confirmation is the cross-repo safety fence (a marker whose digest cannot be recomputed belongs to another repo), so the witness pair, not weaker confirmation, is the complement.

## p83-residual-polish-sweep

Added: 2026-09-28 (investigate skill, user-directed three-origin group investigation); amended 2026-09-29 (grouping pass: five worktree-first-run residual docs items joined the sweep's re-verify-then-fix class)

Origins:
- docs/history/backlog/2026-09-20-phase3-r1-polish-residuals.md
- docs/history/backlog/2026-09-21-r3-review-overflow-residuals.md
- docs/history/backlog/2026-09-28-review-loop-exit-metrics-r1-nonblocking.md
- docs/history/backlog/2026-09-28-execute-plan-vacated-step-numbers.md
- docs/history/backlog/2026-09-28-invariants-referent-naming.md
- docs/history/backlog/2026-09-28-lesson-147-stale-step-0-1a-citation.md
- docs/history/backlog/2026-09-28-plan-g7-base-key-skip.md
- docs/history/backlog/2026-09-28-plans-phase-0-restates-canonical-rationale.md

Grouping: one group by defect class, not surface: all three origins are verified non-blocking residual findings recorded during executed plans' review rounds (2026-09-20 phase-3 r1 of the recovery-contract run; 2026-09-22 r3 of the scheduler state-durability plan; 2026-09-28 r1 of the executed exit-metrics plan), each a small divergence between what a surface claims and what it does. Their half-life is the hazard: later passes have already fixed several findings with no disposition recorded on the origin items, so an executor that fixes blindly re-fixes or contradicts landed bytes. Near-siblings examined and left out: the p81 group (driver behavioral edges, not recorded-review residuals), the p88 closure group (origins satisfied end-to-end, not partially-fixed residuals). The 2026-09-29 amendment adds five residuals of the same recorded-finding class from the worktree-first standard-only-mode run's review rounds (r1-r6) plus the plans-skill Phase 0 restatement item: each a small divergence between what a surface claims and what it does, re-verify-then-fix.

Urgency: Medium-Low; no live-run impact, but un-dispositioned surviving findings decay into stale-review landmines (an executor trusts a usage text or contract claim a later pass already changed, or re-fixes a fixed site). Six findings are already verified fixed on disk today (phase3-r1 findings 1, 6, 7; r3 themes 1, 3, 4), which is exactly why the sweep shape is re-verify-then-fix. Position: fifth, behind the behavioral groups.

Prompt: using the plans skill, author one plan (authoring only, do not execute): a residual-polish sweep that re-verifies every finding against current bytes and fixes only the survivors. Read each origin's full text from docs/history/backlog/ and treat the files as the scope of record. Established mechanism facts to author from (re-verify each on disk before pinning): phase3-r1 finding 1 (added-lines typo'd path reads CLEAN) is fixed, as scripts/check-no-em-dash.sh now fails closed on a pathspec matching no tracked file (around lines 118-125); finding 6 (long-form --base=REF absent from usage) is fixed (usage line 17); finding 7 (resume-same-claim undocumented in the contract) is fixed (runtime-contract.md line 388 pins the exact value); r3 theme 1 (payload-copy consume lifecycle) is fixed (the pending_rearm field paragraph in agents/skills/maintenance/SKILL.md gives every clearer the copy-deletion duty and the dispatch path consumes its copy); r3 themes 3 and 4 are fixed (the named live-bound condition and the Step 3 loop-mode exclusion exist as the one-statement definitions); the exit-metrics N4 `<report-home>` placeholder still sits in the maintenance skill's weekly rider (around line 164) and the `_atomic_write_private` helper in scripts/summarize_review_stats.py (around line 2408) is the mkdir question. Scope arms: (1) the plan's first task re-verifies every remaining finding against the current bytes and records a per-finding disposition (fixed-with-evidence, survivor, or mooted-for-completed-history per the doc-hierarchy states); (2) survivors get their small fixes: the phase3-r1 shared-shape items (junk-state rejection witness, parameterized blocked-persist tail, shared task-heading predicate, runtime-contract.md indentation), the r3 theme-2 appendix wording pair, and the exit-metrics N2-N5 items (float formatting, report legend caveat, report-home definition plus parent-directory creation, strict-package wording placement); (3) completed-history mooting (the exit-metrics N1 grep pin lives in an executed plan's immutable bytes) records the moot disposition in the sweep's own surfaces, never an edit to the completed artifact; (4) no behavior changes beyond the named findings; every fix carries its discriminating witness or, for prose, its pin. Amended-residual arm (5), added 2026-09-29: re-verify each added origin against current bytes before fixing. The vacated Phase 0 numbering either renumbers gapless with pins and cross-skill citations re-keyed in the same change or adds the one-line retirement note, and Step 0.1's transfer-in obligation points directly at the canonical Transfer-in implementation; the Invariants isolation-bullets citation names agents/skills/maintenance/SKILL.md as its owning file; the plans Phase 0 Step 0.1 rationale and Step 0.2 marker-keying restatements slim to reference-plus-literal; lesson 147's stale Step 0.1a half and See-also citation are corrected through the learn/lessons flows (never a hand edit of the lessons corpus), citing the consolidation as the driving incident; the plan-g7 base-key item is adjudicated at execution time -- a completed-history moot disposition (the owning plan is executed and archived) unless a live consumer need proves a correction branch is warranted, per the sweep's completed-history arm.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Fixing all 19 findings as written without re-verification: rejected; six verified-fixed findings would be re-fixed or their re-fixes would fight landed bytes, which is the exact stale-review failure the sweep exists to prevent.
- Closing the three origin items as stale: rejected; several survivors are real (the N4 report-home placeholder is verified still present), so closure would orphan live defects.
- Folding the survivors into the closure group's housekeeping plan: rejected; code and prose fixes need their own review surface, not a status-flip plan.

## p97-maintenance-payload-landing-pins-ledger-hygiene

Added: 2026-09-29 (grouping pass, eight-origin hygiene group over the maintenance machinery's landing tails, pins suite, and ledgers)

Origins:
- docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md
- docs/history/backlog/2026-09-28-execute-plan-repoint-missing-revisions-ledger-entry.md
- docs/history/backlog/2026-09-28-landing-machinery-on-main-shorthand.md
- docs/history/backlog/2026-09-28-landing-tail-parenthetical-precedence-and-pin.md
- docs/history/backlog/2026-09-28-maintenance-pins-cherry-pick-comment-home.md
- docs/history/backlog/2026-09-28-maintenance-pins-consolidation-comment-stale-claim.md
- docs/history/backlog/2026-09-28-prompt-templates-deviation-entry-leadin-and-source-record.md
- docs/history/backlog/2026-09-28-s15-rekey-narrowed-done-lock-gate-pin.md

Grouping: one group by shared surface rather than severity: the maintenance payloads' landing tails (prompt-templates.md), the pins suite that freezes them (scripts/check_maintenance_pins.sh), and the bookkeeping ledgers the machinery owes (the maintenance SKILL.md Revisions ledger, the blueprint deviation list) -- every item is a residual of the worktree-first standard-only-mode run's review rounds (r1 F12/F14, r3, r4 sibling observations, r6), and every fix is either a payload-prose edit with its pin re-keyed in the same change or a comment/ledger entry verified by a green pins run. Near-sibling: p83 owns prose residuals on skill bodies; this group owns the payload-and-pin machinery layer.

Urgency: Medium-Low; mostly formal/docs class, but the checkout-flow arm is real correctness (an unattended landing in a configured checkout-flow project could sweep operator-branch commits onto the default branch, and no arm compares the resolved creation base with the landing target), so the guard lands first inside the group.

Prompt: using the plans skill, author one plan (authoring only, do not execute) sweeping the maintenance machinery's landing-tail, pin, and ledger hygiene. Read each origin's full text and treat the files as the scope of record; re-verify each against current bytes before fixing. Scope arms: (1) the checkout-flow guard: the payload landing critical section compares the resolved worktree-creation base with the landing target and fails closed on mismatch (defer-landing naming both refs), or the payload prescribes landing-to-resolved-base for checkout-flow projects; (2) the landing paragraph's 'on main' shorthand rewords to the default-branch form; (3) the landing-tail parenthetical mirrors the canonical sentence's carve-out framing and gains a wrap-tolerant exactly-once pin on its distinctive fragment; (4) the blueprint deviation list registers the r5 final-merge lead-in re-pin (paraphrase-only so body-scoped count pins hold) and its source-of-record sentence re-points to the surviving folded plan or declares the deviation list itself the record; (5) the cherry-pick pin's operator comment names the canonical transfer-in implementation as the span's home; (6) the consolidation comment block rewords to the narrowed claim (worktree paragraph replaced by reference; pre-work gate paragraph rewritten, not retired), mirroring the F8 deviation-entry wording; (7) the maintenance SKILL.md Revisions ledger gains the dated entry for the supersession-chain re-point (or the next ledger entry names it); (8) the S15 re-key's narrowed coverage is restored: the execution blueprint's keying phrase (`done locks are keyed per-worktree on --show-toplevel`) is count-gated beside the re-keyed pin. Every prose edit re-keys its owning pin in the same change; every comment or ledger edit verifies by a green pins-suite run; no behavior change beyond the checkout-flow guard arm.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Folding these into p83's residual sweep: rejected; the payload-and-pin machinery layer carries behavior-bearing arms (the checkout-flow guard) and pin re-keys that need their own review surface, not a prose-sweep ride-along.
- Deleting stale pin comments instead of rewording them: rejected; the comments are operator-facing provenance for re-keying, and the suite's freeze-literal discipline expects corrected claims, not absence.
- A log-and-continue treatment for the checkout-flow mismatch: rejected by the origin's fail-closed direction; an unattended landing must not sweep operator-branch commits onto the default branch.

## p88-executed-plan-origin-closure-sweep

Added: 2026-09-28 (investigate skill, user-directed nine-origin closure group)

Origins:
- docs/history/backlog/2026-09-27-execute-plan-task-scoped-verification-contract.md
- docs/history/backlog/2026-09-21-quota-probe-wait-minutes-unbounded-overrides.md
- docs/history/backlog/2026-09-23-stale-validator-rejected-enum-deployment-gap.md
- docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md
- docs/history/backlog/2026-09-19-model-selection-persist-foreign-key.md
- docs/history/backlog/2026-09-19-subagent-session-record-persistence-races.md
- docs/history/backlog/2026-09-22-live-record-carrier-migration-deferral.md
- docs/history/backlog/2026-09-28-review-loop-exit-condition-and-metrics.md
- docs/history/backlog/2026-09-28-maintenance-autonomous-pipeline.md

Grouping: one closure group, not a work group: investigation verified each origin's demand is already satisfied by an executed plan, is an external prerequisite with its repo-side half landed, or is discharged by a witnessed no-op. They sit together because their remaining work is the same shape: record the disposition on the origin, close what is closable under the done/plans completion conventions, and leave the external-gate watchers open with their anchors intact. Near-siblings: the authoring-lane-guard-precedence origin (docs/history/backlog/2026-09-28-authoring-lane-guard-precedence.md) belongs here too: its target-distinctness rule with the 09:32 witness landed in the maintenance skill via the executed pipeline plan, and its own text directs folding into that plan's surface.

Urgency: Low (housekeeping); the value is a truthful backlog: seven origins demand work that no longer exists, and an executor picking them up by priority alone would re-author executed plans. Position: last.

Prompt: using the plans skill, author one plan (authoring only, do not execute): an origin-closure sweep over nine verified dispositions. Read each origin's full text from docs/history/backlog/ and treat the files as the scope of record, then re-verify every disposition below against current bytes at execution start (the evidence decays; a failed re-verification promotes that origin out of the sweep into its own work item). Verified dispositions (2026-09-28): (1) task-scoped-verification-contract: fixed; the pre-seed consistency gate (`_preseed_verifier_consistency_problems`, refusing cloned verifiers and verifiers depending on strictly later tasks' artifacts before any manifest bytes are written) and the `recover-evidence-contract` operation exist in scripts/execute_plan_runtime.py, landed by the executed preseed-verifier plan (main 07885e0f); (2) quota-probe-wait-minutes: fixed; the probe refuses `--minutes-before` above 300 with a named error (landed 11e63b63); (3) stale-validator-rejected-enum: fixed; the done skill carries the stale-deployment signature routing `invalid state value` on a repo-accepted state to the copy remedy and covering the silent rejected-archive direction, and the deployed validator copy is a symlink to the repo copy (verified on disk); (4) hook-outcome-audit-visibility: repo half landed (agents/hooks/budget-guard/ decision log and heartbeat); the host-side stderr/exit-code enrichment and per-hook heartbeat remain external prerequisites; the item stays open under its recorded Ship-when; (5) model-selection-persist-foreign-key: external prerequisite in full (host application code); stays open as the signal record; (6) subagent-session-record-persistence-races: the repo-side store-level darkness-triage witness is landed in the maintenance runtime overlay; the ordering, hydrate-retry, and resume-guard fixes stay external; stays open; (7) live-record-carrier-migration-deferral: discharged by no-op; the automation listing on 2026-09-28 shows zero automations of any kind, so the old-title record it migrates does not exist; record the no-op witness and close; (8) review-loop-exit-condition-and-metrics: fixed; blocking-only exit, the advisory stop-and-escalate guidance, the per-project strictness split resolved from `personal_projects_root`, and the metrics aggregation pass are landed in the review skills and the maintenance weekly rider by the executed exit-metrics plan; (9) maintenance-autonomous-pipeline: fixed; executed (main 05644b4f) and live in the skill text (the continue-loop condition, in-session authoring chaining, the parked re-arm discharge precedence, the quota-governor consult); also fold the authoring-lane-guard-precedence origin per its own folding direction. Scope arms: (1) re-verify all nine dispositions from disk, one evidence line each in the sweep's record; (2) close the fixed and discharged origins (fold disposition into the executed plans' records where the conventions require, run the claimed-origin checker before any move, flip Status with a dated line); (3) keep the three external-gate watchers open with their Ship-when anchors and facts keys intact, each gaining the dated verification line; (4) no code or skill-text changes; the sweep moves status and evidence only; (5) registry audit notes where the doc-registry write gate requires them.

Standing pre-authorization: accept all recommended options and suggestions throughout without asking the user.

Rejected alternatives:
- Closing the three external-gate watchers with the rest: rejected; their host-side halves are unlanded and their acceptance gates (zero persist_failed over 72 hours, diagnosable hook-failure records, zero persisted_missing) are measurable and unmet, so closure would orphan live signals.
- Re-authoring any of the satisfied items' demands as fresh plans: rejected; the mechanisms are verified on disk and re-authoring executed plans is the exact duplication the do-not-re-author records guard against.
- Leaving the seven satisfied items open until their external siblings close: rejected; mixing satisfied and external origins in one open pool is what makes the backlog untrustworthy for prioritization.

## p90-execute-plan-certified-progress-sync

Added: 2026-09-29 (investigate skill, single-origin consumer witness); amended 2026-09-29 with execute-plan preflight progress-reconciliation witness.

Origins:
- docs/history/backlog/2026-09-29-docs-branch-certified-plan-progress.md

Urgency: Medium; the docs-branch guard refused a checklist update before staging, and a later execute-plan preflight refused the next task because a checkpointed predecessor retained an unobserved RED step and a parent-owned Commit item despite task receipts. A fresh review handles changed plan bytes, but no receipt-backed progress reconciliation closes both gates without false completion claims.

Prompt: using the plans skill, author one focused implementation plan (authoring only, do not execute) for receipt-backed plan progress synchronization across docs-branch and execute-plan preflight. Re-read the backlog origin and verify the current certified-plan guard, source-plan digest selection, task checkbox ordering, runtime preflight ownership check, verification receipts, `done` commit receipt, and both refusal witnesses. Keep substantive plan certification and acceptance-item checks fail-closed. At docs-branch sync, compare the incoming plan with the latest certified plan after normalizing only task checklist markers `[ ]` and `[x]`; permit the overlay only when normalized bytes match exactly, with a witness naming plan path, sidecar, certified digest, incoming digest, and normalization result. At execute-plan preflight, reconcile each checkpointed task's checklist against exact verification and `done` receipts: close parent-owned `Commit:` items only from matching commit evidence, and represent a TDD RED step that could not be observed with an explicit bounded disposition receipt rather than a false checked marker. Refuse unexplained open acceptance items, stale or absent digests, missing/mismatched receipts, and substantive plan drift. Cover both checkbox flip directions, mixed-task progress, valid and foreign commit receipts, unavailable RED evidence, unexplained open acceptance items, substantive edits with checkbox changes, stale/missing certification, actual guard CLI behavior, actual preflight behavior, and docs-branch sync staging refusal/acceptance. Keep archive/history protections intact and update the relevant docs-branch, execute-plan, and done contracts only where required. Use the existing backlog origin as the plan's Backlog origin.

Rejected alternatives:
- Remove or bypass certified-plan ordering: rejected because substantive unreviewed plan content must remain protected.
- Require a fresh full plan review after every task checkbox update: rejected because routine progress is not a substantive contract change and repeated reviews burden the per-task commit path.
- Delay all docs-branch sync until final plan archival: rejected because per-task done owns the commit and documentation-preservation boundary.
- Treat every unchecked line as a false completion claim and refuse all future continuation: rejected because receipt-backed task completion can be valid when a parent-owned commit is recorded or a TDD phase was unobservable; the unresolved item still needs an explicit disposition, never an invented pass.

## p91-execute-plan-post-squash-artifact-cleanup

Added: 2026-09-29 (investigate skill, single-origin witnessed closeout gap)

Origins:
- docs/history/backlog/2026-09-29-execute-plan-post-squash-artifact-cleanup.md

Urgency: Low; the source ref and archived snapshot are redundant after verified landing and plan completion, but the worktree-first lifecycle already specifies cleanup and no active work was lost. This is a missing squash-specific closeout arm, not a reason to relax active-worktree or artifact-preservation gates. Position: last.

Prompt: using the plans skill, author one focused implementation plan (authoring only, do not execute) to close out exact execute-plan run branches and disposable artifacts after a verified squash landing. Read the origin and `docs/history/backlog/2026-09-29-execute-plan-single-worktree-run-identity.md` in full. Re-verify the current worktree-first lifecycle, managed archive behavior, landing implementation, run-artifact migration, and any supported archived-snapshot cleanup operation before choosing a minimal change. The witnessed source branch `codex/execute-plan-preflight-followup` had no linked worktree after archival; its work was squash-landed (`f0d851a2`), its plan later executed and moved to completed (`41a4dc2b`), yet the source branch remained. The sibling backlog handles same-run worktree identity but only permits branch deletion when ancestry proves source commits reachable, which does not cover squash. Preserve the lifecycle's exact-artifact migration and fail-closed behavior. Add one closeout arm that (1) binds the exact run's source branch, worktree, landing destination, and artifact inventory; (2) proves the run's intended changes landed even when squash breaks source-commit ancestry; (3) verifies required durable review and plan artifacts before cleanup; (4) removes only that run's source branch and disposable artifacts once no live task or process depends on them; (5) preserves durable history, active sibling branches, and platform-managed recovery snapshots when there is no supported deletion operation, reporting retained artifacts honestly. Cover ordinary merge and squash, live sibling preservation, migration failure, plan/review retention, repeat closeout, and unsupported archive deletion. Do not use wildcard branch cleanup, blanket clean, raw managed-worktree deletion, or ancestry-only proof. Keep implementation and tests scoped to the existing lifecycle owner, updating other consumers only when the contract requires it.

Rejected alternatives:
- Delete every `codex/*` branch after landing: rejected; active worktrees may own those refs.
- Use source-commit ancestry as the only landed-proof: rejected; it cannot pass after squash.
- Treat managed archival as complete cleanup: rejected; it retains a recoverable snapshot and branch ref.
- Delete archived snapshots by raw filesystem path: rejected; it bypasses platform recovery and ownership semantics.
