# Plan: scope-control family (plans scope-extension gate + cleanup preservation)

Backlog origin:
- `docs/history/backlog/2026-09-05-plans-scope-extension-requires-grill-with-docs.md` (High)
- `docs/history/backlog/2026-09-05-cleanup-scope-preserve-preexisting-content.md` (High; extends the first, per its own header)

## Terms

- **Scope extension**: proposed plan work not required to deliver the stated primary goal, including any concern the plan itself labels as owned by another ticket or feature.
- **Scope ledger**: the plan-recorded list of the exact base ref, task-owned files, classes, methods, and hunks, frozen areas, pre-existing dirty paths, untracked paths, and explicit deletion permissions for multi-file cleanup or restoration work.
- **Cleanup baseline checker**: `scripts/check_cleanup_scope_baseline.py` (new in this plan); classifies dirty and deleted paths against a base ref and an allow-list, failing with named errors.
- **Pin**: a fixed-string validation span quoted verbatim from a prescribed insertion; each pin must occur exactly once in its target file (rule 18, mechanical pin audit after every fold).

## Assumptions

- assume one combined plan for both items; basis: task prompt plus item 2's explicit cross-reference ("this item should extend that work").
- assume item-1 plans edits land before item-2 extensions in task order; basis: item 2 builds on item 1's gate.
- assume the item-2 "lightweight validator or checklist" is a small repo-local Python script with `--selftest`; basis: item text offers "validator or checklist"; repo convention (e.g. `scripts/check_backlog_inbox_location.py`) prefers mechanical checks with selftests.
- assume no `execute-plan` skill changes; basis: item 1 explicit non-goal ("Do not teach execute-plan to re-grill").
- assume all skill text stays domain-agnostic with no consumer-repo examples; basis: item 1 acceptance criteria.
- assume work on the current branch (`main`), no new branch, never push; basis: task constraint.
- assume both backlog items stay open under `docs/history/backlog/` until plan completion; basis: plans Plan Lifecycle.

## Gist & Examples

Two High-severity holes share one root: agents treat adjacent work as already-decided. First, the plans skill's confidence gate only classifies *uncertainty*; it does not classify *scope*. An agent that sees a neighboring security or identity concern classifies "another ticket owns production" as a high-confidence assumption, folds verifier stacks, headers, and tests into the plan, and the user batch-confirms a list that quietly contains a second product. Second, cleanup and review flows lack a scope boundary: "simplify this branch" is read as permission to make the whole branch resemble its base, review findings are read as authorization to keep fixing outward, and pre-existing uncommitted work is deleted or staged as collateral.

This plan lands two coordinated gates:

1. A **scope-extension hard gate** in `plans` Phase 1, independent of the confidence tiers: a scope extension may only enter the plan through `grill-with-docs` with an explicit in / split / defer decision, never as a batch-confirmed assumption; the default outcome is a backlog item, never silent absorption into the current scope. Step 1.2 confirms extensions explicitly; Step 1.4 lists them separately from assumptions; a contradiction check catches "owned elsewhere" prose coexisting with implementing tasks. `grill-with-docs` gets the mirror Integration Points sentence; `execute-plan` gets an explicit faithfulness note (it never re-opens scope).
2. A **cleanup-preservation gate** across `grilling`, the three review skills, `plans`, and `done`: cleanup wording becomes a mandatory ambiguity trigger with a recommended preservation question; findings are evidence, not authorization; multi-file cleanup requires a scope ledger; `done` captures a session baseline and refuses pre-existing paths. A small mechanical checker (`scripts/check_cleanup_scope_baseline.py`, with `--selftest`) classifies dirty and deleted paths against the ledger so a cleanup commit cannot silently sweep unaccounted work.

### Scenario 1 (happy path): plan authoring meets a scope extension

