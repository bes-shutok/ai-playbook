# Backlog: primary log commits can follow a checkout branch switch

- **Filed:** 2026-10-25, learn capture from a plan closeout
- **Status:** open
- **Priority:** medium
- **Workflow:** backlog
- **Origin class:** session-witnessed execution incident
- **Class:** fix-class
- **Driving force:** reliability + simplicity
- **Skill/step:** `docs/history/backlog/PLAN-PROMPTS.md`, Standing rules, Write boundary; primary-checkout log commit
- **Environment:** shared repository checkout with concurrent session activity, 2026-10-25
- **Suspected root area:** primary-checkout log writes are not bound to the intended branch ref at commit time

## Problem

A prompt-log prune was prepared on the primary branch while the required done and merge locks were held. Before the commit, another session switched the shared checkout to its own branch. The plain commit succeeded on that branch. The change was later transferred to the intended branch and the peer branch was returned to its prior tip. Expected: a lock-protected primary log write either updates its intended ref or detects checkout/ref drift before changing a branch.

## Evidence

- The checkout reported the primary branch before the operation, then the commit receipt named a different branch.
- The committed diff contained only the prompt-log prune; it was cherry-picked onto the primary branch, and the accidental peer-branch commit was removed with an expected-OID ref update.
- `docs/history/backlog/PLAN-PROMPTS.md` requires the done lock followed by the merge lock through commit, but neither lock pins the checkout's symbolic branch.
- `docs/history/plans/completed/2026-09-20-merge-landing-lock-grouping.md` already uses a temporary-index and expected-ref update path when the primary checkout is on another branch.

## Suggested direction

Investigate whether primary rolling-log commits should reuse the existing temporary-index and expected-ref update pattern, or whether all checkout branch switches can be serialized through the existing lock contract. Prefer the smallest path that binds the write to its intended ref. Do not add a new blocking gate or lock without meeting the repository machinery-admission rule.

## Alternatives

- Treat this only as an operator lapse and keep the write contract unchanged: rejected because the recorded branch check became stale before commit, while the lock contract does not bind the symbolic branch; the observed wrong-branch commit shows a concrete gap in this write surface (`docs/history/backlog/PLAN-PROMPTS.md`).
- Add a new repository-wide lock for every branch switch: rejected because no evidence shows all branch-switching paths can acquire it, so it could block unrelated work without closing the observed path (`agents/skills/plans/SKILL.md`, primary-placement workflow).
- Keep plain commits with a branch check in a separate earlier command: rejected because the check can become stale before the commit, as this incident demonstrates (current session commit receipt and branch history).
