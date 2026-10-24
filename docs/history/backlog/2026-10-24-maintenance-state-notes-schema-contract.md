# Backlog: maintenance scheduler state notes schema and carry-forward contract

- **Filed:** 2026-10-24, plan-review certification residual `consistency#state-notes-existence`
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review residual
- **Class:** fix-class
- **Driving force:** code-quality
- **Skill/step:** `agents/skills/maintenance/state-file.md`, schema-v4 example and Step 6 carry-forward
- **Cluster:** docs/history/plans/2026-10-24-scheduler-state-decision-shape-drift.md

## Problem

The scheduler-state plan refers to an existing top-level `notes` array and requires legacy decision strings to be preserved there, but the canonical schema-v4 example omits `notes`. That leaves executors uncertain whether the field is part of the contract and what entry shape Step 6 must preserve.

## Expected

Declare the `notes` field in the canonical schema-v4 example and define the entry shape and Step 6 carry-forward behavior consistently with the live state and the authorized repair contract.
