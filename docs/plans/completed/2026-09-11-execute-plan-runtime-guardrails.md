# Plan: execute-plan runtime guardrails: quota pause/resume, budget-guard hooks, flexible predecessor lineage

Backlog origins (scope of record; moved to `docs/history/backlog/completed/` at completion):

- `docs/history/backlog/2026-09-10-execute-plan-quota-window-pause-resume.md`
- `docs/history/backlog/2026-09-10-runtime-budget-guard-hooks.md`
- `docs/history/backlog/2026-09-10-flexible-predecessor-lineage-precondition.md` (absorbed here as a third origin per user decision 2026-09-11: its predecessor-check clauses live on the same execute-plan precondition surface this plan already owns, so a standalone plan would double-author the same files)

Plan review: `docs/reviews/*plan-review-execute-plan-runtime-guardrails*.md` (latest staged round by round number; findings folded before the next review).

Guidance: `projects/.ai-playbook/agent_workflow_guidelines.md` (plan quality sections).

## Terms

- **Probe**: `scripts/quota_window_probe.py`, the shared stdlib-only script that reports provider quota windows as one JSON document and optionally writes the guard flag.
- **Binding limit**: the reported limit whose `reset_at` is earliest; it decides the pause.
- **Budget gate**: the execute-plan checkpoint-boundary check (Step 1.5 and Step 3.5) that runs the Probe and either continues or starts the Budget pause.
- **Budget pause**: the pause protocol: finish the current boundary only, arm the guard flag, append a `budget_pause` record to `manifest.md`, skip Phase 5 tmp cleanup, schedule the resume, and stop.
- **Guard flag**: `~/.ai-playbook/runtime/budget-guard.flag`, the file the Probe writes when the pause decision fires; its content records runtime, reset epoch, and reset ISO time.
- **Fired marker**: `~/.ai-playbook/runtime/budget-guard.fired`, written by the hook on its first block so the session is interrupted once, not on every tool call.
- **Predecessor declaration**: the structured `Predecessors:` block a plan carries; each entry names a neutral work-item reference plus one or more outcome predicates.
- **Outcome predicate**: one verifiable kind of proof for a predecessor: `history-ref`, `ancestry`, or `artifact` (driver-verified), or `validator` (orchestrator-run with recorded exit evidence).
- **Skill-gate marker**: the plans-class marker under `~/.ai-playbook/runtime/skill-invoked/` refreshed before every plan-file write per `agents/hooks/skill-gate/README.md`.
- **Session key**: the value supplied to the marker recipe; emptiness is checked first (empty after strip becomes the literal `no-session`), otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume the execute-plan chain state at authoring: the prose-residual rider is archived via squash `47cdc6f`, the runtime-residuals plan reached `ready=yes` in the same squash, and the acceptance-witness plan is parked under `docs/plans/deferred/` and is NOT an origin of this plan; basis: `git log main` and the `docs/plans/` tree at authoring time (2026-09-11), plus the authoring instruction.
- assume the predecessor verification is a new driver CLI operation with its own closed reason code, invoked by the orchestrator before Phase 1; basis: the runtime contract assigns mechanical git verification to the driver ("the driver, not the shared prose or the adapter, owns these transitions"), the authoring target list names `scripts/execute_plan_runtime.py` and its selftests, and the origin requires test coverage for rebased, cherry-picked, and squashed histories.
- assume plans-side authoring wording (teaching plan authors how to declare predecessors) stays out of scope; the executor-side contract in `agents/skills/execute-plan/` defines which declarations are admissible; basis: the authoring target list names only the execute-plan skill files.
- assume the ZCode quota endpoint shape and the Codex rollout `rate_limits` shape are as recorded in the quota origin item (live-verified 2026-09-10); basis: the origin's feasibility findings; the tests pin recorded fixtures under `scripts/testdata/quota/`, never live endpoints or credentials.
- assume one-shot automation creation works from automation-born ZCode sessions as of 2026-09-10 (the 2026-09-02 refusal recorded in the origin is stale); basis: the 2026-09-10 re-check in the user-level instructions; the launchd and report-only fallbacks stay in the protocol regardless.
- assume no driver state-machine change is required for the budget pause: the pause fires between boundaries, the claim is already closed, and the driver never reads `manifest.md`; basis: the runtime contract's durable-driver boundary (the Markdown manifest is a human audit receipt, never the source of truth), proven by the Task 7 characterization test.
- assume the runtime stays standard-library-only with `python3` and `git` on `PATH`; basis: the runtime contract ("intentionally small and standard-library-only") and the existing selftest conventions.

