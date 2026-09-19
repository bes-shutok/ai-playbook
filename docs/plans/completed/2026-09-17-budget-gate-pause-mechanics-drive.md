# Plan: budget-gate pause mechanics + drive (4 origins)

Origin backlog items (scope of record):
- `docs/history/backlog/2026-09-15-budget-gate-midrun-pause-resume.md` (midrun-pause-resume)
- `docs/history/backlog/2026-09-15-budget-gate-pause-protocol-timing.md` (pause-protocol-timing, HIGH)
- `docs/history/backlog/2026-09-15-budget-gate-plan-review-exit-residue.md` (exit-residue)
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` (codex-deny-envelope)

## Terms

- **Budget gate**: the quota-window pause-and-resume protocol at long-loop boundaries; the canonical home is the `execute-plan` skill's "Budget gate (quota-window pause and resume)" section; the `plans` skill carries the authoring-boundary mirror; this plan adds a review-loop surface.
- **Guard flag**: `~/.ai-playbook/runtime/budget-guard.flag`; host-global key=value file the probe writes on a pause decision and the backstop hook enforces.
- **Fired marker**: `~/.ai-playbook/runtime/budget-guard.fired`; anti-thrash marker written at the first block, binding to the flag's `reset_at_epoch`.
- **Binding window**: the quota limit whose `reset_at_epoch` is earliest (`primary` or the weekly `secondary`).
- **Standing resume watcher**: the one-shot resume automation scheduled at every continue boundary with a trusted binding; machine state in `scripts/execute_plan_resume_watcher.py`; this plan extends the protocol around it and never redesigns it.
- **Protocol margin**: `budget_pause_min_protocol_minutes` (fallback 10); a wall-clock floor under which the binding window's remaining minutes cannot cover the pause protocol itself.
- **Between-boundary probe**: a budget-gate probe run inside a review loop before every fold batch and every mechanical audit pass, not only before worker-wave or round launches.
- **`budget_pause` record**: the loop's persisted pause record (execute-plan: `manifest.md`; plans: `{tmp_dir}/plan-requirements-<slug>.md`; review-loop: the round's staging doc); this plan adds a `resume_scheduled: yes|no` field.
- **Wave recommendation**: the probe's forward-looking launch advice computed from `--plan-cost <percent>`: `full`, `split` (waves of `wave_size`), or `pause`.
- **Drive**: the manual live acceptance procedure for the Codex deny envelope (trust prompt plus one real denied tool call), including the post-drive decision table.

## Assumptions

- assume the standing resume watcher exists and is certified; basis: `scripts/execute_plan_resume_watcher.py` at HEAD plus the canonical "Standing resume watcher" subsection; this plan only extends boundary coverage through skill text and never redesigns the machine state, fences, schedulers, or classification (origin non-goal).
- assume the `budget_pause_*` facts keys are absent from `.ai-playbook/facts.md` today, so fallback defaults apply (20 / 90 / auto; the new margin default is 10); basis: grep at authoring time.
- assume the Codex drive cannot run unattended (it needs a human-approved hook trust prompt and a real Codex session start); basis: origin item plus the README trust-prompt section; the drive stays a Ship-when condition.
- assume existing pause thresholds keep their semantics and the margin adds to them, and there is no mid-worker interruption; basis: origin non-goals.
- assume fixture epochs in tests are synthetic; the 2026-09-15 incident numbers (54/76/97/98 percent) are history, not current probe behavior; basis: origin 2 narrative.

Decision points requiring a grill: forward-looking gate placement resolved to probe `--plan-cost` flag plus skill wave-size convention, never the hook (hook stays a fail-open flag reader) - source: origin open decision plus candidate direction - 2026-09-17 - Tasks 2, 4, 5, 6; per-worker cost history resolved to no persistent store (YAGNI): the orchestrator derives `--plan-cost` from the loop's own last recorded comparable panel cost when known, else omits the flag - source: author decision against origin open decision - 2026-09-17 - Tasks 4, 5; record sinks stay as-is (manifest.md, plan-requirements notes, staging doc) and the hook never reads records - source: existing canonical surfaces - 2026-09-17 - Tasks 4, 5, 6; Codex question canonical home moves to `agents/hooks/budget-guard/README.md` by a single fold (item becomes history-only and moves to completed at plan completion with a pointer) - source: lifecycle need, canonical content must outlive the backlog item's archive move - 2026-09-17 - Task 7; F8 witness-block extraction not taken (exactly one witness test exists today, verified by grep; conditional trigger not fired) - source: origin text plus authoring grep - 2026-09-17 - Gist; idle-time-queue timer not added to the fallback chain (watcher plus schedule-first already satisfy acceptance criterion 1) - source: author decision, YAGNI - 2026-09-17 - Task 4; worker token caps deferred (no portable cross-runtime ceiling parameter; wave sizing addresses the same risk) - source: author decision - 2026-09-17 - Gist; protocol margin is wall-clock minutes per the origin's own proposed shape, with the used-percent line remaining the budget-side guard - source: origin layer 2 text - 2026-09-17 - Task 1; origin exit-residue item 3 (r2 F1 stale-comment reword) dispositioned as misattribution with no code change (both fixture epochs already past, so the flagged comment is factually correct; the origin's 1791551411 claim belongs to a different test's inline payload) - source: fixture probe at authoring time - 2026-09-17 - Gist item 7; pause-leg resolution follows the canonical non-schedulable-pause shape (the orchestrator-created automation carries the pause resume; the driver's supersede-only pause classification stays untouched and the watcher module remains out of scope) - source: r6 collision between this plan's driver-opt-in fold and the concurrent canonical rewrite, resolved by re-basing the plan on the fresh shape per the joint-state rule - 2026-09-17 - Tasks 4, 5.

## Gist & Examples

Four origins, one coherent change set.

**1. Schedule-first pause protocol and record reconciliation (origin 2, layers 1 and 4).** Today the canonical pause protocol appends the `budget_pause` record (step 3) before scheduling the resume (steps 4-5); the 2026-09-15 incident died between those steps and the run sat dead for two hours. The reorder schedules the resume automation FIRST, then appends the record with a new `resume_scheduled: yes|no` field, and every resume path (Step 0.5 resume, fired watcher, manual) reconciles a record carrying `resume_scheduled: no` by completing the scheduling step before any other resume work. Example record line after the change:

```
budget_pause: runtime=zcode reset_at_epoch=1789631198 reset_at_iso=2026-09-17T08:46:38+01:00 thresholds=20/90/10 next_step=launch r8 review panel resume_scheduled=yes (the record line is key=value encoded; the field's semantics spelling in the pinned skill text is resume_scheduled: yes|no)
```

**2. Protocol-completion margin (origin 2, layer 2).** The probe gains `--min-protocol-minutes <N>` (facts key `budget_pause_min_protocol_minutes`, fallback 10): it also pauses when the binding window's remaining minutes fall below the margin, so a late pause still leaves the protocol itself time to complete. The margin is wall-clock (the origin's proposed shape); the used-percent line remains the budget-side guard. Weekly `secondary` bindings keep their report-only behavior under the margin too.

**3. Between-boundary probes (origin 2, layer 3; origin 1, gap 2).** All three loop surfaces (execute-plan Phase 3, plans Plan Quality Gate, review-loop) run the probe before every fold batch and every mechanical audit pass inside a loop, and record the outcome (canonical: `manifest.md` line; plans: requirements notes; review-loop: a `budget-gate: continue, <binding>, <used_percent>%` line in the round's staging doc). A continue at a between-boundary with a trusted binding schedules or replaces the standing resume watcher on the surfaces that own one (the execute-plan runtime machine state and the plans authoring machine state; replace, never stack), so a death during fold work still leaves a watcher firing at reset plus one minute there; review-loop owns no machine state and records the probe outcome plus the pause protocol only.

**4. Forward-looking wave sizing (origin 1, gaps 1 and 5).** The probe gains `--plan-cost <percent>`. When provided, the report carries `plan_cost_percent`, `wave_recommendation`, and `wave_size`; the skills pass the last recorded comparable panel cost when known. Example: window used 80 percent, panel cost 40 percent: remaining is 20, so `wave_recommendation: split`, `wave_size: 2`; cost 45 would give `pause`.

**5. Guard observability (origin 1, gap 4).** The probe writes `armed_by=probe` into the guard flag (manual drives write `armed_by=manual`), and the block reason gains the flag path and armed-by: `... record the budget pause, and schedule the resume. Budget guard flag: <flag path> (armed by <armed_by>).` A missing `armed_by` line reads `unknown`. The README documents the flag path, writer, and clear procedure (already present) plus the new reason text.

**6. Codex drive procedure folded into its durable home (origin 4).** The open envelope question, the Ship-when drive procedure (fixture flag now includes `armed_by=manual`), the post-drive decision table (with its four attribution-gate follow-throughs), the row-2 contingency, and the real-pause observation move into `agents/hooks/budget-guard/README.md`, which becomes the canonical home; the backlog item becomes history-only and moves to completed at plan completion with a pointer. The drive itself stays manual (Ship when).

**7. Review residue (origin 3).** F7: introduce a `_git_stdout(*args)` fixture helper in `scripts/test_execute_plan_runtime.py` and migrate exactly 20 `_git(...).stdout.strip()` sites (count re-baselined 19 to 20 at execution, 2026-09-18: the efficiency-plan merge effe76dc added a 20th chain; originally 19 verified at authoring time), with a two-line helper body so the helper's own definition can never satisfy the forbidden-pattern gate; test-only tidy in its own commit. F8: not taken; the extraction trigger (a second ResourceWarning witness test) has not fired (exactly one exists today). Item 3 (the r2 F1 stale-comment reword): NOT taken; verified against the fixture at authoring time (`scripts/testdata/quota/zcode_limit_response.json`): both fixture epochs are already past (2026-09-11 and 2026-09-16 17:50 local), so the comment's "fails open to unknown/continue" is factually correct today and stays correct as the epochs only age; the origin item's epoch claim (1791551411, live until 2026-10-10) belongs to a different test's inline payload (`test_parse_zcode_live_payload_with_extra_fields`) and was misattributed to this fixture. Disposition: no code change; the exit-1 pin is correct in every phase.

Origin acceptance-criteria mapping (origin 2): AC1 death-between-boundaries = existing standing watcher at continue boundaries plus schedule-first (gate G); AC2 98-percent drill = the new drill test plus gate G ordering; AC3 reconciliation = `resume_scheduled: no` greps plus the reconciliation sentences; AC4 between-boundary probe = the between-boundary greps plus the per-surface outcome-recording lines; AC5 weekly secondary = preserved report-only (probe test plus unchanged no-flag wording).

## Evaluation Criteria

**Quality dimensions:**
- correctness: margin and wave-recommendation logic unit-tested at boundaries (strict inequality, split threshold, out-of-range rejection, secondary report-only); both hook adapters' exact-envelope fixtures updated in the same change; all four suites green.
- consistency: canonical, plans mirror, and review-loop surfaces state the same probe resolution, thresholds, margin key, and pause-protocol order; schedule precedes record in both canonical and mirror.
- observability: the block reason carries the flag path and armed-by; the README documents the new reason text and remains the canonical drive home.
- repo-verifiability: the Validation Commands block exits 0 on the completed tree and every gate is executable as written.

**Done when:**
- The three plan-owned unit suites pass (`test_quota_window_probe.py`, `test_budget_guard_hooks.py`, `test_execute_plan_runtime.py`), plus the watcher regression suite on trees that carry the watcher module (skipped loudly where the module is absent; the watcher is a declared non-goal of this plan).
- The probe accepts `--min-protocol-minutes` and `--plan-cost`, writes `armed_by=probe`, and the core reason carries the flag path and armed-by suffix.
- Both skills carry the margin key row, the two new probe arguments, schedule-before-record order, `resume_scheduled` semantics, the reconciliation rule, and the between-boundary probes; review-loop carries its budget-gate subsection with the outcome line.
- The README carries the folded drive procedure, decision table (with its four attribution-gate follow-throughs), row-2 contingency, the abort and retirement protocol (stop trigger, restore branches, superseded-edit branch, retirement, standing order), real-pause observation, and `armed_by=manual` fixture step.
- The 19 strip chains are migrated (`self._git_stdout(` count exactly 19, old pattern absent).
- The 20 strip chains are migrated (`self._git_stdout(` count exactly 20, old pattern absent; count re-baselined 19 to 20 at execution, 2026-09-18, effe76dc).
- The Validation Commands block exits 0.

**Ship when:**
- One Codex deny-envelope live drive per the README procedure, after the user approves the hook trust prompt, closed per the post-drive decision table (manual; needs a real Codex session start).
- One real budget pause with a scheduled resume completing end-to-end on at least one runtime where the backstop block is observed to have fired (fired marker at the pause's reset epoch or the block reason in the transcript); a completed pause record without an observed block proves the probe path only.
- Manual verification of the margin and wave sizing under real quota pressure (open by design; needs a live window near exhaustion).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/quota_window_probe.py`
- `agents/hooks/budget-guard/budget_guard_core.py`
- `agents/hooks/budget-guard/README.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

**Tests:**
- `scripts/test_quota_window_probe.py`
- `scripts/test_budget_guard_hooks.py`
- `scripts/test_execute_plan_runtime.py`

**Documentation:**
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` (Canonicality paragraph only; the item itself moves to completed at plan completion)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_resume_watcher.py` and `scripts/test_execute_plan_resume_watcher.py`; reason: the watcher design is a declared non-goal (the canonical pause boundary is non-schedulable and the driver's supersede-only pause classification is preserved untouched); the suite runs as a regression guard only.
- `docs/plans/completed/` and `docs/history/backlog/completed/`; reason: archived history is immutable context.
- `agents/hooks/budget-guard/zcode.sh` and `codex.sh`; reason: adapters pass through to the core unchanged; reason-text changes are pinned by their existing fixture tests.

## Design Invariants (CR Guard)

- **Fail-open direction is never inverted.** A missing, unreadable, or malformed flag still passes; a probe failure still reports `status: unknown` and continues; the margin and plan-cost inputs must not turn any absent-data path into a block (Tasks 1-3; hook README fail-open rule).
- **Weekly `secondary` stays report-only.** It writes no flag, schedules nothing, and reports for user decision; the margin and wave features must not change this, and reconciling a record bound to the weekly secondary window reports for user decision and never schedules (Tasks 1-6).
- **Existing thresholds keep their semantics.** `budget_pause_minutes_before_reset` (20) and `budget_pause_max_used_percent` (90) behave exactly as before; the margin adds a condition (origin non-goal; Tasks 1, 4, 5).
- **The watcher is extended, never redesigned.** `scripts/execute_plan_resume_watcher.py` is untouched; boundary coverage grows only through skill text (Tasks 4-6), and the driver's supersede-only pause classification is preserved (the orchestrator-created automation carries the pause resume).
- **One shared guard lock contract.** New flag writers keep using the probe's existing locked `os.replace` path; the core keeps its re-read-before-unlink pattern; no new unlock writers appear (Tasks 3).
- **The hook never reads `budget_pause` records.** Records are resume-path inputs only; the hook stays a flag-only fail-open reader (Tasks 3-6).
- **Exact-envelope pins move with the reason change.** The codex drive's decision-table ISO-embed check is unaffected by the suffix; the fixture tests' exact strings update in the same change that alters `REASON_TEMPLATE` (Task 3).

## Validation Commands

```bash
#!/usr/bin/env bash
# Validation for 2026-09-17-budget-gate-pause-mechanics-drive.md. Fail-closed:
# every gate aborts non-zero on miss, forbidden match, or tool error (rc >= 2).
set -u
TOP="$(git rev-parse --show-toplevel 2>/dev/null)" || TOP="$PWD"
cd "$TOP" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

expect_match() {
  grep -q "$1" "$2" 2>/dev/null
  rc=$?
  if [ "$rc" -eq 0 ]; then return 0; fi
  if [ "$rc" -ge 2 ]; then fail "grep error rc=$rc on $2"; fi
  fail "missing expected pattern in $2: $1"
}

expect_no_match() {
  grep -q "$1" "$2" 2>/dev/null
  rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present in $2: $1"; fi
  if [ "$rc" -ge 2 ]; then fail "grep error rc=$rc on $2"; fi
  return 0
}

# Gate A: unit suites (full selectors; abort on any failure). The watcher
# suite is a regression guard only on trees that carry the watcher module
# (a declared non-goal of this plan); skip it loudly when the module is
# absent from the executing tree instead of failing on an out-of-scope file.
python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py' > /tmp/val_probe.log 2>&1 || { tail -20 /tmp/val_probe.log >&2; fail "probe suite"; }
python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py' > /tmp/val_hook.log 2>&1 || { tail -20 /tmp/val_hook.log >&2; fail "budget-guard suite"; }
python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py' > /tmp/val_runtime.log 2>&1 || { tail -20 /tmp/val_runtime.log >&2; fail "runtime suite"; }
if [ -f scripts/execute_plan_resume_watcher.py ]; then
  python3 -m unittest discover -s scripts -p 'test_execute_plan_resume_watcher.py' > /tmp/val_watch.log 2>&1 || { tail -20 /tmp/val_watch.log >&2; fail "watcher suite"; }
else
  echo "watcher module absent from this tree (out-of-scope non-goal); watcher suite skipped" >&2
fi

# Gate B: F7 helper migration (origin 3).
expect_no_match '_git(.*)\.stdout\.strip()' scripts/test_execute_plan_runtime.py
test "$(grep -c 'self\._git_stdout(' scripts/test_execute_plan_runtime.py)" -eq 20 || fail "expected exactly 20 _git_stdout call sites (re-baselined 19 to 20, effe76dc)"
expect_match '_git_stdout(self' scripts/test_execute_plan_runtime.py

# Gate C: probe surface (origin 1 gaps 1/4/5, origin 2 layer 2).
expect_match 'DEFAULT_PROTOCOL_MINUTES_THRESHOLD = 10' scripts/quota_window_probe.py
expect_match 'min-protocol-minutes' scripts/quota_window_probe.py
expect_match 'min-protocol-minutes must be >= 0' scripts/quota_window_probe.py
expect_match 'plan-cost' scripts/quota_window_probe.py
expect_match 'wave_recommendation' scripts/quota_window_probe.py
expect_match 'armed_by=probe' scripts/quota_window_probe.py

# Gate D: guard core reason suffix (origin 1 gap 4).
expect_match 'Budget guard flag: {flag_path} (armed by {armed_by})' agents/hooks/budget-guard/budget_guard_core.py
expect_match 'armed_by' agents/hooks/budget-guard/budget_guard_core.py

# Gate E: README drive fold (origin 4) and new reason docs (origin 1 gap 4).
expect_match 'Post-drive observation' agents/hooks/budget-guard/README.md
expect_match 'armed_by=manual' agents/hooks/budget-guard/README.md
expect_match 'Budget guard flag:' agents/hooks/budget-guard/README.md

# Gate F: skill surfaces (origin 2 layers 1-4) - per-file, no context spillover.
for f in agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md; do
  expect_match 'budget_pause_min_protocol_minutes' "$f"
  expect_match 'min-protocol-minutes' "$f"
  expect_match 'plan-cost' "$f"
  expect_match 'resume_scheduled: yes|no' "$f"
  expect_match 'resume_scheduled: no' "$f"
  expect_match 'completing the scheduling step' "$f"
  expect_match 'between-boundary probe' "$f"
done
expect_match 'between-boundary probe' agents/skills/review-loop/SKILL.md
expect_match 'budget-gate: continue' agents/skills/review-loop/SKILL.md
expect_match 'completing the scheduling step' agents/skills/review-loop/SKILL.md
expect_match 'resume_scheduled' agents/skills/review-loop/SKILL.md
expect_match 'stay report-only' agents/skills/review-loop/SKILL.md

# Gate G: schedule-first order (origin 2 layer 1) - full chain, both surfaces.
# Canonical: the non-schedulable pause record (watcher-schedule call) must
# precede the manifest record append; mirror: the create-first schedule step
# must precede the record append.
exec_create=$(grep -n 'A pause boundary is non-schedulable' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
exec_rec=$(grep -n 'Append a `budget_pause` line' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
[ -n "$exec_create" ] && [ -n "$exec_rec" ] || fail "canonical create/record anchors missing"
[ "$exec_create" -lt "$exec_rec" ] || fail "canonical: record still precedes the boundary record"
exec_sch=$(grep -n 'resume_scheduled' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)
[ -n "$exec_sch" ] || fail "canonical resume_scheduled missing"
pl_sched=$(grep -n 'create the resume automation FIRST' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)
pl_rec=$(grep -n 'Append a `budget_pause` record' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)
[ -n "$pl_sched" ] && [ -n "$pl_rec" ] || fail "mirror schedule/record anchors missing"
[ "$pl_sched" -lt "$pl_rec" ] || fail "mirror: record still precedes schedule"

# Gate H: weekly secondary report-only wording survives (origin 2 AC5).
expect_match 'writes no flag' agents/skills/execute-plan/SKILL.md
expect_match 'writes no flag' agents/skills/plans/SKILL.md
expect_match 'writes no flag' agents/skills/review-loop/SKILL.md

# Gate I: format gates over the changed prose plus this plan.
bash scripts/check-no-em-dash.sh file docs/plans/2026-09-17-budget-gate-pause-mechanics-drive.md agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/review-loop/SKILL.md agents/hooks/budget-guard/README.md || fail "em dash scan"
bash scripts/scan-public-hygiene.sh || fail "public hygiene scan"

echo "VALIDATION OK"
exit 0
```

Authoring-time note: the block was executed against the pre-work tree (bash -n clean) and aborted at the first failing gate as designed: Gate A passed (all four suites green on the authoring lineage), Gate B failed on the forbidden-pattern check (the 19 chains exist). RED-today gates: B (chains exist), C, D, E, F (strings absent), and H's review-loop line (review-loop carries no budget-gate text yet); Gate G's order checks are RED-today with their anchors PRESENT (on the current tree the canonical boundary-record step sits after the manifest record append, and the mirror's create-first step sits after its record append), so Gate G fails on the order comparisons, not on missing strings. After Task 9 the whole block must exit 0.

### Task 1: Probe protocol-completion margin (origin 2, layer 2)

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [ ] `QuotaWindowProbeTest#test_evaluate_pause_protocol_margin_pauses_above_fixed_threshold`; given a binding primary limit with `minutes_remaining` 25 and thresholds `minutes_threshold=20, percent_threshold=90, protocol_minutes_threshold=30`, expects `("pause", reasons)` where some reason contains `protocol margin` (the margin fires above the fixed minutes line)
- [ ] `QuotaWindowProbeTest#test_evaluate_pause_protocol_margin_default_floor_is_subsumed`; given the same limit with default thresholds (margin 10), expects `("continue", [])` (the 10-minute default is a floor under the 20-minute line, not a second pause line at normal range)
- [ ] `QuotaWindowProbeTest#test_evaluate_pause_protocol_margin_boundary_is_strict`; given `minutes_remaining` exactly equal to `protocol_minutes_threshold`, expects `("continue", [])` (mirrors the strict `<` of the minutes line)
- [ ] `QuotaWindowProbeTest#test_secondary_binding_margin_stays_report_only`; given a secondary-only limit set inside the margin with `protocol_minutes_threshold=30`, expects `build_report` to return `pause_decision: pause` and `write_flag_if_paused` to return False with no flag file written (weekly secondary keeps report-only under the margin)
- [ ] `QuotaWindowProbeTest#test_cli_min_protocol_minutes_flag_pauses`; given a zcode fixture payload whose binding limit has 25 minutes remaining and `main(["--runtime", "zcode", "--config", <fixture>, "--min-protocol-minutes", "30"])`, expects exit 0 and a stdout report with `pause_decision: pause` and a reason containing `protocol margin`
- [ ] `QuotaWindowProbeTest#test_cli_ninety_eight_percent_pause_drill_ac2_witness`; given a zcode fixture payload whose binding limit reports used_percent 98 with 40 minutes remaining and `main(["--runtime", "zcode", "--config", <fixture>, "--min-protocol-minutes", "10"])`, expects exit 0, `pause_decision: pause`, and reasons containing the `used_percent` line (the origin-2 AC2 fixture drill: the pause fires at very high used-percent with wall-clock margin intact, so the protocol runs while budget, not the clock, is the binding constraint)
- [ ] `QuotaWindowProbeTest#test_cli_min_protocol_minutes_rejects_negative`; given `main(["--runtime", "zcode", "--config", <fixture>, "--min-protocol-minutes", "-5"])`, expects `SystemExit` with code 2 and a usage error on stderr (0 stays legal and disables the margin; negatives fail loud like `--plan-cost`)
- [ ] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'` (the new evaluate_pause/build_report tests fail with TypeError on the missing parameter and the new CLI tests fail with `SystemExit(2)` on the unrecognized `--min-protocol-minutes` argument; all pre-existing tests pass)
- [ ] Write minimal implementation: module constant `DEFAULT_PROTOCOL_MINUTES_THRESHOLD = 10`; `evaluate_pause(..., protocol_minutes_threshold=DEFAULT_PROTOCOL_MINUTES_THRESHOLD)` appending reason `"minutes_remaining {X} below protocol margin {Y}"` when `minutes_remaining < protocol_minutes_threshold`; thread the parameter through `build_report`, `probe_zcode`, `probe_codex`, `run_probe`; CLI `--min-protocol-minutes` (int, default `DEFAULT_PROTOCOL_MINUTES_THRESHOLD`) wired through `main`, with `parser.error("--min-protocol-minutes must be >= 0")` for negative values (0 stays legal and disables the margin)
- [ ] Run → expect GREEN: the probe suite passes (this task only; the budget-guard suite is untouched and still green)
- [ ] Commit: `feat: quota probe protocol-completion margin threshold`
- [x] `QuotaWindowProbeTest#test_evaluate_pause_protocol_margin_pauses_above_fixed_threshold`; given a binding primary limit with `minutes_remaining` 25 and thresholds `minutes_threshold=20, percent_threshold=90, protocol_minutes_threshold=30`, expects `("pause", reasons)` where some reason contains `protocol margin` (the margin fires above the fixed minutes line)
- [x] `QuotaWindowProbeTest#test_evaluate_pause_protocol_margin_default_floor_is_subsumed`; given the same limit with default thresholds (margin 10), expects `("continue", [])` (the 10-minute default is a floor under the 20-minute line, not a second pause line at normal range)
- [x] `QuotaWindowProbeTest#test_evaluate_pause_protocol_margin_boundary_is_strict`; given `minutes_remaining` exactly equal to `protocol_minutes_threshold`, expects `("continue", [])` (mirrors the strict `<` of the minutes line)
- [x] `QuotaWindowProbeTest#test_secondary_binding_margin_stays_report_only`; given a secondary-only limit set inside the margin with `protocol_minutes_threshold=30`, expects `build_report` to return `pause_decision: pause` and `write_flag_if_paused` to return False with no flag file written (weekly secondary keeps report-only under the margin)
- [x] `QuotaWindowProbeTest#test_cli_min_protocol_minutes_flag_pauses`; given a zcode fixture payload whose binding limit has 25 minutes remaining and `main(["--runtime", "zcode", "--config", <fixture>, "--min-protocol-minutes", "30"])`, expects exit 0 and a stdout report with `pause_decision: pause` and a reason containing `protocol margin`
- [x] `QuotaWindowProbeTest#test_cli_ninety_eight_percent_pause_drill_ac2_witness`; given a zcode fixture payload whose binding limit reports used_percent 98 with 40 minutes remaining and `main(["--runtime", "zcode", "--config", <fixture>, "--min-protocol-minutes", "10"])`, expects exit 0, `pause_decision: pause`, and reasons containing the `used_percent` line (the origin-2 AC2 fixture drill: the pause fires at very high used-percent with wall-clock margin intact, so the protocol runs while budget, not the clock, is the binding constraint)
- [x] `QuotaWindowProbeTest#test_cli_min_protocol_minutes_rejects_negative`; given `main(["--runtime", "zcode", "--config", <fixture>, "--min-protocol-minutes", "-5"])`, expects `SystemExit` with code 2 and a usage error on stderr (0 stays legal and disables the margin; negatives fail loud like `--plan-cost`)
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'` (the new evaluate_pause/build_report tests fail with TypeError on the missing parameter and the new CLI tests fail with `SystemExit(2)` on the unrecognized `--min-protocol-minutes` argument; all pre-existing tests pass)
- [x] Write minimal implementation: module constant `DEFAULT_PROTOCOL_MINUTES_THRESHOLD = 10`; `evaluate_pause(..., protocol_minutes_threshold=DEFAULT_PROTOCOL_MINUTES_THRESHOLD)` appending reason `"minutes_remaining {X} below protocol margin {Y}"` when `minutes_remaining < protocol_minutes_threshold`; thread the parameter through `build_report`, `probe_zcode`, `probe_codex`, `run_probe`; CLI `--min-protocol-minutes` (int, default `DEFAULT_PROTOCOL_MINUTES_THRESHOLD`) wired through `main`, with `parser.error("--min-protocol-minutes must be >= 0")` for negative values (0 stays legal and disables the margin)
- [x] Run → expect GREEN: the probe suite passes (this task only; the budget-guard suite is untouched and still green)
- [x] Commit: `feat: quota probe protocol-completion margin threshold`

### Task 2: Probe plan-cost wave recommendation (origin 1, gaps 1 and 5)

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [x] `QuotaWindowProbeTest#test_build_report_plan_cost_full`; given a binding limit used 50 percent and `plan_cost_percent=40`, expects report fields `wave_recommendation: "full"`, `wave_size: None` (40 <= remaining 50)
- [x] `QuotaWindowProbeTest#test_build_report_plan_cost_split`; given used 80 percent and `plan_cost_percent=40`, expects `wave_recommendation: "split"` and `wave_size: 2` (cost 40 > remaining 20, half-cost 20 <= remaining 20)
- [x] `QuotaWindowProbeTest#test_build_report_plan_cost_pause`; given used 85 percent and `plan_cost_percent=40`, expects `wave_recommendation: "pause"`, `wave_size: None` (half-cost 20 > remaining 15)
- [x] `QuotaWindowProbeTest#test_build_report_plan_cost_boundary_full_at_exact_remaining`; given used 60 percent and `plan_cost_percent=40`, expects `"full"` (cost 40 equals remaining 40; the `<=` boundary is inclusive)
- [x] `QuotaWindowProbeTest#test_build_report_without_plan_cost_has_no_recommendation_fields`; given no `plan_cost_percent`, expects the report to carry neither `plan_cost_percent` nor `wave_recommendation` nor `wave_size` (existing report shape unchanged for callers that omit the flag)
- [x] `QuotaWindowProbeTest#test_cli_plan_cost_split_recommendation`; given a fixture payload with binding used 80 percent and `main([..., "--plan-cost", "40"])`, expects exit 1 (continue) and stdout report `wave_recommendation: "split"`, `wave_size: 2`
- [x] `QuotaWindowProbeTest#test_cli_plan_cost_rejects_out_of_range`; given `main([..., "--plan-cost", "150"])`, `main([..., "--plan-cost", "0"])`, and `main([..., "--plan-cost", "-5"])`, each expects `SystemExit` with code 2 and a usage error on stderr (fail loud at the CLI on both bounds and on non-positive values, never a silent recommendation)
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'` (the new tests fail on missing fields/argument; Task 1's tests stay green)
- [x] Write minimal implementation: `build_report(..., plan_cost_percent=None)`; when provided and status ok, set `plan_cost_percent`, and compute against the binding limit's `used_percent`: `cost <= 100 - used` → `("full", None)`; `cost / 2 <= 100 - used` → `("split", 2)`; else `("pause", None)`; thread through `probe_zcode`, `probe_codex`, `run_probe`; CLI `--plan-cost` (float, default None) with `parser.error("--plan-cost must be within (0, 100]")` for any value outside that range (covers 0, negatives, and values above 100)
- [x] Run → expect GREEN: the probe suite passes
- [x] Commit: `feat: quota probe plan-cost wave recommendation`

### Task 3: Guard observability: armed_by and flag path in the block reason (origin 1, gap 4)

Files:
- `scripts/quota_window_probe.py`
- `agents/hooks/budget-guard/budget_guard_core.py`
- `scripts/test_quota_window_probe.py`
- `scripts/test_budget_guard_hooks.py`

- [x] `QuotaWindowProbeTest#test_write_flag_writes_armed_by_probe`; given a pausing primary limit set and `write_flag_if_paused(..., "pause")`, expects the written flag to contain the line `armed_by=probe`
- [x] Update both adapters' exact-envelope fixtures in `test_budget_guard_hooks.py`: the deny/block reason now ends with ` Budget guard flag: <flag path> (armed by probe).` where `<flag path>` is the fixture `--flag-path`; given the future-dated fixture flag written by the probe path, expects the exact envelope including the suffix
- [x] `BudgetGuardHookTest#test_reason_names_armed_by_manual`; given a fixture flag carrying `armed_by=manual`, expects the reason to end with `(armed by manual)`
- [x] `BudgetGuardHookTest#test_reason_names_armed_by_unknown_when_line_missing`; given a fixture flag with no `armed_by` line, expects the reason to end with `(armed by unknown)`
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'` fails on the exact-envelope updates (the core still emits the old reason), and the probe suite's new armed_by test fails; all other tests pass
- [x] Write minimal implementation: `write_flag_if_paused` appends `armed_by=probe` to the flag lines (after the `plan` line; same first-line-only hardening is unnecessary for a constant, but keep the write inside the existing locked `os.replace` block unchanged); `REASON_TEMPLATE` gains the trailing sentence ` Budget guard flag: {flag_path} (armed by {armed_by}).`; `main()` formats it with `flag_path=str(flag_path)` and `armed_by=fields.get("armed_by", "unknown")`
- [x] Run → expect GREEN: both suites pass
- [x] Refresh the deployed hook copies per the README refresh recipe: copy `zcode.sh`, `codex.sh`, and `budget_guard_core.py` from `agents/hooks/budget-guard/` into `~/.ai-playbook/hooks/budget-guard/` preserving modes (real files, never symlinks); run the deny and pass fixture probes against the deployed paths inside a temp directory (fresh fixture files per script; expect the deny/block envelope whose reason now ends with the `Budget guard flag: ... (armed by probe).` suffix and exit 2 for zcode / exit 0 for codex, then the no-flag pass probes with empty stdout); verify both runtime config `command` values equal the `$HOME`-expanded deployed paths (completion evidence: probe outputs recorded in the session log; the deployed copies otherwise keep emitting the old reason until this re-deploy)
- [x] Commit: `feat: budget-guard block reason carries flag path and armed-by`

### Task 4: Canonical budget gate: schedule-first, margin wiring, between-boundary probes, reconciliation (origin 2, layers 1, 3, 4; origin 1, gap 3)

Files:
- `agents/skills/execute-plan/SKILL.md`

Apply these exact edits (pin text is normative):

- [ ] Facts table: after the `budget_probe_runtime` row add the row `| budget_pause_min_protocol_minutes | Pause when the binding quota window's remaining minutes fall below this protocol-completion margin (the time the boundary's remaining work plus the pause protocol needs) | 10 |`
- [ ] Boundary sentence: replace the gate intro so it reads `At the Step 1.5 and Step 3.5 boundaries, before every Phase 3 worker-wave launch (the Step 3.1 panel launch and the Step 3.3 address launch, single or fanned), before every fold batch and every mechanical audit pass inside a Phase 3 review round (the between-boundary probes), and never mid-task or mid-worker, run:`
- [ ] Probe command line: append `[--min-protocol-minutes <N>] [--plan-cost <percent>]` to the `python3 "$BUDGET_PROBE"` invocation
- [ ] Margin bullet after the exit-codes bullet: `- The margin threshold travels via --min-protocol-minutes from the facts key budget_pause_min_protocol_minutes (fallback 10): the probe also pauses when the binding window's remaining minutes fall below the margin, so a late pause decision still leaves the protocol itself time to complete.`
- [ ] Wave-sizing bullet: `- Forward-looking wave sizing: when the manifest or this run's records name a comparable earlier panel's observed window cost, pass it as --plan-cost <percent>. On wave_recommendation: full launch at full width; on split launch the next panel in waves of the reported wave_size (probe between waves); on pause run the pause protocol below instead of launching. A pause decision always outranks any wave_recommendation: on pause_decision: pause run the pause protocol below instead of launching. Without a recorded comparable cost, omit the flag: the recommendation fields are then absent and the launch decision is unchanged.`
- [ ] Pause protocol reorder (baseline note: the pin below is normative against the canonical Budget gate text verified 2026-09-17 whose pause boundary is non-schedulable: the watcher-schedule call supersedes any pending watcher, writes no `resume_watcher` receipt, runs no scheduler chain, and the orchestrator-created automation carries the pause resume; where an executing tree carries a different shape, apply the same semantic deltas - the boundary record before the manifest append, the resume_scheduled field, the margin and wave wiring, the between-boundary probes - to whatever steps exist rather than importing a foreign wiring). Swap steps 3 and 4 so the boundary record precedes the manifest append, moving both VERBATIM with only their internal step-number references renumbered:
- [x] Facts table: after the `budget_probe_runtime` row add the row `| budget_pause_min_protocol_minutes | Pause when the binding quota window's remaining minutes fall below this protocol-completion margin (the time the boundary's remaining work plus the pause protocol needs) | 10 |`
- [x] Boundary sentence: replace the gate intro so it reads `At the Step 1.5 and Step 3.5 boundaries, before every Phase 3 worker-wave launch (the Step 3.1 panel launch and the Step 3.3 address launch, single or fanned), before every fold batch and every mechanical audit pass inside a Phase 3 review round (the between-boundary probes), and never mid-task or mid-worker, run:`
- [x] Probe command line: append `[--min-protocol-minutes <N>] [--plan-cost <percent>]` to the `python3 "$BUDGET_PROBE"` invocation
- [x] Margin bullet after the exit-codes bullet: `- The margin threshold travels via --min-protocol-minutes from the facts key budget_pause_min_protocol_minutes (fallback 10): the probe also pauses when the binding window's remaining minutes fall below the margin, so a late pause decision still leaves the protocol itself time to complete.`
- [x] Wave-sizing bullet: `- Forward-looking wave sizing: when the manifest or this run's records name a comparable earlier panel's observed window cost, pass it as --plan-cost <percent>. On wave_recommendation: full launch at full width; on split launch the next panel in waves of the reported wave_size (probe between waves); on pause run the pause protocol below instead of launching. A pause decision always outranks any wave_recommendation: on pause_decision: pause run the pause protocol below instead of launching. Without a recorded comparable cost, omit the flag: the recommendation fields are then absent and the launch decision is unchanged.`
- [x] Pause protocol reorder (baseline note: the pin below is normative against the canonical Budget gate text verified 2026-09-17 whose pause boundary is non-schedulable: the watcher-schedule call supersedes any pending watcher, writes no `resume_watcher` receipt, runs no scheduler chain, and the orchestrator-created automation carries the pause resume; where an executing tree carries a different shape, apply the same semantic deltas - the boundary record before the manifest append, the resume_scheduled field, the margin and wave wiring, the between-boundary probes - to whatever steps exist rather than importing a foreign wiring). Swap steps 3 and 4 so the boundary record precedes the manifest append, moving both VERBATIM with only their internal step-number references renumbered:
```markdown
  3. A pause boundary is non-schedulable: record it in one operation through the driver's watcher-schedule call, `python3 scripts/execute_plan_runtime.py --manifest <runtime_state.json> --operation watcher-schedule --input '<probe report JSON plus "plan_path">'`. The code pins a pause boundary to supersede: the operation supersedes and clears any existing pending watcher, writes no `resume_watcher` receipt, and runs no scheduler chain, so no `pending_resume_watcher` survives into the pause and no launchd job is armed by the driver on a pause. The pause resume is carried by the orchestrator-created automation, not by the driver: on a host whose agent runtime supports one-shot scheduled automations, create the automation FIRST (its prompt and fire contract are step 5), then run the watcher-schedule call, so the create result is already on record when the boundary line lands. (The payload `automation` key and the CLI fallback chain belong to a schedulable boundary - a continue with a trusted binding reset epoch: there the create's result is passed as the payload `automation` key so the chain echoes it and arms no launchd job on top of it, and a refused create is dropped from the payload so the chain arms the launchd one-shot, ending report-only if that fails too; never create an automation after the operation already armed a launchd job, which would double-arm the resume - one window, one resume.)
  4. Append a `budget_pause` line to `manifest.md` with the runtime, reset epoch and ISO time, thresholds used (including the protocol margin), and the next step that would have run, plus `resume_scheduled: yes|no`: `yes` when step 3's orchestrator-created automation exists (the create preceded the watcher-schedule call; the call's supersede leaves nothing else pending); `no` when nothing could be scheduled (the report-only ends in steps 6 and 7).
  5. The automation's prompt carries the resume contract, and which half applies follows what the boundary recorded. On a pause boundary (step 3 wrote no receipt) there is nothing for the fire operation to evaluate, so the prompt performs the epoch-checked manual clear itself: execute the plan path, read the `budget_pause` record, apply the Step 0.5 resume rules, clear `~/.ai-playbook/runtime/budget-guard.flag` and `budget-guard.fired` before relaunching work only if the flag's `reset_at_epoch` matches the reset epoch recorded in this run's `budget_pause` record (otherwise leave both in place and report the mismatch: the flag encodes a different, still-live window, another runtime's or a newer window of the same runtime; if the flag (or fired marker) is already absent, nothing is armed, so proceed with the relaunch and note the pre-cleanup in the record), re-reading the flag immediately before each deletion and aborting the clear if its `reset_at_epoch` changed since the match check (mirror the hook core's re-read-before-unlink pattern: a concurrent probe may have replaced the flag in between), and stand down if the plan is archived or a peer session resumed it. This manual procedure is the no-CLI fallback path of the protocol; on a pause boundary it is the only path. When a pending receipt exists (a Standing resume watcher scheduled at a continue boundary), the prompt's fire contract is the driver's fire entry `python3 scripts/execute_plan_runtime.py --manifest <runtime_state.json> --operation watcher-fire --input '{"flag_path": "~/.ai-playbook/runtime/budget-guard.flag"}'`: the operation re-reads machine state, applies the fences and the four stand-down checks, and clears the guard flag and fired marker only on a resume decision, so the prompt must not re-apply the stand-down checks or delete the guards by hand. A cleanup call issued before the window resets may itself be denied once by the guard; retry it after that single block. (This step is the prompt and fire contract only: the create ordering and the launchd fallback of a schedulable boundary live in step 3.)
  6. On a host with no automation capability there is no carrier for the pause resume: the pause protocol runs no launchd fallback (the launchd one-shot belongs to the scheduler chain of a schedulable boundary, and a pause boundary runs no chain, so nothing is armed at the pause). Record the boundary through the step 3 operation (it supersedes any pending watcher, writes no receipt, runs no chain), keep the guard flag armed per step 2, and report the pause in `manifest.md` with the exact manual resume command and reset time from the operation's output (`manual_command`, `execute <plan-path>` at the recorded reset time): the resume is manual - the user runs it, or the next session re-enters through Step 0.5 after the window resets.
  7. When the binding limit is the weekly `secondary` window, do not schedule (step 4's record was already written with `resume_scheduled: no`): report for user decision.
```
  and update step 2's secondary exception tail to read `... the record applies to every binding window, so continue with step 4 (record) and step 7 (secondary report-only), skipping the scheduling steps (3, 5, and 6).` This task moves the existing driver-operation steps verbatim (the non-schedulable watcher-schedule record, the two-half prompt and fire contract, the launchd-only narration) and edits only the ordering, the record line's fields, and the two new bullets; the `paused` state row and the driver operations themselves are NOT edited, and the subsection's "(exact command in the pause protocol above)" pointer keeps resolving because the exact commands move with their steps.
- [ ] Reconciliation paragraph after the resume-prompt paragraph: `**budget_pause reconciliation:** every resume path (the Step 0.5 resume, a fired standing resume watcher, and any manual resume) first checks the run's latest budget_pause record: when it carries resume_scheduled: no, the resume path reconciles it by completing the scheduling step before any other resume work (schedule at reset time plus one minute when the window is still in the future; when the window has already reset, note the reconciliation in the manifest and continue). Exception: a record whose binding is the weekly secondary window stays report-only - report for user decision and never schedule.`
- [ ] Standing resume watcher boundary coverage: in the "At every budget-gate boundary whose decision is continue..." paragraph, insert `including the between-boundary probes (fold batches and mechanical audit passes)` after "continue and whose probe report contains a trusted binding reset epoch" context so watcher replacement covers the new probe points
- [ ] Run → expect GREEN: no suite runs this task (prose only); `grep -c 'budget_pause_min_protocol_minutes' agents/skills/execute-plan/SKILL.md` is at least 1 and the Gate G canonical order check from the Validation block passes when run standalone
- [ ] Commit: `docs: execute-plan budget gate schedule-first, margin, between-boundary probes`
- [x] Reconciliation paragraph after the resume-prompt paragraph: `**budget_pause reconciliation:** every resume path (the Step 0.5 resume, a fired standing resume watcher, and any manual resume) first checks the run's latest budget_pause record: when it carries resume_scheduled: no, the resume path reconciles it by completing the scheduling step before any other resume work (schedule at reset time plus one minute when the window is still in the future; when the window has already reset, note the reconciliation in the manifest and continue). Exception: a record whose binding is the weekly secondary window stays report-only - report for user decision and never schedule.`
- [x] Standing resume watcher boundary coverage: in the "At every budget-gate boundary whose decision is continue..." paragraph, insert `including the between-boundary probes (fold batches and mechanical audit passes)` after "continue and whose probe report contains a trusted binding reset epoch" context so watcher replacement covers the new probe points
- [x] Run → expect GREEN: no suite runs this task (prose only); `grep -c 'budget_pause_min_protocol_minutes' agents/skills/execute-plan/SKILL.md` is at least 1 and the Gate G canonical order check from the Validation block passes when run standalone
- [x] Commit: `docs: execute-plan budget gate schedule-first, margin, between-boundary probes`

### Task 5: Plans mirror deltas (origin 2, layers 1-4)

Files:
- `agents/skills/plans/SKILL.md`

Apply these exact edits to the "Budget gate (plan-authoring pause and resume)" section (pin text is normative):

- [ ] Threshold resolution: the opening line gains the margin key so it resolves `budget_pause_minutes_before_reset` (fallback `20`), `budget_pause_max_used_percent` (fallback `90`), `budget_pause_min_protocol_minutes` (fallback `10`), and `budget_probe_runtime` (fallback `auto`, unchanged semantics)
- [ ] Boundaries: the "Boundaries:" paragraph reads `...the orchestrator runs the probe before launching each review-plan round in the Plan Quality Gate loop, before every fold batch and every mechanical audit pass inside the loop (the between-boundary probes), and before the final done handoff; never mid-worker and never mid-fold.`
- [ ] Probe invocation: the example command gains `[--min-protocol-minutes <N>] [--plan-cost <percent>]`
- [ ] Pause protocol reorder: swap steps 3 and 4 so the boundary record precedes the manifest append, moving the create-first step VERBATIM (only its reference to the record step renumbers): new step 3 = the current step 4 text exactly ("On a host whose agent runtime supports one-shot scheduled automations, create the resume automation FIRST at the reset time rounded up to the whole minute plus one, then record the boundary through `plans-watcher-schedule`: ... so the created automation - not the driver - carries the resume." including the full two-half prompt and fire contract and the cleanup-call retry), and new step 4 = the current step 3 record line with the additions `thresholds used (including the protocol margin)` and `resume_scheduled: yes|no` - `yes` when step 3's orchestrator-created automation exists (the call's supersede leaves nothing else pending); `no` when nothing could be scheduled (the report-only and weekly-secondary cases).
- [ ] Step 5 (fallback) is NOT edited: the current text already carries the schedulable-boundary launchd compression and the pause-boundary manual-resume narration; step 4's new `resume_scheduled` field covers its record semantics.
- [ ] Step 2 secondary wording becomes: `...write no flag, still append the record (step 4) with resume_scheduled: no, schedule nothing, and report for user decision instead.`
- [ ] Reconciliation sentence after the pause protocol: `Every resume path (the scheduled automation's prompt, a fired standing resume watcher, and any manual resume) first reconciles a budget_pause record carrying resume_scheduled: no by completing the scheduling step before continuing work. Exception: a record whose binding is the weekly secondary window stays report-only - report for user decision and never schedule.`
- [ ] Watcher branch: the known-binding-only watcher sentence reads `...schedule the same standing resume watcher the canonical Standing resume watcher subsection defines, at the authoring boundaries (before launching each review-plan round in the Plan Quality Gate loop; at every between-boundary probe inside the loop; before the final done handoff)...` (the lead-in drops "at both authoring boundaries" so it does not head a three-item list)
- [ ] Mirror schedule step: the swapped step 3 is the current step 4 text VERBATIM; no `boundary_kind` payload key is added (the pause boundary is non-schedulable and the driver's supersede-only classification is preserved).
- [ ] Wave-sizing sentence (authoring sink): after the probe invocation example add: `When the notes name a comparable earlier round panel's observed window cost, pass it as --plan-cost <percent> and follow the report's wave_recommendation (full / split with wave_size / pause; on pause run the pause protocol instead of launching the round). A pause decision always outranks any wave_recommendation: on pause_decision: pause run the pause protocol instead of launching. Without a recorded comparable cost, omit the flag.`
- [ ] Run → expect GREEN: prose only; the Gate G mirror order check passes standalone
- [ ] Commit: `docs: plans budget gate mirror deltas for pause mechanics`
- [x] Threshold resolution: the opening line gains the margin key so it resolves `budget_pause_minutes_before_reset` (fallback `20`), `budget_pause_max_used_percent` (fallback `90`), `budget_pause_min_protocol_minutes` (fallback `10`), and `budget_probe_runtime` (fallback `auto`, unchanged semantics)
- [x] Boundaries: the "Boundaries:" paragraph reads `...the orchestrator runs the probe before launching each review-plan round in the Plan Quality Gate loop, before every fold batch and every mechanical audit pass inside the loop (the between-boundary probes), and before the final done handoff; never mid-worker and never mid-fold.`
- [x] Probe invocation: the example command gains `[--min-protocol-minutes <N>] [--plan-cost <percent>]`
- [x] Pause protocol reorder: swap steps 3 and 4 so the boundary record precedes the manifest append, moving the create-first step VERBATIM (only its reference to the record step renumbers): new step 3 = the current step 4 text exactly ("On a host whose agent runtime supports one-shot scheduled automations, create the resume automation FIRST at the reset time rounded up to the whole minute plus one, then record the boundary through `plans-watcher-schedule`: ... so the created automation - not the driver - carries the resume." including the full two-half prompt and fire contract and the cleanup-call retry), and new step 4 = the current step 3 record line with the additions `thresholds used (including the protocol margin)` and `resume_scheduled: yes|no` - `yes` when step 3's orchestrator-created automation exists (the call's supersede leaves nothing else pending); `no` when nothing could be scheduled (the report-only and weekly-secondary cases).
- [x] Step 5 (fallback) is NOT edited: the current text already carries the schedulable-boundary launchd compression and the pause-boundary manual-resume narration; step 4's new `resume_scheduled` field covers its record semantics.
- [x] Step 2 secondary wording becomes: `...write no flag, still append the record (step 4) with resume_scheduled: no, schedule nothing, and report for user decision instead.`
- [x] Reconciliation sentence after the pause protocol: `Every resume path (the scheduled automation's prompt, a fired standing resume watcher, and any manual resume) first reconciles a budget_pause record carrying resume_scheduled: no by completing the scheduling step before continuing work. Exception: a record whose binding is the weekly secondary window stays report-only - report for user decision and never schedule.`
- [x] Watcher branch: the known-binding-only watcher sentence reads `...schedule the same standing resume watcher the canonical Standing resume watcher subsection defines, at the authoring boundaries (before launching each review-plan round in the Plan Quality Gate loop; at every between-boundary probe inside the loop; before the final done handoff)...` (the lead-in drops "at both authoring boundaries" so it does not head a three-item list)
- [x] Mirror schedule step: the swapped step 3 is the current step 4 text VERBATIM; no `boundary_kind` payload key is added (the pause boundary is non-schedulable and the driver's supersede-only classification is preserved).
- [x] Wave-sizing sentence (authoring sink): after the probe invocation example add: `When the notes name a comparable earlier round panel's observed window cost, pass it as --plan-cost <percent> and follow the report's wave_recommendation (full / split with wave_size / pause; on pause run the pause protocol instead of launching the round). A pause decision always outranks any wave_recommendation: on pause_decision: pause run the pause protocol instead of launching. Without a recorded comparable cost, omit the flag.`
- [x] Run → expect GREEN: prose only; the Gate G mirror order check passes standalone
- [x] Commit: `docs: plans budget gate mirror deltas for pause mechanics`

### Task 6: Review-loop between-boundary probes (origin 2, layer 3)

Files:
- `agents/skills/review-loop/SKILL.md`

- [x] Add a subsection `### Budget gate (between-boundary probes)` immediately before `## Exit criteria (default)` with exactly this content:
```markdown
At loop start and before every fix or fold batch and every mechanical audit pass between review rounds (the between-boundary probes), run the quota probe per the canonical Budget gate protocol (agents/skills/execute-plan/SKILL.md, Budget gate section): three-step probe resolution, thresholds from `.ai-playbook/facts.md` (fallbacks 20 / 90 / 10 via `--minutes-before` / `--max-percent` / `--min-protocol-minutes`), and pass `--write-flag ~/.ai-playbook/runtime/budget-guard.flag`. Parse `pause_decision` from the stdout JSON report, never from the exit code. On `pause`, run the canonical pause protocol with the current round's staging doc as the record sink: schedule the resume automation FIRST (reset rounded up to the whole minute plus one; self-contained prompt to re-enter this loop at the recorded next step, apply the canonical flag-clear match rules, and stand down if the loop exited clean or a peer session resumed the work), then append a `budget_pause` record to the staging doc with the runtime, reset epoch and ISO time, thresholds used, next step, and `resume_scheduled: yes|no` (at loop start, before any staging doc exists, record it in the loop's session notes). Weekly `secondary` bindings stay report-only: the probe writes no flag, nothing is scheduled, and the outcome is reported for user decision; a record bound to the weekly secondary window is never scheduled by a resume path. On `continue`, record one outcome line `budget-gate: continue, <binding>, <used_percent>%` in the round's staging doc (at loop start, before any staging doc exists, record it in the loop's session notes or the first round's staging doc once it exists) and proceed. Every resume path reconciles a `budget_pause` record carrying `resume_scheduled: no` by completing the scheduling step before continuing work; a record whose binding is the weekly secondary window stays report-only and is never scheduled. This skill schedules no standing resume watcher (it owns no machine-state home); the between-boundary probes and the pause protocol are its only budget-gate surface.
```
- [x] Run → expect GREEN: prose only; `grep -c 'between-boundary probe' agents/skills/review-loop/SKILL.md` is at least 1
- [x] Commit: `docs: review-loop between-boundary budget-gate probes`

### Task 7: Fold the Codex drive procedure into the budget-guard README (origin 4)

Files:
- `agents/hooks/budget-guard/README.md`
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` (Canonicality paragraph only; the item itself moves to completed at plan completion)

- [ ] Replace the `### Open envelope question` section content so the README becomes the canonical home: keep the question statement (codex binary names `permissionDecisionReason`; adapter emits the flat deny envelope; acceptance unverified until the trust prompt is approved) and fold in, from `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`: the Ship-when drive procedure as it stands at fold time per docs/plans/completed/2026-09-15-budget-gate-decision-table-attribution.md (currently: step-1 pre-drive session check; step-2 pre-drive evidence: fired-marker baseline stat plus co-registered matcher-`.*` hooks trust status (the step also owns stale-marker removal and the live-window abort-and-investigate path); arm the canonical flag with `runtime=codex`, `reset_at_epoch` at now + 10 minutes, and matching `reset_at_iso`; drive one real tool call in a trusted Codex session and check the denial reason embeds the armed `reset_at_iso`; post-drive cleanup of flag AND fired marker, with immediate removal on an aborted drive (plus a diff-verified hooks-backup restore, with fallback order and backup retirement, when the row-2 contingency was invoked)), the four-row post-drive decision table (headers `Post-drive observation | Verdict | Follow-through`, first row `A denial is observed AND the denial reason embeds the armed flag's reset_at_iso`), the row-2 contingency steps plus abort clause (superseding the retired attribution caveat), the abort and retirement protocol (stop trigger, restore branches, superseded-edit branch, retirement, standing order), and the real-pause observation paragraph with its attribution-gate sentence (a completed pause record without an observed backstop block proves the probe path only)
- [ ] End the section with the canonicality note: `Canonical home since 2026-09-17 (plan 2026-09-17-budget-gate-pause-mechanics-drive); docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md is history-only after this fold.`
- [ ] Update the codex backlog item's Canonicality paragraph (`docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`) to record the move: the canonical home of the open question, Ship-when drive procedure, and post-drive decision table is `agents/hooks/budget-guard/README.md` ("Open envelope question") since 2026-09-17 (plan 2026-09-17-budget-gate-pause-mechanics-drive); the item is history-only from that date and moves to completed at plan completion
- [ ] Update the reason-string documentation (fixture recipe and exit conventions) to the new text ending ` Budget guard flag: <flag path> (armed by <armed_by>).`
- [ ] Run → expect GREEN: prose only; Gate E greps pass standalone
- [ ] Commit: `docs: fold codex deny-envelope drive procedure into budget-guard README`
- [x] Replace the `### Open envelope question` section content so the README becomes the canonical home: keep the question statement (codex binary names `permissionDecisionReason`; adapter emits the flat deny envelope; acceptance unverified until the trust prompt is approved) and fold in, from `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`: the Ship-when drive procedure as it stands at fold time per docs/plans/completed/2026-09-15-budget-gate-decision-table-attribution.md (currently: step-1 pre-drive session check; step-2 pre-drive evidence: fired-marker baseline stat plus co-registered matcher-`.*` hooks trust status (the step also owns stale-marker removal and the live-window abort-and-investigate path); arm the canonical flag with `runtime=codex`, `reset_at_epoch` at now + 10 minutes, and matching `reset_at_iso`; drive one real tool call in a trusted Codex session and check the denial reason embeds the armed `reset_at_iso`; post-drive cleanup of flag AND fired marker, with immediate removal on an aborted drive (plus a diff-verified hooks-backup restore, with fallback order and backup retirement, when the row-2 contingency was invoked)), the four-row post-drive decision table (headers `Post-drive observation | Verdict | Follow-through`, first row `A denial is observed AND the denial reason embeds the armed flag's reset_at_iso`), the row-2 contingency steps plus abort clause (superseding the retired attribution caveat), the abort and retirement protocol (stop trigger, restore branches, superseded-edit branch, retirement, standing order), and the real-pause observation paragraph with its attribution-gate sentence (a completed pause record without an observed backstop block proves the probe path only)
- [x] End the section with the canonicality note: `Canonical home since 2026-09-17 (plan 2026-09-17-budget-gate-pause-mechanics-drive); docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md is history-only after this fold.`
- [x] Update the codex backlog item's Canonicality paragraph (`docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`) to record the move: the canonical home of the open question, Ship-when drive procedure, and post-drive decision table is `agents/hooks/budget-guard/README.md` ("Open envelope question") since 2026-09-17 (plan 2026-09-17-budget-gate-pause-mechanics-drive); the item is history-only from that date and moves to completed at plan completion
- [x] Update the reason-string documentation (fixture recipe and exit conventions) to the new text ending ` Budget guard flag: <flag path> (armed by <armed_by>).`
- [x] Run → expect GREEN: prose only; Gate E greps pass standalone
- [x] Commit: `docs: fold codex deny-envelope drive procedure into budget-guard README`

### Task 8: F7 tidy: `_git_stdout` fixture helper (origin 3, F7)

Files:
- `scripts/test_execute_plan_runtime.py`

- [x] Add next to `_git` (two-line body so the definition can never satisfy Gate B's single-line forbidden pattern):
```python
def _git_stdout(self, *args, cwd=None):
    # Stripped-stdout form of the hermetic git helper for fixture assertions.
    completed = self._git(*args, cwd=cwd)
    return completed.stdout.strip()
```
- [x] Migrate exactly 20 call sites of the shape `_git(...).stdout.strip()` to `self._git_stdout(...)` (count re-baselined 19 to 20 at execution, 2026-09-18: effe76dc added the 20th chain; authoring-time count was 19)
- [x] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py'` passes before and after (pure refactor, characterization net is the existing suite); `grep -c 'self\._git_stdout(' scripts/test_execute_plan_runtime.py` is exactly 20 and the old pattern has zero matches (count re-baselined, see above)
- [x] Commit: `test: introduce _git_stdout fixture helper and migrate strip chains` (separate tidy commit; no functional change mixed in)

### Task 9: Final validation

Files:
- none (verification only)

- [x] Run the full Validation Commands block above → expect exit 0 with `VALIDATION OK` (Gate A suites green; Gate B count exactly 20 (re-baselined 19 to 20, effe76dc); Gates C-H green; Gate I format scans clean)
- [x] Verify every checkbox in this plan is `[x]`; commit any residual checkbox updates: `test: final validation sweep green (task 9; validation block exit 0; checkboxes [x])`
