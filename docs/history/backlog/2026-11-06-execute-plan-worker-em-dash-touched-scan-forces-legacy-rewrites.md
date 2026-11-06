Status: open
Priority: high
Class: fix-class
Origin class: consumer-feedback (company)

# Implement worker satisfies the whole-file em-dash scan by rewriting legacy prose the task never touched

## Problem

A docs-only task edited five existing pages that already carried legacy em dashes on lines the task did not change (27 hits in total, 1 to 12 per page). The worker ran the repo's em-dash scan in its whole-file `touched` mode, saw non-zero exits, and replaced all 27 dashes mechanically so the scan would exit 0. It reported the replacement as a deviation, and two review workers verified the replacements were mechanical, but the plan never foresaw the situation and the choice rode on worker judgment.

The rewrite was unnecessary. The done landing sweep's own em-dash gate already adjudicates this exact case: when the `touched` probe fails on a tracked path, it re-checks that path with `added-lines --base HEAD` and, if no added line carries a dash, passes it as a pre-existing known-violation baseline (`scripts/done_sweep_gates_lib.py`, `gate_em_dash_scan`). The check script's own usage text says `added-lines` exists to gate insertions only. So the landing gate would have passed the untouched legacy dashes, and only the worker-side self-check made them look blocking.

Current text that leaves the gap:

- `agents/skills/execute-plan/subagent-prompts.md`, implement-worker rule 9 ("No silent gate-satisfying rewrites of human-authored prose"): forbids wholesale rewrites and limits gate-driven edits to hunks the run touched, but names no em-dash-specific mode and does not say which scan mode a worker should run to stay inside that limit. A worker that reads "run the em-dash scan before commit" (the user-level cross-project rule, mode unspecified) picks `touched` and then has to choose between violating rule 9 and stopping.
- `agents/skills/plans/validation-authoring-rules.md`, rule 28: already tells plan authors to scope forbidden-pattern sweeps to authored content and to select `added-lines --base REF` for files with known pre-existing hits, but it governs plan Validation Commands only. It does not reach the worker's own pre-return self-check, and a plan with no em-dash validation command (this one) leaves the worker to choose.

## Observed vs expected

Observed: 27 legacy dashes in untouched prose were rewritten across five pages to turn a worker-chosen whole-file scan green; the diff carried unrelated prose edits and reviewers had to confirm each was mechanical.

Expected: a worker whose task edits an existing file runs the em-dash scan in `added-lines --base HEAD -- <edited paths>` mode (insertions only), treats `touched` hits on lines the task did not add as baseline matching the landing gate's own disposition, reports them in the return, and rewrites only dashes in lines it authored.

## Exact location

- `agents/skills/execute-plan/subagent-prompts.md`: implement-worker rule 9 (add the scan-mode clause), or the worker's verification checklist where gate commands are named.
- Optional pointer: `agents/skills/plans/validation-authoring-rules.md` rule 28, one clause saying the same mode choice binds the worker self-check, so plans and workers agree.

## Suggested fix (minimal)

Add one sentence to implement-worker rule 9: for the em-dash gate, scan edited files with `bash scripts/check-no-em-dash.sh added-lines --base HEAD -- <paths>` (and `touched` only for files the task creates); a `touched` hit on a line the task did not add is pre-existing baseline, the same disposition the landing sweep applies, so report it and leave it, never rewrite it to satisfy the scan. No new script.

## Severity and source

Severity: Medium-high; every docs task over legacy pages can trigger unrelated prose churn, and the conflict with rule 9 is resolved differently by each worker.
Source: a company consumer project stack run, docs task boundary, 2026-11-06. Capture hygiene: public hygiene scan and em-dash scan run over this text before filing.

## Why not fixed now

Learn capture only; the fix edits the execute-plan worker prompts, which are reviewed by the skills panel before commit.

## Driving force

reliability

## Dedup probe

Searched open backlog names and bodies for `added-lines`, `em-dash`, `legacy`, `pre-existing`, and `touched`; the nearest rows mention the scan only in unrelated contexts (residual cleanup of backlog rows, plan-gate certification), none covers the worker self-check mode. Verified in the current skill text that rule 9 carries no scan-mode clause and rule 28 is scoped to plan Validation Commands.