Decision points requiring a grill: origin absorption = fold the flexible-predecessor item in as a third origin instead of a standalone plan: source: user decision 2026-09-11 in the authoring prompt; date: 2026-09-11; affected sections: header, Task 5, Task 6. Predecessor verification design = identity-versus-outcome rule (neutral work-item references plus verifiable outcomes, never a lone hardcoded commit identity): source: user decision 2026-09-11 in the authoring prompt; date: 2026-09-11; affected sections: Task 5, Task 6, and the contract section they add.

## Gist & Examples

Long execute-plan runs die mid-task when the provider 5-hour quota window ends: the session hits an opaque provider error at an arbitrary point, and scheduled overnight runs stay stranded until someone notices. Three backlog origins close this family in one pass, because they touch the same files: the execute-plan runtime surfaces and the hooks tree.

**Budget gate (origin 1).** Before (today): a run at hour four of the window blindly starts the next implement sub-agent, the provider rejects mid-task, and the session dies with an uncommitted worktree and no pause record. After (this plan): at the Step 1.5 boundary (after the per-task `done` verification passes) and the Step 3.5 boundary (after the round counter refresh), the orchestrator runs the Probe. The Probe prints one JSON document, for example:

```json
{"runtime": "zcode", "limits": [{"kind": "primary", "used_percent": 87.5, "reset_at_epoch": 1789146000, "reset_at_iso": "2026-09-11T18:00:00+01:00", "minutes_remaining": 12}], "binding": "primary", "pause_decision": "pause", "reasons": ["minutes_remaining 12 below 20"], "status": "ok"}
```

On `pause_decision: pause` the orchestrator completes only the finished boundary, arms the guard flag, appends a `budget_pause` record to `manifest.md` (runtime, reset epoch and ISO time, thresholds used, the next step that would have run), schedules the resume at `reset_at` rounded up to the whole minute plus one, and stops. The pause never fires mid-task, never skips a `done` commit, and never edits the plan file (the review digest stays intact for the resume exemption). A Probe failure fails OPEN: `status: unknown` notes the failure and the run continues. When the weekly `secondary` window is the binding one, the run reports for user decision instead of scheduling a same-day resume.

**Budget-guard hook (origin 2).** Before (today): between checkpoint boundaries nothing can stop a long sub-agent from running the window into the ground; skill discipline is the only control. After (this plan): a PreToolUse hook under `agents/hooks/budget-guard/` checks for the guard flag and, on its first sight, blocks one tool call with a wrap-up instruction:

```json
{"decision": "block", "reason": "Provider quota window for runtime zcode ends at 2026-09-11T18:00:00+01:00. Do not start new tool work. Finish the current sub-agent step, land the pending done commit if any, record the budget pause, and schedule the resume."}
```

(Codex hosts get the equivalent `{"permissionDecision": "deny", "reason": ...}` shape.) The fired marker makes it a single intervention; the hook never touches the Stop event (on Codex a Stop block means continue, the opposite of the desired effect); a missing or expired flag passes every call. The hook is offline: it only reads two files, well inside the 5 to 10 second hook timeout.

**Flexible predecessor lineage (origin 3).** Before (today): a plan that names one exact commit identity as its prerequisite proof blocks valid executions whenever history was rebased, cherry-picked, or squashed, because the required work is present under a different identity. After (this plan): a plan declares predecessors as neutral work-item references with outcome predicates, and the driver verifies them repository-locally:

```json
{"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "history-ref", "value": "CRM-1234"}, {"kind": "ancestry", "value": "v1.2-tag"}, {"kind": "artifact", "path": "scripts/quota_window_probe.py", "contains": "pause_decision"}]}]}
```

`history-ref` matches a commit message containing the reference on the current history (identity-independent, so rebased, cherry-picked, and squashed variants all verify); `ancestry` uses the existing descendant check; `artifact` checks a repository path exists and contains a pinned span. A `validator` outcome is run by the orchestrator and recorded as exit evidence. When no outcome verifies, the driver returns `blocked` with reason `precondition-unverified` and a diagnostic naming the reference and every outcome it tried; a malformed declaration fails closed the same way. A declared commit identity is never as the sole proof of a prerequisite.

Edge cases covered: minutes exactly at the threshold (20 minutes remaining continues, 19 pauses; used percent exactly 90 pauses, 89 continues); a guard flag whose reset time is in the past is ignored and removed by the hook (self-cleaning after resume); a fired-marker write failure still blocks once (the block is the safety effect; the marker is only anti-thrash); a probe run with no runtime detectable returns `status: unknown` and the gate continues the run; a plan with no `Predecessors:` block skips the verification step entirely.

## Evaluation Criteria

**Quality dimensions:**

