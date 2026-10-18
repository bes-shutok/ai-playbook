# Backlog: align archive review evidence with completed implementation reviews

- **Filed:** 2026-10-17
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed closeout blocker
- **Class:** correctness + recoverability
- **Driving force:** reliability + simplicity
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, `gate_archive_ceremony`; execute-plan review completion evidence

## Problem

Archive ceremony requires a review receipt in the plan-specific `*-plan-review-<slug>-exec-r<N>.md` series for every completed plan. A completed implementation review can exist and pass its review gate yet fail to satisfy archive ceremony when it is recorded under a different review artifact identity or is not bound to the plan's final bytes. The closeout then blocks after implementation and review are complete, even though the missing artifact may be reconstructible from the actual review evidence.

This differs from the deferred legacy-filename issue: there the valid receipt exists under an older supported identity; here the gate has no matching plan-specific execution receipt.

## Evidence

- `scripts/done_sweep_gates_lib.py`, `_has_exec_review_record` and `gate_archive_ceremony`, require a filename containing `-plan-review-`, the archived plan slug, and a trailing `-exec-r<N>` token. On absence, the refusal explicitly permits a review of the plan's final bytes or a marked reconstruction.
- `docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md`, Terms and Outcome, identifies the execution-completion receipt as a separate archive-certification artifact; Task 1 separates its namespace from staged reviews but does not replace the archive-coverage requirement.
- `agents/skills/execute-plan/SKILL.md`, completion evidence, permits a marked reconstruction with re-verification evidence when no claimed review receipt exists.
- The observed closeout sequence had a passing implementation review but no discoverable receipt in the archived plan's required series; the gate stopped the archive closeout.

## Expected

Determine whether the archive gate can safely recognize the completed implementation review as execution evidence when it binds to the final plan and implementation bytes, or whether execute-plan should consistently produce a separate plan-specific receipt. Preserve evidence that the exact final plan was covered. Keep archive certification for executed plans and retain the rejected-plan exemption.

## Immediate workaround

Before archiving, produce the actual execution-review record for the plan's final bytes using the established review workflow. If the review occurred but its receipt is unavailable, add a clearly marked reconstruction that cites the surviving review evidence and records re-verification against the final plan and implementation bytes; do not invent findings or claim a review that did not happen. Then rerun the archive-ceremony gate. This follows the remedy emitted by `gate_archive_ceremony` and the reconstruction duty in `execute-plan/SKILL.md`.

## Rejected alternatives

- Remove the execution-review requirement: rejected because the completed archive-ceremony plan explicitly retained execution evidence as protection against certifying unchecked or unreviewed work (`docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md`, Outcome).
- Treat any code-review receipt as sufficient by filename alone: rejected because archive evidence must establish coverage of the archived plan's final bytes (`scripts/done_sweep_gates_lib.py`, `gate_archive_ceremony`; `agents/skills/execute-plan/SKILL.md`, completion evidence).
- Reconstruct a receipt without surviving review evidence and re-verification: rejected because that would fabricate execution evidence (`agents/skills/execute-plan/SKILL.md`, completion evidence).
- Fix only the legacy filename grammar: rejected because the adjacent deferred item addresses an existing receipt with a legacy name, while this witness has no matching plan-specific execution receipt (`docs/history/backlog/deferred/2026-10-09-archive-ceremony-legacy-exec-review-name.md`).

## Source

- Observed during a completed implementation plan's final closeout on 2026-10-17; the archive gate refusal names the required receipt pattern and sanctioned reconstruction remedy.
