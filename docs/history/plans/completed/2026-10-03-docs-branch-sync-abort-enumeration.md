# Plan: docs-branch sync failure-semantics abort enumeration

Origin: `docs/history/backlog/2026-09-20-tasks-7-8-prose-precision.md` (restoration receipt narrows scope to its item 2)
Plan review record: `docs/reviews/2026-10-03-plan-review-docs-branch-sync-abort-enumeration-r*.md` (+ `.stats.json` sidecars)

## Driving force

The `Failure semantics (sync)` paragraph in `agents/skills/docs-branch/SKILL.md` (the paragraph opens `Failure semantics (sync): every failure path in the block is loud on stderr and splits into two classes.`) claims to classify every failure path in the sync block, but its exit-1 abort list names only three classes: the hygiene gate, the certified-downgrade refusal, and the docs-branch `git worktree add` refusal. Two more exit-1 aborts stand in the block outside the named set: the invalid docs/* branches consolidation error (the `refs/heads/docs/*` sub-branch check whose error line reads `ERROR: found invalid docs/* branches; consolidate them into refs/heads/docs first`) and the unsafe-shadow-path refusal (the case guard reading `Refusing unsafe shadow path: ...`). The paragraph was rewritten once since the row was deferred (the docs-branch wording pass, commit 8bd3bc9d) without gaining the enumeration, so the false-exhaustiveness claim is live today. Authoring-time re-derivation (2026-10-03): a full sweep of the sync block's `exit 1` sites finds exactly five - the hygiene gate, the certified-downgrade guard refusal, the docs-branch worktree-add refusal, the docs/* consolidation error, and the unsafe-shadow-path refusal - three of which the paragraph already enumerates, so the two named above are the complete unenumerated set.

## Outcome

- The `Failure semantics (sync)` paragraph's exit-1 abort list gains the two missing classes, one clause each naming the trigger and the reader action, keeping the paragraph's two-class structure (exit-1 aborts versus warn-and-continue) and its opening claim intact; after this plan the EXIT-1 HALF of the opening claim is exhaustive (the warn-and-continue half and post-staging failure modes are out of scope, see Assumptions).

## Gate delta

None. This is a documentation-precision change: no new machinery, no new checks, no script edits. Priced by the origin row's restoration receipt per the machinery delta doctrine (`docs/history/plans/completed/2026-09-29-plans-machinery-delta-doctrine.md`).

## Terms

- **Sync block**: the bash fence under the docs-branch sync step's intro `Run this entire script as a single shell invocation` (with the target-shell note `Target shell is bash, not zsh.`) - the block whose failure semantics the paragraph classifies, NOT the witness-append block's invocation.
- **Abort enumeration**: the exit-1 class list inside the `Failure semantics (sync)` paragraph; each entry names the trigger and the reader action in one clause.
- **Shadow path**: a path from the overlay list the sync copies into the docs worktree; the unsafe-shadow-path refusal rejects empty, dot, parent-relative, absolute, or parent-escaping entries (the guard's case arms).

## Assumptions

- assume the enumeration lands against the paragraph's CURRENT text (post-8bd3bc9d), not the deferred text; the row's restoration receipt records the paragraph was rewritten once without the enumeration. Basis: the origin row and the live paragraph re-read 2026-10-03.
- assume the two clauses are comment-only: the sync block's executable lines are untouched, so no behavior changes and no test surface exists beyond the text itself. Basis: this is the plan's own scoping decision, consistent with the origin row's prose-precision driving force and its item-2 narrowing (the row itself records no rejected-alternatives section; the restructuring bar is the plan's, stated here).
- assume the two aborts are the complete unenumerated set. Basis: the authoring-time sweep above (five `exit 1` sites in the sync block, three already enumerated); the review re-derives this sweep and any additionally found site folds into the same task shape.
- assume this plan makes only the EXIT-1 half of the paragraph's opening claim exhaustive and does NOT claim the whole sentence true: the paragraph's warn-and-continue list may carry unnamed members (for example the skipped-deny-pattern-scan warning when no hygiene patterns file is present) and post-staging failure modes (a failed commit propagating non-zero) fit neither named class; those residuals are outside the origin row's narrowed scope and are visible to future prose-precision passes. Basis: the live paragraph and block text 2026-10-03; the silent-partial-extract sibling row `docs/history/backlog/2026-10-03-docs-branch-silent-partial-extract-no-op.md` tracks the silent-swallow family.
- assume the unsafe-shadow-path clause says the abort trips before any commit (earlier overlay copies may have run, but nothing is staged or committed when the refusal fires), matching the paragraph's exit-1 class definition. Basis: the sync block's staging order (shadow assembly, then overlay, then stage and commit last).
- assume the operator execution-lane closure of 2026-10-02 stands: authoring only.

Decision points requiring a grill: clause placement inside the existing list order; whether the docs/* clause names the consolidation command inline or by pointer.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/docs-branch/SKILL.md` *(modified; the `Failure semantics (sync)` paragraph only - two clauses added to its exit-1 list)*

**Tests:** none; the artifact is skill text and the Validation Commands carry the needles.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The sync block's executable lines; reason: the plan's own scoping decision is documentation-precision only (see Assumptions), and any script edit is a behavior change this plan forbids.
- The paragraph's warn-and-continue list and the block's silent-swallow paths; reason: outside the exit-1 class this plan completes; the silent-swallow family is tracked by `docs/history/backlog/2026-10-03-docs-branch-silent-partial-extract-no-op.md`.
- The witness-append block's own `Failure semantics` paragraph (the lesson-scope-drift append); reason: a separate block with its own paragraph, not named by the origin row.
- `docs/maintenance/development_lessons.md`; reason: an enumeration of two clauses is not a lesson-bearing defect; no lesson duty is triggered.
- Other skills' failure-semantics prose; reason: single-origin scope per the restoration receipt.

## Validation Commands

```bash
# The paragraph gate: the Failure semantics (sync) paragraph names BOTH unenumerated
# aborts. RED before Task 1 (neither clause is named today); GREEN after.
# Paragraph-scoped by construction: the gate reads only the line(s) starting with
# 'Failure semantics (sync):', so the sync block's pre-existing error lines cannot
# satisfy it.
python3 - <<'EOF'
import re, sys, pathlib
text = pathlib.Path("agents/skills/docs-branch/SKILL.md").read_text(encoding="utf-8")
paras = [ln for ln in text.splitlines() if ln.startswith("Failure semantics (sync):")]
if len(paras) != 1:
    print(f"expected exactly one sync failure-semantics paragraph, found {len(paras)}"); sys.exit(1)
para = paras[0]
docs_ok = ("invalid docs/*" in para) or ("refs/heads/docs first" in para)
unsafe_ok = ("unsafe shadow path" in para.lower()) or ("unsafe-shadow-path" in para.lower())
if not docs_ok:
    print("MISSING: the docs/* consolidation abort clause"); sys.exit(1)
if not unsafe_ok:
    print("MISSING: the unsafe-shadow-path refusal clause"); sys.exit(1)
print("paragraph gate OK: both abort clauses named"); sys.exit(0)
EOF
# the executable abort sites are untouched by this plan: the two error lines
# still exist verbatim in the sync block (they pre-date the plan and must not move).
grep -q "found invalid docs/\* branches" agents/skills/docs-branch/SKILL.md
grep -q "Refusing unsafe shadow path" agents/skills/docs-branch/SKILL.md
```

### Task 1: amend the Failure semantics (sync) paragraph's exit-1 list

Files:
- `agents/skills/docs-branch/SKILL.md`

- [ ] Run the Validation Commands -> expect the paragraph gate RED with BOTH missing-clause messages (the paragraph names neither abort today), and the two error-line greps GREEN (the abort sites exist and are not touched by the RED state) [class: REPOSITORY_TEST]
- [ ] Re-read the `Failure semantics (sync)` paragraph immediately before amending and compare it against the opening text quoted in Driving force; any difference is drift a peer lane introduced: stop and reconcile before editing (the paragraph was rewritten once since deferral by exactly this kind of drift) [class: REPOSITORY_TEST]
- [ ] Amend the `Failure semantics (sync)` paragraph's exit-1 abort list: after the docs-branch `git worktree add` refusal clause, add one clause for the invalid docs/* branches consolidation error (exit 1, before staging: any `refs/heads/docs/*` sub-branch trips it; the reader action is the error line's own instruction - consolidate the sub-branches into `refs/heads/docs` first, then re-run the sync), and one clause for the unsafe-shadow-path refusal (exit 1, before any commit: an empty, dot, parent-relative, absolute, or parent-escaping shadow path trips it; the reader action is to fix the path list that produced the entry, naming the refused path from the error line), keeping each clause in the paragraph's existing comma-and-clause style, the two-class structure, and the opening claim unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands -> expect every command GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `docs: enumerate the docs-branch sync aborts in the failure-semantics paragraph` [class: IMPLEMENTATION_REQUIRED]

### Task 2: completion pass

Files:
- none (validation and bookkeeping only)

- [ ] Run every Validation Command in order -> expect each GREEN [class: REPOSITORY_TEST]
- [ ] Confirm Task 1's commit touched only the `Failure semantics (sync)` paragraph: `git show --stat HEAD` names exactly one file, and `git show HEAD -- agents/skills/docs-branch/SKILL.md` shows a diff confined to that paragraph's line (the two error-line greps in the Validation Commands double as the executable-lines guard) [class: REPOSITORY_TEST]
- [ ] Run the duplicate-origin coverage gate for the cited origin and mark it covered per the completion duty [class: REPOSITORY_TEST]
- [ ] Commit (if any residue): `chore: docs-branch abort enumeration validation residue` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-20-tasks-7-8-prose-precision.md`: narrowed by its restoration receipt to item 2 only (item 1 was completed by earlier work before this plan); the docs-branch SKILL.md `Failure semantics (sync):` paragraph now enumerates the `invalid docs/* branches` and `Refusing unsafe shadow path` aborts beside the plan-mandated exit-1 classes; execution evidence docs/reviews/2026-10-03-exec-review-docs-branch-sync-abort-enumeration-r1.md; origin fold-deleted 2026-10-04 in the backlog-root fold pass.