- correctness: boundary tests at exactly the 20 minute and 90 percent thresholds; binding selection picks the earliest `reset_at`; the pause protocol never crosses a `done` boundary (Task 3 clause pins) and never edits the plan file.
- fail-open versus fail-closed split: Probe failures and missing flags open; predecessor verification failures and malformed declarations close; every direction has a named test.
- testability: every behavior is fixture-based under `scripts/testdata/quota/` or tmp-built git repositories; no network access and no real credentials anywhere in the suite.
- maintainability: one Probe with one JSON contract feeds both the skill gate and the hook; the reason-code set stays closed and documented in the contract.
- observability: the `budget_pause` manifest record carries runtime, reset epoch and ISO time, thresholds, and the next step; the hook block reason carries the runtime and reset time.
- hygiene: no credentials, personal absolute paths, or machine-specific identifiers in any committed file; host registration stays in README snippets with tilde paths only.

**Done when:**

- `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'`, `-p 'test_budget_guard_hooks.py'`, and `-p 'test_execute_plan_runtime*.py'` all pass.
- The final `## Validation Commands` block exits 0 on the completed tree.
- The public-hygiene scan exits 0 with the repo-rooted fallback patterns.

**Ship when:**

- The operator registers the hook on their hosts (README snippets cover `~/.zcode/cli/config.json` and `~/.codex/hooks.json`; user-managed, never committed).
- One live run pauses at a real quota boundary and resumes from the scheduled automation or the documented fallback.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/quota_window_probe.py` *(new)*
- `scripts/execute_plan_runtime.py` *(Task 5 additions only: the `verify_preconditions` operation, the `_git_commit_matching_reference` helper, the CLI table entry, the `main()` argument-gate relaxation for the manifest-free precondition operation, and the `_outcome` use for the new reason; all other methods are frozen; reject any review finding that touches them)*
- `scripts/runtime_capabilities.py` *(Task 5 only: admission of `precondition-unverified` into the closed reason-code sets this file owns, including `REASON_CODES`, `BLOCKING_REASON_CODES`, and `RESUMABLE_REASONS`; the rest of the file is frozen)*
- `agents/hooks/budget-guard/budget_guard_core.py` *(new)*
- `agents/hooks/budget-guard/zcode.sh` *(new)*
- `agents/hooks/budget-guard/codex.sh` *(new)*

**Tests:**

- `scripts/test_quota_window_probe.py` *(new)*
- `scripts/test_budget_guard_hooks.py` *(new)*
- `scripts/test_execute_plan_runtime.py` *(new predecessor and characterization tests appended; existing tests frozen)*

**Documentation:**

- `agents/skills/execute-plan/SKILL.md` *(Task 3 and Task 6 sections only: the Configuration table rows, the Budget gate subsection, the Step 1.5 and Step 3.5 gate sentences, the Step 0.5 resume note, the Phase 5 skip note, and the Step 0.6 predecessor clause; all other sections are frozen)*
- `agents/skills/execute-plan/runtime-contract.md` *(Task 5 only: the reason-code list membership, the CLI operation table row, and the new Predecessor verification section; the rest is frozen)*
- `agents/hooks/budget-guard/README.md` *(new)*
- `scripts/testdata/quota/zcode_limit_response.json` *(new fixture)*
- `scripts/testdata/quota/codex_rollout.jsonl` *(new fixture)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/plans/SKILL.md`; reason: plans-side authoring wording is a separate surface; this plan defines the executor-side contract only.
- `docs/plans/deferred/2026-09-10-execute-plan-acceptance-witness-and-archive-closure.md`; reason: parked by the 2026-09-11 threat-model triage; not an origin of this plan.
- `scripts/execute_plan_runtime_codex.py`; reason: the adapter's protocol-translation surface is unaffected by all three origins.
- `agents/skills/execute-plan/subagent-prompts.md` and `agents/skills/execute-plan/agent-logs.md`; reason: the pause report and manifest rows reuse existing wording; no template change is required.
- `~/.zcode/cli/config.json` and `~/.codex/hooks.json`; reason: host registration is user-managed and never committed; the README documents the snippets.

## Design Invariants (CR Guard)

