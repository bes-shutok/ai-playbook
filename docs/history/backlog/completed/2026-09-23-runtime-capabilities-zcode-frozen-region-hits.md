# Runtime-capabilities shared-body scan RED: two pre-existing `zcode` tokens in frozen regions

Status: done (executed via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md)
Priority group: 1 (efficiency)
Class: real
Date: 2026-09-23

## Origin

Surfaced by the P48 post-execution residuals sweep execution (Task 2, commit 65d2bd0c) and confirmed by its Phase 3 review r1: `PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities` is RED on pristine main 1a949948 with exactly 2 failures, both `zcode` vendor-name violations from the shared-body scan (`find_forbidden_shared_terms`, which renders hits as `<path>: <term>` and has no path exemption):

- `agents/skills/plans/SKILL.md` (the literal path `agents/skills/maintenance/zcode.md` appears in its budget-gate wording; the file was introduced/extended by 341961d1's emission-suppression sentences)
- `agents/skills/execute-plan/SKILL.md` (same literal path in a region the P48 plan declares frozen)

The P48 plan could not fix either: one file is entirely outside its review scope, the other hit sits in a frozen region, and `scripts/runtime_capabilities.py` (the matcher owner) was deliberately excluded from P48 scope to avoid colliding with the active runtime reconciliation workstream. The plan's Gate 2 therefore cannot reach exit 0 without this item.

## Suggested fix

Either (a) reword the two sentences to reference the maintenance overlay without the literal `zcode` token (e.g. "the runtime overlay for the maintenance skill"), or (b) teach the matcher a path-shaped exemption for legitimate documentation references to overlay filenames (the token appears only as part of a path literal, never as a runtime name). Option (b) changes the gate's contract and should carry its own positive/negative control; option (a) is the smaller blast radius. Coordinate with the workstream branch `2026-09-22-codex-execute-plan-runtime-reconciliation` before touching `scripts/runtime_capabilities.py`.

## Acceptance

- The capabilities suite is green on main with no frozen-region edits required at fix time.
- The scan still catches genuine runtime-name usage in shared skill bodies (negative control: reintroducing a bare `zcode` mention in a test tree flips it RED).
