# Plan: execution claim write enforcement

Backlog origin: docs/history/backlog/2026-10-07-execution-claim-write-enforcement.md
Driving force: efficiency + automation
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-execution-claim-write-enforcement-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3h total, largest task 1h

## Terms

- execution claim: `docs/tmp/execution-claims/<artifact-slug>.md` in the primary checkout; four frontmatter lines (session, plan, created, updated) plus the base line after the run worktree exists; the occupancy single source of truth (SOT) the G1e discovery arm, the noclobber start refusal, the freshness decay, and the stale takeover all read.
- take: the atomic unit this plan introduces: claim create-or-refuse immediately followed by run-worktree creation; a failed take leaves no half-created state.
- claim (mode): the claim-only arm of the script for the authorized primary-placement lane: create-or-refuse with no worktree creation.
- gateway: the per-execution worktree creation step; the one mandatory passage point of every plan-work start, dispatched child or in-session.
- fresh foreign claim: a claim naming another session whose `updated:` is fresher than one cadence period (2 hours); refuses the take.
- stale takeover: re-reading a stale foreign claim immediately before unlinking it (only while it still names the same foreign session with a stale `updated:`), recording the takeover, then creating this session's claim; when the dead session's worktree still occupies the branch, the take refuses with the occupying worktree named instead.
- delete arm: the existing duty that a failed create deletes this session's own claim file and the session stands down writing nothing.
- primary checkout: the first `worktree` entry of `git worktree list --porcelain`; the claims directories always resolve there.
- canonical artifact slug: the feature slug lowercased, derived by `artifact_slug` in `scripts/plan_readiness.py` (the single derivation landed by 80ad2666).
- OUTCOME contract: the repo's four-outcome vocabulary (`scripts/OUTCOME_CONTRACT.md`): exit 0 with a final `OUTCOME: pass` line, 1 fail, 2 indeterminate, 3 tool_error; a run with no final line is tool error.
- liveness ledger: `scripts/gate_liveness_ledger.json` plus `scripts/gate_liveness_ledger.py` with its `show` subcommand; counts catches, incidents, overrides, and time lost per guard.
- user-directed override: the interactive-session override rule in `agents/skills/maintenance/SKILL.md` (proceed with the tripped gate named in the decision reason; integrity guards stay non-overridable).
- pins suite: `scripts/check_maintenance_pins.sh`; the mechanical structural gate whose recognition spans the blueprint and shared skill edits re-key.
- fix-class: the backlog `Class:` taxonomy value marking a row that fixes a defect in existing machinery; its refusal-path additions carry an origin-cited no-exit justification under the Gate delta rule.
- carrier: a fired maintenance session (scheduler or one-shot) that surveys, decides, and dispatches or executes lane work.
- prove-first: the landed ledger doctrine (commit 538f1f08): no new guard is designed or planned before its harm class shows recorded cases and time lost in the liveness ledger.
- check-claim-fence: the landed deletion fence (commit 18c65b33) refusing plan-file deletion while a live claim names it; a reader of the claim registry this plan leaves untouched.

## Why

The execution claim is the occupancy SOT, but writing it is a prose duty: nothing mechanical requires a session that starts plan work to hold one. On 2026-10-07 a carrier took the head plan claim-less (its own Phase 0 todo listed the write), the next carrier's survey legitimately read the empty registry as free, and both executions ran concurrently until the peer landed; about 130 lane-minutes and four commits were discarded. The complement the mechanism always lacked is mechanical enforcement at the one gateway every start passes.

## Outcome

A plan-work start cannot create its run worktree without owning a live execution claim.

- A duplicate start is refused at the gateway with the holder, the claim age, the occupying worktree when derivable, and the override path named, instead of being discovered hours into a run.
- Refusals self-heal through the existing freshness decay and stale takeover, and a dead session's leftover worktree is named by the refusal so the next session adopts or removes it deliberately; an interactive operator override always exists, riding the user-directed-override framework.
- The liveness ledger counts the gateway's catches, incidents, and overrides, so the gate can be re-priced, re-shaped, or retired on data.

