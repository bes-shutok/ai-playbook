# Backlog: an interactive plan, review and commit session stops to ask the user at steps that are mandated or recoverable, and never consults self-heal first

- **Filed:** 2026-11-16, user-requested capture after an interactive session needed a user reply at nearly every gate
- **Status:** closed (investigated 2026-11-16: no skill-text change warranted. The rule already exists and says what this row asks for: `agents/skills/using-skills/SKILL.md` item 1 (invoke `self-heal` once before judging a skill-workflow stop unrecoverable; ask only for a decision or authorization that belongs to the user), `agents/skills/plans/SKILL.md` Uncertain workflow stops, `agents/skills/done/SKILL.md` Uncertain stop handoff, `agents/skills/maintenance/decisions.md` (the self-heal consultation paragraph for non-user-only blockers). Witness 3 below was wrong: `done/SKILL.md` names side-repo staging asks as user-only stops, so that ask was sanctioned. Witnesses 1 and 2 were agent non-compliance with existing text, not a text gap; adding a fifth restatement is a rejected shape under the growth-balance rule, and a hook would be machinery with one witnessed session)
- **Priority:** high
- **Origin class:** session-witnessed stops (an interactive plan-authoring, plan-review and skill-fix session; the stops are recorded below)
- **Workflow:** backlog
- **Class:** fix-class (the interactive flow has no rule that separates a user-only decision from a step the skills already mandate or the agent can recover, so every gate becomes a question)
- **Skill and step:** `agents/skills/using-skills/SKILL.md` (self-heal consult pointer), `agents/skills/plans/SKILL.md`, `agents/skills/review-plan/SKILL.md` (blocked-verdict handling outside the churn trigger), `agents/skills/self-heal/SKILL.md` Recovery step 5; `docs/AGENTS.md` Skill maintenance sentence (the panel review that gates a skill commit)

## Observed vs expected

Observed: in one interactive session the agent ended nearly every turn with a question and waited for a reply, and the session record shows no `self-heal` invocation. Concrete stops:

1. After a skill-text edit, the agent asked "run the panel review on the skill diff?". The user rule (`docs/AGENTS.md`, Skill maintenance) makes that review the precondition of the commit, so it was a mandated step, not a decision.
2. The readiness gate failed because a newer review round (run in another session) reported `ready=no`. The agent diagnosed the cause (a skill sentence stated more broadly than its rule), then asked the user how to handle the finding instead of consulting `self-heal` for the smallest safe route (fix the skill text, file the backlog row, re-review).
3. The closeout runner skipped a side-repository step, and the agent asked the user how to proceed instead of consulting `self-heal` first (done SKILL.md names a mandatory consult).

None of the three was a user-only decision as `self-heal` Recovery step 5 defines it (missing authority, ambiguous ownership, or an unsafe target). The unattended maintenance loop has a self-heal-first rule (`agents/skills/maintenance/decisions.md`, one consult before a non-user-only stop); the interactive flow has none.

Expected: an interactive session carries the same rule. Before a question to the user it names which of the user-only classes applies; a mandated step (a review that gates a commit, a gate re-run, a backlog capture) runs without asking; a blocked verdict gets one `self-heal` consult before a question; and a user's standing "continue" or "fix" instruction in the same session covers the steps that follow from it, while commit, push and external writes keep their own authorization rules.

## Reproduction evidence (trimmed)

1. Start an interactive plan-authoring session, close a plan review at its cap, then run the readiness gate: a later review round blocks it.
2. Observe the agent end the turn on a question for a derivable next step, with no `self-heal` invocation in the session record.
3. Compare with `agents/skills/maintenance/decisions.md` (self-heal-first on blocks), which covers the unattended loop only.

## Environment

- Playbook skills repo, deployed copy, 2026-11-16; Claude Code desktop session; the host app also prompts the agent to end a turn with a next-step question when a decision is pending, so the skill text has to define what counts as pending.

## Suspected root area

`self-heal` is wired into the maintenance loop, `plans` (SKILL.md), `done`, `using-skills` and `review-plan`'s churn trigger, but no skill states an interactive "ask only for user-only classes" rule or tells the agent that a skill-mandated gate is not a question. The unattended arms are covered by completed plans (2026-11-02 self-heal-first-on-blocks, 2026-11-13 interactive-lane-indefinite-operation, which is about maintenance lanes only). Fix options to price: a short interactive-stop rule in `using-skills`; a one-line pointer in `plans` and `review-plan`; naming mandated gates as non-questions where the skill already mandates them. Do not add a validator without a witnessed incident.
