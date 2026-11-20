# Plan: execute-plan read-only verification lane

Backlog origin: docs/history/backlog/2026-11-17-execute-plan-no-lane-for-read-only-verification-plans.md
Driving force: simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-11-19-plan-review-execute-plan-read-only-verification-lane-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.75h
Executed: yes (ee1af836156e80b6bd1bac7dca93302ecd83e031 - pre-squash executed branch tip recorded at execution closeout)
Authoring claim: 2026-11-17-execute-plan-no-lane-for-read-only-verification-plans.md (session sess_abb144a9-b265-4d4d-a2c7-0e12bf45f4d4)

## Terms

- Read-only verification plan: an execute-plan plan whose every task declares `Files: none` and whose tasks edit no tracked path before the completion pass.
- Lane condition: the observable test that selects the lane; evaluated once at Phase 0 entry from the plan file.
- Retained duty: a Phase 0 to Phase 5 duty the lane keeps running for a read-only verification plan.
- Vacuous duty: a duty the lane declares not applicable for a read-only verification plan.
- Execution receipt: the dated exec-review record under `.ai-playbook/reviews/` the archive guard's evidence leg consumes.
- Completion pass: the Phase 2 validation run and the archive transition of a plan.
- EPMODULES: the pins-script variable listing the execute-plan module files governed by the absence sweeps.
- Pins cell: one `pin "<label>"` assertion line in `scripts/check_maintenance_pins.sh`.
- Base recorded-red cell: the pins cell `Step 1.2 pre-prompt task-scope digest record (region-scoped)`, already failing at this plan's base tip before any task (provenance: re-derived at execution 2026-11-19, base `036c2aead`, replacing the authoring-time cell `prompt log has no all-served (stale) entry` which is dormant at this base; the Terms re-derive clause authorized this re-pin).

## Why

A plan whose tasks are all read-only checks still faces the full run contract today: worktree, execution claim, per-task workers, intermediate reviews, light-boundary commits, and a Phase 3 panel. The 2026-11-17 witness run improvised a reduced path with no rule behind it, and the archive guard then refused its first commit for the missing exec-review record. No rule says which duties apply when no task changes a tracked file, so every such run is an unreviewed judgment call.

## Gist & Examples

TLDR: a defined read-only verification lane for execute-plan, so zero-edit verification plans stop improvising their reduced path, named for the simplicity force.

Before: a three-task plan with every `Files:` entry "none" runs its tasks inline by judgment, takes no claim and no panel with nothing authorizing the reductions, and the archive commit is refused for a missing exec-review record that only the full flow would have written.

After: the same plan matches the lane condition at Phase 0 entry; the lane module names the retained duties (manifest, readiness gate, marker, Validation Commands, context checkpoints, the plans-egress pointer record with the archived digest, archive-egress check, registry rows) and the vacuous ones (worktree and claim, per-task workers and reviews, light-boundary commits, Phase 3 panel, suite-policy machinery, continuity probe); the run report discloses the lane, and the archive commit passes the existing evidence leg unchanged.

## Outcome

A read-only verification plan executes under a named, reviewable lane instead of an improvised reduced path.

- The lane's execution receipt satisfies the archive guard's exec-review-record leg with the same name grammar and sha256 contract the full flow already uses.
- The coupling pins fail when the lane module and the archive module's plans-egress pointer record duty drift apart.
- The full-flow contract is byte-unchanged for every plan that does not match the lane condition.

Gate delta: no new refusal class, hard gate, fence, protocol layer, or schema field; adds three pins cells, one pins-script variable, and one EPMODULES membership in `scripts/check_maintenance_pins.sh` (checked-set growth priced by the witnessed silent-drift failure: the 2026-11-17 archive-egress refusal after an unreviewed reduced-path run, `docs/history/backlog/2026-11-17-execute-plan-no-lane-for-read-only-verification-plans.md`); removes, for plans matching the lane condition, the applied worktree placement, execution claim, per-task implement workers with intermediate reviews and light-boundary commits, the Phase 3 review panel, and the suite-policy resolution machinery (protocol-depth removal priced by the same witnessed incident: the reduced path ran unreviewed because no rule defined it); full-flow contract unchanged for every non-lane plan. Follow-up disposition: no follow-up leads anticipated; any residual discovered during execution files a durable backlog origin with a ready-to-dispatch prompt per the archive conversion duty.

