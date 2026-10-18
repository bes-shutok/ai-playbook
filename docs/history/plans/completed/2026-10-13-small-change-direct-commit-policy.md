# Plan: small-change direct-commit policy

Backlog origins (scope of record):
- docs/history/backlog/2026-10-12-small-change-direct-commit-policy.md
- docs/history/backlog/2026-10-09-plan-authoring-primary-placement.md
- docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md

Driving force: simplicity + efficiency
Plan review record: the staging series docs/history/reviews/2026-10-13-plan-review-small-change-direct-commit-policy-r*.md (the highest rN is the authoritative record, including any deferred-residual list; the artifact slug is the plan's feature slug lowercased)
Execution budget: 1h total, largest task 0.5h

## Terms

- Direct-commit class: the eligibility and routing rule that lands a tiny, self-contained, session-owned edit as one path-limited commit in the checkout owning its destination branch, with no worktree and no task branch.
- Eligible edit: an edit satisfying every eligibility clause of the direct-commit class (size and self-containment, no behavior, API, or schema change, quick verification path, no overlap with any other arm's governed work, closeout-compatible checkout state).
- Target checkout: the working checkout whose current branch is the edit's destination branch.
- Crossing: committing from a different checkout than the one whose branch is the destination, for example an edit arising inside a worktree the session occupies that should land on the primary checkout's base branch.
- Unowned staged entry: a path staged in a checkout's index that the session's done manifest does not claim as owned.
- Project profile: the facts-document record of project_type (pet or company), the pet-only artifact_visibility, worktree_policy, and base_branch persisted by the bootstrap interview.
- Ordinary work: ad-hoc session work whose placement and closeout no other arm governs; never a named worktree-requiring lane, never a maintenance ad-hoc-backlog child, never a primary-execution placement.
- Named lane: a workflow the Worktree-first standard requires to run in its own worktree (plan authoring, plan execution), per the standard's policy paragraph.
- Quick verification path: the repository's cheap mechanical checks over the touched set, for this repository the public-hygiene scan and the em-dash scan over touched prose, per-project equivalents elsewhere.
- Path-limited commit: a commit that stages exactly the session-owned declared paths via explicit pathspecs, preserving unrelated staged and untracked state.
- Landing sweep gates: the closeout checks the done commit run composes, as enumerated by the done skill's commit-stage ladder.
- Merge-landing lock: the repository-keyed lock that serializes landing critical sections, held by the landing runners themselves per the Worktree-first standard's Land-under-the-lock discipline.

## Why

Tiny, self-contained edits currently escalate into worktree and task-branch setup, or stall when the closeout refuses on unrelated staged work, because no rule distinguishes them from work that needs isolation. The operator's 2026-10-12 direction, witnessed by the d63b14e1 four-file documentation commit, is to route such edits directly in the checkout owning their destination branch while keeping every protection plan work relies on. This plan writes that rule where placement is already decided, and its consult stands down while the merge-landing lock reports any holder, the consult-to-commit window and the deferred-landing-record interleaving remaining owned by the durable backlog row.

## Gist & Examples

TLDR: a direct-commit eligibility class routes tiny self-contained edits to a path-limited done commit in the target checkout, removing worktree setup for bounded edits; isolation, the merge-landing lock, and every closeout gate stay untouched.

Before: a four-file documentation fix arising during other work triggers the plan lanes' branch and worktree setup, or the done commit refuses because an unrelated change is staged in the primary checkout, and the operator directs a manual path-limited commit.

After: the placement consult resolves the direct-commit class first, the session commits exactly its owned paths in the target checkout through the done closeout after a read-only merge-status consult that stands down while it reports any holder, and unrelated staged or untracked state survives untouched; every ineligible shape falls through to the existing arms unchanged.

## Outcome

Eligible tiny edits land without worktree or branch setup, through the normal closeout, in the checkout that owns their destination branch.

- The routing decision fires at the existing placement consult, so no new decision surface is created.
- Company projects keep small edits on the current branch of the target checkout; pet projects and projects with no recorded project_type ask the operator before crossing out of the session's current checkout when it is not the target checkout.
- The class consults the merge-landing lock's status immediately before committing and stands down while it reports any holder, so a session never knowingly commits into an in-flight landing critical section.
- Every landing sweep gate keeps its present behavior, and every ineligible case keeps today's stop.

Gate delta: none - policy text only; no refusal class, gate, fence, protocol layer, or schema field is added, removed, or re-aimed; the route consults the merge-landing lock's status and stands down while it reports any holder rather than adding or widening any gate, and the two sibling origins stay separate open rows (recorded in Assumptions), not folded machinery.

## Assumptions

- assume the route lands through the existing done commit path with every landing gate intact and no gate widening; basis: the post-landing-staging gate's liveness record shows 2 catches (scripts/gate_liveness_ledger.py show, read 2026-10-13), and the origin rejects new or widened gates and persistent settings.
- assume unowned staged residue in the target checkout keeps its refusing class and the foreign-dirt ladder's live-peer abort keeps its behavior; both shapes make the route ineligible instead of being tolerated; basis: the staged-residue contract of gate_post_landing_staging in scripts/done_sweep_gates_lib.py, and the origin's rule that an unsatisfied gate preserves the existing stop behavior.
- assume the sibling origins (plan-authoring primary placement, worktree lifecycle ownership) stay separate plans; basis: the entry directs the author to decide, the three contracts share no mechanism, and folding them would put three behavior surfaces in one review against the plans skill's two-round alarm; both rows stay open and cross-linked.
- assume a project with no recorded project_type follows the pet arm (ask before crossing); basis: project_type is persisted only by the bootstrap interview with no path-derived default, and unrecognized profiles are read strictly elsewhere (docs/AGENTS.md public-pet rule).
- assume a tiny edit that belongs to an open plan's claimed scope rides that plan's own closeout and is never routed by this class; basis: the origin's scope arms exclude plan-lane work and the entry preserves per-execution isolation.

- assume the residual owns both the consult-to-commit window, a concurrent squash-landing ref move landing between the consult and the landing commit, and the deferred-landing-record interleaving, whose pending record holds no lock and whose branch field carries the source branch, so no class-level check can discriminate it; basis: this plan's scope freezes script bytes and rejects machinery growth, the window and the record shape are the done commit ladder's pre-existing properties, and the durable backlog row owns their sizing.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the eligibility boundary excludes every ownership shape the existing closeout refuses (unowned staged residue, live-peer foreign claims, foreign-owned or plan-claimed paths, work governed by another arm), verified against the staged-residue contract of gate_post_landing_staging in scripts/done_sweep_gates_lib.py and the foreign-dirt ladder named in the Assumptions' basis lines
- no-regression: the skill text changes are additive paragraphs plus one named amendment to lifecycle step 3's exception clause (the sanctioned direct-commit crossing); no other existing refusal, lane, or protection sentence is weakened or deleted
- maintainability: one home per rule, placement and eligibility in the Worktree-first standard and closeout integration in the done skill, cross-referenced rather than duplicated

**Done when:**
- both files carry the direct-commit class text and every Validation Command exits 0
- the branch diff touches only the two declared files and this plan's own file (its completed/ twin after landing)
- the public-hygiene scan exits 0 and the em-dash scan is clean over touched prose

**Ship when:**
- none: the change is repository-verifiable policy text; consuming sessions adopt it at their next placement consult.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- agents/skills/execute-plan/SKILL.md
- agents/skills/done/SKILL.md

**Tests:**
- none: the change is policy text; the Validation Commands block is the verification battery.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- scripts/done_sweep_gates_lib.py and scripts/staged_scope_guard.py; reason: the plan changes no gate behavior, and a finding there is a pre-existing defect on a separate surface
- agents/skills/plans/SKILL.md and agents/skills/maintenance/decisions.md; reason: the sibling origins' surfaces, kept for separate plans by the recorded decision in Assumptions
- README.md; reason: no skill name, path, or usage change

## Validation Commands

Run from the repository root with bash. Each pin grep is dedicated to one obligation and fails closed; the pins are absent from both target files at authoring time (verified 2026-10-13 at tip b420d9673 and re-verified after the r1 fold), so each flips green exactly when its task lands. The scope guards distinguish a true no-match (empty output with the search tool's rc 1) from a tool error (rc 2 or worse) and fail closed on both an unexpected path and a tool error. Staged-state guards describe the pre-commit tree; branch guards describe the committed tree; both pass at the stages their names state.

```bash
test -f agents/skills/execute-plan/SKILL.md || { echo "missing standard file" >&2; exit 1; }
test -f agents/skills/done/SKILL.md || { echo "missing done skill file" >&2; exit 1; }
for pin in \
  "Direct-commit class (ordinary ad-hoc work)" \
  "no behavior, API, or schema change" \
  "quick verification path" \
  "resolves the direct-commit class" \
  "ask the operator before crossing" \
  "current branch of the target checkout" \
  "no unowned staged entries" \
  "the maintenance ad-hoc backlog arm" \
  "rides that plan's own closeout" \
  "governed by another arm's placement or closeout contract" \
  "never authorizes push" \
  "sanctioned direct-commit crossing" \
  "stands down while it reports any holder" \
  "named hold of the run" \
  "never knowingly commits" \
  "the primary checkout's index carries none either" \
  "any worktree the session occupies included" \
  "resolves as ineligibility" \
  "live peer's foreign claim"; do
  grep -q "$pin" agents/skills/execute-plan/SKILL.md || { echo "missing pin: $pin" >&2; exit 1; }
done
grep -q "direct-commit class is engaged" agents/skills/done/SKILL.md || { echo "done integration missing" >&2; exit 1; }
grep -q "existing explicit-pathspec staging applies unchanged" agents/skills/done/SKILL.md || { echo "done pathspec note missing" >&2; exit 1; }
base="$(git merge-base main HEAD)" || { echo "cannot resolve merge base with the confirmed base branch main" >&2; exit 1; }
branch_extra="$(git diff --name-only "$base" HEAD | grep -vx -e agents/skills/execute-plan/SKILL.md -e agents/skills/done/SKILL.md -e docs/history/plans/2026-10-13-small-change-direct-commit-policy.md -e docs/history/plans/completed/2026-10-13-small-change-direct-commit-policy.md)"
rc=$?
if [ "$rc" -ge 2 ]; then echo "branch allowlist tool error" >&2; exit 1; fi
if [ -n "$branch_extra" ]; then echo "branch touches undeclared path(s): $branch_extra" >&2; exit 1; fi
staged_extra="$(git diff --cached --name-only | grep -vx -e agents/skills/execute-plan/SKILL.md -e agents/skills/done/SKILL.md)"
rc=$?
if [ "$rc" -ge 2 ]; then echo "staged allowlist tool error" >&2; exit 1; fi
if [ -n "$staged_extra" ]; then echo "unexpected staged path(s): $staged_extra" >&2; exit 1; fi
scripts_branch="$(git diff --name-only "$base" HEAD -- scripts/)" || { echo "branch scripts diff tool error" >&2; exit 1; }
if [ -n "$scripts_branch" ]; then echo "script bytes changed on the branch: $scripts_branch" >&2; exit 1; fi
scripts_tree="$(git diff --name-only HEAD -- scripts/)" || { echo "tree scripts diff tool error" >&2; exit 1; }
if [ -n "$scripts_tree" ]; then echo "script bytes changed in the tree: $scripts_tree" >&2; exit 1; fi
bash scripts/check-no-em-dash.sh touched || { echo "em dash found in touched prose" >&2; exit 1; }
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || { echo "public hygiene failed" >&2; exit 1; }
```

### Task 1: Add the direct-commit class to the Worktree-first standard

Context surface: the plan's Terms, this task; referenced, never restated.

Files:
- agents/skills/execute-plan/SKILL.md

- [ ] Add a paragraph titled by the literal line `Direct-commit class (ordinary ad-hoc work):` immediately after the Project worktree policy paragraph. The paragraph opens with the eligibility contract: an eligible edit is tiny and self-contained, over at most four files, session-owned, carries no behavior, API, or schema change, needs no plan or review cycle, and has a quick verification path. [class: IMPLEMENTATION_REQUIRED]
- [ ] Complete the paragraph's eligibility contract with the plan-scope exclusion: an edit inside an open plan's claimed scope is never eligible for the direct-commit class and rides that plan's own closeout. [class: IMPLEMENTATION_REQUIRED]
- [ ] Complete the eligibility contract with the session-shaped exclusion: work governed by another arm's placement or closeout contract (a live plan run holding its worktree or execution claim, a maintenance ad-hoc child, a primary-execution placement) is never eligible and rides that arm's own closeout or defers to session end. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph add the routing rule: the placement consult resolves the direct-commit class before escalating ordinary ad-hoc work to a worktree or task branch; an ineligible edit falls through to the existing arms (the primary default, the named worktree lanes, or operator direction). [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph add the destination rules: company projects commit on the current branch of the target checkout; pet projects and projects with no recorded project_type ask the operator before crossing out of the session's current checkout when it is not the target checkout, any worktree the session occupies included, and proceed unasked when the session already sits in the target checkout. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph add the unattended and live-run arms: with no operator in the turn, the crossing ask resolves as ineligibility, the edit falls through to the existing arms, the hold recorded under a named reason; the class never knowingly commits in a target checkout whose consult reports a holder, and never authorizes push. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph add the closeout compatibility precondition: the route is eligible only when the target checkout's index carries no unowned staged entries and, when the target checkout is not the primary checkout, the primary checkout's index carries none either, the primary being the index that gate inspects. [class: IMPLEMENTATION_REQUIRED]
- [ ] Complete the precondition with the disjointness and live-peer legs: the declared paths are disjoint from all foreign work and the checkout carries no dirty or untracked path the run classifies as a live peer's foreign claim; unowned staged residue keeps its refusing class, which is exactly what makes that shape ineligible. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph add the closeout integration: the commit lands through the done closeout's path-limited commit in the target checkout with every landing sweep gate running unchanged; immediately before the commit stage the session runs scripts/done-lock.sh merge-status read-only and stands down while it reports any holder. [class: IMPLEMENTATION_REQUIRED]
- [ ] Complete the integration with the stand-down's resolution: a named hold of the run per the done skill's blocked posture, never a placement fall-through and never an unbounded re-consult loop. [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend lifecycle step 3's exception clause: after the coordination-witness and transfer-step clause, naming the sanctioned direct-commit crossing per the Direct-commit class paragraph as likewise sanctioned; amend nothing else in the step. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same paragraph add the boundary notes: the class changes neither the maintenance ad-hoc backlog arm's worktree containment and panel contract, nor the plan authoring and execution lanes, nor the primary-execution authorization, nor the per-execution worktree isolation protections; the session-shaped exclusion keeps each arm's work out of the class. [class: IMPLEMENTATION_REQUIRED]

Evidence: the new paragraph reads as one paragraph with its clauses in the order this task states them; lifecycle step 3's exception clause carries exactly the one named amendment and no other existing sentence in the standard changed; every pinned span for this file appears in the prescribed text exactly as the Validation Commands pin them.

### Task 2: Cross-reference the route in the done skill's placement

Context surface: the plan's Terms, this task; referenced, never restated.

Files:
- agents/skills/done/SKILL.md

- [ ] Add one paragraph immediately after the Step 0 paragraph that ends with the literal sentence "the classifier's own usage text is the procedure of record.": when the direct-commit class is engaged, the done run executes in the target checkout, and the run manifest claims the session-owned declared paths as owned paths; the commit stage's existing explicit-pathspec staging applies unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Complete the same paragraph with the gate, consult, and ownership note: every landing sweep gate runs unchanged, the consult-and-stand-down discipline runs as the standard's direct-commit class paragraph prescribes, and eligibility and destination rules are owned there, referenced here, never restated; the consult is a read-only status read, not lock management, leaving the runner-owned acquire-and-release spans untouched. [class: IMPLEMENTATION_REQUIRED]

Evidence: the new paragraph sits immediately after the Step 0 paragraph ending with the classifier sentence; the rest of the done skill is byte-identical; the pinned spans for this file appear in the prescribed text exactly as the Validation Commands pin them.
