# Backlog: allow intentional removal of branch-added documentation

- **Filed:** 2026-10-14, consumer feedback
- **Status:** covered (docs/history/plans/2026-10-17-dirt-gate-removal-only-cleanup-passing.md)
- **Workflow:** backlog
- **Priority:** high
- **Cluster:** docs/history/backlog/2026-10-16-worktree-done-boundary-primary-gate-block.md, docs/history/backlog/2026-10-16-done-setup-after-task-edits-foreign-staging-trap.md, docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md, docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md, docs/history/backlog/2026-10-06-done-boundary-review-candidates.md, docs/history/backlog/2026-10-12-done-interrupted-manifest-state-classification-certification-residuals.md
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** simplicity + maintainability
- **Skill/step:** `agents/skills/done/SKILL.md`, Step 3; dirt-regression gate
- **Environment:** consumer repository, repository copy of the closeout runner, 2026-10-14
- **Suspected root area:** dirt-regression gate's removal-only hunk classification
- **Severity:** medium; the gate stopped an authorized documentation cleanup before commit
- **Consumer urgency:** Consumer projects that run this shared skill need a sanctioned path for intentional documentation removals; the skills-repo personal priority profile must not park or defer the fix as formal-hardening for the skills repo alone.
- **Source:** user-directed cleanup of duplicated artifact-location and workflow guidance in active project documentation; commit gate refusal during closeout. Capture hygiene: `scan-public-hygiene --files` passed.
- **Cluster:** docs/history/backlog/2026-10-17-done-plan-removal-only-regression-block.md

## Problem

A user-directed documentation cleanup removed workflow details that belong to shared skills. The dirt-regression gate classified a removal-only hunk of branch-added documentation as a regression and refused the landing. The content removal was intentional and required to remove duplicated, configuration-dependent guidance.

The change passed after a concise, useful boundary statement was added inside the same rewritten section. That workaround made the edit forward-looking to the classifier, but requires replacement prose for a valid removal and can pressure authors to retain unnecessary text.

## Expected

Allow a scoped, intentional removal of branch-added documentation to pass without requiring replacement prose, while continuing to reject an accidental restoration of base-era content over newer branch content.

## Suggested fix

Evaluate whether the dirt-regression gate should exempt explicitly claimed documentation-only removals or use a narrower signal for actual reverts. Consider removing the check if investigation shows its valid-removal false positives cannot be addressed without adding more closeout machinery. Keep the fix-class shape: remove the false positive or add a sanctioned exit, without adding refusal paths.

## Why not fixed now

The project documentation cleanup was completed with the bounded same-section rewrite. Changing the shared closeout gate is outside that consumer task and needs focused analysis of its revert-detection value and safeguards.

## Dedup probe

Searches of open backlog filenames and problem text for `dirt-regression`, `removal-only`, and `base-era` found the open declared-deletion issue and an unrelated gate-display issue. The declared-deletion issue concerns `git add` rejecting an absent tracked path, not the dirt-regression classifier. The nearest same-gate item, `2026-10-05-done-dirt-regression-blocks-reviewed-fix.md`, is closed because its proposed API change was not valid; this item records a distinct, user-directed documentation correction that the gate refused.
