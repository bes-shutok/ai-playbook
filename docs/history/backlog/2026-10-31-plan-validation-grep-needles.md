Status: open
Priority: low
Class: fix-class
Origin class: review-finding (execute-plan run session-channel-zcode-runtime-derivation-empty, Phase 3 code-review r1, 2026-10-31)
Cluster: docs/history/backlog/2026-10-31-plan-review-record-glob-infix.md (plan-doc evidence pointers without discriminating power)

# Plan doc-path validation greps are non-discriminating

Driving force: testability

The covering plan's Validation Commands re-run three `rg` greps over the must-fix doc paths (`agents/hooks/skill-gate/README.md`, `agents/skills/maintenance/zcode.md`, `agents/hooks/lessons-recall/README.md`) as those docs' only run-evidence, but the needle set (`ZCode|ZCODE|no-session`) also matches pre-existing content at `main`, so the greps cannot fail: reverting the doc edits keeps them green, and a future re-run of the plan family passes after an accidental doc revert. Exact location: `docs/history/plans/2026-10-30-session-channel-zcode-runtime-derivation-empty.md` Validation Commands block (line 66). The plan's code paths have a discriminating gate (`scripts/session_channel.py --selftest`); the doc paths have none.

Source: finding F8 (Low, non-blocking, pattern `testing#non-discriminating-pin`), Phase 3 code-review r1 of the covering execution run, staging doc `.ai-playbook/reviews/2026-10-31-session-channel-zcode-runtime-derivation-empty-code-review-r1.md`; capture hygiene: scan-public-hygiene --files pass (2026-10-31).

Suggested fix options: (a) validate doc paths with per-file example spans measured against each doc's landed text: `rg -n "EXPLICIT identity|marker-recipe-only" agents/hooks/skill-gate/README.md`, `rg -n "MARKER-ONLY" agents/skills/maintenance/zcode.md`, `rg -n "explicit --session-id input" agents/hooks/lessons-recall/README.md` (each span re-verified against its file with rg on 2026-10-31); (b) the plans skill tightens its Validation Commands guidance so must-fix doc paths get discriminating needles by construction.

Why not fixed now: editing the certified plan's Validation Commands mid-run would churn the plan digest the executing run is bound to; the r1 fix pass (2026-10-31) captured this row instead of mutating the plan file.

Dedup probe: keyword search ("validation command", "non-discriminating", "grep") over the open backlog filenames and problem bodies, 2026-10-31; nearest items are `2026-10-29-done-final-only-plan-validation-residuals.md` (done-boundary validation residuals for completed plans, a different validation surface) and `2026-10-31-pre-execution-re-verification-label-mismatch.md` (pointer-label mismatch, not validation discriminating power); no open item owns plan Validation Commands' needle discriminating power, no merge.

**Ship when:** the plan family's doc-path validation carries discriminating needles (v5-specific grep spans over the three doc paths) or the plans skill's Validation Commands guidance tightens its command-shape requirements so must-fix doc paths get non-pre-existing needles by construction.
