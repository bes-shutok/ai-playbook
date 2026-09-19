# Plan: maintenance scheduler liveness: selection-loop and dispatch guarantees

Origin backlog (scope of record, read fully): `docs/history/backlog/2026-09-15-maintenance-rearm-action-selection-loop.md`, `docs/history/backlog/2026-09-16-scheduler-dispatch-fallback.md`, `docs/history/backlog/2026-09-15-maintenance-authoring-lane-chaining-gap.md`, `docs/history/backlog/2026-09-15-maintenance-indefinite-operation.md`, `docs/history/backlog/2026-09-15-maintenance-paused-execution-resume.md`, `docs/history/backlog/2026-09-16-successor-chaining-after-plan-completion.md`, `docs/history/backlog/2026-09-15-maintenance-review-r4-polish-residue.md`. Queue context: `docs/tmp/future-plan-prompts-2026-09-16.md` (P1). Driving principles: repo guidelines section 64 (efficiency, token usage, simplicity, code quality, quality never priced at zero).

Historical note (2026-09-18, P12): this plan is an executed historical record, archived as-is; the landed skill files (`agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/zcode.md`, `agents/skills/maintenance/prompt-templates.md`) are authoritative wherever its quotes have gone stale versus the landed r3/r4 fixes. Stale quotes: Task 1's field-semantics checkbox still names a re-arm write in the `parent_absent_since` clearer list, which the landed r4 fix dropped (the ENABLED-match clear suffices); Task 1's state-file arm still joins a pending `children[]` entry by a matching `created_at`, where the landed join is the entry's `(idle)` target marker; the idle-lane per-session attribution bullet counts only own-session tasks as lane blockers, where the landed rule adds the alternative arm for a task a pending `children[]` entry records; Task 4's Step 0 sentence is the superseded listing-first wording, annotated in place under the Task 4 heading below; and the Design Invariants writer-mode list omits the turn's hand-off refusal rearm_note write mode and describes `pending_dispatch` / `parent_absent_since` as written by non-Step-6 actors, where the landed scoping says they are written outside Step 6 by the turn's own earlier steps or by touch sessions. Also stale: the witness table's row 3 probe claim `decision_reason records the release` is not an explicit landed record duty; the duty actually landed as SKILL.md's early authoring outcome check in "Failure detection and the failure cap", which records `outcome: progress` plus `outcome_checked_at` on observe.

## Terms

- **Scheduler turn / deciding turn**: one run of the maintenance skill (Steps 0-6); the deciding turn is the turn whose D1/D2 decision produced a given child.
- **Child**: a dispatched session; kind `execute` or `author`. Its **spawner record** is the automation record the deciding turn (or a manual dispatcher) created for it; the child session is bound to that record.
- **Re-arm**: restoring the recurring parent automation after the dispatch ladder left it absent or in child form. **Recognition rule**: title "Maintenance scheduler turn (every 2 hours)" plus prompt opening "You are the maintenance scheduler for the repository at", with the resolved repository root contained in the prompt.
- **Record recycling**: reshaping an existing automation record with the update primitive (CronUpdate) instead of delete-plus-create. **Record oscillation**: the single record's lifecycle under this plan; it alternates between parent form (recurring scheduler payload) and child form (one-shot child payload) while keeping one id; `parent_automation_id` names the record in either form, and a pending `children[]` entry carrying that id means child form.
- **Lane guards `G1e` / `G1a`**: execution and authoring lane occupancy guards. **State file**: `.ai-playbook/scheduler-state.json` (gitignored; schema of record in SKILL.md).
- **Progress predicate (authoring)**: a top-level plan now references the target item, or the item left the backlog top level. **Certification oracle**: `python3 scripts/plan_readiness.py <plan>` exit status.
- **`pending_dispatch`**: state-file record of a decided-but-unscheduled dispatch (kind, target, payload slug, decided_at).
- **Selection-loop signature**: the action-selection loop on automation primitives; repeated identical read-only listings without advancing to the mutating step (witnessed 4+ times 2026-09-15).

## Assumptions

- assume SKILL.md stays runtime-agnostic: primitive names appear only in the zcode.md overlay and the pins suite; basis: existing structure and the pins check that fails SKILL.md naming a runtime primitive.
- assume the state file schema bumps 2 to 3; no script parses the live state file (grep verified 2026-09-16), only the pins suite validates the schema block; basis: repo grep this session.
- assume the update primitive's recurring flip (false to true and true to false) and completed-record re-enable are UNVERIFIED platform behavior; every recycling path therefore carries a fully specified delete-plus-create fallback, and a fresh-session verification recipe records the verdict as a dated "verified live" marker; basis: origin 1's explicit "Requires: verify" plus the 2026-09-16 cap-model refinement.
- assume child sessions may lack the clocked mutating primitives entirely (witnessed 2026-09-16: an automation-born authoring session exposed only read-only automation primitives plus the idle-time create); every duty degrades through the fallback chain to the state file record and never hard-depends on one primitive; basis: this authoring session's toolset plus the contradicting witnesses in the origins.
- assume one plan covers all seven origins; basis: the P1 dispatch prompt.
- assume the review loop runs to a fresh blind ready=yes with zero blocking findings, cap 5 total rounds, the two regenerating classes defer to backlog (ADR-0002); basis: standing rules in the P1 prompt file.
- assume the user-level session-start instruction surface (indefinite-operation FIX-2 third surface) is outside this repo's scope and ships as prose under Ship when; basis: repo-public hygiene rule against personal paths in skill files.

Decision points requiring a grill: guarantee model: state-machine liveness, the state file is the source of record and every fix lands a probe-checkable field while listings only verify; source: dispatch-prompt standing pre-authorization plus seven-origin convergence (rearm candidate 2, dispatch-fallback pending record, authoring-lane recorded-on-observe checks, indefinite-op FIX-6, paused-resume progress_mark); decided 2026-09-16; affects Tasks 1-3. re-arm placement: stays FIRST ACTION but as a single deterministic state-driven recycling duty (relocating it to LAST ACTION would break the child-restores-parent invariant for children that die mid-run, witnessed by the 429-killed child); source: standing pre-authorization accepting the recommendation, origin-1 preference order; decided 2026-09-16; affects Task 3. launchd external heartbeat (indefinite-op FIX-3 variant 1): deferred, the existing idle-time watchdog plus rearm-on-touch cover the detector gap without new launchd infrastructure; source: standing pre-authorization accepting the recommendation per guidelines section 64 simplicity; decided 2026-09-16; affects Ship when.

