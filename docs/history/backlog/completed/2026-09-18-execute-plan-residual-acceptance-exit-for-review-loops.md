# Backlog: execute-plan review loops need a sanctioned residual-acceptance exit

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-18
Class: execute-plan Phase 3 exit-criteria gap (skill-level, affects every consumer repo)
Origin: execute-plan run of docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md. The Phase 3 loop ran its full five-round budget, stopped at the cap with blocking findings, needed a user-granted standing continue (r6), hit the reconciliation stop condition again (r6 regenerated the wedge class), and only converged after the user chose Option B and agreed - in chat, ad hoc - to a residual-acceptance policy: fix the named blocking findings, verify with a focused targeted round, and route any NEW blocking finding that is not a defect in those fixes to durable backlog items instead of looping. Round 7 then exited clean on the first try (zero blocking; 8 non-blocking residuals backlogged). The skill's exit criteria today allow only "one fresh blocking-clean review" or user-directed stops; there is no sanctioned exit for "blocking-clean on the verified fixes, residuals owned" - so every long loop ends at the cap with an ask instead of a defined convergence path.

## Problem

A fresh-adversarial full panel over a large diff asymptotes but never reaches zero (observed raw findings across rounds: 36, 26, 27, 27, 17, 16, 8-0-blocking). Most surviving findings live in opt-in machinery no real run has exercised, so inspection-based review finds their edge cases indefinitely, while the plan's own Ship-when assigns their real validation to future runtime runs. The loop needs a defined, pre-authorized exit that converts this structural fact into process instead of requiring an ad-hoc chat agreement at the cap.

## Prevention

1. In the execute-plan skill (Step 3.5 and/or the Review end condition table), define a residual-acceptance exit: when the reconciliation pass or the fix-risk triage produces a named fix set, the orchestrator may propose (or a standing instruction may grant) a bounded exit - one address pass for the named set, one focused targeted round per review-panel-selection Targeted follow-ups, and every NEW blocking finding outside the named set becomes a durable backlog item (owner + trigger) instead of a loop.
2. Require the residual policy to be recorded in the manifest before the verification round runs (a `residual_policy:` manifest line), so the exit is auditable and a resumed session cannot silently widen it.
3. Mirror one line in the review-loop skill (its exit criteria have the same shape).

## Evidence

Session manifest (r1-r7 history, two budget pauses, cap stop, r6 stop condition, r7 clean exit under the policy); reconciliation ledger docs/reviews/2026-09-18-review-reconciliation-execute-plan-review-fix-pipeline-efficiency.md; r7 staging docs/reviews/2026-09-18-...-code-review-r7.md (verdict yes, 8 residuals backlogged in docs/history/backlog/2026-09-18-watcher-teardown-receipt-and-authoring-rectification-coverage.md and docs/history/backlog/2026-09-18-r7-low-residuals-release-shape-pins-hermeticity.md).
