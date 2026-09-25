# Plan: 2d cap-row cell session-note definition hoist

Backlog origin: `docs/history/backlog/2026-09-03-2d-cell-session-note-duplication.md`
Source review: `docs/reviews/2026-09-02-r5-residuals-fixes-code-review-r1.md` (finding DS-3, Low, design-simplicity)

## Assumptions

- assume the target file is the ARCHIVED copy `docs/plans/completed/2026-09-02-phase3-residue-pass.md`; basis: the residue-pass plan was executed and archived after the backlog item was written, so the backlog's `docs/plans/2026-09-02-phase3-residue-pass.md` path no longer exists on disk (verified by listing); editing the archived copy is the established rider pattern (the 2f prose-lows plan makes the same assumption and edits the same archived file).
- assume scope is the archived residue-pass plan plus the r5-residuals plan's Validation Commands pin only; the live `agents/skills/execute-plan/SKILL.md` cap row already carries the de-duplicated form (`otherwise write the same short session note`, line ~648) and is out of scope; basis: on-disk content.
- assume this plan is sequencing-independent of the 2f paragraph-prose-lows plan: both ride on the same archived file but in disjoint regions (the 2d cap-row cell vs the prescribed 2f paragraph), and this plan's Validation Commands do not pin any 2f span; basis: on-disk region locations.
- assume the session-note definition is hoisted to the FRONT of the cell (before the reconciliation branch), per the backlog's suggested fix; the resulting `otherwise write the same short session note` back-reference uses the same wording as the live `execute-plan` skill's otherwise-branch (the live row keeps its definition inside the reconciliation branch, so the two surfaces remain structured differently — only the back-reference wording mirrors; r1-F2).

## Terms

- **2d cap-row cell**: the action cell of the Step 3.5 table row beginning `` | `review_round` has reached `max_review_rounds` ``, as prescribed by Task 2d (`` **2d (ds-F1, cap row)** ``) of the residue-pass plan.
- **session-note definition**: the parenthetical `` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) ``.
- **r5 2d pin**: the `expect_once "$RP"` line in the r5-residuals plan's Validation Commands block that pins the reconciliation-branch copy of the session-note definition.

## Gist & Examples

The prescribed 2d cap-row cell states the session-note definition twice — once in the reconciliation branch and once in the otherwise-branch (finding DS-3: verbatim duplication in a cell of the regenerating-wording family that churned every review round). This plan hoists the definition to the front of the cell (one occurrence, attached to the leading `write a short session note under ...` clause) and turns both branches into short back-references, then syncs the r5 2d pin, which counts exactly the reconciliation-branch copy and would fire (count 0) against the hoisted cell if left as-is.

Before (cell shape, after the leading `Stop; `):

``where a reconciliation trigger also holds, review-reconciliation runs first, then a short session note under `{tmp_dir}/` (DEF) is written and the user ask happens (...); where fix-risk stop conditions also hold (...), take the Fix-risk direction per Hard Gate 23 (...), still writing the short session note; otherwise write a short session note under `{tmp_dir}/` (DEF) and ask the user whether to continue, ...``

After:

``write a short session note under `{tmp_dir}/` (DEF); where a reconciliation trigger also holds, review-reconciliation runs first, then the session note is written and the user ask happens (...); where fix-risk stop conditions also hold (...), take the Fix-risk direction per Hard Gate 23 (...), still writing the short session note; otherwise write the same short session note and ask the user whether to continue, ...``

(DEF = the session-note definition; the full exact text is pinned in the task below.) Nothing else in the cell changes; the Fix-risk branch's `still writing the short session note` and the archiving-acceptance clause are untouched. Edge case: the hoisted front clause must keep the `;` after the definition so the reconciliation branch remains a co-hold ordering, not a replacement of the note.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the session-note definition occurs exactly once in the whole residue-pass plan (verified today at 2), and every behavioral fact of the old cell (reconciliation-first ordering, Fix-risk stop-and-ask with budget folded in, otherwise-branch budget question, archiving acceptance clause) survives verbatim.
- maintainability: the regenerating-wording family's duplication in the 2d cell is gone; both branches reference one definition.
- contract consistency: the r5-residuals plan's counting pin for the 2d cell is synced in the same edit (check 4), and the r5 Validation Commands block remains shell-valid after the pin edit (`bash -n`, check 5). The r5 block is NOT re-run end-to-end: its `RP` variable still points at the pre-archive live path, which is absent on disk, so a full re-run exits at its missing-file guard for reasons unrelated to this plan (r1-F1).

**Done when:**
- The Validation Commands block below exits 0 (it is RED today: the definition count is 2, both duplicated branch spans are present, and the hoisted pin and synced r5 pin are absent).

**Ship when:**
- None; repository-local documentation change only.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `docs/plans/completed/2026-09-02-phase3-residue-pass.md` (2d cap-row cell only; all other content frozen)