## Gist & Examples

The maintenance loop is the queue now: it executed four plans and certified two more in one day (2026-09-15), and then broke five ways in the same day. The user's standing demand is indefinite operation. Every witnessed failure is a liveness failure: the loop going dark or a lane not chaining.

**Before (today), one 2h cycle:** the deciding turn deletes the parent and creates the child with two gated mutating calls (a cap-refusal dance); the child's FIRST ACTION re-arm is listing-driven ("list, and if no parent, list once more, then create"), and each listing echoes the list-then-create instruction back into the context, so sessions emit 4 to 20 identical listings and never mutate; the dispatch is simply lost and a full cycle produces no child. When a child does run and finishes early, the authoring lane stays closed for up to ~5 more hours (the 6-hour outcome horizon sized for execution children), an execution completion idles the lane up to 2 hours until the next parent fire (children are forbidden to dispatch successors), and a plan paused mid-run by a context boundary makes no countable progress (only archival counts), so a legitimate three-session plan false-trips the failure cap.

**After (this plan), the same cycle:** the deciding turn reshapes the one record with a single ungated update call (parent form to child form, same id); the child's FIRST ACTION reads the state file and acts state-first: the primary path performs one mutating update with no listing at all, the recovery paths list at most once to decide and never a second time before a mutation, and an explicit loop guard stops any listing run; a trapped turn writes `pending_dispatch` so the next turn dispatches mechanically, and the authoring lane falls back to the ungated idle-time primitive immediately. A finished authoring child releases its lane as soon as its plan passes the certification oracle; a paused execution plan books checkbox progress (`progress_mark`) so no failure credit accrues and the next turn re-dispatches it as a resume run; a completing execution child chains the successor by recycling its own record into the next one-shot, arming the next plan within minutes instead of the next 2h fire.

**Witness-to-fix-to-probe map** (every fix is witnessable by a state-file probe):

| Witnessed failure | Fix | State-file probe |
|---|---|---|
| rearm action-selection loop (4+ witnesses; parent dark 19:15-23:2xZ) | state-driven recycling rearm duty, anti-loop guard (Task 3) | `parent_automation_id` set after first action; `rearm_note` stays null |
| dispatch lost when the ladder traps (2 full cycles) | `pending_dispatch` record + idle-time fallback for the authoring lane (Tasks 1-2) | `pending_dispatch` set on trap, cleared on the next turn's mechanical dispatch |
| authoring lane idles up to ~5h per finished child | early progress check past `fire_at` + certified-release arm (Task 1) | `outcome: progress` with `outcome_checked_at` recorded on observe; `decision_reason` records the release |
| paused execution never resumed; honest plans false-trip the cap | checkbox `progress_mark`, fast re-dispatch, RESUME sentence, `resume_count` (Tasks 1, 3) | `progress_mark` increases; `resume_count` increments; `consecutive_failures` stays 0 across pauses |
| completed plan idles the lane up to 2h (2 witnesses 2026-09-16) | successor chaining via record recycling with an exactly-one carve-out (Task 3) | new pending `children[]` entry (kind execute) whose `created_at` is within minutes of the closeout |
| cap refusals from lingered spawner records (r4 item 8) | linger deletion on the create path; recycling removes recurring-path creates entirely (Tasks 2-3) | `rearm_note` names a recycling refusal only on the fallback path |
| detectors that cannot fire (RC5) | `parent_absent_since` + rearm-on-touch (Step 0 and done skill) + watchdog wording (Tasks 1, 2, 4) | `parent_absent_since` set when dark and cleared when armed; the done-skill check line is pinned |

