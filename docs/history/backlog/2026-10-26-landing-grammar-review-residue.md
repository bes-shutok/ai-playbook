# Landing-grammar review residue

- **Cluster:** landing-subject-grammar-end-to-end
- **Origin:** Phase 3 review panel over the landing branch (two lenses, blocking-clean; valid unfixed findings captured per the backlog-exit rule)
- **Class:** code-quality

## Members

1. **Guard prose drifts behind the widened constant.** The prose block above `LANDING_CLAIM_PREFIXES` in `scripts/reverse_squash_guard.py` (~lines 1466-1474) frames itself as the grammar's "single definition" and still enumerates only `plans: land ` and `done: execute ` while the constant below carries four prefixes. One-sentence prose refresh beside the next guard touch; the Task 1 intermediate review and both Phase 3 lenses recorded it.
2. **land-worktree reports a modeled-fail remedy for a partial guard deploy.** When the guard copy exists but fails to import (a partial deployment, e.g. missing `plan_shape.py`), the wired check-landing gate exits 1 through an uncaught Python exception and the helper prints the "rebase onto the current base tip" remedy instead of a deployment-gap message. Pre-existing wiring shape, adjacent to (not caused by) the compose-time notice; the `land` mode note-line path handles the same class correctly.

## Non-findings (recorded, no action)

- Subject-grain divergence (notice reads the first line, sweep anchor reads `%s`): one-directional, warning-only, zero cost per the machinery admission; the plan's edge-case note covers it.
- The notice's Python subprocess widens the lock-held window slightly: accepted under the warning-only posture; review rides the next `land_squash.sh` touch.
