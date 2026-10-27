# Backlog: learn missed its own workflow failure

- **Filed:** 2026-10-27, current-session operator correction
- **Status:** open
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class (a missed skill-use issue required the user to prompt again)
- **Driving force:** reliability + efficiency
- **Skill/step:** `agents/skills/learn/step-1-extract.md` Step 1 and Step 1.8 candidate capture

## Problem

After a learn run reviewed the session where the user had to invoke `self-heal` manually, I reported that no separate learn issue needed capture because the workflow blocker already had a backlog item and plan. The user had to ask why learn missed its own failure. This confused coverage of the original workflow defect with coverage of learn's failure to identify and capture the distinct skill-use issue.

## Expected behavior

When learning from a workflow failure, assess the workflow's underlying defect and the agent's failure to invoke or follow an applicable skill as separate candidates. Before dismissing either as covered, verify that the existing item covers that specific failure mode and skill step. Step 1.8 should capture a distinct learn issue when learn's candidate review omits one.

## Evidence

- As witnessed in the current session, the user asked why learn had missed that they needed to manually invoke `self-heal`, then requested a learn backlog item and investigation.
- `agents/skills/learn/step-1-extract.md` Step 1 already requires reviewing mistakes, corrections, and friction; its premature-dismissal anti-pattern requires checking the specific failure mode before treating it as covered.
- The same module's Step 1.8 already requires identifying skill-usage issues and capturing skill or workflow instruction failures.
- `docs/history/backlog/2026-10-27-self-heal-before-workflow-stop.md` and its covering plan address the workflow's missed self-heal invocation, not learn's separate omission.

## Suspected root area

Candidate extraction and deduplication conflated shared incident context with shared failure mode. Investigate whether a short explicit cross-check in Step 1 or Step 1.8 would prevent this class of omission, or whether the existing rule was sufficiently clear and this was execution noncompliance.

## Source

Current-session operator correction after learn failed to capture its own skill-use issue on the first pass.
