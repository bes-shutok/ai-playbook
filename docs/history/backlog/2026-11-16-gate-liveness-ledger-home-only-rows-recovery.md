# Gate-liveness ledger home copy carried two 2026-10-06 rows the repository twin lacked

- **Filed:** 2026-11-16, recovery-before-reconcile leg of the runtime-scripts-home-reconcile-follow-up EXEC-PROMPTS entry (the deployed-home reconcile pass; origin row `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md`, deleted covered in the same landing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Driving force:** records-provenance
- **Cluster:** docs/history/backlog/2026-10-21-sync-runtime-scripts-prefixed-manifest-lines.md (shared deployed-home maintenance surface; this row is the residue reconciliation's recovery leg)
- **Dedup probe:** searched open backlog filenames and bodies for "gate liveness", "ledger rows", "home-only"; nearest hits are the 2026-10-23 ledger-clobber investigation (stale-snapshot rewrite dropped a different row's witness, resolved) and the origin row itself; no open row covers these two rows.

## Observed versus expected

Observed (2026-11-16, pre-reconcile diff of `~/.ai-playbook/scripts/gate_liveness_ledger.json` against the repository twin `scripts/gate_liveness_ledger.json`): the home copy carried two incident rows dated 2026-10-06 that exist in no form in the repository twin (row-set diff over every `note`+`date`+`evidence` triple):

```jsonl
{"kind": "incident", "date": "2026-10-06", "evidence": "5bb878fe", "time_lost_minutes": null, "note": "New-file path absent at merge base made an equivalent serialization replacement look like a removal-only regression hunk."}
{"kind": "incident", "date": "2026-10-06", "evidence": "scripts/dirt_regression_gate.py", "time_lost_minutes": null, "note": "Valid review fix in a file introduced on the feature branch was classified as a regression because the merge-base blob had no lines."}
```

Expected: no witness row is lost to a deployment-home divergence; the rows' content survives the reconcile in a records surface, not only in the deleted home copy.

## Work needed

Route the two rows back into the live ledger's corpus (or their lesson-equivalent home in `docs/maintenance/development_lessons.md`) through the ledger's own writer contract, then close this row with a receipt naming where each row landed; do NOT hand-append into `scripts/gate_liveness_ledger.json` (the save-ledger freshness arm owns the writer contract; a hand append would be the unowned-edit class). The home copy itself was deleted by the reconcile in the same landing; this row is the recovered content's durable home until the routing lands.

## Sibling adjudication (recorded, no row)

The reconcile diff found no other live home-only delta worth recovery: `skill_text_budget_caps.json`'s home-only lines were the STALE pre-2026-11-10 cap values (the repository twin carries the 2026-11-10 lowering pass's metadata and lowered caps; repository side authoritative and newer), `reconcile_post_landing.py`, `review_record_selection.py`, `quota_governor.py`, and `quota_pressure_stats.py` were byte-identical to their twins (the 2026-10-18 divergences healed by later conversions), and `sync-mcp-credentials.sh` gained its repository twin in the same landing rather than retiring.
