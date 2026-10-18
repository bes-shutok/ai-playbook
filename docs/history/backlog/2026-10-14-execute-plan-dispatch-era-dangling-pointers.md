# Backlog: sweep the dangling dispatch-era pointers in the execute-plan surfaces

- **Filed:** 2026-10-14, red-on-main-baseline-repair-and-auto-demote execution review r1 (worker 1, finding 4; recorded-only residual, ruled out of that plan's mirror-coherence scope)
- **Status:** open
- **Workflow:** skill text adjudication
- **Priority:** low
- **Origin class:** execution review residual
- **Class:** fix-class
- **Driving force:** correctness

## Problem

Several execute-plan skill surfaces still cite contract shapes or sections that no surface defines since the certified adapter-removal landing e0d7d6961 removed the dispatch-era prose: agents/skills/execute-plan/subagent-prompts.md's `pre_restart:`/`pre_restart_paths:` shape references and its remaining "dispatch-mode paragraph" pointer, and agents/skills/plans/SKILL.md's "canonical Standing resume watcher subsection" citation. None is pinned, and each was equally dangling before and after the red-on-main landing, so the mirror-coherence clause could not reach them.

## Expected

A bounded sweep that resolves or removes each dangling pointer: either the cited shape or subsection returns to a live surface with an owning plan, or the citing sentence is reworded to name only defined vocabulary. No new pin or gate is expected; the red-on-main consult already keeps the wired surfaces honest.
