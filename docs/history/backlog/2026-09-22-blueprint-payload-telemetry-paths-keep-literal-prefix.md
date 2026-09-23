# Backlog: blueprint payload telemetry paths keep their pinned literal-path prefix

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-22
Origin: docs/plans/2026-09-22-p37-context-budget-probes-and-runtime-state.md Task 3 (narrowed remainder of backlog origin 2026-09-20-context-budget-telemetry-tmp-dir-substitution.md)

## Problem

The execute-plan Telemetry substitution rule now scopes `{tmp_dir}` substitution to every telemetry path that policy names, but it explicitly excepts the two maintenance blueprints' payload telemetry paths: `docs/tmp/execute-plan/<plan-slug>/context.jsonl` and `docs/tmp/authoring/<plan-slug>/context.jsonl` (payload text in `agents/skills/maintenance/prompt-templates.md`). Those keep their pinned literal-path rationale: child payloads are self-contained and cannot resolve user-facts keys, and the pins suite freezes each payload body's placeholder set, so a `{tmp_dir}`-style placeholder cannot enter the payload.

## Expected

This is an accepted residual, not a defect. If a future facts override ever requires substituting these payload paths, the change must edit the payload text and its freeze-note pins in the same edit (`pin "authoring blueprint checkpoint duty"` and `pin "execution blueprint checkpoint duty"` in `scripts/check_maintenance_pins.sh`), so the pinned literal never silently diverges from the payload it freezes.

## Environment context

Playbook skills repo; recorded while executing P37 Task 3 on branch 2026-09-22-p37-context-budget-probes-and-runtime-state, 2026-09-22.
