# Plan: Budget gate quota fixes and plans-skill safeguard

Predecessors: docs/plans/completed/2026-09-11-execute-plan-runtime-guardrails.md (authored the quota probe, budget gate, and guard-flag mechanics this plan repairs and completes)

## Terms

- **Budget gate**: the quota-window pause-and-resume check that runs only at sub-step boundaries; execute-plan has one (Step 1.5 / Step 3.5); this plan adds the matching gate to the plans skill and repairs its data source.
- **Probe**: `scripts/quota_window_probe.py`; fetches or parses the provider quota windows, evaluates pause thresholds, and optionally writes the guard flag. Exit code 0 means pause decision, 1 means continue (including `status: unknown`); `pause_decision` is parsed from stdout JSON, never from the exit code.
- **Monitor endpoint**: `https://api.z.ai/api/monitor/usage/quota/limit`; the live Z.ai quota URL extracted from the shipping ZCode desktop app bundle, replacing the dead `https://api.z.ai/api/quota/limit`.
- **Binding window**: the quota limit whose `reset_at_epoch` is earliest; `primary` is the 5-hour window, `secondary` the weekly/monthly window.
- **Guard flag**: `~/.ai-playbook/runtime/budget-guard.flag`; host-global marker written by the probe only on a pause decision for a non-secondary binding window.
- **Fired marker**: `budget-guard.fired` next to the flag; written by the backstop hook on its first block so the intervention happens once per host per window.
- **Backstop hook**: `agents/hooks/budget-guard/zcode.sh` / `codex.sh` plus `budget_guard_core.py`; a PreToolUse hook that blocks the next tool call while a live guard flag exists.
- **Skills repo root**: resolved at run time via `git rev-parse --show-toplevel` inside the skills repository checkout (per `skills_repo_path` in the user facts document); plan text never hardcodes an absolute host path.

## Assumptions

- assume the monitor endpoint is the stable replacement; basis: extracted from the shipping ZCode desktop app bundle (`app.asar`, build dated 2026-09-13, function `buildZaiQuotaUrl`), and a live probe on 2026-09-13 returned a usable `data.limits` array over HTTP 200.
- assume both raw and `Bearer` Authorization header forms are accepted; basis: both returned HTTP 200 with identical bodies on 2026-09-13; the probe keeps its existing raw form.
- assume the parser needs no code change for the live payload shape; basis: the live body (extra `unit`, `number`, `usage`, `usageDetails`, `level` fields alongside the known `type`/`percentage`/`nextResetTime`) parsed successfully with the current recursive limits-array finder on 2026-09-13; Task 1 pins the shape as characterization.
- assume the deployed runtime copy stays a symlink into the skills repo; basis: every other script in `~/.ai-playbook/scripts/` is a symlink into the repo.
- assume pause thresholds stay at the documented defaults (20 minutes before reset, 90 percent used); basis: execute-plan Configuration table fallbacks; no override keys exist in project facts.
- assume fixing the execute-plan Budget gate probe resolution is in scope; basis: the user accepted the offered fix list (endpoint fix, backstop hook registration in both runtime configs, deployed probe copy), and the deployed copy is reachable in consumer repos only if the gate command resolves it; without the fallback the deployment task is inert outside the skills repo.
- assume the shipped Codex deny envelope may need field-name correction; basis: the codex binary's own error string names `permissionDecisionReason` while the adapter emits `reason`; Task 6 records the open question and a Ship-when decision table instead of changing code on a probe the plan cannot decide (the registered hook does not run until the trust prompt is approved, a human step).

Decision points requiring a grill: none remain.

## Gist & Examples

The execute-plan Budget gate is designed to pause a run before the 5-hour quota window blocks execution, then schedule a resume automation after reset. On this host today the safeguard is inert on the ZCode side and absent on the plans side:

**Before (today).** The probe calls `https://api.z.ai/api/quota/limit`, which now answers `{"code":500,"success":false,"msg":"404 NOT_FOUND"}` inside HTTP 200. The parser finds no `limits` array and fails open: `{"status":"unknown","reasons":["zcode quota response carried no usable limits"]}`. A real ZCode execute-plan run therefore never pauses; when the 5-hour window exhausts mid-run, work dies with the session and nothing reschedules. The Codex side of the probe works (it parses `rate_limits` from the newest rollout), so the defect is ZCode-specific. Additionally: neither runtime has the budget-guard backstop hook registered (`~/.zcode/cli/config.json` PreToolUse carries only the agterm agent-status hook; `~/.codex/hooks.json` has no budget entry), so nothing blocks tool calls mid-pause even when a pause does fire; the deployed copy `~/.ai-playbook/scripts/quota_window_probe.py` is missing, so the gate command `python3 scripts/quota_window_probe.py` (repo-relative) only works from the skills repo root; and the plans skill has no budget gate at all, even though plan authoring runs the same long review loops that get killed by quota exhaustion.

**After (this plan).** The probe returns, for example (entry order preserved from the live payload, `secondary` first): `{"runtime":"zcode","limits":[{"kind":"secondary","used_percent":2.0,"reset_at_epoch":1791551411,...},{"kind":"primary","used_percent":62.0,"reset_at_epoch":1789315099,...}],"binding":"primary","pause_decision":"continue","status":"ok"}` (verified live on 2026-09-13 by pointing the probe at the monitor endpoint; the response shape is unchanged from what the parser already expects, so the code fix is the URL constant only). The gate command resolves the probe from an env override, the repo, or the deployed runtime dir, so it works from any consumer repo. Both runtimes register the backstop hook, so an armed guard flag blocks the next tool call with the recovery steps embedded in the block reason. The plans skill gains a Budget gate of its own: before each review-plan round and before the final `done` handoff, the orchestrator probes the quota window and, on a pause, records the pause, schedules a resume automation at reset plus one minute, and stops; because a pause never edits the plan file, the review sidecar digest stays valid and the resumed run re-enters the loop without re-certification.

**Edge cases that shaped the design.** The weekly `secondary` binding stays report-only (no flag write, no scheduling, user decides), matching the shipped probe and skill rules. A missing or unopenable probe script must degrade to `status: unknown` and continue, never block. Codex hook trust is hash-gated by the codex binary itself (`trusted_hash` entries under `[hooks.state]` in `~/.codex/config.toml`); the hashing algorithm is not reproducible from outside, so first-start trust approval stays a human step (Ship when), and because the registered hook cannot run before that approval, Task 6 records the Codex deny envelope question with a decision table instead of deciding it in-task.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe returns `status: ok` with non-empty `limits` against the live monitor endpoint; both test suites pass; the plans-skill gate section names the same thresholds, boundaries, and resume rules as execute-plan's and pins the canonical-home reference that keeps the duplicated protocol from drifting.
- fail-open safety: unknown status, missing probe script, missing rollout, and malformed payloads all continue the run; no new code path may block on absent data.
- coverage: both runtimes carry the registered backstop hook; fixture probes demonstrate each adapter's block envelope and the no-flag pass path.
- maintainability: the endpoint lives in exactly one constant in `scripts/quota_window_probe.py` and is not duplicated elsewhere in that module; test pins and fixtures that copy the URL verbatim are expected and exempt.
- docs alignment: the budget-guard README registration section matches the schemas verified in this plan (ZCode config shape, Codex hooks.json shape, trust-prompt note), and the provisional Codex warning is replaced with the verified state.

**Done when:**
- `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'` exits 0 (existing tests plus the new URL pin and live-shape characterization).
- `python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'` exits 0.
- `python3 scripts/quota_window_probe.py --minutes-before 20 --max-percent 90` prints a JSON report with `"status": "ok"` and a binding of `primary` or `secondary`.
- The execute-plan Budget gate block and the new plans-skill Budget gate section contain the three-step probe resolution and the grep-verified obligations listed in Tasks 2 and 3.
- `test -L ~/.ai-playbook/scripts/quota_window_probe.py` succeeds and the deployed path runs `--help` cleanly.
- A python3 parse of `~/.zcode/cli/config.json` finds the zcode.sh PreToolUse entry, and a parse of `~/.codex/hooks.json` finds the codex.sh PreToolUse group.
- The zcode.sh fixture probe fires exit 2 with a `{"decision": "block", ...}` envelope; the codex.sh fixture probe fires its deny envelope; both pass with no flag (exit 0, empty stdout).

