# Dispatch exemption wording-precision residuals (review r4 Lows)

- **Filed:** 2026-10-29 (execute-plan Phase 3 round r4, window-dispatch-hardening exit round)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (wording precision only; no wrong behavior derivable from either reading, verified by the r4 workers)
- **Origin class:** review finding (Phase 3 r4, converged contract-docs + design-simplicity worker, both Low non-blocking)
- **Class:** fix-class (two one-phrase precision edits; zero behavior change)
- **Driving force:** reliability (secondary: simplicity)

## Observed versus expected

Two wording-precision residuals from the exit round of the window-dispatch-hardening execution:

1. zcode.md Child dispatch ladder step 1 grounds the re-arm create route's spacing exemption on "the same arm the operator-named minute is", while the single-homed exemption set at scheduling.md Step 5 keys the stop-park resume carrier's exemption on the Quota leg's arm (class b); the quoted rationale ("wall-clock anchor, not a chosen minute") is class b's. Expected: ground the re-arm exemption on the class whose predicate covers it (the Quota leg's arm, quota-policy.md Step 4) or on the wall-clock-anchor sentence alone.
2. quota-policy.md Step 4's Ad-hoc route clause quotes "blocked ad-hoc work holds with a recorded reason and never parks" as "the arm's own recorded form", but that sentence is byte-present at the state-file.md pending_dispatch kind-enum paragraph, not at the named decisions.md Ad-hoc backlog arm bullet (whose own wording is "hold the item with a recorded reason ... never a scheduled-child payload route"). Expected: name the quote's actual home (the State file's kind-enum paragraph) or quote the decisions.md arm bullet's own wording beside the label.

Content agrees everywhere; a strict exact-string verifier is the only cost.

## Environment context

Playbook repo, branch 2026-10-28-window-dispatch-hardening at a746207c7 (the reviewed exit digest); both r4 workers verified no wrong behavior is reachable from either reading; the owning modules are agents/skills/maintenance/zcode.md and agents/skills/maintenance/quota-policy.md.
