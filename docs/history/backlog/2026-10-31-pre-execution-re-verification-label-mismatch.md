# Backlog: pre-execution re-verification label mismatch

Driving force: code-quality. The pre-execution re-verification pointer in `agents/skills/maintenance/state-file.md` names its duty by a label ("pre-execution re-verification") that appears nowhere in the owning module `agents/skills/maintenance/template-authoring.md`, so a reader grepping the target for the label finds nothing. Pre-existing (predates the pointer re-homing landed by docs/history/plans/2026-10-29-execute-plan-claim-procedure-pointer.md); found as a non-blocking candidate in that run's Step 1.2b intermediate review. Remedy: either rename the label in the referencing docs to wording the owning module uses, or add the label to the owning module's duty heading.

Cluster: docs/history/backlog/2026-10-31-template-split-residual-pointers.md
