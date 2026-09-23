# execute-plan: SKILL.md telemetry paths name `.jsonl` and fail runtime_capabilities tests

- Status: open
- Priority: High
- Area: execute-plan
- Driver: validation probe regression observed during 2026-09-22-execution-integrity-worker-evidence execution (Task 1, probe 2)
- Driving force: the P37 context-budget landing (b4c5e902) added telemetry path literals `context.jsonl` (three occurrences in execute-plan/SKILL.md lines ~529/531: review-loop lane, execution blueprint payload, authoring blueprint payload). `scripts/test_runtime_capabilities.py` has two hard assertions that shared skill bodies name no vendor runtime/command/event envelope; the `.jsonl` suffix is on its vendor-event-envelope deny list, so `test_shared_skill_bodies_have_no_runtime_names` and `test_cross_artifact_contract_coherence` both fail on pristine main (verified in a detached main worktree at 56102482, 2 failures, unrelated to the executing plan's edits).

## Findings

- The plan's Validation Command probe 2 (`python3 -m unittest test_runtime_capabilities`) therefore cannot go GREEN on any tree based on current main; the executing plan defers this and records the probe as pre-existing-red with main-worktree evidence.
- Fix shape is not runnable from the execute-plan plan: one candidate remedy edits the frozen SKILL.md sections (out of that plan's scope list), another edits `scripts/runtime_capabilities.py`/its tests (explicitly out of scope: runtime scripts owned by the codex-reconciliation runtime plan). Hence a separate origin.

## Suggested fix

Either (a) add an exemption/allowlist entry in `scripts/runtime_capabilities.py` for the pinned literal telemetry paths (keeping the `.jsonl` deny rule for prose), with a mirrored test fixture update, or (b) reword the SKILL.md telemetry literals to a non-enumerated suffix (e.g. `context-telemetry log paths`), updating the pins that quote them. Option (b) touches pins; verify `scripts/check_maintenance_pins.sh` stays green.