- Fail-direction split is explicit: the budget gate fails OPEN (a Probe failure never blocks a run; the hook passes when the flag is missing or expired) while predecessor verification fails CLOSED (an unverifiable or malformed declaration blocks with a diagnostic). Neither direction may be inverted by review-driven edits.
- Authorization boundary unchanged: no operation gains automatic approval. Scheduling the resume automation creates work, never authorization; push, merge, and deploy stay governed by their own rules.
- Manifest ownership unchanged: `budget_pause` is recorded only in the human-readable `manifest.md`; the driver never reads it; `runtime_state.json` stays untouched by the pause; the plan file is never edited by the pause protocol.
- The hook is PreToolUse-only: no Stop-event registration on any runtime (on Codex a Stop block means continue). The hook never relaunches, aborts, or rewrites anything; the block reason is an instruction to the orchestrator, not an action.
- The driver never performs commits and never executes plan-declared commands: `validator` outcomes are orchestrator-run; driver outcome kinds stay repository-local reads (`history-ref`, `ancestry`, `artifact`).
- Post-chain runtime invariants from the `47cdc6f` squash stay intact: atomic manifest writes, generation fencing, owner claims, the closed reason-code set, and the done-boundary witnesses are not weakened by this plan.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO" || exit 1

expect_match() {
  if ! grep -qF -- "$1" "$2"; then echo "MISSING: $1 in $2"; exit 1; fi
}
expect_no_match() {
  pat=$1; shift
  for f in "$@"; do
    test -e "$f" || { echo "ABSENT: $f"; exit 1; }
    grep -qF -- "$pat" "$f"; rc=$?
    if [ "$rc" -eq 0 ]; then echo "FORBIDDEN: $pat in $f"; exit 1
    elif [ "$rc" -ge 2 ]; then echo "GREP ERROR rc=$rc on $f"; exit 1; fi
  done
}

python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py' || exit 1
python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py' || exit 1
python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py' || exit 1

expect_match "Budget gate (quota-window pause" agents/skills/execute-plan/SKILL.md
expect_match "budget_pause" agents/skills/execute-plan/SKILL.md
expect_match "quota_window_probe.py" agents/skills/execute-plan/SKILL.md
expect_match "budget_pause_minutes_before_reset" agents/skills/execute-plan/SKILL.md
expect_match "budget_pause_max_used_percent" agents/skills/execute-plan/SKILL.md
expect_match "budget_probe_runtime" agents/skills/execute-plan/SKILL.md
expect_match "Predecessor verification" agents/skills/execute-plan/SKILL.md
expect_match "--operation precondition" agents/skills/execute-plan/SKILL.md
expect_match "never as the sole proof" agents/skills/execute-plan/SKILL.md

expect_match "precondition-unverified" agents/skills/execute-plan/runtime-contract.md
expect_match "verify_preconditions" agents/skills/execute-plan/runtime-contract.md
expect_match "def verify_preconditions" scripts/execute_plan_runtime.py
expect_match "_git_commit_matching_reference" scripts/execute_plan_runtime.py
expect_match "precondition-unverified" scripts/runtime_capabilities.py

expect_match "budget-guard.flag" agents/hooks/budget-guard/README.md
expect_match "fails open" agents/hooks/budget-guard/README.md
expect_match "budget-guard.flag" agents/hooks/budget-guard/budget_guard_core.py
expect_match "fired" agents/hooks/budget-guard/budget_guard_core.py
expect_match "permissionDecision" agents/hooks/budget-guard/budget_guard_core.py
expect_match "zcode" agents/hooks/budget-guard/zcode.sh
expect_match "codex" agents/hooks/budget-guard/codex.sh

