# Backlog: plan-execution-no-candidate-follow-up-disposition certification residuals

Status: open
Workflow: backlog
Priority: low
Origin class: plan-review residual
Class: fix-class
Driving force: code-quality

## Problem and evidence

The r5 certification round of `docs/history/plans/2026-11-08-plan-execution-no-candidate-follow-up-disposition.md` (plan bytes sha256 36a73465f487e1e2bb29cbc6285c6cea08796e9a7cfd2cd9a7f818e07ba79c15) staged zero blocking findings and carried ten non-blocking findings, routed here per the certification-residual routing instead of forcing a fold past the round cap. Each premise was verified from disk by the staging panel:

1. Remap leaves the Class line and the hygiene-verdict home undefined (Medium, r5 F1, risk+testing): the finding-shaped field remap for conversion rows covers Problem statement, Exact location, Suggested fix, Why-not-fixed-now, and severity/source-reference, but leaves no defined value for the mandated Class line on a promotion-row investigation lead (the closed fix-class/fence-class taxonomy describes failed-closed behavior, not future-work leads) and no recording home for the capture hygiene passing verdict once the source-reference field is substituted away; misclassified lead origins distort later authoring Gate-delta pricing.
2. Egress widening misses the second section naming (Medium, r5 F2, risk): the widening instruction names only the archive-egress clause's inline section naming, while the cited-receipt paragraph in the same plans-skill bullet carries a second promoted-only naming of the disposition section, so a rejected-only completion can read its own mandated append as a forbidden body edit and skip it silently.
3. Gist Before example rejected drift (Medium, r5 F3, contract-docs): the Before example says the witness plan "ends with all candidates rejected" while the witness record shows candidates failed to qualify or stayed unproven, colliding with the Terms' rejected disposition (ruled-out options spawn nothing) and misstating the witness.
4. Gate delta itemization and file attribution (Low, r5 F4, design-simplicity+contract-docs): the Gate delta grouping omits two operative additions (the completion-pass cross-reference clause and the receiving-review Scope-line carve-out) and groups the receiving-review sentences under the execute-plan skill.
5. Gist TLDR force mismatch (Low, r5 F5, correctness-completeness): the TLDR's why-phrase names "for reliability" while the header declares code-quality, contradicting the Gist rule that the opening line names the declared force.
6. Rejected ruling vs disposition term drift (Low, r5 F6, testing): the tasks say "rejected ruling(s)" while Terms defines only "rejected disposition", leaving two names for one concept.
7. Disposition term candidate narrowness (Low, r5 F7, contract-docs): the follow-up disposition definiens scopes to "candidate work" while the operative duty covers all still-viable follow-up work named in the run's own outputs (feature notes, recommendations, unmet objectives are not necessarily candidate work).
8. Parked-record idempotency wording contradiction (Low, r5 F8, risk): for a worktree-arm parked record committed without its tracked landing path, clause one declines to count it as recorded while clause two forbids re-filing, leaving the disposition state ambiguous in exactly the resumed-run state the bullet settles.
9. Promoted-row Exact location allows non-durable run outputs (Low, r5 F9, risk): the remap points Exact location at the run outputs naming the lead with no durability requirement, so a lead named only in session-tmp output leaves a dangling evidence pointer after Phase 5 cleanup.
10. Promoted-row forward reference (Low, r5 F10, design-simplicity): promoted origins filed before the archive commit carry the archived plan path as source reference before the `git mv` materializes it, so a run aborted between filing and archive leaves rows pointing at a nonexistent path.

## Correction

At plan execution, the executor folds items 1-8 into the corresponding task work as one-clause repairs (a Class-line substitution clause and a verdict-home clause in the remap bullet; both inline namings widened in the plans-skill bullet; the Before example restated to the evidence-backed stopping point arm; the Gate delta grouping completed and file-attributed; the TLDR why-phrase aligned to code-quality; "rejected ruling" normalized to the Terms term or one Terms alias line; the definiens widened to named follow-up work; a resolving clause for the non-compliant parked record), and records items 9-10 as execution-time guidance in the same change (an Exact-location durability clause; a both-paths source-reference rule), all within the plan's existing prose-duty register and the skill-text anti-growth rules.
