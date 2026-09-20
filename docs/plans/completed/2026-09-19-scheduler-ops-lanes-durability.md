# Plan: Scheduler ops lanes and durability (claim check, quota decisions, live-session ladder, recycling, dispositions)

Backlog origins (all `docs/history/backlog/`): `2026-09-18-authoring-lane-claim-check-gap.md`,
`2026-09-18-maintenance-quota-aware-lane-decisions.md`,
`2026-09-19-execute-plan-live-session-check-runtime-ambiguity.md`,
`2026-09-19-recycling-update-flip-refuted-delete-plus-create.md`,
`2026-09-19-host-caveat-durability-claim-scope.md`,
`2026-09-19-transcription-cross-check-before-write.md`,
`2026-09-19-hook-outcome-audit-visibility.md`,
`2026-09-19-subagent-session-record-persistence-races.md`,
`2026-09-19-model-selection-persist-foreign-key.md`,
`2026-09-19-maintenance-friction-audit-lane.md` (disposition only).

Split of record: the 14-origin dispatch "scheduler ops liveness residuals" is split into two
plans per the dispatch's split guidance. This is plan 2 (the durability/transcription/
persistence trio plus the lane origins that fold there). Plan 1 is
`docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (selection-helper pair, verb contract,
toolset precheck). The friction-audit-lane origin is deferred to its own future plan
(Task 7 annotates the item; folding a new audit subsystem here would exceed the plan budget).

## Terms

- **Authoring claim file**: `{tmp_dir}/authoring-claims/<backlog-item-basename>.md` (default
  `docs/tmp/authoring-claims/`), carrying session id, target item path, created/updated
  timestamps; the authoring lane's liveness witness.
- **Cadence period**: 2 hours (the loop's firing cadence and the freshness bound reused by
  the manifest staleness rules).
- **G1a / G1e**: the authoring and execution lane guards (SKILL.md Step 2).
- **Discovery arm**: the lane-guard arm that detects a live session not visible in the
  automation listings.
- **Dispatch ladder**: the overlay's ordered child-dispatch steps; its primary path today is
  a recycling `CronUpdate`, refuted live 2026-09-19.
- **HOST CAVEAT**: the rule that a recycling update whose echoed record is not verifiably
  the intended form is treated as a refusal (delete-plus-create instead).
- **Quota snapshot**: the survey-time primary-window reading (percent used, minutes to
  reset, source) recorded with each lane decision as `quota_at_decision`.
- **Liveness ladder**: the repo-scoped live-session discovery order: driver claim check,
  manifest heartbeat, process scan last.
- **Pins suite**: `scripts/check_maintenance_pins.sh`; exit 0 = all pins hold.

## Assumptions

- assume claim files are keyed by backlog item basename (the collision surface witnessed
  2026-09-18 was two authoring sessions on the same scope, not the same plan filename);
  basis: the claim-check item's witness paragraph.
- assume payloads write the literal `docs/tmp/authoring-claims/` path (payloads cannot
  resolve facts keys; the facts currently pin `tmp_dir` to `docs/tmp/`), the same recorded
  rationale as the resume rule's literal `docs/tmp/` path; basis: prompt-templates.md
  resume-rule and worktree bullets.
- assume the quota estimates of record are the pinned observations (execution one to four
  hours per the lane guards; authoring 30 to 120 minutes observed) and no new constants are
  introduced; basis: the quota-aware item's reuse clause and the fire-time item.
- assume the state schema STAYS 4 (peer commit `20e87544` landed the 3-to-4 bump with
  fire-time bookkeeping on 2026-09-19, satisfying the item's "under a schema bump" line):
  Task 2 adds `quota_at_decision` additively within the landed schema-4 shape, and the pins
  schema assertion (line ~146) already checks 4 and is not touched; basis: the landed
  SKILL.md schema block and pins block, verified 2026-09-20.
- assume the recycling rewrite keeps the delete-plus-create fallback's existing semantics
  (rollback, ambiguous-outcome carve-out, retries) and only demotes the update call from
  operative primary to optimization-behind-live-verification; basis: the recycling item's
  fix step 1.
- assume the execute-plan runtime overlay of record is `runtime-contract.md`; the live-session
  item names `agents/skills/execute-plan/zcode.md`, which does not exist on disk;
  basis: execute-plan directory inventory and SKILL.md line 36, 2026-09-19.
- assume the durable HOST CAVEAT rewrite (not the one-off scoping alternative) is the
  disposition for the durability item, closing both items together; basis: the item offers
  either and the recycling item is executed by this same plan.
- assume repo-owned hooks self-log decisions; host-side log enrichment (`hook.run.failed`
  stderr/exit-code attachment, per-hook heartbeat in host logs) is an external prerequisite;
  basis: the hook-outcome item's two gaps, only the first being repo-code.
- assume the transcription fix lands as a numbered rule in
  `projects/.ai-playbook/agent_workflow_guidelines.md` (next number 67), not a new skill;
  basis: the item's "candidate to later grow into a small verification skill" wording.

Decision points requiring a grill: two-plan split and friction-audit-lane deferral: per dispatch split guidance and two-plan cap, source: dispatch standing pre-authorization, 2026-09-19, header and Task 7; transcription home: guidelines rule not a skill, source: dispatch standing pre-authorization over the item's wording, 2026-09-19, Task 5; host-owned dispositions: backlog annotations plus overlay witness, source: item texts name ZCode application internals, 2026-09-19, Task 7; durable-caveat alternative: land the rewrite, source: item's either-or with the rewrite as the durable option, 2026-09-19, Task 4; quota schema rebase: additive quota_at_decision within the landed schema 4 rather than a renumber to 5, source: peer-landed baseline 20e87544 verified against disk 2026-09-20, Task 2.

## Gist & Examples

Seven fixes that make the scheduler's lanes and their durability witnesses honest.

1. **Authoring claim check (Task 1).** The 2026-09-18 collision (automation-343ce2b0 vs a
   foreign session on the same P9 scope) was caught only by worktree inspection: the lane
   guards' arms are listing- and state-based, and a live foreign authoring session appears
   in neither. Each authoring session now writes a claim file before its pre-work gate and
   refreshes it like the execute manifest; the G1a discovery arm treats a fresh foreign
   claim as an occupied lane, and the authoring payload's fire-time gate refuses to start
   when a fresh foreign claim covers the same item.
2. **Quota-aware lane decisions (Task 2).** The 2026-09-18 ~20:22 turn recorded "execution
   no-op" while the primary window was fresh; the decision mechanism never saw the quota
   numbers. The survey now takes the quota snapshot, every lane decision records
   `quota_at_decision`, near-reset windows defer dispatches that cannot fit their lane's
   runtime estimate, and a fresh-window no-op on a free lane with dispatchable work must
   cite an explicit non-quota reason.
3. **Live-session discovery ladder (Task 3).** Answering "is a peer session live?" had no
   defined mechanism, so an orchestrator grepped the host process table for another agent's
   binary. A repo-scoped ladder replaces it: driver claim check when a machine manifest
   exists, session-manifest heartbeat plus staging-doc presence next, process scan last and
   only with the reason stated. The maintenance discovery arm mirrors the ladder.
4. **Recycling demoted to verified-only (Task 4).** The live 2026-09-19 flip refuted the
   parent-to-child recycling update: the call reported success while the record landed
   disabled, completed, with a stale `nextRunAt`, silently darkening the loop. The ladder's
   operative path becomes delete-plus-create; the update stays only as an optimization
   re-enabled after a live-verified flip; both child blueprints gain the durable HOST CAVEAT
   text; the refuted-verdict line's durability claim is landed truthfully.
5. **Transcription cross-check (Task 5).** The highest-stakes correction class: form-field
   swaps, duplicate invoice entries, wrong amounts carried into summaries. A numbered
   guideline rule makes the cross-check-before-write step explicit: dedupe on a
   source-identity key, verify written fields against the source region (not memory), and
   copy canonical values from the project facts document on repeated workflows.
6. **Hook outcome self-logging (Task 6).** Repo-owned hooks never logged their decisions,
   and a failing hook's log record carried neither exit code nor stderr. The shared
   budget-guard core gains a rate-limited decision log and a daily heartbeat line; host-side
   log enrichment stays an external prerequisite (Task 7).
7. **Dispositions for host-owned residuals (Task 7).** The subagent persistence races, the
   model-selection FK failure, and the host-side hook logging live in the ZCode application,
   not this repo: the plan annotates those items with dated dispositions and external
   prerequisites, adds the store-level darkness-triage witness to the runtime overlay, and
   records the friction-audit-lane deferral.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every origin acceptance is either a task checklist outcome or a Ship-when
  line with its evidence owner; the coverage map in the split header is complete.
- mechanical verifiability: every new rule is pinned or grep-gated fail-closed with a
  recorded RED-today flip; the pins suite exits 0 after each task that touches pinned files.
- conservation: existing semantics (rollback, ambiguous-outcome carve-out, re-arm parity
  between the two blueprints, watcher contracts) survive the recycling and claim-check
  rewrites; the pins suite is the regression net.

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0 with the new pins (claims, quota fields,
  ladder precheck ordering, recycling operative path, caveat parity, store witness).
- The state-file schema block shows schema 4 with `quota_at_decision` and the pins schema
  block asserts it.
- The authoring blueprint contains the claim-file duty and the foreign-claim fire-time gate;
  the execution blueprint's re-arm paragraph is byte-identical to the authoring one (parity
  pin holds).
- The overlay's ladder section names delete-plus-create as the operative path and the
  verification section records the refuted parent-to-child verdict with the durability claim
  landed truthfully.
- `agent_workflow_guidelines.md` carries rule 67 with its three obligations.
- The budget-guard core writes decision and heartbeat log lines and its tests pass.
- The four disposition annotations exist in their backlog items.

**Ship when:**
- A 7-day log window shows zero `persisted_missing` events for completed subagents
  [class: EXTERNAL_RELEASE_GATE]; evidence owner: the ZCode application's session-store
  fix; closure: the log-window audit recorded on the backlog item.
- A forced empty-resume produces a visible repair/tombstone record, not a blank replay
  [class: EXTERNAL_RELEASE_GATE]; evidence owner: the ZCode application.
- Zero `session.model_selection.persist_failed` events over a 72-hour window, with resumed
  sessions keeping their selected model or the write removed from the code path
  [class: EXTERNAL_RELEASE_GATE]; evidence owner: the ZCode application.
- A deliberate budget-guard block and a killed hook appear in host logs with decision,
  exit code, and stderr tail; a down daemon-backed hook is visible within one day via a
  heartbeat [class: EXTERNAL_RELEASE_GATE]; evidence owner: the ZCode application's hook
  runner.
- The friction-audit lane is authored as its own certified plan (watermarks, cadence,
  bounded passes) [class: OPERATIONS_FOLLOW_UP]; evidence owner: a future authoring
  dispatch of `2026-09-19-maintenance-friction-audit-lane.md`.
- A sample re-run of an invoice or form task produces the dedupe-plus-verify receipt the
  transcription origin's acceptance names (entries deduped, fields checked against source)
  [class: OPERATIONS_FOLLOW_UP]; evidence owner: the next real transcription-shaped task in
  any repo; closure: the receipt recorded in that task's notes.
- Zero new duplicate-entry or wrong-field corrections in the next corrections-mining pass
  over typed prompts [class: OPERATIONS_FOLLOW_UP]; evidence owner: the friction-audit
  mining pass; closure: a dated mining-pass result recording the zero.
- The first real scheduler-dispatched child after Task 4 lands re-arms an ENABLED parent
  with a future `nextRunAt`, witnessed in the listing (the recycling origin's second
  acceptance) [class: OPERATIONS_FOLLOW_UP]; evidence owner: the next maintenance dispatch
  cycle; closure: the listing witness recorded in the scheduler state file's children entry
  and turn output.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/hooks/budget-guard/budget_guard_core.py`