**Before (today).** The ticket says "add request signing to the upload API". During Phase 1 the agent notices the uploads service also lacks rate limiting. Nothing in the repo settles who owns rate limiting, but the agent rates it high-confidence ("another ticket owns throttling"; "fail-open is safer for now") and, on that basis, adds Tasks 4-6 (limiter, config, tests) to the plan. Step 1.4 presents a fourteen-item assumption list; the user scans it and replies "yes". `execute-plan` then ships a second product faithfully, and the review loops score the branch against the plan's own (expanded) Review Scope, so nobody questions the limiter tasks again. The user first sees the scope growth when the PR is already large.

**After (this plan).** Same moment, different flow. The scope-extension hard gate classifies rate limiting as work not required by the stated primary goal, so it cannot enter Terms, Assumptions, Tasks, Files, or Review Scope as an assumption; adding those tasks is blocked at authoring time. The agent invokes `grill-with-docs` and asks one question: keep in this plan, split, or defer? The user answers "defer". The agent records the outcome in Step 1.2 and Step 1.4 shows a separate block, "Scope extensions (grilled): request rate limiting: split/defer (backlog item created)", while Tasks 4-6 never enter the plan and the limiter lives in a backlog item. The shipped plan contains exactly the signing work; a bare "yes" to the assumptions list could not have admitted it.

### Scenario 2 (happy path): cleanup request on a shared branch

**Before (today).** The user says "clean up this branch". The agent reads it as "make the branch resemble its base": it deletes an untracked scratch file a peer session created yesterday, reverts a pre-existing modified guideline file, and stages everything in one sweep. Recovery needs reflog archaeology plus a docs-branch restore before the real feature work can continue.

**After (this plan).** `grilling` fires the mandatory ambiguity trigger and asks the preservation question exactly as prescribed in Task 2: "Should I change only the files, classes, and methods required by this feature, while preserving every other file and all pre-existing uncommitted content?" The user confirms; the session records a scope ledger: base ref, task-owned files and hunks, frozen areas, the peer's untracked file as pre-existing. When the cleanup commit is prepared, the baseline checker runs with that ledger and exits 1 with `cleanup-scope: unaccounted dirty path docs/tmp/scratch-notes.md` because the peer's file is not in the allow-list, so the agent preserves it instead of deleting. At `done`, the session baseline refuses to stage anything that was dirty or untracked before the session unless the user explicitly includes it.

### Scenario 3: review findings pulling the scope outward

**Before (today).** A reviewer notes the new endpoint lacks pagination. The loop fixes pagination, which surfaces caching, which surfaces a migration; each fix generates fresh findings and the branch grows in every direction. Nothing in the workflow distinguishes "a valid observation" from "authorized to implement now".

**After (this plan).** The three review skills state the boundary in one sentence: findings are evidence to assess, not authorization to broaden. Pagination outside the accepted scope becomes a backlog item (per `receiving-review` Backlog capture) unless the user explicitly expands scope; the loop then exits on its own merits instead of chasing the new work it created.

### Edge cases that shaped the design

- An extension the user explicitly keeps: the grill outcome "in" admits it, and Step 1.4 shows it as a grilled, user-accepted extension (not an assumption); this is the only path in.
- Findings inside the accepted scope keep flowing exactly as today; the evidence-not-authorization sentence changes only out-of-scope findings.
- A cleanup where every dirty path is in the ledger: the checker exits 0 and the commit proceeds unchanged.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every acceptance criterion in both backlog items maps to a task, and every structural obligation introduced by the tasks carries a dedicated validation pin; rule 7 holds per obligation, with one pin allowed to carry the obligations of its own prescribed paragraph (shared pins are fine where one paragraph carries one obligation, and prose-only criteria such as domain-agnostic wording are covered by the task text and review scope rather than a pin).
- consistency: integration points are bidirectional (plans ↔ grill-with-docs; review skills reference `receiving-review` Backlog capture); verified per file with dedicated greps.
- mechanical enforcement: the cleanup baseline checker's `--selftest` is green and its arms cover a dirty tree containing unrelated modified and untracked content (item 2 acceptance criterion), plus unauthorized-deletion and clean-tree arms.
- hygiene: no-em-dash scan and public hygiene scan green over authored bytes at authoring time (rule 29); all seven target files verified at 0 em dashes today, so the executor's done gate will not trip on frozen legacy content.