## Assumptions

- assume the lane condition is evaluable from the plan alone (every task's `Files:` list declares none and no tracked-path edit before the completion pass); basis: origin row Expected and entry scope arm 1
- assume the lane resolves to primary placement and takes no execution claim; basis: entry scope arm 2 vacuous list and the witnessed run's disclosed reduced path
- assume new-module plus router-bullet placement, the only pre-existing execute-plan file touched being SKILL.md's dispatch table; basis: the load-on-dispatch module architecture and the repo byte-budget anti-growth rules
- assume pins cells are the drift fixture; basis: `scripts/check_maintenance_pins.sh` already governs execute-plan modules through per-module variables and the EPMODULES absence sweeps
- assume the lane's execution receipt reuses the existing name grammar and carries the archived plan bytes' sha256; basis: the `reverse_squash_guard.py` check-archive evidence leg (anchored filename shape plus egress-bytes sha256)

Decision receipts (maintenance-selected arm): lane text home: new module plus router bullet over pointer lines in four phase modules (existing modules stay byte-untouched); suite-policy machinery: vacuous over retained (no code work exists; the retained Validation Commands run is the actual verification); Phase 3: vacuous with the receipt carrying the no-panel statement over a token review (no diff exists to review); drift fixture: pins coupling cells over a new validator (no new machinery).

Decision points requiring a grill: none remain.

## Standing constraints

- No em dashes in any file this plan creates or edits; the write-time fixer runs before every plan-file write.
- Tool-agnostic skill text: the new module names behaviors by intent, never tool names or tool-specific flags.
- Every pre-existing execute-plan skill file is frozen except the Review Scope's explicit must-fix paths (Task 1's SKILL.md dispatch-table edit included); the lane module owns the duty classification and no phase module is edited.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the lane's retained list names exactly the duties the archive guard and closeout gates consume; the coupling pins fail when either side drifts
- maintainability: the lane module and `archive-and-cleanup.md` stay name-coupled through the pins suite
- simplicity: no new blocking gate or validator; the full-flow contract untouched

**Done when:**
- the lane module, the dispatch bullet, and the pins cells exist; the pins suite passes with at most the base recorded-red cell failing; the byte-budget gate exits 0; the public hygiene scan exits 0; the em-dash gate is clean over the plan's added lines