- `agents/hooks/budget-guard/README.md`
- `scripts/check_maintenance_pins.sh`

**Tests:**
- `scripts/test_budget_guard_hooks.py`

**Docs and skill layer:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `docs/history/backlog/2026-09-19-subagent-session-record-persistence-races.md`
- `docs/history/backlog/2026-09-19-model-selection-persist-foreign-key.md`
- `docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md`
- `docs/history/backlog/2026-09-19-maintenance-friction-audit-lane.md`

**Plan-related extension**; implementation and review may change files not listed above.
Treat a finding as in scope when it is **causally related to this plan**: it implements or
completes a plan task, fixes a regression introduced by plan work, closes wiring or docs
implied by an explicit must-fix change, or contradicts a contract the plan changed. If the
link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `projects/.ai-playbook/development_lessons.md`; peer-session-owned and currently dirty in
  the shared checkout.
- `docs/plans/2026-09-19-provider-429-retry-storm-shaping.md`; a peer session's untracked
  plan draft.
- `agents/skills/execute-plan/runtime-contract.md` sections outside the new discovery pin
  (driver state machine, transition table); frozen except for the Task 3 insertion.
- The friction-audit lane's implementation (state file, script, recipe); deferred to its own
  future plan; only the item annotation is in scope.

## Validation Commands