**Ship when:**
- The user approves the Codex hook trust prompt at the next Codex session start (a `trusted_hash` entry for the new hooks.json entry appears under `[hooks.state]` in `~/.codex/config.toml`), and the backlog item's decision table runs to a conclusion via a fixture-flag drive in the trusted session: before the drive, confirm `budget-guard.fired` is absent (a stale marker with a matching epoch would suppress the block via the anti-thrash rule and fake an envelope rejection); because the registered hook command passes no arguments, the drive arms the fixture flag at the canonical `~/.ai-playbook/runtime/budget-guard.flag` path (the only path the hook reads; this Ship-when drive is the one sanctioned exception to Task 6's canonical-path fixture prohibition), observes whether the next tool call is denied, then immediately removes the canonical flag and `budget-guard.fired` marker; the three post-drive states are discriminated by the core's own fired marker (it is written whenever the core runs and emits a block, independent of Codex acceptance): a denial closes the question as envelope accepted; no denial with the marker present after the drive proves the hook ran and Codex did not honor the block, triggering the item's RED-first envelope fix; no denial with the marker still absent after the drive proves the hook never ran, which is a trust or registration gap, not an envelope defect.
- One real budget pause and scheduled resume completes end-to-end on at least one runtime (a live window boundary, not a fixture).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/quota_window_probe.py`
- `agents/skills/execute-plan/SKILL.md` (Budget gate block only)
- `agents/skills/plans/SKILL.md` (new Budget gate section and its cross-references)
- `agents/hooks/budget-guard/README.md` (Registration and Exit conventions sections only)
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` *(new)*

**Tests:**
- `scripts/test_quota_window_probe.py` *(edits)*

**Host wiring targets (not repo files, edited by Tasks 4-6 under exception receipts):**
- `~/.ai-playbook/scripts/quota_window_probe.py` (new symlink)
- `~/.zcode/cli/config.json` (PreToolUse entry)
- `~/.codex/hooks.json` (PreToolUse group)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Deploying `execute_plan_runtime.py`, `execute_plan_runtime_codex.py`, or `runtime_capabilities.py` to `~/.ai-playbook/scripts/`; reason: separate deployment residual, not required by the budget gate.
- Any change to pause thresholds or to the weekly secondary report-only rule; reason: working as designed by the guardrails plan.
- Changes to the ZCode or Codex CLI applications themselves; reason: this plan only configures and verifies against them.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1

# Task 1: suites and the live probe
python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py' || { echo "FAIL: probe suite"; exit 1; }
python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py' || { echo "FAIL: guard suite"; exit 1; }
python3 scripts/quota_window_probe.py --minutes-before 20 --max-percent 90 | grep -q '"status": "ok"' || { echo "FAIL: live probe not ok"; exit 1; }

# Task 1: exactly one endpoint literal in the module (the monitor endpoint)
test "$(grep -cF 'api.z.ai/api/monitor/usage/quota/limit' scripts/quota_window_probe.py)" -eq 1 || { echo "FAIL: endpoint literal count"; exit 1; }
rc=0; grep -F 'ZCODE_QUOTA_URL = "https://api.z.ai/api/quota/limit"' scripts/quota_window_probe.py || rc=$?
if [ "$rc" -eq 0 ]; then echo "FAIL: stale endpoint assignment"; exit 1; elif [ "$rc" -gt 1 ]; then echo "FAIL: stale-endpoint grep error rc=$rc"; exit 1; fi