**Tests:**
- `docs/plans/completed/2026-09-02-r5-residuals-fixes.md` (the r5 2d pin line in the Validation Commands block only; the rest of the block and all task history frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; already carries the de-duplicated form on line ~648 (runtime skill, separate pass)
- `docs/plans/completed/2026-09-01-phase3-review-churn-control.md`; frozen completed-plan history, its session-note sentence is a different span
- `docs/history/backlog/2026-09-03-2d-cell-session-note-duplication.md`; stays in place under the backlog dir while this plan is open per the backlog lifecycle (archived to `backlog_completed_dir` only at plan completion)

## Validation Commands

```bash
RP=docs/plans/completed/2026-09-02-phase3-residue-pass.md
R5=docs/plans/completed/2026-09-02-r5-residuals-fixes.md
DEF='(rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run)'
NEWPIN='a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run); where a reconciliation trigger also holds'

# 1. session-note definition occurs exactly once in the whole residue-pass plan
#    (RED-today proof 2026-09-04: count is 2, both inside the 2d cell)
test "$(grep -oF "$DEF" "$RP" | wc -l | tr -d ' ')" -eq 1 || { echo "definition count != 1"; exit 1; }

# 2. duplicated branch copies are gone
#    (RED-today proof 2026-09-04: both strings present, count 1 each)
if grep -qF 'otherwise write a short session note under `{tmp_dir}/`' "$RP"; then echo "otherwise-branch duplication left"; exit 1; fi
if grep -qF 'then a short session note under `{tmp_dir}/`' "$RP"; then echo "reconciliation-branch duplication left"; exit 1; fi

# 3. hoisted front-of-cell pin present exactly once
#    (RED-today proof 2026-09-04: count 0)
test "$(grep -cF "$NEWPIN" "$RP")" -eq 1 || { echo "hoisted pin count != 1"; exit 1; }

# 4. r5 2d counting pin synced (fixed-string greps; regex line-anchors are not
#    portable across grep implementations — r2-F1. The `expect_once "$RP" '`
#    prefix occurs only on pin lines in the r5 file, so the historical [x]
#    checklist quote of the old span in r5 Task 3 cannot satisfy or fail the check)
#    (RED-today proof 2026-09-04: count 0)
test "$(grep -cF "expect_once \"\$RP\" '$NEWPIN'" "$R5")" -eq 1 || { echo "r5 pin not synced"; exit 1; }
if grep -qF "expect_once \"\$RP\" 'then a short session note under" "$R5"; then echo "stale r5 2d pin left"; exit 1; fi

# 5. r5 Validation Commands block still shell-valid after the pin edit
R5CHECK="$(mktemp)" || exit 1
awk '/^```bash$/{f=1;next} /^```$/{if(f){f=0}} f' "$R5" > "$R5CHECK" || { rm -f "$R5CHECK"; exit 1; }
bash -n "$R5CHECK" || { echo "r5 validation block shell error"; rm -f "$R5CHECK"; exit 1; }
rm -f "$R5CHECK"

echo "ALL VALIDATION PASS"
```

### Task 1: Hoist the session-note definition in the 2d cap-row cell and sync the r5 pin

Files:
- `docs/plans/completed/2026-09-02-phase3-residue-pass.md`
- `docs/plans/completed/2026-09-02-r5-residuals-fixes.md`

- [ ] In the residue-pass plan's Task 2d prescribed cell (the `` `where a reconciliation trigger also holds, ...` `` literal), replace the ENTIRE cell text after the leading `Stop; ` with this exact text (one edit; the Fix-risk branch middle and the archiving clause are carried over verbatim from the current cell):

    ``write a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run); where a reconciliation trigger also holds, review-reconciliation runs first, then the session note is written and the user ask happens (reconciliation changes which digest the next round reviews, not whether the user is asked); where fix-risk stop conditions also hold (their direction is taken whether or not a reconciliation trigger holds, but any such reconciliation still runs first), take the Fix-risk direction per Hard Gate 23 (a stop-and-ask) and fold the budget question (continue, backlog non-blocking residuals, standing continue, or stop) into that single ask rather than issuing both, still writing the short session note; otherwise write the same short session note and ask the user whether to continue, backlog non-blocking residuals, give a standing continue instruction, or stop; archiving with unresolved blocking findings additionally requires the user's explicit documented acceptance``

- [ ] In the r5-residuals plan's Validation Commands block, replace the line

    ``expect_once "$RP" 'then a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) is written and the user ask happens'``

    with

    ``expect_once "$RP" 'a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run); where a reconciliation trigger also holds'``

    (the pin moves from counting the reconciliation-branch copy to counting the single hoisted copy; it still occurs only in the prescribed cell text, never in the residue-pass block's own `$EP` pin lines, so self-count immunity holds)

- [ ] Run the plan's Validation Commands block → expect RED before the task (definition count 2, branch strings present, hoisted and synced pins absent; RED-today proofs recorded 2026-09-04 in the block comments) and GREEN after both edits land
- [ ] Commit: `plans: hoist 2d cell session-note definition, sync r5 pin`