Gate delta: adds one mechanical refusal class at the worktree gateway (the take refusing a fresh foreign claim before worktree creation) plus one liveness-ledger guard row and the ledger's override kind; the refusal-path addition is a fix-class origin's no-exit case: the origin row's Evidence rejects the prose-duty and reader-side-checker class-defaults, the log entry's rejected alternatives (cited as design input, never as origin) rejects the landing-side-backstop-alone default, and all three rejections stand on the witnessed 2026-10-07 duplicate execution (about 130 lane-minutes, landing 80ad2666); the ledger's authoring-time catch-to-incident ratio is 12:14 (`python3 scripts/gate_liveness_ledger.py show`, 2026-10-07); removes the prose claim-create duty (the EXECUTION CLAIM paragraph's create sentence and the claim-registration paragraph's hand-write duty), replaced by the pinned script call; the fresh-foreign refusal, freshness decay, and stale takeover semantics are kept, not added.

## Assumptions

- assume the script joins the shell helper family (like `scripts/done-lock.sh`), bash, zero dependencies, answering in the OUTCOME contract; basis: repo precedent for the lock/claim script family.
- assume execution-side-only scope this cycle; the authoring lane joins only when its own ledger rows record the harm class; basis: the operator's constraint, the log entry's rejected alternative, and the prove-first ledger doctrine.
- assume the choke point lives in the canonical execute-plan worktree step with one blueprint mirror reference, not duplicated prose; basis: the worktree-first standard consolidation made execute-plan the lifecycle owner.
- assume the claim filename derives through the python SOT (`artifact_slug`) exposed by a new read-only CLI flag, never reimplemented in bash; basis: the single-derivation rule landed by 80ad2666.
- assume the claim file schema (frontmatter lines and their order) is unchanged; every reader (G1e discovery arm, freshness rule, check-claim-fence) parses the current shape.
- Decision receipts: the operator set the four binding constraints (one SOT step only, self-healing refusals, an always-present operator override, ledger metrics) in the filing ask of 2026-10-07; the Step 1.4 requirements block was presented the same day and the operator deferred authoring without adjustments, then directed the in-session resume.

Decision points requiring a grill: none remain.

## Standing constraints

- Skill-file insertions stay tool-agnostic (no agent names, no tool names) and are swept against the shared-body forbidden-term gate before certification.
- Every pinned recognition span an edit retires is re-keyed in the same task that breaks it; the pins suite stays green at every task boundary.
- No em-dashes in added lines anywhere.

## Gist & Examples

TLDR: one atomic take script makes the execution claim a mechanical prerequisite of the run worktree, so a duplicate execution start is refused at the gateway; driving force: efficiency + automation.

