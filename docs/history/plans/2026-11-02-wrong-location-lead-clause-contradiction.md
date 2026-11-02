# Plan: Amend the Wrong Location lead clause alongside the project-local convention

Backlog origin: docs/history/backlog/2026-11-02-wrong-location-lead-clause-contradiction.md
Driving force: consistency
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-wrong-location-lead-clause-contradiction-pa1a342b2-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: 2026-11-02-wrong-location-lead-clause-contradiction.md (session sess_2e80006b-4108-4c79-9fc9-b6cfb4fd26ae)

## Terms

- Wrong Location section: the "### 4. Wrong Location" section of `agents/skills/how-to-write-skills/SKILL.md`.
- Lead Solution line: the section's lead "**Solution:**" line (line 424 at authoring time), comprising the resolve-paths directive ("resolve paths from `user_facts_path` (`skills_repo_path`, local agent mirrors);") and the hardcode prohibition ("do not hardcode one vendor directory as canonical in skill text:").
- Facts-document rule: the Wrong Location section's directive that conventions be documented in user or repo facts rather than skill bodies; the lead line's resolve-paths fragment is a separate facts-directed directive, named explicitly wherever it is amended.
- Clause amendment: the Task 1 bullet of the project-local-skills plan that amends the section's "document the convention in user or repo facts, not in generic skill bodies" clause.
- The project-local-skills plan: `docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md`.

## Why

The project-local-skills plan's r2 review flagged that its clause amendment leaves the Wrong Location section's lead Solution line unamended. Beside the new vendor-path convention, two readings of that line can send a reader back to per-project facts: the hardcode prohibition read as forbidding documenting the vendor path, and the resolve-paths directive read as requiring the path from user facts. Either reading contradicts the documented project-local path. The referenced plan's Task 1 must cover both fragments in the same edit.

## Gist & Examples

TLDR: the project-local-skills plan's Task 1 gains one acceptance bullet covering the Wrong Location section's lead Solution line, so the consistency finding is fixed where it will execute.

Today, Task 1 amends only the "document the convention..." clause; the lead Solution line (the resolve-paths directive plus the hardcode prohibition) would stay as-is, and a reader could read either fragment as forbidding or redirecting the very `.agents/skills/` path the amended section documents. After this plan executes, the executing session amends both fragments of the lead line in the same edit, scoping the facts-document rule to installation-specific values while the tracked project-local skill path stays documented in the section.

## Outcome

Executing the project-local-skills plan leaves no clause in the Wrong Location section that directs readers away from the documented project-local path convention.

- The lead Solution line and the clause amendment land in one edit, so the section never carries a half-amended state.
- The facts-document rule stays scoped to installation-specific values, not to the tracked project-local path convention.

Gate delta: none (no refusal classes, gates, fences, protocol layers, or schema fields added or removed; one acceptance bullet added to an existing plan task).

## Assumptions

- assume the lead Solution line is still unamended in `agents/skills/how-to-write-skills/SKILL.md`; basis: line 424 read 2026-11-02, and the project-local-skills plan's Task 1 is unexecuted (the referenced plan file's history ends at its certification checkpoint d436ffd24, which added it, and `git log -- agents/skills/how-to-write-skills/SKILL.md` shows no commit implementing Task 1).
- assume the plan-amendment arm (not the executing-session-scope arm) is the operative fix; basis: the backlog row names it first and it keeps the fix reviewable inside the referenced plan's existing review record.
- assume the referenced plan is still unexecuted when this plan executes; basis: its plan file and the SKILL.md are unchanged since certification (verified 2026-11-02). If it has executed by then, the executing session applies the residual as a plan-related extension instead, per the backlog row's alternative arm.
- assume the amended bullet's absence from the referenced plan's Done when enumeration is a known, tracked gap class; basis: open row `docs/history/backlog/2026-11-02-plan-done-when-enumeration-gap.md` tracks the same referenced-plan gap class for the existing clause-amendment bullet.

Decision points requiring a grill: none remain.

## Evaluation Criteria

Quality dimensions:

- Consistency: the amended Task 1 bullet names both fragments of the lead Solution line, the same-edit timing, and the scoped facts-document rule (the scoping may cite the clause-amendment bullet's installation-specific scoping by reference rather than restating it).
- Traceability: the bullet carries the r2 finding's substance without in-plan review-state prose.
- Gate pass: `python3 scripts/plan_readiness.py` over this plan exits 0; the referenced plan's readiness gate stays green after the edit.

Done when:

- The referenced plan's Task 1 carries the extended bullet naming both lead-line fragments and the same-edit timing, and the origin row's Status is flipped to covered by the same change set.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-wrong-location-lead-clause-contradiction.md --pre-round` and the referenced plan's equivalent both exit 0.

Ship when:

- None (fully repository-verifiable).

## Review Scope

- Explicit must-fix: `docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md` (Task 1 acceptance bullets only), `docs/history/backlog/2026-11-02-wrong-location-lead-clause-contradiction.md` (Status line only) (Task 1)
- Production: none (plan-text amendment; no skill bodies)
- Tests: none beyond the pinned repository gates (Task 1)
- Out of scope: `agents/skills/how-to-write-skills/SKILL.md` and any other skill body (per Standing constraints); the referenced plan's tasks other than Task 1

## Validation Commands

- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-wrong-location-lead-clause-contradiction.md --pre-round` (authoring-time readiness, non-blocking warnings only)
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md --pre-round` (referenced plan stays well-formed after the amendment)
- `git show --name-only --format= HEAD` (run after Task 1's commit) shows exactly `docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md` and `docs/history/backlog/2026-11-02-wrong-location-lead-clause-contradiction.md`.

## Standing constraints

- This plan amends plan text only; it never edits `agents/skills/how-to-write-skills/SKILL.md` or any other skill body.

### Task 1: Extend the referenced plan's clause-amendment bullet to the lead Solution line

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md`
- `docs/history/backlog/2026-11-02-wrong-location-lead-clause-contradiction.md`

- [ ] The project-local-skills plan's Task 1 gains one acceptance bullet, placed directly after the existing clause-amendment bullet, covering the Wrong Location section's lead Solution line: both fragments (the resolve-paths directive and the hardcode prohibition) are amended in the same edit as the clause amendment so neither reading contradicts the documented project-local path convention. [class: IMPLEMENTATION_REQUIRED]
- [ ] The new bullet names the facts-document rule's installation-specific scoping by reference to the clause-amendment bullet's scoping (for example "same scoping as the clause-amendment bullet above") rather than restating the clause's text; given the amended section, expects no clause in it to direct readers away from the documented project-local path. [class: IMPLEMENTATION_REQUIRED]
- [ ] The new bullet follows the referenced plan's existing checkbox shape (class tag, given/expect form) and does not duplicate the clause-amendment bullet's clause text. [class: IMPLEMENTATION_REQUIRED]
- [ ] The origin backlog row's `Status: open` line is flipped to `Status: covered (docs/history/plans/2026-11-02-wrong-location-lead-clause-contradiction.md)` in the same change set. [class: IMPLEMENTATION_REQUIRED]
- [ ] The referenced plan's other tasks, metadata block, and review-record citation stay unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect pass: `python3 scripts/plan_readiness.py docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md --pre-round` exits 0 (warnings allowed); `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0 over the added lines since the base (working tree included); `git show --name-only --format= HEAD` (run after the task's commit) shows exactly the two files named in the commit bullet. [class: REPOSITORY_TEST]
- [ ] Commit: `plans: extend wrong-location clause-amendment task to the lead Solution line`. [class: IMPLEMENTATION_REQUIRED]
