# Backlog: plans rule 22 pin/text mechanical audit should also run at authoring time, before the first review round

Status: open
Priority: deferred (formal-hardening triage 2026-09-21, user directive: on this personal/pet repo formal fixes are not a priority — no witnessed failure; gates, naming/wording pins, vacuity audits and hypothetical-input hardening auditing other gates defer by default. Revive only on a witnessed scanner/gate mis-fire or a project-priority-profile change. Per-project profiles: see 2026-09-21-project-priority-profiles backlog.)
Workflow: backlog
Date: 2026-09-20
Class: plans-skill Validation Commands authoring-rule gap (rule 22 scope)

## Observed vs expected

During an authoring run (four review rounds, 2026-09-20), the plan's prescribed insert text and its
own gate pattern disagreed at the byte level: the Task 2 insert carried backslash-escaped backticks
inside an inline-code span while the G2c gate's double-quoted grep decoded to real backticks, so a
verbatim insert could never satisfy its own gate (`classification`: validation-span-escaping-mismatch).
Rule 22's mechanical audit (extract every pinned span and verify it occurs exactly once in the plan's
prescribed snippets, plus `bash -n`) is scoped to "after every fold", so it first ran only after round
r1, and the reviewer caught the mismatch before the audit did. Expected: the audit also runs at
authoring time, before the first review round launches, as part of the same authoring-time execution
record that already proves the validation block RED-today and `bash -n` clean (rules 19 and 29).
The r1 blocking finding was mechanically detectable from the plan bytes alone.

## Suggested fix

Extend plans SKILL.md Validation Commands authoring rule 22 (or the authoring-time execution record
bullet it hangs on) to require the pin/text span audit before the first review round, not only after
folds; the audit is cheap (one extraction pass over the plan bytes) and every gate span it checks is
already present at authoring time.

## Suspected root area

`agents/skills/plans/SKILL.md` Validation Commands authoring rules (rule 22's "after every fold"
scope; the Plan Quality Gate's pre-round checklist has no span-audit step). Witness environment:
repo-local authoring run, 2026-09-20.
