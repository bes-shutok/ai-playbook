# Model-guard refusal-contract edges

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-codex-model-guard-refusal-contract-edges.md`

Classification: [class: fix-class] fail-closed contract edges (two low-impact r7 review finds); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Structured refusal**: `model_guard_check`'s `runtime-policy-unavailable` shape for `selected_config`. On the pinned interpreter (Python 3.14) the origin's construction-escape premise is FALSE: non-strict `Path.resolve()` returns the loop path without raising, the adapter constructs, and the probe's own `_resolve_path` already returns the exact structured refusal (live-simulated). The behavior the origin demands already holds; this plan freezes it with a characterization pin and records the allowlist, so an interpreter or refactor change that breaks the refusal gets caught.
- **Success JSON shape**: the probe's successful result carries `failed_check`, `error`, and `recovery` as empty strings beside the value-bearing fields; the process-level test asserts the full key set.

## Coverage dispositions (verified on disk 2026-10-02, at HEAD)

- The archived alignment plan's Privacy criterion bytes are immutable (completed history): the allowlist arm documents the success shape in the probe's own module documentation instead, which the origin's "or" alternative covers.
- The process-level test already asserts the full success key set including the empty refusal-detail fields (the test file's allowlist line); the documentation arm records what that test enforces, homed in the probe module because the archived alignment plan's bytes are immutable completed history (not the origin's field-removal alternative).
- The origin's Additional-witness class is single-arm; the plan-g7-style completed-history adjudication does not apply here (the alignment plan is cited, never edited).
- The pins suite reads red today for a pre-existing environmental reason (the PLAN-PROMPTS all-served entry p82-codex-model-guard-activation-probe-and-recovery awaits its own prune by that entry's owner); this plan's Validation records the pins line with that baseline note, and the branch diff carries only this plan's own surfaces.

## Tasks

### Task 1: symlink-loop config resolution stays inside the refusal contract

Files:
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime_codex.py`

Evidence:
- `PYTHONPATH=scripts python3 -m pytest scripts/test_execute_plan_runtime_codex.py -k symlink_loop -q`

- [ ] Run → expect RED: `grep -c "test_symlink_loop_config_override_refuses_without_mutation" scripts/test_execute_plan_runtime_codex.py` returns 0 [class: REPOSITORY_TEST]
- [ ] Add `test_symlink_loop_config_override_refuses_without_mutation` as a green-at-RED characterization pin (the behavior already holds; the pin freezes it): a `CODEX_CONFIG` override pointing at a symlink loop (Path.symlink_to(self), the probe fixture's own pattern); the adapter constructs without escaping, `model_guard_check()` returns the structured `runtime-policy-unavailable` refusal naming `selected_config`, and the adapter path mutates no run state (the origin's construction-escape premise is false on the pinned Python 3.14 interpreter, where non-strict resolve() returns the loop path and the probe's own _resolve_path produces the refusal - live-simulated; the pin catches any interpreter or refactor change that moves the failure to construction) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command (green at first run - the characterization shape; the RED grep above is the gate) [class: REPOSITORY_TEST]
- [ ] Commit: `codex: characterize the symlink-loop structured refusal` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the probe's success JSON key set documented

Files:
- `scripts/codex_model_guard_probe.py`

Evidence:
- `grep -c "failed_check" scripts/codex_model_guard_probe.py` returns at least 2

- [ ] Run → expect RED: `grep -c "empty refusal-detail" scripts/codex_model_guard_probe.py` returns 0 [class: REPOSITORY_TEST]
- [ ] Expand the probe module's one-line docstring into an output-contract docstring whose Success-shape section names the full successful key set explicitly: the value-bearing fields plus `failed_check`, `error`, and `recovery` present as empty refusal-detail fields on success, matching the process-level test's allowlist [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence command and the RED grep now returning 1 [class: REPOSITORY_TEST]
- [ ] Commit: `probe: success JSON key set documented with the empty refusal-detail fields` [class: IMPLEMENTATION_REQUIRED]

### Task 3: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime_codex.py scripts/test_codex_model_guard_probe.py -q
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime_codex.py -k symlink_loop -q
grep -c "empty refusal-detail" scripts/codex_model_guard_probe.py
```

## Assumptions

- The archived alignment plan's Privacy criterion is cited, never edited; the allowlist arm lands in the probe module's own documentation.
- The pins suite reads red today for a pre-existing environmental reason (the PLAN-PROMPTS all-served p82 entry awaits its owner's prune); the Validation records that baseline, and this plan's branch diff carries only its own surfaces.
- The symlink-loop arm is a characterization pin, not a behavior change: every current behavior is byte-identical by definition (the pin freezes what the live simulation showed).

Decision points requiring a grill: Task 1 failure direction (None - the structured refusal path - never an escaping exception); Task 1 mutation proof (the run manifest byte-unchanged); Task 2 documentation home (the probe module's docstring, never the archived plan's bytes).

## Review Scope

- `docs/history/plans/2026-10-02-model-guard-refusal-contract-edges.md`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/codex_model_guard_probe.py`
- `docs/history/backlog/2026-10-01-codex-model-guard-refusal-contract-edges.md`

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-01-codex-model-guard-refusal-contract-edges.md` - the plan's sole origin; executed+landed 2026-10-02 (landing d977a3df), origin file deleted in this completion pass per the fold-and-delete rule with this section as its disposition record.
