Status: open
Priority: low
Workflow: backlog
Class: consolidation completeness (a consumer entry point restates canonical-owned prose instead of pure reference plus literals)
Driving force: simplicity

# plans Phase 0 restates canonical rationale and the Writing marker-keying rule instead of pure reference plus literals

**Exact location:** `agents/skills/plans/SKILL.md` Phase 0, Step 0.1 (the "a worktree's gitignored directories start empty, so copy ... in before any gate or plan-file write" rationale restatement) and Step 0.2 (the marker-keying sentences restating the **Writing** section's skill-gate marker recipe: "the skill-gate marker recipe keys its project root from the write target (see **Writing** above): refresh the marker against the worktree root before each write, never against the primary checkout"). Appended r4 (2026-09-28): the Phase 0 intro sentence's parenthetical lifecycle summary ("(create the ad-hoc worktree on its own branch off the per-project base branch, work inside it, land under the lock, transfer artifacts out, delete only after verification)") belonged to this same restatement family; it was dropped in the r4 pass (see Source reference), leaving Steps 0.1 and 0.2 as this item's open remainder.

## Problem

The worktree-first consolidation's own Evaluation Criterion sets the bar: "no target file restates the recipe's steps; each entry point carries only a reference plus its own payload-critical literals." plans Phase 0 still carries two restatement shapes the criterion names: Step 0.1 restates the canonical section's transfer-in rationale (why a worktree's gitignored directories start empty and what must be copied), which the canonical **Transfer-in implementation** owns; and Step 0.2 restates the **Writing** section's marker-keying rule instead of referencing it with the phase-specific literal only (writes key to the worktree root). Each restated copy is a second home for a rule that can drift away from its owner.

## Observed versus expected

- Observed: Phase 0 carries reference-plus-restatement: the rationale sentence and the marker-keying mechanics both reappear in phase prose beside their owning homes.
- Expected: Phase 0 carries reference-plus-literals: one sentence naming the canonical transfer-in implementation and one naming the Writing section's keying rule, each with only the phase's own literal (the facts transfer-in; the worktree-root write target), no restated rationale or mechanics.

## Suggested fix

Slim Step 0.1 to the reference plus the facts-transfer-in literal, and slim Step 0.2 to a one-sentence pointer at the **Writing** marker recipe with the worktree-root literal; run the plans-body pins and the hygiene gates in the same edit (a pinned span reworded updates its owning pin in the same change).

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r1.md, round r1, finding F16 (deferred; Low). Capture hygiene: scan-public-hygiene --files pass (see execution log review-r1-receiving-review.log.md). Why not fixed now: deferred by the round's triage (further prose slimming risks regenerating findings on a just-consolidated surface; the round's fix scope was the named spans only), captured as durable backlog per receiving-review Backlog capture. Round r4 (2026-09-28, same review loop) fixed the intro-parenthetical surface named in the Exact-location append; Steps 0.1 and 0.2 remain open under the original deferral.

Dedup probe: searched the open backlog corpus for "Phase 0 restates", "reference plus literals", "plans Phase 0"; nearest item is the consolidation plan itself (landed); no existing open item owns this surface; no overlap.

Origin class: self-serving