PUBLIC_HYGIENE_PATTERNS_FILE="${PUBLIC_HYGIENE_PATTERNS_FILE:-$REPO/docs/scan-public-hygiene.patterns.example}" bash scripts/scan-public-hygiene.sh || exit 1
```

Notes: every `expect_match` pattern above is RED-today (verified at authoring on the 2026-09-11 tree: zero hits for every pattern, the hook directory and the Probe module absent) and flips GREEN with its owning task: the SKILL.md pins with Task 3 and Task 6, the driver and capability pins with Task 5, the contract pins with Task 5, and the hook pins with Task 4. The `expect_no_match` helper is defined for fold-time use and is intentionally unused in the final block; rule 10 requires the helper exist and abort correctly, and its polarity was executed at authoring: a forbidden match exits 1 and an absent file exits 1 (both recorded below the block). The greps sweep only the plan's own must-fix files, so the plan document's own text can never self-match (rule 15). The hygiene scan is anchored to the repo root and uses the repo-rooted fallback patterns when no host patterns file exists.

### Task 1: Probe limit contract, parsing, and binding selection

Files:
- `scripts/quota_window_probe.py` *(new)*
- `scripts/test_quota_window_probe.py` *(new)*
- `scripts/testdata/quota/zcode_limit_response.json` *(new)*
- `scripts/testdata/quota/codex_rollout.jsonl` *(new)*

- [x] `QuotaWindowProbeTest#test_parse_zcode_limits`; given the recorded `zcode_limit_response.json` fixture (a `limits[]` array with a `TOKENS_LIMIT` entry carrying `percentage` and `nextResetTime` epoch milliseconds and a `TIME_LIMIT` entry with `unit: 5`), expects both entries parsed into the limits list with `kind`, `used_percent`, `reset_at_epoch` (seconds), `reset_at_iso` (local time from the epoch, never a hardcoded zone), and `minutes_remaining`
- [x] `QuotaWindowProbeTest#test_parse_codex_rollout_windows`; given the recorded `codex_rollout.jsonl` fixture whose last turn carries `rate_limits` with `primary.window_minutes: 300`, `primary.used_percent`, `primary.resets_at` epoch seconds, and a `secondary` 10080 window, expects both windows parsed with the same field contract
- [x] Calibrate the ZCode kind mapping per the origin's do-not-skip instruction: cross-check `nextResetTime` of the `TOKENS_LIMIT` and `TIME_LIMIT` entries against the observed exhaustion line in the local ZCode log, fix the recorded fixture's `kind` fields and the parser's mapping to the calibrated truth, and note the finding (including any timezone discovery) in the task log; timezone encoding stays in the user facts document, never in the skill
- [x] `QuotaWindowProbeTest#test_binding_earliest_reset`; given limits with a primary window resetting later than the secondary, expects `binding` set to `secondary`; given the primary earliest, expects `primary`
- [x] `QuotaWindowProbeTest#test_minutes_remaining_negative_maps_to_expired`; given a reset time in the past, expects `minutes_remaining` of 0 or less and `pause_decision: pause`
- [x] `QuotaWindowProbeTest#test_pause_decision_minutes_boundary`; given used percent 10 and `minutes_remaining` exactly 20 against threshold 20, expects `pause_decision: continue`; given 19, expects `pause`
- [x] `QuotaWindowProbeTest#test_pause_decision_percent_boundary`; given `minutes_remaining` 120 and used percent exactly 90 against threshold 90, expects `pause_decision: pause`; given 89, expects `continue`
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_quota_window_probe.py'` (module does not exist; import error counted as RED)
- [x] Write the minimal pure-core implementation: limit dataclasses, `parse_zcode_limits`, `parse_codex_rollout`, binding selection, threshold evaluation with defaults 20 minutes and 90 percent overridable by argument, and the top-level `build_report` returning the exact JSON contract from the Gist (`runtime`, `limits`, `binding`, `pause_decision`, `reasons`, `status`)
- [x] Run → expect GREEN: the same discovery command passes
- [x] Run → expect GREEN (rest of the runtime suite unaffected): `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'`
- [x] Commit: `feat: quota probe limit contract and binding selection`

### Task 2: Probe transports, runtime discovery, fail-open, and flag write

Files:
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [x] `QuotaWindowProbeTest#test_zcode_fetch_via_injected_transport`; given a config fixture carrying `provider.zai.options.apiKey` and an injected transport returning the recorded endpoint JSON, expects the request to carry the raw key in an `Authorization` header (no `Bearer` prefix) and the report `status: ok`
- [x] `QuotaWindowProbeTest#test_zcode_missing_key_fail_open`; given a config fixture without the key, expects `status: unknown`, `pause_decision: continue`, and a non-empty `reasons` entry; expects no exception escapes
- [x] `QuotaWindowProbeTest#test_zcode_transport_error_fail_open`; given an injected transport raising, expects `status: unknown` and `pause_decision: continue`
- [x] `QuotaWindowProbeTest#test_codex_rollout_discovery_newest`; given a tmp sessions tree with several dated rollout files, expects discovery to select the newest by name sort (`rollout-*.jsonl`)
- [x] `QuotaWindowProbeTest#test_codex_missing_rollout_fail_open`; given an empty sessions tree, expects `status: unknown` and `pause_decision: continue`
- [x] `QuotaWindowProbeTest#test_runtime_explicit_override`; given `--runtime codex` on a host with a ZCode config present, expects the codex path only; given `--runtime zcode`, the zcode path only
- [x] `QuotaWindowProbeTest#test_runtime_autodetect_order`; given both host markers present and no override, expects `zcode` selected (documented precedence)
- [x] `QuotaWindowProbeTest#test_write_flag_writes_on_pause_only`; given a pause decision and `--write-flag <tmp>/budget-guard.flag`, expects the file created with `runtime=`, `reset_at_epoch=`, and `reset_at_iso=` lines; given a continue decision, expects no file created
- [x] `QuotaWindowProbeTest#test_secondary_binding_reports_no_schedule`; given the secondary window binding, expects a `reasons` entry instructing report-only handling instead of a same-day resume
- [x] Run → expect RED: the same discovery command (new test methods fail against the Task 1 core)
- [x] Implement the transports: zcode endpoint fetch via `urllib` behind an injectable transport with the config-path and URL overridable by argument, codex rollout discovery and tail parse, runtime detection and override, and the `--write-flag` mode (atomic write, mode `0o600`, into `~/.ai-playbook/runtime/` when the orchestrator passes that path); the endpoint fetch runs in the orchestrator's host context only, never inside a worker action envelope (task policy tokens keep `network: false`)
- [x] Run → expect GREEN: the same discovery command passes
- [x] Commit: `feat: quota probe runtime transports, discovery, and flag write`

