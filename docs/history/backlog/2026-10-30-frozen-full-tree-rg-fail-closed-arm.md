# Fail-closed rg arm for the frozen full-tree/changed hygiene scan modes

Driving force: correctness

The frozen full-tree and changed modes of scripts/scan-public-hygiene.sh pass the active patterns line as a positional rg argument and swallow rg exit > 1, so a dash-led patterns line is silently unapplied to the blocking roots and an invalid regex degrades to pass, while files mode (r3 F4) and the new report scope honor `-e` and fail closed on the same input. Add `-e "$pattern"` plus an rc > 1 fail-closed arm mirroring the files branch, or record the frozen-by-design residual explicitly at the next freeze review. Witness: Phase 3 review r2 comment 1, run hygiene-scanner-default-scope-parity 2026-10-30.

Cluster: docs/history/backlog/2026-10-30-report-scope-degradation-and-toctou-residuals.md (same surface: scripts/scan-public-hygiene.sh frozen modes vs report scope; same review origin)
