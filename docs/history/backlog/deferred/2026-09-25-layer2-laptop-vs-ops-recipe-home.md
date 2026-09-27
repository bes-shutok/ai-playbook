# Backlog: Layer 2 laptop how-to vs ops runbook (one recipe home)

Status: deferred (2026-09-27; closed with all edits landed; parked to hold the standing second-dual-recipe-incident trigger record out of the actionable surface)
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
   Witness probe, fixture-validated 2026-09-25 (run under bash at the service-repo root; save as a file or wrap in ( ... ) before running, because the guard exits the calling shell): exit 0 with output lines means recipe lines shared between the column-0 fenced blocks of both files (inspect the lines before building the verify-family assertion); exit 1 means no shared recipe-shaped (java/compose) lines among column-0 fenced blocks (list-indented fences are invisible to it, so confirm fence placement before trusting clean); exit 2 means a target doc is missing or unreadable (the probe witnesses nothing); an unbalanced or mixed-indent fence run can corrupt the capture window and a directory at either path also reports as exit 1, so investigate before trusting clean).

       test -r docs/architecture/operational-guides.md && test -r docs/maintenance/local-development.md || { echo "probe witnesses nothing: a target doc is missing or unreadable"; exit 2; }
       comm -12 <(awk '/^```/{if(b!="")print b; b=""; f=!f; next} f{b=b $0 "\n"} END{if(b!="")print b}' docs/architecture/operational-guides.md | sort -u) <(awk '/^```/{if(b!="")print b; b=""; f=!f; next} f{b=b $0 "\n"} END{if(b!="")print b}' docs/maintenance/local-development.md | sort -u) | grep -E 'java -jar|docker compose'
3. ~~**Backlog authors:**~~ Done, encoded 2026-09-25: backlog authors rewrite stale acceptance per the plans skill origin-acceptance rule (one-recipe standing example), with the review-plan closure matrix bullet as backstop; see plan 2026-09-25-layer2-origin-acceptance-rewrite (archived under docs/plans/completed/ on completion).

Origin lifecycle note: this item's header is closed (the archive-time straggler gate accepts completed, closed, or rejected statuses); it closes to promotion. The maintenance survey enumerates backlog files regardless of status, so this note is the standing no-op basis for authoring dispatch: do not author from this item; item 2's conditional arm remains here as the standing trigger record and triggers only on a second dual-recipe incident witness.

## Reproduction evidence

1. Open the pre-fix `operational-guides.md` Local enablement recipe section and the `local-development.md` optional workers step.
2. Observe the same JAR flag block in both files with inverted "Full checklist" cross-links.
3. Post-fix: recipe only in `local-development.md`; ops has a Local disposable enablement pointer heading.
