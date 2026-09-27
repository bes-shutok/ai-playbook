# Release privacy gate: result-only scanning follow-through

- **Filed:** 2026-09-27
- **Origin:** self-serving; operator directive 2026-09-27 during the first release run (per-original-commit scanning called out as unneeded work; "only scan the result on the worktree and fix it right there")
- **Status:** open
- **Priority:** low

## Context

The release privacy gate (`scripts/release-rewrite.sh`) originally scanned every
original publish-delta commit, which made any historically dirty pile unpublishable:
a blob added and later cleaned inside the pile kept failing the gate forever, and no
tip fix could ever clear it. The 2026-09-27 release run aborted on exactly that
(24 of 252 commits carried hits, mostly placeholder fixtures and pattern-quoting
sources). The gate now scans the published RESULT once: the rewritten tip tree,
materialized into the hygiene root after the tree-identity gate, plus the groups
file carrying the authored messages. This landed in-place in
`scripts/release-rewrite.sh` with selftest updates in
`scripts/test_release_skill_selftest.py` (three dirt-never-published cases flipped
from abort to proceed; the materialization-failure case repointed from
`git show` to `git archive`).

## Known boundary this item tracks

1. **Intermediate squash-commit trees are not privacy-scanned.** Only the final
   result is. A blob present in a group-end tree but absent from the final tree is
   published inside that intermediate squash commit unscanned. Document the
   boundary in the release skill's contract wording and consider an optional
   per-group scan arm if it ever matters.
2. **Exclusion-list growth policy.** The scan now excludes 13 named pattern-quoting
   sources (detector implementations carrying the deny patterns themselves, their
   detection fixtures, and archived records quoting sweep commands or placeholder
   home paths). Consider a marker-based or directory-level convention before the
   list grows further, so each new exclusion stays a deliberate decision.
3. **SKILL.md wording pin.** Pin the result-only semantics in the release skill
   contract text ("scans the published result, not every original commit") so a
   future edit cannot silently reintroduce per-commit scanning.

## Acceptance

A small plan covering the three items above; the in-place gate change and selftest
updates are already landed and are not re-done by the plan.
