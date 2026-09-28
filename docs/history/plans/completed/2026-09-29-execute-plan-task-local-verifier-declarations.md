# Plan: Execute-plan explicit task-local verifier declarations

Backlog origin: docs/history/backlog/2026-09-27-execute-plan-task-scoped-verification-contract.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-29-plan-review-execute-plan-task-local-verifier-declarations-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A consumer run can no longer seed a machine manifest whose declared task commands literally embed a strictly later task's allowed path under the gate's boundary rule, because manifest seeding derives every task's evidence contract from that task's own explicit declaration and refuses embedded later-artifact contracts before any manifest bytes are written.

- Manifest seeding derives per-task verification commands and required criteria only from the task's structured `Evidence:` declaration in the plan; checklist prose, worker summaries, and the global validation block never seed a contract, and the skill layer's mandate stops declaration-less plans at seeding.
- The pre-seed consistency gate refuses a declared command carried by a non-path token whose payload embeds a strictly later task's allowed path under the tail-boundary rule (the `bash -lc` body shape, single-line or marker-bearing) before the manifest is written, naming the task and path with the token elided; pure-path tokens keep exact canonical equality as their sole refusal basis, so nested-path namesakes such as `src/reports/report.txt` and suffix variants such as `reports/report.txt.bak` stay accepted.
- A plan task without an `Evidence:` declaration stops seeding before create with a named remedy (add the declaration through the semantic plan-edit path, which requires a fresh whole-plan review round), instead of silently inferring a contract from prose.
- Corrected-contract recovery keeps its exact task id, claim token, and generation fencing, re-runs the same gate over the merged task map with responsible-task attribution, and refuses only problems whose responsible task is the corrected task, so a sibling's seeded embed can no longer block the sanctioned exit.

## Terms

- **Evidence declaration:** the per-task structured block in a plan document that binds each task's verification commands to the acceptance criteria they cover; the sole seeding source for that task's evidence contract.
- **Pure-path token:** a string argv token containing no whitespace or quote characters whose canonicalization through the driver's fail-closed path policy succeeds (identity when no repository root is supplied); pure-path tokens keep exact canonical equality as their sole matching basis.
- **Non-path token:** any other string argv token (shell bodies single-line or marker-bearing, flag-assignment values, quoted strings); non-path tokens get boundary-ruled containment as the shape-3 basis.
- **Refusal shapes:** the pre-seed gate's three numbered refusal classes: 1, a verifier depending on a strictly later task's artifact by exact canonical token equality; 2, two or more tasks declaring identical whole verification command lists cloned from the global block; 3, a non-path token embedding a strictly later task's allowed path under the tail-boundary rule.
- **Global validation block:** the plan's `## Validation Commands` section; the whole-plan gate checked at the done boundary, never seeded into per-task verifiers.
- **Corrected contract:** the replacement evidence contract supplied to the `recover-evidence-contract` driver operation; fenced by exact task id, claim token, and generation.

## Assumptions

