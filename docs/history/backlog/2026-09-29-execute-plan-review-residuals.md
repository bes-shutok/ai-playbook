Status: open
Priority: medium
Workflow: backlog
Class: tooling
Driving force: reliability
Origin class: review-residual (2026-09-29: execute-plan-task-local-verifier-declarations r1 full-panel review, verdict clean, seven non-blocking findings; staging record docs/reviews/2026-09-29-code-review-execute-plan-task-local-verifier-declarations-r1.md)

# Execute-plan task-local-verifier landing residuals

## Problem

The task-local-verifier-declarations landing left five substantively open non-blocking residuals; none blocks, but each is either an uncovered fence or a plan-letter deviation that a later touch could silently regress.

## Items

1. Root-less classification (`scripts/execute_plan_runtime.py` around 592-598): when no repository root is supplied, a whitespace-free token falls to containment classification instead of pure-path identity, over-refusing nested-path namesakes for library callers. Production paths always resolve a root; align the classification with the plan letter (canonicalization identity when no root) or pin the stricter behavior deliberately.
2. Unpinned mid-run fences: (a) `recover_evidence_contract` prior_exact skips the claim_token equality when the stored checkpoint result carries none (records written after the landing carry it); (b) the ambiguous-claims continuation exam excludes closed claims. Both judged safe, neither has a dedicated regression test. Add: a recovery test seeding a handoff intent whose prior checkpoint record carries a mismatched claim_token (refusal) and one whose record omits it (acceptance); a startup-reconciliation pin that a closed claim on a requeued-pending task completes instead of quarantining.
3. Acceptance-pin fixture literals vs plan pins (Task 1 item 4): nested namesake landed as `other/reports/report.txt` (plan pinned `src/reports/report.txt`); tail-boundary acceptance landed as a flag-assignment token (plan pinned a marker-bearing body embedding `reports/report.txt.bak`); same-or-earlier carve-out landed as pure-path tokens (plan pinned a marker-bearing body). The plan's exact shapes verified accepted; add the three pinned-shape sub-cases.
4. Display elision: the refusal display gives byte count only; the plan letter is first line plus byte count. Current form is stricter and test-consistent; either amend the plan-letter expectation or add the first line. Also the shape-1 display says "embeds" for exact-equality tokens (cosmetic wording).
5. Harness placement: the three plan-pinned recovery test names live in `EvidenceContractRecoveryCodexTest`, not the plan-named `ExecutePlanRuntimeTest`; commit messages for tasks 1 and 4 use house `<area>:` style instead of the pinned `feat:` texts. Accepted in place; recorded so a later reconciliation does not "fix" them blind.

## Suggested fix

One small follow-up plan covering items 1-4 (test pins plus the root-less classification decision); item 5 is record-only.

## Environment

Witnessed in the skills repo worktree ai-playbook-tlvd-exec during the 2026-09-29 unattended execution; reviewer verdict clean with zero blocking; all gates green (529 runtime tests, em-dash scans).
