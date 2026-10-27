# Backlog: check agent-type affinity before authoring or executing work

Filed: 2026-10-27
Status: covered (docs/history/plans/2026-10-27-agent-type-affinity-before-plan-work.md)
Workflow: backlog
Priority: high

- **Class:** fix-class
- **Origin class:** self-serving
- **Skill/step:** maintenance D2 authoring selection and D1 execution selection; plans and execute-plan entry
- **Driving force:** token-usage; secondary: simplicity
- **Severity/source:** medium; operator correction on 2026-10-27 during maintenance after a ZCode-runtime backlog item was selected in a Codex session. The origin item explicitly scopes its reproduction to the ZCode desktop runtime (`docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md`, “Environment context”). The user stopped work before any plan or execution artifact was written; the empty authoring worktree, branch, and claim were removed.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `agent type`, `different agent`, `runtime-specific`, `agent affinity`, and `cross-agent`. Nearest hit: `docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md` concerns deriving a per-session marker in ZCode, not deciding which agent type may author or execute an origin. The completed `docs/history/plans/completed/2026-09-22-agent-aware-execute-plan-skill-contract.md` defines runtime adapter profiles for execution mechanics but does not assign backlog or plan affinity.

## Problem

The maintenance authoring and execution selections do not visibly compare the current agent type with an origin's required agent type before selecting the work. In the witnessed case, an item whose environment context names the ZCode desktop runtime was selected for authoring in a Codex session. The operator stopped the run before plan authoring or execution, after setup work had begun. This risks spending authoring or execution effort in a runtime that cannot reproduce or validate the origin's behavior, and can yield a plan or result based on assumptions from the wrong agent type.

Expected behavior: before authoring or executing an origin that declares an agent-type requirement, the workflow recognizes the requirement and proceeds only when the current agent type is compatible. Work with no such requirement remains eligible across agent types. Investigate whether the origin's creator type is a valid compatibility signal or whether the origin must declare its required target explicitly; do not infer compatibility solely from the agent that filed the backlog row.

## Location

- `agents/skills/maintenance/decisions.md`, D1 and D2 selection rules
- `agents/skills/plans/SKILL.md`, authoring entry and runtime-neutral handoff contract
- `agents/skills/execute-plan/SKILL.md`, execution entry prerequisites
- Witnessing origin: `docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md`

## Suggested investigation

Compare a minimal compatibility declaration and check at the authoring/execution entry points with alternatives that keep origins runtime-neutral or route incompatible work to an agent that can satisfy it. Preserve shared runtime-neutral work as eligible everywhere. Determine where the requirement belongs, who owns compatibility evidence, and how a mismatch is recorded without adding a broad refusal gate or duplicate runtime registry.

Why not fixed now: this crosses backlog selection, plan authoring, and plan execution, and the right compatibility key (creator type versus required target type) is a design question. The operator requested investigation before implementation.
