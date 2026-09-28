# Execute-plan must revalidate invocation scope after a task change

- **Filed:** 2026-09-29
- **Status:** done (2026-09-30; executed+landed via docs/history/plans/completed/2026-09-30-execute-plan-prior-choice-scope-binding.md, exec review r1 ready=yes zero blocking)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** An earlier execute-plan choice can leak into a later, materially different authoring or landing request and start implementation without current authorization.
- **Origin class:** consumer-feedback
- **Driving force:** reliability; secondary usability
- **Source:** interactive plan-workflow correction, 2026-09-29. A user switched from executing a consumer plan to finishing and merging an ai-playbook plan-authoring branch. Invocation detection's session-level prior-choice signal was applied without checking whether the current objective was still execution. The user clarified that the request was authoring and merge only; an implement worker and runtime claim had already been started.

## Problem

The execute-plan invocation detector treats a prior execute-plan gate choice as a session-wide signal. That prevents repeated confirmation during one execution, but it can outlive the plan or objective it authorized. A later request to author, review, merge, or otherwise manage a different plan branch can then be interpreted as permission to execute the plan's tasks, even when the latest user message does not ask for execution. This changes the action scope and can create claims, edits, and worker activity that the current request did not authorize.

## Issue archaeology

`agents/skills/execute-plan/SKILL.md` added the `Prior gate` signal in commit `02348755` alongside invocation detection and continuous execution. Its intent is to avoid asking between steps after execute-plan was selected. The detector records no plan identity or task scope for that choice, and its algorithm lets the old choice classify later messages before considering whether the user changed objectives. No current test or plan requirement covers an authoring-only or branch-landing request after a prior execution choice.

## Fix shape

- Preserve automatic continuation within one explicitly selected plan run.
- Bind any carried invocation choice to that plan identity and active execution objective.
- Reclassify each new user message before continuing. A clear switch to plan authoring, review, branch cleanup, or merge supersedes the prior execution choice unless the current message also explicitly resumes execution.
- Add deterministic examples or tests covering both sides: author-and-merge after a prior execute choice stays authoring-only; an explicit same-plan request to continue execution resumes without another gate.
- Keep authorization for commits, merges, and pushes governed by their own rules; an execute choice must not imply unrelated repository actions.

## Rejected alternatives

- Remove prior-choice continuation entirely: rejected because it would reintroduce repeated execute-plan gates between steps of one active run.
- Treat phrases such as "finish the plan" as execution by default: rejected because they do not distinguish finishing plan authoring from executing its tasks.
- Carry execution intent across unrelated objectives until the session ends: rejected because a later user instruction can narrow or replace the task.