**Done when:**

- All six tasks committed on `main`; the full Validation Commands block exits 0; a fresh review-plan round reports `ready=yes` with zero blocking findings at the final digest; the done run has committed the plan and its review artifact with selective staging.

**Ship when:**

- The next real plan-authoring, cleanup, or review session in any repo exercises the new gates without regressing existing flows (human-observed; not a checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/plans/SKILL.md` (Phase 1 confidence-gate region, Step 1.2, Step 1.4, Integration Points `grill-with-docs` and `execute-plan` subsections; all other sections frozen)
- `agents/skills/grill-with-docs/SKILL.md` (Integration Points "With `rfc-design` / `plans` skills" subsection only; rest frozen)
- `agents/skills/grilling/SKILL.md` (main body, new mandatory-triggers paragraph before Integration Points; rest frozen)
- `agents/skills/doing-code-review/SKILL.md` (one sentence at the end of the `## Boundary` section; rest frozen)
- `agents/skills/receiving-review/SKILL.md` (one sentence at the end of the `## Boundary` section; rest frozen)
- `agents/skills/review-loop/SKILL.md` (one sentence at the end of the `## Orchestration rules` section; rest frozen)
- `agents/skills/done/SKILL.md` (Step 3 item 0 region; rest frozen)
- `scripts/check_cleanup_scope_baseline.py` *(new)*

**Tests:**

- `scripts/check_cleanup_scope_baseline.py` `--selftest` arms (embedded in the same file, built in Task 4)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/execute-plan/SKILL.md`; item 1 explicit non-goal (execute-plan stays faithful to the plan)
- `agents/skills/review-agents/review-panel-selection.md`; panel composition is unchanged by this plan
- `README.md`; no catalog change (no new skill, no renamed skill)
- Any product or consumer repo file; this plan edits the skills repo only

## Validation Commands

```bash
#!/bin/bash
# Anchored at the repo root. Fail-closed: every check aborts on miss (rule 10).
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
fail() { echo "VALIDATION FAILED: $1" >&2; exit 1; }
# pin_once <file> <fixed-string>: the span must occur EXACTLY once (rules 7, 18).
pin_once() {
  local f="$1" s="$2" c
  [ -f "$f" ] || fail "missing file: $f"
  c=$(grep -cF -- "$s" "$f")
  [ "$c" -eq 1 ] || fail "pin count $c (want 1) in $f: $s"
}

# Task 1: plans gate + grill-with-docs mirror
pin_once agents/skills/plans/SKILL.md "Scope-extension hard gate (independent of the confidence tiers)"
pin_once agents/skills/plans/SKILL.md "must not enter Terms, Assumptions, Tasks, Files, or Review Scope as a high-confidence assumption"
pin_once agents/skills/plans/SKILL.md "grill outcome (in / split / defer)"
pin_once agents/skills/plans/SKILL.md "a bare yes on assumptions does not admit an extension that was never grilled"
pin_once agents/skills/plans/SKILL.md "Cleanup scope ledger"
pin_once agents/skills/plans/SKILL.md "never re-grills or re-opens scope mid-implementation"
pin_once agents/skills/plans/SKILL.md "never silently absorbed into the current scope"
pin_once agents/skills/plans/SKILL.md "the outcome is a backlog item unless the user explicitly accepts the extension into this plan"
pin_once agents/skills/grill-with-docs/SKILL.md "routes every proposed scope extension through this interview"
pin_once agents/skills/plans/SKILL.md "routes every proposed scope extension through this skill"

# Task 2: grilling mandatory triggers
pin_once agents/skills/grilling/SKILL.md "Mandatory ambiguity triggers (cleanup and restoration)"
pin_once agents/skills/grilling/SKILL.md "preserving every other file and all pre-existing uncommitted content"
pin_once agents/skills/grilling/SKILL.md "make the branch resemble its base"

# Task 3: findings-are-evidence sentence, one per file
for f in agents/skills/doing-code-review/SKILL.md agents/skills/receiving-review/SKILL.md agents/skills/review-loop/SKILL.md; do
  pin_once "$f" "evidence to assess, not authorization to broaden"
  pin_once "$f" "unless the user explicitly expands scope"
done

# Task 4: cleanup baseline checker
test -f scripts/check_cleanup_scope_baseline.py || fail "checker script missing"
python3 scripts/check_cleanup_scope_baseline.py --selftest || fail "checker selftest failed"
grep -F -q "cleanup-scope: unaccounted dirty path" scripts/check_cleanup_scope_baseline.py || fail "checker: unaccounted-dirty error class missing"
grep -F -q "cleanup-scope: unauthorized deletion" scripts/check_cleanup_scope_baseline.py || fail "checker: unauthorized-deletion error class missing"

# Task 5: done baseline + refusal
pin_once agents/skills/done/SKILL.md "dirty-tree and untracked-file baseline before the first edit"
pin_once agents/skills/done/SKILL.md "already dirty or untracked at baseline unless the user explicitly includes it"
grep -F -q "check_cleanup_scope_baseline.py" agents/skills/done/SKILL.md || fail "done: checker pointer missing"

echo "VALIDATION OK"
```

Self-match note (rule 15): every pin above targets a skill or script file, never this plan; the plan's own copies of these spans are the checker literals, not stale references. Pin targets are verified absent today (each span is new text), so the block is RED until the tasks land, and the block itself is the positive control: `pin_once` fails on zero matches and on duplicates alike.

### Task 1: plans scope-extension hard gate + grill-with-docs mirror

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/grill-with-docs/SKILL.md`

- [x] In `plans/SKILL.md` Phase 1, insert immediately before the paragraph beginning "Keep every high-confidence assumption in one running list" a new paragraph: `**Scope-extension hard gate (independent of the confidence tiers):** any proposed plan work that is not required to deliver the stated primary goal is a scope extension. Scope extensions include, without limiting: a second auth or identity mechanism, a cross-cutting header or principal model, a sibling-service contract the ticket does not own, a multi-tenant or multi-market product shape, and any concern the plan already labels as owned by another ticket or feature. A scope extension must not enter Terms, Assumptions, Tasks, Files, or Review Scope as a high-confidence assumption; before writing or expanding the plan file to include it, invoke grill-with-docs and get an explicit user decision: keep in this plan, split to a separate plan, or defer. When the user does not explicitly accept the extension into the current plan, its disposition is a backlog item (per receiving-review Backlog capture); a scope extension is never silently absorbed into the current scope. Contradiction check: if OUT-of-scope or owned-elsewhere prose coexists with Tasks or Files that implement that concern, treat the extension as unresolved; grill it or remove the implementing tasks before the plan file is written.`
- [x] In `plans/SKILL.md` Step 1.2 "Confirm these elements", append element: `6. **Scope extensions:** every proposed scope extension, each with its grill outcome (in / split / defer); extensions are listed separately from ordinary assumptions and are never batch-confirmed; the outcome is a backlog item unless the user explicitly accepts the extension into this plan.`
- [x] In `plans/SKILL.md` Step 1.4 confirmation template, insert after the "Assumptions (high-confidence, not grilled)" block: `**Scope extensions (grilled):** <extension>: <grill outcome: in / split / defer>; a bare yes on assumptions does not admit an extension that was never grilled, and an extension without an explicit keep-in-this-plan decision is recorded as a backlog item.`
- [x] In `plans/SKILL.md`, insert after the scope-extension hard gate paragraph a cleanup-ledger paragraph: `**Cleanup scope ledger:** for multi-file cleanup, simplification, or restoration work, the plan records a scope ledger: the exact base ref, task-owned files, classes, methods, and hunks, frozen areas, pre-existing dirty paths, untracked paths, and explicit deletion permissions. The mechanical check is the repo-local cleanup baseline checker (scripts/check_cleanup_scope_baseline.py in the skills repo); the ledger is its allow-list.`
- [x] Amendment (review r1/r2/r4/r5): the landed wording was amended after the plan was written (carve-out sentence added by r1; checker pointer reworded by r2; r4 anchored the primary-goal necessity test to the ticket/request text, made the Step 1.4 Scope extensions block always render with an explicit "none proposed." when empty, and added the not-named-by-the-request tie-breaker; r5 split the template's meta-rule prose out of the placeholder rendering); the plan text above preserves the original prescription, the Validation pins still match the landed spans.
- [x] Note (forward reference, accepted): the ledger paragraph names `scripts/check_cleanup_scope_baseline.py`, which Task 4 creates. Between the Task 1 and Task 4 commits the reference is forward-looking by design: the sentence describes the completed contract, and no validation pin targets the script before Task 4 lands.
- [x] In `plans/SKILL.md` Integration Points "With `grill-with-docs` skill", append: `The Phase 1 scope-extension hard gate routes every proposed scope extension through this skill before the plan file admits it; the confirmed outcome (in / split / defer) lands in the Step 1.4 confirmation block as a grilled scope extension.`
- [x] In `plans/SKILL.md` Integration Points "With `execute-plan` skill", append: `Scope control happens at plan authoring: execute-plan stays faithful to the plan and never re-grills or re-opens scope mid-implementation; overscope discovered during execution is reported, not silently implemented beyond the plan, and not silently dropped.`
- [x] In `grill-with-docs/SKILL.md` Integration Points "With `rfc-design` / `plans` skills", append: `The plans skill's Phase 1 scope-extension hard gate routes every proposed scope extension through this interview before the plan file admits it; record the in / split / defer decision inline per this skill's glossary and ADR capture.`
- [x] Run → expect RED: the Task 1 pins in the Validation block fail today (spans absent; verified 2026-09-05)
- [x] Commit: `skills: plans scope-extension hard gate + cleanup scope ledger`

### Task 2: grilling mandatory cleanup ambiguity triggers

Files:
- `agents/skills/grilling/SKILL.md`

- [x] In `grilling/SKILL.md`, insert a new paragraph immediately before `## Integration Points`: `**Mandatory ambiguity triggers (cleanup and restoration):** when a request says simplify, remove, clean up, clean the branch, restore, or make it match the base, and the working tree or branch contains more than the obvious feature work, ask one focused scope question before any edit or restore operation. Recommended wording: Should I change only the files, classes, and methods required by this feature, while preserving every other file and all pre-existing uncommitted content? Do not treat cleanup wording as permission to make the branch resemble its base; distinguish the task-owned diff from pre-existing work before touching anything.`
- [x] Run → expect RED: the Task 2 pins fail today (verified 2026-09-05: grilling has no cleanup triggers)
- [x] Amendment (review r2/r3/r4/r5): the landed trigger condition was reworded after the plan was written (r2 narrowed it to git-status-visible pre-existing paths; r3 restored a branch-aware condition so committed pre-existing work also triggers the question; r4 widened the enumerated word list with a catch-all so near-synonyms like delete, prune, or reset-to-base cannot bypass it; r5 extended the catch-all to requests whose natural fulfillment includes deleting, reverting, or reorganizing files); the plan text above preserves the original prescription, the Validation pins still match the landed spans.
- [x] Commit: `skills: grilling mandatory cleanup ambiguity triggers`

### Task 3: review findings are evidence, not authorization

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [x] In `doing-code-review/SKILL.md`, insert a sentence at the end of the `## Boundary` section: `Review findings are evidence to assess, not authorization to broaden the reviewed change's scope; findings outside the accepted scope become backlog items (per receiving-review Backlog capture) unless the user explicitly expands scope.`
- [x] In `receiving-review/SKILL.md`, insert at the end of the `## Boundary` section the same sentence, adapted to point at its own Backlog capture section: `Review findings are evidence to assess, not authorization to broaden the change's scope; findings outside the accepted scope become backlog items (see Backlog capture below) unless the user explicitly expands scope.`
- [x] In `review-loop/SKILL.md`, insert at the end of the `## Orchestration rules` section: `Review findings are evidence to assess, not authorization to broaden the loop's scope; findings outside the accepted scope become backlog items (per receiving-review Backlog capture) unless the user explicitly expands scope.`
- [x] Run → expect RED: the six Task 3 pins fail today (verified 2026-09-05: none of the three files carries authorization language)
- [x] Commit: `skills: review findings are evidence, not scope authorization`

### Task 4: cleanup baseline checker (RED → GREEN)

Files:
- `scripts/check_cleanup_scope_baseline.py` *(new)*

- [x] `CheckCleanupScopeBaselineSelftest#unaccounted_dirty_fails`; given a temp git repo with one committed base file, an unrelated modified tracked file, and an unrelated untracked file, with `--base <ref>` and an allow-list covering only the task-owned file, expects exit 1 and stderr containing `cleanup-scope: unaccounted dirty path` naming both the modified and the untracked path
- [x] `CheckCleanupScopeBaselineSelftest#allowed_dirty_passes`; given the same tree with both paths added via `--allow`, expects exit 0
- [x] `CheckCleanupScopeBaselineSelftest#unauthorized_deletion_fails`; given the committed base file deleted on disk and absent from the allow-list, expects exit 1 and stderr containing `cleanup-scope: unauthorized deletion`
- [x] `CheckCleanupScopeBaselineSelftest#clean_tree_passes`; given no dirty or deleted paths beyond the allow-list, expects exit 0
- [x] Run → expect RED: `python3 scripts/check_cleanup_scope_baseline.py --selftest` fails (script absent, exit non-zero)
- [x] Implement the checker: stdlib-only, no network; CLI `--repo-root` (default `.`), `--base <ref>`, `--allow <path>` repeatable, `--selftest`; classifies `git status --porcelain` dirty paths (modified, staged, untracked) and `git diff --name-only --diff-filter=D <base>` deletions; every unaccounted path fails with one of the two named error classes; `--selftest` builds its four fixture repos in a temp dir and asserts the outcomes above, setting an explicit local git identity (user.name and user.email via git config) in every fixture repo so identity-less machines stay green; deterministic output ordering (sorted paths)
- [x] Run → expect GREEN: all four selftest arms pass
- [x] Commit: `feat: cleanup scope baseline checker with selftest`

### Task 5: done session baseline + pre-existing path refusal

Files:
- `agents/skills/done/SKILL.md`

- [x] In `done/SKILL.md` Step 3, extend item 0 ("Distinguish session changes from pre-existing local changes") with: `For cleanup or restoration sessions, capture the dirty-tree and untracked-file baseline before the first edit (record git status --porcelain output in the session notes, or run the cleanup baseline checker scripts/check_cleanup_scope_baseline.py (in the skills repo) against the task's scope ledger), and refuse to stage any path that was already dirty or untracked at baseline unless the user explicitly includes it.`
- [x] Amendment (review r1/r2/r4/r5): the landed wording was amended after the plan was written (carve-out sentence added by r1; checker pointer reworded by r2; exit-code semantics plus the ledger-vs-session-notes authority clause added by r2; r4 made the session-notes baseline mandatory with the checker as an additional arm and defined the exit-2-without-recorded-baseline behavior as ask-before-staging; r5 corrected the post-commit coverage claim and added the no-pre-edit-baseline ask rule and the ignored-files discovery command); the plan text above preserves the original prescription, the Validation pins still match the landed spans.
- [x] Run → expect RED: the three Task 5 pins fail today
- [x] Commit: `skills: done session baseline capture + pre-existing path refusal`

### Task 6: final validation

Files: none (validation only)

- [x] Run the full `## Validation Commands` block from the repo root → expect exit 0 with `VALIDATION OK` (all tasks landed; at this point every pin is present exactly once and the selftest is green)
- [x] Run `bash -n` over the Validation Commands block → expect clean
- [x] Run the no-em-dash scan (`~/.ai-playbook/scripts/check-no-em-dash.sh touched`) → expect exit 0
- [x] Run the public hygiene scan (`~/.ai-playbook/scripts/scan-public-hygiene.sh`) → expect exit 0
- [x] Commit (if any residue): `chore: scope-control family final validation`
