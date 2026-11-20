# Plan: Claude Code runtime overlay for the maintenance loop

Backlog origins (scope of record):
- docs/history/backlog/2026-11-20-maintenance-claude-code-runtime-overlay.md
- docs/history/backlog/2026-11-20-authoring-session-ends-certified-plan-unlanded.md
- docs/history/backlog/2026-11-20-direct-maintenance-invocation-asks-instead-of-deciding.md
- docs/history/backlog/2026-11-20-claude-runtime-worktree-authoring-friction.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-20-plan-review-claude-maintenance-indefinite-loop-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically).
Execution budget: 3h total, largest task 1h
Executed: yes (1219c75a96d31cef212385b7d235c9d3ef00bf12)
Authoring claim: 2026-11-20-maintenance-claude-code-runtime-overlay.md (session 883322f3-c823-4664-87ca-27d5422722a3)

## Terms

- overlay: a runtime-specific module beside `agents/skills/maintenance/SKILL.md` that the loop's Step 0 loads by runtime id; today `codex.md` and the `zcode` set exist.
- quota probe and governor: `scripts/quota_window_probe.py` reads one runtime's usage windows into a report, and `scripts/quota_governor.py` turns reports into dispatch verdicts; both take `--runtime` and today accept only `codex` and `zcode`.
- usage file: a JSON file holding one `get_usage` result, written by the model because `get_usage` is a tool call that scripts cannot make; scripts read its path from a `--usage-file` flag, falling back to the `CLAUDE_USAGE_JSON` environment variable.
- pause decision: the probe's `pause_decision` field; `pause` with a primary binding is the quota wall.
- quota wall: the point where the 5-hour usage window is full enough that the probe says pause, so no further work starts until it resets.
- reset epoch: the window's reset time as Unix seconds, the form the probe and governor use.
- standing margin: the 10-minute delay added to the reset epoch before arming a successor.
- successor: the one scheduled run that restarts the loop after a quota wall, armed for the reset epoch plus the standing margin.
- carrier: the scheduled mechanism that restarts the loop; for Claude Code it is a scheduled task.
- scheduled task: a task stored on disk by the scheduled-tasks connector (`create_scheduled_task`) that runs once at a given time while the Claude app is open, or at the next launch.
- recognition rule: the existing rule that finds a loop carrier by its title, its prompt's opening line, and the repository root in its prompt, so only one successor exists per repository.
- D-17 and D-18: operator directives in `docs/maintenance/operator-directives.md`; D-17 keeps the loop continuing after each task, and D-18 requires every exit to arm a carrier or record an exemption.
- loop exit token, loop-liveness line, and `operator-park`: the `loop-exit:<class>` record every exit carries, the closing-report line naming the armed carrier and its fire time, and the terminal exit that parks the loop for the operator after a failed arm.
- dark, blocked-retry, and repair successor: D-18 words; a scheduler parent that is absent or missed its fire is classed dark, a queue-empty exit then becomes blocked-retry, and the repair successor is the one carrier armed in its place.
- arm-failure ladder: the existing rule to try the arm once, then park, ending in `operator-park`.
- pilot target and byte cap: the advisory size target in `scripts/skill_text_budget.py` and the enforced per-file cap in `scripts/skill_text_budget_caps.json`.
- coverage window and pending-dispatch record: existing maintenance names; the window of fire times the occupied-lane chaining duty counts as already covering a successor, and the scheduler state field that keeps the selected pick across a pause.
- harness-detection skip arm: the existing rule that records `skipped-unsupported-harness` and skips the probe when the harness helper reports none.
- inventory deferral and execute-plan runtime eligibility: the `[deferrals.claude]` row in `projects/.ai-playbook/execute-plan-runtime-inventory.toml`, which says whether execute-plan may use a runtime's own adapter; it does not gate maintenance overlays.
- queue-empty and Final Step: the exit taken when no task remains, with its preconditions in the authoring FINAL STEP, and the plans skill's last step that lands a certified plan.
- fail-open: when an input is unknown the existing default behavior continues and nothing is armed.
- claim: the authoring claim file that marks a backlog item as being authored by one session.
- self-heal consult: one invocation of the `self-heal` skill before a stop is judged unrecoverable.
- guards: the ordered gates of the scheduler turn, including the project-class guard that holds company-class and undeclared projects to survey-only.
- manual invocation: a person typing `/maintenance <mode>` in a live session, as opposed to a carrier firing on a schedule.
- skill-gate marker: the short-lived file that proves the plans skill was invoked before a plan file is written; the gate checks it for the directory the hook payload reports.
- worktree: a separate checkout, here the ad-hoc one an authoring or execution run works in.

