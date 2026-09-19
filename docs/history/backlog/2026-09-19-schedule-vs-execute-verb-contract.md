# Backlog: schedule-vs-execute verb contract for interactive asks

Captured: 2026-09-19 (source: cross-session friction audit - user-correction mining over 1,776 typed prompts, 2026-07-17 → 09-19)
Status: open
Priority: medium

Workflow: backlog

## What was witnessed

The largest user-correction theme in the corpus (~20 corrections, Jul 30 → Sep 17, nearly all in this repo): scheduling asks executed inline, and loop asks treated as one-shots. Verbatim: "stop I asked you to reschedule the task, notto do it right now" (Aug 8); "you were supposed to schedule the task not execute it" (Aug 11); "you r job was to schedule the execution, not to run it... give me the updated prompt that will avoid the same issue again" (Aug 12); "Why didn't you schdeule the next execute-plan? Is there any issues with the current maintenance skill?" (Sep 13); plus repeated time-format corrections ("no, the time should be 12am 30 minutes this night"). The user compensated by hand-patching prompt templates with `{schedule_time}` placeholders and standing pre-authorization boilerplate.

The maintenance skill's 2026-09-13+ rewrite (dispatch ladder, re-arm-on-touch, guards) hardens automation-fired turns, but the interactive boundary is still unpinned: a typed "Schedule at HH:MM ..." can be read as do-it-now; nothing in the trigger section distinguishes scheduling verbs from execution verbs.

## Suggested fix

Add a verb contract to the maintenance SKILL.md trigger section (and a one-line standing rule in the repo AGENTS.md): "schedule at HH:MM" ⇒ create/patch the automation only, echo back the automation id and its next fire time, never execute the payload inline in the same turn; "run/execute now" ⇒ execute; "resume/re-arm the loop" ⇒ state-file re-arm per the existing recipe. Ship the proven `{schedule_time}`/`{backlog_item}` template (already in productive use by the scheduler's own children) into the runtime overlay so the user stops hand-pasting it.

## Acceptance

- Zero schedule-vs-execute corrections after the pin lands (next mining pass over corrections).
- The template lives in the overlay; a fresh interactive session given "Schedule at 11:47 ..." creates the automation and stops, without executing inline.
