# Backlog: known-red baseline Phase 3 r1 residuals

Driving force: code-quality (witnessed by the Phase 3 fresh full-panel r1, 2026-11-19, run known-red-gates-consumed-baseline, staging record `.ai-playbook/reviews/2026-11-19-known-red-gates-consumed-baseline-code-review-r1.md`, zero blocking findings, all staged findings deferred here).

Staged residuals:

1. Render-invocation detection recognizes only the literal space-form flag; equals-form and argparse abbreviations exit the legacy usage shape; the register row does not declare the non-repo arm (machinery_inventory.py:702-705,725-726; OUTCOME_CONTRACT.md:89).
2. `--render-baseline ""` truthiness falls through to a legacy check run (machinery_inventory.py:733).
3. `_git_probe` misses a missing-git OSError and duplicates the `_git` helper (machinery_inventory.py:428-432).
4. Embedded-line placement lacks a consumer-facing explanation; a placement-keyed consumer could govern a pins-embedded budget line by pins-section staleness (machinery_inventory.py:612-620; plan-quality-gate.md:7) [Medium].
5. Composite digest recipe exists only in code; the classification clause does not cite it (machinery_inventory.py:495-500).
6. Env-posture provenance absent; exec pointer could carry a no-exit-code bound sentence (machinery_inventory.py:557-576; implementation-loop.md:175).
7. Capture `class` label never asserted; longest-prefix order invariant untested (test_machinery_inventory.py:797).
8. Digest-input completeness proven one-input-per-producer only (test_machinery_inventory.py:874).
9. Per-file digest map is diagnostic-only payload beyond the required composite (machinery_inventory.py:495-500).
10. Exclusion prefix `missing ` broader than the Terms' scoped arm (machinery_inventory.py:406).
11. Preamble restates the operative clause's fail-open definitions verbatim (review-agents/SKILL.md:16; rides the Task 2 residual 3 witness-needle wording).
12. Env-posture test comment claims an unasserted duplicate-root fallback (test_machinery_inventory.py:982).
13. Render JSON shape carries redundant placement fields (machinery_inventory.py:577-582).
14. Unconstrained render output path can clobber working-tree bytes via silent os.replace of a mistyped relative path [Medium] (machinery_inventory.py:654-670).

Overflowed at synthesis (per-worker non-blocking Low budget): F3, F5, F6, F11, F12, F13 (same surfaces as items 3, 5, 6, 11, 12, 13 above).

Cluster: known-red-gates-consumed-baseline
Cluster: docs/history/backlog/2026-11-20-known-red-baseline-stales-under-landing-traffic.md (same mechanism: that row owns the traffic-pattern staleness and the consumption-evidence gap, this row the code-level residuals)