**Ship when:**
- none (repository-internal contract change)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_maintenance_pins.sh` (Task 2)

**Documentation (skill text):**
- `agents/skills/execute-plan/read-only-verification-lane.md` (Task 1) *(new)*
- `agents/skills/execute-plan/SKILL.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/run-setup.md`; frozen: the lane module owns the duty classification and no phase module is edited
- every other pre-existing execute-plan file; same freeze reason
- `scripts/plan_readiness.py`; no readiness grammar change

## Validation Commands

Validation preamble (authoring-time record, per the plans skill rule 29; every command below was executed over the plan bytes at authoring on 2026-11-19): pins suite exit 1 with exactly one failing cell, the base recorded-red cell named in Terms (the authoring-time failing cell `prompt log has no all-served (stale) entry`, pre-existing at base `eaf670f81`; every other cell green at authoring; this plan's cells not yet present, so they assert nothing today); byte-budget gate exit 0 with 0 ceiling breaches (advisory ratchet rows only); public hygiene scan exit 0; em-dash added-lines gate exit 0 over the plan bytes; readiness pre-round exit 1 on its first authoring run (consumer-before-owner and two over-cap items), fixed by the task reorder and item splits in this revision, and re-run to exit 0 before round 1. The pins step accepts at most the base recorded-red cell and fails on any other failing cell, so a new regression cannot hide behind the baseline.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
# 1. Coupling pins (the drift fixture). Exactly one failing cell is accepted:
#    the base recorded-red cell named in Terms. Any other failing cell fails.
bash scripts/check_maintenance_pins.sh > /tmp/pins-run.out 2>&1; pins_rc=$?
if [ "$pins_rc" -ne 0 ]; then
  grep -qF 'Step 1.2 pre-prompt task-scope digest record (region-scoped)' /tmp/pins-run.out || { echo "FAIL: pins failed without the base recorded-red cell"; cat /tmp/pins-run.out; exit 1; }
  [ "$(grep -cF 'PIN FAIL' /tmp/pins-run.out)" -eq 1 ] || { echo "FAIL: pins have failing cells beyond the base recorded-red"; grep -F 'PIN FAIL' /tmp/pins-run.out; exit 1; }
  echo "pins: only the base recorded-red cell failed (accepted baseline)"
fi
# 2. Byte-budget gate (blocking ceiling class).
python3 scripts/skill_text_budget.py --check || { echo "FAIL: byte-budget gate"; exit 1; }
# 3. Public hygiene scan over the repo (outcome contract; exit 0 required).
bash scripts/scan-public-hygiene.sh || { echo "FAIL: public hygiene scan"; exit 1; }
# 4. Em-dash gate over this plan's added lines (explicit base).
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)" || { echo "FAIL: em-dash scan"; exit 1; }
# 5. Readiness structural pre-round over the plan bytes.
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-19-execute-plan-read-only-verification-lane.md || { echo "FAIL: readiness pre-round"; exit 1; }
```

### Task 1: Author the lane module and the router dispatch bullet

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/read-only-verification-lane.md` *(new)*
- `agents/skills/execute-plan/SKILL.md`

- [x] Run `test -f agents/skills/execute-plan/read-only-verification-lane.md` and record RED today: the module does not exist yet [class: REPOSITORY_TEST]
- [x] Create `agents/skills/execute-plan/read-only-verification-lane.md` with heading `## Read-only verification lane` and the required span `plans-egress pointer record` in its receipt-duty sentence [class: IMPLEMENTATION_REQUIRED]
- [x] The module states the lane condition: every task's `Files:` list declares none and no task edits a tracked path before the completion pass, evaluated once at Phase 0 entry from the plan file [class: IMPLEMENTATION_REQUIRED]
- [x] The module states the placement in one sentence: the lane defines its own placement rule through the router dispatch as a named exception to the Worktree-first standard's worktree default, so the run resolves to the primary checkout with no worktree, no execution claim, no transfer-in, and no closeout-baseline capture [class: IMPLEMENTATION_REQUIRED]
- [x] The module states the serialization consult in one sentence: before any task work the run consults the live execution-claim surface and recorded witnesses and refuses to start while any of them occupies the primary checkout, reusing the standard's primary-placement serialization semantics while itself taking no claim [class: IMPLEMENTATION_REQUIRED]
- [x] The module states the branch posture in one sentence: the run works on the primary checkout's current branch only after verifying it equals the base branch at run start, standing down with the standard's two-option remedy (check out the base branch or take the worktree lane) when it does not [class: IMPLEMENTATION_REQUIRED]
- [x] The module states the vacuous duties: per-task implement workers, intermediate task reviews, per-task light-boundary commits, the Phase 3 review panel, the suite-policy resolution machinery, and the per-boundary continuity probe; tasks run inline in the orchestrator with evidence in the session manifest task rows [class: IMPLEMENTATION_REQUIRED]
- [x] The module states retained duties part 1: session bootstrap and manifest including `runtime_state.json` and `pre_archive_receipt`; the readiness gate; the plans skill-gate marker for every plan-file edit; the Phase 2 Validation Commands run; the context budget checkpoint ladder at its safe boundaries [class: IMPLEMENTATION_REQUIRED]
- [x] The module states retained duties part 2: at the Phase 3 exit position, the plans-egress pointer record under the resolved reviews home named `<date>-plan-review-<plan-slug>-exec-r<N>.md`, carrying the SHA-256 of the final plan bytes and the explicit statement that no code review panel ran because the plan's tasks edit no tracked file, pointing at the Phase 2 validation evidence and manifest task rows instead of a code-review pair [class: IMPLEMENTATION_REQUIRED]
- [x] The module states retained duties part 3: the archive move with its document-registry row update and `doc_registry_validator.py validate`; the archive-egress check whose exec-review-record leg this record satisfies unchanged; and the Phase 5 closeout minus its worktree legs [class: IMPLEMENTATION_REQUIRED]
- [x] The module states the stop rule (a task discovered editing a tracked file stops the run at that task boundary and reports; resume follows the existing interruption rules) and the disclosure duty (the run report names the lane and lists the vacuous duties) [class: IMPLEMENTATION_REQUIRED]
- [x] Add one dispatch bullet to the SKILL.md module dispatch table, after the Phase 0 entry, naming `read-only-verification-lane.md`, loaded at Phase 0 entry when the active plan matches the lane condition, stating the lane module owns which duties stay retained or vacuous [class: IMPLEMENTATION_REQUIRED]
- [x] Run the greps and expect GREEN: `grep -qF 'plans-egress pointer record' agents/skills/execute-plan/read-only-verification-lane.md` and `grep -qF 'read-only-verification-lane.md' agents/skills/execute-plan/SKILL.md` both succeed [class: REPOSITORY_TEST]
- [x] Commit: `feat: add execute-plan read-only verification lane module and dispatch bullet` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the lane coupling cells in the maintenance pins script

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `EPMODULES` in `scripts/check_maintenance_pins.sh`