## Why

The maintenance loop is meant to run until no task remains or the 5-hour limit is reached, and then restart right after the reset. Its quota scripts and overlays know only two other runtimes, so a Claude Code turn cannot read quota, cannot arm a successor, ended after one authored plan with the plan unlanded, and asked its operator questions the loop is meant to decide itself.

## Gist & Examples

TLDR: let the quota scripts accept a `claude` source fed by a `get_usage` file and add a `claude.md` overlay that binds the loop's exit, authorization, successor, and worktree rules to Claude Code, so the loop can run unattended there (automation).

Before: a manual `/maintenance author` run in Claude Code certifies a plan, lists what is "not done", and stops; quota is "unknown" and nothing is armed for after the 5-hour reset.
After: the same run writes the `get_usage` result to a usage file, runs the probe with `--runtime claude`, continues to the next task, and when the probe says pause arms one scheduled task for the reset epoch plus the standing margin, then exits with a loop exit token and a loop-liveness line naming that task and noting it needs the app open.

## Outcome

Aim: a Claude Code maintenance run keeps going until the queue is empty or the 5-hour limit, and restarts itself right after the reset.

- The quota probe and governor read Claude Code usage, and report quota unknown when the usage file is absent, stale, or unusable.
- When the probe says pause the run arms exactly one durable successor at the reset epoch plus the standing margin.
- A run exits only by the existing D-18 exit classes, and a certified authoring plan goes through the Final Step first. A queue-empty exit on Claude is reached only while a recorded carrier exists (an enabled matching scheduled task whose fire time is still in the future); without one it takes the D-18 repair path.
- A manual invocation with a mode word decides within the guards instead of asking the operator.
- A Claude worktree authoring run writes its first plan file without a refused write.

Gate delta: no refusal, gate, fence, schema field, or pause condition is added. Four counted changes: the overlay's runtime id supersedes the unsupported-harness skip arm at its two sites (the quota-policy skip and the survey quota snapshot), which loosens an existing skip; one accepted runtime id (`claude`) is added to the allowed-runtime tuples of two scripts and one source table, which loosens an existing refusal; one new fail-open freshness bound (a usage file older than 15 minutes reads as unknown, local to the Claude reader, never a refusal because unknown continues the loop) is added; one environment name (`CLAUDE_CODE_SESSION_ID`) is added to the governor's updated-by list. Apart from that supersession, the overlay takes every existing quota-policy and D-18 arm unchanged and adds no exit class or exemption; it supplies only the Claude carrier. The plans skill's separate budget-gate harness skip is deliberately untouched: a Claude execution child keeps its own override route and its skip stands. An overlay section it does not carry (peak-pricing deferral, recurring-parent re-arm) means that behavior is absent on Claude, as with the Codex overlay.

Follow-up disposition, origin by origin: (1) the overlay row is closed by Tasks 1 to 3; its request to replace the inventory deferral stays unchanged because `[deferrals.claude]` governs execute-plan runtime eligibility, as the Codex deferral does beside its own overlay (`projects/.ai-playbook/execute-plan-runtime-inventory.toml`). (2) The unlanded-authoring row is closed for the Claude runtime by the overlay's exit rule. (3) The manual-invocation row is closed for the Claude runtime by the overlay's authorization rule. (4) The worktree row is closed by the overlay's worktree note (marker route, sandbox allowlist, re-issue of a hook-rewritten call) and Task 4's README sentence. Rejected disposition: the origin rows asked for `SKILL.md` and `template-authoring.md` edits that would cover every runtime; that is rejected because the failures were witnessed only on Claude and the modules are at their size limits (`SKILL.md` is 41056 bytes, over its advisory pilot target of 40960 in `scripts/skill_text_budget.py` with a cap of 44233; `template-authoring.md` is 56588 bytes, over its enforced cap of 42066; caps in `scripts/skill_text_budget_caps.json`); a non-Claude witness reopens the question.

## Assumptions

