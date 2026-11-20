# Plan: order the done closeout's finalize before worktree teardown

Backlog origin: docs/history/backlog/2026-11-18-done-finalize-teardown-order-conflict.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-18-plan-review-done-finalize-teardown-order-conflict-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: yes (e53f03ca84ae26c62294b5c3a3055f1a2f3ecce3)
Authoring claim: 2026-11-18-done-finalize-teardown-order-conflict.md (session sess_c28fb710-699f-4d79-bfae-232376228347)

## Terms

- done closeout: the done skill's runner sequence (setup, learn, commit, finalize) run once at a session's final boundary.
- finalize: the done runner's `finalize` subcommand; its manifest leg re-verifies the session manifest's repo_root fingerprint against the invoking checkout.
- owner checkout: the checkout holding the run's done-session scratch and manifest; the run worktree for a worktree-placement run.
- teardown: the worktree removal and branch deletion legs of a closeout.
- Operator branch closeout: the done skill's gate-authorized sequence (quiesce writers, residue sweep, closeout gate, inventory verification, worktree removal, ref deletion); the only sanctioned branch deletion.
- gate-removal: the `worktree_closeout_migrate.py gate-removal` subcommand; the migration-backed removal gate whose `OUTCOME: pass` authorizes removal.
- closeout migration manifest: the `closeout-migration.json` record the migration writes; the operand gate-removal and its branch-only mode consume.
- branch-only gate-removal: gate-removal's mode for a branch ref with no linked worktree; requires an explicit `--migration-manifest`.
- commit run: the done runner's `commit` subcommand span (Steps 2 and 3), owning the landing sweep, the docs-branch sync, and the captured-tree landing.
- record mirror: the transfer of the run's gitignored review records and session logs to the primary checkout's homes.

## Why

The done skill's own step text places the Operator branch closeout's removal sequence inside the commit run, while its finalize must run from the owner checkout the removal destroys; a closeout following the written order can tear down the worktree first and then fail finalization, misclassifying an invalid recovery as complete. The plan pins the written order in the done skill and the execute-plan closeout to the finalize-from-owner-checkout rule the lessons corpus already owns, without touching the runner surfaces that already enforce and explain the constraint.

## Gist & Examples

TLDR: The done closeout's worktree teardown is re-ordered to run after finalize, pinning the written sequence across both skill files to the finalize-from-owner-checkout rule (code-quality).

Before: a worktree-placement done run follows Step 2's written order, removes the run worktree inside the commit run, and Step 6's finalize then refuses from the primary checkout on the manifest leg's identity check. After: Step 2 migrates, verifies presence, and egresses the migration manifest only; finalize runs from the original owner checkout; the Operator branch closeout runs after finalize, and a closeout reaching finalize post-teardown reports the failed leg without a reconstructed witness.

Before: execute-plan Phase 5's ad-hoc-worktree closeout names no position for its removal legs relative to the done finalize. After: its removal legs run only after finalize completed from the original owner checkout, the same honest-failure disposition applies, and the migration manifest is egressed before any removal so a retained branch keeps its branch-only gate operand.

Edge cases: an already-torn-down closeout reports the failed finalize leg and releases the locks (never fabricates the leg from a reconstructed checkout); a retained branch's later branch-only gate-removal still has its migration manifest.

## Outcome

A done closeout that follows its written skill text always reaches finalize from the original owner checkout before any worktree removal or branch deletion.

- The commit run's migration no longer carries a removal order; it migrates, verifies presence, and egresses the closeout migration manifest.
- The Operator branch closeout sequence runs after finalize, with the finalize-before-removal order stated where the closeout reads.
- A closeout whose worktree is already gone reports the failed finalize leg honestly and never treats a reconstructed checkout or copied manifest as a completion witness.
- execute-plan Phase 5's ad-hoc-worktree closeout states the same post-finalize position and egress duty.