# Task 2: execute-plan budget gate resolves the probe via three steps (one distinctive pin per resolution leg)
grep -qF 'BUDGET_PROBE' agents/skills/execute-plan/SKILL.md || { echo "FAIL: env override leg"; exit 1; }
grep -qF 'repo-local `scripts/quota_window_probe.py` when present' agents/skills/execute-plan/SKILL.md || { echo "FAIL: repo-local leg"; exit 1; }
grep -qF '$HOME/.ai-playbook/scripts/quota_window_probe.py' agents/skills/execute-plan/SKILL.md || { echo "FAIL: deployed leg"; exit 1; }
grep -qF 'unopenable probe script' agents/skills/execute-plan/SKILL.md || { echo "FAIL: fail-open note"; exit 1; }
grep -qF 'canonical home' agents/skills/execute-plan/SKILL.md || { echo "FAIL: mirror back-reference"; exit 1; }

# Task 3: plans-skill budget gate obligations (dedicated probes, one per obligation)
grep -qE '^## Budget gate \(plan-authoring pause and resume\)$' agents/skills/plans/SKILL.md || { echo "FAIL: plans gate section"; exit 1; }
grep -qF 'BUDGET_PROBE' agents/skills/plans/SKILL.md || { echo "FAIL: plans gate env leg"; exit 1; }
grep -qF 'repo-local `scripts/quota_window_probe.py` when present' agents/skills/plans/SKILL.md || { echo "FAIL: plans gate repo-local leg"; exit 1; }
grep -qF '$HOME/.ai-playbook/scripts/quota_window_probe.py' agents/skills/plans/SKILL.md || { echo "FAIL: plans gate deployed leg"; exit 1; }
grep -qF 'unopenable probe script' agents/skills/plans/SKILL.md || { echo "FAIL: plans gate fail-open rule"; exit 1; }
grep -qF 'budget_pause_minutes_before_reset' agents/skills/plans/SKILL.md || { echo "FAIL: minutes threshold key"; exit 1; }
grep -qF 'budget_pause_max_used_percent' agents/skills/plans/SKILL.md || { echo "FAIL: percent threshold key"; exit 1; }
grep -qF 'budget_probe_runtime' agents/skills/plans/SKILL.md || { echo "FAIL: runtime override key"; exit 1; }
grep -qF 'before launching each review-plan round' agents/skills/plans/SKILL.md || { echo "FAIL: review-round boundary"; exit 1; }
grep -qF 'before the final `done` handoff' agents/skills/plans/SKILL.md || { echo "FAIL: done-handoff boundary"; exit 1; }
grep -qF 'never mid-round' agents/skills/plans/SKILL.md || { echo "FAIL: mid-round prohibition"; exit 1; }
grep -qiF 'secondary' agents/skills/plans/SKILL.md || { echo "FAIL: weekly secondary rule"; exit 1; }
grep -qF 'write-flag ~/.ai-playbook/runtime/budget-guard.flag' agents/skills/plans/SKILL.md || { echo "FAIL: flag-arming argument"; exit 1; }
grep -qF '`budget_pause` record' agents/skills/plans/SKILL.md || { echo "FAIL: pause record sink"; exit 1; }
grep -qF 'reset time rounded up to the whole minute plus one' agents/skills/plans/SKILL.md || { echo "FAIL: resume timing"; exit 1; }
grep -qiF 'launchd' agents/skills/plans/SKILL.md || { echo "FAIL: launchd fallback"; exit 1; }
grep -qF 'stands down if the plan is archived' agents/skills/plans/SKILL.md || { echo "FAIL: stand-down rule"; exit 1; }
grep -qF 'never edits the plan' agents/skills/plans/SKILL.md || { echo "FAIL: digest-unchanged line"; exit 1; }
grep -qF 'canonical home' agents/skills/plans/SKILL.md || { echo "FAIL: protocol canonical home"; exit 1; }
grep -qF 'mirrors the execute-plan Budget gate protocol' agents/skills/plans/SKILL.md || { echo "FAIL: integration-points mirror"; exit 1; }

