# Backlog: plan authoring can stand down after provisioning without a charter closeout

- **Filed:** 2026-10-26, maintenance plan-authoring session
- **Status:** open
Quarantine: 2026-10-27
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** simplicity; secondary: reliability
- **Skill/step:** `agents/skills/plans/SKILL.md` Phase 0 and authoring closeout; `scripts/worktree_closeout_migrate.py` `gate-removal`
- **Cluster:** docs/history/backlog/2026-10-21-gate-removal-empty-owned-set-remedy.md (same gate-removal surface; the refusal causes differ)
- **Dedup probe:** searched open backlog filenames and Problem bodies for `authoring stand-down`, `no charter`, `missing plan`, `already implemented`, `gate-removal`, and `worktree cleanup`; nearest items are `2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md` (post-landing cleanup ownership; landed and archived) and `2026-10-21-gate-removal-empty-owned-set-remedy.md` (an existing charter with no owned review claims). This is distinct: authoring stopped before a plan file existed, so the plan-dependent removal gate could not run.

## Problem

The plan-authoring flow can reserve and provision a run before confirming that its selected backlog item still needs a plan. In the observed session, source and history checks after Phase 0 showed the requested implementation had already landed, so authoring correctly stopped without creating a plan file. The normal removal gate then returned a tool error because it requires that plan file, leaving no supported charter-based closeout for the already-provisioned worktree and branch. The operator authorized exact cleanup after reviewing the remaining artifacts.

## Expected

Confirm that the selected origin still needs plan authoring before freezing its prompt and provisioning the authoring run. If later evidence requires a stand-down after provisioning but before the first plan write, provide a bounded closeout path that preserves artifact and ownership checks without requiring a nonexistent plan charter or weakening the normal removal gate.

## Suggested direction

Trace the selection, Phase 0, and closeout sequence. Prefer moving a narrow current-actionability check before reservation and provisioning if it can use existing source-of-truth evidence. For an unavoidable later stand-down, determine whether the existing owned-artifact and exact-identity checks can support cleanup without adding a new blocker, ledger, or broad deletion path. Keep the gate fail-closed for ordinary plan closeout.

## Evidence

- Session evidence: Phase 0 created an authoring worktree and baseline; a later source/history check established the implementation already existed, and no implementation plan was authored.
- `agents/skills/plans/SKILL.md` requires Phase 0 at the start of authoring and prescribes plan-dependent removal checks for worktree closeout.
- `scripts/worktree_closeout_migrate.py` `gate-removal` returned `OUTCOME: tool_error` for the absent plan path; exact cleanup proceeded only after operator direction and separate artifact verification.
- capture hygiene: `scan-public-hygiene --files` pass; em-dash scan pass

## Why not fixed now

This session was cleaning up the specific abandoned run. Changing shared authoring and closeout behavior needs a reviewed plan and regression evidence across both the pre-provision and post-provision stand-down paths.
