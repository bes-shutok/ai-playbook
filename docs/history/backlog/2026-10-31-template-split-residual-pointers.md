# Backlog: template-split residual pointers and counts

Driving force: code-quality. Residuals found by the 2026-10-31 claim-procedure-pointer run's Phase 3 panel, all pre-existing (not introduced by that run), recorded so they are not lost:

1. `scripts/machinery_registry.json` entries[0].note still cites the authoring blueprint at `agents/skills/maintenance/prompt-templates.md`; the blueprint lives in `template-authoring.md` since the 2026-10-10 split.
2. `scripts/test_authoring_plans_liveness.py` defines an unused `PROMPT_TEMPLATES` constant pointing at the old file (dead code since the split).
3. `agents/skills/maintenance/scheduling.md` Unblock-dispatch slice names "the unblock template" with no module path in any dispatch slice; the one operative path naming is the scheduled-payload sources sentence in `agents/skills/maintenance/zcode.md`.
4. `agents/skills/maintenance/scheduling.md` authoring-payload sentence says "the two field lines after the block are fill-in spec", but `template-authoring.md` carries three field lines since the 2026-10-29 effort-directive pin.

Remedy shape: one bounded docs/registry session; pin literals re-aimed in the same change where the pins suite freezes any edited sentence.

Cluster: docs/history/backlog/2026-10-31-pre-execution-re-verification-label-mismatch.md
