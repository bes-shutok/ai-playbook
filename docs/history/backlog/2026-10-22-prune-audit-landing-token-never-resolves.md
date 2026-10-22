# Backlog: the prune audit's ledger witness class cannot resolve the log's own standard receipt token

- **Filed:** 2026-10-22, learn+investigate pass over the evening exec-mode max-3 run
- **Status:** open
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** session-witnessed (exec-run closeout), learn Step 1.9
- **Cluster:** docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md, docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md

## Observed

`scripts/check_prompt_log_origins.py --prune-audit` classifies a removal as ledger-witnessed only when the receipt line's token resolves (`ledger_token_resolves`: a commit sha probe, or a tree-membership probe of the removal commit). The two tracked rolling logs' operative receipt convention for ad-hoc landings is `EXEC-PROMPTS-PRUNE: <slug> -> landing in this commit`, whose token (`landing`) is neither. Result: every conformant ad-hoc landing that prunes its own entry in the landing commit is flagged `REMOVED-WITHOUT-WITNESS` (0 by log ledger) whenever the audit window covers the landing commit - witnessed 2026-10-22 on four same-day landings (three from the evening max-3 run, plus the peer's earlier trio member), all with clean pins/hygiene gates and matching the 14-receipt precedent on main.

## Expected

Either the audit recognizes the in-commit receipt form (the removal commit's own post-image receipt naming the slug witnesses the removal, since the receipt and removal ride the same commit by the Freeze rule's design), or the log's receipt convention changes to a resolvable token form and the two logs' precedent lines are migrated in one pass. The current state makes the audit's fail exit unusable as a closeout gate for ad-hoc runs: it fails on conformant landings, so runs ignore it and a genuinely unwitnessed removal hides in the same noise.

## Suggested fix

Extend `check_prompt_log_origins.py`'s removal classification with one arm: when the removal commit's own post-image adds a ledger receipt line naming the removed slug with token `landing`, classify `PRUNE-OK (in-commit receipt)`. The RECEIPT-WITHOUT-REMOVAL warning class (pre-registered 2027-01-18) already covers the inverse abuse (receipt added, nothing removed), so the widening keeps an abuse guard. Machine admission: this is a checker-widening on a witnessed false-positive class (four same-day witnesses), priced against the existing pre-registered warning class.
