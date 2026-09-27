# Plan: Execution-lane continuation policy

Backlog origins (scope of record):
- docs/history/backlog/2026-09-27-next-execute-after-landing-interactive-default.md
- docs/history/backlog/2026-09-27-compact-between-execution-runs-mechanism.md

Driving force: automation + simplicity
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-p68-execution-lane-continuation-policy-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

An execution turn knows what to do after landing a plan without re-deriving intent: stop and hand the operator a ready-to-send continuation ask by default, and keep going down the queue when the operator's live directive says so.

- The default post-landing behavior is written down: an interactive single-plan ask stops after landing and its closing report names the next-highest open plan plus a ready-to-send continuation ask.
- A live operator continuation directive overrides the stop in-session: the turn proceeds to the next digest-intact open plan immediately after landing, re-running the readiness gate and the scheduler-state check per plan, until the directive is withdrawn, the queue is empty, or the context genuinely runs low; the per-dispatch boundary keeps applying to automation-born sessions.
- The fresh-context story matches reality: compaction is operator-only, the dispatch boundary is the compaction boundary, and no payload instructs a session to invoke a host CLI slash command anymore.
- Task boundaries stay durable checkpoint state (green commit plus manifest update), so an automatic harness compaction can only land on resumable state.

## Terms

- Live continuation directive: an operator instruction in the current session to keep executing plans sequentially (for example "continue one by one"); live from its utterance until the operator withdraws it, the session ends, or the queue empties.
- Per-dispatch boundary: the rule that one automation dispatch executes one plan and ends; the dispatch boundary is the compaction boundary for automation-born sessions.
- Closing report: the final report of an execution turn; under the default policy it names the next-highest open plan and a ready-to-send continuation ask.
- Payload-guard rule: the authoring rule that a scheduled or dispatched payload never instructs the receiving session to invoke a host CLI slash command (compaction included).

## Assumptions

- assume the whether-to-continue decision is option (b) with option (a) as the default: the operator directed the interactive one-by-one behavior on 2026-09-27 ("continue one by one" in-session = start the next plan immediately after landing), and the second origin's updated fix shape records the same rule; basis: the user direction of 2026-09-27 and the origin's `Fix shape (updated 2026-09-27)` NEW paragraph.
- assume the compact-between-runs mechanism resolves to ending, not compacting: `/compact` is operator-only, a payload invoking it is the refuted premise, and the dispatch boundary is the compaction boundary; basis: the second origin's Problem fact 1 and fix shapes, plus this runtime's own no-compact-primitive witness (an authoring cycle in this repository, 2026-09-28, recorded that no in-session compaction primitive exists).
- assume the merged supersession (the task-boundary compaction item) retires the self-invoked-compaction instruction and keeps its implementable residue: every task boundary ends with a green commit plus the manifest update, so an automatic harness compaction lands only on durable checkpoint state; basis: the second origin's MERGED paragraph.
- assume the maintenance pins suite gates the machinery this plan rewords, so the pins are reconciled in the same edit per the script's own provenance rule: `scripts/check_maintenance_pins.sh` pins the full literal `FINAL STEP, after the report: compact this session` at count 4 (not a bare prefix), the literal `TASK-BOUNDARY COMPACTION` at count 1, and the execute-plan presence literal `Task-boundary compaction duty`; basis: disk reads of the pins script, 2026-09-28 (the suite is green on today's tree and a scratch simulation of the bare rewording fails both count pins).
- assume the dispatch-selection machinery (D1, lane guards, quota legs) already governs each continued plan, so the continuation rule needs only to reference those checks per plan, not restate them; basis: the maintenance skill's D1 paragraph already re-evaluates guards per dispatch.

Decision points requiring a grill: interactive continuation runs option (b) under a live operator directive with option (a) as the default (user direction recorded in the operator's 2026-09-27 one-by-one directive, restated in the second origin's updated fix shape; Tasks 1 and 2); compaction is operator-only and the dispatch boundary is the compaction boundary (refuted-primitive witness recorded in the second origin's Problem, 2026-09-27; Tasks 1 and 3); the task-boundary compaction instruction is retired to its durable-checkpoint residue per the recorded supersession (the second origin's MERGED paragraph, 2026-09-27; Task 3).

## Gist & Examples

TLDR: the execution lane gains its missing post-landing rule (stop-and-report by default, continue-one-by-one under a live operator directive), and the payload templates stop instructing sessions to run compaction they cannot run, for automation (a directive now carries past the first landing without re-deriving intent) plus simplicity (refuted machinery leaves the payloads).

Before this plan, an interactive "execute X" landed X and stopped while the queue sat full, and the one-by-one payloads' `/compact` instruction degraded into running out of context. After it, the default and the override are both written down where the executing turn reads them, and the payload text describes what actually happens: runs end, dispatches start fresh.

Examples:

- The operator asks "execute plan X". The turn lands X and stops; the closing report's last line names plan Y (next-highest open) with a ready-to-send "execute Y" ask.
- The operator says "execute X, then continue one by one". The turn lands X, re-runs the readiness and scheduler-state checks, proceeds to Y, and keeps going until the queue is empty or the context genuinely runs low.
- A scheduled one-by-one payload still executes exactly one plan per dispatch; its FINAL STEP now says the run ends so the next dispatch starts fresh, not that the session should compact itself.

## Evaluation Criteria

**Quality dimensions:**

- single-homing: the continuation rule is stated once in the maintenance skill's execution-lane section; the execute-plan completion area references it rather than restating it.
- reality alignment: no payload text instructs self-invoked compaction; the FINAL STEP sentence prefix count stays pinned green.
- policy clarity: both modes (default stop-and-report, directive override) are decidable from the text alone, with the mode conditions (live directive, queue empty, context genuinely low) explicit.
- residue fidelity: the task-boundary rewrite keeps the durable-checkpoint residue (green commit plus manifest update) and drops only the refuted self-compaction instruction.

**Done when:**

- the maintenance skill's execution-lane section carries the interactive-continuation rule and the compaction-is-operator-only note.
- the execute-plan Phase 5 completion area carries the post-landing duty referencing the maintenance rule.
- the payload templates' two FINAL STEP sentences and the TASK-BOUNDARY COMPACTION duty describe ending and durable checkpoint state instead of self-invoked compaction, and the register entry for the task-boundary duty matches.
- the maintenance pins suite passes green with its three reconciled pins (literals updated beside their provenance comments in the same edit, counts never weakened).
- the Validation Commands block passes end to end.

**Ship when:**

- future one-by-one scheduling asks adopt the payload-guard rule at authoring time (human-owned practice; the rule is written down by this plan).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/maintenance/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh` *(pin reconciliation only: the three literals naming the reworded machinery, with their provenance comments)*

**Tests:**

- none as separate files; `scripts/check_maintenance_pins.sh` is both a reconciliation target (three pin literals, Task 3) and the gate (the suite must pass green after reconciliation).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- the scheduler state file schema and the D1 dispatch machinery; reason: both already exist and the continuation rule references them per plan without changing them.
- the runtime drivers and resume-watcher machinery; reason: the fresh-context rule is prose policy; the machinery already ends runs correctly.
- `docs/history/` archived plans; reason: no task touches completed history.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. The continuation rule and the operator-only note landed in the execution lane (Task 1).
grep -qF "interactive continuation" "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: continuation rule missing"; exit 1; }
grep -qF "the dispatch boundary is the compaction boundary" "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: compaction note missing"; exit 1; }
grep -qF "until the directive is withdrawn, the queue is empty, or the context genuinely runs low" "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: override stop conditions missing"; exit 1; }

# 2. The execute-plan completion area carries the post-landing duty referencing the rule (Task 2).
grep -qF "post-landing continuation duty" "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "FAIL: post-landing duty missing"; exit 1; }
grep -qF "ready-to-send continuation ask" "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "FAIL: closing-report default missing"; exit 1; }

# 3. No payload instructs self-invoked compaction; the durable-checkpoint residue stays (Task 3).
# The negated sweeps flatten newlines first (the FINAL STEP bodies wrap across lines, so a
# line-based grep cannot see a wrapped remainder); the positive counts prove the new form.
PT="$REPO/agents/skills/maintenance/prompt-templates.md"
EP="$REPO/agents/skills/execute-plan/SKILL.md"
if tr '\n' ' ' < "$PT" | tr -s ' ' | grep -qF "compact this session with the runtime's session-compact command"; then echo "FAIL: self-invoked compaction instruction still present"; exit 1; fi
if tr '\n' ' ' < "$PT" | tr -s ' ' | grep -qF "compact this session at the boundary"; then echo "FAIL: refuted boundary compaction instruction still present"; exit 1; fi
test "$(grep -oF 'FINAL STEP, after the report:' "$PT" | wc -l | tr -d ' ')" -eq 4 || { echo "FAIL: FINAL STEP prefix count changed"; exit 1; }
test "$(grep -oF 'the dispatch boundary is the compaction boundary' "$PT" | wc -l | tr -d ' ')" -eq 4 || { echo "FAIL: fresh-context wording not on all four FINAL STEP occurrences"; exit 1; }
test "$(grep -oF 'TASK-BOUNDARY CHECKPOINT' "$PT" | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: durable checkpoint duty missing or duplicated"; exit 1; }
if tr '\n' ' ' < "$PT" | tr -s ' ' | grep -qF "TASK-BOUNDARY COMPACTION"; then echo "FAIL: old duty name still present in templates"; exit 1; fi
if tr '\n' ' ' < "$EP" | tr -s ' ' | grep -qF "Task-boundary compaction duty"; then echo "FAIL: old duty name still present in execute-plan"; exit 1; fi
grep -qF "Task-boundary checkpoint duty" "$EP" || { echo "FAIL: execute-plan checkpoint duty rename missing"; exit 1; }
if tr '\n' ' ' < "$EP" | tr -s ' ' | grep -qF "performs a proactive compaction"; then echo "FAIL: refuted proactive-compaction instruction still in execute-plan"; exit 1; fi

# 4. The pins suite passes green after Task 3's reconciliation (pins updated beside their provenance comments).
( cd "$REPO" && bash scripts/check_maintenance_pins.sh ) || { echo "FAIL: maintenance pins failed"; exit 1; }

# 5. Em-dash cleanliness, scoped to what this plan creates and adds (rule 28). BASE is
# recorded by Task 1's first item before any task commit; the unset guard keeps a
# missing base from silently scanning nothing.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-p68-execution-lane-continuation-policy.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
test -n "$BASE" || { echo "FAIL: BASE not recorded (Task 1 first item)"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE" ) || { echo "FAIL: em-dash in added lines"; exit 1; }
```

