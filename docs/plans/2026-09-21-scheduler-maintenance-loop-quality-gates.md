# Plan: Scheduler/maintenance loop-quality gates (origins closure, dirt regression, review threads, vendored landing)

Backlog origins (scope of record): `docs/history/backlog/2026-09-20-executed-plan-origins-left-open-no-gate.md`,
`docs/history/backlog/2026-09-21-merge-dirt-regression-gate.md`,
`docs/history/backlog/2026-09-21-done-review-thread-completion-gate.md`,
`docs/history/backlog/2026-09-21-vendored-runtime-catalog-landing-gap.md`.

Sibling plans: `2026-09-21-scheduler-maintenance-state-durability.md` (durability cluster, externally gated)
and `2026-09-21-scheduler-maintenance-loop-quality-hygiene.md` (hygiene cluster). This plan touches
`agents/skills/execute-plan/SKILL.md`, which the unlanded branch `2026-09-19-scheduler-ops-lanes-durability`
also edits (discovery-ladder sections); the sections are distinct and landing order resolves by the
PRE-STEP re-certification and union-merge precedent.

Plan review: docs/reviews/2026-09-21-plan-review-scheduler-maintenance-loop-quality-gates-r*.md (latest ready round)

## Terms

- **Origins block**: the plan-header "Backlog origins (scope of record)" line(s) listing promoted backlog basenames.
- **Dirt regression**: a hunk in restored dirt that removes at least one line HEAD gained since the run's merge base while every line it adds exists verbatim in the merge-base version of the file (base-era text restored over HEAD-gained content); hunks whose added lines are not all base text are forward-looking rewrites, never regressions.
- **Deploy stamp**: a `.source-commit` file written beside a deployed runtime script recording the source commit the copy was taken from.
- **Review-thread marker**: the JSON file a passive-review session writes when it begins processing feedback: PR identity, branch head, tracked thread IDs, per-thread dispositions.
- **Thread closure**: the state in which every tracked thread carries a verified agent reply or an explicit disposition; human threads are never auto-resolved.

## Assumptions

- assume `gh` CLI is available at execution time for the thread gate's live mode; basis: the github-pr-workflow skill standardizes on gh; unit tests stay offline with canned output.
- assume the merge gates' operative home is the execution blueprint (`prompt-templates.md`), not execute-plan SKILL.md: measured 2026-09-21, no peer-dirt/tree-identical text exists in execute-plan SKILL.md on main; the merge-dirt origin's "Exact location" line overstates that surface, and this plan states the correction in place of inheriting it.

Decision points requiring a grill: gate logic lives in new scripts invoked by skill text (scripts-over-prose preference); standing pre-authorization (scheduling ask, 2026-09-21); affects the new files and wiring tasks. Deploy provenance via a stamp plus helper script rather than changing the deploy flow; standing pre-authorization (scheduling ask, 2026-09-21); affects the merge-dirt task. Review-thread markers live under `docs/tmp/review-threads/` (session-lifetime scratch); standing pre-authorization (scheduling ask, 2026-09-21); affects the receiving-review and done tasks.

## Gist & Examples

What changes: four mechanical gates close four witnessed integrity gaps. The archive step verifies a
plan's origins actually left the backlog top level; the dirt-preservation dance learns to refuse
backward-looking dirt; done proves review threads were closed before reporting completion; and a
mid-execution runtime-catalog edit gains a defined landing path.

**Before (today):** three executions archived their plans while leaving origins open at the backlog top
level (manual sweep closed six on 2026-09-20, commit eff584c9); the authoring lane then risks authoring
duplicate plans for delivered work, the exact waste the coverage rule exists to prevent. A byte-identical
revert of committed merge-lock keying rode three successive squash merges untouched because every dirt
check compared paths, never diff direction (witnessed 2026-09-21, the done-lock.sh Sep-4 revert). A
review-fix session committed and tested its code while eight live automated PR threads went unanswered
(witnessed, the review-thread origin). A review-rule-5 catalog fix made during an execution stranded the
vendored repo copy as uncommitted orphan dirt (witnessed 2026-09-21, context-budget closeout).

**After (this plan):** before an archive commit, the executor runs `scripts/check_plan_origins_closed.py`:
stragglers are dispositioned in the same commit or recorded why open, and the maintenance survey warns on
any survivor. After a squash merge restores dirt, the executor runs `scripts/dirt_regression_gate.py`
against the merge base: any hunk removing lines HEAD gained is a named regression, the file is restored
from HEAD, and the summary carries one line per restored file; deployed copies carry a `.source-commit`
stamp the gate cites as provenance. A passive-review session writes its thread marker at processing
start; `done` runs `scripts/review_thread_gate.py` and fails closed while a tracked thread lacks a
verified reply or disposition, reporting push authorization separately. review-plan rule 5 gains the
landing clause: land the vendored copy in-run when it is in plan scope, else file a vendored-sync backlog
item naming the changed files.

