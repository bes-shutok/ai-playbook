# Backlog: define and verify active-plan referral behavior

- **Filed:** 2026-10-10, plan-scope gist surface review
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed plan-review finding
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, interruption and plan-prose mismatch handling
- **Severity:** blocking plan-review finding; the claimed referral path is not implemented by the referenced runtime contracts.

## Problem

The plan claims that a real operator message naming a plan before landing recalls it for scope changes at zero machinery cost. The maintenance re-entry rule only reruns lane selection after an ad-hoc task; the execute-plan interruption rules handle stop/resume and plan-prose mismatch, but do not route a named active plan into scope changes, refresh review/digest, and resume. Calling this an existing path can therefore leave an operator referral processed as an ordinary interruption with no scope update.

## Expected

Define an owned referral lifecycle for an active plan: recognize and bind the named plan, pause before further task claims, record the requested scope change, apply the plan-edit gate, refresh plan review and digest, and resume through the sanctioned execution path. Include observable acceptance and regression coverage for referral before claim, during worker activity, and after a task boundary. Until that contract exists, plan authors must not claim the active-plan referral is already supported.

## Evidence

- Plan: `docs/history/plans/2026-10-10-plan-scope-gist-surface.md`, Terms, Assumptions, Task 2.
- Review finding: `implementation#unwired-behavior`; maintenance `Interruption-resume` and execute-plan User Interruption / Plan-prose mismatch rules do not implement the promised active-plan referral.

## Dedup probe

Searched open backlog titles and Problem bodies for referral, active plan, scope changes, and interruption routing; no existing row owns a missing active-plan referral lifecycle. The existing plan recovery and done-verification rows concern task execution receipts and do not bind operator scope referrals.