**Edge cases:** a child that dies before its re-arm leaves the record in child form; the darkness readers are the watchdog, the staleness rail, `parent_absent_since` age, and every rearm-on-touch session. A capped session performs no create at all on the primary paths. A fresh (unbound) session keeps the direct-create path. When the update primitive withholds the flip, the refusal falls through to the delete-plus-create recipe and the `rearm_note` records it for the corpus. When no open plan remains, the successor duty chains nothing and the parent legitimately idles the lane.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `bash scripts/check_maintenance_pins.sh` exits 0; every mutating duty path has a named fallback; the schema block validates as schema 3 with the new fields.
- liveness: each of the seven origin witnesses maps to a fix and a state-file probe (the table above is complete; a reviewer can trace every row to a task).
- token usage: steady-state re-arm duties perform zero listings before mutation and at most one after (the successor duty's chain-nothing precondition listing is the sanctioned exception); the recycle paths remove all gated creates from recurring dispatch.
- simplicity: no new scripts, no new runtime surfaces; net automation-primitive calls per cycle decrease; outdated ladder wording is rewritten, not accumulated.
- code quality: `bash -n` clean on the pins suite; the pins script ends with a newline; no em-dashes in touched files.

**Done when:**
- all task checkboxes checked; the full Validation Commands block exits 0 on the final tree.
- the schema block in SKILL.md parses as JSON with `"schema": 3` and the fields `parent_absent_since`, `pending_dispatch`, `progress_mark`, `resume_count`.
- the two re-arm duty paragraphs in prompt-templates.md are identical after whitespace normalization and contain the recycling-first decision table and the loop guard.
- the done skill carries the rearm-on-touch line and SKILL.md Step 0 carries the runtime-agnostic rearm-on-touch sentence.

**Ship when:**
- a first live cycle exercises recycling in both directions (turn-to-child and child-to-parent) and the outcome (or the fallback refusal) is recorded as a dated "verified live" note next to the verification recipe in zcode.md, per the repo's platform-fact pattern.
- the fresh-session flip-verification recipe documented in Task 2 has been run once by an unbound session and its verdict recorded.
- the human applies the user-level session-start rearm-on-touch line outside this repo; exception confirmed by user: the P1 dispatch prompt's standing pre-authorization (accept all recommended options, 2026-09-16) covers landing the plan with the two in-repo surfaces only; why executable now: the scheduler Step 0 check and the done-skill line already heal the loop on every touching session, so the third surface is defense-in-depth, not a launch blocker; completion evidence: the applied user-level line confirmed at closeout, or an explicit waiver recorded in the completion report.
- the origin witnesses reproduce unattended: a paused plan completes across two dispatched children with zero human intervention, and a completed plan's successor is armed within minutes by the completing child.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/done/SKILL.md` *(one-sentence rearm-on-touch insertion only; all other sections frozen; reject any review finding that touches them)*

**Tests:**
- `scripts/check_maintenance_pins.sh`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/` and `scripts/execute_plan_runtime.py`; reason: the resume path and manifest contract are consumed as-is; this plan only adds the payload sentence that points at them.
- `agents/hooks/` and `scripts/quota_window_probe.py`; reason: consumed as-is; no hook or probe behavior changes.
- any file under the user home outside the repo (user-level session-start instructions); reason: external surface, ships via Ship when.
- `docs/history/backlog/` origin files; reason: they are the immutable scope of record; they move to `completed/` only at plan completion per the plans skill lifecycle.

## Design Invariants (CR Guard)

- SKILL.md stays runtime-agnostic; the pins check that fails SKILL.md naming a runtime primitive must keep passing (primitive names live only in the overlay and pins suite).
- The two lanes stay independent; executions are strictly sequential; the execution lane is never dispatched through a primitive without a clock.
- The state file's writer classes are enumerated (five): scheduler turns (whose own write modes are the Step 6 full rewrite, the Step 1 outcome-check updates, the mid-ladder trap Bash edits writing `pending_dispatch` and `turn_error`, the mid-ladder listing-confirm dispatch edits (children[] append), the turn's Step 0 adopt/set-clear edits (including the rearm_note clear when the listing shows the parent armed again), the loop-guard rearm_note write, the Quota-leg pricing_cache update plus its repo-matching pricing-note deletion, the dispatch-discipline stand-down turn_error write, and the Step 1 reader edits (pending_dispatch clear/retain, memory-note adoption)), a child's re-arm FIRST ACTION targeted edits, the idle-time watchdog targeted edits, the completing execution child's successor-dispatch targeted edits (children array append plus the successor duty's parent re-create field edits, Task 3), and rearm-on-touch sessions (Task 4; targeted edits to `parent_automation_id`, `parent_absent_since`, the `rearm_note` write the loop-guard fallback requires, and the `rearm_note` clear when the recipe re-arm succeeds). Every child, watchdog, and touch-session write stays a targeted field edit through a temp file plus atomic replace. The Step 6 full rewrite carries forward every field the turn does not own: `parent_automation_id`, `rearm_note`, successor-appended `children[]` entries, and `pending_dispatch` / `parent_absent_since` written by non-Step-6 actors.
- Anti-runaway bound: a child performs exactly the re-arm duty and (execution children only) exactly one successor dispatch, whose authorized mutations are the successor reshape, its stated fallback delete-plus-create leg, and the parent re-create on the both-legs-fail path; no other child-initiated automation mutation is authorized; the carve-out sentence in the execution blueprint is the only authorization text.
- Never push to origin; never block on questions in unattended duties.
- Documentation minimality: superseded ladder and duty wording is rewritten in place, not duplicated; the archived plans' pinned v1 wordings stay historical.
- Review-loop shape per ADR-0002: cap 5 total rounds; the two regenerating classes defer to backlog; fold cheap Lows until zero findings.

## Validation Commands

```bash
set -u
repo="$(git rev-parse --show-toplevel)" || { echo "not in a repo"; exit 1; }
fail=0
run() { if ! "$@"; then echo "GATE FAIL: $*"; fail=1; fi; }
expect_pin() { # expect_pin <pattern> <file>: positive presence, fail-closed
  if ! grep -qF -- "$1" "$2"; then echo "GATE FAIL: missing pin span in $2: $1"; fail=1; fi
}
expect_no_match() { # expect_no_match <pattern> <file>: rc 0 fails, rc 1 passes, rc >= 2 aborts
  out="$(grep -nF -- "$1" "$2" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "GATE FAIL: forbidden span present in $2: $1"; fail=1
  elif [ "$rc" -ge 2 ]; then echo "GATE FAIL: grep error on $2: $out"; fail=1; fi
}

S="$repo/agents/skills/maintenance/SKILL.md"
Z="$repo/agents/skills/maintenance/zcode.md"
P="$repo/agents/skills/maintenance/prompt-templates.md"
D="$repo/agents/skills/done/SKILL.md"
PIN="$repo/scripts/check_maintenance_pins.sh"
for f in "$S" "$Z" "$P" "$D" "$PIN"; do
  [ -f "$f" ] || { echo "GATE FAIL: missing $f"; fail=1; }
done

# 1. mechanical pins suite (schema 3 block, parity, needles, counts, runtime-agnosticism)
run bash "$PIN"
run bash -n "$PIN"

# 2. state-machine fields landed in SKILL.md (Task 1)
expect_pin "parent_absent_since" "$S"
expect_pin "pending_dispatch" "$S"
expect_pin "progress_mark" "$S"
expect_pin "resume_count" "$S"
expect_pin "checked-checkbox count" "$S"
expect_pin '\[[xX]\]' "$S"
expect_pin "timestamp older than one cadence period" "$S"
expect_pin 'lifecycleStatus` is completed or `enabled` is false' "$S"
expect_pin "rearm-on-touch check: consult the scheduler state file first" "$S"

# 3. oscillation ladder and fallbacks in the overlay (Task 2)
expect_pin "update the recorded parent record into the child one-shot" "$Z"
expect_pin "Automation primitive verification" "$Z"
expect_pin "deleting your own lingered" "$Z"
expect_pin " sessionId matches the current session" "$Z"
expect_pin "clears the pricing-verification-failed note" "$Z"
expect_pin "note surfaces in the survey read-back" "$S"
expect_pin "treat the child as dispatched" "$Z"
expect_no_match "sessions whose spawner automation has completed are not blocked" "$Z"

# 4. child blueprints: re-arm table, successor carve-out, resume rule (Task 3)
expect_pin "state-first, without listing first" "$P"
expect_pin "listed twice without a mutating step" "$P"
expect_pin "beyond the re-arm duty below and the single successor-dispatch duty below" "$P"
expect_pin "SUCCESSOR DISPATCH" "$P"
expect_pin "this is a resume run" "$P"
expect_pin "counts as success only after one more listing confirms" "$P"
expect_pin "fall back to deleting your own spawner record whatever its current form" "$P"
expect_pin "when both legs fail" "$P"
auth="$(cat "$P")"
n_succ="$(printf '%s' "$auth" | grep -cF "SUCCESSOR DISPATCH")"
if [ "$n_succ" -ne 1 ]; then echo "GATE FAIL: SUCCESSOR DISPATCH appears $n_succ times, want 1 (execution blueprint only)"; fail=1; fi

# 5. rearm-on-touch surfaces (Task 4)
expect_pin "rearm-on-touch check defined in the maintenance skill" "$D"

# 6. forbidden patterns: the old listing-driven rearm wording must be gone (negated, rc-aware)
expect_no_match "list once more immediately before the create" "$P"

# 7. format gate on every touched path
run env CHECK_NO_EM_DASH_ALL=1 bash "$repo/scripts/check-no-em-dash.sh" file "$S" "$Z" "$P" "$D" "$PIN"

if [ "$fail" -ne 0 ]; then echo "validation: FAIL"; exit 1; fi
echo "validation: all gates green"
```

Notes: the `expect_no_match` sweeps target skill files, never this plan, so no bracket-escape is needed (the plan's own quoted spans are checker literals, not file content). Gate 6's pattern is the superseded rearm wording; it must be RED at authoring time (it is present today) and GREEN only after Task 3 lands, which is the intended flip. RED-today execution record (2026-09-16, this authoring run): the block exits 1; gate 1 (pins suite) passes as-is; the FIRST failing gate is gate 2 (`parent_absent_since` missing from SKILL.md), the intended Task 1 flip; gate 6 fires as designed; gate 7 also fails today by design (the four em-dash lines below), turning green only when Tasks 1-2 fold them. The no-em-dash scanner prints only the first matching line per file, so the authoring run's first execution undercounted: measured with `grep -c` the touched files carry four em-dash lines, two in SKILL.md (the idle-children bullet and the 2026-09-16 compaction Revisions entry) and two in zcode.md (the cap paragraph and the session-compaction bullet); all four sit inside spans Tasks 1-2 rewrite and are folded there. Every other failure is a missing Task 1-4 span, all intended flips.

### Task 1: state schema v3 and SKILL.md liveness semantics

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add pins to `scripts/check_maintenance_pins.sh` (RED first): schema `3`; `decision`/`decision_reason` per-lane keys and `pricing_cache` fields unchanged; children entries carry `progress_mark` and `resume_count`; top-level `parent_absent_since` and `pending_dispatch` present; the release-arm needle `certification oracle` in the G1a arm text; the checkbox-progress needle `checked-checkbox count`; the `pending_dispatch` reader needle in the Step 1 list; the `parent_absent_since` needle; a RED-first pin on the corrected checkbox regex literal `\[[xX]\]` present in SKILL.md's failure-detection text (no gate may be unable to distinguish the broken unbracketed class from the corrected one); the stop-evidence needle `timestamp older than one cadence period` (the manifest-staleness conjunct that prevents replacing a live child); the enabled-only arms needle `lifecycleStatus\` is completed or \`enabled\` is false`; the writer-classes wording flips to `five sanctioned writer classes`. Pin reconciliation for this task: the superseded `three sanctioned writer classes` pin is removed in the same edit; the existing `null \`fire_at\`` arm span must survive the reworded arms (Task 1's arms bullet keeps the idle-child clause). Run the suite; expect exactly the new pins failing (schema still 2, fields absent).
- [x] Rewrite the `## State file` section: schema 3 JSON block exactly:

```json
{
  "schema": 3,
  "last_run_at": "<iso8601>",
  "parent_automation_id": "<id or null>",
  "parent_absent_since": "<iso or null>",
  "pending_dispatch": null,
  "survey": {"open_backlog": 0, "open_plans": 0, "digest_intact_plans": 0},
  "decision": {"execution": "execute|noop", "authoring": "author|noop"},
  "decision_reason": {"execution": "<short reason>", "authoring": "<short reason>"},
  "pricing_cache": {"peak_window": "<pinned window>", "multipliers": "<pinned multipliers>",
     "last_verified": "<iso date>", "source": "<notice url>"},
  "turn_error": null,
  "rearm_note": null,
  "children": [
    {"automation_id": "<id or null for idle-time>", "kind": "execute|author",
     "target": "<path or <path> (idle)>", "created_at": "<iso>", "fire_at": "<iso or null>",
     "quota_status": "ok|unknown", "outcome": "pending|progress|failed",
     "outcome_checked_at": "<iso|null>", "progress_mark": null, "resume_count": 0}
  ],
  "consecutive_failures": 0,
  "consecutive_turn_errors": 0,
  "alert": null
}
```

- [x] Add field semantics paragraphs: `parent_absent_since` is set when the absence is first observed (the transition from a listing that showed an ENABLED recognition match, or from a null field, to a listing that shows none writes that observation's timestamp), keeps the earliest value while the absence persists and is never refreshed to a later observation's timestamp, and is cleared only by a listing showing an ENABLED recognition match or a re-arm write; absence with a pending child entry carrying `parent_automation_id` is expected surrender (record oscillation child form); a pending child entry explains the absence only while it is live, meaning its `fire_at` (or `created_at` for idle-time) is fewer than six hours past with no failed outcome: a ghost pending record past that horizon does not suppress the darkness classification, mirroring the human check's six-hour rule, so a never-fired record cannot silence automated finders indefinitely; absence with no live pending child and `parent_absent_since` older than one cadence period (2 hours) is darkness, and an automated finder (turn Step 0 or a rearm-on-touch session) re-arms per the overlay recipe instead of only noting. `pending_dispatch` is an object `{"kind": "execute|author", "target": "<path>", "payload_slug": "<blueprint id>", "decided_at": "<iso>"}` or null; written by a turn that decided but could not schedule; read at Step 1.
- [x] Rewrite `## Failure detection and the failure cap`: (a) early authoring outcome check: every pending authoring child whose `fire_at` has passed (idle-time: once the idle-task listing no longer shows it queued or running) gets the progress predicate evaluated each turn and `outcome: progress` plus `outcome_checked_at` recorded on observe; the 6-hour horizon stays the failure threshold for children that never show progress; (b) execution-child progress becomes "the target plan left the top-level plans directory (archived), or the target plan's checked-checkbox count increased beyond the recorded `progress_mark`"; the checkbox count is stored in `progress_mark` at every survey turn while the child is pending (one grep per turn) and at each outcome check, counting with `grep -cE '^[[:space:]]*-[[:space:]]\[[xX]\]' <plan>` (the escaped literal brackets are load-bearing: an unbracketed `[xX]` class matches the bare letter after the dash-space and never matches a `- [x]` line; measured at authoring: 0 matches on pure checked-checkbox lines vs 2 for the corrected pattern); progress resets `consecutive_failures` exactly as archival does, so a multi-session plan never false-trips the cap; (c) fast re-dispatch with a single sound trigger, aligned with the release arms: a pending execution child is fast-re-dispatched when BOTH hold, progress evidence (its checkbox count exceeds the `progress_mark` stored at the previous turn, or its outcome is already `progress`) and stop evidence (the execute-plan session manifest under the resolved tmp directory (facts key `tmp_dir`, `docs/tmp/` default) at `execute-plan/<plan-slug>/manifest.md` carries an `updated:` timestamp older than one cadence period; a live child refreshes the manifest on every orchestrator update, so the staleness conjunct is what prevents re-dispatching a live child that is merely between manifest writes) AND a negative live-session check: the re-dispatch goes through the Step 5 lane-guard re-evaluation with the discovery arm (the execute-plan claim check) mandatory before the replacement dispatch, so a live child whose manifest gap exceeded one cadence period is caught by the claim check, not replaced; the re-dispatch replaces the old child record with the new entry (same target, new `created_at`, `resume_count` incremented on the new entry) so two records for one plan never coexist, and accrues no failure credit when the progress evidence held; the fresh child enters via the existing PRE-STEP re-cert and the payload's resume rule (Task 3); (d) the provider-429 requeue exception and the idle-children coverage carry over semantically unchanged; their sentences are reworded only by the em-dash fold below.
- [x] Reword the `G1e` / `G1a` state-file arms in Step 2 to the release rules: a recorded child holds its lane while `fire_at` has not elapsed, or while its 6-hour horizon has not elapsed and (outcome is `pending`, or outcome is `progress` and the completion evidence is absent); completion evidence is, for an authoring child, the target plan passing the certification oracle, and for an execution child, the target plan archived; an execution child with `outcome: progress` whose manifest `updated:` is stale past one cadence period releases the lane as evidenced stopped (eligible for fast re-dispatch); an idle-time child (null `fire_at`) holds the lane until the runtime's idle-task listing (named in the overlay) no longer shows it queued or running, idle-time tasks being lane-occupying per the overlay's attribution rule (an entry whose session identifier matches the current session, or one a pending `children[]` entry records with a matching `created_at`), or six hours pass after `created_at`, with the same outcome and completion-evidence conditions; and the listing-based arms adopt the linger model consistently with r4 item 8(a): the Fired arm counts a listing record only while it is ENABLED, and the Widened arm's classification ignores records whose `lifecycleStatus` is completed or `enabled` is false (a lingered completed child record occupies nothing; the state-file arms are the in-flight detectors), so the fast re-dispatch, successor chaining, and early release paths are not re-blocked by a corpse record. One authoring child still never runs alongside another.
- [x] Add the Step 1 `pending_dispatch` reader: when set and the fresh survey still validates the target (execution: plan top-level; authoring: item top-level and plan-uncovered), dispatch it per its kind through the normal Step 5 path (quota leg applies) without re-running the Step 3 selection, then clear the field; when the target is invalid, clear it and record the invalidation in `decision_reason`; when the target is valid but the Step 5 lane precondition trips on the final slot, retain `pending_dispatch` (retry next turn) and record the deferral in `decision_reason`; the Step 1 memory-index read-back also surfaces repo-matching `successor-chain-failed` notes and records the re-chain decision for the note's target.
- [x] Add the five-writer-classes sentence to the State file scoping note (turns, whose write modes are the Step 6 full rewrite, the Step 1 outcome-check updates, the mid-ladder trap Bash edits, the mid-ladder listing-confirm dispatch edits (children[] append), the turn's Step 0 adopt/set-clear edits (including the rearm_note clear when the listing shows the parent armed again), the loop-guard rearm_note write, the Quota-leg pricing_cache update plus its repo-matching pricing-note deletion, the dispatch-discipline stand-down turn_error write, and the Step 1 reader edits (pending_dispatch clear/retain, memory-note adoption); a child's re-arm FIRST ACTION; the idle-time watchdog; a completing execution child's successor-dispatch children-append plus the successor duty's parent re-create field edits; rearm-on-touch sessions writing parent_automation_id, parent_absent_since, and rearm_note), each non-turn write a targeted field edit through a temp file plus atomic replace, and rewrite the carry-forward sentence to name every field the Step 6 rewrite must preserve that the turn does not own: `parent_automation_id`, `rearm_note`, successor-appended `children[]` entries, and `pending_dispatch` / `parent_absent_since` written by non-Step-6 actors. Add the lost-update sentence to the same scoping note: atomic replace prevents torn writes, not lost updates; non-Step-6 targeted edits re-read the file immediately before the atomic replace and retry once when the bytes drifted from the writer's pre-read (one retry; a second drift records the loss in the turn output or the writer's note channel), and the residual interleaving window between Step 6 rewrites and child appends is accepted and named (a lost successor append is caught by the listing-based lane arms, which see the armed successor's own execution-marker payload, and by the next child's own-record lookup finding no record; only a failed chain writes `successor-chain-failed`; a lost outcome check self-corrects on the next turn).
- [x] The rewritten spans replace both pre-existing em-dashes in SKILL.md (the idle-children bullet's provider-429 exception sentence and the 2026-09-16 compaction Revisions entry) with colons, so the whole-file no-em-dash gate is satisfiable after this task (the scanner prints only the first match per file; zcode.md's two instances are Task 2's).
- [x] Add the SKILL.md Revisions entry for this change (dated 2026-09-16, schema 3 and liveness semantics).
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN.
- [x] Commit: `maintenance: scheduler state schema v3 and liveness semantics` (the original commit was dropped as empty in the 2026-09-17 rebase onto b105d7d8; its content is present via the branch's ancestor state)

### Task 2: zcode.md oscillation ladder, fallbacks, verification recipe, overlay polish

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md` (one read-back sentence only)
- `scripts/check_maintenance_pins.sh`

- [x] Add pins (RED first): the ladder recycling needle `update the recorded parent record into the child one-shot`; the new section anchor `## Automation primitive verification`; the linger-deletion needle `deleting your own lingered`, pinned against the ladder fallback's own sentence in zcode.md (this task writes that sentence; the re-arm paragraph in prompt-templates.md carries its copy); the ambiguous-outcome needle `treat the child as dispatched` against the rewritten carve-out (kept, now scoped); the per-session idle attribution needle ` sessionId matches the current session`; the pricing clear needle `clears the pricing-verification-failed note` and the SKILL.md read-back needle `note surfaces in the survey read-back`; a forbidden pin for the superseded step 1 claim `sessions whose spawner automation has completed are not blocked` (its presence fails). Run; expect the new pins failing.
- [x] Rewrite the dispatch ladder: step 1 fresh-session direct create (rewritten together: deleting the superseded completed-spawner claim and rewording its trailing fresh-chat rationale so no dangling antecedent remains, both superseded by the 2026-09-16 cap-model refinement already recorded in the cap paragraph); step 2 primary for automation-born turns: update the recorded parent record into the child one-shot with one update-primitive call (same id, recurring false, the computed one-shot schedule, the dispatch-slice payload, enabled true), applied only when no pending children[] entry carries the recorded parent id (a pending entry holding the id leads to the fallback's confirm listing: proceed-with-recycling on parent-form confirmation, a fresh-id create otherwise), then the fallback on any refusal: the existing delete-parent-then-create dance with its rollback, retries, `parent-restore-failed` path, and the ambiguous-outcome carve-out kept with the `treat the child as dispatched` wording, now scoped to cap-shaped refusals or listing-verified success (folds r4 item 7), plus the linger-deletion clause in the fallback create (`deleting your own lingered` completed spawner record first when the create is refused for the automation-born cap); the trap write is one of the turn's sanctioned write modes (Design Invariants); step 3 second lane via the idle-time primitive (unchanged) plus the trap rule: when the selection-loop signature appears mid-ladder after a decision, write `pending_dispatch` (and `turn_error`) via a Bash state edit before standing down, clearing `pending_dispatch` when the same turn's idle-time fallback dispatch succeeds (the dispatched idle child is then recorded in `children[]` and the field must not linger), and dispatch the authoring lane through the idle-time primitive when reachable (a different primitive that Bash-reliability witnesses show stays reachable mid-loop; the execution lane stays clocked-only); step 4 last resort unchanged plus the `pending_dispatch` cross-reference.
- [x] Add the `## Automation primitive verification` section: the fresh-session recipe that probes both flip directions on a throwaway record (create a one-shot probe record from an unbound session; update it recurring true with a cron; update it back to a one-shot; confirm each `nextRunAt`; delete the probe) and the recording rule: verdicts land as dated "verified live" lines beside the recipe; until verified, every recycling path keeps its delete-plus-create fallback and a recycling refusal is recorded in `rearm_note` naming the refusal.
- [x] Idle-lane per-session attribution (origin 3): the idle-lane visibility rule counts only idle-time tasks whose ` sessionId matches the current session` as lane blockers; foreign-session queued tasks are reported, not treated as occupying.
- [x] Watchdog garden path (r4 item 4): name the two levels explicitly, reworded for the new ladder (the OffPeakCreate arming refusal by the dispatching turn after a successful step 2 dispatch, versus the watchdog payload's own re-arm create refusal) and keep the already-exists and no-op semantics; already-exists verification failure routes to the child duty's escalation (record `rearm_note`, write the `loop-parent-missing` note, continue; folds r4 item 6 on the watchdog side).
- [x] Pricing clear-on-success (r4 item 5): a successful pricing re-verification `clears the pricing-verification-failed note`; add the one-sentence Step 1 read-back mention to SKILL.md (that a repo-matching `pricing-verification-failed` note surfaces in the survey read-back like other notes), pinned by the needle `note surfaces in the survey read-back`.
- [x] The rewritten spans replace both pre-existing em-dashes in zcode.md (the automation-born create cap paragraph and the session-compaction bullet) with colons, matching Task 1's em-dash fold so the whole-file no-em-dash gate passes.
- [x] Rewrite the recipe's Re-arm hygiene bullet to the state-first duty shape governing the re-arm decision of its two named actors (the turn's Step 0 and rearm-on-touch sessions; the shape is the template other re-arm actors may follow, the watchdog, child, and Step 1 memory-note-reader duties carrying their own embedded shapes): consult the state file first and decide state-first, at most one listing after the mutation decision never before, delete the own lingered record before a cap-refused create, and reuse the loop-guard sentence (`listed twice without a mutating step` means write `rearm_note` via Bash and stop touching automations), so the recovery paths cannot re-enter the listing-priming loop origin 1 witnessed.
- [x] Correct the vanish claim in every living restatement per r4 item 8(a), one pass: the zcode.md "Scheduling primitives" bullet, the zcode.md automation-born cap bullet's `completed one-shots disappear from \`CronList\`` clause, and SKILL.md Step 2's state-file arm rationale sentence `One-shot children vanish from the automation listing on completion` all become the linger model (`linger listed (enabled false, lifecycleStatus completed) and still bind` their spawner session before they age out), so no living span keeps teaching disappear-on-completion next to the corrected claim.
- [x] Add dated inline notes for the ladder rewrite and the verification section (this file's convention: dated notes, not a Revisions ledger).
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN.
- [x] Commit: `maintenance: record-oscillation dispatch ladder with fallbacks and verification recipe`

### Task 3: child blueprints: state-driven re-arm duty, successor dispatch, resume rule

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add pins (RED first): the state-first needle `state-first, without listing first`; the loop-guard needle `listed twice without a mutating step`; the carve-out needle `beyond the re-arm duty below and the single successor-dispatch duty below`; the successor anchor `SUCCESSOR DISPATCH` (exactly once in the file); the successor fallback needle `fall back to deleting your own spawner record whatever its current form`; the successor failure needle `when both legs fail`; the resume needle `this is a resume run`; the linger needle `deleting your own lingered`; the success-via-existing needle `counts as success only after one more listing confirms` (r4 item 2's pin, re-homed on the new wording). Pin reconciliation for this task (each an explicit pin edit in the same commit, never a change to the exact texts): the title-literal count pin now wants exactly zero occurrences of `Maintenance scheduler turn (every 2 hours)` in prompt-templates.md with the recipe in zcode.md remaining the single literal home (still exactly once there); the recognition-span count pin now wants exactly zero occurrences of the span in prompt-templates.md (zcode.md keeps its two); the escalation needle `retry at most twice` is re-pinned to the new wording `after two retries`; the suite's re-arm escalation needle list drops the superseded `list once more immediately before the create` entry (that wording becomes the forbidden span in the Validation block) and pins the new escalation spans instead (`after two retries`, `counts as success only after one more listing confirms`, `rearm_note`, `loop-parent-missing`, `parent_automation_id`, `Recurring automation recipe`); the re-arm parity regex is updated to the new paragraph's start and tail spans. Run; expect the new pins failing.
- [x] Replace both re-arm duty paragraphs (FIRST ACTION, identical text in both blueprints; register the deviation-list entry) with the state-first decision table, exact text:

```text
FIRST ACTION, before any gate or phase: re-arm the maintenance loop state-first, without listing first. Read .ai-playbook/scheduler-state.json (Bash) and take your own record to be the last children[] entry whose kind and target match this payload (an idle-time dispatch records a null automation id and takes no record: a matching entry is not taken as its record either, and the session proceeds exactly as if "parent_automation_id" were null); when no entry matches, you have no record: proceed exactly as if "parent_automation_id" were null. Then, first applicable step wins: (1) when "parent_automation_id" equals your own record's automation id and that entry still has outcome "pending" in the state file, the dispatch ladder left the parent record in child form under this session: update that one record into the parent form with one update-primitive call per the recipe in agents/skills/maintenance/zcode.md "Recurring automation recipe" (its title, its cadence cron, recurring true, enabled true, its prompt template with {REPO_ROOT} filled), then update "parent_automation_id" as a targeted field edit (atomic replace; change no other field) and stop (a refused flip falls back to deleting your own spawner record and creating the parent exactly per the recipe, recording the refusal in the "rearm_note" field); when that entry is no longer pending, the recorded id is untrusted: do not flip on it, and route through steps (2) and (3) instead (listing to confirm before any mutation). (2) when "parent_automation_id" names a different non-null id, the parent is believed armed: list at most once to confirm; when an ENABLED automation with the recognition title and prompt opening (the literals defined in agents/skills/maintenance/zcode.md "Recurring automation recipe": its Title line and its prompt template opening) whose prompt also contains the resolved repository root is present, stop; when absent, set "parent_automation_id" to null (targeted field edit) and enter step 3 with that listing already in hand (do not list again). (3) when "parent_automation_id" is null: decide from the listing you already performed in step 2 when you entered from there, otherwise list at most once; when an ENABLED recognition match is present (an ENABLED automation with that recognition title and prompt opening whose prompt contains the resolved repository root), adopt its id into "parent_automation_id" (targeted field edit) and stop; when the listing shows an armed child payload for this repository other than your own spawner record (a non-recurring ENABLED automation whose prompt contains the resolved repository root and a plan-execution payload), do not create or recycle: the lane is held by that child; stop; when neither is present, recycle your own spawner record into the parent form with the same update as step 1 when you have one, otherwise create the parent exactly per the recipe, deleting your own lingered completed spawner record first when the create is refused for the automation-born cap; a create refusal indicating the parent already exists counts as success only after one more listing confirms an ENABLED automation with that title and prompt opening whose prompt contains the resolved repository root is present, and a failed confirmation routes to the escalation below; then update "parent_automation_id" as a targeted field edit. When this step succeeds after an earlier refusal recorded in "rearm_note", clear "rearm_note" in the same targeted edit. A recycling update refusal of any kind in this step falls back to this step's create path and is recorded in the "rearm_note" field naming the refusal. Loop guard: if you have listed twice without a mutating step between listings, write the "rearm_note" field via a Bash state edit naming the loop and stop touching automation primitives. (4) Any other refusal after two retries: record it in the state file "rearm_note" field (targeted field edit), write a memory note {"type": "loop-parent-missing", "repo": "<repository root>"} in the agent's persistent memory index, and continue; a later session reading that note re-arms per the recipe.
```

- [x] Insert the SUCCESSOR DISPATCH paragraph into the execution blueprint after the final squash-merge sentence (and before the FINAL STEP compaction line), exact text:

```text
SUCCESSOR DISPATCH, after the final squash merge passes and before ending the session: chain the next execution child by recycling your own spawner record. Read .ai-playbook/scheduler-state.json and the open top-level plans. Chain nothing, and end, when any of these holds: no open plan remains; any other children[] entry whose lane hold is still active under the scheduler's release rules (outcome not `failed` and completion evidence absent within the outcome horizon, with the Step 2 evidenced-stopped early release applying: another actor holds or awaits the record); the automation listing shows an armed child payload for this repository; or this run did not end in a clean closeout. Otherwise select the successor target by the D1 rule: memory dependency-chain order when available; otherwise the oldest open plan that passes the certification oracle, run once per open top-level plan as Step 1 does; otherwise the oldest open plan, whose re-certification the PRE-STEP performs; skip plans the memory index marks dependency-blocked whose blocker is still an open plan or a deferred plan anywhere under the resolved plans directory. Fix the fire time per the quota leg (run scripts/quota_window_probe.py; never inside a deferred window; at least 5 minutes out; the overlay's peak-window deferral and starvation exception apply). Then reshape your own spawner record into the successor one-shot with one update-primitive call: recurring false, the successor fire time, this payload's body with {some_plan} filled with the successor plan path and {REPO_ROOT} filled, enabled true. When that update is refused or its outcome is unverifiable, fall back to deleting your own spawner record whatever its current form (child one-shot, lingered completed, or the re-armed parent this session created) and creating the successor one-shot per the overlay's clocked child shape (agents/skills/maintenance/zcode.md "Scheduling primitives": one-shot delayMinutes schedule, recurring false), carrying the same payload and fire time; this fallback leg is part of the single successor-dispatch duty the opening guard authorizes; when both legs fail, list at most once before the re-create: when an ENABLED automation with the recognition title and prompt opening (the literals defined in agents/skills/maintenance/zcode.md "Recurring automation recipe") whose prompt also contains the resolved repository root is present, adopt its id into "parent_automation_id" (targeted field edit) and end without creating; only when the listing shows no such match, re-create the parent per the recipe in agents/skills/maintenance/zcode.md "Recurring automation recipe" and update "parent_automation_id" (targeted field edit) so the loop stays armed; only when that re-create is also refused, write a memory note {"type": "successor-chain-failed", "repo": "<repository root>", "target": "<successor plan path>"} in the agent's persistent memory index and end; on this path the loop may stay dark until an outside actor re-arms it and no watchdog covers it: the note is surfaced by the next touch session's or human read-back of the memory index, and by the next scheduler turn's survey read-back only when the loop has been re-armed by some actor, which then re-runs the normal D1 decision for the target. Loop guard: if you have listed twice without a mutating step between listings, stop touching automation primitives and end; the next scheduler turn re-decides the target. On success, record the successor in the state file children[] as kind execute, pending, the same automation id when the reshape leg ran, otherwise the fresh id of the created successor, with the new target and fire_at (targeted field edit). Dispatch exactly one successor per completed child (a failed chain counts as the one attempt); never chain after a stood-down or failed run. Never push.
```

- [x] Amend the execution inner block's opening guard sentence to `...do not create or schedule further automations beyond the re-arm duty below and the single successor-dispatch duty below` and register the deviation-list entry; the authoring blueprint's guard keeps the re-arm-only exception.
- [x] Add the resume rule sentence to the execution blueprint after the PRE-STEP block, exact text: `Resume rule: when the target plan already carries checked checkboxes at fire time, this is a resume run: read the execute-plan session manifest at docs/tmp/execute-plan/<plan-slug>/manifest.md first, refresh its updated: timestamp, and continue from the first unchecked task; do not re-run completed tasks; the PRE-STEP re-certification covers the digest drift the checkbox marks cause.` The literal `docs/tmp` path is intentional here (unlike Task 1's facts-resolved wording): child payloads must be self-contained and cannot resolve facts keys, and today's facts pin `tmp_dir` to `docs/tmp/` (verified 2026-09-16); a future facts override must revisit this payload text, and that divergence is the recorded rationale, not an oversight.
- [x] Register all wording changes in the file's deviation list with dated entries (2026-09-16), noting which backlog-source spans they supersede; each deviation-list entry paraphrases its subject anchor (never quotes an anchor verbatim, including the superseded rearm wording that Validation gate 6 forbids) so the exactly-one count gate on `SUCCESSOR DISPATCH` and the forbidden-span gates stay passable at Task 6.
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN (parity regex may need a deliberate update to the new tail wording; make the pin and the text agree in the same edit).
- [x] Commit: `maintenance: state-driven rearm duty, successor chaining, resume rule in child blueprints`

### Task 4: rearm-on-touch surfaces (indefinite-operation FIX-2)

Deviation (2026-09-18, P12): the Step 0 trigger was rewritten to state-first wording (backlog 2026-09-17-step0-rearm-trigger-state-first-wording); the Task 4 quote above is historical, and this plan's gate needle was flipped to the new sentence's discriminating needle in the same commit so this plan's gate block and the pins suite never disagree.

Files:
- `agents/skills/maintenance/SKILL.md` (Step 0 sentence)
- `agents/skills/done/SKILL.md` (one line before Step 0)
- `scripts/check_maintenance_pins.sh`

- [x] Add pins (RED first): the SKILL.md Step 0 discriminating needle `rearm-on-touch check: when the automation listing shows no ENABLED parent` (unique to this insertion; the Task 1 semantics paragraph's mention of a rearm-on-touch session must not satisfy it); the done-skill needle `rearm-on-touch check defined in the maintenance skill`. Run; expect the new pins failing.
- [x] Add to SKILL.md Step 0 (runtime-agnostic), deferring to the State file semantics as the single owner of the re-arm decision: `rearm-on-touch check: when the automation listing shows no ENABLED parent for this repository (an automation whose title and repo-filled prompt opening match the recognition rule), and only when this repository already runs the loop (its scheduler state file exists at the path the State file section defines), consult the State file semantics and re-arm per the runtime overlay's recipe only when they classify darkness. Whatever the classification, the check then always performs its three bookkeeping edits: adopt the live id into parent_automation_id when the listing shows a recognition match whose prompt contains the resolved repository root and the recorded id differs, but only when the recorded id is not itself live in the listing (a recorded id still present is kept; more than one differing-id match defers to the Step 2 duplicate-parent tripwire); set parent_absent_since when the parent is absent (first observation, keeping the earliest value while the absence persists) or clear it when a recognition match is present; and clear rearm_note when the listing shows the parent armed again.` (fold the Step 1 memory-note path unchanged).
- [x] Add to the done skill, immediately before its Step 0 heading: `Before Step 0, in a repository that resolves the maintenance skill, run the rearm-on-touch check defined in the maintenance skill's Step 0 and follow its darkness classification.` Nothing else in the done skill changes; the line is a scoped pointer and restates no condition of its own (the SKILL.md State file semantics stay the single owner of the re-arm decision).
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN.
- [x] Commit: `maintenance: rearm-on-touch in scheduler Step 0 and done`

### Task 5: r4 polish residue remainder

Files:
- `agents/skills/maintenance/SKILL.md` (Revisions ledger only)
- `scripts/check_maintenance_pins.sh` (trailing newline)

- [x] Revisions ledger r3 entry (r4 item 1): add a dated `2026-09-15 (review r3 fix round)` entry covering the operative r3 changes (ambiguous carve-out, step 4 branching, watchdog guards, idle horizon alignment, Step 1 reader branch, full-span pin) and move the r3-only clauses out of the amended r2 entry so each entry attributes only its own round's work; leave all other history untouched.
- [x] Pins script trailing newline (r4 item 3): make the file end with exactly one newline; verify with `tail -c 1 scripts/check_maintenance_pins.sh | od -c | head -1` showing `\n`.
- [x] Verify the r4 items folded by Tasks 2-3 are pinned and green: run the full suite and confirm the refusal-kind scope and ambiguous-outcome needle (Task 2), the success-via-existing, lingered-record, and escalation-needle pins (Task 3), and the pricing-marker clear needle (Task 2) all pass, closing r4 items 2, 5, 6, 7, 8 by the rewritten invariants and their new pins.
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN.
- [x] Commit: `maintenance: r4 residue ledger and pins hygiene`

### Task 6: final validation

Files: none (gate task; no commit expected).

- [x] Run the entire `## Validation Commands` block from the repo root; expect `validation: all gates green`.
- [x] Run `bash scripts/check-no-em-dash.sh touched`; expect exit 0.
- [x] Run `bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"`; expect exit 0.
- [x] Record any failure as a task-checkbox regression and fix within Review Scope before finishing; do not mark the plan complete with a red gate.
