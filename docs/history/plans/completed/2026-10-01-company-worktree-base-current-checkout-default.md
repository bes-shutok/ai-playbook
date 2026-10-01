# Plan: Company worktree base defaults to the current checkout

Backlog origin: `docs/history/backlog/2026-10-01-company-worktree-base-current-checkout-default.md`
Driving force: reliability (stacked-review integrity on consumer company projects)
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-company-worktree-base-current-checkout-default-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A company project whose facts pin neither `base_branch` nor `project_class` builds its run worktree off the branch the primary checkout holds at run start, so stacked review work is never stranded on the remote default's history.

- The Base-branch resolution rule gains the company arm: a repository root resolving under the user facts' `company_projects_root` defaults to checkout-flow semantics when `project_class` is absent, with the resolved branch ref and commit captured once at run start and carried through worktree creation and the run's landing path.
- A detached checkout or an unresolvable current branch stands the run down in that arm (fail closed); the origin-HEAD fallback stays exclusively the default-branch-integration arm.
- Bootstrap seeds the classification for company-scoped repos (`project_class = "checkout-flow"`) so fresh setups carry the default explicitly, with an existing or operator-pinned value untouched.
- The automated dispatch payload surfaces are audited against the amended rule with the disposition recorded, per the origin's audit-before-changing-copies direction.

Gate delta: one checked condition added to the existing base-branch resolution surface (the company-root classification arm gating which fallback derivation applies) and one bootstrap seeding default (a company-scoped repo persists `project_class = "checkout-flow"` unless present or operator-pinned); the origin-HEAD fallback is unchanged and stays scoped to default-branch-integration projects, and no refusal surface is removed - the arm adds a fail-closed stand-down (detached or unresolvable current branch) where today's derivation would silently select the remote default. Fix-class origin prices the additions: the witnessed wrong-checkout incident is the missing classification, not an over-refusal, and the origin's rejected alternative (keeping the remote-default fallback for company projects) is the defect itself.

## Terms

- Company project: a repository whose root resolves under the user facts' `company_projects_root` key; the sanctioned environment-specific carrier, never a hardcoded path.
- Company arm: the Base-branch resolution rule's classification leg that gives an absent-`project_class` company project checkout-flow semantics.
- Captured-once base: the branch ref and commit recorded at run start and carried unchanged through worktree creation and the landing path.

## Assumptions