Gate delta: prose-only reordering across two skill files; net machinery across refusal classes, hard gates, fences, protocol layers, schema fields, and dispatch-pausing conditions: none added and none removed; the two added prose duties (the migration-manifest egress before removal; the post-finalize ordering with the honest-failure disposition) mirror the duties the lessons corpus entries #317 and #326 already own and close the witnessed sequence contradiction; no blocking review-layer duty declared; no gate or fence added, so no gate-liveness ledger citation applies.

## Assumptions

- assume the correction is skill-text reordering only, no script change; basis: the finalizer's identity-mismatch refusal already carries the post-removal disposition and cites the finalize-before-removal rule (scripts/done_sweep_gates_lib.py, the refusal string naming development_lessons.md #326), and the wrapper's owner-checkout resolution already enforces the binding constraint mechanically.
- assume the Operator branch closeout paragraph moves whole, not re-scoped; basis: its sequence steps (quiesce, residue sweep, closeout gate, inventory, removal, ref deletion) are already the only sanctioned branch deletion and need no content change to run post-finalize.
- assume the docs-branch sync and the landing commit stay at their current commit-run position; basis: the migration stays before the sync and the sync before the landing commit (done Step 2), and neither leg depends on worktree removal.
- Decision receipts (maintenance-selected arm, one per origin concern): the ordering concern fixes the sequence by moving the removal authorization after finalize rather than weakening finalize's owner-checkout binding, because the manifest leg's root fingerprint is the incident's actual guard and the rule stands while the text stops contradicting it; the retained-branch concern egresses the migration manifest before removal rather than reconstructing it later, because the lessons corpus names reconstruction as the sanctioned recovery of a lost manifest, never the plan; the already-torn-down concern records the honest-failure disposition rather than a completion substitute, because the lessons corpus explicitly rejects a reconstructed checkout as a completion witness.

Decision points requiring a grill: none remain.

## Standing constraints

