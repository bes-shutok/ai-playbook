# Backlog: replace peer-authored em dashes from the deferred-plans convention session

Status: done (fixed 2026-09-12: the four scoped em dashes replaced with punctuation in doc-hierarchy SKILL.md, deferred/ README.md, and the guidelines section 64 amendment sentence; hygiene scan exit 0)
Workflow: backlog
Source: code review round 3 finding F-r3-16 (docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r3.md), deferred as peer-owned; extended by round 4 finding F-r4-11 (docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r4.md), same deferred disposition
Severity: Low (mechanical text fix)
Scope: agents/skills/doc-hierarchy/SKILL.md; docs/plans/deferred/README.md; guidelines §64 amendment (projects/.ai-playbook/agent_workflow_guidelines.md, ~line 1043 at r4 review time, peer-authored in c5e0bfb)

## Problem

Peer-authored sentences written during the deferred-plans convention session
contain em dashes, violating the repository's no-em-dash convention for
authored text:

- `agents/skills/doc-hierarchy/SKILL.md` (the `backlog/deferred/` sentence; line 68 at review time, line 81 on the current tree)
- `docs/plans/deferred/README.md` (intro paragraph and deferral-rationale paragraph)
- the user-level guidelines §64 amendment (~line 1043 at r4 review time), peer-authored text landed in c5e0bfb and named by F-r4-11; it is covered by this same deferred disposition (do not edit the §64 text from the r4 address run)

## Why not fixed now

The deferred-plans convention session owns both files; this backlog item
defers to that session rather than editing peer-owned work mid-flight.

## Suggested fix

Mechanical dash replacement (em dash to comma, colon, or spaced hyphen as the
sentence requires) in the two locations above.