# Task 6: envelope question recorded, provisional README note gone
test -f docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md || { echo "FAIL: envelope backlog item"; exit 1; }
rc=0; grep -qiF 'Codex (provisional)' agents/hooks/budget-guard/README.md || rc=$?
if [ "$rc" -eq 0 ]; then echo "FAIL: provisional codex note still present"; exit 1; elif [ "$rc" -gt 1 ]; then echo "FAIL: provisional-note grep error rc=$rc"; exit 1; fi

# Tasks 4-6: host wiring (run on the host that owns the runtime dirs)
test -L "$HOME/.ai-playbook/scripts/quota_window_probe.py" || { echo "FAIL: probe symlink"; exit 1; }
python3 "$HOME/.ai-playbook/scripts/quota_window_probe.py" --help >/dev/null 2>&1 || { echo "FAIL: deployed probe runs"; exit 1; }
python3 - <<'PYEOF' || { echo "FAIL: zcode hook entry"; exit 1; }
import json, pathlib, os, sys
cfg = json.loads(pathlib.Path("~/.zcode/cli/config.json").expanduser().read_text())
hooks = cfg["hooks"]["events"]["PreToolUse"]
found = any(
    h.get("command", "").endswith("agents/hooks/budget-guard/zcode.sh")
    for group in hooks for h in group.get("hooks", [])
)
sys.exit(0 if found else 1)
PYEOF
python3 - <<'PYEOF' || { echo "FAIL: codex hook entry"; exit 1; }
import json, pathlib, sys
data = json.loads(pathlib.Path("~/.codex/hooks.json").expanduser().read_text())
groups = data["hooks"]["PreToolUse"]
found = any(
    h.get("command", "").endswith("agents/hooks/budget-guard/codex.sh")
    for group in groups for h in group.get("hooks", [])
)
sys.exit(0 if found else 1)
PYEOF
```

Note on the stale-endpoint sweep: the forbidden-match grep pins the full legacy assignment string so the test fixture URL (`api/quota/limit-test`, different file) cannot trip it; only an exact legacy `ZCODE_QUOTA_URL` assignment fails the gate. Live-probe and host-wiring checks are environment-dependent by nature; run them on the host that owns `~/.zcode`, `~/.codex`, and `~/.ai-playbook`.

### Task 1: Point the ZCode probe at the monitor endpoint

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [x] `QuotaWindowProbeTest#test_zcode_default_url_targets_monitor_endpoint`; given the module constant `ZCODE_QUOTA_URL`, expects the exact string `https://api.z.ai/api/monitor/usage/quota/limit`
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'`; the new URL pin fails against the legacy constant while all pre-existing tests stay green
- [x] `QuotaWindowProbeTest#test_parse_zcode_live_payload_with_extra_fields`; given the captured live response body (`data.limits` listing the `TIME_LIMIT` entry first with `percentage` 2 and `nextResetTime` 1791551411983, then the `TOKENS_LIMIT` entry with `percentage` 62 and `nextResetTime` 1789315099416, plus the `unit`/`number`/`usage`/`usageDetails`/`level` extras), expects `parse_zcode_limits` to return exactly two limits identified by kind, never by list position: `primary` used_percent 62.0 with reset epoch 1789315099, and `secondary` used_percent 2.0 with reset epoch 1791551411; run as characterization (expect GREEN before the URL change: the parser already tolerates the shape and the entry order, and it must stay green after)
- [x] Run → expect GREEN: the characterization test alone passes against today's module
- [x] Change the `ZCODE_QUOTA_URL` constant in `scripts/quota_window_probe.py` to the monitor endpoint; no other endpoint literal may be introduced
- [x] Run → expect GREEN: the full `test_quota_window_probe.py` suite (all pre-existing tests plus both new tests)
- [x] Live verification: `python3 scripts/quota_window_probe.py --minutes-before 20 --max-percent 90` prints a JSON report with `"status": "ok"` and non-empty `limits`; if it prints `status: unknown`, stop and investigate before continuing (the endpoint verified live on 2026-09-13)
- [x] Commit: `fix: point zcode quota probe at the live monitor endpoint`