- assume the declaration is authored in the plan document and translated by the orchestrating parent, not parsed by the driver: the driver's create operation keeps consuming a task map, and the skill layer owns translating declarations into that map; basis: the driver's create contract is plan-agnostic today, and plan parsing belongs to the skill and preflight layers, which this plan does not extend.
- assume preflight scope extraction and the worker-role contract are owned by the predecessor plan `docs/history/plans/2026-09-29-execute-plan-worker-lifecycle-and-scope-recovery.md`; this plan does not modify preflight, so the two plans execute in either order; basis: that plan's scope of record owns the preflight scope-parser, worker-prompt, and scope-refresh surfaces.
- assume the witnessed mechanism facts hold at execution time and are re-verified before implementation: the pre-seed helper compares whole argv tokens by exact equality (scripts/execute_plan_runtime.py, the `_preseed_verifier_consistency_problems` helper around line 512), so a path embedded inside one argv string never matches, and the recovery path re-runs the same helper over the merged task map with a string-based sibling filter (around line 8060) whose classification this plan replaces with responsible-task attribution; basis: verified 2026-09-29 against the main tip.
- assume the shape-3 matching basis is deliberately scoped: exact equality remains the sole basis for cleanly-canonicalizing tokens (the pinned `reports/report.txt.bak` and nested `src/reports/report.txt` acceptance classes stay intact), and containment applies to non-path tokens (any token containing whitespace or quote characters, plus tokens whose canonicalization raises) where the canonical later path ends the token or the following character is outside `[A-Za-z0-9._-]`; regex matching over payload strings stays forbidden; basis: the pinned acceptance tests' false-positive rationale and the CRM-607 supplemental witness, and the empirical probe that single-line shell bodies canonicalize cleanly while containing no shell markers, so a canonicalization-raised-only scope would exempt the standard verifier spelling.
- assume no new recovery path and no manifest-edit escape: already-launched malformed contracts keep recovering only through `recover-evidence-contract` under its existing identity fencing; basis: the origin's recovery-interaction section records that operation as the sanctioned exit and the runtime contract prohibits manual manifest edits.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Manifest seeding must derive each task's evidence contract from that task's explicit `Evidence:` declaration and refuse commands embedding later-task artifacts, so a whole-plan shell block can no longer masquerade as a task verifier; driving force: code-quality.

In the CRM-607 consumer run the task checklist declared a focused GREEN command, but the seeded manifest bound the task to the multiline whole-plan `bash -lc` validation block. The worker implemented both required files and the focused test passed, and the driver still refused the result as `malformed-result` because later-task artifacts did not exist at that boundary. The create-time gate missed the shape because its later-artifact check compares whole argv tokens by exact equality, while the shell body embeds future paths inside one string. After this plan, the parent derives each task's commands and covered criteria only from the task's `Evidence:` lines, and the create gate additionally refuses non-path tokens whose payload contains a strictly later task's allowed path under the tail-boundary rule, so the global block stays the whole-plan gate at the done boundary.

Example declaration a plan authors immediately after the task's `Files:` list (the witnessed consumer shape; skill texts carry a generic form):

```
Evidence:
- verify: `mvn -pl segments -am -Dtest=SegmentJobTypeTest -Dsurefire.failIfNoSpecifiedTests=false test` covers SegmentJobTypeTest#maps_segment_job_types
```

## Evaluation Criteria