- plans Phase 0 needs no edit: its worktree paragraph already resolves the base "by the canonical section's **Base-branch resolution rule**", so it inherits the company arm without changes. (Basis: plans SKILL.md worktree-creation paragraph, read today.)
- The scheduler payloads' landing tails (maintenance skill and zcode overlay) pin the default branch for THIS repository's scheduler landings, which are default-branch-integration by class; company projects run plans through their own sessions, whose worktree creation and landing resolve per the canonical rule. The origin's "audit the canonical payload source and generated payload producers before changing copies" is satisfied by an audit task with a recorded disposition, not by editing pinned payload text. (Basis: the landing-tail paragraphs and the pins suite's presence-and-ordering pins over the tail span; the class-conditioned clause itself is unpinned.)
- The origin-HEAD fallback span is count-pinned (exactly once, normalized) in execute-plan SKILL.md; the amendment leaves that span and its arm byte-identical and scoped to default-branch-integration projects. (Basis: the pins suite's worktree-first r3 witness needles block.)
- `company_projects_root` appears in neither target skill today, and the bootstrap seeding token is absent. (Basis: the RED canary greps, run this cycle.)
- Reconciliation with the still-open `2026-09-28-checkout-flow-landing-mismatch-guard` item (the origin's own acceptance criterion): this plan owns the interactive/canonical side (the Base-branch resolution rule's company arm); the guard item keeps owning the scheduler payload tails' landing-target binding, including the fail-closed mismatch check it demands for any divergent lane - the two acceptance boundaries are recorded as distinct in Task 3's audit, and the guard item stays open. (Basis: the guard item's body and the payload tail's class-conditioned equality clause.)
- The origin's temp-repo regression-coverage suggestion (suggested fix 6) is dispositioned as the grep-canary suite below: this is a Markdown-only contract change and the execute-plan anti-pattern table forbids scratch harnesses for such plans; the in-vivo observation is Ship-when's first bullet. (Basis: the origin's suggested fix versus the execute-plan anti-pattern table row forbidding mutation/scratch harnesses for Markdown-only plans.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The base-branch resolution rule classifies company projects (via the user facts' company projects root) into checkout-flow semantics when `project_class` is absent, so an unset base means the branch the checkout holds, never the remote default; force: reliability.

A plan authoring session for a company Jira task sat on a review branch two commits ahead of its remote tracking ref; the facts pinned no base and no class, the default-branch-integration fallback derived origin/HEAD, and the first worktree was created from a different history - the user caught it before any plan file was written. After this plan the same session classifies the repo as a company project (its root sits under the company projects root in user facts), the absent class resolves to checkout-flow, the run captures the current branch and commit once, and the worktree and the eventual landing both use that captured base. A detached checkout refuses instead of guessing, and bootstrap writes the classification down for fresh company setups so the runtime classification is a fallback, not the only line.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the company arm fires only when `project_class` is absent (an explicit value or `base_branch` always wins) and classifies by the repository root against `company_projects_root`; personal and unclassifiable projects keep today's default-branch-integration derivation byte-for-byte.
- Fail-closed: a detached checkout or unresolvable current branch in the company arm stands the run down; the origin-HEAD fallback is never reached from that arm.
- Minimalism: the pinned origin-HEAD span stays byte-identical and count-1; plans Phase 0 inherits without edits; the payload audit records a disposition instead of churning pinned text.

**Done when:**
- Every Validation Commands line exits 0, including the pins suite (the origin-HEAD count pin holds) and the absence canary proving plans Phase 0 is untouched.

**Ship when:**
- The next company-project authoring or execution run with unpinned facts captures the current branch as its base (operator-observed; external condition, no checklist item).
- Existing company repositories whose facts already carry an explicit `project_class = "default-branch-integration"` pinned under the old default need a one-time operator audit: a stale explicit value suppresses the company arm by design (explicit keys win), and the fix lives in those repos' gitignored facts files. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`

**Tests:**
- none; verification is the grep canaries and the pins suite in Validation Commands.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/plans/SKILL.md`; reason: Phase 0 defers to the canonical rule and inherits (Assumptions); byte-frozen by the absence canary.
- `agents/skills/maintenance/SKILL.md` and its zcode overlay; reason: the payload audit records a disposition (Assumptions); the landing-tail text stays untouched (presence-and-ordering pinned, not count-pinned).
- `docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md`; reason: stays open as the payload-lane residual owner (Assumptions); this plan records the distinct acceptance boundary, it does not implement or close the guard.
- `projects/.ai-playbook/agent-runtime-layout.md` and README rows; reason: no catalog change (no new skill, no path change).

## Validation Commands

```bash
grep -c "company_projects_root" agents/skills/execute-plan/SKILL.md | grep -q -v "^0$" || { echo FAIL: company arm; exit 1; }
grep -q "defaults to checkout-flow instead" agents/skills/execute-plan/SKILL.md || { echo FAIL: company arm wording; exit 1; }
grep -q "never the origin-HEAD fallback" agents/skills/execute-plan/SKILL.md || { echo FAIL: fail-closed wording; exit 1; }
[ "$(grep -cF 'resolves its default branch via the origin HEAD symbolic ref' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo FAIL: pinned span disturbed; exit 1; }
[ "$(grep -c 'defaults to default-branch-integration' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo FAIL: personal default disturbed; exit 1; }
grep -c 'project_class = "checkout-flow"' agents/skills/bootstrap-ai-playbook/SKILL.md | grep -q -v "^0$" || { echo FAIL: bootstrap seeding; exit 1; }
grep -q "company_projects_root" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo FAIL: bootstrap classifier; exit 1; }
[ "$(grep -cF 'off the base branch resolved by the canonical section' agents/skills/plans/SKILL.md)" -eq 1 ] || { echo FAIL: plans deference disturbed; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo FAIL: pins baseline; exit 1; }
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/bootstrap-ai-playbook/SKILL.md docs/history/plans/2026-10-01-company-worktree-base-current-checkout-default.md || { echo FAIL: em-dash; exit 1; }
bash scripts/scan-public-hygiene.sh --files agents/skills/execute-plan/SKILL.md || { echo FAIL: hygiene execute-plan; exit 1; }
bash scripts/scan-public-hygiene.sh --files agents/skills/bootstrap-ai-playbook/SKILL.md || { echo FAIL: hygiene bootstrap; exit 1; }
```

### Task 1: the company arm in the Base-branch resolution rule

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c "company_projects_root" agents/skills/execute-plan/SKILL.md`; covers the classification leg landed
- `grep -q "never the origin-HEAD fallback" agents/skills/execute-plan/SKILL.md`; covers the fail-closed stand-down

- [ ] Run → expect RED: `grep -c "company_projects_root" agents/skills/execute-plan/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [ ] In the **Base-branch resolution rule**'s configuration note, immediately after the sentence ending `the project defaults to default-branch-integration.`, insert: `A company project - the repository root resolving under the user facts' company_projects_root key - defaults to checkout-flow instead when project_class is absent: its base is the primary checkout's branch at run start, captured once (branch ref and commit) and carried through worktree creation and the run's landing path; an explicit base_branch key remains the override; a detached checkout or an unresolvable current branch stands the run down (fail closed, never the origin-HEAD fallback).` (wrap in the paragraph's prose style with the facts-key code span; the inserted text must not contain the pinned origin-HEAD span, which stays scoped to the default-branch-integration arm in its own following sentence) [class: IMPLEMENTATION_REQUIRED]
- [ ] In the project configuration table's `project_class` row, extend the default cell from `default-branch-integration` to `default-branch-integration (a company project per the Base-branch resolution rule defaults to checkout-flow when the key is absent)` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence commands; both the pinned-span count and the personal-default count still return 1 [class: REPOSITORY_TEST]
- [ ] Commit: `skills: company projects default their worktree base to the current checkout` [class: IMPLEMENTATION_REQUIRED]

### Task 2: bootstrap seeds the company classification

Files:
- `agents/skills/bootstrap-ai-playbook/SKILL.md`

Evidence:
- `grep -c 'project_class = "checkout-flow"' agents/skills/bootstrap-ai-playbook/SKILL.md`; covers the seeding default landed
- `grep -q "company_projects_root" agents/skills/bootstrap-ai-playbook/SKILL.md`; covers the classifier wording

- [ ] Run → expect RED: the Evidence greps return 0 [class: REPOSITORY_TEST]
- [ ] Insert one bullet directly after the existing company-scoped `team_references_project` bullet: `For company-scoped repos - the repository root resolving under the user facts' company_projects_root key - persist project_class = "checkout-flow"` unless the key already exists or the operator pins another value: stacked review work is the company default, and the execute-plan Base-branch resolution rule's company arm applies the same classification at run time when the key is absent. (wrap in the bullet list's prose style with the facts-key code span) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence commands [class: REPOSITORY_TEST]
- [ ] Commit: `skills: bootstrap seeds checkout-flow class for company-scoped repos` [class: IMPLEMENTATION_REQUIRED]

### Task 3: payload-surface audit with recorded disposition

Files:
- none; audit-and-record task

Evidence:
- the audit record in the task log; covers the origin's audit-before-changing-copies direction

- [ ] Read the execution payload's landing tail (the canonical source at `agents/skills/maintenance/prompt-templates.md`, the paragraph containing `Finally squash merge to the repository's default branch`) and the zcode overlay's landing wording; record the audit disposition in the task log quoting the tail's own class-conditioned clause: the tail's default-branch pin is correct for default-branch-integration landings (this repository's deployment), the tail's parenthetical already conditions creation/landing equality on that class, the company-class scheduler lane's divergence (creation per the captured current branch, landing target pinned default) is a residual OWNED by the still-open `2026-09-28-checkout-flow-landing-mismatch-guard` item with its fail-closed mismatch check, and no payload copy edit is warranted in this plan (the tail span is presence-and-ordering pinned, not count-pinned, and the class-conditioned clause is unpinned; the guard item is the tracked home for that work) [class: REPOSITORY_TEST]
- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
