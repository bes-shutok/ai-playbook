# Backlog: Layer 2 laptop how-to vs ops runbook (one recipe home)

Status: open
Priority: medium
Workflow: backlog

## Skill and step

- Skill: `doc-hierarchy-upkeep`
- Step: Edit Layer 2 in the same change set (single SOT / link instead of duplicate)
- Also: `doc-hierarchy` company-decisions Layer 2 placement; review/plan gates that touch ops + local-dev docs

## Observed behavior

A disposable laptop enablement recipe (Compose, JAR flags, smoke, local escape hatches) was authored under `docs/architecture/operational-guides.md` while `docs/maintenance/local-development.md` also listed the same flags and pointed "Full checklist" at ops. Two Layer 2 homes for one bash recipe; flags drifted when only one copy gained a local escape hatch.

Witness: a migration-complete company service briefly hosted a dual Local enablement recipe; fixed by collapsing the recipe into `local-development.md` and leaving ops with the production release check plus a pointer.

## Expected behavior

- Disposable Compose/JAR recipes, smoke curls, and local escape hatches: **only** `docs/maintenance/local-development.md` (or the service equivalent).
- Production/UAT release checks, SRE ticket owners, runtime tunables: **only** `docs/architecture/operational-guides.md`.
- Architecture may keep a one-line pointer to the local guide; it must not host a second copy of the command block.
- Root `README.md` stays a short pointer to local-development (existing best-practices rule).

## Instruction updates already applied

- `doc-hierarchy-upkeep` SKILL.md: laptop vs ops bullet + checklist item
- `doc-hierarchy/company-decisions.md`: Layer 2 placement bullet + PR checklist row
- Incident service repo: project-guidelines Documentation Hierarchy item 4; Layer 2 best-practices claim; project `development_lessons` witness

## Remaining work (this backlog)

1. ~~**Review / plan gate:**~~ Done in the same change set: `review-plan` Step 1 plan-closure matrix bullet; `doc-hierarchy-upkeep` laptop-vs-ops checklist; company-decisions PR checklist row.
2. **Optional verify hook:** if a second dual-recipe incident appears in another service repo, add a `rg`-based assertion under the doc-hierarchy verify family (compare fenced `java -jar` / `docker compose` blocks that appear in both files) rather than inventing per-repo scripts.
3. **Backlog authors:** when a completed-history item asks to "document local enablement in ops guides," rewrite the acceptance to "local-development SOT + ops pointer" before promoting to a plan.

## Reproduction evidence

1. Open the pre-fix `operational-guides.md` Local enablement recipe section and the `local-development.md` optional workers step.
2. Observe the same JAR flag block in both files with inverted "Full checklist" cross-links.
3. Post-fix: recipe only in `local-development.md`; ops has a Local disposable enablement pointer heading.