- The loop's Step 0 loads `agents/skills/maintenance/<runtime-id>.md` and `codex.md` is the single-file overlay shape to follow (basis: `agents/skills/maintenance/SKILL.md` Step 0 and `codex.md`, read 2026-11-20).
- The runtime id `claude` is the canonical inventory id and is established by the runtime-provided session identity (`CLAUDE_CODE_SESSION_ID`, resolved by `scripts/session_channel.py`), not inferred from the host (basis: a live run of the helper on 2026-11-20 and the inventory's `canonical_ids`).
- The probe and governor accept only `codex` and `zcode` (literal tuples in `quota_window_probe.py`, `quota_governor.py`, and the `RUNTIME_SOURCES` table), harness detection does not detect Claude so the runtime is passed with `--runtime claude`, and the governor calls the probe in-process so one reader serves both (basis: reading and live `--runtime claude` and `--runtime cursor` runs on 2026-11-20, both reporting unsupported).
- The `get_usage` tool returns `plan.windows` with a `5-hour limit` window carrying `percentUsed` and an ISO `resetsAt`, a weekly window, and a `plan.status` of `ok`, `unavailable`, or `not_applicable` (basis: a live call on 2026-11-20 returned 31 percent used and a reset time).
- Existing quota policy is fail-open: an unknown quota keeps the default behavior and arms nothing (basis: `agents/skills/maintenance/quota-policy.md` Step 4 and the governor's `unknown` class).
- The wall trigger is the probe's pause decision with a primary binding, which is what D-18 ties `quota-wall` to; a governor `exhausted` class with `continue` does not arm (basis: probe thresholds and `EXHAUSTED_PERCENT` read 2026-11-20).
- The governor's shared state file is one per host and a refresh replaces the stored pressure, so the overlay passes a Claude-specific `--state-path` (basis: `DEFAULT_STATE_PATH` and `refresh` read 2026-11-20).
- `CronCreate` jobs are session-only and expire after 7 days, so they cannot carry a successor past the session; the scheduled-tasks connector stores a task on disk with a one-shot `fireAt` (basis: the tool descriptions and empty `CronList` and `list_scheduled_tasks` results on 2026-11-20); creating, listing, and deleting one task for real is Task 3's probe.
- The standing margin, the one-successor rule, the recognition rule, and the arm-failure ladder ending in `operator-park` come from `zcode-scheduling-primitives.md`, `template-authoring.md`, and D-18 (basis: read 2026-11-20).
- In Claude Code the skill-gate consult keys from the hook payload's cwd, so a worktree session's first plan write is refused until a marker is keyed to the session cwd (basis: the refused write on 2026-11-20 and the skill-gate README Marker WRITE RECIPE item 4).
- The two tests `test_zcode_transport_never_follows_redirects` and `test_version_skew_fails_closed` fail on today's tree in the review sandbox; their cause is undiagnosed (basis: a read-only run on 2026-11-20 with the `ai-playbook-test` venv, 185 passed and 2 failed).
- No pins are added for the overlay: a pin is machinery and no incident of overlay drift is witnessed; the executor records the grep needles it used in its task report instead.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Verifiability: every primitive the overlay names was called once for real before the overlay names it.
- Safety: an unknown or stale quota never arms anything and never stops the loop, and a pause decision arms at most one successor per repository.
- Contract fit: the overlay changes no D-17 or D-18 exit class, token, or arm; it only binds the Claude carrier.

**Done when:**
- The probe and governor accept `claude`, every Task 1 and Task 2 witness passes, and the failure set of the two test files equals the pre-change baseline.
- `agents/skills/maintenance/claude.md` exists and every Task 3 witness holds.
- The skill-gate README carries the Claude marker sentence and every Task 4 witness holds.

**Ship when:**
- A Claude Code maintenance run on this repository continues past one task, shown by its closing report listing two or more landed tasks [class: OPERATIONS_FOLLOW_UP]; evidence owner: the operator; closed when that report exists.
- A Claude Code maintenance run reaches a probe pause decision and arms a successor, shown by its closing report's loop-liveness line and a matching entry in the scheduled-tasks list [class: OPERATIONS_FOLLOW_UP]; evidence owner: the operator; closed when both are observed.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/quota_window_probe.py` (Task 1)
- `scripts/quota_sources.py` (Task 1)
- `scripts/quota_governor.py` (Task 2)
- `agents/skills/maintenance/claude.md` (Task 3) *(new)*
- `agents/hooks/skill-gate/README.md` (Task 4)

**Tests:**
- `scripts/test_quota_window_probe.py` (Task 1)
- `scripts/test_quota_governor.py` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/template-authoring.md`, and `scripts/check_maintenance_pins.sh`; the overlay carries the rules, and these modules are at their size limits.
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`; its Claude deferral governs execute-plan eligibility.
- The codex and zcode readers and the budget guard's `--write-flag` runtime choices; behavior unchanged, and the overlay never passes `--write-flag`.

## Validation Commands

```bash
~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_quota_window_probe.py scripts/test_quota_governor.py -q -p no:cacheprovider
python3 scripts/skill_text_budget.py --check
bash ~/.ai-playbook/scripts/check-no-em-dash.sh file agents/skills/maintenance/claude.md agents/hooks/skill-gate/README.md
bash scripts/scan-public-hygiene.sh
```

### Task 1: Claude usage source in the quota probe

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/quota_sources.py`
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

Primary class anchors:
- `detect_runtime` in `scripts/quota_window_probe.py`
- `RUNTIME_SOURCES` in `scripts/quota_sources.py`

- [x] Baseline: before editing, record the failure set of the two test files; preservation means the failure set stays identical [class: REPOSITORY_TEST]
- [x] Probe delivers the claude source: given `--runtime claude` and a fresh usage file with status `ok` and a `5-hour limit` window at 95 percent resetting in the future, expects a report for runtime `claude` with a primary window at 95 percent and the reset epoch equal to `resetsAt` [class: IMPLEMENTATION_REQUIRED]
- [x] Channel witness: given the path passed with `--usage-file`, expects a report; given only `CLAUDE_USAGE_JSON`, expects the same; given neither, expects status unknown [class: REPOSITORY_TEST]
- [x] Weekly witness: given a weekly window in the file, expects it mapped as the secondary window and report-only [class: REPOSITORY_TEST]
- [x] Safety witness: given a missing, malformed, or expired-reset file, a status other than `ok`, or no `5-hour limit` window, expects status unknown, no pause decision, and no invented window [class: REPOSITORY_TEST]
- [x] Freshness witness: given a file with a future reset and an mtime 14 minutes old, expects a report; given an mtime 16 minutes old, expects status unknown; the observed-at time comes from the file mtime [class: REPOSITORY_TEST]
- [x] Run → expect RED (claude reported unsupported), write the reader, the accepted id, and the `--runtime` help text, run → expect GREEN [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `quota: read Claude Code usage in the quota probe` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Claude runtime in the quota governor

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/quota_governor.py`
- `scripts/test_quota_governor.py`

Primary class anchors:
- `_expected_runtime` in `scripts/quota_governor.py`

- [x] Governor witness: given `--runtime claude` with `CLAUDE_USAGE_JSON` naming a usage file as in Task 1, expects the same class policy as codex for the same percent and reset; given the variable unset, expects unknown; given an unsupported id such as `cursor`, expects the existing refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Plumbing witness: given a claude refresh, expects both runtime tuples and the `--runtime` help texts of the probe and governor to accept `claude`, the in-process probe call to reach the claude reader through the environment variable, and the codex and zcode calls to stay unchanged [class: REPOSITORY_TEST]
- [x] Unknown witness: given a claude report with status unknown or only a weekly window, expects class unknown, both lanes allow, and no reset epoch [class: REPOSITORY_TEST]
- [x] State witness: given the other session-id variables cleared (the Claude variable is read last), a claude refresh with its own `--state-path` and `CLAUDE_CODE_SESSION_ID` set, expects the stored updated-by to carry that id and a codex state file untouched [class: REPOSITORY_TEST]
- [x] Preservation witness: given the codex and zcode cases, expects the failure set of the two test files identical to the Task 1 baseline [class: REPOSITORY_TEST]
- [x] Run → expect RED (claude refused), write the accepted id and the updated-by env entry, run → expect GREEN [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `quota: accept the Claude runtime in the governor` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Claude Code overlay module

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/maintenance/claude.md` *(new)*

Primary class anchors:
- `claude-runtime-overlay` in `agents/skills/maintenance/claude.md`

- [x] Primitive probe: given a one-shot scheduled task with a unique probe name prefix and a no-op prompt due next year, expects it listed, then gone after deletion, then an empty list for that prefix; any leftover id is recorded in the task report [class: REPOSITORY_TEST]
- [x] Identity witness: given the runtime-provided session identity, expects runtime id `claude` to supersede the harness-detection skip arm at both sites (the quota-policy skip and the survey quota snapshot with its governor refresh condition); given the id absent, expects the skip arm to stand [class: IMPLEMENTATION_REQUIRED]
- [x] Quota witness: given runtime id `claude`, expects the model to write `get_usage` to a per-session usage file, and the probe and governor to run with `--runtime claude`, `CLAUDE_USAGE_JSON` set inline on each call, and a Claude state path [class: IMPLEMENTATION_REQUIRED]
- [x] Fail-open witness: given the `get_usage` tool absent or failing, expects quota unknown, nothing armed, and the loop to continue per default [class: IMPLEMENTATION_REQUIRED]
- [x] Arm binding: given any quota-policy arm (pause, stop-before-exhaustion, wait-for-reset, mid-run) or D-18 exit arm, expects it taken unchanged, with the overlay supplying only the carrier: where an arm arms a resume or successor, a scheduled task at that time, and the parked pick recorded in the existing pending-dispatch record [class: IMPLEMENTATION_REQUIRED]
- [x] Carrier witness: given an armed task, expects a fixed title and prompt-opening literal, the repository root in the prompt, a self-contained payload that names the mode and re-derives state from disk, the task id recorded through the existing carrier fields, and the loop-liveness line noting the app must be open [class: IMPLEMENTATION_REQUIRED]
- [x] One-successor witness: given a matching enabled task whose fire time lies inside the existing coverage window, expects no second task; given the create refused or failing, expects the arm-failure ladder to `operator-park`; given a fired successor, expects it to re-probe first and re-arm at the new reset if the decision is still pause or wait-for-reset [class: IMPLEMENTATION_REQUIRED]
- [x] Residual witness: given a usage-limit refusal that ends the turn, expects the overlay to record that it cannot self-arm and that the next run re-derives from disk; given no recorded carrier, expects the sequence blocked-retry, blocked-retry, operator-park [class: IMPLEMENTATION_REQUIRED]
- [x] Queue-empty witness: given an empty queue and an enabled matching scheduled task still in the future, expects loop-exit queue-empty; given an empty queue and no such task, including a fired successor whose own task is consumed, expects blocked-retry with one repair successor, never a queue-empty token [class: IMPLEMENTATION_REQUIRED]
- [x] Exit witness: given a certified authoring plan not yet landed, expects the overlay to run the Final Step before any loop exit token [class: IMPLEMENTATION_REQUIRED]
- [x] Authorization witness: given a manual invocation with a mode word on a pet project whose guards pass, expects no operator question; given a guard refusal or a company-class or undeclared project, expects the existing stop, token, and confirmation unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Worktree witness: given a Claude worktree authoring session, expects the overlay to name the marker route linked to the README sentence, the sandbox allowlist for the worktrees root, and re-issue of a hook-rewritten call [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: add the Claude Code runtime overlay` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Marker sentence and repository checks

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/hooks/skill-gate/README.md`

Primary class anchors:
- `Marker WRITE RECIPE` in `agents/hooks/skill-gate/README.md`

- [x] Add one sentence to the recipe's project-key item that scopes its worktree MUST as an explicit exception: in Claude Code the consult keys from the session cwd, so a worktree authoring session writes its own marker keyed to the session cwd with `--cwd`, the one sanctioned case of a marker keyed away from the write target [class: IMPLEMENTATION_REQUIRED]
- [x] Gated-write witness: given a marker written by that route in a temporary runtime directory, expects the skill-gate consult CLI with the session cwd, the same session id, and `--target <plan path in the worktree>` to allow the write, and given no marker to refuse, the two runs differing only by the marker [class: REPOSITORY_TEST]
- [x] Preservation witness: given the added sentence, expects a grep needle for the exception wording to match and the recipe's fail-loud rule and every other runtime's rule to read unchanged [class: REPOSITORY_TEST]
- [x] Run the Validation Commands, expect no new failure, no ceiling breach, and no growth in the over-budget maintenance modules [class: REPOSITORY_TEST]
- [x] Commit: `docs: key the skill-gate marker to the Claude session cwd` [class: IMPLEMENTATION_REQUIRED]

## Origin dispositions

- `2026-11-20-maintenance-claude-code-runtime-overlay`: closed by Tasks 1 to 3 (quota probe and governor accept the `claude` runtime; `agents/skills/maintenance/claude.md` overlay).
- `2026-11-20-authoring-session-ends-certified-plan-unlanded`: closed by Task 3 (overlay exit rule runs the plans Final Step before any loop exit token).
- `2026-11-20-direct-maintenance-invocation-asks-instead-of-deciding`: closed by Task 3 (standing authorization section).
- `2026-11-20-claude-runtime-worktree-authoring-friction`: closed by Tasks 3 and 4 (overlay worktree notes; skill-gate README exception sentence).
- Residuals filed, not fixed here: `docs/history/backlog/2026-11-20-claude-usage-reader-residual-hardening.md` (three Low reader gaps from the Phase 3 review).
