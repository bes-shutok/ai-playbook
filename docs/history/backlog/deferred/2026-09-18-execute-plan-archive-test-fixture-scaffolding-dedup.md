# Backlog: archive test fixture scaffolding duplicated across four test classes

Status: closed (2026-10-01 triage, operator adjudication "follow row contracts"; completed by other work, completion receipt below)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; test-fixture dedup (code-quality polish, no witnessed failure). Revive on the touched test files are next edited under a live plan, or a project-priority-profile change.)
Workflow: backlog
Date: 2026-09-18
Class: execute-plan driver test suite, fixture scaffolding duplication

## Problem

`ArchiveGatePreArchiveTest`, `TerminalFinalStageTest`, `ArchiveLocationTest`,
and `TerminalResumeTest` in `scripts/test_execute_plan_runtime.py` each carry
their own copy of the same scaffolding: the TOML-fence facts writer, the
plans/completed directory creation, the manifest seed with the same two task
rows, the sidecar writer, and the conforming `archive_gate` seeding shape.
Roughly 60-80 duplicated lines; a change to the gate receipt shape or the
facts format must be repeated four times.

## Location

`scripts/test_execute_plan_runtime.py`, the four archive/terminal test
classes (setUp, write_facts, write_sidecar, driver helpers).

## Suggested direction

Extract a shared mixin or module-level helper (for example a
`ArchiveGateFixtureBase` next to the existing helpers) owning the facts
writer, the seeded manifest, the sidecar writer, and the gate seeding shape;
the classes keep only their differing plan paths and expectations. Keep the
hermetic git setup only in the class that proves real ancestry.

## Severity and source

Low; staging doc
`docs/reviews/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety-code-review-r1.md`,
round 1, finding D-4.

## Why not fixed now

Pure test-structure refactor with regression risk across four green classes;
deferred by the round 1 address-pass disposition.

## Completion receipt (2026-10-01)

The item's own proposed fix shape exists on the current tree: scripts/test_execute_plan_runtime.py defines ArchiveGateFixtureBase and all four classes named here inherit it (ArchiveGatePreArchiveTest at line 13493, TerminalFinalStageTest at line 14312, ArchiveLocationTest at line 14550, TerminalResumeTest at line 14595). The scaffolding duplication this row recorded is gone.
