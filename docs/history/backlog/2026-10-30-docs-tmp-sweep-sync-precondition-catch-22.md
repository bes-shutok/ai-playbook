# docs/tmp sweep's only general file-deletion arm can never fire over docs/tmp

- **Filed:** 2026-10-30, operator-directed docs/tmp accumulation survey
- **Status:** covered (docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md)
- **Workflow:** backlog
- **Priority:** moderate
- **Cluster:** docs/history/backlog/2026-10-30-done-session-cross-repo-marker-immortality.md; docs/history/backlog/2026-10-30-execute-plan-proof-family-retention-unbounded.md; docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md; docs/history/backlog/2026-10-30-remaining-run-era-tmp-dirs-drain.md; docs/history/backlog/2026-10-29-done-gate-report-retention.md; docs/history/backlog/2026-10-31-gate-removal-stranded-drained-migration-destination.md (same surface: docs/tmp drain of done-session artifacts vs downstream consumers; distinct defect class: stranded gate-removal teardown accounting)
- **Origin class:** operator-directed cleanup request; accumulation measured and root-caused in a repository survey
- **Class:** fix-class (a retention-policy decision inside the existing sweep gate; no new machinery)
- **Driving force:** simplicity
- **Surface:** `scripts/done_sweep_gates_lib.py` `gate_docs_tmp_sweep` and `_docs_sync_state`; `agents/skills/done/SKILL.md` docs-tmp-sweep paragraph; the docs-branch runner's archive-root exclusion
- **Environment context:** this repository's landing sweep; measured 2026-10-30T15:33Z
- **Dedup probe:** searched open backlog rows and both rolling logs for tmp sweep retention, docs-branch sync precondition, and never-synced scratch; `2026-10-09-done-recursive-tmp-sweep-safety.md` (covered) owns the sweep's deletion-safety contract and did not revisit the sync precondition; `2026-10-29-done-gate-report-retention.md` owns the opposite direction (the sweep pruning reports a retained manifest still cites) and its PLAN entry is frozen for authoring; none owns the dead file-deletion arm or the never-synced catch-22.

## Problem

The landing sweep's docs-tmp-sweep gate has exactly one deletion arm for scratch files at the `docs/tmp/` top level: a `.py`, `.log.md`, or date-prefixed `.md` file whose docs-branch sync state is `synced` and whose mtime sits outside the session window. The gate reads that sync state with `_docs_sync_state`, an `ls-tree` against `refs/heads/docs`. The docs-branch runner excludes `docs/tmp/` from its archive roots by design, so the branch holds zero docs/tmp paths. Every top-level scratch file is therefore `never-synced`, and the gate keeps each one with the printed reason "never synced to the docs branch; removal would be permanent". The only file class the sweep can positively attribute is dead code over its own target: no top-level file has been deletable through this arm since the gate landed (fe61c8471 introduced both the gate and the sync precondition).

Measured consequence (2026-10-30T15:33Z): 343 top-level files, of which 204 are `.md` (202 of those not date-prefixed, so outside the arm's shape even without the sync precondition), 74 `.json`, 24 `.lock`, 23 `.txt`, 8 `.patch`; none eligible. Exactly 2 files pass the shape test (the date-prefixed `.draft.md` files from 2026-10-18 and 2026-10-27) and both are kept by the sync arm alone. Directories outside the sweep's two named classes fall through to "unclear ownership or active work" and are likewise kept forever (for example `tool-runtime-stats/`, 19M).

## Evidence

- `scripts/done_sweep_gates_lib.py`, `gate_docs_tmp_sweep`: the synced-outside-window arm is the only general file deletion path; the `never-synced` state appends "removal would be permanent" and keeps the file.
- `git ls-tree -r --name-only refs/heads/docs -- docs/tmp` returns 0 paths (re-derived 2026-10-30T15:33Z).
- `agents/skills/done/SKILL.md`, docs-tmp-sweep paragraph: "The docs-branch runner excludes `{tmp_dir}` from its archive roots and leaves local tmp bytes untouched."
- Introduction archaeology: `git log -S "never synced" -- scripts/done_sweep_gates_lib.py` lands on fe61c8471, the same commit that introduced `gate_docs_tmp_sweep`.

## Suggested investigation

Decide the deletion policy for never-synced scratch bytes: whether the sweep gains an attributable deletion class that does not depend on docs-branch sync (attribution via the session-window markers, the migrate manifests' verified records, or an explicit age bound carrying the fail-closed protections the covered recursive-tmp-sweep-safety plan fixed), or whether the arm stays sync-gated and the catch-22 is accepted with the arm's docs/tmp scope documented as intentionally inert. Any widening must reconcile with the opposite-direction guard in `2026-10-29-done-gate-report-retention.md`: the widening must not re-open pruning bytes a retained manifest still cites.
