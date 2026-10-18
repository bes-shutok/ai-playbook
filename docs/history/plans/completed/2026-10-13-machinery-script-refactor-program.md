# Plan: machinery script refactor program, first cycle

Authoring claim: docs/tmp/authoring-claims/machinery-script-refactor-program.md (session zcode-auth-automation-fd67f4d3-2314)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-13-machinery-script-refactor-census.md
- docs/history/backlog/2026-09-19-plan-readiness-parser-dedup.md
- docs/history/backlog/2026-10-07-claim-race-retry-duplication.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/*-plan-review-machinery-script-refactor-program-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution dependency: Tasks 2 through 4 execute only after docs/history/plans/2026-10-13-red-on-main-baseline-repair-and-auto-demote.md is executed on the exec lane and the pins suite reads green on main (the census row's gate); until then the suite is red at the reviewed base (21 documented failures) and those tasks park
Execution budget: 3.5h total, largest task 1.5h

## Terms

- Census document: the inventory and hot-spot document Task 1 produces at docs/maintenance/machinery-script-census.md; no behavior change.
- Hot spot: a script whose size, churn, or duplication makes it the next decomposition target.
- Dedup first item: single-homing one witnessed duplicated logic pair (Tasks 2 and 3).
- Module move: extracting one cohesive region of a script into a new module file the script imports, behavior byte-preserved (Task 4).
- Pins reconciliation: re-aiming scripts/check_maintenance_pins.sh rows whose matched literals moved, beside the provenance of the move, so the suite stays green.
- Focused suite: the owning script's own selftest or regression family covering the touched region, execution-selected.
- Red baseline: a main state where scripts/check_maintenance_pins.sh exits nonzero, the RED-on-main condition whose repair the landed plan docs/history/plans/2026-10-13-red-on-main-baseline-repair-and-auto-demote.md owns.
- Green baseline: the pins suite exiting 0 on the branch base; the precondition for every behavior-changing task here.
- Ledger-recorded true catch: a scripts/gate_liveness_ledger.json row recording a gate's real catch; its behavior is byte-preserved by this plan.
- Outcome contract: scripts/OUTCOME_CONTRACT.md, the four-outcome exit vocabulary the gates speak.
- Pins suite: the scripts/check_maintenance_pins.sh regression suite; its exit 0 is the green baseline.
- Deployed twin: the runtime copy of a script under the deployed skills home, deployed as manifest-driven per-file symlinks into the canonical repo scripts/ (scripts/sync_runtime_scripts.sh); a new module file becomes importable through the deployed path because Python resolves the symlink's sys.path[0] to the canonical scripts/ directory, which is the property the no-bespoke-deployment claim rests on.

## Why

The machinery's scripts grew ad-hoc into god scripts (an 18k-line validator, an 8k-line readiness gate, a 7.6k-line sweep library in weeks), and duplication is already witnessed inside two of them. This plan starts the census-first, incremental refactor program so later cycles move on measured data instead of per-incident churn.

## Gist & Examples

TLDR: starts the machinery-script refactor program (census document, two witnessed dedups, first decomposition move of the review-staging validator), so later refactors run on measured hot spots instead of ad-hoc churn; declared force code-quality, motivated by reliability (hot-spot churn compounds review surface and drift risk).

Before: scripts/validate_review_staging.py holds 18,110 lines; the race-retry discipline is duplicated between two loops in scripts/execution_claim.sh; the section and Files parser pair is duplicated inside scripts/plan_readiness.py; no census document exists, so decomposition targets are picked by anecdote.
After: the census document records per-script size, churn, duplication clusters, and outcome-contract adoption; the two witnessed duplications are single-homed; validate_review_staging.py carries its first extracted module with the pins suite and the focused suites green.
Edge cases: a red pins baseline holds the behavior-changing tasks while the read-only census document still proceeds; a pins row whose literal moves is re-aimed beside provenance in the same change; the deployed twin stays in sync through the manifest-driven per-file symlinks, never a hand copy.

## Outcome

One plan that starts the machinery-script refactor program on measured data.
- The census document exists and names the next decomposition targets with per-script size, churn, duplication, and consistency data.
- The plan_readiness.py section and Files parser pair is single-homed behind one wrapper, so the review-scope and ownership inventories cannot drift apart.
- The execution_claim.sh race-retry discipline exists once, shared by both callers.
- validate_review_staging.py carries its first extracted module with the pins suite and the focused suites green.

Gate delta: none.

## Assumptions

- assume the first program cycle is exactly the census document, the two dedup first items, and one validate_review_staging.py module move; basis: the dispatch entry's ordering and the census row's fix shape steps 1 through 3.
- assume the behavior-changing tasks (Tasks 2 through 4) execute only over a green baseline; basis: the census row's gate ("refactoring guard scripts over a red baseline repeats the audit's Part 4.6 violation"); measured at authoring, the pins suite exits 1 with the 21 documented baseline failures and the repair plan's landing 9073e5001 is docs-only, so the sequencing dependency is that plan's EXECUTION on the exec lane, and the operative bar is the suite reading green, not the repair plan file's presence; until then Tasks 3 and 4's pins verifications are dormant behind the suite's fail-fast checkpoint, not green.
- assume no new gate, budget, ledger, or validator is proposed by this plan; basis: the entry's scope arms and the repository Machinery admission protocol; the script-versus-skill-text governance asymmetry is recorded in the census document as an operator finding, never auto-landed.
- assume the first module move targets the finding-record calibration vocabulary region of scripts/validate_review_staging.py (the VALID_BLAST_RADIUS, VALID_REACHABILITY, and VALID_CONFIDENCE constants and the finding calibration checks inside validate_current_payload); basis: a verified cohesive region whose three consumer sites are inventoried (the checks in validate_current_payload, the in-file selftest vocabulary arms, and the external qualified reads vrs.VALID_* in scripts/test_review_record_selection.py that pin the move's re-export shape); Task 1's coupling data finalizes the exact boundary at execution.
- assume exact focused-suite invocations, fixture paths, and selftest entry points are execution-selected from repository evidence; basis: the no-guessed-inventory rule; the plan names only the owning scripts and the regression families the origin rows cite.
- assume the script-runtime telemetry entry stays a separate plan; the census document uses spot measurements and records the telemetry dependency; basis: the entry's orientation line naming the telemetry plan this program's measurement input.
- assume a new module file needs no deployment step: the deployed entry script's symlink resolves sys.path[0] to the canonical scripts/ directory, so the module is importable through the deployed path with no sync or manifest change (a manifest entry would be wrong for a library module); basis: the Terms' Deployed twin definition and scripts/sync_runtime_scripts.sh (manifest-driven per-file symlinks).

Decision points requiring a grill: execution-gate bar read as pins-suite green rather than repair-plan landing: resolved by the census row's own rationale text, 2026-10-13, affected sections: Standing constraints and Tasks 2 through 4; first decomposition region choice: resolved by the entry's explicit ordering plus verified region evidence, 2026-10-13, affected section: Task 4.

## Standing constraints

- Behavior byte-preservation: every ledger-recorded true catch's observable behavior (error text, exit class, refusal shape) is byte-preserved; this plan relocates and single-homes, it never retunes a guard.
- Green-baseline gate: Tasks 2, 3, and 4 start only when the pins suite exits 0. The execution branch is first rebased (or re-cut) onto post-repair main so the base commit and main coincide, and the measurement runs in a scratch checkout of that base (a throwaway worktree created detached at the base sha and pruned after the measurement), never on the working branch and never through the deployed twin; on a red baseline the tasks park-for-operator with the failure output recorded in the round's review-staging record, and only the census document (Task 1) proceeds; on any gate outcome the scratch worktree is reconciled before the next task starts (git worktree list, then git worktree remove for any detached scratch checkout matching this gate's pattern, followed by git worktree prune for stale entries).
- Pins beside provenance: each task that moves or reshapes code the pins suite matches verifies the suite stays green and re-aims any row whose literal moved, in the same change.
- No new machinery: this plan adds no gate, budget, ledger, hook, or required ceremony; removal-shaped work only.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pins suite, the touched scripts' focused suites, and the hygiene scan all exit 0 after every task.
- behavior preservation: the deduped loops and the moved calibration checks produce byte-identical outputs on their existing suites.
- maintainability: each dedup leaves exactly one owner of the shared logic; the decomposition leaves one cohesive imported module with no import cycle.
- measurability: the census document answers "what moves next and why" from recorded data, not anecdote.

**Done when:**
- docs/maintenance/machinery-script-census.md exists with per-script size, churn, duplication-cluster, and outcome-contract sections.
- scripts/plan_readiness.py's review-scope Files inventory and the ownership check read the same parsed pair.
- scripts/execution_claim.sh holds one race-retry implementation serving both callers.
- scripts/review_staging_calibration.py exists, is imported by scripts/validate_review_staging.py, and the full pins suite exits 0.

**Ship when:**
- the deployed twin resolves scripts/review_staging_calibration.py once the branch lands [class: OPERATIONS_FOLLOW_UP]; evidence owner: the execution run's landing verification; closure: a validator invocation through the deployed path imports the module (the twin symlink points at the canonical checkout, which carries the module only after landing).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`
- `scripts/execution_claim.sh`
- `scripts/validate_review_staging.py`
- `scripts/review_staging_calibration.py` *(new)*
- `scripts/check_maintenance_pins.sh` (pins re-aims only)

**Tests:**
- `scripts/test_execution_claim.py` (Task 3 adds its witnesses here)
- `scripts/test_review_record_selection.py` (run-only regression net for Task 4's vocabulary arms)

**Documentation:**
- `docs/maintenance/machinery-script-census.md` *(new)*
- `docs/maintenance/document-registry.md` (registry tidy)

**Backlog rows (dispositions):**
- `docs/history/backlog/2026-09-19-plan-readiness-parser-dedup.md` *(deleted)*
- `docs/history/backlog/2026-10-07-claim-race-retry-duplication.md` *(deleted)*
- `docs/history/backlog/2026-10-13-machinery-script-refactor-census.md` (Cluster pointers tidy)
- `docs/history/backlog/2026-10-06-claim-fence-test-coverage-gaps.md` (Cluster tidy)
- `docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md` (Cluster tidy)
- `docs/history/backlog/2026-10-07-execution-claim-ownership-toctou-serialization.md` (Cluster tidy)
- `docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md` (Cluster tidy)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, or reconciles a pins row or twin-sync contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/summarize_review_stats.py`, `scripts/done_sweep_gates_lib.py` and its test; reason: later program cycles own their decomposition; this plan's decomposition surface is validate_review_staging.py only.
- any byte-budget or wall-time gate over scripts; reason: the Machinery admission protocol requires its own witnessed incident and plan.
- the script-runtime telemetry writer; reason: its own entry owns it (the PLAN-PROMPTS entry script-runtime-cost-telemetry).

## Validation Commands

Validation preamble (rule 29 record): the pre-round structural gate ran OUTCOME: pass with one sanctioned warning (declared total 3.5h exceeds the 3.0h cap) before round 1 on 2026-10-13; the authoring-time em-dash fixer pass and the public-hygiene scan (exit 0) are recorded at authoring; this plan pins no literal spans or counts, so no rule-22 audit set applies; rule 19 RED-today record: the pins suite is the first actually-failing validation gate at authoring (exit 1, the 21 documented baseline failures; see Execution dependency), the hygiene scan passes, and there are no vacuous passes.

```bash
( cd "$(git rev-parse --show-toplevel)" && bash scripts/check_maintenance_pins.sh )
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

Full selftests per touched script (no per-family selectors exist) are execution-selected from repository evidence and must pass before each task's commit; the execution claim test suite carries Task 3's witnesses, and scripts/test_review_record_selection.py is the run-only regression net for Task 4's vocabulary-equality arms.

### Task 1: census and hot-spot inventory document

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/maintenance/machinery-script-census.md` *(new)*

- [x] Census document records a mechanical table over every script under scripts/ (python and shell) with line counts, function counts, and outcome-contract adoption (explicit exempt-class decisions for probe-shaped scripts) [class: IMPLEMENTATION_REQUIRED]
- [x] Census document adds 30- and 90-day commit churn from git log plus duplication-cluster depth for the top offenders the table surfaces; the clusters are the two witnessed in the origin rows plus any spot measurement named as such (no script-corpus duplication tooling exists; scripts/skill_text_duplication.py is Markdown-scoped) [class: IMPLEMENTATION_REQUIRED]
- [x] Census document names the next decomposition targets in priority order with the measured basis for each, and records the consumer-site coupling data for the plan's own module move (the three consumer sites: the calibration checks in validate_current_payload, the in-file selftest vocabulary arms, and the external vrs.VALID_* reads in scripts/test_review_record_selection.py) [class: IMPLEMENTATION_REQUIRED]
- [x] Census document records the twin-sync contract (the manifest-driven symlink deployment and the Python sys.path[0] symlink-resolution property it rests on, with the interpreter floor for cross-symlink imports) and the spot-measurement method used where live telemetry is absent, with the dependency on the script-runtime telemetry plan [class: IMPLEMENTATION_REQUIRED]
- [x] Census document records the script-versus-skill-text governance asymmetry as an operator finding without proposing a gate [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the hygiene scan exit 0 over the new document [class: REPOSITORY_TEST]
- [x] Commit: `docs: machinery script census and hot-spot inventory` [class: IMPLEMENTATION_REQUIRED]

### Task 2: single-home the plan_readiness parser pair

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`
- `docs/history/backlog/2026-09-19-plan-readiness-parser-dedup.md` *(deleted)*
- `docs/history/backlog/2026-10-13-machinery-script-refactor-census.md` (Cluster tidy)
- `docs/maintenance/document-registry.md` (registry tidy)

Primary class anchors:
- `_review_scope_task_files` in `scripts/plan_readiness.py`

- [x] Capture the baseline: run the script's full --selftest (no per-family selector exists) and confirm the review_scope and plan_ownership family lines report PASS before the change [class: REPOSITORY_TEST]
- [x] `_review_scope_task_files` becomes a wrapper over `_plan_task_sections` plus `_plan_files_items` per the origin row's fix shape, so review-scope clause (c) and the ownership check inventory the same Files lists through one parser implementation; `_plan_path_shaped` and the shared token normalization stay as they are [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the review_scope and plan_ownership families green with unchanged outputs, and run the pins suite expecting exit 0 (authoring check: zero rows reference plan_readiness literals, so no re-aim is expected; the run, not the note, is the check) [class: REPOSITORY_TEST]
- [x] Delete the completed origin row docs/history/backlog/2026-09-19-plan-readiness-parser-dedup.md with a witness naming the covering commit, tidy the census row's Cluster pointer at it, and mark or remove the row's document-registry entry in docs/maintenance/document-registry.md per that registry's disposition convention, in the same change [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `refactor: single-home plan_readiness section and Files parsers` [class: IMPLEMENTATION_REQUIRED]

### Task 3: extract the shared claim race-retry helper

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execution_claim.sh`
- `scripts/test_execution_claim.py`
- `scripts/check_maintenance_pins.sh` (pins re-aims only)
- `docs/history/backlog/2026-10-07-claim-race-retry-duplication.md` *(deleted)*
- `docs/history/backlog/2026-10-13-machinery-script-refactor-census.md` (Cluster tidy)
- `docs/history/backlog/2026-10-06-claim-fence-test-coverage-gaps.md` (Cluster tidy)
- `docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md` (Cluster tidy)
- `docs/history/backlog/2026-10-07-execution-claim-ownership-toctou-serialization.md` (Cluster tidy)
- `docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md` (Cluster tidy)

Primary class anchors:
- `acquire_claim` in `scripts/execution_claim.sh`
- `cmd_refresh` in `scripts/execution_claim.sh`

- [x] Capture the baseline: the execution claim test suite passes before the change, with the exact test invocations execution-selected [class: REPOSITORY_TEST]
- [x] One shared retry helper owns the increment-plus-ceiling check and the byte-identical `claims directory kept racing` tool error, with each caller keeping the zero initialization of its own attempt counter; each loop keeps its full body and all state mutations (including every continue site and the state flags the cleanup and exit trap consume) in its caller and invokes the helper once per iteration [class: IMPLEMENTATION_REQUIRED]
- [x] Terminal refusal paths (fresh-foreign die_fail, occupant gate, refresh foreign-session refusal) keep their own refusal exits and are never routed through the retry ceiling [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a permanently contended claims directory (built by placing a dangling symlink at the claim path, which the noclobber create refuses deterministically and root-proofly; a PATH shim cannot fail the builtin create and a chmod does not fail for root), both callers still fail on the third attempt with the same error text and nonzero exit as before the extraction, pinned by a new witness test in scripts/test_execution_claim.py [class: REPOSITORY_TEST]
- [x] Safety witness: given a contender that releases after the first create loss, both callers succeed on attempt 2 with the state flags exactly as a cold start sets them, pinned beside the contended witness [class: REPOSITORY_TEST]
- [x] The lost-then-won stub is a date shim whose first invocation plants a dangling symlink at the claim path and exits nonzero, so the noclobber create refuses once (the failed stamp is absorbed in the create's condition context), and whose later invocations remove the planted link and delegate; never a timed contender file [class: REPOSITORY_TEST]
- [x] Run → expect the claim test suite green (including both new witnesses) and the pins suite exit 0 in the same change, re-aiming any of the execution_claim rows whose matched literal moved (authoring check: the four rows grep other files; expected re-aims zero) [class: REPOSITORY_TEST]
- [x] Delete the completed origin row docs/history/backlog/2026-10-07-claim-race-retry-duplication.md with a witness naming the covering commit, and tidy the census row's Cluster pointer at it in the same change; the census row itself stays open [class: IMPLEMENTATION_REQUIRED]
- [x] Tidy the Cluster lines listing the deleted claim-race row in the four claim-fence backlog rows named in this task's Files list, in the same change [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `refactor: extract shared execution claim race-retry helper` [class: IMPLEMENTATION_REQUIRED]

### Task 4: first validate_review_staging module move

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/validate_review_staging.py`
- `scripts/review_staging_calibration.py` *(new)*
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `validate_current_payload` in `scripts/validate_review_staging.py`
- `VALID_REACHABILITY` in `scripts/validate_review_staging.py`

- [x] Capture the baseline: the validator's full --selftest, including the in-module calibration vocabulary arms, and the vocabulary-equality arms in scripts/test_review_record_selection.py, which read the constants as validator module attributes, pass before the change [class: REPOSITORY_TEST]
- [x] The finding-record calibration vocabulary (the VALID_BLAST_RADIUS, VALID_REACHABILITY, and VALID_CONFIDENCE constants and the finding calibration checks inside validate_current_payload) moves into scripts/review_staging_calibration.py; the exact boundary is finalized from the census document's recorded coupling data and stays import-cycle-free [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/validate_review_staging.py from-imports the three constants so they stay resolvable as validator module attributes, because scripts/test_review_record_selection.py reads vrs.VALID_* in its vocabulary-equality arms [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the validator selftest green with unchanged verdicts on the existing fixtures, scripts/test_review_record_selection.py green with its vocabulary-equality arms pinning the vrs.VALID_* re-export, and the pins suite exit 0 unchanged, re-aiming any validate_review_staging row whose matched literal moved (authoring check: none of the thirteen rows pin the calibration region; expected re-aims zero) [class: REPOSITORY_TEST]
- [x] Run → expect the sys.path[0] resolution property to hold for a deployed-shaped path: invoke the worktree's validator through a temporary symlink created in an mktemp directory (outside the scripts directory) and removed with that directory after the check, and confirm the invocation imports scripts/review_staging_calibration.py, per the twin-sync contract the census document records [class: REPOSITORY_TEST]
- [x] Commit: `refactor: extract review staging calibration module` [class: IMPLEMENTATION_REQUIRED]