### Task 1: The execution-lane continuation rule and the operator-only compaction note

Files:

- `agents/skills/maintenance/SKILL.md`

- [ ] Record the base revision for validation command 5 in the run notes: `BASE="$(git rev-parse HEAD)"`, executed before any task commit of this run. [class: REPOSITORY_TEST]
- [ ] In `agents/skills/maintenance/SKILL.md`, insert into the Step 3 decision area (after the D1 paragraph) one paragraph titled by its opening words `interactive continuation`: the default for an interactive execution ask is one plan, and the closing report names the next-highest open plan plus a ready-to-send continuation ask; when a live continuation directive governs the session, the turn proceeds to the next digest-intact open plan immediately after landing the previous one, re-running the execute-plan readiness gate and the scheduler-state check per plan, until the directive is withdrawn, the queue is empty, or the context genuinely runs low; the per-dispatch boundary applies only to automation-born sessions; the closing "report and stop" shape must not fire while a live continuation directive stands. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same inserted paragraph, add the fresh-context note: compaction is operator-only; agent runs achieve a fresh context by ending, not by compacting, and the dispatch boundary is the compaction boundary; a dispatched or scheduled payload must never instruct the receiving session to invoke a host CLI slash command (the payload-guard rule). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 1 [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: interactive continuation rule with the operator-only compaction note` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The execute-plan post-landing duty

Files:

- `agents/skills/execute-plan/SKILL.md`

- [ ] In `agents/skills/execute-plan/SKILL.md`, insert one paragraph into the Phase 5 area (after the Phase 5 heading's success-path text) opening with the words `post-landing continuation duty`: after the terminal receipt, an interactive turn follows the maintenance skill's execution-lane interactive continuation rule, defaulting to the closing report that names the next-highest open plan plus a ready-to-send continuation ask, and proceeding to the next digest-intact open plan only when a live continuation directive governs the session; reference the rule, do not restate its conditions. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 2 [class: REPOSITORY_TEST]
- [ ] Commit: `execute-plan: post-landing continuation duty referencing the execution-lane rule` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Payload templates and pins describe reality

Files:

- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Reword the four FINAL STEP occurrences (the pinned prefix `FINAL STEP, after the report:` appears four times across the file's template bodies; keep every prefix intact) so each reads: end this run after the report; the next scheduled payload starts in a fresh, compacted context, because the dispatch boundary is the compaction boundary and compaction itself is operator-only. [class: IMPLEMENTATION_REQUIRED]
- [ ] Rename and reword the `TASK-BOUNDARY COMPACTION` standing duty (execution blueprint) to `TASK-BOUNDARY CHECKPOINT`: the duty at every green task boundary is the durable checkpoint state (the task's done commit landed, the session manifest updated), so an automatic harness compaction can only land on resumable state; the session never invokes compaction itself; the boundary telemetry record duty is unchanged. Update the register entry at the top of the file that documents the task-boundary duty to the same name and substance. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/execute-plan/SKILL.md`, rename the mirrored `Task-boundary compaction duty` at both its sites (the Context budget checkpoints subsection heading sentence and the Step 1.1 reference) to `Task-boundary checkpoint duty`, and reword its proactive-compaction instruction to the same durable-checkpoint substance (the run structures each boundary as a green commit plus manifest update so an automatic harness compaction lands only on resumable state; the session never invokes compaction itself). [class: IMPLEMENTATION_REQUIRED]
- [ ] Reconcile the three pins in `scripts/check_maintenance_pins.sh` beside their provenance comments: the FINAL STEP pin's literal becomes `FINAL STEP, after the report:` at count 4 (the reworded tails are gated by validation command 3's positive count instead), the task-boundary anchor pin's literal becomes `TASK-BOUNDARY CHECKPOINT` at count 1, and the execute-plan duty pin's literal becomes `Task-boundary checkpoint duty`; no count weakens. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 3 (all wrap-tolerant negations clean, all positive counts exact, both rename sites present) and command 4 (pins suite green after reconciliation) [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: payloads describe ending and durable checkpoints; pins reconciled` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Full block

Files:

- none (verification-only task)

- [ ] Run → expect GREEN: the full Validation Commands block (rule 21 interim expectation: every command passes at this point). [class: REPOSITORY_TEST]