- Operative skill text carries no incident narrative and cites no backlog path; land the rule, not the story (repository anti-growth rule). Lesson-number citations to the lessons corpus stay allowed (the amended files already use them).
- Skill-text growth stays within the byte-budget gate's blocking ceilings; `python3 scripts/skill_text_budget.py --check` must exit 0 after the amendment.
- Em dashes never enter the amended text; every task runs the em-dash gate over the scoped changes in added-lines form, plus the file-mode gate over the done skill file (the execute-plan module carries a pre-existing em dash outside this plan's spans, which the freeze note protects).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every removal leg sits strictly after finalize in the amended text, and finalize's owner-checkout binding is unchanged
- consistency: the done skill's workflow-continuity summary, Step 2, Step 6, and execute-plan Phase 5 describe one teardown order
- minimality: only the prescribed spans change; no drive-by rewrites
- anti-growth: no incident narrative and no backlog-path citation in the amended spans; the byte-budget gate exits 0

**Done when:**
- the Validation Commands block passes green over the amended tree
- the em-dash gate, the public hygiene scan, and the pre-round readiness gate pass over the plan bytes

**Ship when:**
- none; the change is repository-verifiable prose only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` (Task 1)
- `agents/skills/execute-plan/archive-and-cleanup.md` (Task 2)

**Tests:**
- none; validation is the grep-based block below over the amended text, plus the repository gates it invokes.

Partially-in-scope freeze note: in each listed file, only the spans the tasks prescribe may change; all other lines in both files are frozen; reject any review finding that touches them.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh` and `scripts/done_sweep_gates_lib.py`; the runner surfaces already carry the post-removal disposition and the owner-checkout enforcement, and no origin names them as edit targets.
- `docs/history/plans/completed/2026-10-31-done-finalize-manifest-leg-post-removal-ordering.md`; completed-history bytes are immutable context, not an edit surface.
- `docs/maintenance/development_lessons.md`; the lessons corpus already owns the rule statements this plan pins into skill text.
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/execute-plan/worktree-first.md`; the Worktree-first standard already orders transfer-out before deletion (lifecycle steps 5 and 6) and no origin names them.

## Validation Commands

Authoring-time record (2026-11-18, probe over the base bytes): every positive pin below counts 0 today in both scoped files, the absence pins count 1 today (the old Step 2 lead-in fragment `never removes the worktree before its gitignored review artifacts` and the old continuity tail `the report (Step 7)` preceded by the finalize arrow), the Operator branch closeout paragraph sits at its pre-move position (the only `branch closeout` occurrence in the done skill, inside Step 2), and the runner-side refusal probe confirms the post-removal disposition text is present in scripts/done_sweep_gates_lib.py, so the block is red as a whole before the tasks land and green exactly when they are. The block passes `bash -n` clean.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
DONE="agents/skills/done/SKILL.md"
AC="agents/skills/execute-plan/archive-and-cleanup.md"
test -f "$DONE" || { echo "missing $DONE"; exit 1; }
test -f "$AC" || { echo "missing $AC"; exit 1; }

expect_absent() {
  rc=0; grep -qF -- "$1" "$2" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "FORBIDDEN PRESENT: $1"; exit 1; fi
  if [ "$rc" -ge 2 ]; then echo "TOOL ERROR rc=$rc on: $1"; exit 1; fi
}
expect_present() {
  rc=0; grep -qF -- "$1" "$2" || rc=$?
  if [ "$rc" -ne 0 ]; then echo "MISSING (rc=$rc): $1"; exit 1; fi
}
expect_count() {
  n=$(grep -oF -- "$1" "$2" | wc -l | tr -d ' ')
  if [ "$n" -ne "$3" ]; then echo "COUNT MISMATCH: $1 got $n want $3"; exit 1; fi
}

# G1 Task 1 Span A: migration removes no worktree; old removal order phrasing gone (Task 1)
expect_count 'removes no worktree in this step' "$DONE" 1
expect_absent 'never removes the worktree before its gitignored review artifacts' "$DONE"

# G2 Task 1 Span A: migration-manifest egress duty present (Task 1)
expect_count 'so a retained branch keeps its migration-manifest operand' "$DONE" 1

# G3 Task 1 paragraph move: label present exactly once, sitting after Step 6 and before Step 7 (Task 1)
expect_count 'Operator branch closeout (post-finalize teardown' "$DONE" 1
expect_count 'runs only after the finalize of Step 6 completed from the original owner checkout' "$DONE" 1
LN_S6=$(grep -n '^## Step 6' "$DONE" | cut -d: -f1)
LN_S7=$(grep -n '^## Step 7' "$DONE" | cut -d: -f1)
LN_LBL=$(grep -n 'Operator branch closeout (post-finalize teardown' "$DONE" | cut -d: -f1)
if [ -z "$LN_S6" ] || [ -z "$LN_S7" ] || [ -z "$LN_LBL" ]; then echo "POSITION: anchors missing"; exit 1; fi
if [ "$LN_LBL" -le "$LN_S6" ] || [ "$LN_LBL" -ge "$LN_S7" ]; then echo "POSITION: closeout paragraph not between Step 6 and Step 7"; exit 1; fi

# G4 Task 1 Span C: finalize-before-removal order and honest-failure disposition in Step 6 (Task 1)
expect_count 'The finalize runs before any worktree removal or branch deletion' "$DONE" 1
expect_count 'never treat a reconstructed checkout or copied manifest as a completion witness' "$DONE" 1

# G5 Task 1 Span E: workflow continuity names the post-finalize teardown (Task 1)
expect_count 'the post-finalize Operator branch closeout teardown' "$DONE" 1

# G6 Task 2 Span D: Phase 5 post-finalize ordering, honest-failure disposition, egress clause (Task 2)
expect_count 'completed from the original owner checkout' "$AC" 1
expect_count 'never treat a reconstructed checkout as a completion witness' "$AC" 1
expect_count 'so a retained branch keeps its branch-only gate operand' "$AC" 1

# G7 repository gates over the amended text (both tasks)
BASE=$(git merge-base HEAD main 2>/dev/null || git rev-parse main)
bash scripts/check-no-em-dash.sh added-lines --base "$BASE" || { echo "em-dash added-lines gate failed"; exit 1; }
bash scripts/check-no-em-dash.sh file "$DONE" || { echo "em-dash file gate failed"; exit 1; }
python3 scripts/skill_text_budget.py --check >/dev/null 2>&1 || { echo "byte-budget gate failed"; exit 1; }
bash scripts/scan-public-hygiene.sh >/dev/null 2>&1 || { echo "hygiene scan failed"; exit 1; }

echo "validation: all gates green"
```

### Task 1: done skill teardown reordering

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `Preserve Gitignored Docs and Instructions` in `agents/skills/done/SKILL.md`
- `Release project done lock` in `agents/skills/done/SKILL.md`
- `Workflow continuity` in `agents/skills/done/SKILL.md`

Prescribed edits, verbatim spans; each old span is text present today in the named location, each new span replaces or relocates it exactly, and all other bytes of the file are unchanged.

Span A sits inside the Step 2 migration paragraph as its second sentence (the paragraph opens with the sentence stating the docs-branch sync position); the old span below is that full sentence, byte-present today.

Span A, old:
"When the session runs in an ad-hoc worktree, the commit run first migrates the run's review staging docs and session logs to the main checkout (`worktree_closeout_migrate.py migrate`) and never removes the worktree before its gitignored review artifacts verify present in the main checkout; the gated removal check `python3 scripts/worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree <worktree>` (for a dated plan directory, `<plan>` is the `PLAN.md` charter inside the dated directory, so the gate derives the date-stripped directory `<PLAN_SLUG>` for its default manifest lookup per the execute-plan canonical session-slug rule) passes (`OUTCOME: pass`) before any removal, and a refusal names what to resolve and re-run."

Span A, new:
"When the session runs in an ad-hoc worktree, the commit run first migrates the run's review staging docs and session logs to the main checkout (`worktree_closeout_migrate.py migrate`) and removes no worktree in this step: the migration verifies the run's gitignored review artifacts present in the main checkout and copies the closeout migration manifest (`closeout-migration.json`) to the primary checkout's session home before any worktree removal, so a retained branch keeps its migration-manifest operand for the later branch-only gate-removal (development_lessons.md #317); the removal authorization itself (the gated removal check `python3 scripts/worktree_closeout_migrate.py gate-removal --plan <plan> --target <primary> --worktree <worktree>` (for a dated plan directory, `<plan>` is the `PLAN.md` charter inside the dated directory, so the gate derives the date-stripped directory `<PLAN_SLUG>` for its default manifest lookup per the execute-plan canonical session-slug rule) passes (`OUTCOME: pass`) before any removal, and a refusal names what to resolve and re-run) belongs to the post-finalize Operator branch closeout below, never to this step."

Span B relocates the whole Operator branch closeout paragraph: the paragraph is the only `branch closeout` occurrence in the file today, it opens with the bold label below, and it sits in Step 2 between the docs-branch sync runner paragraph and the "After the sync, verify gitignored files are still on disk" paragraph. Cut the whole paragraph from that position and insert it, byte-identical except for the label and preamble below, immediately after the Step 6 paragraph beginning "Finalize also assembles the report inputs" and immediately before the `## Step 7: Report outcome to the user` heading.

Span B, old label and first sentence:
"**Operator branch closeout (operator-run when stand-alone; the only sanctioned branch deletion; plan 2026-10-19-gate-removal-closeout-accounting Task 2):** the gate's `branch-closeout` output authorizes this sequence only for an ancestry-accounted or exact-tree-only branch whose identity and artifact checks passed;"

Span B, new label and first sentences:
"**Operator branch closeout (post-finalize teardown; operator-run when stand-alone; the only sanctioned branch deletion; plan 2026-10-19-gate-removal-closeout-accounting Task 2):** this sequence runs only after the finalize of Step 6 completed from the original owner checkout, per the finalize-before-removal rule (development_lessons.md #326: the finalize runs from the run worktree before any worktree removal or branch deletion). The gate's `branch-closeout` output authorizes this sequence only for an ancestry-accounted or exact-tree-only branch whose identity and artifact checks passed;"

Every other byte of the moved paragraph, through its final sentence ending with the Resource cleanup disposition contract reference, is unchanged.

Span C appends to the Step 6 finalize paragraph (the paragraph beginning "Run finalize from the owner checkout"), immediately after its sentence ending "rerun the identical command from the owner checkout." and before the paragraph's remaining sentences, which stay unchanged:

Span C, appended text:
" The finalize runs before any worktree removal or branch deletion (development_lessons.md #326), and the Operator branch closeout below owns every removal leg after it. When the worktree has already been removed before this finalize, the manifest leg's identity-mismatch refusal is final: report the failed finalize leg honestly with the refusal's recorded disposition, let the release steps run, and never treat a reconstructed checkout or copied manifest as a completion witness."

Span E replaces the workflow-continuity sequence tail inside the Invocation section's Workflow continuity paragraph:

Span E, old:
"→ `done_run.sh finalize` (Step 6) → the report (Step 7)."

Span E, new:
"→ `done_run.sh finalize` (Step 6) → the post-finalize Operator branch closeout teardown → the report (Step 7)."

- [x] Span A is replaced verbatim: the migration removes no worktree, egresses the closeout migration manifest, and names the removal authorization as belonging to the post-finalize closeout [class: IMPLEMENTATION_REQUIRED]
- [x] Span B relocation: the Operator branch closeout paragraph is cut from Step 2 and inserted whole between the Step 6 report-inputs paragraph and the Step 7 heading, with only the label and preamble amended [class: IMPLEMENTATION_REQUIRED]
- [x] Span C is appended verbatim to the finalize paragraph: the teardown-order sentence and the honest-failure disposition [class: IMPLEMENTATION_REQUIRED]
- [x] Span E replaces the continuity tail verbatim: the sequence names the post-finalize teardown between finalize and the report [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block: expect G1 through G5 green and the block failing inside G6 at this task point [class: REPOSITORY_TEST]
- [x] Commit: `done: finalize precedes worktree teardown in the closeout sequence` [class: IMPLEMENTATION_REQUIRED]

### Task 2: execute-plan Phase 5 alignment

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/archive-and-cleanup.md`

Primary class anchors:
- `Ad-hoc-worktree closeout` in `agents/skills/execute-plan/archive-and-cleanup.md`

Prescribed edit, verbatim span; the old span is the paragraph head present today, the new span replaces it exactly, and all other bytes of the file are unchanged.

Span D sits at the head of the Phase 5 paragraph labeled "Ad-hoc-worktree closeout (before any removal)".

Span D, old:
"**Ad-hoc-worktree closeout (before any removal):** the run's worktree closeout is the canonical section's named **Transfer-out-and-deletion implementation** (Worktree-first standard, lifecycle steps 5 and 6): detect the worktree, migrate the gitignored run artifacts to the primary checkout under the canonical baseline rule in the Worktree-first standard, pass the tracked-dirt inversion check,"

Span D, new:
"**Ad-hoc-worktree closeout (before any removal):** the removal legs of this closeout run only after the run's final done closeout's `finalize` completed from the original owner checkout (development_lessons.md #326's finalize-before-removal order); when teardown already happened before that finalize, report the failed finalize leg honestly per the runner's identity-mismatch disposition and never treat a reconstructed checkout as a completion witness. The run's worktree closeout is the canonical section's named **Transfer-out-and-deletion implementation** (Worktree-first standard, lifecycle steps 5 and 6): detect the worktree, migrate the gitignored run artifacts to the primary checkout under the canonical baseline rule in the Worktree-first standard, copying the closeout migration manifest to the primary session home before any removal so a retained branch keeps its branch-only gate operand (development_lessons.md #317), pass the tracked-dirt inversion check,"

- [x] Span D is replaced verbatim: the post-finalize ordering condition, the honest-failure disposition, and the migration-manifest egress clause [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full Validation Commands block: expect all gates green at this task point [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: phase 5 teardown runs after the done finalize` [class: IMPLEMENTATION_REQUIRED]