### Task 3: Wire the budget gate into the execute-plan skill

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add three rows to the Configuration (from facts document) table: `budget_pause_minutes_before_reset` (pause when the binding window ends within N minutes; fallback `20`), `budget_pause_max_used_percent` (pause when the binding window used percent is at or above N; fallback `90`), `budget_probe_runtime` (force `zcode` or `codex` instead of auto-detect; fallback `auto`), resolved from the opening TOML block of `.ai-playbook/facts.md` per the existing table convention
- [x] Add a `Budget gate (quota-window pause and resume)` subsection after the Configuration table prescribing: run `python3 scripts/quota_window_probe.py --minutes-before <N> --max-percent <P> [--runtime <id>] --write-flag ~/.ai-playbook/runtime/budget-guard.flag` at the Step 1.5 and Step 3.5 boundaries only, never mid-task; on `pause_decision: continue` (or `status: unknown`, noting the failure in `manifest.md`) continue the normal flow; on `pause` run the pause protocol: finish the current boundary only, keep the written guard flag armed, append a `budget_pause` line to `manifest.md` with runtime, reset epoch and ISO time, thresholds used, and the next step that would have run, then schedule the resume: reset time rounded UP to the whole minute plus one minute (the guard flag is host-global: while armed it gates every session's tool calls on the host until expiry or manual removal, mirroring the hook README's host-scope note); on a ZCode host create a one-shot scheduled automation whose self-contained resume prompt says to execute the plan path, read the `budget_pause` record, apply the Step 0.5 resume rules, clear `~/.ai-playbook/runtime/budget-guard.flag` and `budget-guard.fired` before relaunching work, and stand down if the plan is archived or a peer session resumed it; if the automation create is refused fall back to a launchd one-shot on the host clock; if both are unavailable end with a report-only outcome naming the exact resume command and time; the resume prompt continues through the normal Step 0.5 resume path and the driver's `continue` operation (a budget pause leaves no blocked claim, so the blocked-claim `resume` operation does not apply); on a Codex host use the launchd one-shot with a sentinel self-disable file; when the binding limit is the weekly `secondary` window, do not schedule: report for user decision
- [x] Insert one gate sentence at the end of Step 1.5 and one at the end of Step 3.5, each: after this boundary's verification passes, run the Budget gate before starting any new work; on a pause the run stops here (Phase 5 is never reached, so session tmp survives for resume by construction)
- [x] Add a Phase 5 note: a run paused by the Budget gate never reaches Phase 5; tmp cleanup stays skipped until a resumed run completes the full workflow
- [x] Add a Step 0.5 resume note: the resume exemption digest rule is unaffected because the pause protocol never edits the plan file; the resumed orchestrator clears the guard flag and fired marker before relaunching any worker
- [x] Run → expect GREEN: `grep -c "budget_pause" agents/skills/execute-plan/SKILL.md` is at least 3 (table-independent gate clause, pause record, resume note)
- [x] Run → expect GREEN: the full runtime suite still passes (no code change in this task)
- [x] Commit: `docs: wire execute-plan budget gate at checkpoint boundaries`

### Task 4: Budget-guard PreToolUse backstop hook

Files:
- `agents/hooks/budget-guard/README.md` *(new)*
- `agents/hooks/budget-guard/budget_guard_core.py` *(new)*
- `agents/hooks/budget-guard/zcode.sh` *(new)*
- `agents/hooks/budget-guard/codex.sh` *(new)*
- `scripts/test_budget_guard_hooks.py` *(new)*

