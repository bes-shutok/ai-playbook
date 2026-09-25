# Backlog: periodic deferred-corpus re-triage lane in maintenance

Status: open
Workflow: backlog (promote via `plans` skill when scheduled)
Source: owner directive 2026-09-26, after the manual deferred-corpus direction triage ("make maintenance do the same from time to time")
Priority: medium
Created: 2026-09-26

## Problem

The 2026-09-26 direction triage had to be run by hand across `docs/plans/deferred/` and `docs/history/backlog/deferred/`: 6 plans and 54 backlog items routed to the rejected archives, 4 done-record strays with committed conflict markers removed, 33 items kept. Nothing in the maintenance loop repeats that pass, so the deferred corpora regrow stale, direction-contradicting, and superseded entries silently. The 2026-09-22 "defer 72 formal items" sweep alone committed four conflict-marker strays (f8fbd660) that survived until this sweep found them.

## Fix direction (mirror the friction-audit lane; no second parallel mechanism)

1. Lane state: a re-triage record beside the friction-audit record under the resolved `friction_audit_dir` state file, carrying `next_due` and a corpus digest; facts key `deferred_retriage_cadence_days`, fallback 30. The Step 1 consult reads due exactly like the friction-audit consult.
2. Dispatch: when due and lanes allow, dispatch at most one re-triage child under the authoring-lane discipline (claim check, `children[]` entry, park on quota pressure, idle preferred, sub-agent and token caps recorded in the state); an in-turn sweep is allowed when the corpus is small.
3. Rubric home: the child reads the "2026-09-26 direction triage" section of `docs/plans/deferred/README.md` as its rubric SOT; the skill pins the pointer, never a copy, so rubric edits need no skill change.
4. Classes: profile-aware per guidelines rule 68. Review-tooling correctness, personal-fork protection, real public-hygiene leaks, witnessed live defects, simplification work, and live-surface prose polish are never rejected. Reject classes: archived-record-only edits, unwitnessed gate/validator/hardening additions, superseded or already-covered targets, and withdrawn harness-security hardening.
5. Sweep mechanics (from the witnessed sweep): rejected = git mv into `docs/history/backlog/rejected/` (plans: `docs/plans/rejected/`) plus the one header status-line rewrite (`Status: rejected (<date>; <reason>)`) and registry rows with audit notes; registry identity collisions take the MMDD suffix plus directory tag; a done-record stray (a deferred copy whose registry row or completed twin records done) is removed with a note appended to the authoritative row.
6. Gates, in order, before commit: `scripts/check_backlog_claimed.py` over every candidate in one invocation (a claimed item is skip-and-annotate, never moved), then the doc-registry validator, the check-writes gate over changed paths, the origins gate, and the added-lines em-dash scan.
7. Authorization: unattended rejection acts only under a standing owner directive recorded in the deferred README section (the current one names the reject classes); without a live standing directive the child writes a proposal report instead and the lane records `awaiting-authorization` instead of moving anything.
8. Output: counts (moved, strays removed, kept, skipped-claimed) land in `decision_reason`; `next_due` advances like the audit lane's; kept items are not re-judged before the next due date (no churn).

## Acceptance

- The maintenance survey consults the re-triage state; a due lane dispatches or performs the sweep under the caps; the rubric is read from the deferred README pointer.
- A dry run over the current deferred corpus reproduces the latest triage verdicts: the items the triage kept parked stay, nothing already in `rejected/` is re-touched, promoted items are not re-judged, and a claimed item (if one appears) is skipped with the claiming plan recorded.
- Every sweep commit passes the four gates above, and the lane's `next_due` write advances.
