# Backlog: the mandated commit-time hygiene scan reads two roots while the release gate scans the whole tree

- **Filed:** 2026-10-26, learn Step 1.8 over the 2026-10-26 release run
- **Status:** covered (docs/history/plans/2026-10-26-hygiene-scanner-default-scope-parity.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-26-release-privacy-gate-failure-report-unactionable.md (same surface: the release privacy gate and the hygiene scanner it wraps)
- **Origin class:** self-serving
- **Class:** fix-class (two scopes of one scanner disagree; default shape: one declared scope, or the commit-time mandate names the publish-scope mode)
- **Driving force:** reliability (primary), operator time (secondary)
- **Skill/step:** `scripts/scan-public-hygiene.sh` (`SCAN_STRICT` roots in full-tree mode versus the explicit `--files` mode the release gate uses); the commit-time mandate in `AGENTS.md` Testing Guidelines and the `done` landing sweep's sensitive-data scan
- **Source reference:** the 2026-10-26 release run: six receipts in `docs/history/certification-seal-landing-diagnostics.md` carrying absolute home paths landed across seven commits dated 2026-10-21 to 2026-10-24, each preceded by a green mandated scan, and were refused only by the release privacy gate; see `docs/maintenance/development_lessons.md` #237
- **Why not fixed now:** widening the default scan changes the scope contract of a gate every commit runs; the false-positive population under `docs/` must be measured first (files that legitimately quote a pattern join the exclusion list), so the change needs a plan
- **Dedup probe:** searched open backlog filenames and Problem text for `SCAN_STRICT`, `hygiene scan`, `scan scope`, `full-tree`; no open row owns the scope gap (`docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md` concerns the runtime copy of the scripts, not the scan's roots)

## Problem

The default (full-tree) mode of `scripts/scan-public-hygiene.sh` reads `SCAN_STRICT=(agents/skills projects)` only, so every tracked file under `docs/`, `scripts/`, and the repository root is outside the mandated pre-commit scan. The release gate (`scripts/release-rewrite.sh`) runs the same scanner in `--files` mode over every blob of the published tree. Dirt landing outside the two roots therefore passes every commit-time scan and surfaces only on release day, where it blocks the whole publish and tempts an exclusion-list fix.

## Evidence

- `scripts/scan-public-hygiene.sh`: `SCAN_STRICT=(agents/skills projects)`; `run_scan "full-tree" "SCAN_STRICT"` is the default mode; the built-in absolute home-directory path check (the macOS and Linux home prefixes, named here by class so this row does not trip it) runs over `rg_paths`, which is the roots in full-tree mode and the argument list in `--files` mode.
- `scripts/release-rewrite.sh` step 10 builds `scan_call_paths` from `git ls-tree -r` of the rewritten tip (every regular-file blob) plus the groups file.
- The 2026-10-26 release: the same scanner reported `PASS` in default mode on the working tree and `FAIL` in `--files` mode over the materialized identical tree, the difference being the six ledger receipts and one archived plan line under `docs/history/`.
- The scanner's exclusion list comment states the policy "real identifiers elsewhere are masked, not excluded", so the gap is a scope gap, not an intended allowance.

## Expected

A file the release gate will refuse is refused, or at least reported, by the mandated commit-time scan. Either the default mode's scan set is the same tracked-file set the release gate scans (minus the shared exclusion list), or the commit-time mandate explicitly runs the publish-scope mode, so the two scopes derive from one declaration.

## Suggested direction

Measure first: run `--files` over the whole tracked tree at the current tip and classify every hit outside the two roots (real identifier to mask, pattern quote to exclude, or stale record). Then choose between widening the default roots (deleting the two-root restriction) and having the commit-time mandate call the publish-scope mode; prefer the one that leaves a single declared scope. Pay growth by deleting the roots restriction or the duplicated mode text.

## Alternatives

- **Keep two scopes and rely on the release gate:** rejected on the witnessed cost; the gap let one leak accumulate for four days and converted a routine release into a two-attempt run with a mid-release hygiene commit (`docs/maintenance/development_lessons.md` #237).
- **Exclude `docs/history/` from the release gate to match the commit scan:** rejected; the leaking receipts were real machine paths in published records, exactly what the gate exists to refuse (`scripts/scan-public-hygiene.sh` exclusion list comment).
- **Add a scheduled full-tree scan as a separate carrier:** rejected as new machinery with no admission case beyond this incident; the smaller arm aligns the existing scopes (no witnessed incident the existing scanner could not catch once scoped).
- **Widen only the home-path check to the full tree, keeping the deny patterns on the two roots:** viable narrower arm; the plan measures whether deny-pattern hits under `docs/` would make the full widening noisy.

## Machinery assessment

No new gate. The change widens or re-declares the scope of an existing gate every commit already runs; the false-positive cost is the exclusion-list growth the measurement step quantifies before the choice is made.