### Task 2: Budget-gate probe resolution fallback in execute-plan

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Apply the plans-class skill-gate marker (see `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE) immediately before the edit
- [x] In the Budget gate section, replace the bare `python3 scripts/quota_window_probe.py ...` invocation with three-step resolution mirroring Step 0.5: `BUDGET_PROBE` env override first; then the repo-local `scripts/quota_window_probe.py` when present; then the deployed `$HOME/.ai-playbook/scripts/quota_window_probe.py`
- [x] Add the fail-open sentence: a missing or unopenable probe script is treated as `status: unknown`, noted in `manifest.md`, and the flow continues; it must never block the run
- [x] Add the mirror back-reference to the same section: the plans skill mirrors this protocol at plan-authoring boundaries (see the plans skill Budget gate section), which makes this section the canonical home of the shared pause protocol
- [x] Leave the pause-protocol steps, the exit-code rule, and the weekly secondary report-only rule byte-unchanged
- [x] Commit: `docs: resolve budget-gate probe via repo-local and deployed fallbacks`

### Task 3: Add the budget gate to the plans skill

Files:
- `agents/skills/plans/SKILL.md`

- [x] Apply the plans-class skill-gate marker immediately before the edit
- [x] Add `## Budget gate (plan-authoring pause and resume)` as its own H2 section immediately before `## Plan Quality Gate` (an H3 would nest under the preceding `## Validation Commands (authoring rules)` section), resolving `budget_pause_minutes_before_reset` (default 20), `budget_pause_max_used_percent` (default 90), and `budget_probe_runtime` (default auto) from the opening TOML block of `.ai-playbook/facts.md`, restating the same three-step probe resolution prescribed in Task 2 (the `BUDGET_PROBE` env override, then the repo-local `scripts/quota_window_probe.py` when present, then the deployed `$HOME/.ai-playbook/scripts/quota_window_probe.py`) and the same fail-open rule (a missing or unopenable probe script is treated as `status: unknown`, noted, and the flow continues) so the section stays self-contained outside the skills repo
- [x] State the two boundaries: the orchestrator runs the probe before launching each review-plan round in the Plan Quality Gate loop, and before the final `done` handoff; never mid-round
- [x] State the probe invocation: `python3 <resolved-probe> --minutes-before <N> --max-percent <P> [--runtime <id>] --plan <plan-slug> --write-flag ~/.ai-playbook/runtime/budget-guard.flag`, so `write_flag_if_paused` arms the guard flag on a pause decision and the registered backstop hook has something to enforce (the weekly `secondary` binding still writes no flag and schedules nothing)
- [x] State the pause protocol: finish the current boundary only; keep the guard flag armed (when the binding window is the weekly `secondary`, write no flag, schedule nothing, and report for user decision); append a `budget_pause` record (runtime, reset epoch and ISO time, thresholds used, next step that would have run) to `{tmp_dir}/plan-requirements-<slug>.md`; schedule the resume automation at the reset time rounded up to the whole minute plus one, with a self-contained prompt that re-enters the plans review loop on the plan path, verifies the latest review sidecar digest still matches the plan bytes (a budget pause never edits the plan, so no re-certification is needed), clears `~/.ai-playbook/runtime/budget-guard.flag` and `budget-guard.fired` before relaunching, and stands down if the plan is archived or completed or a peer session resumed the work; fall back to a launchd one-shot when automations are unavailable; if neither capability exists, end report-only naming the exact resume command and time
- [x] State the canonical home: this section mirrors the execute-plan Budget gate section, which is the canonical home of the shared pause protocol (thresholds, weekly secondary rule, resume timing, flag and fired-marker clearing, fallbacks); on conflict that section wins, and the deltas owned here are the two authoring boundaries and the `budget_pause` record sink
- [x] State that the runtime budget-guard backstop hook (`agents/hooks/budget-guard/`) enforces the pause at the tool-call level once registered, so a mid-round quota exhaustion cannot silently burn the window
- [x] Add the mirror pointer in the plans skill's Integration Points: the `With execute-plan` subsection gains a line stating that the plans skill's Budget gate mirrors the execute-plan Budget gate protocol (the canonical home) at plan-authoring boundaries
- [x] Every obligation added above is independently grep-verifiable: the Validation Commands block carries one dedicated probe per obligation listed in the bullets of this task (section heading, three threshold keys, the three resolution legs, the fail-open rule, both boundaries, the mid-round prohibition, the weekly secondary rule, the flag-arming argument, the record sink, the resume timing, the launchd fallback, the stand-down rule, the digest-unchanged line, the canonical-home line, and the Integration Points mirror line)
- [x] Commit: `feat: add plan-authoring budget gate to plans skill`

### Task 4: Deploy the probe as a runtime symlink

Files (host wiring, outside the repository; see exception receipt):
- `~/.ai-playbook/scripts/quota_window_probe.py` *(new symlink)*

Exception receipt (applies to the host-wiring checklist items in this task): exception confirmed by user: the user asked for a fix plan covering the offered items, including deploying the probe into `~/.ai-playbook/scripts/` (authoring session, 2026-09-13); item: create the deployed probe symlink; target/environment: `~/.ai-playbook/scripts/` on this host; confirmation time/session: 2026-09-13 plans authoring session; why executable now: the runtime scripts directory exists on this host, is user-writable, and the symlink target verifies with `test -L` and a `--help` run in this session; completion evidence: `test -L ~/.ai-playbook/scripts/quota_window_probe.py` succeeds and `python3 ~/.ai-playbook/scripts/quota_window_probe.py --help` exits 0.

- [x] Create the symlink: `ln -s "<skills-repo-root>/scripts/quota_window_probe.py" "$HOME/.ai-playbook/scripts/quota_window_probe.py"` with `<skills-repo-root>` resolved at run time
- [x] Verify the symlink resolves and the deployed copy runs: `test -L` plus a `--help` invocation exits 0
- [x] Commit: none (host-only task; no repository delta)

### Task 5: Register the ZCode backstop hook

Files (host wiring; see exception receipt):
- `~/.zcode/cli/config.json`

Exception receipt (applies to the host-wiring checklist items in this task): exception confirmed by user: the user asked for a fix plan covering the offered items, including registering the budget-guard hook in both runtime configs (authoring session, 2026-09-13); item: append the zcode.sh PreToolUse entry; target/environment: `~/.zcode/cli/config.json` on this host; confirmation time/session: 2026-09-13 plans authoring session; why executable now: the config file exists on this host, is user-writable, a pre-edit backup is taken, and the registration verifies by JSON parse plus a fixture block probe in this session; completion evidence: the JSON parse finds the entry and the fixture probe fires exit 2 with a block envelope.

- [x] Back up the config: `cp ~/.zcode/cli/config.json ~/.zcode/cli/config.json.bak-$(date +%Y%m%d-%H%M%S)-budget-guard`
- [x] Append to `hooks.events.PreToolUse` the group `{"hooks": [{"type": "command", "command": "<skills-repo-root>/agents/hooks/budget-guard/zcode.sh", "timeout": 10}]}` (a group object with a `hooks` array, no matcher key, per the budget-guard README), with `<skills-repo-root>` resolved at run time into the stored command string
- [x] Verify by parse: a python3 read of the config finds the entry whose command ends with `agents/hooks/budget-guard/zcode.sh`
- [x] Fixture block probe: create a synthetic future-dated flag (`runtime=zcode`, `reset_at_epoch` one hour ahead, `reset_at_iso` matching) in a temp directory, run `zcode.sh --flag-path <tmp>/budget-guard.flag --fired-path <tmp>/budget-guard.fired`, and expect exit 2 with stdout `{"decision": "block", ...}` whose reason embeds the reset ISO time; then delete the temp flag and fired marker
- [x] Fixture pass probe: rerun with no flag present and expect exit 0 with empty stdout (fail-open)
- [x] Note in the task log that registration takes effect for sessions started after the config change (restart semantics for live sessions are unverified)
- [x] Commit: none (host-only task; no repository delta)

### Task 6: Register the Codex backstop hook and verify the deny envelope

Files:
- `~/.codex/hooks.json` (host wiring; see exception receipt)
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` *(new)*
- `agents/hooks/budget-guard/README.md`

Exception receipt (applies to the host-wiring checklist items in this task): exception confirmed by user: the user asked for a fix plan covering the offered items, including registering the budget-guard hook in both runtime configs (authoring session, 2026-09-13); item: append the codex.sh PreToolUse group; target/environment: `~/.codex/hooks.json` on this host; confirmation time/session: 2026-09-13 plans authoring session; why executable now: the hooks file exists on this host, is user-writable, a pre-edit backup is taken, and the codex binary (2026-09-13 install) parses the same PreToolUse schema already used by a registered hook in that file; completion evidence: the JSON parse finds the group and the fixture probes demonstrate the deny and pass envelopes.

- [x] Back up the hooks file: `cp ~/.codex/hooks.json ~/.codex/hooks.json.bak-$(date +%Y%m%d-%H%M%S)-budget-guard`
- [x] Append to `hooks.PreToolUse` the group `{"matcher": ".*", "hooks": [{"type": "command", "command": "<skills-repo-root>/agents/hooks/budget-guard/codex.sh"}]}` (schema mirrors the existing registered PreToolUse group in the same file), with `<skills-repo-root>` resolved at run time into the stored command string
- [x] Verify by parse: a python3 read of the file finds the group whose hook command ends with `agents/hooks/budget-guard/codex.sh`
- [x] Adapter deny fixture probe: with a future-dated fixture flag (`runtime=codex`, `reset_at_epoch` one hour ahead, `reset_at_iso` the matching local ISO time; all three keys are required because `parse_flag` returns an empty mapping without `reset_at_iso` and the hook fails open) in a temp directory, run `codex.sh --flag-path <tmp>/budget-guard.flag --fired-path <tmp>/budget-guard.fired` and record the exact stdout envelope and exit code (expected: exit 0 with the flat `{"permissionDecision": "deny", "reason": ...}` envelope whose reason embeds the reset ISO time); this verifies the adapter's emission only, not Codex's acceptance of the envelope
- [x] Adapter pass fixture probe: rerun `codex.sh` with no flag present and expect exit 0 with empty stdout (fail-open); delete all temp fixture files and never write a fixture flag to the canonical `~/.ai-playbook/runtime/budget-guard.flag` path
- [x] Create the follow-up backlog item `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` (shape follows the existing items in that directory) recording: the open question (the codex binary's own error strings name `permissionDecisionReason` for deny decisions, while the adapter emits the flat `{"permissionDecision": "deny", "reason": ...}` envelope; acceptance by the live codex binary is unverified because the registered hook does not run until the user approves the first-start trust prompt); the decision table for the Ship-when live check, including flag placement at the canonical path, a pre-drive check that `budget-guard.fired` is absent (a stale matching-epoch marker would suppress the block and fake a rejection), and post-drive cleanup of the flag and fired marker; the three post-drive states are discriminated by the core's own fired marker (the core writes it whenever it runs and emits a block, independent of whether Codex honors the envelope): a denial observed closes the question as accepted; no denial with the fired marker PRESENT after the drive proves the hook ran and emitted a block Codex did not honor, which means the envelope was rejected and the fix writes the RED pin of the probed-accepted shape against the pre-fix core first, then adapts `codex.sh`/`budget_guard_core.py`, then flips GREEN and re-verifies live; no denial with the fired marker still ABSENT after the drive proves the hook never ran, which means a trust or registration gap, not an envelope defect; plus a pointer to the README section below
- [x] Update `agents/hooks/budget-guard/README.md`: replace the provisional Codex registration paragraph with the verified schema actually registered (matcher `.*` group shape as observed in the live hooks.json), document the first-start hook trust prompt and its Ship-when follow-through, and record the open envelope question with the same decision table as the backlog item
- [x] Commit: `docs: register codex budget-guard path and record envelope verification`