- [x] `BudgetGuardHookTest#test_flag_absent_passes`; given no guard flag at the configured path, expects exit 0 and empty stdout
- [x] `BudgetGuardHookTest#test_zcode_block_shape_and_exit`; given a guard flag present and no fired marker, expects stdout exactly `{"decision": "block", "reason": "Provider quota window for runtime zcode ends at 2026-09-11T18:00:00+01:00. Do not start new tool work. Finish the current sub-agent step, land the pending done commit if any, record the budget pause, and schedule the resume."}` (built via `json.dumps`, never string concatenation) and exit code 2
- [x] `BudgetGuardHookTest#test_codex_deny_shape`; given the same flag and the codex runtime argument, expects stdout exactly `{"permissionDecision": "deny", "reason": "Provider quota window for runtime codex ends at 2026-09-11T18:00:00+01:00. Do not start new tool work. Finish the current sub-agent step, land the pending done commit if any, record the budget pause, and schedule the resume."}` and exit 0
- [x] `BudgetGuardHookTest#test_fired_marker_single_intervention`; given the flag and an existing fired marker, expects exit 0 and empty stdout (the session was already interrupted once)
- [x] `BudgetGuardHookTest#test_fired_marker_written_on_block`; given the flag and no fired marker, expects the marker created after the first block; the block itself still fires
- [x] `BudgetGuardHookTest#test_fired_marker_write_failure_still_blocks`; given the flag and an unwritable fired-marker directory, expects the block still fires (the block is the safety effect; the marker is anti-thrash only)
- [x] `BudgetGuardHookTest#test_expired_flag_ignored_and_removed`; given a flag whose `reset_at_epoch` is in the past, expects exit 0, empty stdout, and both flag and fired marker removed
- [x] `BudgetGuardHookTest#test_flag_read_error_fail_open`; given an unreadable flag file, expects exit 0 and empty stdout (a broken backstop never blocks)
- [x] `BudgetGuardHookTest#test_hook_completes_within_host_timeout`; given the flag present, expects one hook invocation to complete within a 10-second subprocess timeout (the outer ceiling a host PreToolUse hook may impose; a timeout fails the test) with no network access (the hook module imports no network modules)
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'` (the hook directory does not exist)
- [x] Implement the core: stdlib-only, reads the flag path and runtime from arguments, ignores stdin, applies the expired-flag and fired-marker rules above, emits the per-runtime block envelope via `json.dumps` with the reason interpolating the runtime and reset ISO time from the flag, and never reads the network; thin `zcode.sh` and `codex.sh` adapters pass the runtime id and exit code convention (zcode block exits 2; codex block exits 0 with the deny JSON)
- [x] Write the README: what the gate protects, the flag-file contract (path, content lines, expiry), the fired-marker anti-thrash rule, the fail-open rule ("a missing flag fails open; the hook never blocks without it"), a host-scope note (the guard flag and fired marker live under `~/.ai-playbook/runtime/` and are host-global: on a shared host they gate every session's tool calls until expiry or manual removal, and the flag content names the plan slug for forensics), registration JSON snippets for `~/.zcode/cli/config.json` `hooks.events.PreToolUse` and `~/.codex/hooks.json` `PreToolUse` with tilde paths only, a fixture test mode recipe (synthetic flag file in tmp; no network, no credentials), and a PreToolUse-only note: never register this hook on a Stop event
- [x] Run → expect GREEN: the same discovery command passes
- [x] Commit: `feat: budget-guard PreToolUse backstop hook`

### Task 5: Driver precondition verification operation

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `ExecutePlanRuntimeTest#test_precondition_history_ref_verifies_rebased_history`; given a tmp fixture repo where a commit message contains `CRM-1234` and HEAD was rebased onto a newer base (the commit identity changed), expects the `history-ref` outcome to verify and the operation to return `status: success` with per-predecessor evidence
- [x] `ExecutePlanRuntimeTest#test_precondition_history_ref_verifies_cherry_picked_history`; given the referenced work cherry-picked onto a new branch under a different identity, expects `history-ref` to verify
- [x] `ExecutePlanRuntimeTest#test_precondition_history_ref_verifies_squashed_history`; given two referenced work commits squashed into one whose message carries both references, expects `history-ref` to verify for each reference
- [x] `ExecutePlanRuntimeTest#test_precondition_ancestry_outcome`; given an `ancestry` outcome naming a base commit that is an ancestor of HEAD, expects it to verify; given an unrelated commit, expects it not to
- [x] `ExecutePlanRuntimeTest#test_precondition_artifact_outcome`; given an `artifact` outcome whose path exists under the repository root and whose content contains the pinned span, expects it to verify; given the span absent, expects it not to
- [x] `ExecutePlanRuntimeTest#test_precondition_fails_closed_names_reference`; given a predecessor whose outcomes all fail, expects `status: blocked`, `reason_code: precondition-unverified`, `resume_allowed: true`, and a diagnostic naming the reference and every outcome tried
- [x] `ExecutePlanRuntimeTest#test_precondition_malformed_declaration_fails_closed`; given a declaration with an unknown outcome kind, an empty outcome list, or a missing `ref`, expects `blocked` with `precondition-unverified` and a malformed-declaration diagnostic
- [x] `ExecutePlanRuntimeTest#test_precondition_any_outcome_verifies`; given one failing and one passing outcome on the same predecessor, expects success (outcomes are OR-combined per reference)
- [x] `ExecutePlanRuntimeTest#test_precondition_history_ref_fixed_string_no_regex_meta`; given a reference `PROJ-1.3` and a fixture history whose commit message contains `PROJ-123` but never the literal `PROJ-1.3`, expects no verification (the reference is matched as a fixed string, never as a basic regex; the dot must not act as a wildcard)
- [x] `ExecutePlanRuntimeTest#test_precondition_cli_without_manifest`; given a CLI dispatch with `--operation precondition`, a valid `--predecessors-file`, and no `--manifest` argument, expects the verdict JSON on stdout instead of the missing-required-argument error (the operation is manifest-free end to end)
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime*.py'` (the operation does not exist; the new tests fail)
- [x] Implement `def verify_preconditions` in `scripts/execute_plan_runtime.py`: reads a `--predecessors-file` JSON document plus the repository root resolved from the working directory (the operation requires no machine manifest and must not load one), evaluates the `history-ref`, `ancestry`, and `artifact` outcome kinds repository-locally (new `_git_commit_matching_reference` helper running `git log -F --grep` against HEAD-reachable history, fixed-string matching, never a basic regex; the existing `_git_commit_is_descendant` and safe-path reads for the others), OR-combines outcomes per reference, and returns the normalized result with `precondition-unverified` on any failure; register the CLI operation table entry `precondition` and relax `main()`'s argument gate so this operation runs without `--manifest`; admit `precondition-unverified` into the closed reason-code sets in `scripts/runtime_capabilities.py` named by the Review Scope note (`REASON_CODES`, `BLOCKING_REASON_CODES`, `RESUMABLE_REASONS`)
- [x] Document in `agents/skills/execute-plan/runtime-contract.md`: add `precondition-unverified` to the standard reason-code list, add the `precondition` row mapped to `verify_preconditions` in the CLI operation table, and add a `Predecessor verification` section defining the declaration shape, the three driver-evaluated kinds, the orchestrator-run `validator` kind (exit evidence recorded in `manifest.md`; the driver never executes plan-declared commands), the OR-combination rule, and the closed failure diagnostic
- [x] Run → expect GREEN: the same discovery command passes including all new tests
- [x] Commit: `feat: driver precondition verification operation`

### Task 6: Wire flexible predecessor verification into the execute-plan skill

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add a `### Step 0.6: Predecessor verification (hard gate, before Phase 1)` subsection: when the plan carries a `Predecessors:` block, build the declaration JSON from it and run `python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file <json>` (the operation verifies against the repository working tree and takes no machine manifest: a fresh run has not created `runtime_state.json` yet, and the driver raises on a missing manifest path); on `blocked: precondition-unverified` stop before any implement launch, report the driver's diagnostic (the reference and the outcomes tried), and record the returned result in `manifest.md`; a plan without the block skips this step
- [x] In the same clause: `validator` outcomes are run by the orchestrator (never by the driver) with the exit evidence recorded in `manifest.md` before the run proceeds; a declared commit identity is never as the sole proof of a prerequisite; when a plan text carries only a bare commit identity for a prerequisite, treat it as a `history-ref` value plus at least one `ancestry` or `artifact` outcome, and stop with a diagnostic when none verifies
- [x] Apply the identity-versus-outcome principle to this plan's own anchors: this plan pins symbols, test names, and grep spans only; no task or validation command pins a commit identity as proof
- [x] Run → expect GREEN: `grep -q "### Step 0.6: Predecessor verification" agents/skills/execute-plan/SKILL.md` (the new hard-gate subsection exists; the Validation block's own span check covers the section name)
- [x] Run → expect GREEN: the full runtime suite still passes (no code change in this task)
- [x] Commit: `docs: wire flexible predecessor verification into execute-plan`

### Task 7: Resume characterization and full validation

Files:
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_continue_selects_first_incomplete_after_budget_pause_gap`; given a manifest with tasks 1 and 2 completed and no claim in flight (the state a budget-paused run leaves behind), expects the driver `continue` operation (`continue_parent`) to select task 3 as the next incomplete step without relaunching or re-checkpointing the completed tasks; the blocked-claim `resume` operation is not the budget-pause continuation path (a pause leaves no blocked claim); this is a characterization test: it captures existing behavior, runs GREEN before and after with no production change
- [x] Run → expect GREEN (characterization, captures behavior before any potential later change): the discovery command passes
- [x] Run the complete `## Validation Commands` block from the repo root; expect GREEN (every pinned span landed with its owning task; the hygiene scan exits 0 with the fallback patterns)
- [x] Commit: `test: characterize budget-pause continuation to the next incomplete task`
