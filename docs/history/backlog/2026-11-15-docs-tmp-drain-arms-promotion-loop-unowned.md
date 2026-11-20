# Backlog: the docs/tmp drain arms' report-only promotion loop has no owning duty, so the landed retention policy never advances

- **Filed:** 2026-11-15, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture)
- **Status:** covered (docs/history/plans/2026-11-15-docs-tmp-drain-arms-promotion-loop.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** landed report-only machinery whose promotion criterion no duty consumes
- **Skill/step:** the done skill's docs-tmp-sweep paragraph (the drain arms' text home); the maintenance scheduler turn (the census-adjudication duty's candidate home); `scripts/done_sweep_gates_lib.py` `gate_docs_tmp_sweep` posture resolution
- **Dedup probe:** the retention-policy rows are completed (`docs/history/plans/completed/2026-11-01-docs-tmp-retention-redesign.md` and its two sibling origins); the residue-cleanup row `2026-11-02-agent-resource-cleanup-disposition.md` is covered; no open row owns the promotion loop.
- **Cluster:** (none open; single-origin)

## Observed versus expected

Observed: the retention redesign landed three drain arms inside the sweep gate, default report-only, and pinned the promotion path in its assumptions: one docs/tmp census cycle whose would-drain rows are all confirmed correctly priced flips the facts knob (`docs_tmp_drain_arms`: report-only to on). Fourteen days later the knob key is still absent from the facts file (the gate resolves the key and falls back to the report-only default), no text names a duty that reads or adjudicates the sweep's would-drain reports, accumulation continued to an interactive census of roughly 620 entries and 2.7 GB reaching back to September, and the operator-directed prune on 2026-11-15 bypassed the arms entirely (manual deletion, no arm attribution), removing the would-drain data the promotion criterion needed before any cycle adjudicated it. This is corpus lesson #446's no-ops-silently class with the promotion-consumer variant: the traces exist (each done closeout's sweep reports), but no duty consumes them.

Expected: the promotion loop gets an owner: the sweep's would-drain report is surfaced where a standing duty reads it, one read-only census-adjudication duty (the daily scheduler turn is the candidate home) confirms a clean cycle and reports the knob flip for the operator's approval per the admission protocol, and the same duty's census answers which scratch directory families the three arms never reach (the class the emergency interactive session had to inventory by hand).

## Evidence

- Absence probes: `grep -rn docs_tmp_drain_arms .ai-playbook/` and the tip probe `git grep docs_tmp_drain_arms HEAD -- .ai-playbook` both return nothing; the gate resolves the key in `scripts/done_sweep_gates_lib.py` with the module-default fallback.
- The completed plan's promotion assumption names the census criterion but no adjudicating duty; the done skill's sweep paragraph and the maintenance skill carry no census-review step.
- The 2026-11-15 interactive residue census (2.7 GB, files to September) and the same-session operator-directed manual prune that preceded any arm adjudication.

## Suggested correction

Plan-shaped completion of the landed design: pin the census-adjudication duty (read-only; home it in the daily scheduler turn's monitor step), define the clean-cycle record and the operator-gated knob-flip review, and add the uncovered-family census line to the same duty. No new gate; the arms and the posture knob already exist; this supplies the consumer the landed plan's own promotion assumption requires.

Machinery admission: the duty is read-only reporting; witnessed incident is this row's fourteen-day unpromoted posture and the manual bypass; expected catch: every daily turn once wired (each sweep report finally read); false-positive cost: one census line per turn; review date 2026-12-15.