**Quality dimensions:**
- correctness: the gate refuses every non-path embed shape the new tests pin (single-line and marker-bearing shell bodies, flag assignments, alias and absolute spellings) under the boundary rule, and keeps accepting every cleanly-canonicalizing map the existing and new acceptance pins cover (earlier references, shared declarations, suffix variants, nested-path namesakes).
- compatibility: the only newly refused task maps are those matching refusal shape 3 (non-path tokens embedding a strictly later task's allowed path under the tail-boundary rule); all other currently accepted task maps stay accepted.
- maintainability: all refusal shapes live in the one pre-seed helper with structured attribution, and the skill and contract texts name the same shapes the tests pin, machine-checked by contract-parity probes.

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py` exits 0 with the new tests and pins present.
- The skill and contract texts state the declaration rule and the embedded-path refusal shape, and the `ContractContentParityTest` probes assert both the presence of the new spans and the absence of the three retired phrases.
- `bash scripts/check-no-em-dash.sh file` over the changed docs exits 0, and the all-extensions em-dash scan over the changed Python files exits 0.

**Ship when:**
- The vendored runtime-side skill twins carry the same text at the next vendored sync per the standing sync rules; evidence owner: the vendored-sync backlog rules; closure condition: the runtime twins are byte-identical to the landed skill files after the next sync. [class: OPERATIONS_FOLLOW_UP]
- Consumer operators are prepared for the designed stop wave: every plan authored before this mandate lands stops at seeding on its first post-redeploy run and remedies through the semantic plan-edit path; evidence owner: the execute-plan SKILL.md seeding paragraph's remedy sentence; closure condition: the stop-wave remedy sentence is carried to the runtime-side skill twins by the next vendored sync (byte-identical twins), a post-landing observable that can fail. [class: OPERATIONS_FOLLOW_UP]
- Consumer repositories redeploy the updated driver copy before their next seeded run per the runtime contract's "Resolution policy (normative)" section; evidence owner: the consumer run's preflight deployment check; closure condition: preflight on the updated driver passes in the consumer repository. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (the `_preseed_verifier_consistency_problems` helper, its structured attribution, and the recovery sibling filter)

**Tests:**
- `scripts/test_execute_plan_runtime.py` *(new tests added to the existing pre-seed and recovery test groups, plus acceptance-side comment rewrites and the parity-probe extensions)*

**Docs/contracts:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/plans/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py` preflight scope extraction and the worker-role launch contract; reason: the predecessor plan owns those surfaces and this plan must not collide with them.
- The `recover-evidence-contract` identity-fencing implementation beyond the sibling-filter attribution; reason: the fencing itself just landed and is not a defect.

## Validation Commands

```bash
python3 scripts/test_execute_plan_runtime.py
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/plans/SKILL.md
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/execute_plan_runtime.py scripts/test_execute_plan_runtime.py
```

### Task 1: Refuse embedded later-artifact verifier contracts at create

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_preseed_gate_rejects_shell_body_embedding_later_task_path`; given a two-task map whose Task 1 declares a `bash -lc` command with a single-line body (`test -f reports/report.txt`, canonicalizes cleanly, no shell markers) and a marker-bearing multiline body, each containing Task 2's allowed path, expects create to refuse both before writing the manifest with a problem naming the task id and the later path with the token elided [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preseed_gate_rejects_flag_assignment_embedding_later_path`; given a map whose Task 1 command carries the later task's allowed path in a flag assignment such as `--out=reports/report.txt` (a non-path token whose embedded occurrence ends the token), expects the same refusal, so flag boundaries cannot hide an embedded path [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preseed_gate_rejects_alias_or_absolute_embedding_of_later_path`; given a map whose Task 1 marker-bearing multiline `bash -lc` body embeds the later task's allowed path as `./reports/report.txt` and as the absolute tmp-root spelling, expects the same refusal; the comment notes the embeds are refused via shape-3 containment on the non-path token while a bare clean alias token is refused via shape 1's canonical equality [class: REPOSITORY_TEST]
- [x] Extend `ExecutePlanRuntimeTest#test_preseed_gate_allows_earlier_and_shared_artifact_references` on the acceptance side only: the `reports/report.txt.bak` suffix-variant sub-case stays acceptance with its assertion unchanged as the clean-arm/suffix-variant pin, the comment that pins "never substring containment" is rewritten to the boundary rule, a further sub-case pins the nested-path namesake (`argv: ["cat", "src/reports/report.txt"]` against a later task declaring `reports/report.txt` seeds successfully), a further sub-case pins the tail boundary on a non-path token (a marker-bearing `bash -lc` body embedding `reports/report.txt.bak` with the in-class `.` follower seeds successfully), and a further sub-case pins the same-or-earlier carve-out on a non-path token (a marker-bearing body embedding a path the declaring task also declares seeds successfully); the inverted shape-numbering comments in the recovery pre-seed-gate test (around lines 3488 and 3503) are relabeled to the folded taxonomy (clone signature = shape 2, exact-equality later artifact = shape 1) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py` (the three new refusal tests fail against the current exact-equality gate; the extended allows-test stays green throughout) [class: REPOSITORY_TEST]
- [x] Implement refusal shape 3 in `_preseed_verifier_consistency_problems`: for each task in document order, for each verification command, classify each string argv token as pure-path (no whitespace or quote characters and canonicalization through `canonical_token` succeeds, identity when no repository root is supplied) or non-path (everything else), and for each non-path token containing a strictly later task's canonical allowed path as a substring where the path ends the token or the following character is outside `[A-Za-z0-9._-]` and that path is not declared by the same or an earlier task, collect a problem; the helper's problems gain structured attribution (responsible task id and matching basis beside a display string that names the task id and path first and elides the token to its first line plus a byte count; a clone-signature problem is attributed to the PAIR and refuses recovery when either named task is the corrected task), `create_manifest` keeps joining display strings, exact-equality shape 1 and the clone signature shape 2 stay unchanged as the pure-path bases, and the helper docstring documents all three shapes, the pure-path/non-path scope, and the boundary rule's rationale (suffix-variant and nested-path false positives stay accepted; regex matching over payload strings stays forbidden) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: refuse embedded later-artifact verifier contracts at pre-seed` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Declaration-sourced seeding mandate in the execute-plan skill and runtime contract

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [x] SKILL.md Phase 0 machine-manifest seeding paragraph: retire and replace the derivation sentence "Before invoking create, derive the task-to-evidence mapping from each task's own acceptance criteria and Files list" with the declaration-only rule (derive only from the task's `Evidence:` declaration; checklist prose, worker summaries, and the global validation block never seed a contract), and replace the count-bearing sentence "The create operation refuses both malformed shapes mechanically" with the three-shape enumeration; the remedy sentence for a declaration-less task names the semantic classification of the edit (adding an Evidence block changes the evidence class) and the required fresh whole-plan review round before continuation [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md declaration format rule beside the existing task guidance: one `Evidence:` block per task immediately after the task's `Files:` list; one line per command carrying the exact command and the checklist criteria it covers; every declared command must be runnable at that task boundary; criteria deferred to the final gate stay out of the task's required criteria [class: IMPLEMENTATION_REQUIRED]
- [x] runtime-contract.md Verification evidence envelope section: replace the matching-basis sentence "matched against strictly later tasks' `allowed_paths` entries by exact equality only, never substring containment" with the two-basis rule (exact canonical equality remains the whole-token basis for pure-path tokens; a non-path token embedding a strictly later task's allowed path under the tail-boundary rule is likewise refused with the token elided in durable evidence; regex over payload strings stays forbidden), document shape 3 as the literal embedded shape only (a shell body constructing the path at runtime through variables, encoding, or glob and selection-tool forms, a case-spelled literal on a case-insensitive filesystem, and trailing-dot or backslash-separator spellings on Windows-family filesystems, evade the pre-seed gate by design and still fail closed at the task boundary with recovery as the exit), and name the operator remedies for a false-positive refusal (reword the command, or move the check to the task that owns the artifact; declaring the path on the earlier task to trip the carve-out grants write scope and creates cross-task overlap) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `ContractContentParityTest` and give it a second source: the class additionally reads agents/skills/execute-plan/SKILL.md through the same whitespace-normalized block scanner; presence probes anchor on the amended matching-basis sentence (runtime-contract.md), the three-shape enumeration and the declaration-mandate wording (SKILL.md); absence probes assert all three retired phrases ("derive the task-to-evidence mapping from each task's own acceptance criteria", "never substring containment", "refuses both malformed shapes") appear in neither file [class: REPOSITORY_TEST]
- [x] Run the gates → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` and the em-dash lines in Validation Commands over the changed files [class: REPOSITORY_TEST]
- [x] Commit: `docs: mandate declaration-sourced evidence contracts in execute-plan seeding` [class: IMPLEMENTATION_REQUIRED]

### Task 3: plans skill authoring rule for Evidence declarations

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/test_execute_plan_runtime.py`

- [x] Plan Format task skeleton: add the `Evidence:` block immediately after the task's `Files:` list with a generic placeholder example (a neutral targeted test command covering one named criterion), not the witnessed Maven command [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring rules: state that every plan task carrying implementation work declares its `Evidence:` block at authoring time; the declarations are the execute-plan seeding source; a task without one stops execution at seeding, so the declaration is part of plan completeness [class: IMPLEMENTATION_REQUIRED]
- [x] Integration Points: extend the plans skill's execute-plan integration mention to name the `Evidence:` declaration as the seeding source, verified against the execute-plan SKILL.md seeding paragraph's actual wording [class: IMPLEMENTATION_REQUIRED]
- [x] Add a content probe for the declaration-rule span in `ContractContentParityTest`'s generalized per-source helper (the class gains plans/SKILL.md as a third source beside the Task 2 second source): a test asserting the added declaration-rule sentence is present in agents/skills/plans/SKILL.md through the same fail-closed assert form [class: REPOSITORY_TEST]
- [x] Run the gates → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` (the runtime-neutral shared-skill-body probe reads this file and the new content probe reads the landing span) and `bash scripts/check-no-em-dash.sh file agents/skills/plans/SKILL.md` [class: REPOSITORY_TEST]
- [x] Commit: `docs: add per-task Evidence declaration to the plans skill task format` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Recovery attribution and fencing over declaration-shaped corrected contracts

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] Replace the recovery merged-gate's string-set sibling filter with responsible-task attribution: a problem refuses recovery only when its responsible task names the corrected task id (a pair-attributed clone problem refuses when either named task is the corrected task), keeping display strings for evidence; a sibling's seeded embed of the corrected task's declared path is reported in the outcome evidence without refusing; the recovery operation's docstring wording at scripts/execute_plan_runtime.py around line 7916 is updated to the responsible-task rule [class: IMPLEMENTATION_REQUIRED]
- [x] Generalize the recovery test seed/patch/digest helper to a parameterized N-task map per the existing pre-gate patch pattern: the new fixtures seed a clean multi-task manifest, patch the sibling contract in post-create, recompute the digest, and drive the hold onto the corrected task [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_refuses_corrected_contract_cloning_sibling_list`; given a launched hold on a task whose corrected contract's verification command list deep-equals a sibling's seeded list, expects refusal with the clone problem attributed to the pair so the corrected task's own recovery refuses [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_succeeds_past_sibling_embed_of_corrected_path`; given a launched malformed-result hold on task 3 whose seeded sibling task 1 contract embeds task 3's declared path inside a `bash -lc` body, expects recovery of task 3 to succeed under its exact token and generation fencing with the sibling embed reported in outcome evidence and the manifest otherwise unchanged [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_refuses_corrected_contract_embedding_later_path`; given the same hold whose corrected contract embeds a strictly later task's allowed path inside a `bash -lc` body, expects refusal before mutation with the merged-gate problem naming the task and path, and the manifest bytes unchanged [class: REPOSITORY_TEST]
- [x] Run → expect the acceptance pin GREEN as a regression pin after the Task 1 helper change and the filter change (the existing `test_evidence_recovery_happy_path` continues to pin the corrected single-line contract acceptance), and the refusal pin GREEN as a regression pin (the recovery path re-runs the pre-seed helper over the merged task map) [class: REPOSITORY_TEST]
- [x] Commit: `feat: attribute pre-seed problems to responsible tasks in recovery` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

Recorded at the round-5 cap per the cap-closure terminal shape; five non-blocking r5 nits (the staging record r5 is authoritative for verdicts).

- Task 1 item 1's parenthetical "canonicalizes cleanly, no shell markers" states probe rationale for why the retired raised-only scope would miss the shape, not the classification basis (whitespace); a skimmer could misread it. [residual: accepted, non-blocking, r5]
- Task 4 sequences its tests after the implementation item and carries no explicit RED run; nothing false is claimed, and the sibling-embed pin would have been RED under the interim string-set filter. [residual: accepted, non-blocking, r5]
- The Task 2 absence probes say "neither file"; whether they extend to the Task 3 third source depends on the generalized helper's loop, which Task 3 item 4 leaves implicit (green either way today because plans/SKILL.md carries none of the phrases). [residual: accepted, non-blocking, r5]
- Task 1 item 4's relabel clause identifies the recovery test by line refs only (3488 and 3503) without naming `test_evidence_recovery_rejects_corrected_payload_failing_preseed_gate`. [residual: accepted, non-blocking, r5]
- The display format's "token elided" is vacuous elision for a single-line body token; the test expectation stays satisfiable (task id, path, and byte count asserted present, no absence requirement on the token string). [residual: accepted, non-blocking, r5]