**Edge cases:** a plan with no origins block passes the origin check trivially (nothing to verify). The
dirt gate passes untouched forward-looking dirt (the witness's original preservation behavior). A session
with no marker is unaffected by the thread gate; human-authored threads never auto-resolve; retrying a
timed-out reply must not duplicate it (idempotence check before create). A vendored edit already in plan
scope lands in-run and files nothing.

## Design Invariants (CR Guard)

- The survey's warn arm stays warn-and-continue (same posture as sibling optional gates); only the
  archive-step arm gates behavior, and only on its own stragglers.
- Tests never touch the network: `review_thread_gate.py` classifies canned `gh` output; live fetch is a
  separate invocation path behind the same classifier.
- Scripts take host-specific inputs as arguments; no personal or absolute machine paths in repo files.
- The dirt gate is additive to the existing preservation dance: it runs after restore and only classifies
  direction; it does not change what may be committed.
- Integration Points update in both directions: receiving-review and review-plan gains carry a consumer
  step in done; done's new step references the provider duties without restating them.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each gate fails closed exactly on its named condition and passes the documented
  non-conditions (no origins block, forward-looking dirt, no marker, all threads closed).
- testability: every new script has a unit test file with scratch fixtures under mktemp and explicit
  teardown; flip-probes simulated (deleting the guarded behavior flips the test).
- consistency: skill-text insertions name their integration counterparts; no duplicated duty prose
  between provider and consumer skills.
- simplicity: four scripts, no new state files beyond the marker, no schema changes.

**Done when:**
- All tasks checked; `python3 scripts/test_check_plan_origins_closed.py`, `python3 scripts/test_dirt_regression_gate.py`,
  and `python3 scripts/test_review_thread_gate.py` all exit 0.
- `bash scripts/check_maintenance_pins.sh` exits 0; the plan's Validation Commands block exits 0.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-21-scheduler-maintenance-loop-quality-gates.md` exits 0.
- The latest review round reports ready=yes with zero unresolved blocking findings on the final digest.

**Ship when:**
- The thread gate witnesses a real passive-review session closing all tracked threads before done, and a
  real merge cites the dirt gate's regression line for restored backward dirt. Loop/human-owned; prose
  only. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `scripts/check_plan_origins_closed.py` *(new)*
- `scripts/dirt_regression_gate.py` *(new)*
- `scripts/review_thread_gate.py` *(new)*
- `scripts/deploy_runtime_scripts.sh` *(new)*
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `AGENTS.md`

**Tests:**
- `scripts/test_check_plan_origins_closed.py` *(new)*
- `scripts/test_dirt_regression_gate.py` *(new)*
- `scripts/test_review_thread_gate.py` *(new)*
- `scripts/check_maintenance_pins.sh`

**Plan-related extension;** findings are in scope when causally related to this plan. Docs named in the
closure duties (stale-reference sweeps) are in scope when a must-fix change requires the update.

**Partially-in-scope files:** in `execute-plan/SKILL.md`, only the Phase 4 archive step region is open. In
`maintenance/SKILL.md`, only the Step 1 survey bullet list is open. In `done/SKILL.md`, only Step 3 item 1
and the new gate step are open. In `review-plan/SKILL.md`, only Iteration Discipline rule 5 is open. In
`AGENTS.md`, only the Vendored Asset Sync Rules section gains one clause. In `prompt-templates.md`, only
the execution blueprint's final-merge paragraph and archive sentence are open.

**Out of scope; reject unless plan-related:**
- `scripts/done-lock.sh` internals; reason: the gate consumes its locks, changes none.
- budget-gate sections of any skill; reason: owned by the quota-aware sibling work.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
EMDASH="$(printf '\342\200\224')"
fail=0
# 1. New scripts exist and their tests pass
for t in test_check_plan_origins_closed test_dirt_regression_gate test_review_thread_gate; do
  python3 "$REPO/scripts/$t.py" >/dev/null 2>&1 || { echo "FAIL: $t did not pass"; fail=1; }
done
# 2. Wiring needles: each structural obligation gets its own dedicated search
grep -qF 'check_plan_origins_closed.py' "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "FAIL: archive arm unwired"; fail=1; }
grep -qF 'origins block' "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: survey warn unwired"; fail=1; }
grep -qF 'dirt_regression_gate.py' "$REPO/agents/skills/maintenance/prompt-templates.md" || { echo "FAIL: merge arm unwired"; fail=1; }
grep -qF 'run the origins-closure check' "$REPO/agents/skills/maintenance/prompt-templates.md" || { echo "FAIL: blueprint archive-sentence duty unwired"; fail=1; }
grep -qF 'dirt_regression_gate.py' "$REPO/agents/skills/done/SKILL.md" || { echo "FAIL: done dirt guard unwired"; fail=1; }
grep -qF 'review_thread_gate.py' "$REPO/agents/skills/done/SKILL.md" || { echo "FAIL: done thread gate unwired"; fail=1; }
grep -qF 'review-thread marker' "$REPO/agents/skills/receiving-review/SKILL.md" || { echo "FAIL: marker duty unwired"; fail=1; }
grep -qF 'vendored-sync backlog item' "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: rule 5 clause missing"; fail=1; }
grep -qF 'land the vendored copy in the same run' "$REPO/AGENTS.md" || { echo "FAIL: AGENTS.md clause missing"; fail=1; }
# 3. Pins suite green
bash "$REPO/scripts/check_maintenance_pins.sh" || { echo "FAIL: pins do not hold"; fail=1; }
# 4. Em-dash ban scoped per plans rule 28: whole-file sweep ONLY for files this plan creates
#    plus prompt-templates.md (whose single legacy dash, line 26, Task 4 fixes); other edited
#    files carry legacy em dashes in frozen regions (measured 2026-09-21: execute-plan SKILL.md
#    lines 505/508/509) and are covered by the exact-needle greps above, which the inserted
#    lines must match verbatim.
for f in scripts/check_plan_origins_closed.py scripts/dirt_regression_gate.py scripts/review_thread_gate.py scripts/deploy_runtime_scripts.sh scripts/test_check_plan_origins_closed.py scripts/test_dirt_regression_gate.py scripts/test_review_thread_gate.py agents/skills/maintenance/prompt-templates.md; do
  if grep -q "$EMDASH" "$REPO/$f"; then echo "FAIL: em dash in $f"; fail=1; fi
