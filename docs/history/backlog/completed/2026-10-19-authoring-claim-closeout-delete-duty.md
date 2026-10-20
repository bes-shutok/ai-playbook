# Backlog: authoring-claim closeout delete duty never runs; closed claims accumulate on the consult surface

- **Filed:** 2026-10-19, operator-directed registry cleanup + same-session investigate pass
- **Status:** covered (docs/history/plans/2026-10-20-authoring-worktree-landing-shape.md)
- **Workflow:** backlog
- **Priority:** high
- **Cluster:** docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md (same defect class: terminal-state artifacts the closing boundary leaves behind)
- **Cluster:** docs/history/backlog/2026-10-20-authoring-worktree-landing-shape.md (shared plans Final Step closeout surface; a different omitted terminal duty)
- **Cluster:** docs/history/backlog/2026-10-21-plans-authoring-claim-marker-contract.md (shared plans/template authoring-claim lifecycle; marker lifetime and registry-file closeout are distinct duties)
- **Cluster:** docs/history/backlog/2026-10-14-authoring-worktree-create-path.md (shared plan-authoring lifecycle; worktree creation duty)
- **Cluster:** docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md (same artifact class: claim files outliving their session)
- **Cluster:** docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md (same defect class: terminal-state artifacts the closing boundary leaves behind; investigate 2026-10-20 roster)
- **Origin class:** observed recovery gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/template-authoring.md` (AUTHORING CLAIM paragraph, the two-deletes arm); `agents/skills/plans/SKILL.md` (Final Step authoring-closeout handoff); `agents/skills/maintenance/SKILL.md` (Step 1 survey / D2 authoring-claim consult)
- **Driving force:** reliability (the consult surface must not report dead sessions as occupied targets)

## Problem

The AUTHORING CLAIM duty owns two deletes (at the done closeout and on an owned stand-down), but no closeout path that actually runs carries the delete step: the plans skill's Final Step handoff does not list it, and the done runner has no claim step. Observed 2026-10-19: the primary registry `docs/tmp/authoring-claims/` held 24 claim files of which 21 were residue: 18 whose plans had landed and archived (authored 10-08 through 10-13), one whose plan had landed and re-dated under a different title, one whose target plan had been rejected out of the lifecycle, and one for a plan that never existed. The 2026-10-18 done-final-only-learn-intermediate closeout closed its own claim in place (writing CLOSED into the `updated:` line) instead of deleting the file, which is the operator-visible failure that surfaced the accumulation.

## Expected

The delete arm runs mechanically where closeouts already run: the plans Final Step's authoring-closeout checklist names the claim delete (with the duty's ownership re-check), and the maintenance survey/D2 consult reads heartbeat staleness (a claim whose `updated:` is older than the liveness cadence is not an occupied target). No new recurring sweep duty and no script change: the liveness probe already keys on a fresh heartbeat, so stale claims are inert to it; the fix is text that makes the existing delete arm and an explicit staleness reading unavoidable at the two consumption points.

## Evidence

2026-10-19 cleanup: 21 claim files deleted after per-claim target resolution (18 archived plans verified in `docs/history/plans/completed/`; one re-dated landing, `2026-10-19-worktree-rebase-feature-start-boundary.md`, matched by loose title; one rejected target; one plan that never existed). Four claims kept: a stranded-authoring witness (skill-monolith-module-extraction, plan branch-only), two in-flight authorings, one closeout-pending claim with a two-hour heartbeat. The plans skill's integration section states the delete duty ("this skill deletes its claim at closeout and on an owned stand-down") and the duty text owns "the deletes at closeout (the done handoff) and on a refusal stand-down", but no closeout checklist in either skill names the delete step.

## Why not fixed now

The text fix spans three skill files plus a consult-semantics decision (which staleness cadence the survey reading cites), which is authoring work with review; the operator-directed cleanup removed the accumulated residue, and this row tracks the prevention so the accumulation does not regrow.

## Source

- Observed 2026-10-19 while cleaning the registry per operator direction; the in-place-closed claim of the 2026-10-18 done-final-only-learn-intermediate authoring is the named witness.
