# Execute-plan prior-gate signal must bind to plan identity and reclassify on objective switch

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-29-execute-plan-prior-invocation-scope-leak.md

## Gist TLDR

Invocation detection's signal E ("Prior gate: user already chose execute-plan in this session") is a session-wide signal with no plan identity and no objective binding, and the algorithm lets it classify a brand-new user message before any check of whether the user changed objectives. Witnessed 2026-09-29: a switch from executing a consumer plan to finishing and merging an authoring branch was classified as execution; an implement worker and runtime claim started without current authorization. Fix: bind the carried choice to the plan it authorized and reclassify every new message first - a clear switch to authoring, review, cleanup, or merge supersedes the prior execution choice unless the message explicitly resumes execution; continuation within the same active run is unchanged.

## Outcome + Gate delta

The prior-choice signal exists to avoid re-asking between steps of one active run; this plan keeps that property and closes the leak:

- Signal E in the invocation-detection table becomes scoped: the Signal cell stays `**Prior gate**`; the How-to-match cell becomes "User already chose execute-plan (option 1) in this session **for the plan currently in play**; the choice carries that plan identity and never classifies a message about a different plan or a different objective." The carried choice records the plan it authorized; it never applies to a different plan path or a different objective.
- The `invoked = false` definition line is amended to match: "`invoked = false` when none of A-E match, **or when an objective switch supersedes a signal-E-only match per the reclassification precedence below**", and the false-examples list gains the switch class - without this, the retained "only when none of A-E match" quantifier would force `invoked = true` on any E match and reinstate the leak through the definition line itself.
- The second statement of the same signal in the "Execute-plan already chosen" section (legacy list item 3, "Prior gate choice in the same session") is scoped identically: "Prior gate choice for the plan in play in the same session, subject to the reclassification precedence (see table E)" - the stale-semantics copy left behind by a scoped row E would otherwise re-advertise the unscoped alias route.
- Reclassification precedence: signals A-D (verb+plan, verb+path, hyphen/slash, skill attachment) are evaluated on the current message first. When only E matches, the detector must check the current message for an objective switch: a clear request to author, review, finish authoring, clean up, merge, or otherwise manage a plan branch supersedes the prior execution choice (the message classifies as not-invoked and the plan-path gate or normal workflow applies), unless the message also explicitly resumes execution (`continue executing`, `run the next task`, or equivalent). "Finish the plan" alone is ambiguous between finishing authoring and executing tasks and never defaults to execution.
- Within one explicitly selected plan run, nothing changes: step-continuation messages that neither switch objective nor name a different plan keep `invoked = true` without a repeated gate.
- Commit authorization text is untouched: an execute choice still never implies unrelated repository actions.

Out of scope: the three-way gate's own options, the plan-path gate's path list, and the commit/push authorization rules.

## Terms

- **Prior gate choice**: the user's selection of execute-plan at the three-way gate, carried as signal E.
- **Objective switch**: a new user message whose request is authoring, review, branch cleanup, merge, or another plan-management action rather than executing the plan's tasks.
- **Plan in play**: the plan the carried choice was made for; signal E records this identity when the choice is made.

## Assumptions

- The fix is skill prose only: invocation detection is a decision procedure an agent runs, not driver code; no script or test harness in the repo executes it.
- Worked examples are the deterministic witness the origin item asks for: the repo's convention for behavioral detector rules is example tables (the section already has a worked-examples table and a misreads list), so both sides of the fix land as new rows rather than a separate test file.

Decision points requiring a grill: none - the origin item's Fix shape prescribes all four arms (preserve in-run continuation, bind to plan identity, reclassify before continuing, deterministic examples on both sides); no user-visible behavior beyond the leak closes.

### Task 1 - Invocation detection: scope signal E and add reclassification precedence

- [ ] In `agents/skills/execute-plan/SKILL.md`, the invocation-detection signal table, rewrite row E per the Outcome bullet (Signal cell unchanged; How-to-match cell scoped as prescribed there). [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same section, amend the `invoked = false` definition line and false-examples list per the Outcome bullet (the switch class becomes a first-class false outcome). [class: IMPLEMENTATION_REQUIRED]
- [ ] In the "Execute-plan already chosen" section, scope legacy list item 3 per the Outcome bullet. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same section, after the `invoked = false` definition line, add a reclassification-precedence paragraph: evaluate A-D on the current message first; when only E matches, inspect the message for an objective switch (authoring, review, finish-authoring, branch cleanup, merge, or other plan-management phrasing) - a clear switch classifies the message as not-invoked (the plan-path gate or the switched-to workflow applies) unless the message explicitly resumes execution; ambiguous phrasing such as "finish the plan" alone never defaults to execution. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the worked-examples table, add three rows: (author-and-merge) a message asking to finish authoring and merge a plan branch after a prior execute choice - `invoked: false` - action: plan-path gate or authoring workflow, no implement worker, no claim; (explicit resume) a message saying continue executing the same plan's next task after a prior execute choice - `invoked: true` - action: proceed without re-asking; (different plan) a bare path to a different plan after a prior execute choice - `invoked: false` - action: three-way gate (different plan). [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Validation

- [ ] All checks in Validation Commands pass from the worktree root. [class: REPOSITORY_TEST]

## Evaluation Criteria

- Signal E is scoped to the plan in play and states the identity carry.
- The reclassification precedence exists, orders A-D before E, requires explicit resume after an objective switch, and never defaults ambiguous phrasing to execution.
- All three deterministic example rows exist (author-and-merge stays authoring-only; explicit same-plan resume proceeds gateless; a bare path to a different plan after a prior choice hits the three-way gate).
- The in-run continuation contract and the commit-authorization paragraph are unchanged.

## Review Scope

Files: `agents/skills/execute-plan/SKILL.md` (the invocation-detection signal table row E, the `invoked = false` definition line and false-examples list, the new reclassification paragraph, the "already chosen" section's legacy list item 3, and the worked-examples table only). Contract files referenced read-only: origin backlog item.

## Validation Commands

Run from the worktree root:

1. `test "$(grep -cE '^\| E \|.*for the plan currently in play' agents/skills/execute-plan/SKILL.md)" = "1" && echo row-e-scoped` - the scope phrase lives in row E specifically, exactly once (subsumes the rewrite-in-place check).
2. `grep -n "or when an objective switch supersedes a signal-E-only match" agents/skills/execute-plan/SKILL.md` - the `invoked = false` definition line itself carries the amendment (the literal is unique to that line, so the paragraph alone cannot satisfy it).
3. `grep -n "never defaults to execution" agents/skills/execute-plan/SKILL.md` - the ambiguous-phrasing rule is present.
4. `grep -n "plan-path gate or authoring workflow" agents/skills/execute-plan/SKILL.md` - the author-and-merge example row exists.
5. `grep -n "continue executing the same plan" agents/skills/execute-plan/SKILL.md` - the explicit-resume example row exists.
6. `grep -n "subject to the reclassification precedence" agents/skills/execute-plan/SKILL.md` - the legacy restatement (already-chosen list item 3) is scoped to the precedence.
7. `grep -n "three-way gate (different plan)" agents/skills/execute-plan/SKILL.md` - the different-plan example row exists (the action cell is prescribed with this row-unique literal; bare "three-way gate" already occurs elsewhere in the file).