done
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: Origins-closure check script and tests

Files:
- `scripts/check_plan_origins_closed.py` *(new)*
- `scripts/test_check_plan_origins_closed.py` *(new)*

- [ ] Write the script: `--plan <path>` mode is the archive gate's arms: given the plan being archived, extract ITS origins-block basenames and exit 1 listing the stragglers of THAT plan only; without `--plan`, the corpus-wide scan over all archived plans runs on the warn arm only (exit 0 with warnings; the maintenance survey owns it); a basename passes when it sits under `{backlog_completed_dir}` or the top-level item's header carries `Status: closed` or `Status: done`; paths from facts-resolution arguments, never hardcoded [class: IMPLEMENTATION_REQUIRED]
- [ ] `test_check_plan_origins_closed.py#test_all_closed_passes`; given a scratch backlog with every origin under completed/, expects exit 0 and no straggler lines [class: REPOSITORY_TEST]
- [ ] `test_check_plan_origins_closed.py#test_open_straggler_fails`; given one top-level open origin of the plan under test, expects exit 1 naming it, and `--warn` exits 0 with the warning [class: REPOSITORY_TEST]
- [ ] `test_check_plan_origins_closed.py#test_closed_status_in_place_passes`; given a top-level item with `Status: closed (...)`, expects exit 0 [class: REPOSITORY_TEST]
- [ ] `test_check_plan_origins_closed.py#test_no_origins_block_trivial`; given an archived plan without the block, expects exit 0 [class: REPOSITORY_TEST]
- [ ] `test_check_plan_origins_closed.py#test_unrelated_plans_stragglers_do_not_block`; given an unrelated archived plan carrying an open origin while the plan under test has none, expects `--plan` mode exit 0 for the plan under test and a corpus-wide warning [class: REPOSITORY_TEST]
- [ ] Fixtures built under mktemp with explicit teardown; run → expect GREEN [class: REPOSITORY_TEST]

### Task 2: Wire the origins gate into archive step, survey, and blueprint

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

