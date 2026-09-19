# Backlog: single-source the allowlist glob surface in scan-public-hygiene.sh

Status: open
Severity: Low
Origin: review records contract code review r1 (F9, correctness-completeness + design-simplicity; accepted for backlog deferral); staging doc docs/reviews/2026-09-16-review-records-contract-code-review-r1.md; capture hygiene: scan-public-hygiene --files pass (2026-09-19)
Date: 2026-09-19

The standard allowlist globs are hand-maintained on three surfaces inside `scripts/scan-public-hygiene.sh`: the `GLOB_EXCLUDES` array fed to rg, the inline glob list in `changed_files_in_scope`, and the case-glob branches in `_path_is_excluded`. A glob added to one surface and missed on the others silently diverges the modes: the full-tree scan would exclude a path that the changed-from scan still scans (or the reverse), and the explicit-paths mode would follow whichever copy it inherited.

Fix shape: one declared glob list and one shared matcher consumed by all three surfaces (rg args built from the list, changed-from filtering and the explicit-paths predicate calling the same matcher), with the scanner selftest extended to assert the surfaces agree.

Trigger: the next allowlist glob addition, or the next scanner change touching any of the three surfaces. Known live instance for that refactor (r3 overflow risk F5): the root-level `LICENSE.txt` shape (and absolute spellings of it) is scanned in the explicit-paths mode while allowlisted on the other two surfaces; the asymmetry scans in the fail-closed direction, so it is recorded here rather than fixed now.
