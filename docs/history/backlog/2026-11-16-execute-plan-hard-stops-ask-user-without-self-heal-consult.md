# Backlog: execute-plan stop rows that ask the user for direction are not wired to the self-heal consult the rest of the playbook requires

- **Filed:** 2026-11-16, user-requested capture (survey of where the unattended and interactive flows stop)
- **Status:** closed (investigated 2026-11-16: no skill-text change warranted. `agents/skills/using-skills/SKILL.md` item 1 already requires one `self-heal` consult before any skill-workflow stop is judged unrecoverable, which covers the `execute-plan` stop rows; a local pointer would formalize a duty an existing mechanism performs)
- **Priority:** medium
- **Origin class:** corpus survey with on-disk re-derivation (no live run witnessed the stop; the rows are read from the skill text)
- **Workflow:** backlog
- **Class:** fix-class (a stop row ends in "ask the user" while the playbook's stated rule is one self-heal consult before any non-user-only stop)
- **Skill and step:** `agents/skills/execute-plan/phase-3-review.md` (the escalation table rows "A second escalation is required" and "Fix-risk stop conditions met"), `agents/skills/execute-plan/implementation-loop.md` (the Inclusion Hard Gate "Stop" outcome), `agents/skills/execute-plan/launch-rules-and-gates.md` (hard gate 23, the one existing self-heal pointer)

## Observed vs expected

Observed (re-derived from disk 2026-11-16):

- `phase-3-review.md` escalation table: "A second escalation is required: Stop; report unresolved blocking findings and ask the user", and "Fix-risk stop conditions met: Stop; ask the user for direction".
- `implementation-loop.md` Inclusion Hard Gate: outcome 3 "Stop the run and record the hard-gate reason".
- The only self-heal pointer in `execute-plan` is hard gate 23 in `launch-rules-and-gates.md` (before folding further when fixes regenerate findings, and review-plan's churn sequence). Whether it runs before the two table rows above is not stated.
- `agents/skills/execute-plan/subagent-prompts.md` already tells sub-agents not to ask the user for permission between tasks, review rounds or fixes, so the policy intent is no unnecessary asks.

Expected: each stop row that ends in a question either names the user-only class that makes it a user decision (missing authority, ambiguous ownership, unsafe target) or runs one `self-heal` consult first and records its disposition, as `agents/skills/maintenance/decisions.md` requires for the unattended loop.

## Reproduction evidence (trimmed)

1. `grep -n "self-heal" agents/skills/execute-plan/*.md` lists one pointer (launch-rules-and-gates.md hard gate 23) plus one archive-and-cleanup mention.
2. Read the two `phase-3-review.md` rows and the implementation-loop hard-gate outcome: each ends in a stop or a question with no consult.

## Environment

- Playbook skills repo, deployed copy, 2026-11-16.

## Suspected root area

The stop rows were written before the self-heal-first rule was added to other skills, and the later plans wired the maintenance, plans, done and review-plan sites only. Fix options to price: one sentence under the escalation table ("before either stop, one self-heal consult; ask only for a user-only class"); or classify each row as user-only with its reason so no consult is owed. A hard-gate stop for an external prerequisite or a missing authorization may legitimately be user-only; the investigation decides per row. Cap and wall behavior is out of scope (covered by the completed interactive-lane plan).
