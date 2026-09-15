# Plan: Budget-gate family residuals

Origins (backlog items, scope of record; read each in full before executing):
docs/history/backlog/2026-09-12-budget-gate-secondary-pause-record-wording.md,
docs/history/backlog/2026-09-12-runtime-test-git-env-coverage.md,
docs/history/backlog/2026-09-11-quota-probe-calibration-fallback.md,
docs/history/backlog/2026-09-14-budget-guard-deployed-hook-copies.md,
docs/history/backlog/2026-09-14-budget-probe-codex-fail-open-diagnostics-collapse.md,
docs/history/backlog/2026-09-14-budget-probe-vacuous-resourcewarning-witness.md,
docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md (Ship-when drive; canonical home of the decision table; stays open after this plan).
Conditional rider: docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md (applies only if the drive's outcomes contradict the fixture probes; stays open).
Predecessors: docs/plans/completed/2026-09-11-execute-plan-runtime-guardrails.md and docs/plans/completed/2026-09-13-budget-gate-quota-fixes.md (built the probe, budget gates, backstop hook, and registrations this plan repairs and completes).
Reviews: docs/reviews/2026-09-14-plan-review-budget-gate-family-residuals-r*.md (review rounds; latest round's verdict governs).

## Terms

- **Pause protocol**: the numbered pause steps in the execute-plan Budget gate section (canonical home); the plans skill Budget gate section mirrors it at plan-authoring boundaries.
- **budget_pause record**: the unconditional pause audit line appended to the run manifest (execute-plan) or the plan requirements buffer (plans mirror); written for every binding window, including `secondary`.
- **Binding window**: the quota limit whose `reset_at_epoch` is earliest; `primary` is the 5-hour window, `secondary` the weekly window. A `secondary` binding stays report-only: no guard flag write, no scheduling, user decides.
- **Guard flag / fired marker**: `~/.ai-playbook/runtime/budget-guard.flag` and `budget-guard.fired`; host-global, written by the probe (flag) and the backstop hook (marker).
- **Deny envelope**: the codex adapter's `{"permissionDecision": "deny", "reason": ...}` stdout contract; live acceptance by the codex binary is the open envelope question (origin 7).
- **Deployed copies**: pinned real-file copies of the hook trio under `~/.ai-playbook/hooks/budget-guard/`, refreshed by an explicit deploy-and-smoke-check step; distinct from the repo working tree the current registrations execute.
- **Kind calibration**: the ZCode `TOKENS_LIMIT`/`TIME_LIMIT` to `primary`/`secondary` mapping check against an observed local exhaustion line.

## Assumptions

- assume the pause-record fix lands in both homes of the clause; basis: the plans skill Budget gate section declares execute-plan's section the canonical home that wins on conflict, and the mirror (agents/skills/plans/SKILL.md line 549) carries the same record-skipping secondary clause, so fixing only the canonical home leaves the same audit-trail hole active at plan-authoring boundaries; this is one clause fixed at its two homes, not a second concern.
- assume the ResourceWarning replacement keeps the `simplefilter("error", ResourceWarning)` escalation and adds `sys.unraisablehook` recording; basis: mutation probes on 2026-09-14 (python 3.14.7): with the escalation removed the implicit-close warning is default-ignored and records nothing (the recipe's literal "replace the escalation" reading is vacuous); with the escalation kept, deleting `exc.close()` records exactly one ResourceWarning unraisable and the restored close records none (probes A/B/C in the authoring session log).
- assume the codex reason split adds a record-presence predicate instead of changing `parse_codex_rollout`'s `list[dict]` return contract; basis: the zcode sibling already distinguishes shapes via a payload predicate (`_has_limits_array`, probe line 77) plus a distinct reason (line 388); callers of `parse_codex_rollout` (probe_codex and tests) keep the list contract.
- assume the deployed hook copies are real files (never symlinks) under `~/.ai-playbook/hooks/budget-guard/` and both registrations keep absolute paths, now pointing at the deployed copies; basis: the origin item's option text; the adapters resolve `budget_guard_core.py` relative to their own directory (`CORE="$(cd "$(dirname "$0")" && pwd)/budget_guard_core.py"`), so the trio is self-contained; JSON config files do not expand `~`, so an absolute deployed path is the only portable-enough form (README Registration note).
- assume origins 7 (deny-envelope drive) and the attribution rider stay open after this plan; basis: the drive is gated on the human-approved first-start Codex hook trust prompt, and the rider applies only to contradicting drive outcomes; this plan records the Ship-when follow-through and closes nothing about the envelope question.
- assume the known runtime-suite failure `test_shared_skill_bodies_remain_runtime_neutral` (a `codex` mention in the plans SKILL.md Budget gate prose) is pre-existing and out of scope; basis: reproduced 2026-09-14 on committed state (136 tests, 1 failure), introduced by the predecessor plan's plans-skill section, unrelated to any clause this plan edits; validation gates assert "no failure other than this baseline" so a peer fixing it cannot break the gate.

Decision points requiring a grill: none remain.

## Design Invariants (CR Guard)

- Fail-open preservation: no new code path in the probe or hooks may block on absent, stale, or malformed data; the unknown-status and empty-stdout pass paths are contracts.
- Exit conventions unchanged: zcode block exit 2 with `{"decision": "block", ...}`; codex block exit 0 with the deny envelope; pass exit 0 empty stdout.
- `parse_codex_rollout` keeps its `list[dict]` return contract; only the reason selection in `probe_codex` changes.
- The `secondary` binding stays report-only: the fix makes the `budget_pause` record unconditional, never the flag write or the scheduling.
- The redirect-blocking assertions of `test_zcode_transport_never_follows_redirects` (status unknown, 302 reason, `hits == []`) survive the witness reshape verbatim in behavior.
- Host-global flag semantics and the fired-marker anti-thrash rule are untouched by this plan.

## Gist & Examples

Six residuals from the budget-gate family's review rounds stayed open after the predecessor plans hit their round caps. Each is small; together they close the family's executable surface and leave exactly one human-gated question open.

**Before (today), pause record.** When a budget pause binds on the weekly `secondary` window, execute-plan's pause protocol step 2 says "skip to the report-for-user-decision step": the run reports and stops, but step 3, the unconditional `budget_pause` manifest record, never runs. The one pause variant a user must investigate manually is the one variant with no audit trail. The plans skill mirror carries the same clause, so a plan-authoring pause on `secondary` also drops its record.

**After.** The secondary clause skips only the flag/scheduling steps; step 3's record runs for every binding window. A `secondary` pause today therefore leaves a `budget_pause` record naming the runtime, reset epoch and ISO time, thresholds, and the next step that would have run, then reports for user decision without scheduling anything.

**Before, codex diagnostics.** A codex-path `status: unknown` says `rollout carried no rate_limits record` whether the newest rollout had no `rate_limits` record at all or had one whose every window was dropped by per-entry validation (non-mapping window, missing `resets_at`, non-finite or out-of-range `used_percent`). Diagnosis requires opening the rollout by hand.

**After.** The two shapes get two reasons: a record-less rollout keeps `rollout carried no rate_limits record`; a record whose windows all dropped yields `rollout rate_limits record carried no usable windows`, aligned with the zcode sibling's `zcode quota response carried no usable limits`.

**Before, ResourceWarning witness.** `test_zcode_transport_never_follows_redirects` claims that deleting `exc.close()` from `urllib_transport` makes its `warnings.simplefilter("error", ResourceWarning)` plus `gc.collect()` escalation fail the test. On python 3.14 that is false (mutation-verified 2026-09-14): the warning-as-error raises inside the HTTPError file object's destructor, and CPython converts it into an unraisable that prints and never propagates to the `gc.collect()` call site; the test stays green with the mutation in place.

**After.** The witness records unraisables: `sys.unraisablehook` is replaced (and restored in `finally`) with a list-appending hook around the probe call plus the forced collection pass, and a new assertion fails when any recorded unraisable has `exc_type` ResourceWarning. Deleting `exc.close()` now fails the test (probed: exactly one recorded unraisable, message "Implicitly cleaning up <HTTPError 302: 'Found'>" surfacing through tempfile's `_TemporaryFileCloser.__del__`, because the 3.14 HTTPError body is tempfile-backed); the intact transport records nothing. The redirect-blocking assertions are untouched.

**Before, git-env coverage.** The runtime test harness hermeticity fix applied `self._git_env` (GIT_CONFIG_GLOBAL/SYSTEM pinned to /dev/null) at 8 of 56 git subprocess call sites; the other 48 (commit, checkout, rebase, cherry-pick, commit-tree, reset helpers) inherit host config, so `commit.gpgsign`, `core.hooksPath`, or `sequence.editor` on a configured host fail or skew fixture repos.

**After.** One `self._git(*args)` helper always injects `self._git_env`, and every remaining site routes through it, so a new call site cannot skip hermeticity by forgetting the env.

**Before, deployed hook copies.** Both runtime configs register the budget-guard hooks by absolute path into this repository's working tree, so every tool call of every future session executes whatever the checkout currently contains: a mid-edit state, a branch switch, or a moved checkout transiently breaks or disables the backstop host-wide.

**After.** Pinned real-file copies of the trio live under `~/.ai-playbook/hooks/budget-guard/`, deployed by an explicit copy-then-smoke-check step, and both configs point at the deployed paths. Hook behavior no longer tracks the checked-out branch; refreshes are an explicit re-deploy.

**Before, calibration fallback.** The `ZCODE_KIND_MAP` comment points to "the task log" for the calibration note (a dead pointer after the authoring session ended) and states no fallback for a host with no observable local exhaustion line.

**After.** The comment carries the procedure itself: cross-check `nextResetTime` of both kinds against the observed exhaustion line; when none is observable (fresh host, rotated logs, never-exhausted window), calibrate against a live `nextResetTime` progression across two probe calls spaced apart, or record the mapping as provisionally documented with an explicit note in the run log; never skip the calibration silently.

**Ship when (not in tasks).** The deny-envelope drive of origin 7 runs after the user approves the Codex hook trust prompt (re-armed by the deployed-copy repoint in Task 6); its decision table, the fired-marker discriminations, and the rider's attribution isolation on contradicting outcomes stay owned by the backlog item. A real budget pause completing end-to-end with the backstop block observed (fired marker at block time or block reason in the transcript) remains the live proof of the enforcement path.

## Evaluation Criteria

**Quality dimensions:**
- correctness: probe suite, budget-guard hooks suite, and runtime harness suite run with no failure other than the pinned baseline (`test_shared_skill_bodies_remain_runtime_neutral`); the two codex unknown-shapes produce the two distinct reasons; the witness mutation check flips the test RED with `exc.close()` deleted and GREEN restored.
- audit-trail completeness: a `secondary`-bound pause still appends the `budget_pause` record in both the canonical protocol and the plans mirror; only scheduling is skipped.
- hermeticity: zero git subprocess call sites in `scripts/test_execute_plan_runtime.py` run without `self._git_env`; the 8 pre-covered sites remain covered.
- docs alignment: the deployed-copy registration schema and refresh recipe live in the budget-guard README Registration section; no stale live-worktree registration prose remains there; the calibration fallback lives at the `ZCODE_KIND_MAP` comment with the dead task-log pointer gone.
- maintainability: the new reason string exists exactly once in the probe module; the record-less reason exactly once; the predicate is a pure module-level function.

**Done when:**
- All Validation Commands pass on the final tree, including the negated sweeps for every removed clause and pointer, and the plan readiness validator exits clean on the final bytes.
- The deployed trio passes its deny and pass fixture probes from the deployed paths, and both runtime configs parse with the budget-guard commands pointing at the deployed paths.
- The backlog disposition of Task 7 is recorded: origins 1-6 items move to the backlog completed directory at plan completion; the two live-question items stay open.

**Ship when:**
- The user approves the first-start Codex hook trust prompt after the Task 6 repoint, and the single live drive of docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md runs to a decision-table verdict, applying the rider's attribution isolation only if an outcome contradicts the fixture probes.
- One real budget pause completes end-to-end on at least one runtime with the backstop block observed (fired marker written at block time recording the pause's reset epoch, or the block reason observed in the transcript).
- A real `secondary`-bound pause leaves its `budget_pause` record under the reworded clause (live confirmation of the audit-trail fix).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/quota_window_probe.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/hooks/budget-guard/README.md`

**Tests:**
- `scripts/test_quota_window_probe.py`
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. Host wiring of Task 6 (`~/.ai-playbook/hooks/budget-guard/`, `~/.zcode/cli/config.json`, `~/.codex/hooks.json`) is outside the repository review surface but is task-verified by parse and fixture probes.

**Out of scope; reject unless plan-related:**
- `scripts/test_budget_guard_hooks.py`; reason: unchanged by this plan, runs as a gate only.
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` and `docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md`; reason: open live-question items, untouched by tasks.
- The `codex` mention in the plans SKILL.md Budget gate prose that trips `test_shared_skill_bodies_remain_runtime_neutral`; reason: pre-existing baseline failure from the predecessor plan, unrelated to the clauses this plan edits; pinned, not fixed (a separate capture if anyone chooses to close it).
- `agents/hooks/budget-guard/budget_guard_core.py`, `zcode.sh`, `codex.sh` (repo copies); reason: the trio's logic is frozen; Task 6 copies and re-points them but changes no logic, and review findings there belong to the predecessor plans' surfaces.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# 1. Probe suite (Tasks 1, 2, 5 surfaces).
python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py' > /tmp/val-probe.log 2>&1 \
  || { tail -20 /tmp/val-probe.log; fail "probe suite not green"; }

# 2. Budget-guard hooks suite (Task 6 gate).
python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py' > /tmp/val-hooks.log 2>&1 \
  || { tail -20 /tmp/val-hooks.log; fail "hooks suite not green"; }

# 3. Runtime harness suite (Task 3 surface): no failure other than the pinned
# baseline; tolerates the baseline being fixed by a peer, catches any new one.
python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py' > /tmp/val-runtime.log 2>&1
grep -qE "^Ran [0-9]{2,} tests" /tmp/val-runtime.log || fail "runtime suite did not run to a count"
NEWFAIL="$(grep -c '^FAIL:\|^ERROR:' /tmp/val-runtime.log)"
BASE="$(grep -cE '^FAIL: test_shared_skill_bodies_remain_runtime_neutral|^ERROR: test_shared_skill_bodies_remain_runtime_neutral' /tmp/val-runtime.log)"
test "$((NEWFAIL - BASE))" -eq 0 || fail "new runtime-suite failures (new=$NEWFAIL baseline=$BASE)"

# 4. Git-env consolidation (Task 3): the 8 hermetic sites remain, zero uncovered.
test -f scripts/test_execute_plan_runtime.py || fail "runtime test file missing"
TOTAL="$(grep -cE 'subprocess\.(run|check_output|check_call|call|Popen)\(\s*\[\s*"git"' scripts/test_execute_plan_runtime.py)" \
  || fail "git-subsite grep found nothing (expected the covered sites to remain)"
test "$TOTAL" -ge 8 || fail "covered hermetic sites dropped below 8 (TOTAL=$TOTAL)"
UNCOV="$(grep -E 'subprocess\.(run|check_output|check_call|call|Popen)\(\s*\[\s*"git"' scripts/test_execute_plan_runtime.py | grep -vc '_git_env')" \
  || true
test "$UNCOV" -eq 0 || fail "$UNCOV uncovered git subprocess sites remain"
HELPERCALLS="$(grep -c 'self\._git(' scripts/test_execute_plan_runtime.py)"
test "$HELPERCALLS" -ge 48 || fail "helper call-site floor broken ($HELPERCALLS < 48)"
if grep -qE '^[[:space:]]*\[[[:space:]]*"git",' scripts/test_execute_plan_runtime.py; then
  fail "multiline git subprocess site escapes the hermeticity gate"
fi

# 5. Codex reason split (Task 1): each reason exactly once, predicate present,
# both reasons pinned in tests, updated malformed-shape pin.
test -f scripts/quota_window_probe.py || fail "probe module missing"
test "$(grep -cF 'rollout rate_limits record carried no usable windows' scripts/quota_window_probe.py)" -eq 1 \
  || fail "new distinct reason missing or duplicated in probe"
test "$(grep -cF 'rollout carried no rate_limits record' scripts/quota_window_probe.py)" -eq 1 \
  || fail "record-less reason must remain exactly once in probe"
grep -qF 'rollout_carries_rate_limits' scripts/quota_window_probe.py || fail "record-presence predicate missing"
test -f scripts/test_quota_window_probe.py || fail "probe test file missing"
test "$(grep -cF 'rollout rate_limits record carried no usable windows' scripts/test_quota_window_probe.py)" -ge 2 \
  || fail "new reason not pinned in tests (distinct-shape and updated-pin)"
test "$(grep -cF 'rollout carried no rate_limits record' scripts/test_quota_window_probe.py)" -ge 1 \
  || fail "record-less reason not pinned in tests"

# 6. ResourceWarning witness (Task 2): recording hook present, escalation kept,
# redirect assertions intact.
grep -qF 'unraisablehook' scripts/test_quota_window_probe.py || fail "unraisable recording witness missing"
grep -qF 'simplefilter("error", ResourceWarning)' scripts/test_quota_window_probe.py \
  || fail "escalation filter was removed; the witness is vacuous without it"
grep -qF 'self.assertEqual(hits, [])' scripts/test_quota_window_probe.py \
  || fail "redirect-target assertion missing"

# 7. Pause-record clause (Task 4): old clause gone from both homes, new wording present.
test -f agents/skills/execute-plan/SKILL.md || fail "execute-plan SKILL missing"
if grep -qF 'skip to the report-for-user-decision step' agents/skills/execute-plan/SKILL.md; then
  fail "old secondary clause still skips the record in execute-plan"
fi
grep -qF 'the record applies to every binding window' agents/skills/execute-plan/SKILL.md \
  || fail "new record-always wording missing in execute-plan"
test -f agents/skills/plans/SKILL.md || fail "plans SKILL missing"
if grep -qF 'write no flag, schedule nothing, and report for user decision instead' agents/skills/plans/SKILL.md; then
  fail "old mirror clause still skips the record in plans"
fi
grep -qF 'still append the record' agents/skills/plans/SKILL.md \
  || fail "new mirror record-always wording missing"

# 8. Calibration fallback (Task 5): fallback stated at the mapping comment,
# dead pointer gone. Region-scoped to the ZCODE_KIND_MAP comment block (the
# obligation's location), comment-strip + flatten before matching: the sentence
# lives in a wrapped comment block, so a line-based fixed-string grep can never
# match it. Anchors fail loud so a broken extractor cannot pass vacuously.
grep -q '^# Z.ai limit entry type' scripts/quota_window_probe.py || fail "calibration comment start anchor missing"
grep -q '^ZCODE_KIND_MAP' scripts/quota_window_probe.py || fail "ZCODE_KIND_MAP anchor missing"
CAL="$(sed -n '/^# Z.ai limit entry type/,/^ZCODE_KIND_MAP/p' scripts/quota_window_probe.py | sed -e 's/^[[:space:]]*#[[:space:]]\{0,1\}//' | tr '\n' ' ' | tr -s ' ')"
case "$CAL" in *"Never skip the calibration silently"*) : ;; *) fail "calibration fallback sentence missing at the mapping comment";; esac
case "$CAL" in *"See the task log"*) fail "dead task-log pointer still present";; esac

# 9. Deployed-copy README schema (Task 6 repo side).
test -f agents/hooks/budget-guard/README.md || fail "hook README missing"
grep -qF '.ai-playbook/hooks/budget-guard' agents/hooks/budget-guard/README.md \
  || fail "deployed-copy path schema missing from README"

echo "ALL VALIDATION GATES GREEN"
```

### Task 1: Split the collapsed codex fail-open diagnostics

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [ ] `QuotaWindowProbeTest#test_codex_recordless_rollout_keeps_old_reason`; given a rollout JSONL file with no `rate_limits` record (an unrelated JSON line only), expects `status: unknown` with the reason exactly `rollout carried no rate_limits record`; run → expect GREEN today (pins the surviving shape before the split so the split cannot silently change it)
- [ ] `QuotaWindowProbeTest#test_codex_all_windows_dropped_reason_distinct`; given a rollout whose only `rate_limits` record carries a single malformed window (non-numeric `used_percent`) and no valid sibling, expects `status: unknown` with the reason exactly `rollout rate_limits record carried no usable windows`; run → expect RED today (probe emits the collapsed record-less reason)
- [ ] Update `QuotaWindowProbeTest#test_codex_malformed_used_percent_fail_open`; given each malformed `used_percent` subTest (`"high"`, `None`, `Infinity`), expects the NEW distinct reason (all three subTests are all-windows-dropped shapes); update the stale reason quote in the test comment; keep the trailing healthy-sibling case (one healthy + one malformed window parses the healthy window, report `status: ok`) unchanged; run → expect the pin change RED until the probe change lands
- [ ] GREEN: add a pure module-level predicate `rollout_carries_rate_limits(lines) -> bool` next to `parse_codex_rollout` (json.loads per stripped line, `_find_rate_limits(record) is not None` on the first record wins, unparseable lines skipped, mirroring the parser's own scan); in `probe_codex`, when `limits` is empty select `rollout rate_limits record carried no usable windows` if the predicate is true over `text.splitlines()` else keep `rollout carried no rate_limits record`; do not change `parse_codex_rollout`'s signature or return contract
- [ ] Run the probe suite → expect GREEN (38 existing + 2 new tests)
- [ ] Commit: `probe: split codex all-windows-dropped fail-open reason`

### Task 2: Replace the vacuous ResourceWarning witness with unraisable recording

Files:
- `scripts/test_quota_window_probe.py`

- [ ] Reshape the witness block in `QuotaWindowProbeTest#test_zcode_transport_never_follows_redirects` (currently `simplefilter("error", ResourceWarning)` + probe call + `gc.collect()`, lines ~333-350): keep the escalation filter inside `warnings.catch_warnings()`; before the `with`, define `_unraisables: list = []` and capture `_orig_hook = sys.unraisablehook`; inside the `with`, set `sys.unraisablehook` to a list-appending recorder and wrap BOTH the probe call and the `gc.collect()` pass in one `try/finally` whose `finally` restores the original hook after the collection pass (recorder installed across probe + collect, matching the Gist; both placements were mutation-tested on 3.14.7 and fire, but this one does not rely on refcount-time finalization of the HTTPError body); update the stale r4 F2 comment to state the python 3.14 mechanics (a warning-as-error raised inside the HTTPError body destructor becomes an unraisable that never propagates to the call site; on 3.14 the body is tempfile-backed, so the recorded warning surfaces through `_TemporaryFileCloser.__del__` as "Implicitly cleaning up <HTTPError ...>")
- [ ] After the existing `self.assertEqual(hits, [])` assertion, add: `self.assertFalse(any(u.exc_type is ResourceWarning for u in _unraisables), [str(u) for u in _unraisables])`; the redirect-blocking assertions (`status: unknown`, `302` reason, `hits == []`) stay verbatim
- [ ] Run the probe suite → expect GREEN on the intact transport (probed 2026-09-14: no false positive from the test's own tempfile machinery; the TemporaryDirectory cleanup sits outside the recording window)
- [ ] Mutation bar (re-run once in this task, record the outcome in the task log): delete `exc.close()` (and its `raise` partner line stays) from `urllib_transport`'s HTTPError branch in `scripts/quota_window_probe.py`, run only this test via `-k test_zcode_transport_never_follows_redirects`, expect exactly one FAILURE whose message lists the recorded ResourceWarning unraisable; restore the probe file to committed bytes and re-run → GREEN
- [ ] Commit: `test: record unraisables so the ResourceWarning witness fires on py3.14`

### Task 3: Route every git subprocess site through one hermetic helper

Files:
- `scripts/test_execute_plan_runtime.py`

- [ ] Characterization baseline (before edits): run `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py'` and record in the task log: 136 tests, the only failure is `test_shared_skill_bodies_remain_runtime_neutral` (pinned baseline; if a peer fixed it meanwhile, zero failures is equally acceptable); capture the count to compare after
- [ ] Add to the fixture base class next to `_git_env` (line ~69): `def _git(self, *args, cwd=None)` running `["git", *args]` with `cwd or self.root`, `env=self._git_env`, `capture_output=True, text=True, check=True`, returning the `CompletedProcess`
- [ ] Route the 48 uncovered sites (counted 2026-09-14: 56 total `subprocess.(run|check_output|check_call|call|Popen)(["git"` sites, 8 covered at lines 72-77 and 127-129) through `self._git`: capture-style sites become `self._git(...).stdout.strip()` chains, assert-style sites drop their explicit `check=True`; sites living in helper methods that take an explicit `root`/tmp path pass `cwd=root`; the 8 covered sites may stay as explicit `subprocess.run(..., env=self._git_env)` calls
- [ ] Escape hatch: a site that genuinely needs non-default subprocess semantics (non-zero exit expected, custom timeout) keeps `subprocess.run` but MUST pass `env=self._git_env`; no such site is known today (all 48 are `check=True`)
- [ ] Run the runtime harness suite → expect the same result as the characterization baseline (136 run, baseline-only failures, nothing new); fixture repos behave identically on hosts without special git config and stop inheriting `commit.gpgsign`/`core.hooksPath`/`sequence.editor`
- [ ] Commit: `test: one hermetic git helper for every fixture subprocess site`

### Task 4: Keep the budget_pause record on a secondary-bound pause

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`

- [ ] In the execute-plan Budget gate pause protocol (step 2, line ~399), replace the exception sentence "Exception: when the binding limit is the weekly `secondary` window, the probe writes no flag at all (nothing is armed); skip to the report-for-user-decision step instead." with: "Exception: when the binding limit is the weekly `secondary` window, the probe writes no flag at all (nothing is armed); the record applies to every binding window, so continue with step 3 and skip only the scheduling steps (4-6)."
- [ ] Align step 7 (line ~404) to: "When the binding limit is the weekly `secondary` window, do not schedule (step 3's record was already written): report for user decision."
- [ ] In the plans SKILL.md mirror pause protocol (line ~549, step 2), replace "When the binding window is the weekly `secondary`, write no flag, schedule nothing, and report for user decision instead." with: "When the binding window is the weekly `secondary`, write no flag, still append the record (the record applies to every binding window), schedule nothing, and report for user decision instead." The mirror's scheduling steps are 4-5; the clause must skip only those.
- [ ] Check the surrounding prose for sibling sentences written from the old contract (the plans mirror's boundary note "The weekly `secondary` binding still writes no flag and schedules nothing." stays true and stays); reword any sentence that still implies the record is skippable
- [ ] No suite runs required (skill-prose edit); the Validation Commands block's gate 7 is the check
- [ ] Commit: `skills: keep the budget_pause record on secondary-bound pauses`

### Task 5: State the calibration fallback where the mapping lives

Files:
- `scripts/quota_window_probe.py` (comment block only, lines ~24-27)

- [ ] Rewrite the `ZCODE_KIND_MAP` comment so the calibration procedure lives with the mapping and the dead pointer is gone; replacement text: "Z.ai limit entry type -> window kind. Kind calibration (do not skip silently): cross-check each type's nextResetTime against the observed exhaustion line in the local ZCode log; TOKENS_LIMIT is the 5-hour window that reports the reset (primary), TIME_LIMIT the weekly secondary window. When no local exhaustion line is observable (fresh host, rotated or cleaned logs, never-exhausted window), calibrate against a live nextResetTime progression observed across two probe calls spaced apart (the moving window is primary), or record the mapping as provisionally documented with the fixture carrying the documented mapping and an explicit note in the run log. Never skip the calibration silently; timezone encoding lives in the user facts document only."
- [ ] No suite runs required (comment-only edit); the Validation Commands block's gate 8 is the check
- [ ] Commit: `probe: state the kind-calibration fallback at the mapping`

### Task 6: Deploy the hook trio and repoint both runtime configs

Files:
- `agents/hooks/budget-guard/README.md`
- Host wiring (outside the repository; see exception receipt): `~/.ai-playbook/hooks/budget-guard/zcode.sh`, `~/.ai-playbook/hooks/budget-guard/codex.sh`, `~/.ai-playbook/hooks/budget-guard/budget_guard_core.py` *(new)*, `~/.zcode/cli/config.json`, `~/.codex/hooks.json`

Exception receipt (applies to the host-wiring checklist items in this task): exception confirmed by user: the authoring prompt for this plan directs coverage of the offered backlog items including the deployed-copy registration, with standing pre-authorization to accept all recommended options (authoring prompt, 2026-09-14); item: deploy the hook trio as real files and repoint both runtime config registrations; target/environment: `~/.ai-playbook/hooks/budget-guard/`, `~/.zcode/cli/config.json`, and `~/.codex/hooks.json` on this host; confirmation time/session: 2026-09-14 scheduled plans authoring session; why executable now: the target directory is creatable and both configs exist, are user-writable, and get timestamped pre-edit backups; the smoke probes run repo-locally in this session; completion evidence: the deployed trio answers the deny and pass fixture probes from the deployed paths and both configs parse with the budget-guard commands equal to the expanded absolute deployed paths.

- [ ] Back up both configs: `cp ~/.zcode/cli/config.json ~/.zcode/cli/config.json.bak-$(date +%Y%m%d-%H%M%S)-deployed-hooks` and the same shape for `~/.codex/hooks.json`
- [ ] Deploy the trio: `mkdir -p ~/.ai-playbook/hooks/budget-guard` then copy `zcode.sh`, `codex.sh`, `budget_guard_core.py` from the repo checkout (preserving modes; the two scripts stay executable); real files, never symlinks
- [ ] Smoke-check the deployed copies directly: with a future-dated fixture flag in a temp directory (`runtime=codex`, `reset_at_epoch` one hour ahead, matching `reset_at_iso`; all three keys required), run the DEPLOYED `codex.sh --flag-path <tmp>/budget-guard.flag --fired-path <tmp>/budget-guard.fired` and expect exit 0 with the deny envelope embedding the reset ISO; run the deployed `zcode.sh` the same way and expect exit 2 with the block envelope; rerun both with no flag and expect exit 0 with empty stdout; delete all temp fixture files; never write a fixture flag to the canonical `~/.ai-playbook/runtime/budget-guard.flag`
- [ ] Run the repo hooks suite `python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'` → GREEN (repo-side sanity; the deployed probes above are the deployed-side check)
- [ ] Repoint both configs: edit each budget-guard hook `command` value from `<repo-root>/agents/hooks/budget-guard/<script>` to `$HOME-resolved` `~/.ai-playbook/hooks/budget-guard/<script>` (python3 JSON read-modify-write preserving all other entries); verify by parse that each config's budget-guard command EQUALS the expanded absolute deployed path (`os.path.expanduser("~") + "/.ai-playbook/hooks/budget-guard/zcode.sh"` in the zcode config, the `codex.sh` analogue in `~/.codex/hooks.json`), explicitly rejecting a literal-tilde value (JSON config files do not expand `~`; an endswith check cannot discriminate the broken value)
- [ ] Note in the task log: registration changes take effect for sessions started after the edit; the codex trust hash re-arms on the repointed command, so the origin-7 drive's trust-prompt approval must happen again before the drive
- [ ] Update `agents/hooks/budget-guard/README.md` Registration section: replace the live-worktree registration schema and the smoke-check-after-edit paragraph with the deployed-copy schema (commands `~/.ai-playbook/hooks/budget-guard/zcode.sh` / `codex.sh`, absolute paths, JSON does not expand `~`), add a "Deployed copies" subsection carrying the refresh recipe (copy trio, run the fixture probes against the deployed paths, repoint or verify the configs), and drop the stale backlog pointer sentence (the deployed-copies item closes with this plan)
- [ ] Commit: `docs: register budget-guard via deployed copies` (README only; host-only steps have no repository delta)

### Task 7: Backlog disposition and final validation

Files:
- none new (disposition note for the completion pass)

- [ ] Run the full Validation Commands block → every gate green (on the pre-Task-6 tree gate 9 is RED-today; at this point it is GREEN; the only tolerated suite failure anywhere is the pinned runtime baseline)
- [ ] Record the completion-pass disposition in the task log: at plan completion, move exactly these backlog items to the backlog completed directory with `Status: done`: 2026-09-12-budget-gate-secondary-pause-record-wording.md, 2026-09-12-runtime-test-git-env-coverage.md, 2026-09-11-quota-probe-calibration-fallback.md, 2026-09-14-budget-guard-deployed-hook-copies.md, 2026-09-14-budget-probe-codex-fail-open-diagnostics-collapse.md, 2026-09-14-budget-probe-vacuous-resourcewarning-witness.md; leave 2026-09-13-codex-deny-envelope-verification.md and 2026-09-13-budget-gate-decision-table-attribution.md open in the backlog directory (live drive pending)
- [ ] Commit: none (checklist-only task; the disposition executes during the completion pass)