```bash
set -u
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
fail=0

# 1. Pins suite (all new pins included) and its own syntax.
if bash "$repo/scripts/check_maintenance_pins.sh" 2>&1; then :; else
  echo "GATE FAIL: pins suite"; fail=1; fi
bash -n "$repo/scripts/check_maintenance_pins.sh" || { echo "GATE FAIL: pins syntax"; fail=1; }

# 2. Budget-guard core tests still pass with the decision log.
if python3 "$repo/scripts/test_budget_guard_hooks.py" 2>&1; then :; else
  echo "GATE FAIL: budget-guard tests"; fail=1; fi
python3 -m py_compile "$repo/agents/hooks/budget-guard/budget_guard_core.py" \
  || { echo "GATE FAIL: guard core does not compile"; fail=1; }

# 3. Claim-check surfaces: SKILL.md discovery arm, blueprint duty and gate (per-file gates).
grep -qF "authoring-claims" "$repo/agents/skills/maintenance/SKILL.md" \
  || { echo "GATE FAIL: G1a discovery arm missing claim reading"; fail=1; }
grep -qF "authoring-claims" "$repo/agents/skills/maintenance/prompt-templates.md" \
  || { echo "GATE FAIL: blueprint claim duty missing"; fail=1; }
grep -qF "never clobber the first writer's witness" "$repo/agents/skills/maintenance/prompt-templates.md" \
  || { echo "GATE FAIL: blueprint foreign-claim gate missing (clobber-witness needle)"; fail=1; }

# 4. Quota-aware decision surfaces: snapshot in Step 1, per-lane record + branches in Step 3.
step3="$(sed -n '/### Step 3: decision/,/### Step 4/p' "$repo/agents/skills/maintenance/SKILL.md")"
case "$step3" in
  *"quota_at_decision"*) :;;
  *) echo "GATE FAIL: Step 3 lacks the quota_at_decision record"; fail=1;;
esac
case "$step3" in
  *"D1 defers the execution dispatch past the reset and D2 defers the authoring dispatch"*) :;;
  *) echo "GATE FAIL: Step 3 lacks the near-reset deferral branch (branch-verbatim needle)"; fail=1;;
esac

# 5. Schema 4 in the skill's state block and in the pins validator.
grep -qF '"schema": 4' "$repo/agents/skills/maintenance/SKILL.md" \
  || { echo "GATE FAIL: state schema not bumped to 4 in SKILL.md"; fail=1; }
grep -qF '"schema") != 4' "$repo/scripts/check_maintenance_pins.sh" \
  || { echo "GATE FAIL: pins schema block not bumped to 4"; fail=1; }

# 6. Recycling operative path: the update-as-primary literal is gone; the operative needle
#    and the durable caveat are present. The escaped bracket keeps this document's own text
#    from matching (intentional escape; do not normalize).
out="$(grep -nF 'update the recorded parent record into the child one-shot' "$repo/agents/skills/maintenance/zcode.md" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ]; then echo "GATE FAIL: recycling-update primary wording still present: $out"; fail=1
elif [ "$rc" -ge 2 ]; then echo "GATE FAIL: grep error on overlay: $out"; fail=1; fi
grep -qF "HOST CAVEAT" "$repo/agents/skills/maintenance/prompt-templates.md" \
  || { echo "GATE FAIL: durable HOST CAVEAT missing from blueprints"; fail=1; }
grep -qF "delete-plus-create" "$repo/agents/skills/maintenance/zcode.md" \
  || { echo "GATE FAIL: operative delete-plus-create path missing"; fail=1; }

# 7. Live-session ladder: execute-plan section, overlay pin, maintenance mirror.
grep -qF "Live-session discovery ladder" "$repo/agents/skills/execute-plan/SKILL.md" \
  || { echo "GATE FAIL: ladder section missing from execute-plan"; fail=1; }
grep -qF "Live-session discovery ladder" "$repo/agents/skills/execute-plan/runtime-contract.md" \
  || { echo "GATE FAIL: ladder pin missing from runtime contract"; fail=1; }
grep -qF "discovery ladder" "$repo/agents/skills/maintenance/SKILL.md" \
  || { echo "GATE FAIL: maintenance discovery arm not mirrored"; fail=1; }

# 8. Refuted-verdict durability claim landed truthfully (the old unscoped sentence is gone).
out="$(grep -nF "carries a matching HOST CAVEAT sentence in its re-arm duty payload" "$repo/agents/skills/maintenance/zcode.md" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ]; then echo "GATE FAIL: unscoped durability claim still present"; fail=1
elif [ "$rc" -ge 2 ]; then echo "GATE FAIL: grep error on overlay verdict line: $out"; fail=1; fi

# 9. Guideline rule 67 and its three obligations (dedicated greps).
grep -qF "## 67. Transcription" "$repo/projects/.ai-playbook/agent_workflow_guidelines.md" \
  || { echo "GATE FAIL: rule 67 heading missing"; fail=1; }
grep -qF "amount+date+merchant" "$repo/projects/.ai-playbook/agent_workflow_guidelines.md" \
  || { echo "GATE FAIL: dedupe obligation missing"; fail=1; }
grep -qF "against its source region" "$repo/projects/.ai-playbook/agent_workflow_guidelines.md" \
  || { echo "GATE FAIL: field-verification obligation missing"; fail=1; }

# 10. Hook decision log: core writes decisions and a daily heartbeat (test-asserted; the
#     test run in gate 2 covers behavior, this grep pins the wiring literal).
grep -qF "hook_outcomes_log" "$repo/agents/hooks/budget-guard/budget_guard_core.py" \
  || { echo "GATE FAIL: decision-log wiring missing from guard core"; fail=1; }

# 11. Dispositions: one dated line per annotated item (per-file gates).
for item in subagent-session-record-persistence-races model-selection-persist-foreign-key \
            hook-outcome-audit-visibility maintenance-friction-audit-lane; do
  f="$repo/docs/history/backlog/2026-09-19-$item.md"
  if ! grep -q "Disposition: 2026-09-19" "$f" 2>&1; then
    echo "GATE FAIL: disposition line missing from $item"; fail=1; fi
done

# 12. Store-level darkness witness in the overlay.
grep -qF "persisted_missing" "$repo/agents/skills/maintenance/zcode.md" \
  || { echo "GATE FAIL: store-level witness missing from overlay"; fail=1; }

if [ "$fail" -eq 1 ]; then exit 1; fi
echo "ALL GATES GREEN"
```

