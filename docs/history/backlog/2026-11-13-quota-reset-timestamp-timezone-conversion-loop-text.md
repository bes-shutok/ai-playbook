# Backlog: provider-displayed quota reset timestamps are GMT+8; the conversion recipe lives in user memory, not loop text

- **Filed:** 2026-11-13, interactive arc over the session-identity authoring run (operator indefinite-operation mandate 2026-11-12/13)
- **Status:** covered (docs/history/plans/2026-11-13-indefinite-operation-loop-continuation-duties.md)
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fence-class
- **Origin class:** operator-scoped knowledge the loop's wall arms depend on
- **Skill/step:** `agents/skills/maintenance/quota-policy.md` (Step 4 quota leg, the stop-before-exhaustion arm and the probe fallback area)

## Observed versus expected

**Observed:** both usage walls this arc surfaced unlabeled reset strings ("2026-11-13 09:49:24" and "2026-11-13 20:39:29") that are GMT+8 while the host runs WET; each conversion was performed manually from the operator-level instruction note ("treat any reset timestamp as GMT+8", re-checked 2026-07-25), which lives in user memory, not in the repository. The quota leg's stop-before-exhaustion arm converts the reset into the resume carrier's window-start minute, and the mid-run wall arm (see the same-day carrier-arm row) would do the same; a session or carrier without the user-memory note converts the displayed string as local time and arms the resume hours late or early.

**Expected:** quota-policy.md owns one conversion sentence beside the arm that consumes it: the probe's `reset_at_epoch` when the probe output is usable, otherwise convert the provider-displayed string as GMT+8 per the standing operator note (with the note's own re-check date cited), so the loop text carries its own recipe and no user-scoped dependency stands between a wall and its resume carrier.

## Reproduction evidence (trimmed)

- Two manual conversions this arc (01:49:24 WET and 12:39:29 WET), both from the user-level note; the armed carrier payload carried the conversion inline in its prompt text.

## Environment context

- zcode runtime; the display format is ZCode/Z.ai's quota-reset surfacing, unlabeled as of 2026-11-13; the operator note records the format unconfirmed-label status with a re-check clause.

## Suspected root area

The quota leg treats the displayed reset as an input but never names its timezone; the knowledge sits one scope above the machinery that needs it.
