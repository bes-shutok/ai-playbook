# Plan: Receipt-fenced recovery for reviewed execute-plan scope changes

Backlog origin: `docs/history/backlog/2026-09-29-execute-plan-reviewed-scope-recovery-successor.md` (Priority: high)
Authoring status: ready. Narrowed to the current successor backlog on 2026-09-29; the prior staging series (r1-r8) reviewed the superseded broader draft and does not certify this version. Aligned 2026-09-29 (evening) to the landed worker-lifecycle runtime; the mechanism-facts block below pins the landed primitives and composition sources the implementation must reuse. Implementation has not started.
Driving force: new-capability. Justification: this is not one of the five driving principles, but it is implemented anyway because a legitimate reviewed scope change currently strands the seeded prelaunch claim until lease expiry with no auditable exit, the gap that led the worker-lifecycle execution to descope its Task 7; park-triage would not take it because the stranded-claim path stays live on the execute-plan runtime's prelaunch boundary until this recovery exists.
Plan review record: the staging series docs/reviews/2026-09-29-plan-review-execute-plan-reviewed-scope-recovery-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Allow one legitimate reviewed task-scope change to recover before launch through a driver-owned, auditable transition, while ordinary preflight continues to reject scope mismatches.

- Recovery rotates the exact prelaunch claim's identity across the claim and every identity carrier of its prepared handoff intent, and replaces the eligible task's canonical allowed paths (moving the evidence-contract digest the replacement changes) from the task's structured `Files:` declaration, so the refreshed manifest passes ordinary preflight and the launch boundary's validation unchanged.
- The transition is bound to the current plan digest, the latest ready review round covering that digest, and a fresh preflight recomputation whose only failure is the target task's scope drift; the replay fence on the recorded receipt is evaluated first and matches the recorded prior claim identity.
- Refusal paths preserve the manifest byte-for-byte; successful recovery lands the whole closed mutation set (claim identity, the three handoff-intent carriers, the task's allowed paths with the evidence-contract digest, the manifest generation bump, and one receipt) in one locked manifest write, then proceeds through ordinary preflight and launch with the rotated identity.

## Terms

- **Reviewed scope**: the normalized paths in the task's structured `Files:` declaration for the current plan revision, after that revision passes plan review and readiness gates.
- **Recoverable prelaunch claim**: the exact intent-backed prelaunch claim in the claimed state with no launch record, worker, or reservation, and no live claim-group ownership, whose fresh ordinary-preflight recomputation fails with exactly the target task's scope-drift failure shape.
- **Scope recovery receipt**: a bounded runtime history entry keyed on the prior claim identity (task id, prior token and generation), recording the plan digest, the review evidence identity (review artifact path, round number, source digest), the prior and replacement scopes, the outcome, and the rotated claim identity.

## Assumptions

Decision points requiring a grill: none remain.

- The operation handles only a legitimate reviewed scope change for one exact prelaunch claim; it does not repair launched work, import a new manifest, or bypass ordinary preflight.
- The structured `Files:` declaration is the sole source of replacement paths. Backticked prose and other path-looking text do not add scope.

Established mechanism facts to author from (re-verify each on disk at execution start; the plan pins no line numbers by design):

- The worker-lifecycle landing (f4b110bb) added `_plan_declared_files` to `scripts/execute_plan_runtime.py`, a parser for the task's structured `Files:` declaration. The recovery operation reuses it as the sole path-parsing source; adding a second parser or a parallel declaration reader is out of scope.
- The same landing landed the eligibility lookups this plan's checks consume: launch-record, worker-state, and reservation-state lookups and the claim-group ownership lookup. Recovery composes these lookups; it adds no new lookup machinery beyond the review-evidence composition pinned below.
- The prepared handoff intent is the only prelaunch claim shape recovery admits (the runtime also creates direct claimed claims with no intent, which recovery refuses as not intent-backed): `_prepare_handoff_locked` writes the successor identity into three carriers (`successor`, `outcome_action` including its `idempotency_key`, and `prelaunch_binding`), and recovery requires that shape, meaning the claim's handoff intent must exist and key to the claim, re-stamping every carrier the writer stamps.
- Review evidence is resolved by composition, never by re-derivation and never by parsing the review markdown: the recovery resolves the reviews directory through `resolve_reviews_dir` (`scripts/validate_review_staging.py`), derives the feature slug through `feature_slug` and the latest round through `latest_review_round` (`scripts/plan_readiness.py`), and determines readiness with the recorded digest and verdict through the readiness validator's own evaluation composition (`evaluate_readiness`). These imports are the sanctioned review-evidence composition; this one operation supersedes the runtime's never-reads-review-sidecars posture, documented as such in Task 2. The composition is coherent under concurrency: the plan bytes are read once per recovery and the round and digest recorded in the receipt are re-verified (latest round re-resolved and on-disk bytes re-hashed, refusing by name on disagreement) before the receipt is written. The composition imports live function-locally inside the recovery operation, mirroring the runtime's lazy-import precedent for cold dependencies, and the never-patched rule scopes to these imports.
- The manifest lock (`_manifest_lock`) is deliberately non-reentrant and the preflight entry point acquires it for the manifest load only. This plan builds the composition it needs (a Task 1 build step, not a landed fact): the preflight check body factors into a lock-free private helper that takes the already-loaded manifest, the plan text, and the raw plan bytes or the resolved plan path for the single bounded digest read, and performs no locking and no manifest loads; preflight keeps its existing lock scope (acquire, load, release, then call the helper), and recovery loads its own manifest under its single locked mutation and calls the same helper. No second encoding of the preflight decision is added, and the existing preflight tests are the refactored entry point's regression gate.
- The drift check is widening-only: it reports plan paths the seeded scope does not cover and never reports seeded paths the reviewed plan dropped. Recovery admits reviewed widenings (the drift-failure shape); a reviewed narrowing passes ordinary preflight and leaves the wider seeded scope live, which is out of scope here.
- The task-local-verifier plan is executing against the same runtime file in a sibling worktree. Re-derive every anchor against the current bytes at execution start; its landed shape wins where declarations differ.
- This plan is the minimal sanctioned exit of the descoped worker-lifecycle Task 7 (see the successor origin's excluded-residues list): no snapshot-coherent readiness capture, no actor provenance, no new test suite. Any arm an executor proposes that adds one of those is out of scope, not a gap.

## Gist & Examples

TLDR: recover one valid reviewed prelaunch scope refresh through a receipt-fenced claim rotation, so legitimate scope corrections stop stranding a prelaunch claim until lease expiry; force: new-capability (a legitimate reviewed change must exit cleanly through an auditable transition instead of wedging the claim).

When a task's reviewed `Files:` list changes after the runtime claim is seeded, preflight should continue to refuse the stale scope. A narrow recovery command can verify that exact claim is still an intent-backed prelaunch claim, verify the latest ready review round covers the current plan digest, require a fresh preflight recomputation to fail with exactly the target task's scope drift, replace the task's canonical allowed paths (moving the evidence-contract digest with them), rotate the claim and every identity carrier of its prepared handoff intent in one locked manifest write, and record the transition. The replay fence is evaluated first and matches the recorded prior claim identity, so an identical retry returns the recorded outcome. The operator then uses ordinary preflight and launch.

## Design Invariants

- Ordinary preflight remains read-only, refuses every scope-widening mismatch (the drift check is widening-only), and gains no persistence.
- Recovery changes only the exact eligible prelaunch claim, every identity carrier of its prepared handoff intent, that task's canonical allowed paths together with the evidence-contract digest that replacement moves, the manifest generation bump that accompanies the claim-row rotation, and the appended receipt; it refuses after launch, when worker or reservation evidence exists, or when a live claim-group owns the claim.
- Every refusal leaves the manifest byte-identical and appends no recovery receipt.
- Successful recovery lands the whole closed mutation set in one locked manifest write, records the old and new scopes, and preserves completed-task evidence and unrelated manifest state.
- Replacement paths come only from the structured `Files:` declaration.

## Tasks

### Task 1: Add the minimal locked scope-recovery transition

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Write inventory (the closed set of manifest mutations for one successful recovery; every item lands in the one locked manifest write; a mutation outside this list is out of scope):

- Claim row identity: a fresh token and a bumped generation, citing the reclaim/release rotation precedent; the same locked write bumps the global manifest generation once alongside it (the generation-bumping precedents all do).
- `intent.successor` identity fields, re-stamped with the new token and generation.
- `intent.outcome_action` identity fields, re-stamped with the new token and generation (its `idempotency_key` embeds the launch id and is re-stamped as part of the carrier).
- `intent.prelaunch_binding` identity fields, re-stamped with the new token and generation, preserving the claim owner and launch id.
- The launch id and the claim owner do not rotate; the landed rotation precedents preserve both across carriers, and the five-field parity the launch boundary enforces stays intact on the new token and generation.
- The task record's canonical allowed paths, canonicalized from `_plan_declared_files` over the current plan section and refusing any entry that fails canonicalization or duplicates another after alias resolution (the create boundary's path policy, not preflight's raw-path fallback).
- `evidence_contract_digest`, recomputed over the post-replacement task map, mirroring the landed evidence-contract replacement operation.
- One bounded history receipt keyed on the prior claim identity (task id, prior token and generation), recording the plan digest, the review evidence identity (review artifact path, round number, and the recomputed plan-bytes digest the readiness composition has proven equal to the recorded source digest), the prior and replacement scopes, the outcome, and the rotated claim identity.

- [x] Add a driver operation that accepts the exact task and claim identity, derives the plan digest, review evidence, preflight recomputation, and replacement paths from repository state, and refuses caller-supplied evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Factor the preflight check body into the lock-free helper pinned in Assumptions (it takes the already-loaded manifest, the plan text, and the raw plan bytes or the resolved plan path for the single bounded digest read, performs no locking and no manifest loads, and returns the structured result; the digest check keeps hashing raw file bytes, since the bounded reader's stripped, replacement-decoded text is not byte-faithful, and no second digest recipe is introduced); preflight keeps its existing acquire/load/release scope and calls the helper; keep the existing preflight tests green as the refactored entry point's regression gate. [class: IMPLEMENTATION_REQUIRED]
- [x] Under one manifest lock acquisition, evaluate the history replay fence first against the latest recorded receipt's prior identity only (same task id, prior token, and generation as recorded): an identical replay re-verifies that the receipt's recorded rotated claim identity is still the identity of the live intent-backed claimed prelaunch claim (claimed state, prepared intent, unconsumed binding) and, if it is, returns the recorded outcome with an explicit replay marker naming the matched receipt, any other state (launched, replaced, closed, reclaimed) refusing as stale identity naming the matched receipt; a request whose identity matches an older receipt's prior identity falls to the stale-identity refusal naming that older receipt; any other mismatched replay naming that task is refused with the latest recorded receipt named; a request carrying the current live claim identity is not a replay and proceeds through ordinary eligibility (a passing second correction appends a second bounded receipt). Then verify eligibility: the driver resolves the plan file directly as the facts-resolved plans directory joined with the manifest's recorded plan slug and the `.md` extension (repository-resolved, never caller-supplied; the full-stem identity is the binding, and `feature_slug` is used solely as the reviews-directory discovery key); the claim's handoff intent exists and keys to the claim (the prepared-successor shape), and the intent-backed claimed claim has no launch record, worker, or reservation, and no live claim-group ownership; require the fresh preflight recomputation (via the lock-free helper) to fail with exactly the widening scope-drift problem for the target task whose drift entry carries a non-empty plan-path set, excluding the parse-problem and missing-declaration shapes; determine readiness through the review-evidence composition pinned in Assumptions, whose evaluation is the single digest authority (it refuses unless the latest ready round's recorded digest equals the recomputed plan-bytes digest), with the evidence-coherence re-verification that bullet pins; parse replacement paths only from the structured `Files:` declaration, refusing an absent declaration or an empty replacement path set by name. [class: IMPLEMENTATION_REQUIRED]
- [x] Perform exactly the write inventory above in the same locked manifest write, persisted through the landed validate-before-persist helper (worker-schema validation before the save, mirroring both landed recovery precedents; a validation failure refuses byte-identically); at the driver boundary refusals return without persisting and the single locked save is the only write; prove every refusal, including an empty reviews directory surfaced as a named refusal rather than a traceback, leaves the manifest byte-identical and appends no receipt. [class: IMPLEMENTATION_REQUIRED]
- [x] Refuse stale or foreign identity (wrong task id, never-issued token, or a token matching only an older recorded receipt's prior identity after supersession), a claim with no prepared handoff intent, changed or missing review evidence including no matching round artifact and a not-ready latest round, a fence-shape mismatch (the recomputation passes or fails with any other shape), an absent declaration or an empty replacement path set, canonicalization-failing or duplicate-alias declaration entries, a declaration entry that fails the `Files:` entry grammar or path-looking prose outside the structured declaration, launched work, active workers, reservations, live claim-group ownership, mismatched replay, and a plan file that does not bind by full-stem identity to the manifest's recorded plan slug. [class: IMPLEMENTATION_REQUIRED]
- [x] Add one focused witness per refusal arm and per inventory surface, with the review-evidence fixtures built as real producer shapes (adapting the readiness test suite's cap-closure fixture recipe: round filename per the discovery shape, version-1 plan-kind sidecar with coverage, verdict, and the digest bound to the fixture plan bytes) and the composition imports driven for real (the never-patched rule scopes to those imports), with the fixture facts file seeded to the production key values and the fixture plan placed under that plans dir: valid refresh (the reviewed declaration changes the task's path set) asserting the validating entry point passes over the post-recovery manifest and a post-recovery launch driven through the emitted outcome action reaches a consumed worker-start binding; idempotent replay asserting the replay marker; replay mismatch naming the recorded receipt; superseded-replay falling to the stale-identity refusal naming the older receipt; state-superseded replay (after an intervening reclaim or launch) refusing as stale identity; second correction on the live identity appending a second receipt; changed review evidence; a not-ready latest round (sidecar verdict no with the source digest matching the plan bytes) refusing as changed review evidence; missing round artifact (built by emptying the fixture reviews directory, covering the empty-directory arm); recomputation failing with a non-drift shape (a malformed declaration entry reporting the scope-declaration-parse-problem shape, or a non-drift readiness failure) refused as fence-shape mismatch; recomputation passing because the declaration matches the seeded scope (the genuine out-of-scope declaration arm); a declaration stripped of its `Files:` list and a declaration present-but-empty each refusing by name; duplicate-alias entries; canonicalization-failing entry; stale and foreign identity; a direct claimed claim with no prepared handoff intent refused as not intent-backed; launch record present; active worker; held reservation; claim-group member; unstructured prose; a plan file that fails full-stem identity; a post-transition validation failure built as a helper-level inventory-surface witness mirroring the suite's existing post-validation-failure test (the real validator wrapped to pass pre-transition state and raise only once the recovery receipt event is present) and refusing byte-identically; a dated-filename plan whose manifest slug is seeded to the full stem exactly as a real run records it, asserting the recovery proceeds. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` and `python3 scripts/test_execute_plan_runtime_codex.py` [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: add receipt-fenced reviewed scope recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Expose and document the recovery operation

Files:
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/test_execute_plan_runtime.py`

- [x] Add CLI dispatch (constructing the driver persist-construction-free with the resolved adapter threaded in, mirroring the sibling recovery dispatches, so refusals are byte-identical across the whole CLI invocation; the CLI refusal witnesses assert manifest byte identity across the whole invocation) and document the exact eligibility checks, receipt, replay-first behavior, refusal semantics, and required ordinary preflight/launch sequence; add the scope-recovery transition to the runtime contract's transition table (required evidence, claim handling, resulting state, recovery action), mirroring the done-pending-recovery row; state that this one operation supersedes the runtime's never-reads-review-sidecars posture in the contract, the skill, and the runtime file's own readiness docstring posture sentence (listing the recovery alongside the terminal gate's clean-round sidecar read as the documented exceptions); state that claim-group member scope changes are refused here and the member exits through the group path (the driver `continue` operation with `--batch`), or through the blocked-member reclaim exit only when the member is blocked with `resume_allowed` false; state the widening-only drift bound, so a reviewed narrowing is documented as out of scope for this operation. [class: IMPLEMENTATION_REQUIRED]
- [x] Add CLI witnesses in `scripts/test_execute_plan_runtime.py` via its existing in-process CLI harness for successful recovery and representative refusal cases, including that inventory or review evidence cannot be supplied by the caller. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` and `python3 scripts/test_execute_plan_runtime_codex.py` [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: expose and document reviewed scope recovery` [class: IMPLEMENTATION_REQUIRED]

## Evaluation Criteria

- A legitimate reviewed prelaunch scope correction recovers without waiting for lease expiry or editing runtime state directly.
- Any refusal preserves exact manifest bytes and does not append a recovery receipt.
- The refreshed claim passes ordinary preflight and launches with only the rotated claim token.
- Completed-task evidence and unrelated state remain intact.

## Done when

- Focused runtime and CLI suites pass.
- Valid refresh, replay, refusal, preflight, and launch behavior have repository tests.

## Ship when

- None. This driver transition requires no external deployment or operator-owned prerequisite.

## Review Scope

Explicit must-fix:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

Regression surfaces:
- `scripts/test_execute_plan_runtime_codex.py`
- existing reclaim and preflight tests in `scripts/test_execute_plan_runtime.py`

## Validation Commands

- `python3 scripts/test_execute_plan_runtime.py`
- `python3 scripts/test_execute_plan_runtime_codex.py`
- `python3 scripts/execute_plan_runtime.py --selftest`
- `python3 scripts/plan_readiness.py docs/history/plans/2026-09-29-execute-plan-reviewed-scope-recovery.md`

## Residual findings (cap closure)

The configured round cap is r13 and the loop closes through the cap-closure terminal shape. Each staged r13 finding and its disposition:

- F1 architecture#unwitnessed-refusal-arm: folded (the Assumptions shape sentence is corrected and the intent-backed eligibility predicate, the not-intent-backed refusal arm, and its witness are in Task 1).
- F2 security#empty-declaration-drift-fence-admits-empty-scope: folded (the fence predicate excludes the missing-declaration and parse shapes and the absent-declaration and empty-set refusal arm and witnesses are in Task 1).
- F3 quality#plan-internal-vocabulary-collision: folded (the replay liveness predicate is state-shaped over the prepared-successor form).
- F4 testing#needle-unreachable-from-prescribed-text: folded (the never-patched rule is scoped to the composition imports and the helper-level witness technique is named).
- F5 testing#missing-gate-needle: folded (the scan is removed by the direct plan-file resolution).
- F6 testing#missing-gate-needle: folded (the arm names the concrete grammar and prose producers).
- F7 testing#missing-gate-needle: folded (the not-ready-verdict witness is added).
- F8 simplification#yagni-uniqueness-scan: folded (direct plan-file resolution replaces the scan and states the file origin once).
- F9 simplification#yagni-eager-import: folded (function-local composition imports are pinned in Assumptions).
- F10 consistency#closed-mutation-set-enumeration-drift: folded (the Outcome enumeration names the manifest generation bump).
- F11 security#evidence-identity-rederivation-toctou: folded (the single-read plus re-verification coherence rule is pinned in Assumptions).
