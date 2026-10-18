# execute-plan EXECUTION CLAIM paragraph names a dangling procedure-of-record

Status: open
Cluster: 2026-10-11-plan-authoring-done-closeout (r2 verification finding N2; same class as the plans-side pointer re-homed in that run's r1 finding F3)

The Execution claim registration step in `agents/skills/execute-plan/SKILL.md` names "the EXECUTION CLAIM paragraph in `agents/skills/maintenance/prompt-templates.md`, the procedure of record". The 2026-10-10 prompt-template split moved that paragraph to `agents/skills/maintenance/template-execution.md`; `prompt-templates.md` contains zero EXECUTION CLAIM occurrences, so the pointer is dangling.

Fix: re-home the pointer to `agents/skills/maintenance/template-execution.md` (one-word-class edit, mirroring the plans-side re-home landed by the plan-authoring-done-closeout execution run). Verify no other prompt-templates.md pointers to split-out paragraphs remain (`rg 'prompt-templates.md' agents/skills/ | grep -v template-`).

Evidence: plan-authoring-done-closeout execution r2 record (docs/history/reviews/2026-10-11-plan-authoring-done-closeout-code-review-r2.md, finding F2), corroborated by agents/skills/maintenance/templates-CHANGELOG.md.
