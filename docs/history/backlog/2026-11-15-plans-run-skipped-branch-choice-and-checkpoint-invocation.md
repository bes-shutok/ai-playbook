# Backlog: plans run skipped the company branch choice and the checkpoint commits, and a user-level commit rule hides the conflict

- **Filed:** 2026-11-15, same incident as the sibling item; the agent's own missed invocation, filed separately per the capture step's two-candidate rule
- **Status:** covered (docs/history/plans/2026-11-15-plans-authoring-primary-company-branch-and-checkpoint-enforcement.md)
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class (the agent had no sanctioned way to learn that its commit rule and the skill's checkpoint duty conflict, and the user had to correct the run)
- **Driving force:** clarity
- **Skill/step:** `docs/AGENTS.md` (the cross-project hard rules list, the commit-related entries); `agents/skills/plans/phase-0-placement.md` (Authoring checkpoint duty); `agents/skills/plans/SKILL.md` (Module dispatch entry for Phase 0)
- **Cluster:** docs/history/backlog/2026-11-15-plans-authoring-company-primary-branch-choice-and-checkpoint-gap.md (the workflow defect this run also hit)

## Observed versus expected

Observed. The agent applicable-skill invocation was incomplete in three ways:

1. **The canonical policy section was never loaded.** The plans router dispatches Phase 0 to `phase-0-placement.md`, which refers to the company task-branch arm only by a parenthetical and defers the lifecycle to the Worktree-first standard in `agents/skills/execute-plan/worktree-first.md`. The agent read Phase 0 and the project facts, saw `worktree_policy = "primary"`, and concluded "work on the current branch" without opening the policy paragraph that adds the company-profile branch choice.
2. **The checkpoint duty was read and not scheduled.** The agent's task list had no entry for the `wip:` checkpoint commits or the round-start anchor, so the duty was never executed.
3. **A conflicting commit rule was resolved silently.** The host runtime's built-in instruction says to commit or push only when the user asks (re-derived: that sentence appears in neither the user-level global instructions file nor the cross-project hard rules in `docs/AGENTS.md`; the hard rules authorize only execute-plan's per-task `done` commits). The plans skill's checkpoint commits ("mechanical plan-bytes-only safety commits, never operator-approved") have no matching authorization line at the user level, so the skill duty and the host default pointed in opposite directions and nothing said which wins. The agent resolved the conflict in favour of "do not commit" without raising it, and did not branch either, although the same host instruction says to branch before work when on the default branch.

Expected. When a skill duty and a user-level hard rule appear to conflict, the agent asks once (or the rules cross-reference each other so no conflict exists), and a company-profile primary-placement run asks for the branch choice before the first write.

## Reproduction evidence (trimmed)

- Skill text read: router, Phase 0 module, Phase 1 module, plan-format, task-design, plan-quality-gate. Not read: the Worktree-first standard's policy paragraph.
- The user's correction arrived after certification: the run "should be working in the branch".
- Hard rule text (paraphrased, re-derived against `docs/AGENTS.md` by grep): never push without instruction; execute-plan per-task commits are authorized for that run only; no entry covers plans checkpoint commits, and no entry states a general commit-only-on-instruction rule (that default comes from the host runtime).

## Environment

Interactive Claude Code session, 2026-11-15, deployed home skills, company project with primary placement.

## Suspected root area

- `docs/AGENTS.md` hard rules: add one line that plans `wip:` checkpoint commits on the recorded branch are authorized for the authoring run only (pushes still need explicit instruction), mirroring the execute-plan line, so the user-level rules explicitly outrank the host runtime's commit-on-request default for this one duty.
- `agents/skills/plans/SKILL.md` and Phase 0: the router's Phase 0 dispatch entry should name the policy paragraph as a required read for company-profile projects, so the single home is loaded on dispatch.

## Outcome sought

- The hard rules list authorizes (or explicitly forbids) plans checkpoint commits, so no silent conflict remains.
- The Phase 0 dispatch entry lists the policy paragraph as a mandatory load when the project's facts declare a company profile.

## Rejected alternatives

- Treat this as the agent's mistake only: rejected, the missing authorization line and the parenthetical-only pointer made the omission easy and unobservable.
- Duplicate the policy paragraph into the plans module: rejected, it would create a second copy of a rule whose single home is already designated.