Authoring-time note (rules 19/337): the block was executed against the pre-task tree
(recorded 2026-09-19 ~20:35 local); the FIRST failing gate today is gate 3 (no
authoring-claims wording exists yet), with gates 4, 6, 7, 8, 9, 10, 11, and 12 also red
today for the corresponding missing content, and gates 1, 2, and 5 green today (both suites
pass unmodified; peer commit `20e87544` landed the schema-4 bump mid-authoring at 21:01,
after this block first ran, so gate 5 flipped green after the recorded run: re-verified
2026-09-19 ~22:05). Gates are phrased to flip green exactly when their task lands; each task
below names its own subset for interim runs (rule 16: the multi-path final block runs only
at the final task).

### Task 1: Authoring claim files, G1a discovery arm, and the foreign-claim fire-time gate

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] Authoring blueprint (prompt-templates.md), right after the re-arm duty paragraph and before the fire-time gate: add the claim-file duty in gate-before-write order: FIRST run the foreign-claim check below, and only after it passes write `docs/tmp/authoring-claims/<backlog-item-basename>.md` (frontmatter lines `session:`, `item:`, `created:`, `updated:`); the write is create-if-absent (an O_EXCL-style create that refuses when the file appeared between the check and the write: a file naming a foreign session id at write time is a refusal, a file naming this session's own id is refreshed instead); refresh `updated:` on every plan-file write, immediately before launching each review round, immediately when a review round returns, and at every phase boundary of the pre-plan research (so no active phase can outlast one cadence period without a refresh); delete the claim file at closeout (the done handoff) and on any refusal stand-down this session already owned; a claim left behind decays by freshness, never by trust [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring blueprint fire-time gate extension (runs BEFORE the claim write of the duty above): after the existing merge/rebase/done-lock check, refuse to start when `docs/tmp/authoring-claims/<item-basename>.md` exists with a fresh `updated:` (within one cadence period) naming a session id other than this session's; stand down and write nothing (including no own claim file: the blueprint sentence must carry the span "a second writer must never clobber the first writer's witness", which the plan-level gate pins), reporting the foreign claim's session id and timestamp (the 2026-09-18 automation-343ce2b0 collision is the witness) [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md G1a: give the authoring lane its own discovery arm (today it inherits G1e's by reference): an authoring claim file under the resolved tmp directory's `authoring-claims/` whose `updated:` is fresher than one cadence period occupies the authoring lane UNLESS the state file's pending `children[]` entries explain it: a claim whose item basename matches the target of a pending authoring child entry is that child's own witness (not foreign); a claim whose item matches no pending entry is foreign and occupies the lane (listing records carry no session ids and `children[]` entries carry automation ids, so target-keyed matching against the state file is the only data source the guard has); a stale claim occupies nothing [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md G1e discovery arm and the G1a mirror: name the execute-plan live-session discovery ladder as the execution-side mechanism (wording only; the ladder itself lands in Task 3) [class: IMPLEMENTATION_REQUIRED]
- [x] Overlay (zcode.md): name the concrete claim path and freshness rule in the child-classification markers bullet so the guards' discovery arm and the payloads agree on the literal directory `docs/tmp/authoring-claims/` [class: IMPLEMENTATION_REQUIRED]
- [x] Pins: the claim directory literal in SKILL.md and in the authoring blueprint only, plus an explicit expect-absent pin for `authoring-claims` inside the execution blueprint (an execution payload must never write authoring claim files: a foreign-claim false trip would stall G1a); the claim duty and gate live as separate authoring-blueprint paragraphs, never inside the shared FIRST ACTION span, so the re-arm parity pin is untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite -> expect GREEN: `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `feat: authoring lane claim files and foreign-claim fire-time gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Quota-aware lane decisions and the decision-time quota_at_decision record