- [ ] Phase 4 archive step: after the move and before the archive commit, run the check in `--plan` mode for the plan being archived; stragglers of that plan are dispositioned in the same archive commit per the promoted-backlog rule (done, or recorded why open with a note), mirroring the completeness gate's ordered-transition posture; corpus-wide stragglers are never this gate's blocker (the survey warn arm owns them) [class: IMPLEMENTATION_REQUIRED]
- [ ] Maintenance Step 1 survey: add the warn arm: an open top-level item whose basename appears in any archived plan's origins block is reported as plan-uncovered-with-archived-coverage (warn, never skip semantics change) [class: IMPLEMENTATION_REQUIRED]
- [ ] Execution blueprint archive sentence: extend "move backlog origins to completed/ with Status: done" with the verification duty, prescribed to contain the exact span `run the origins-closure check` (disposition or record why open), so the wiring needle and the Task 8 pin have executable text [class: IMPLEMENTATION_REQUIRED]
- [ ] Revisions ledger entry for the survey addition; deviation-list entry for the blueprint sentence [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the archive-arm needle, the survey-warn needle, and the blueprint archive-sentence needle (`run the origins-closure check` in prompt-templates.md) [class: REPOSITORY_TEST]

### Task 3: Dirt regression gate script, deploy stamp, and tests

Files:
- `scripts/dirt_regression_gate.py` *(new)*
- `scripts/deploy_runtime_scripts.sh` *(new)*
- `scripts/test_dirt_regression_gate.py` *(new)*

- [ ] Write the gate: given `--base <merge-base-sha>` and restored paths, classify per hunk of each restored file's diff against HEAD with the merge base bound: a hunk marks a dirt REGRESSION when it removes at least one line HEAD gained since `--base` AND every line it adds exists verbatim in the merge-base version of the file (the hunk restores base-era text over HEAD-gained content; exit 1, one line per regressed file); hunks whose added lines are not all base text are forward-looking rewrites and pass, so a modification of a HEAD-gained line (removed line replaced by new text not present at the base) passes, as do pure additions and removals of lines already present at the base; `--stamp` cites an adjacent `.source-commit` stamp as provenance when present, report-only when absent. Stamping is manual-only for now: the helper is the sanctioned manual path, automatic deploy-on-landing was considered and rejected (see the decision receipt in Assumptions), and the absent-stamp arm stays report-only [class: IMPLEMENTATION_REQUIRED]
- [ ] Write the deploy helper: copies named scripts to a target dir and writes `.source-commit` with the current HEAD sha; refuses when the tree is dirty (stamped provenance must be committed provenance) [class: IMPLEMENTATION_REQUIRED]
- [ ] `test_dirt_regression_gate.py#test_reverting_hunk_is_regression`; given a scratch repo where dirt reverts a HEAD hunk gained since the base, expects exit 1 naming the file [class: REPOSITORY_TEST]
- [ ] `test_dirt_regression_gate.py#test_forward_dirt_passes`; given dirt that only adds lines, expects exit 0 [class: REPOSITORY_TEST]
- [ ] `test_dirt_regression_gate.py#test_prebase_line_modification_passes`; given dirt that modifies a line already present at the merge base, expects exit 0 (discriminates the base-scoped reading from a literal all-removed-lines reading) [class: REPOSITORY_TEST]
- [ ] `test_dirt_regression_gate.py#test_headgained_line_modification_passes`; given dirt that modifies a line HEAD gained since the base, replacing it with new text not present at the base, expects exit 0 (forward-looking rewrite; discriminates the hunk-level rule from a literal all-removed-lines reading) [class: REPOSITORY_TEST]
- [ ] `test_dirt_regression_gate.py#test_revert_to_base_text_is_regression`; given dirt that replaces a HEAD-gained hunk with the base-era text of that region, expects exit 1 even though the change is not a whole-file revert (the witnessed partial-revert shape) [class: REPOSITORY_TEST]
- [ ] `test_dirt_regression_gate.py#test_stamp_cited_when_present`; given a stamp file, expects the provenance line naming the stamped commit [class: REPOSITORY_TEST]
- [ ] Fixtures under mktemp with explicit teardown; run → expect GREEN [class: REPOSITORY_TEST]

### Task 4: Wire the regression gate into the merge paragraph and done guard

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/done/SKILL.md`

- [ ] Execution blueprint final-merge paragraph: after the squash commit and the dirt backup/restore it sits between, and before the branch deletion, run the regression gate against the run's merge base; any regressed file is restored from HEAD, and the merge summary carries one line per restored file naming the regression [class: IMPLEMENTATION_REQUIRED]
- [ ] prompt-templates.md deviation list: fix the legacy em dash on line 26 (the stand-down-duty deviation entry, inside this plan's open deviation-list region), so the whole-file em-dash gate on this file is satisfiable [class: IMPLEMENTATION_REQUIRED]
- [ ] done Step 3 item 1 pre-commit guard: extend the leaked-revert check to unstaged dirt that regresses HEAD (same classification; restore from HEAD and report instead of committing the regression) [class: IMPLEMENTATION_REQUIRED]
- [ ] Deviation-list entry for the blueprint sentence [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on both wiring needles [class: REPOSITORY_TEST]

### Task 5: Review-thread marker duty and gate script

Files:
- `agents/skills/receiving-review/SKILL.md`
- `scripts/review_thread_gate.py` *(new)*
- `scripts/test_review_thread_gate.py` *(new)*

- [ ] receiving-review: add the marker duty: when a passive-review session begins processing external feedback it writes `docs/tmp/review-threads/<session-slug>.json` carrying PR identity, branch head, tracked thread IDs, and the writer's session identity; per-thread disposition updates land in the same file; replies post idempotently: verify the exact existing response before creating a new one, and verify attachment by stable thread ID plus parent metadata. Session identity derivation (named once here so writer and reader cannot drift): the slug is derived from the runtime session id at marker-write time and recorded in the marker; done matches the CURRENT session's identity against the recorded value, and a marker whose recorded identity does not match is reported as stale and skipped, never gating an unrelated session's done run [class: IMPLEMENTATION_REQUIRED]
- [ ] Write the gate: read-only; `--marker <path>` plus a canned or live inventory source; classify each tracked thread: verified agent reply, explicit disposition, human thread (never auto-resolved), or automated resolved without reply (failure); exit 0 only on closure; exit 1 listing unclosed threads; `gh` output is parsed from a file or pipe in tests, network only via an explicit `--live` flag [class: IMPLEMENTATION_REQUIRED]
- [ ] `test_review_thread_gate.py#test_all_replied_passes`; `#test_unanswered_automated_fails`; `#test_disposition_passes`; `#test_human_thread_never_autoresolved`; `#test_duplicate_reply_detected` (exact-body match marks the reply already posted); `#test_missing_marker_passes` (no marker file means the gate exits 0 with nothing to check, the documented no-marker non-condition); canned fixtures, no network; run → expect GREEN [class: REPOSITORY_TEST]

### Task 6: Done review-thread closure gate

Files:
- `agents/skills/done/SKILL.md`

- [ ] New step after the backlog inbox gate: when a review-thread marker whose recorded session identity matches the current session exists, run the gate; fail closed (report blocked, release the lock per Step 6) when closure is not established; report push authorization separately from review-response state; a session with no marker, or a marker from a different or stale identity, is unaffected (reported, never gating) [class: IMPLEMENTATION_REQUIRED]
- [ ] Integration Points: done gains the consuming step reference; receiving-review names done as the gate consumer [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on the done gate needle [class: REPOSITORY_TEST]

### Task 7: Vendored catalog landing clause

Files:
- `agents/skills/review-plan/SKILL.md`
- `AGENTS.md`

- [ ] Iteration Discipline rule 5: append the landing clause: when the rule forces a runtime-catalog edit during an execution, either land the vendored copy in the same run when the file is in the plan's scope, or file a vendored-sync backlog item naming the changed files, so the twin is a tracked handoff instead of orphan dirt [class: IMPLEMENTATION_REQUIRED]
- [ ] AGENTS.md Vendored Asset Sync Rules: add the mirrored one-line clause pointing at rule 5 (the runtime-side edit must leave a tracked landing path) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN on both clause needles [class: REPOSITORY_TEST]

### Task 8: Pins, em-dash sweep scope check, final validation

Files:
- `scripts/check_maintenance_pins.sh`

- [ ] Add standing pins for ALL nine wiring obligations, each with a recorded flip-probe (delete the guarded sentence in a temp copy, confirm the pin fails): the archive-arm needle in execute-plan SKILL.md; the survey-warn needle in maintenance SKILL.md; the blueprint merge-arm needle and the blueprint archive-sentence duty needle; the done dirt-guard needle and the done thread-gate needle; the receiving-review marker-duty needle; the review-plan rule 5 clause needle; the AGENTS.md clause needle [class: REPOSITORY_TEST]
- [ ] Execute the em-dash scope proof against today's tree BEFORE the edits and record the measured result beside the command: the new-file sweep is clean; the prompt-templates whole-file sweep fires today on line 26 (Task 4 fixes it); execute-plan SKILL.md legacy em dashes at lines 505/508/509 sit in frozen regions no task touches, so the block scopes execute-plan to the exact-needle greps and sweeps no whole edited file beyond prompt-templates (plans rule 28 scope note) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: full Validation Commands block, exit 0 [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-21-scheduler-maintenance-loop-quality-gates.md` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: mechanical gates for origin closure, dirt regression, review threads, vendored landing` [class: REPOSITORY_TEST]
