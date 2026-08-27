# External skill and agent-instruction sources

Catalog of upstream repositories to consult when extending, vendoring, or refreshing skills in `agents/skills/`. This file is the **single source of truth** for external catalogs; individual vendored skills record `metadata.upstream` in `SKILL.md`.

## When to use this catalog

- Before importing a new skill from GitHub
- During periodic upstream refresh (compare local copy vs upstream default branch)
- When looking for patterns to improve first-party skills (`plans`, `execute-plan`, `doing-code-review`, etc.)
- When evaluating overlap: prefer merge into existing skills or references over duplicate directories

## Vendoring checklist (all sources)

1. Read upstream `LICENSE`; copy verbatim into vendored skill `LICENSE.txt` (see `how-to-write-skills/SKILL.md`, lesson #182 in `development_lessons.md`).
2. Set `metadata.upstream` on each vendored skill; drop vendor-specific folders (for example Codex `agents/openai.yaml`).
3. Adapt paths to doc-hierarchy and facts-key conventions; run `public_hygiene_scan_script` before commit.
4. Document the import in `agent-runtime-layout.md` (vendored subsection or this catalog status column).
5. Add or update the source row in `skill-upstream-catalog.md` when importing or refreshing from an external catalog.
6. When **merging patterns** (no new vendored skill directory), add a row to **Merged pattern index** below: upstream file URL, local destination, and one-line note. Keep repo-level rows in **Source catalog**; do not duplicate full URLs only in lesson text or skill bodies without a catalog row.

## Source catalog

| Source | Type | Status in this repo | Local overlap / notes |
|--------|------|---------------------|------------------------|
| [mattpocock/skills](https://github.com/mattpocock/skills) | Skill registry (`skills/productivity/`, `skills/engineering/`) | **Partially vendored** | Imported: `grilling`, `handoff`, `domain-modeling`, `grill-with-docs`. Merged: `writing-great-skills` → `how-to-write-skills/references/`. Not imported: `grill-me` (thin wrapper over `grilling`), `teach` (HTML lesson workspace), `ask-matt`, Matt-specific `setup-matt-pocock-skills`, most engineering skills (overlap with first-party review/plan/TDD stack). Re-sync: sparse-clone skill folders; refresh [upstream LICENSE](https://github.com/mattpocock/skills/blob/main/LICENSE). Local deviation: `grill-with-docs` drops upstream `disable-model-invocation: true` because the `plans` Phase 1 confidence gate invokes it agent-side; preserve the removal on re-sync. |
| [DenisSergeevitch/agents-best-practices](https://github.com/DenisSergeevitch/agents-best-practices) | Harness design reference | **Vendored** | `agents/skills/agents-best-practices/` (`metadata.upstream` set); see `agent-runtime-layout.md`. |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | Cursor rule + Claude guidelines ([karpathy-guidelines.mdc](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/.cursor/rules/karpathy-guidelines.mdc)) | **Reference only** | Principles: think before coding, simplicity first, surgical changes, goal-driven execution. Overlaps `docs/AGENTS.md` coding discipline and `explain-simply-not-simpler`; do not vendor as a skill. Consider borrowing phrasing into user rules when refreshing AGENTS.md, not duplicating as `agents/skills/`. |
| [umputun/cc-thingz](https://github.com/umputun/cc-thingz) (`plugins/`) | Claude Code plugin marketplace (skills, commands, hooks) | **Reference only** (patterns merged) | Plugins: `brainstorm`, `planning`, `review`, `release-tools`, `thinking-tools`, `skill-eval`, `workflow`. Overlaps: `plans` / `execute-plan` (`planning`, `workflow`), `doing-code-review` (`review`), `how-to-write-skills` + `agents-best-practices` evals (`skill-eval`). **Severity:** `plugins/review/` has no formal tiers (uses approve/comment/request-changes); **CRITICAL/MAJOR/MINOR** rules merged from `plugins/planning/skills/exec/references/prompts/review.md` into `review-agents/severity-calibration.md`. PR review plugin useful for discussion-history and scope-creep workflow, not severity taxonomy. |
| [umputun/ralphex](https://github.com/umputun/ralphex) | CLI harness (extended Ralph loop for plan execution) | **Reference only** | Autonomous plan runner; overlaps `execute-plan`, `review-loop`, `done`. Use for harness/eval ideas and `.ralphex/progress/` log analysis (see `learn` Step 1.5), not as a vendored skill. |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (`skills/`) | YAGNI / minimal-solution agent modes + complexity review | **Reference only** (patterns merged) | Core persistent mode overlaps `docs/AGENTS.md` §57 and `coding_guidelines.md` **#28** (minimal solution ladder). Review tags and one-line output merged into `review-agents/simplification.md`. Not imported: `ponytail-gain` (benchmark marketing), `ponytail-help` (plugin install), plugin lifecycle hooks, repo-wide `ponytail-audit`, `ponytail-debt` ledger (optional future skill). Deep links: **Merged pattern index**. Re-sync: `git clone --depth 1 https://github.com/DietrichGebert/ponytail /tmp/ponytail && ls /tmp/ponytail/skills/`. |
| [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) | ADHD-friendly output-style skill | **Vendored** | `agents/skills/i-have-adhd/` (`metadata.upstream` set). Opt-in via `/i-have-adhd` (Claude: `disable-model-invocation: true`). Host plugins also installed for Claude Code, Codex, and Antigravity when those CLIs are present. Re-sync: `git clone --depth 1 https://github.com/ayghri/i-have-adhd /tmp/i-have-adhd && rsync -a --delete --exclude agents /tmp/i-have-adhd/skills/i-have-adhd/ agents/skills/i-have-adhd/` then refresh `LICENSE.txt` from upstream `LICENSE`. |

## Merged pattern index

Deep links for patterns absorbed into first-party skills or guidelines (not standalone vendored directories). Refresh these rows when re-diffing upstream.

| Upstream URL | Local destination | Notes |
|--------------|-------------------|-------|
| [ponytail/skills/ponytail/SKILL.md](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md) | `coding_guidelines.md` **#28**; `docs/AGENTS.md` Simplicity bullet | Minimal solution ladder; not imported as persistent session mode |
| [ponytail/skills/ponytail-review/SKILL.md](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-review/SKILL.md) | `review-agents/simplification.md` | Tag vocabulary (`delete:`, `stdlib:`, `native:`, `yagni:`, `shrink:`), one-line output, `net:` rollup |
| [cc-thingz/.../planning/.../review.md](https://github.com/umputun/cc-thingz/blob/master/plugins/planning/skills/exec/references/prompts/review.md) | `review-agents/severity-calibration.md` | CRITICAL/MAJOR/MINOR taxonomy; default missing tag → MINOR (mapped to Low) |
| [cc-thingz/.../planning/.../codex-review.md](https://github.com/umputun/cc-thingz/blob/master/plugins/planning/skills/exec/references/prompts/codex-review.md) | `review-agents/severity-calibration.md` | Same severity tags as review fanout playbook |
| [cc-thingz/plugins/review/skills/pr/SKILL.md](https://github.com/umputun/cc-thingz/blob/master/plugins/review/skills/pr/SKILL.md) | *(reference only)* | Discussion history, scope creep, quick vs full review workflow; no formal severity tiers |
| [cc-thingz/plugins/review/skills/git-review/SKILL.md](https://github.com/umputun/cc-thingz/blob/master/plugins/review/skills/git-review/SKILL.md) | *(reference only)* | Interactive diff annotation loop; different model from `doing-code-review` staging |
| [mattpocock/skills/.../writing-great-skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-great-skills) | `how-to-write-skills/references/skill-design-*.md` | Merged into references; directory removed |
| [karpathy-guidelines.mdc](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/.cursor/rules/karpathy-guidelines.mdc) | `docs/AGENTS.md` coding discipline (reference) | Principles only; not vendored |

**Not indexed here:** vendored skills with `metadata.upstream` in their own `SKILL.md` (see **Partially vendored** / **Vendored** rows above). Add a merged-pattern row when borrowing from a new upstream **file** even if the repo row already exists.

## Last upstream check

| Date | Scope | Result |
|------|-------|--------|
| 2026-07-23 | Added [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) | Vendored `agents/skills/i-have-adhd/`; host plugins for Claude/Codex/agy. |
| 2026-07-17 | Vendored + reference rows in **Source catalog** | No content refresh needed. `agents-best-practices` still `1.2.0` (refs identical; local Integration Points only). Matt Pocock vendored skills diverge only by playbook adaptations. `writing-great-skills` glossary/principles in sync (upstream layout is now `SKILL.md` + `GLOSSARY.md`). Ponytail tags and cc-thingz CRITICAL/MAJOR/MINOR unchanged. Skip new Matt `grill-me` (thin wrapper over `grilling`). |

## Suggested refresh cadence

| Priority | Action |
|----------|--------|
| After vendoring | Pin `metadata.upstream` URL; note import date in commit message |
| Quarterly (or before large skill work) | Check default branch of **Partially vendored** and **Reference** rows for new skills or breaking edits |
| On user request | Diff a specific upstream skill folder against local copy before merge |

## Quick upstream peek commands

```bash
# List mattpocock productivity + engineering skill names
git clone --depth 1 --filter=blob:none --sparse https://github.com/mattpocock/skills /tmp/mattpocock-skills
cd /tmp/mattpocock-skills && git sparse-checkout set skills/productivity skills/engineering
find skills -name SKILL.md | sort

# List cc-thingz plugins
git clone --depth 1 https://github.com/umputun/cc-thingz /tmp/cc-thingz
ls /tmp/cc-thingz/plugins/

# List ponytail skills
git clone --depth 1 https://github.com/DietrichGebert/ponytail /tmp/ponytail
ls /tmp/ponytail/skills/
```

## Related files

- `agent-runtime-layout.md`: runtime mapping and vendored skill subsections
- `agents/skills/how-to-write-skills/SKILL.md`: LICENSE, facts keys, tool-agnostic authoring
- `development_lessons.md` #182: vendoring license and doc-hierarchy alignment
- `development_lessons.md` #183: merge upstream patterns before vendoring duplicate skills; record deep links in **Merged pattern index**