Drift note (mandatory pre-step): peer commits `20e87544`, `d0a4ac31`, `e19b996d`, and
`cb73fb87` landed 2026-09-19 21:01-21:33 while this plan was under review, and they already
deliver part of the origin: Step 4's runtime-fit rule (minutes_remaining at the planned fire
time below the lane's expected runtime upper bound, execution 240 minutes / authoring 120
minutes, fires at reset_at_epoch and records the comparison in the lane's decision_reason),
schema 4 (children[] `requested_at` and `quota_status: "deferred-peak"`), and the quota leg
binding every clocked dispatch path. Re-read the landed Step 4 wording and the schema block
before editing. This task delivers the origin's remaining half: the DECISION layer consumes
the quota numbers; the fire-time half is already landed. Reuse the landed constants (240/120
upper bounds); introduce no new constants.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md Step 1 (survey): add the quota snapshot action: run the harness detection then the probe exactly as Step 4 prescribes, and carry the reading (primary window percent used, minutes to reset, source: probe | pricing cache | unknown | skipped-unsupported-harness) into Step 3 as decision input; Step 4 keeps its ENTIRE landed wording AND its own landed probe invocation verbatim (the runtime-fit rule is fire-time-relative and keeps computing its own minutes at the planned fire time; only Step 3 consumes the now-relative survey snapshot; the survey's probe run is an additional reading for the decision layer, so no landed Step 4 literal changes) [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Step 3 (decision): every lane decision records `quota_at_decision` (per lane: status, percent_used, minutes_to_reset) alongside `decision_reason`; add the near-reset branch reusing the landed upper bounds, prescribing this sentence verbatim: when minutes to reset at the realistic start of work is below the lane's expected runtime upper bound (execution 240 minutes, authoring 120 minutes, the Step 4 constants), D1 defers the execution dispatch past the reset and D2 defers the authoring dispatch, each recording the quota reason; in the band where the execution bound does not fit but the authoring bound does (120-240 minutes left), D1 defers while D2 may still dispatch, which is the origin's per-lane bias; above both bounds the lane dispatches and the recorded comparison makes the call auditable; add the fresh-window rule: when the window is fresh (under 25 percent used with well over an hour left) and a lane lands on D3 with dispatchable work available, the `decision_reason` must cite an explicit non-quota reason [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md State file section: schema STAYS 4 (bumped by `20e87544` hours ago; additive keys within the same-day schema do not re-number it): add `quota_at_decision` to the schema block with its per-lane shape (status, percent_used, minutes_to_reset), and add one Revisions ledger line recording the same-day additive extension on top of the landed schema-4 fire-time bookkeeping [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md Quota leg: one sentence noting the survey-time snapshot is the decision-layer input and this leg remains the fire-time application (the landed runtime-fit, pricing, horizon, and starvation rules are unchanged and keep their constants) [class: IMPLEMENTATION_REQUIRED]
- [x] Pins: add the `quota_at_decision` key check to the EXISTING schema-4 block in `scripts/check_maintenance_pins.sh` (the `!= 4` assertion is already landed; do not touch or duplicate it) and a Step 3 needle for the fresh-window rule's anchor phrase [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite -> expect GREEN: `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `feat: quota-aware lane decisions with recorded quota_at_decision` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Live-session discovery ladder (execute-plan, runtime contract, maintenance mirror)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/maintenance/SKILL.md`

- [x] execute-plan SKILL.md: add a `## Live-session discovery ladder` section (after the Runtime-neutral execution contract section, before Phase 0): before taking over or duplicating in-flight work on a plan (resuming an interrupted run, relaunching after the Step 3.1 timeout, any peer-collision suspicion), answer liveness in order: first the driver claim check (consult the machine manifest via the driver when `runtime_state.json` exists for the run); second the session-manifest heartbeat (`manifest.md` `updated:` and the review log mtime within the Step 3.1 20-minute window) plus the expected staging doc's presence; last, only when neither repo-scoped signal exists, a process scan, and the report must state the reason in one sentence ("no repo-scoped liveness signal exists for a manifest-only run") [class: IMPLEMENTATION_REQUIRED]
- [x] Same section: the manifest-only deviation cost note: a run that deliberately skips the machine manifest has no driver claim check (rung 1 unavailable); when that deviation is chosen, the session manifest records it, so the run weighs the lost claim check explicitly [class: IMPLEMENTATION_REQUIRED]
- [x] runtime-contract.md: pin the ZCode mechanism under a `Live-session discovery ladder` heading: the concrete claim-check script `scripts/execute_plan_runtime.py` and manifest path shapes, the heartbeat window, and the process-scan-last-with-stated-reason rule (the same way the maintenance overlay pins scheduling primitives) [class: IMPLEMENTATION_REQUIRED]
- [x] maintenance SKILL.md: the Step 2 G1e discovery arm cites the execute-plan live-session discovery ladder by name (replacing the bare "mechanism named in the runtime overlay" pointer; Task 1 already mirrored the G1a side) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite -> expect GREEN: `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `feat: repo-scoped live-session discovery ladder for execute-plan and the guards` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Recycling demoted to verified-only; durable HOST CAVEAT; verdict-line truth

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] Overlay ladder step 2 rewrite: delete-plus-create is the operative path (confirm the recorded record's form with at most one listing per the existing rules, delete it in whatever form it then has, create the child one-shot; the rollback, ambiguous-outcome carve-out, retry cap, and dark-loop path carry over unchanged); the recycling update call is demoted to an optimization leg that may run only after a live-verified flip is recorded in the verification section, and the update-refusal convergence language is removed with it [class: IMPLEMENTATION_REQUIRED]
- [x] Both blueprints' re-arm duty paragraphs (identical edits, parity preserved inside the pinned paragraph span): step (1) and step (3) recycling language gains the durable HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, the intended recurring value, a future `nextRunAt` confirmed by a listing) is treated as a refusal and takes the delete-plus-create path; register the caveat in prompt-templates.md's deviations list [class: IMPLEMENTATION_REQUIRED]
- [x] Execution blueprint successor duty primary leg: add the same verifiable-echo-or-delete-plus-create caveat to the reshape leg (its fallback already exists; an unverifiable echoed record counts as refused); register this successor-caveat edit in prompt-templates.md's deviations list alongside the re-arm caveat entry [class: IMPLEMENTATION_REQUIRED]
- [x] Overlay verification section: record the child-to-parent and completed-record-reshape directions per the recipe (unverified, dated 2026-09-19) and replace the REFUTED parent-to-child verdict line's final sentence with the landed truth: the durable HOST CAVEAT now lives in both blueprints (this plan), superseding the one-off assembled payload of the witnessing turn; close `2026-09-19-host-caveat-durability-claim-scope.md` together with the recycling item per its instruction [class: IMPLEMENTATION_REQUIRED]
- [x] Live probe verification, conditional: when the executing session is an unbound chat, run the recipe's throwaway probe for the child-to-parent direction and record the dated verdict; when the session is automation-born (a scheduled child is expected to be), record `verifier-session-bound: not attempted (recipe requires an unbound chat)` in the verification section and leave the direction unverified with delete-plus-create operative; the MIXED-verdict disposition is recorded in the same section so every probe outcome maps to a termination: a verified child-to-parent flip (with the HOST CAVEAT still in force) re-enables only the re-arm duty's recycling legs, the ladder keeps delete-plus-create operative, and the recycling item closes on the dated mixed record as its acceptance resolution (parent-to-child refuted, child-to-parent verified-with-caveat, operative paths stated per leg); an unverified or refused outcome keeps delete-plus-create as the only operative path with the residual tracked under Ship when [class: REPOSITORY_TEST]
- [x] Pins: replace the `ladder recycling needle` pin's literal with the operative delete-plus-create needle; rewrite the `hand-off proceed refusal bound` pin, whose pinned literal (the update-refusal convergence sentence) dies with the recycling primary path: pin the operative path's refusal wording instead, or drop the pin when no successor sentence carries the semantics, recording which in the pin comment; add the caveat needle for both blueprints (parity-safe); add an expect-absent pin for the demoted update-as-primary wording [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite -> expect GREEN: `bash scripts/check_maintenance_pins.sh` [class: REPOSITORY_TEST]
- [x] Commit: `feat: delete-plus-create operative dispatch path with durable HOST CAVEAT` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Transcription cross-check-before-write guideline rule

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md`

- [x] Add rule `## 67. Transcription and Data-Entry Writes: Cross-Check Before Write` with the three obligations as numbered clauses: (a) dedupe source-identical entries on the schema-equivalent identity key (for line items: amount+date+merchant) before any write; (b) verify each written field against its source region by re-reading the source at write time, never from memory of the source; (c) for repeated workflows, persist canonical values in the project facts document and copy from there instead of re-deriving; name the load trigger (transcription-shaped tasks: forms, invoices, summaries over extracted data) and cite the 2026-09-19 corrections-mining witnesses [class: IMPLEMENTATION_REQUIRED]
- [x] Run a dedicated grep per obligation (the plan-level Validation Commands gate 9 covers all three) -> expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: transcription cross-check-before-write guideline rule 67` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Hook outcome self-logging in the repo-owned budget-guard core

Files:
- `agents/hooks/budget-guard/budget_guard_core.py`
- `agents/hooks/budget-guard/README.md`
- `scripts/test_budget_guard_hooks.py`

- [x] `budget_guard_core.py`: add a rate-limited decision log at `~/.ai-playbook/runtime/hook-outcomes.log` (JSON lines: ts, hook id, event, decision, duration_ms): block decisions and errors always append; allow decisions append at most one heartbeat line per hook per day (first invocation of the day); an error line carries the failure kind, the message text, and the exit code the invocation returns (the fail-open 0; the host-side attachment of stderr tails and exit codes to `hook.run.failed` records remains the external prerequisite already under Ship when); the producer of the error class is an exception-guard around the core's decision path: an unexpected exception there appends the error line and still fails open (decision unchanged), and the guard's failure point is injectable via a fault-injection parameter in the same style as the log-path and day-source parameters, so the test can induce the erroring invocation; the log write is best-effort and never changes the hook's own decision or exit code (fail-open unchanged); the log path is resolvable via a parameter (default the home path) and the day source via the same seam style as `scripts/review_record_selection.py`'s `DATE_SOURCE` (module-level date callable, frozen by its suite), so the test can pin both [class: IMPLEMENTATION_REQUIRED]
- [x] `budget_guard_core.py`: the heartbeat append, the block/error appends, AND the already-today rate check (the read that decides whether the day's heartbeat line exists) run under the shared guard lock helper (`_shared_guard_lock`) so a same-day second invocation cannot interleave a duplicate heartbeat line or a doubled rate check; a lock-acquisition failure degrades to a skipped log line, never a changed decision [class: IMPLEMENTATION_REQUIRED]
- [x] `test_budget_guard_hooks.py#test_decision_log_appends_blocks_and_daily_heartbeat`; given an isolated temp HOME and two invocations where the first blocks and the second allows on the same injected day, expects one block line plus exactly one allow heartbeat line, and given the injected day advancing between invocations, expects a second heartbeat line (the day-rollover assertion over the injected day source), and given the fault-injection seam forcing the decision-path guard to raise, expects an error line carrying the failure kind and message while the decision stays the fail-open allow with exit 0, and given the lock helper stubbed to refuse acquisition, expects the decision unchanged and no log line appended [class: REPOSITORY_TEST]
- [x] `agents/hooks/budget-guard/README.md`: one line documenting the decision-log path, the line shapes (block, error, daily heartbeat), and the fail-open degradation [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED then GREEN around the implementation: `python3 scripts/test_budget_guard_hooks.py` [class: REPOSITORY_TEST]
- [x] Commit: `feat: rate-limited decision log and daily heartbeat in budget-guard core` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Dispositions for host-owned residuals and the friction-audit-lane deferral

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`
- `docs/history/backlog/2026-09-19-subagent-session-record-persistence-races.md`
- `docs/history/backlog/2026-09-19-model-selection-persist-foreign-key.md`
- `docs/history/backlog/2026-09-19-hook-outcome-audit-visibility.md`
- `docs/history/backlog/2026-09-19-maintenance-friction-audit-lane.md`

- [x] Overlay: add the store-level darkness-triage witness (runtime-specific, so the overlay): when classifying a silent or dark turn, read the app logs for session-store integrity events around the child's run window (`zcode_protocol.session.persisted_missing`, hydrate/loadPersistedEvents failures): a cluster distinguishes "child outlived its parent record" (store race) from "the parent actually died"; SKILL.md's failure-detection section gains one sentence pointing at the overlay's store-level witness [class: IMPLEMENTATION_REQUIRED]
- [x] Annotate `2026-09-19-subagent-session-record-persistence-races.md` with a dated `Disposition:` line: the persist-before-teardown ordering, hydrate retry, and resume-guard fixes are ZCode application code (external prerequisites, see this plan's Ship when); the repo-side watch is the overlay's store-level darkness witness [class: IMPLEMENTATION_REQUIRED]
- [x] Annotate `2026-09-19-model-selection-persist-foreign-key.md` with a dated `Disposition:` line: the FK-ordering fix or write removal is ZCode application code (external prerequisite); the repo keeps the item open as the signal's record [class: IMPLEMENTATION_REQUIRED]
- [x] Annotate `2026-09-19-hook-outcome-audit-visibility.md` with a dated `Disposition:` line: the repo-owned half (budget-guard decision log and daily heartbeat) landed via this plan's Task 6; the host-side halves (`hook.run.failed` enrichment, host-level heartbeat) are external prerequisites [class: IMPLEMENTATION_REQUIRED]
- [x] Annotate `2026-09-19-maintenance-friction-audit-lane.md` with a dated `Disposition:` line: deferred to its own future plan (a new audit lane with watermark state and a quantitative script exceeds the two-plan split budget of the 2026-09-19 liveness-residuals dispatch); trigger: the next authoring lane slot; the item stays open [class: IMPLEMENTATION_REQUIRED]
- [x] Run the plan-level Validation Commands end to end -> expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `docs: dispositions for host-owned scheduler residuals and audit-lane deferral` [class: IMPLEMENTATION_REQUIRED]
