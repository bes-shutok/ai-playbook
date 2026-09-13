# Backlog: trailer gate tilde-side selftest arm coverage (r1 overflow F3/F4)

Status: done
Workflow: backlog
Source: docs/reviews/2026-09-09-2026-09-09-plan-readiness-trailer-gate-r5-deferrals-code-review-r1.md (Overflow manifest, rows 1-2; branch 2026-09-09-trailer-gate-r5-deferrals, execute-plan Phase 3 round 1)
Severity: 2 Low (both non-blocking, testing worker overflow)
Scope: scripts/plan_readiness.py (selftest `_selftest_decision_marker` arms family)
Class: duplicate-unit-witness deferral per ADR-0002 (backlog-by-default in execute-plan Phase 3; scheduled for the next plan touching this selftest family)

## Problem

The r1 fresh full-panel review of the trailer-gate r5 deferrals branch staged two Low testing-worker coverage gaps as overflow (over the per-worker Low budget). Both are tilde-side fence-parser variants whose invariants are pinned on the backtick side by existing arms, but have no tilde-side witness: a fence-character-specific or over-broad regression on the tilde side of `_strip_fences` would keep the selftest green.

## Findings

### F3. Tilde closer run-length and indent variants unguarded

- Pattern: `testing#coverage-gap` (anchor at review time: scripts/plan_readiness.py:2252, the closer-rule selftest region).
- Consequence: a closer regression specific to tilde fences (run-length or indent handling) would pass green; only the backtick-side arms (`trailer_inside_short_close_fails`, `trailer_after_indent_4_closer_stays_fenced`) pin the rule today.
- Concrete arms to add (fail-arms inside a still-open `~~~~` fence, real trailer after each pseudo-closer, date 2026-09-08, needle `missing decision-points trailer`):
  - `trailer_inside_tilde_short_close_fails`: `~~~~` opener, a `~~~` line (shorter same-character run, legal content) before the real trailer, then a genuine bare `~~~~` closer after the trailer: the trailer stays swallowed.
  - `trailer_after_indent_4_tilde_closer_stays_fenced`: `~~~~` opener, a 4-space-indented `~~~` pseudo-closer before the real trailer, then a genuine bare closer after it: the indented line is content, the trailer stays swallowed.
- Acceptance: both arms green under the current parser; each flips red under the named regression (tilde closer accepting a shorter run; tilde closer accepting indent >= 4). `python3 scripts/plan_readiness.py --selftest` stays ALL PASS.

### F4. Tilde-opener-with-backtick-info-string still-opens arm missing

- Pattern: `testing#coverage-gap` (anchor at review time: scripts/plan_readiness.py:2317, the r5 F8 backtick-info opener region).
- Consequence: the deliberate exemption in the r5 F8 rule (a BACKTICK opener whose info string contains a backtick is paragraph content; TILDE openers keep accepting any info string) has no tilde-side witness; an over-broad F8 regression that rejects tilde openers carrying backticked info strings would pass green.
- Concrete arm to add (fail-arm, date 2026-09-08, needle `missing decision-points trailer`):
  - `trailer_inside_tilde_fence_with_backtick_info_fails`: a `~~~x` opener with a backtick info string variant (e.g. `~~~ Decision points` styled text with backticks, or `~~~x` followed by content containing ``` on the same line) opens a tilde fence and swallows the real trailer inside it; a bare `~~~` line closes it after the trailer: the trailer stays swallowed, so the gate fails with the missing-trailer reason.
- Acceptance: arm green under the current parser; flips red if the F8 backtick-info rejection is wrongly applied to tilde openers (tilde opener treated as paragraph content, trailer becomes visible, arm unexpectedly passes). `python3 scripts/plan_readiness.py --selftest` stays ALL PASS.

## Why not fixed now

Overflow over the testing worker's Low budget in execute-plan Phase 3 round 1; both findings are duplicate-unit-witness class (the shared closer/opener invariants are pinned by the existing backtick-side arms, e.g. `trailer_inside_short_close_fails` fails when the closer run-length rule is violated), so per ADR-0002 they are backlog-by-default instead of fixed-inline. Deferred by the address sub-agent 2026-09-09 per the pre-decided disposition of the execute-plan orchestrator.

## Acceptance

- Add the F3 and F4 arms in one pass touching this selftest family (next plan that modifies `_selftest_decision_marker` or `_strip_fences`).
- New arms follow the `selftest#decision_marker/<name>` convention; existing arm names unchanged.
- `python3 scripts/plan_readiness.py --selftest` stays ALL PASS with the new arms green; each new arm flips red under its named regression (verified by mutation during the fix pass).