Today the claim write is prose, not machinery: the EXECUTION CLAIM paragraph prescribes a hand-written create-if-absent file, and the worktree creation is a separate prose command. A session under pressure skips the write, and every guard that reads the registry then sees an empty lane. After this plan, the pinned invocation `bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]` is the only way to obtain the run worktree: it derives the canonical slug through the python SOT, creates the claim create-if-absent noclobber (refusing a fresh foreign claim with the holder, age, occupying worktree when derivable, and override named; taking over a stale one with the re-read-before-unlink discipline, and refusing with the occupying worktree path and the adopt-or-remove remedies named when the dead session's worktree still holds the branch), then creates the worktree; any failure after a claim created in this invocation deletes that claim again, so the take is atomic. The `claim` mode is the same create-or-refuse arm without the worktree, for the authorized primary-placement lane. `refresh` re-stamps `updated:` (recreating after a takeover, writing the base line when passed, fencing on a claim naming a foreign session); `release` deletes the claim only while it names this session, and a missing claim is a loud failure.

Examples: a second carrier taking a plan held by a five-minute-old foreign claim exits 1 with `OUTCOME: fail`, a refusal naming the holder session, the age, the occupying worktree, and the override route, and creates no worktree; a dead session's three-hour-old claim is taken over with the takeover recorded, but if that session's worktree still occupies the branch the take refuses naming the worktree path and both remedies (adopt it per the recognition arm, or remove it deliberately); an interactive operator-directed proceed rides the user-directed-override rule, and the ledger's override count for the gateway rises so the false-refusal cost is visible at the next census.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the script's selftest covers the cold-start happy path, the fresh-foreign refusal, the stale takeover, the takeover-with-occupied-worktree refusal, own-claim refresh, the failed-create cleanup, the release ownership fence, the refresh foreign fence, the claim-only mode, the slug-through-SOT integration, and the missing-primary-checkout tool error; every suite it touches stays green.
- refusal-contract quality: tests assert the refusal message names the holder session, the claim age, the occupying worktree when derivable, and the override route.
- integration integrity: the pins suite is green after each re-key; `gate_liveness_ledger.py show` renders the new row with its catches, incidents, and overrides; the shared-body gate and the em-dash and hygiene scans stay green.

**Done when:**
- `scripts/execution_claim.sh` and its selftest exist and pass; `plan_readiness.py` answers `--print-artifact-slug`; the script's born-conformant register row exists in `scripts/OUTCOME_CONTRACT.md`.
- The execute-plan worktree step and the blueprint's per-execution worktree paragraph carry the single pinned take call; retired pin spans are re-keyed.
- The ledger row exists and `show` renders it with the override kind; the runtime manifest lists the script and a pins-suite membership check guards it.

**Ship when:**
- After a census window of nightly lanes running under the take, the operator reviews the row's catches/incidents/overrides counts and decides keep, re-shape, or retire (the prove-first correction loop); runtime home copies refreshed per the established landing convention.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execution_claim.sh` *(new)*
- `scripts/plan_readiness.py` (the read-only slug flag only)
- `scripts/gate_liveness_ledger.py` (the override kind and its show rendering only)
- `agents/skills/execute-plan/SKILL.md` (the worktree step and the claim-registration paragraph)
- `agents/skills/maintenance/prompt-templates.md` (the EXECUTION CLAIM paragraph, the per-execution worktree paragraph, the deviations list)
- `agents/skills/maintenance/SKILL.md` (the user-directed-override enumeration)
- `scripts/gate_liveness_ledger.json`
- `scripts/OUTCOME_CONTRACT.md` (the born-conformant register row)
- `scripts/runtime-scripts.list`
- `scripts/check_maintenance_pins.sh` (re-keyed spans and the manifest-membership pin only)

**Tests:**
- `scripts/test_execution_claim.py` *(new)*
- `scripts/test_plan_readiness.py` (the slug-flag fixture)
- `scripts/test_gate_liveness_ledger.py` or the ledger's owning test file where one exists (the override-kind fixture)
- `scripts/test_docs_branch_plan_guard.py` and `scripts/test_execute_plan_runtime.py` only where a pin or fixture references a span this plan retires

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/plans/SKILL.md` and the authoring-claim flow; reason: the authoring lane is deliberately deferred (prove-first) and its claim duty is untouched.
- Any survey-side occupancy checker or G1e arm semantics change; reason: readers stay unchanged by operator constraint.

## Validation Commands

Validation preamble: this plan declares no frozen regions and no regression-guard pins against target files' current bytes; every pin the audit checks lives in a prescribed snippet. The rule 29 pre-round invocation ran `OUTCOME: pass` on 2026-10-07 before round 1 and is re-run after every fold; the rule 22 mechanical audit (spans exactly-once in the prescribed snippets, `bash -n` over this block) runs at authoring time and after every fold.

```bash
set -e
cd "$(git rev-parse --show-toplevel)"
bash -n scripts/execution_claim.sh
python3 scripts/test_execution_claim.py
python3 scripts/test_plan_readiness.py
python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies
python3 scripts/test_gate_liveness_ledger.py
python3 scripts/test_sync_runtime_scripts.py
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/gate_liveness_ledger.py show
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-07-execution-claim-write-enforcement.md
```

Rule 19 evidence (authoring-time RED-today execution): the selftest file does not exist yet, so `python3 scripts/test_execution_claim.py` fails today with a file-not-found error (exit 2), and `grep -c 'execution_claim' scripts/check_maintenance_pins.sh` returns 0 today against the re-key and manifest-membership obligations; both recorded before round 1.

### Task 1: slug flag, take script, selftest, contract registration

Review tier: H

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`
- `scripts/execution_claim.sh` *(new)*
- `scripts/test_execution_claim.py` *(new)*
- `scripts/OUTCOME_CONTRACT.md`

Evidence:
- `python3 scripts/test_execution_claim.py`; covers the refusal, takeover, occupation, refresh, cleanup, release, claim-mode, slug, and tool-error criteria
- `python3 scripts/test_plan_readiness.py`; covers the slug-flag criterion

- [x] `TestPrintArtifactSlug#test_flag_prints_canonical_slug`; given a fixture plan `2026-09-01-STORY-KEY-Fixture-Story.md`, `python3 scripts/plan_readiness.py --print-artifact-slug <plan>` prints `STORY-KEY-fixture-story` and exits 0 [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_take_cold_start_creates_both`; given an empty claims directory, take exits 0 `OUTCOME: pass`, the claim names this session, and the worktree exists [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_take_fresh_foreign_refusal`; given a seeded foreign claim five minutes old whose session holds a worktree, take exits 1 with `OUTCOME: fail`, the message names the holder session, the age, that holder's worktree path, and the override route, and no worktree is created [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_take_stale_takeover`; given a seeded foreign claim three hours old with no worktree present, take exits 0 `OUTCOME: pass`, the output records the takeover with the foreign session id, the claim now names this session, and the worktree exists [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_take_stale_claim_with_occupied_worktree`; given a seeded foreign stale claim whose session also holds a worktree on the requested branch, take exits 1 `OUTCOME: fail`, the message names the occupying worktree path and both remedies (adopt per the recognition arm, or remove deliberately), and the fresh claim created by this invocation is cleaned up [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_take_own_claim_existing_worktree_fails_keeping_claim`; given our own live claim and an existing worktree directory, take exits 1 `OUTCOME: fail` naming the existing worktree and keeps the claim (the session adopts instead of recreating) [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_failed_create_cleans_fresh_claim`; given a branch-name collision that fails the worktree add after a claim created in this invocation, the claim is deleted, the output names the git error, exit 1 [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_release_ownership_fence`; given a foreign claim, release exits 1 and leaves the claim untouched; given our own claim, release deletes it and exits 0; given no claim file, release exits 1 `OUTCOME: fail` naming the missing claim [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_refresh_restamps_recreates_and_fences`; given our own claim, refresh re-stamps `updated:` and writes the base line when passed; given a claim deleted by a takeover, refresh recreates it; given a foreign-named claim, refresh exits 1 without modifying it [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_claim_mode_creates_without_worktree`; given an empty claims directory, the claim mode exits 0 with the claim created and no worktree directory; a fresh foreign claim refuses it identically to take [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_slug_derived_through_sot`; given a plan path with an uppercase feature segment, the claim filename equals the canonical artifact slug [class: REPOSITORY_TEST]
- [x] `TestExecutionClaim#test_missing_primary_checkout_tool_error`; given a scratch directory that is not a git repository, take exits 3 with `OUTCOME: tool_error` [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_execution_claim.py` fails (module absent) and the slug-flag test fails (no such flag) [class: REPOSITORY_TEST]
- [x] Write the `--print-artifact-slug` flag (read-only print of `artifact_slug`, argparse arm composing with the existing modes' mutual exclusion), the take/refresh/release/claim script per the Gist & Examples contract (freshness constant two hours, OUTCOME contract throughout, self-heal dispositions as canaried), and the born-conformant register row in `scripts/OUTCOME_CONTRACT.md` declaring the script's operating assumptions (primary checkout resolvable, claims directory writable, freshness clock, no indeterminate class today) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both suites pass; the pre-existing `test_plan_readiness.py` body stays green [class: REPOSITORY_TEST]
- [x] Commit: `feat: enforce the execution claim at the worktree gateway (atomic take script + slug SOT flag)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: wire the gateway, mirror the blueprint, re-key pins

Review tier: M

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the re-key criterion
- `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies`; covers the shared-body sweep constraint

- [x] Inventory every pins-suite span whose recognition text the edits below retire; re-key each onto the new pinned sentences in the same task [class: IMPLEMENTATION_REQUIRED]
- [x] The execute-plan worktree-first creation step invokes the take as the single create path for worktree-creation runs: the pinned line `bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]` replaces the prose claim-create duty sentence (the registration paragraph's hand-write duty) and the worktree-first creation step's separate creation prose, keeping branch conventions and the fail-closed stand-down wording; the authorized primary-placement lane (claim with no worktree) retargets to the claim mode; freshness, takeover, and refresh-cadence semantics stay prose-owned and unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] The maintenance blueprint's EXECUTION CLAIM paragraph and per-execution worktree paragraph reference the same script as the procedure of record (one mirror sentence each, no recipe restatement), and the deviations list registers the blueprint edit per the byte-parity protocol [class: IMPLEMENTATION_REQUIRED]
- [x] Shared-body sweep of every inserted sentence passes the runtime-neutrality gate [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: pins suite green after re-keying; shared-body gate green [class: REPOSITORY_TEST]
- [x] Commit: `feat: wire the execution-claim take as the pinned gateway call (skills + pins re-key)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: ledger row and override kind, override arm, deploy manifest

Review tier: M

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/gate_liveness_ledger.json`
- `scripts/gate_liveness_ledger.py` (override kind and show rendering)
- `scripts/test_gate_liveness_ledger.py` or the ledger's owning test file where one exists
- `agents/skills/maintenance/SKILL.md`
- `scripts/runtime-scripts.list`
- `scripts/check_maintenance_pins.sh` (the manifest-membership pin only)

Evidence:
- `python3 scripts/test_gate_liveness_ledger.py`; covers the override-kind canary criterion
- `python3 scripts/gate_liveness_ledger.py show`; covers the ledger-row and override-count criteria
- `bash scripts/check_maintenance_pins.sh`; covers the manifest-membership criterion (the reverse-squash-guard precedent pins the guard's manifest entry the same way)
- `python3 scripts/test_sync_runtime_scripts.py`; covers the manifest parity criterion

- [x] Add the `execution-claim-gateway` guard row: notes cite the origin row and the gateway mechanism; one incident row dated 2026-10-07 with `time_lost_minutes` 130 and evidence naming landing 80ad2666 and the origin row [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the ledger schema and script with the override kind (a per-guard counter beside catches and incidents; `show` renders it; the seeded row starts at zero) with a canary proving a recorded override increments the count and renders [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the user-directed-override rule's deferral-class enumeration with the take refusal (the interactive proceed and its decision-reason recording; integrity guards untouched) [class: IMPLEMENTATION_REQUIRED]
- [x] Add `execution_claim.sh` to the runtime manifest (one line) and pin its membership in the pins suite (a `grep -qFx` check on `scripts/runtime-scripts.list` beside the reverse-squash-guard precedent) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `test_gate_liveness_ledger.py` passes with the override-kind canary; `gate_liveness_ledger.py show` renders the new guard with the seeded incident and a zero override count; the pins suite includes the manifest-membership check; `test_sync_runtime_scripts.py` passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: book the execution-claim gateway in the liveness ledger with override counting, override arm, and manifest pin` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full validation and mechanical audits

Review tier: L

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files: none new; runs the `## Validation Commands` block over the tree this plan created.

Evidence:
- The full `## Validation Commands` block; covers every criterion in `## Evaluation Criteria`

- [x] Run the whole Validation Commands block → expect GREEN end to end [class: REPOSITORY_TEST]
- [x] Mechanical audit (authoring rule 22): extract every pinned span and verify it occurs exactly once in the prescribed snippet (this plan declares no target-bytes pins or frozen regions; the basis is the Validation preamble above); `bash -n` over the Validation block [class: REPOSITORY_TEST]
- [x] Commit: `test: full validation green for the execution-claim gateway plan` [class: IMPLEMENTATION_REQUIRED]
