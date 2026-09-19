# Plan: harness detection and budgeting skip

Backlog origins: docs/history/backlog/2026-09-18-detect-current-ai-harness.md; docs/history/backlog/2026-09-18-skip-unsupported-harness-budgeting.md (one plan, two ordered tasks; the second origin depends on the first)
Design input: docs/tmp/future-plan-prompts-2026-09-16.md (P10 group section)
Detection signal knowledge base: agents/skills/agterm/agent-runtimes.md (Inherited env marker column)
Language guidelines: projects/.ai-playbook/python_guidelines.md (helper and tests are Python)

## Terms

- **Live harness signal**: evidence available inside the current session's own process context (environment variables the harness injected, or the session's process ancestry), as opposed to host-installed-software evidence such as a config file another runtime left on disk.
- **Supported harness**: a runtime id in the detection set, currently `zcode` and `codex`.
- **Budgeting rule family**: the Budget gate boundary in the execute-plan and plans skills plus the maintenance loop's quota leg, together with everything those boundaries drive: the probe call, the pause protocol, the resume watcher, and the host-global guard flag.
- **Skip predicate**: the single consumer-side rule: when the live harness has no supported signal and no explicit runtime override is configured, skip the budgeting rule family for the session.
- **Detection seam**: the one shared helper module (`scripts/harness_detection.py`) that the probe and every consumer use to answer "which harness is live in this process".
- **Guard flag**: `~/.ai-playbook/runtime/budget-guard.flag`, the host-global pause flag the probe arms on a pause decision.

## Assumptions

