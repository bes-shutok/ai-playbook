# Plan: Coordination single-writer + TTL (D-9 as one durable contract across the merge-lock, execution-claim, and staged-state machinery)

Backlog origin: docs/history/backlog/2026-10-09-lockless-staged-landing-orphan-blocks-landers.md and siblings (the PLAN-PROMPTS entry `coordination-single-writer-ttl` carries the operator-confirmed prompt; sanctioning policy directive D-9; the audit's #2 rated coordination blocker family)
Driving force: reliability
Design input: docs/maintenance/operator-directives.md (D-9: no lane blocks indefinitely on a coordination hold); docs/maintenance/machinery-blocker-audit-2026-10-09.md (suggestion 3; the four witnessed shapes); the flagship witness (the overnight lockless-staged-orphan block)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-coordination-single-writer-ttl-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-coordination-single-writer-ttl.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- Bounded exit: every refusal on a foreign hold first waits a bounded interval (the quiesce wait, seconds-scale for landing windows per the witnessed ledger rows), then reports the holder's identity and routes onward - re-dispatch, park-for-operator, or skip-with-report - never blocking indefinitely.
- Liveness proof: the evidence set that justifies self-service reclaim of a foreign hold - for a worker or claim, the claim file, the live manifest, and the checkout process all verifiably dead; a live holder is never reclaimed, only waited on boundedly or reported.
- The staged-orphan shape (arm 1): a stager that never held the merge lock is invisible to the lock contract while converting every other session's landing into a refusal; the landing critical section gains staged-state visibility with a bounded quiesce wait, then the holder-identified report routing onward, per the sanctioned exact-path workaround already operator-approved in the origins.
- The resume-collision shape (arm 3): a restored worktree that still holds a verifiably live worktree state gains a claim takeover or re-derive path instead of a bare collision refusal.
- The TOCTOU shape (arm 4): the claim is re-checked under the same critical section that grants the work.
- Arm 2 (discharged): the prelaunch reclaim after a prior worker's terminal termination is landed by the covering plan docs/history/plans/2026-10-10-execute-plan-reclaim-after-terminal-worker.md (its origin row covered), and this plan does not touch that surface.

## Why

The audit's #2 rated coordination blocker family: four witnessed shapes where a lane sat blocked with no bounded wait, no holder identity, and no adjudication path - the flagship lasted overnight while a compliant, landing-ready session stood down. Directive D-9 states the policy (never block indefinitely; bounded waits carry the holder identity; self-service reclaim requires a liveness proof; no new lock family); this plan lands it as one durable contract across the machinery the lanes already use, consolidating rather than adding. The witnessed takeover-of-a-live-peer is the design hazard that shapes every arm: liveness first, bounded waits second, routing third, reclaim last and only on proof.

## Gist & Examples

TLDR: the landing critical section sees staged-state orphans with a bounded quiesce wait then a holder-identified routing; restored-worktree resumes take over or re-derive a verifiably live state instead of colliding; the claim is re-checked inside the grant critical section; every exit carries the holder identity; arm 2 is already landed.

Before: a landing refuses on a foreign staged set with no visibility into who staged it and no bounded wait; a restored worktree's resume collides with its own live state; a claim passes its check then loses the race before the grant.

After: the same landing waits bounded, names the stager, and routes (re-dispatch, park-for-operator, or skip-with-report); the resume takes over or re-derives; the grant critical section re-checks the claim; every refusal names its holder and its next action.

Edge cases: a live holder is never reclaimed - the liveness proof (claim file, live manifest, checkout process all dead) is the only self-service key, and its absence routes to the operator; the quiesce wait is bounded and its expiry is the routing trigger, not a second blocking wait; the small claims contract-drift rows (dir-resolution drift, stem-case drift) ride as riders only if the execution budget fits, else they stay separate small plans; no new lock family - every arm lives inside the existing merge-lock and claim contracts.

## Outcome

The four witnessed coordination shapes each carry a bounded, holder-identified exit inside the existing machinery: the staged orphan gains visibility and routing, the restored-worktree resume gains its takeover/re-derive path, the claim grant re-checks under its critical section, and the already-landed prelaunch reclaim (arm 2) is recorded as the composing precedent - with no new lock family and no live holder ever reclaimed.

Gate delta: the landing critical section's staged-state pre-refusal gains the bounded quiesce wait and the holder-identified routing (the pre-refusal already names the staged set - it gains the wait and the onward route); the execute-plan claim takeover/re-derive path gains the restored-worktree arm; the claim grant gains the in-critical-section re-check; pins beside provenance; no new lock family, no schema addition beyond the existing lock metadata and claim files, no refusal removed - every today-refusal remains reachable, each now bounded and named.

## Assumptions

- Arm 1's implementation home is the landing critical section's existing staged-state pre-refusal (the dirt-gate refusal the lockless-staged-orphan witness tripped), gaining the bounded wait and the routing there rather than a new detector. The report carries the staged set plus a holder-or-unattributed classification: a staged path carries no session attribution, so the holder identity is attempted by cross-referencing the open claim files (whose plan paths intersect the staged set) and reported as unattributed when nothing matches - D-9's holder-identity requirement is met by naming the staged set and the attribution result, never by inventing an identity. The wait runs inside the merge-lock critical section, so it is capped at a small fraction of the lock's own wait budget, its lock-hold extension is acknowledged, and expiry routing (park-for-operator in the witnessed shape) is the expected outcome the wait is not designed to beat. Basis: the witnessed refusal path, the staged-path enumeration's attribution limits, and the sanctioned exact-path workaround the origins record.
- The wait bound is seconds-scale and capped against the lock's own wait budget (it extends the hold; it never outlives it), named at the call site, with the expiry routing per D-9's three routes and the route choice recorded in the session notes; the expiry route is the expected outcome for a true orphan (the stager is gone or lock-invisible). Basis: the rejected alternative's wording (immediate escalation churns the operator per hold), D-9's routing vocabulary, and the lock-hold arithmetic.
- Arm 3's takeover requires the restored worktree's verifiably same-run state, proven by evidence that cannot false-positive live-as-dead: the covering plan's receipt-to-row terminal evidence shape (state fields written only by the recorded release paths), never process enumeration (a pid check cannot distinguish zombie from live and fails across hosts); verification failure is the DEFAULT and keeps today's collision refusal. The takeover composes with the restored-worktree resume rules the skill already carries rather than adding a second resume mechanism. Basis: the entry's arm (3) wording, the takeover-of-a-live-peer hazard, and the covering plan's evidence shape.
- Arm 4's home is scripts/execution_claim.sh's claim-mutation sites (the TOCTOU origin row's own read-then-act sites: the stale-claim takeover's removal, the release's removal, the stamped write's move), serialized or last-instant compare-and-deleted per that row's suggested direction - there is no separate 'grant critical section' in the runtime to re-check in, and no second lock is introduced. Basis: the entry's arm (4) wording, the origin row's finding, and the no-new-lock-family constraint.
- Arm 2 is discharged by the covering landing and cited, not re-implemented: this plan's liveness-proof vocabulary for arms 1/3 quotes the landed terminal-prior-generation exclusion's proof shape (verifiably dead evidence per surface) as the family precedent. Basis: the covering plan and its covered origin row.
- Residual accepted: the bounded waits add a seconds-scale latency to the witnessed refusal paths; the routing records make the refusals actionable at the cost of one report line per refusal. Basis: the audit's own pricing of the unbounded-block cost.
- The claims contract-drift rows ride only if the execution budget fits (the entry's own constraint); the plan's tasks do not assume them.

Decision points requiring a grill: none remain (the operator-confirmed entry fixes the four arms, the constraints, and the five rejected alternatives including the lock-removal, blind-TTL, ad-hoc-waits, straight-to-operator, and directive-only shapes).

## Standing constraints

- Never reclaim a live holder: the liveness proof is the only self-service key, and the takeover-of-a-live-peer witness is the design hazard every arm is checked against.
- Bounded waits carry the holder identity; every refusal names its holder and its next action (re-dispatch, park-for-operator, or skip-with-report).
- The merge-lock critical section stays the serialization point for genuinely shared mutable state; no new lock family.
- The full battery stays green at every task landing: the runtime suites, the claims/locks suites (the merge-lock and execution-claim test surfaces), the parallel-work regressions, the pins suite, the liveness test, em-dash, hygiene; a red suite stops the task for reconciliation, never a weakened check.
- Deploy truth: the skill and script edits reach their runtime homes at this plan's merge-locked landing (the landing is the deploy).
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; the quiesce/routing and takeover arms are additive guarded paths, so each task reverts cleanly; the pins revert with their tasks.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each arm's bounded exit names the holder, carries the identity through the report, and routes per D-9; the liveness proof gates every self-service reclaim; the today-refusals remain reachable for live or unprovable state.
- regression safety: the claims/locks suites and the battery green at every landing; the existing fast paths byte-identical where the arms do not touch them.
- scope discipline: the changes touch only the landing critical section's staged-state surface, the claim takeover/grant surfaces, the covering skill text, and the pins.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- The next foreign staged set waits bounded, names its holder, and routes instead of blocking; the next restored-worktree resume takes over or re-derives; the next claim grant re-checks under its critical section; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/land_squash.sh` (arm 1: the staged-state pre-refusal gains the bounded quiesce wait and the holder-identified routing)
- `scripts/execution_claim.sh` (arms 3-4: the restored-worktree takeover/re-derive beside refuse_fresh_foreign_claim; the claim-mutation sites' serialization or compare-and-delete)
- `agents/skills/execute-plan/SKILL.md` (the resumed-lane and grant sentences gain the bounded-exit wording by reference)

**Tests:**
- `scripts/test_execution_claim.py` (arms 3-4 fixtures: the takeover on verifiable same-run state, the refusal on unprovable state, the serialized mutation or compare-and-delete behavior)
- `scripts/test_land_squash.py` (Task 1: the declared fixture layer for land_squash.sh - the wait/route behavior's executable proof)
- `scripts/test_parallel_work_regressions.py` (the battery)
- `scripts/check_maintenance_pins.sh` (pins beside provenance)

**Docs:**
- `docs/history/backlog/2026-10-09-lockless-staged-landing-orphan-blocks-landers.md` (read-only this plan; flipped covered by the landing rider)
- `docs/history/backlog/2026-10-09-execute-plan-restored-worktree-resume-claim-collision.md` (read-only this plan; flipped covered by the landing rider)
- `docs/history/backlog/2026-10-07-execution-claim-ownership-toctou-serialization.md` (read-only this plan; flipped covered by the landing rider)

**Read-only (referenced, never edited):**
- `docs/history/plans/2026-10-10-execute-plan-reclaim-after-terminal-worker.md` (the arm-2 covering precedent; its liveness-proof shape quoted)
- `docs/maintenance/operator-directives.md` (D-9, the policy of record, cited not edited)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (the four witnessed shapes)

**Receipts:**
- Origin rows: the three backlog rows above (Status: open; the landing rider flips them covered naming this plan; the fourth origin row is covered by the arm-2 precedent)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## coordination-single-writer-ttl` (frozen under docs/tmp/authoring-claims/2026-10-10-coordination-single-writer-ttl.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -c "quiesce" scripts/land_squash.sh   # expect >=1 (the bounded wait)
grep -c "holder" scripts/land_squash.sh   # expect >=1 (the identity carried through the report)
grep -c "same run" scripts/execution_claim.sh   # expect >=1 (the takeover arm)
grep -c "quiesce\|bounded" scripts/land_squash.sh   # expect >=1 (the bounded wait)
grep -c "unattributed" scripts/land_squash.sh   # expect >=1 (the honest classification)
grep -c "liveness" agents/skills/execute-plan/SKILL.md   # expect >=1 (the proof vocabulary)
```

**Tests:**
```bash
python3 scripts/test_execution_claim.py -k restored   # exit 0 AND at least one test ran
python3 scripts/test_parallel_work_regressions.py   # exit 0
bash scripts/check_maintenance_pins.sh   # exit 0
bash scripts/check-no-em-dash.sh file scripts/land_squash.sh scripts/execution_claim.sh   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: arm 1 - the staged-orphan bounded exit in the landing critical section

Files:
- scripts/land_squash.sh
- scripts/test_land_squash.py
- scripts/check_maintenance_pins.sh

- [x] Give the staged-state pre-refusal the bounded exit: on a foreign staged set, wait the named bound (seconds-scale, capped against the lock's own wait budget, the lock-hold extension acknowledged), then report the staged set with the holder-or-unattributed classification (the open claim files cross-referenced by plan path; unattributed reported as unattributed) and route onward per D-9 (re-dispatch, park-for-operator, or skip-with-report; the route recorded in the session notes); a live merge-lock holder keeps the lock's own bounded wait; the pre-refusal stays reachable exactly as today when the routing is park-for-operator. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the arm-1 fixture in `scripts/test_land_squash.py` (the script's declared fixture layer): a foreign staged set triggers the bounded wait then the routed report carrying the staged set and the attribution classification; the park-for-operator route keeps today's refusal shape. [class: REPOSITORY_TEST]
- [x] Run the land-squash fixture suite, the parallel-work regressions, the pins suite, and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 2: arms 3-4 - the restored-worktree takeover and the claim-mutation serialization

Files:
- scripts/execution_claim.sh
- agents/skills/execute-plan/SKILL.md
- scripts/test_execution_claim.py
- scripts/check_maintenance_pins.sh

- [x] Land arm 3 in `scripts/execution_claim.sh` beside the fresh-foreign-claim refusal: a restored worktree whose state verifies as the same run resuming (the receipt-to-row evidence shape, never process enumeration; verification failure defaults to the refusal) takes over or re-derives its claim instead of colliding. [class: IMPLEMENTATION_REQUIRED]
- [x] Land arm 4 in `scripts/execution_claim.sh`'s claim-mutation sites (the stale-claim takeover's removal, the release's removal, the stamped write's move): serialize the mutation or make it a last-instant compare-and-delete per the origin row's suggested direction - never a second lock; a lost race refuses with today's labels naming the racing holder. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the fixtures in `scripts/test_execution_claim.py` with `restored` in their test names (the `-k restored` validation command filters on the substring): the takeover on verifiable same-run state, the refusal on unprovable state, and the serialized-mutation/compare-and-delete behavior (the race fixture states the seam it uses - the factored predicate or the compare-and-delete pair - since the raw window is not directly constructible); the skill's resumed-lane and grant sentences gain the bounded-exit wording by reference. Add the pins beside provenance. [class: REPOSITORY_TEST]
- [x] Run the full battery: the claim suite (with at least one test ran), the land-squash fixture suite, the parallel-work regressions, the pins suite, the liveness test, em-dash over the touched paths, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
