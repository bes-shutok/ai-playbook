# Backlog: review-loop rule 4 stop-clause anchor precision

Status: done (2026-09-08, commit ba9dbd0: anchor now "closing stop-for-direction clause"; completed-plan probe copies are frozen history, untouched)
Origin: Phase 3 code review r1 (F1, Low) of the review-pointer-wiring-polish execute-plan run, 2026-09-08
Source finding: docs/reviews/2026-09-08-review-pointer-wiring-polish-code-review-r1.md

## Finding

`agents/skills/review-loop/SKILL.md` orchestration rule 4 now reads "A fix-risk stop for user direction follows the stop clause of `receiving-review` **Fix-risk triage when fixes regenerate findings**." The anchor "the stop clause" is unnamed among several stop-for-direction mentions in that section; the behavior (loop ends iterations until the user answers; stops rather than exiting or silently backlogging) resolves only one hop away in the section's closing paragraph.

## Remedy

Anchor more precisely (e.g. "the closing stop-for-direction clause of `receiving-review` **Fix-risk triage when fixes regenerate findings**") when next touching the file. Deferred because the current wording is the plan's certified, probe-pinned text (positive probe `follows the stop clause of `receiving-review``); changing it requires a plan-digest re-cert, which is not worth it for anchor precision alone.