- assume detection is process-scoped (a live signal in this session's environment or ancestry), never host-installed-software-scoped; basis: origin 1's witness is exactly the host-presence mis-bind (a zcode config file on a foreign harness's host auto-binds that runtime's quota window), and the mis-bind is the defect of record.
- assume zcode is detected by the `ZCODE_*` environment family (any `ZCODE_*` key counts, `ZCODE_APP_VERSION` is merely the documented example marker); basis: verified live in the authoring session (`ZCODE_APP_VERSION`, `ZCODE_BASE_URL`, `ZCODE_ENV`, `ZCODE_RUNTIME_ENV` present in this session's environment, `zcode-cli` in the process ancestry), and agents/skills/agterm/agent-runtimes.md lists `ZCODE_APP_VERSION` as the inherited env marker.
- assume codex is detected by a bounded process-ancestry scan because codex sets no reliable inherited env marker; basis: agents/skills/agterm/agent-runtimes.md marks Codex "none reliable" for inherited env markers.
- assume an explicit human override (the `budget_probe_runtime` facts key or the probe `--runtime` flag) suppresses the skip predicate; basis: plans SKILL.md Budget gate facts table and the explicit-wins rule in `detect_runtime` (scripts/quota_window_probe.py).
- assume the budget-guard hook adapters need no change; their per-runtime registration is itself the runtime identity; basis: agents/hooks/budget-guard/budget_guard_core.py takes a required `--runtime` limited to zcode and codex, and ships one adapter per registered runtime.
- assume the probe is already fail-safe when detection answers none (unknown report, continue decision, no flag armed); basis: the `detect_runtime` None path in `main()` produces `_unknown_report`, and `write_flag_if_paused` arms only on a pause decision.
- assume adding a future harness is a data-row addition to the signal table and requires no consumer edit; basis: origin 1's "rules stay harness-agnostic" and the ledger's no-per-harness-special-cases constraint.

Decision points requiring a grill: signal-table membership at v1 (zcode env family, codex bounded ancestry): decision standing pre-authorization accepting the verified-signal table, source authoring prompt 2026-09-18, affects Task 1; skip predicate placement consumer-side before probe resolution rather than inside the probe alone: decision standing pre-authorization accepting origin 2's consumer list, source authoring prompt 2026-09-18, affects Task 2; explicit override beats skip: decision standing pre-authorization, source authoring prompt 2026-09-18, affects Task 2; removal of file-presence auto-detect from the probe: decision standing pre-authorization accepting that the mis-bind is the defect of record, source authoring prompt 2026-09-18, affects Task 1; unsupported-harness quota-leg label `skipped-unsupported-harness` reusing the unknown-mode fallback semantics: decision standing pre-authorization, source authoring prompt 2026-09-18, affects Task 2.

## Gist & Examples

Two gaps in the budgeting rule family, both evidenced by the same incident class: a session running under a harness the family does not support still runs the quota probe, and the probe's auto-detect answers from host file presence rather than from the live process.

1. **The probe auto-detect binds a peer runtime's quota window.** `detect_runtime` (scripts/quota_window_probe.py) answers `zcode` when `~/.zcode/cli/config.json` exists and `codex` when `~/.codex/sessions` is a directory, with no reference to the current process. On a host with a zcode install, a session running under any other harness auto-detects `zcode`, probes zcode's live quota window, and can arm the host-global guard flag and schedule a resume the running harness cannot honor. Reproduced at authoring by reading `detect_runtime` and confirming the config path exists on this host.

   Example: a Cursor-hosted session runs the plans Budget gate with no `budget_probe_runtime` override. Today the probe auto-detects `zcode` from file presence, sees 95 percent used inside the pause threshold, and arms `~/.ai-playbook/runtime/budget-guard.flag`, which blocks tool calls host-globally for a window that means nothing to the Cursor session. After this plan the probe's auto path answers `none` (no live signal), the unknown report follows, and the consumer records a budget skip and continues.

2. **Unsupported harnesses have no skip predicate, so they inherit a family that cannot be correct for them.** The Budget gates in execute-plan and plans and the maintenance quota leg call the probe unconditionally. For an unsupported harness every outcome is wrong: a pause arms a foreign window, and a continue burns quota on a probe whose window is not the session's. The fix: one shared detection seam, one consumer-side skip predicate, one recorded label.

   Example: the maintenance quota leg on an unsupported harness runs the detection helper, records `quota_status: "skipped-unsupported-harness"` in the state file, and proceeds with the existing per-lane child cap plus the failure cap (the same operative fallback the unknown mode already uses), never calling the probe.

Design shape, deliberately narrow: one detection module with a signal table (zcode: any `ZCODE_*` environment key; codex: bounded process-ancestry scan matching the first token's basename; anything else: none), a tiny CLI so prose skill steps can call it exactly like they call the probe, and a skip predicate that lives in the four consumer surfaces, not in per-harness branches. Detection precedence inside the helper is environment first, ancestry second, documented and tested. The guard-flag hooks are untouched: their per-runtime registration already is the runtime identity. The probe keeps its explicit `--runtime` override as the first rule, and `detect_runtime`'s signature and `Optional[str]` return contract are unchanged so existing callers are unaffected.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe's auto path answers a runtime only from a live signal in the current process; the mis-bind canary (config file present, no environment signal) returns none; unit suites cover every signal-table row and the none row.
- simplicity: exactly one detection module; the consumers share one predicate sentence shape; no per-harness conditionals outside the signal table.
- hermeticity: the new unit tests inject the environment and the ancestry probe (no real process tree, no real home), so they pass on any host.
- documentation alignment: all four consumer surfaces carry the same predicate wording and the same label, and each surface's pin is validated per file.

**Done when:**
- `python3 -m pytest scripts/test_harness_detection.py scripts/test_quota_window_probe.py -q` passes.
- Validation command G3 (mis-bind canary) passes: with the detection seam patched to answer none, `detect_runtime(None)` returns `None` even though the real config file exists on disk (the seam patch, not the executor's process tree, is the input).
- G4 passes: with the seam patched to answer zcode, auto-detect answers `zcode`.
- The consumer surfaces carry the skip predicate (per-file pins G5 through G7b pass).
- The forbidden sweeps G9 and G10 confirm both file-presence lines are gone from `detect_runtime`.
- `bash -n` over the Validation Commands block exits 0.

**Ship when:**
- No external conditions; every criterion above is repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/harness_detection.py` *(new)*
- `scripts/quota_window_probe.py`

**Tests:**
- `scripts/test_harness_detection.py` *(new)*
- `scripts/test_quota_window_probe.py`

**Skill prose (prescribed insertions only, plus the single `quota_status` enumeration line in `agents/skills/maintenance/SKILL.md` that Task 2 prescribes; all other content in these files is frozen):**
- `agents/skills/execute-plan/SKILL.md` (Budget gate section: skip predicate paragraph)
- `agents/skills/plans/SKILL.md` (Budget gate section: skip predicate paragraph)
- `agents/skills/maintenance/SKILL.md` (Step 4 quota leg: skip predicate bullet)
- `agents/skills/maintenance/zcode.md` (Quota leg: skip predicate bullet)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/budget-guard/*`; reason: the hooks' per-runtime registration already carries the runtime identity (`--runtime` is required and limited to the supported set), so the skip predicate needs no hook change, and their fixture suite `scripts/test_budget_guard_hooks.py` is frozen unless a probe-contract change breaks it.
- Every other script and skill; reason: the ledger's simplicity-first constraint scopes this plan to one detection seam, one predicate, and the listed consumers.

## Validation Commands

```bash
#!/usr/bin/env bash
# Validation for: harness detection and budgeting skip
# The G3/G4 python blocks MUST run with the repo root as cwd (anchored below).
set -u
cd "$(git rev-parse --show-toplevel)" || { echo "not a repo" >&2; exit 1; }
fail() { echo "VALIDATION FAILED: $1" >&2; exit 1; }

# G1: helper unit suite
python3 -m pytest scripts/test_harness_detection.py -q || fail "G1 harness_detection unit suite"

# G2: probe unit suite (rewired auto-detect expectations)
python3 -m pytest scripts/test_quota_window_probe.py -q || fail "G2 probe unit suite"

# G3 mis-bind canary: with the detection seam patched to answer none, auto-detect
# must answer none even though the real config file exists on disk. The seam patch
# (not the executor's real process tree) is the input, so the canary is deterministic
# on any host. RED today: today's detect_runtime never consults the helper and
# answers zcode from file presence, so the python probe exits 1 and the fail branch
# below fires. GREEN only after Task 1 wires the helper through the patchable seam.
python3 - <<'PY'
import os, sys
sys.path.insert(0, "scripts")
import harness_detection
harness_detection.detect_harness = lambda env=None, ancestry=None: (None, "injected: seam patched to none")
import quota_window_probe as probe
answer = probe.detect_runtime(None)
print("detect_runtime answered:", answer)
sys.exit(0 if answer is None else 1)
PY
rc=$?
if [ "$rc" -ge 2 ]; then fail "G3 probe errored (rc=$rc)"; fi
if [ "$rc" -ne 0 ]; then fail "G3 mis-bind still present: file presence answered a runtime despite the none seam (rc=$rc)"; fi

# G4 wiring proof: with the detection seam patched to answer zcode, auto-detect
# answers zcode (proves detect_runtime consults the helper rather than file
# presence; the helper's own env/ancestry behavior is covered by the unit suite).
# STRUCTURALLY RED today: the helper module does not exist yet, so the import
# fails and the fail branch below fires; GREEN only after Task 1.
python3 - <<'PY'
import sys
sys.path.insert(0, "scripts")
import harness_detection
harness_detection.detect_harness = lambda env=None, ancestry=None: ("zcode", "injected: seam patched to zcode")
import quota_window_probe as probe
answer = probe.detect_runtime(None)
sys.exit(0 if answer == "zcode" else 1)
PY
rc=$?
if [ "$rc" -ge 2 ]; then fail "G4 probe errored (rc=$rc)"; fi
if [ "$rc" -ne 0 ]; then fail "G4 detect_runtime does not consult the detection seam"; fi

# G5: execute-plan Budget gate carries the skip predicate (per-file, exactly once).
test "$(grep -cF 'unsupported harness budget skip: before resolving the probe, run scripts/harness_detection.py' agents/skills/execute-plan/SKILL.md)" -eq 1 \
  || fail "G5 execute-plan skip predicate sentence missing or duplicated"

# G6: plans Budget gate carries the skip predicate (per-file, exactly once).
test "$(grep -cF 'unsupported harness budget skip: before resolving the probe, run scripts/harness_detection.py' agents/skills/plans/SKILL.md)" -eq 1 \
  || fail "G6 plans skip predicate sentence missing or duplicated"

# G7: maintenance Step 4 predicate bullet carries the label (exactly once). The
# pin includes the unquoted key so it cannot match the schema enum line, whose
# key is quoted.
test "$(grep -cF 'quota_status: "skipped-unsupported-harness"' agents/skills/maintenance/SKILL.md)" -eq 1 \
  || fail "G7 maintenance quota-leg label missing or duplicated"

# G7b: the schema enumeration line carries the extended enum (exactly once).
test "$(grep -cF '"quota_status": "ok|unknown|skipped-unsupported-harness"' agents/skills/maintenance/SKILL.md)" -eq 1 \
  || fail "G7b quota_status enum line missing or not extended"

# G8: overlay Quota leg carries the label (per-file, exactly once).
test "$(grep -cF 'skipped-unsupported-harness' agents/skills/maintenance/zcode.md)" -eq 1 \
  || fail "G8 overlay quota-leg label missing or duplicated"

# G9/G10 forbidden sweeps: BOTH file-presence auto-detect lines are gone from
# detect_runtime. Three-way rc split per sweep: rc 0 = forbidden match (fail),
# rc 1 = clean, rc >= 2 = tool error (fail).
grep -nF 'if pathlib.Path(zcode_config).exists():' scripts/quota_window_probe.py >/dev/null
rc=$?
if [ "$rc" -ge 2 ]; then fail "G9 sweep errored (rc=$rc)"; fi
if [ "$rc" -eq 0 ]; then fail "G9 zcode file-presence auto-detect still present in detect_runtime"; fi
grep -nF 'if pathlib.Path(codex_sessions).is_dir():' scripts/quota_window_probe.py >/dev/null
rc=$?
if [ "$rc" -ge 2 ]; then fail "G10 sweep errored (rc=$rc)"; fi
if [ "$rc" -eq 0 ]; then fail "G10 codex file-presence auto-detect still present in detect_runtime"; fi

# G10b: this block parses.
bash -n "$0" || fail "G10b validation block syntax"
echo "VALIDATION OK"
```

### Task 1: Shared harness detection helper and probe auto-detect rewiring

Files:
- `scripts/harness_detection.py` *(new)*
- `scripts/test_harness_detection.py` *(new)*
- `scripts/quota_window_probe.py`
- `scripts/test_quota_window_probe.py`

- [x] `HarnessDetectionTest#test_zcode_env_signal`; given an environment dict carrying `ZCODE_APP_VERSION=3.12.3`, expects `detect_harness` to answer `("zcode", "env")`
- [x] `HarnessDetectionTest#test_zcode_env_family_fallback`; given an environment carrying only `ZCODE_BASE_URL` (no `ZCODE_APP_VERSION`), expects `("zcode", "env")` (the family, not one key, is the signal)
- [x] `HarnessDetectionTest#test_codex_ancestry_signal`; given a clean environment and an ancestry probe returning `["zsh", "codex exec plan X", "launchd"]`, expects `("codex", "ancestry")`
- [x] `HarnessDetectionTest#test_codex_ancestry_matches_basename_only`; given a clean environment and an ancestry probe returning `["zcode --resume codex-notes", "launchd"]`, expects `(None, evidence)` (the word codex in a non-executable argument is not a codex ancestor; matching is on the first token's basename)
- [x] `HarnessDetectionTest#test_env_signal_precedence_over_ancestry`; given an environment carrying `ZCODE_APP_VERSION` and an ancestry probe returning a codex chain, expects `("zcode", "env")` (documented precedence: environment first)
- [x] `HarnessDetectionTest#test_codex_ancestry_when_env_foreign`; given an environment carrying only `CURSOR_INVOKED_AS=agent` and an ancestry probe returning a codex chain, expects `("codex", "ancestry")`
- [x] `HarnessDetectionTest#test_unsupported_harness_env`; given an environment carrying only foreign markers `CURSOR_INVOKED_AS=agent` and `CLAUDECODE=1`, expects `(None, evidence)` where the evidence names that no supported live signal was found
- [x] `HarnessDetectionTest#test_no_signal_at_all`; given a clean environment and an empty ancestry, expects `(None, evidence)`
- [x] `HarnessDetectionTest#test_ancestry_depth_bound_inclusive`; given a codex entry exactly six ancestors deep, expects `("codex", "ancestry")`; given the same entry seven deep, expects `(None, evidence)` (the bound is at most six ancestors scanned, documented next to the constant)
- [x] `HarnessDetectionTest#test_cli_prints_json`; given the module run as a script with an injected environment carrying no supported signal, expects one JSON line on stdout whose `harness` value is the literal string `none` (the token the skill predicates match on, not JSON null) plus `method` and `evidence` keys
- [x] `QuotaWindowProbeTest#test_autodetect_uses_live_env_signal`; given `ZCODE_APP_VERSION` set and a `HOME` pointed at an empty temp dir (no config file on disk), expects `detect_runtime(None)` to answer `"zcode"`
- [x] `QuotaWindowProbeTest#test_autodetect_ignores_file_presence`; given a `HOME` whose `~/.zcode/cli/config.json` exists and an environment with no `ZCODE_*` variable, expects `detect_runtime(None)` to answer `None` (RED today: the file-presence rule answers `zcode`; observed live at authoring, see the requirements buffer)
- [x] `QuotaWindowProbeTest#test_explicit_runtime_still_wins`; given `--runtime codex` and an environment carrying `ZCODE_APP_VERSION`, expects `detect_runtime("codex")` to answer `"codex"`
- [x] Run → expect RED: `python3 -m pytest scripts/test_harness_detection.py -q` (module and tests are new; import fails) and `python3 -m pytest scripts/test_quota_window_probe.py -q` (the two new probe expectations fail against today's file-presence rule)
- [x] Implement `scripts/harness_detection.py`: `SUPPORTED = ("zcode", "codex")`; a signal table with one row per supported harness (zcode: any `ZCODE_*` environment key; codex: a bounded parent-chain command scan, at most six ancestors, matching the first token's basename against the codex executable name so argument mentions never match); `detect_harness(env=None, ancestry=None)` returning `(harness_id_or_None, evidence)` where `ancestry` is an injectable callable (default: a real bounded `ps` walk, factored as its own module-level function so the default path is testable) so tests and validation inject chains instead of spawning processes; the CLI prints `harness` as the literal string `none` when unsupported; a `main()` printing one JSON line (`harness`, `method`, `evidence`); stdlib only
- [x] `HarnessDetectionTest#test_default_ancestry_walk_detects_codex`; given a fixture `ps` executable earlier on `PATH` that answers a canned parent chain containing a codex basename, expects the module's DEFAULT ancestry walk (no injectable callable passed) to produce `("codex", "ancestry")`
- [x] `HarnessDetectionTest#test_default_ancestry_walk_empty_chain`; given the same fixture `ps` answering an empty chain, expects the default walk to yield `(None, evidence)` (exercises the real walk code, not an injected list; the fixture script is created in a temp dir prepended to `PATH` for the test process only)
- [x] Rewire `detect_runtime` in `scripts/quota_window_probe.py`: explicit argument first (unchanged), then a call to the helper through the module attribute (`import harness_detection` at module top; call `harness_detection.detect_harness()` inside `detect_runtime`) so validation can patch the seam at the module boundary; delete the `pathlib.Path(zcode_config).exists()` and `codex_sessions.is_dir()` rules from the auto path; the function's signature and `Optional[str]` return contract are unchanged, so every existing caller is unaffected
- [x] Update `scripts/test_quota_window_probe.py` fixtures that relied on file-presence auto-detection to inject the live signals instead
- [x] Run → expect GREEN: both test files pass and Validation commands G3 and G4 pass
- [x] Commit: `probe: live-signal harness detection replaces file-presence autodetect`

### Task 2: Consumer-side budgeting skip predicate

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`

- [x] In `agents/skills/execute-plan/SKILL.md`'s Budget gate section, insert the skip predicate paragraph immediately before the probe-resolution block: `unsupported harness budget skip: before resolving the probe, run scripts/harness_detection.py` (resolved like BUDGET_PROBE: repo-local copy first, then the deployed home copy); when it reports `harness: none` and no `budget_probe_runtime` override is configured, record `budget_skip` in the run's manifest notes, skip the probe, the pause protocol, and the resume watcher, and continue; never arm or clear the guard flag from an unsupported harness; a missing or erroring helper counts as unsupported (record the evidence; the family must not run against an unknown harness)
- [x] In `agents/skills/plans/SKILL.md`'s Budget gate section, insert the same predicate paragraph adapted to its boundaries (record `budget_skip` in `{tmp_dir}/plan-requirements-<slug>.md`, same missing-helper rule); the same never-arm rule applies
- [x] In `agents/skills/maintenance/SKILL.md` Step 4 quota leg, insert the predicate bullet: run the detection helper first; on `harness: none` (this surface defines no override knob, so no override clause applies here), record `quota_status: "skipped-unsupported-harness"` on the child entry and proceed with the per-lane child cap plus the failure cap (the unknown-mode operative fallback) without calling the probe; same missing-helper rule
- [x] In `agents/skills/maintenance/SKILL.md`'s state-file schema documentation, replace the recorded `quota_status` enumeration line with exactly `"quota_status": "ok|unknown|skipped-unsupported-harness"` (one prescribed edit to that single line; the rest of the schema block stays frozen)
- [x] In `agents/skills/maintenance/zcode.md` Quota leg, add the matching bullet after the probe invocation line, naming the helper's CLI invocation and the label, stating that this leg has no override knob, and stating that the guard flag is never armed from an unsupported harness because the consumers never reach the probe
- [x] Run → expect GREEN: Validation commands G5 through G8 pass per file exactly once; G1 through G4, G9, and G10 still pass (no code change in this task)
- [x] Re-read each of the four inserted paragraphs against its own section's neighboring prose and adjust only the inserted paragraphs where they contradict what the section already says (the surrounding prose is frozen by the Review Scope)
- [x] Commit: `skills: skip the budgeting rule family on unsupported harnesses`
