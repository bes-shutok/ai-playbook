# Backlog: review-agents quality catalog carries MyBatis sections without the portability marker
Cluster: docs/history/backlog/2026-11-01-skill-review-cross-skill-repetition-debt.md; docs/history/backlog/2026-11-01-skill-review-maintenance-stance-stale-cap-wording.md; docs/history/backlog/2026-11-01-skill-review-systematic-debugging-broken-references.md (same-day review family)

- **Filed:** 2026-11-01, weekly skill-review lane run 1 (batch unit: agents/skills/review-agents/)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** audit-lane finding (advisory review suggestion, read-only)
- **Class:** fix-class

## Problem

`agents/skills/review-agents/quality.md` lines 45 and 130 carry MyBatis-specific catalog sections with no `<!-- portability: abstract -->` marker, while the same file's Consumer contract (SKILL.md:32) forbids framework tokens in shared catalogs. The portability checker (`scripts/check_review_agent_portability.py`) passes on the current text, so the gate does not catch these sections - the marker discipline and the checker's detection surface disagree on this shape.

## Expected

Every stack-specific catalog section either carries the portability marker (abstract layer ownership) or lives in a consumer-side overlay; the marker's presence or absence is enforced consistently by the checker.

## Suggested direction

Bounded arms: add the owning-layer marker to the two MyBatis sections, or move them to a doing-code-review overlay; separately extend the portability checker to flag marked-token-bearing sections without the marker (the witnessed false-pass direction), with a collision-pair regression test, under the machinery admission test if the checker change blocks.

## Evidence

- Weekly skill-review run 1 aggregates record, finding 31 (docs/maintenance/skill-review-log.md); agents/skills/review-agents/quality.md:45,130 vs agents/skills/review-agents/SKILL.md:32; scripts/check_review_agent_portability.py exit 0 on current main.
