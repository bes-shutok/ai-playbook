# Backlog: restore the reply-permission vs push-authorization separation statement in done

- **Filed:** 2026-10-27, execute-plan Phase 3 r1 review (self-heal-before-workflow-stop; both lenses, independent)
- **Status:** resolved — the separation sentence exists at HEAD (`agents/skills/done/SKILL.md` passive-review paragraph carries "Keep push authorization separate from permission to reply to review feedback."), restored by 9c318d3e2 (plans: land self-heal recovery plan); re-derived 2026-10-31 during the learn/investigate pass over the self-heal-before-unknown-remedy session.
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-finding
- **Class:** fix-class (byte-balance deletion removed a rule, not a duplicate)
- **Driving force:** reliability (an improvising session could treat review-reply permission as push authorization); secondary: clarity
- **Skill/step:** `agents/skills/done/SKILL.md` passive-review finalization paragraph
- **Cluster:** docs/history/plans/completed/2026-10-29-self-heal-before-unknown-remedy.md (self-heal/done skill-text restoration family; sibling rows landed ad-hoc 2026-10-31)

## Problem

The self-heal plan's byte-payment deletion removed done's only living statement of the separation ("Keep push authorization separate from permission to reply to review feedback."); the retained clause "a reply does not imply the branch was pushed" carries the factual direction but not the authorization boundary. Repo-wide grep at HEAD finds no active-skill home for the concept.

## Suggested investigation

Fold the authorization boundary into the retained sentence (for example "a reply does not imply the branch was pushed, and reply permission never authorizes one"), paid within the file's byte balance, or accept the loss explicitly with the decision recorded.

## Source

Phase 3 r1 record .ai-playbook/reviews/2026-10-27-self-heal-before-workflow-stop-code-review-r1.md finding 2.
