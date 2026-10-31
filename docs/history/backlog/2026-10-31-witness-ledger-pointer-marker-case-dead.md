# Backlog: witness ledger clause-pointer marker is case-dead and its new pin launders it

Driving force: code-quality
Created: 2026-10-31 (hard-mode-clause-pointer-residuals Task 1 intermediate review, finding 1)
Cluster: docs/history/backlog/2026-10-31-clause-pointer-residual-under-routing-families.md
Cluster: docs/history/backlog/2026-10-31-clause-pointer-r2-residual-improvements.md

The `SKILL_CLAUSE_POINTERS` row `("witness ledger", ...)` in `scripts/validate_review_staging.py` matches 0 of the ~1456 real emit-site messages: emissions use capital-W forms ("### Witness ledger", "Witness ledger: N/A", "Metadata declares 'Witness ledger: N/A ...'"), so the row's mapping never fires on a real emission, while Task 1's new selftest `pointer_pins` entry pins the mapping via a synthetic lowercase probe - pinning a mapping that never fires. Of those shapes, only the declaration-contradiction message ("Metadata declares 'Witness ledger: N/A (no public mutators)' but the doc carries a populated '### Witness ledger' section; the declaration line and the section disagree") routes to the bare skill fallback; the post-fix-round gate message ("post-fix round (...) has neither a populated '### Witness ledger' nor the Metadata 'Witness ledger: N/A ...' empty shape") already routes via its own `post-fix round` marker to the same section (Synthesis-time hard gates), so re-casing this marker must keep it ordered after `post-fix round` (or otherwise scoped) so the gate message keeps its own pointer.

Fix: correct the marker case to the real emission prefix and re-derive its selftest probe from the emit site rather than a synthetic bare marker.

Source: 2026-10-31 interactive exec intermediate review of validate_review_staging.py (capture-all emit-site corpus simulation).