- [x] Add the variable `EPRLANE="$repo/agents/skills/execute-plan/read-only-verification-lane.md"` beside the existing execute-plan module variables [class: IMPLEMENTATION_REQUIRED]
- [x] Append `$EPRLANE` to the `EPMODULES` list so the absence sweeps govern the new module [class: IMPLEMENTATION_REQUIRED]
- [x] Add pin cell `pin "read-only lane names the plans-egress pointer record" grep -qF 'plans-egress pointer record' "$EPRLANE"` coupling the lane module to the archive duty [class: IMPLEMENTATION_REQUIRED]
- [x] Add pin cell `pin "archive module keeps the plans-egress pointer record duty" grep -qF 'plans-egress pointer record' "$EPARCH"`; the phrase occurs exactly once in `archive-and-cleanup.md` today (verified 2026-11-19) [class: IMPLEMENTATION_REQUIRED]
- [x] Add pin cell `pin "read-only lane dispatch bullet present" grep -qF 'read-only-verification-lane.md' "$E"` satisfied by the Task 1 bullet [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` and record the outcome: every new cell green; at most the base recorded-red cell (Terms) still failing [class: REPOSITORY_TEST]
- [x] Commit: `test: pin read-only verification lane coupling cells to the archive pointer-record duty` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Verify the gates and the drift fixture both polarities

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (verification only; evidence lands in the session records)

- [x] Run the full `## Validation Commands` block from the repo root and record each command's outcome and exit code in the session manifest [class: REPOSITORY_TEST]
- [x] Mutation evidence, lane side: in a fresh scratch git clone of the repository under `mktemp -d` (the pins script needs a git work tree), remove the phrase `plans-egress pointer record` from the lane module in the clone, run the pins suite there, and record that the read-only-lane cell fails; then remove the scratch clone (teardown) and record the suite back at its accepted baseline in the real tree [class: REPOSITORY_TEST]
- [x] Mutation evidence, archive side: in a second fresh scratch git clone under `mktemp -d`, rename the phrase in `archive-and-cleanup.md`, run the pins suite there, and record that the archive-anchor cell fails; then remove the scratch clone (teardown) and record the real tree untouched [class: REPOSITORY_TEST]
- [x] Boundary: record the outcomes; when no tracked change remains, record the justified `nothing to commit` boundary outcome [class: REPOSITORY_TEST]
