# Plan: Reclaim after terminal prior-generation worker (the prelaunch false refusal)

Backlog origin: docs/history/backlog/2026-10-08-execute-plan-reclaim-after-terminal-worker.md (the PLAN-PROMPTS entry `execute-plan-reclaim-after-terminal-worker` carries the operator-confirmed prompt)
Driving force: automation
Design input: docs/history/plans/completed/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md (the completed prelaunch-reclaim plan whose protection must remain); the witnessed false refusal (the terminal prior-generation worker row, the matching terminal receipt, the released capacity, the claim failed before launch)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-execute-plan-reclaim-after-terminal-worker-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-execute-plan-reclaim-after-terminal-worker.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The prelaunch-reclaim arm: the direct-claim recovery path that bypasses the claim lease for a claimed prelaunch claim holding a stranded prelaunch contract (no registered worker, no stale launch residue, the two-attempt budget, the approval-evidence fence) - the completed prelaunch-reclaim plan's sanctioned exit, which this plan narrows, never relaxes.
- The witnessed false refusal: a claim that failed before launch, whose only registered worker row is TERMINAL and from a PRIOR GENERATION (a worker registered before the current claim's generation), with a matching terminal receipt and released capacity - today's arm refuses the bypass because a registered worker row exists, and the claim then waits the full lease for hours with no launch record.
- The narrow predicate: early reclaim is allowed only when EVERY worker row attributable to the current claim is absent AND any historical worker row is proven terminal with evidence matching the prior worker identity AND no capacity is held. Active, ambiguous, mismatched, incompletely reconciled, or capacity-holding worker state keeps today's refusal.

## Why

A claim blocked before launch waits for the full lease even though its only registered worker is terminal, its capacity reservation is released, and the claim has no launch record - the witnessed recovery strands for hours. The completed prelaunch-reclaim plan requires no registered worker before bypassing the lease; that requirement protects against live or uncertain workers and must remain for every state it was built for. This plan adds one narrow, fully-evidenced exclusion: a historical terminal row from a prior generation with matching evidence and no held capacity is not a live worker, and treating it as one is the false refusal. Every fence the completed plan introduced - exact task, claim token, generation, refusal reason, launch residue, approval evidence, the two-attempt budget - is preserved byte-for-byte in meaning.

## Gist & Examples

TLDR: the prelaunch-reclaim predicate gains one evidenced exclusion - a terminal prior-generation worker row with a matching receipt and released capacity does not block the bypass - and every existing fence stays.

Before: the operator's recovery waits hours behind a full lease because a dead worker row from an earlier generation is registered against the claim's task.

After: the same state reclaims immediately; a live worker, an ambiguous row, a mismatched receipt, an unreleased capacity, or a missing receipt still refuses exactly as today, with focused witnesses for each refusal class.

Edge cases: a worker row registered to the CURRENT claim (any state, including terminal) keeps today's refusal - the exclusion is for prior-generation rows only; a terminal row whose receipt does not match its identity refuses; a terminal row with held capacity refuses; the two-attempt budget and the `prelaunch-reclaim-cap` refusal apply unchanged to the new path; no general worker-registry or launch-lifecycle surface is revised.

## Outcome

The witnessed multi-hour false refusal class is closed: a prelaunch claim whose only worker evidence is a proven-terminal prior-generation row with matching receipt and released capacity reclaims through the bypass, and every protective fence is preserved with focused witnesses for the acceptance and each refusal class.

Gate delta: one predicate extension in the runtime recovery arm's direct surface plus its focused test witnesses (terminal-prior-generation acceptance; active, ambiguous, mismatched, held-capacity, missing-receipt, and at-cap refusals); pins beside provenance; no general worker-registry or launch-lifecycle revision, no schema change, no fence relaxed.

## Assumptions

- The predicate is attributable-row-scoped, not registry-scoped: "every worker row attributable to the current claim is absent" keys on the claim's task and generation identity (the fields the recovery arm already reads), and a historical row is prior-generation when its generation is STRICTLY LESS THAN the current claim's (a terminal row of the current generation keeps today's refusal, pinned by a witness). Basis: the entry's "derive a narrow predicate that distinguishes this historical terminal row from a worker registered to the blocked claim", the recovery arm's existing identity fields, and the Edge-cases promise.
- The terminal evidence match is receipt-to-row identity matching (the same worker identity on the row and the receipt, the receipt terminal), and "released capacity" is the reservations-absence check the arm already runs (the released tombstone in the capacity entries map is optional extra evidence, not a required read). Basis: the entry's evidence list and the constraint against revising the general registry.
- The skill surfaces naming the no-registered-worker precondition are named files, not deviations: agents/skills/execute-plan/SKILL.md's recovery precondition sentence and agents/skills/execute-plan/runtime-contract.md's direct-claim fast path both spell "no registered worker" today (verified at review r1), so both gain the exclusion by reference in the same landing and join the Review Scope. Basis: the entry's "keep the change in the runtime recovery predicate and its direct tests" plus the verified precondition sentences.
- Residual accepted: a prior-generation row that is terminal-but-mismatched still refuses, even though a human could see it is dead - the fence's cost, accepted to keep the exclusion narrow and fully evidenced. Basis: the entry's rejected alternatives (identity matching is the protection).

Decision points requiring a grill: none remain (the operator-confirmed entry derives the predicate's shape, enumerates the fences, the witness classes, and the four rejected alternatives).

## Standing constraints

- Every fence of the completed prelaunch-reclaim plan is preserved in meaning: exact task, claim token, generation, refusal reason, launch residue, approval evidence, and the two-attempt budget with its `prelaunch-reclaim-cap` refusal.
- The lease path is never relaxed for active, ambiguous, mismatched, or incompletely reconciled worker state; the general worker registry and the launch lifecycle are never revised.
- The full battery stays green at every task landing: the runtime suite (the focused witnesses among them), the parallel-work regressions, the pins suite, the liveness test, em-dash, hygiene; a red suite stops the task for reconciliation, never a weakened check.
- Deploy truth: the runtime edit reaches its runtime home at this plan's merge-locked landing (the landing is the deploy, and the runtime script's runtime-scripts.list entry carries the deployed copy in the same run).
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; the predicate extension is additive (a guarded early-return path), so a revert restores the refusal exactly; the witnesses and pins revert with their task.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the acceptance witness passes only on the terminal-prior-generation-matching-released shape, and each refusal witness (active, ambiguous, mismatched, held-capacity, missing-receipt, at-cap) refuses with today's labels.
- regression safety: the full runtime suite green (the completed prelaunch-reclaim plan's own witnesses unchanged and passing); the battery green at every landing.
- scope discipline: the changes touch only the recovery predicate's direct surface, its test file, and the pins; the general worker registry and launch lifecycle untouched.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- The next prelaunch claim stuck behind a terminal prior-generation row reclaims immediately, and every other worker state refuses as before; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (the prelaunch-reclaim predicate's narrow exclusion; nothing else in the file)
- `agents/skills/execute-plan/SKILL.md` (the recovery precondition sentence gains the exclusion by reference)
- `agents/skills/execute-plan/runtime-contract.md` (the direct-claim fast path's precondition sentence gains the exclusion by reference)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (the focused witnesses: the acceptance and the six refusal classes)
- `scripts/check_maintenance_pins.sh` (pins beside provenance, if any span is pinned)

**Docs:**
- `docs/history/backlog/2026-10-08-execute-plan-reclaim-after-terminal-worker.md` (read-only this plan; flipped covered by the landing rider)

**Read-only (referenced, never edited):**
- `docs/history/plans/completed/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md` (the completed prelaunch-reclaim plan whose fences this plan preserves)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (the audit's recovery family evidence)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-08-execute-plan-reclaim-after-terminal-worker.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## execute-plan-reclaim-after-terminal-worker` (frozen under docs/tmp/authoring-claims/2026-10-10-execute-plan-reclaim-after-terminal-worker.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -cE "prior[- ]generation .*terminal|terminal .*prior[- ]generation" scripts/execute_plan_runtime.py   # expect >=1 (the exclusion's spelled conjunction, anchored against the pre-existing unrelated prose)
grep -c "prelaunch-reclaim-cap" scripts/execute_plan_runtime.py   # unchanged >=1 (the budget fence preserved)
grep -c "current generation" scripts/test_execute_plan_runtime.py   # expect >=1 (the strictness witness)
```

**Tests:**
```bash
python3 scripts/test_execute_plan_runtime.py -k prelaunch   # exit 0 AND at least one test ran
python3 scripts/test_parallel_work_regressions.py   # exit 0
bash scripts/check_maintenance_pins.sh   # exit 0
bash scripts/check-no-em-dash.sh file scripts/execute_plan_runtime.py   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: the narrow predicate and its focused witnesses

Files:
- scripts/execute_plan_runtime.py
- scripts/test_execute_plan_runtime.py
- agents/skills/execute-plan/SKILL.md
- agents/skills/execute-plan/runtime-contract.md
- scripts/check_maintenance_pins.sh

- [x] Extend the prelaunch-reclaim predicate with the narrow exclusion: when every worker row attributable to the current claim is absent and a historical worker row is proven terminal with receipt-to-row identity matching and released capacity, the bypass proceeds; every existing fence (exact task, claim token, generation, refusal reason, launch residue, approval evidence, the two-attempt budget with its `prelaunch-reclaim-cap` refusal) preserved in meaning, and active, ambiguous, mismatched, incompletely reconciled, or capacity-holding state keeps today's refusal with today's labels. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the focused witnesses: terminal-prior-generation acceptance (the witnessed shape reclaims immediately) and the refusal classes - active row, ambiguous row, mismatched receipt, held capacity, missing receipt, at-cap, and the current-generation terminal row (pinning the strict less-than on generations) - each refusing with today's labels; the completed plan's existing witnesses pass unchanged. [class: REPOSITORY_TEST]
- [x] Run the runtime suite (`-k prelaunch` with at least one test ran), the parallel-work regressions, the pins suite, the liveness test, em-dash over the touched path, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
