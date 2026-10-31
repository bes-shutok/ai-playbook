# Backlog: residual clause-pointer under-routing families at the covered families' boundaries

Driving force: code-quality
Created: 2026-10-31 (hard-mode-clause-pointer-residuals Task 1 intermediate review, finding 2)
Cluster: docs/history/backlog/2026-10-31-witness-ledger-pointer-marker-case-dead.md
Cluster: docs/history/backlog/2026-10-31-clause-pointer-r2-residual-improvements.md

After the hard-mode-clause-pointer-residuals coverage landing, these emission shapes still route to the bare skill fallback; none matches the coverage row's enumerated message shapes, so they are candidate follow-up families:
- COVERAGE_SIDECAR_MIN_DATE date-fence violations ("date disagreement: staging filename dated ... earlier than COVERAGE_SIDECAR_MIN_DATE", "version-1 sidecar dated ... is earlier than ...") - uppercase constant misses the lowercase `coverage` marker.
- Hyphenated "usage-attribution fallback marker cannot coexist with either mint-pair field" - "mint-pair" != "mint pair".
- Freshness Metadata Review-mode variants ("missing freshness Metadata line 'Review mode'") - no "Metadata Review mode" substring.

Fix: derive markers from these emit sites and add rows byte-exact-pinned as in the parent landing.

Source: 2026-10-31 interactive exec intermediate review of validate_review_staging.py (capture-all emit-site corpus simulation).
