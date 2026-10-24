# Backlog: scheduler-state decision fields drift to string shape and no reader or writer repairs it

- **Filed:** 2026-10-09, during a D-4 authoring carrier turn
- **Status:** covered (docs/history/plans/2026-10-24-scheduler-state-decision-shape-drift.md)
- **Workflow:** backlog
- **Priority:** high
- **Cluster:** agents/skills/maintenance/SKILL.md (State file section — the `decision`/`decision_reason` schema example)

Cluster: docs/history/plans/completed/2026-10-10-contract-single-sourcing.md (the same drift family: copied contracts disagreeing across surfaces; this row is a state-schema instance that stays a separate small plan unless that family's plan budget fits a rider)
- **Origin class:** observed runtime refusal
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/SKILL.md`, State file section; `.ai-playbook/scheduler-state.json`
- **Driving force:** reliability

## Problem

The State file section's schema example pins `decision` and `decision_reason` as objects keyed by lane (`{"execution": ..., "authoring": ...}`). The live scheduler state file carries both as plain strings, and the flattened shape propagated across at least two turns written by different sessions. A reader that performs lane-keyed access on `decision` fails with a `TypeError` on a string, and successive writers preserved the violating shape instead of repairing it, because each turn respected the predecessor's write and appended around it. No reader-tolerance rule and no repair duty exists for these two fields, so one flattening write degrades every later reader until someone happens to restore the object shape.

## Evidence

- `agents/skills/maintenance/SKILL.md`, State file section schema example: `"decision": {"execution": "execute|noop", "authoring": "author|noop"}` and `"decision_reason": {"execution": "<short reason>", "authoring": "<short reason>"}`; the object shape appears only in the JSON example, never as prose, with no tolerance or repair rule.
- `.ai-playbook/scheduler-state.json` read 2026-10-09: `decision` is a plain string (a turn summary) and `decision_reason` is a plain string; both violate the object shape.
- 2026-10-08/09: a session updating the per-lane decision through `decision["execution"]` hit `TypeError: 'str' object does not support item assignment` and fell back to appending `notes[]` entries; the turn-end closeout then replaced the string wholesale with its own summary string rather than restoring the object shape, so the violation propagated one more turn.

## Expected

Pin the two fields' shape explicitly in the State file section prose, not only the JSON example: readers tolerate both shapes (a string-valued `decision` reads as an unspecified-lane decision, never a crash), and any scheduler-turn write that touches `decision` or `decision_reason` restores the object form in the same targeted edit, moving the string content into the matching lane's value or into `notes[]`. The Step 6 full rewrite re-validates the shape on carry-forward. Optionally name the repair in the sanctioned-writer enumeration so the restoring edit has an explicit write-class home.

## Why not fixed now

This row was filed by an ad-hoc analysis turn, not a scheduler turn bound to the maintenance skill's write discipline; repairing the live state file shape outside a turn's sanctioned write classes would itself need a writer-class home, and the skill-text change belongs with the State file section's next edit cycle rather than an unreviewed in-place skill edit. The in-session workaround (append-only notes, shape-tolerant reads) is compliant and was applied.

## Source

- 2026-10-08/09 sessions in this repository (the TypeError witness and the propagated string shape).
