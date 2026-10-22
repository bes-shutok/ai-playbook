# Backlog: hard-mode pointer pinning and fixture-builder residuals

Filed: 2026-10-23
Status: open
Driving force: code-quality

Trigger: any change to SKILL_CLAUSE_POINTERS, the pointer print site, or the arm's fixture builders; the pinning/remedy work should ride the next change on that surface.

Origin: Phase 3 r1 panel of plan 2026-10-22-review-staging-hard-validator-fail-fast-iteration (findings C3, T1, D2; all valid, non-blocking, deferred at exit with this row as the owner).

- T1 (testing, Medium): 16 of the 20 `SKILL_CLAUSE_POINTERS` mappings in `scripts/validate_review_staging.py` are not pinned against a wrong section: the arm's "maps every marker to its own section" check proves only table-internal non-shadowing and the "emitted suffixes equal the recomputed mapping" check recomputes through `_skill_clause_pointer` itself. Mutation-proven: remapping `finding budget exceeded` to "Output discipline" leaves selftest and pins green. Remedy: hardcode the expected `(review-staging SKILL.md, <section>)` suffix per origin-family line in the arm, as the malformed-fixture checks already do.
- C3 (correctness, Low): marker matching is substring-anywhere over messages that interpolate author-controlled values, so a value containing an earlier marker's text misroutes the suffix (reproduced: a `risk_signals` tag literally equal to `coverage attempt record`). Print-layer only; contrived input. Remedy: per-marker anchoring (prefix for the prefix-shaped markers, template-position for the mid-message enum markers), not blanket `startswith`, since several markers legitimately sit mid-message.
- D2 (design, Medium): the `_selftest_hard_mode_diagnostics` arm re-implements existing fixture builders (`finding()` vs `_current_finding(**extra)`, a third copy of the Markdown finding boilerplate in `md_block()`, a hand-built payload vs `_version1_payload()`, a retyped literal in the malformed variant, and a fourth per-arm `_captured()/call()` copy). Remedy: compose from the shared builders, add an optional Pattern bullet to the shared Markdown builder, segment-build the malformed variant, hoist one shared capture helper.

- R2-1 (design, Medium, added at Phase 3 r2): the drift guard's two failure exits in `scripts/check_maintenance_pins.sh` use raw `exit 1`, bypassing the suite's outcome funnel (no final `OUTCOME:` line, no recorded-red/park escape for a legitimate planned section rename). Trigger: any future drift firing the guard, or a planned review-staging section rename that the operator wants to record-red through. Remedy: route both exits through the suite's fail=1 + emit_outcome funnel when the pins suite's failure-path surface is next touched.
- R2-4 (info): the drift-guard provenance comment lacks an admission link/review-by date; complete it with a pointer to the r1 review record at the next touch of the comment.

Cluster: docs/history/backlog/2026-10-23-hard-mode-pointer-coverage-extensions.md (same validator pointer surface); docs/history/plans/completed/2026-10-22-review-staging-hard-validator-fail-fast-iteration.md (archive lands with this plan's execution landing)
