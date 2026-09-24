# Plan: Returned-for-ask semantics completion

Backlog origin: `docs/history/backlog/2026-08-28-returned-for-ask-semantics.md` (promoted backlog item)
Source review: `docs/reviews/2026-08-28-fix-risk-triage-skills-code-review-r8.md` (Medium x2, Low x1)

## Terms

- **returned-for-ask**: a non-terminal record state for a review finding that triage held `pending` for the fix-risk user decision; recorded as the literal marker `returned-for-ask` on the finding's Analysis section while Status/Triage stay `pending`.
- **fix-risk user decision**: the user's fix-vs-backlog direction for a finding presented under `receiving-review` **Fix-risk triage when fixes regenerate findings** (Hard Gate 23 in `execute-plan`).
- **canonical scope phrase**: the exact wording "a finding held `pending` for the fix-risk user decision" : the single exception scope shared by all four backlog-shield call sites.
- **outstanding presentation**: a returned-for-ask record whose question has not yet been relayed to the user (or returned to the orchestrator / turned into a stop for direction in a non-interactive run).

## Assumptions

- assume gate numbering drift: the backlog item cites "Hard Gate 17" for the fix-risk ask; current `execute-plan` numbers the fix-risk gate Hard Gate 23 (17 is now the no-per-step-continuation-prompts gate). This plan anchors to current text; basis: grep of `agents/skills/execute-plan/SKILL.md` (Hard Gate 17 at the per-step-continuation bullet, Hard Gate 23 referenced from the Step 3.3 gate and Step 3.5 rows).
- assume instruction-only change: this repo has no test harness for SKILL.md files, so validation is fail-closed grep commands, not unit tests; basis: repo layout (skills are Markdown instruction sets).
- assume the canonical scope phrase from the backlog item's candidate fix, which two of the four sites already use verbatim; basis: grep evidence recorded at authoring time (execute-plan Step 3.3 gate #4 and subagent-prompts step 7 carry it; receiving-review Backlog capture does not).

## Gist & Examples

Three findings from the 2026-08-28 fix-risk-triage-skills review r8 all concern the **returned-for-ask** state that the r7 consumer sweep introduced but never fully specified. This plan completes the semantics with three aligned edits; all are Markdown instruction changes, no runtime code.

1. **One exception scope across four sites.** Today the `receiving-review` Backlog capture shield protects only "a must-stay-blocking finding held for the fix-risk user decision", while the Fix-risk closing paragraph, the execute-plan Step 3.3 verification gate #4, and subagent-prompts step 7 all protect the broader set (any Critical/High/Medium finding held `pending` for the ask). A literal reader hits a contradiction for a non-blocking High finding awaiting the user: the narrow shield does not apply, so the reader must backlog the finding now, conflicting with the do-not-backlog-until-answered instruction. Fix: replace the narrow shield with the canonical scope phrase (the wording the other three sites already use).

2. **One defined record form and location.** "returned-for-ask" appears at three call sites but no document says what the record looks like or where it lives; it is not a staging Status/Triage value (done/drop/pending/deferred), and review-staging's receiving-review consumer row covers triage updates and Blocking re-evaluation but not this state. Fix: define the record once in review-staging's consumer row : the literal marker `returned-for-ask` on the finding's Analysis section, Status/Triage stay `pending`, Blocking unchanged : and point every call site at that definition.

   Before: a finding's Analysis section says only "pending"; three skills disagree on what "recorded as returned-for-ask" produces.
   After: the Analysis section carries a `returned-for-ask` marker line with the question to relay; Status/Triage remain `pending` until the user decides.

3. **The ask is mandated before the next fold.** Hard Gate 17 sanctions the interactive ask and the Fix-risk closing says who asks, but nothing obligates the orchestrator to relay an outstanding presentation before incrementing `review_round`; an interactive loop can legally fold on a rule-2-frozen finding until the round cap. Fix: a new Step 3.3 verification-gate item : an outstanding returned-for-ask presentation must be performed (interactive) or escalated (returned to the orchestrator / stop for direction, non-interactive) before returning to Step 3.1 : mirrored in review-loop orchestration rule 4.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the canonical scope phrase appears verbatim at the three backlog-shield call sites (receiving-review Backlog capture, execute-plan Step 3.3 gate #4, subagent-prompts step 7), the Fix-risk closing paragraph carries the broad `pending` scope with the record pointer, and no file retains the narrow "must-stay-blocking" shield wording.
- consistency (single source): the record form/location is defined exactly once (review-staging consumer row); every other mention points at it rather than restating the definition.
- enforceability: the outstanding-ask obligation is a dedicated gate row/rule sentence in both execute-plan and review-loop, each with its own dedicated validation grep.
- validation soundness: the Validation Commands block is fail-closed (explicit abort on every miss and on every forbidden match), and each changed-site check was RED-today at authoring time.

**Done when:**
- all tasks checked; the Validation Commands block exits 0 against the post-edit tree.

**Ship when:**
- the next review loop that reaches a returned-for-ask state applies the aligned semantics with no literal-reader conflict (observable only in a future live run; human-owned; prose only).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/receiving-review/SKILL.md` (Backlog capture exception paragraph; Fix-risk closing paragraph)
- `agents/skills/review-staging/SKILL.md` (receiving-review consumer row)
- `agents/skills/execute-plan/SKILL.md` (Step 3.3 verification gate)
- `agents/skills/execute-plan/subagent-prompts.md` (step 7)
- `agents/skills/review-loop/SKILL.md` (orchestration rule 4)

**Tests:**
- none; instruction-only repo (see Assumptions)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; pre-existing foreign working-tree modification, unrelated to this plan's semantics edits
- `README.md`; no skill is added, removed, or renamed, so the catalog is unaffected
- any Hard Gate renumbering; the plan anchors to current gate numbers and does not renumber gates

## Validation Commands

```bash
#!/usr/bin/env bash
# Fail-closed: aborts on every missing obligation and on every forbidden match.
set -u
fail() { echo "FAIL: $1"; exit 1; }
RR=agents/skills/receiving-review/SKILL.md
RS=agents/skills/review-staging/SKILL.md
EP=agents/skills/execute-plan/SKILL.md
SP=agents/skills/execute-plan/subagent-prompts.md
RL=agents/skills/review-loop/SKILL.md
for f in "$RR" "$RS" "$EP" "$SP" "$RL"; do test -f "$f" || fail "missing file $f"; done

CANON='a finding held `pending` for the fix-risk user decision'
grep -Fq "$CANON" "$RR" || fail "canonical scope phrase missing in receiving-review"
grep -Fq "$CANON" "$EP" || fail "canonical scope phrase missing in execute-plan"
grep -Fq "$CANON" "$SP" || fail "canonical scope phrase missing in subagent-prompts"

grep -Fq 'literal marker `returned-for-ask` on the finding' "$RS" \
  || fail "returned-for-ask record definition missing in review-staging consumer row"
grep -Fq 'recorded as returned-for-ask per review-staging' "$RR" \
  || fail "record pointer missing in receiving-review"
grep -Fq 'stays `pending` and is recorded as returned-for-ask per review-staging' "$RR" \
  || fail "Fix-risk closing record pointer missing in receiving-review"
grep -Fq 'returned-for-ask per review-staging' "$SP" \
  || fail "subagent-prompts step 7 does not point at the review-staging definition"

grep -Fq 'returned-for-ask presentation is outstanding' "$EP" \
  || fail "outstanding-presentation gate item missing in execute-plan"
grep -Fq 'before returning to Step 3.1' "$EP" \
  || fail "pre-fold obligation wording missing in execute-plan"
grep -Fq 'never increments its round with the ask outstanding' "$RL" \
  || fail "review-loop rule 4 mirror missing"

# Forbidden: the old narrow shield, swept across every must-fix file (any site may
# retain it). Flattens newlines first (the phrase can wrap).
# The [g] bracket escape is intentional (it keeps the pattern from matching a
# verbatim copy of itself); do not normalize it to a plain g.
for f in "$RR" "$RS" "$EP" "$SP" "$RL"; do
  if tr '\n' ' ' < "$f" | grep -q 'a must-stay-blocking findin[g] held for the fix-risk'; then
    fail "old narrow shield wording still present in $f"
  fi
done
echo "ALL VALIDATION CHECKS PASS"
```

### Task 1: Define the returned-for-ask record in review-staging and point the provider at it

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

- [x] In review-staging's skill-consumer table, extend the `receiving-review` row's contract cell to add, after the Blocking re-evaluation clause: "A returned-for-ask record is NOT a Status or Triage value: record the literal marker `returned-for-ask` on the finding's Analysis section (with the question to relay); Status and Triage stay `pending` and the Blocking value is unchanged until the user decides." This row is the single definition; do not restate the form elsewhere.
- [x] In receiving-review's Fix-risk closing paragraph, extend the clause "until answered, the finding stays `pending`" to "until answered, the finding stays `pending` and is recorded as returned-for-ask per review-staging's receiving-review consumer row" so the provider points at the single definition.
- [x] In execute-plan subagent-prompts step 7, extend the exception clause "record it as returned-for-ask, not backlogged" to "record it as returned-for-ask per review-staging's receiving-review consumer row, not backlogged" so the call site points at the single definition.

### Task 2: Align the exception scope to the canonical phrase at all four sites

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

- [x] In receiving-review's Backlog capture exception, replace the narrow shield "a must-stay-blocking finding held for the fix-risk user decision ... stays `pending` and is recorded as returned-for-ask, not backlogged" with the canonical scope phrase: "a finding held `pending` for the fix-risk user decision (**Fix-risk triage when fixes regenerate findings**) is recorded as returned-for-ask per review-staging's receiving-review consumer row, not backlogged"; keep the trailing "once the user decides, apply this section to it" sentence unchanged.
- [x] Confirm execute-plan Step 3.3 verification gate #4 and subagent-prompts step 7 already carry the canonical scope phrase verbatim; adjust only if wording drifted, keeping the exact string "a finding held `pending` for the fix-risk user decision" present in both files.

### Task 3: Mandate the ask before the next fold

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [x] Add a new item to the Step 3.3 verification gate (after the current item 5): "A returned-for-ask presentation is outstanding only until it is discharged: an interactive run performs the fix-risk ask before returning to Step 3.1 (the Step 3.5 counter update waits for the answer, or takes the fix-risk stop row); a non-interactive run returns the question to its orchestrator or stops for direction per the Fix-risk section, and never increments its round with the ask outstanding."
- [x] In review-loop orchestration rule 4 (Fix-risk triage before more folding), append: "A returned-for-ask presentation outstanding is a stop for user direction: relay the ask and get the answer before the next fold or iteration; the loop never increments its round with the ask outstanding."
- [x] Check no sibling paragraph (Step 3.5 launch paragraph, Hard Gate 17 bullet) contradicts the new obligation; if one reads as permitting a round increment with the ask outstanding, reconcile its wording in the same commit.

### Task 4: Validate and commit

Files: none new.

- [x] Run the full Validation Commands block; expect exit 0 ("ALL VALIDATION CHECKS PASS"). Before running, confirm each check is RED-today against the pre-edit tree for the sites this plan changes (authoring-time evidence: canonical phrase absent from receiving-review; record definition absent from review-staging; outstanding-ask wording absent from execute-plan and review-loop; the Fix-risk closing pin 'stays `pending` and is recorded as returned-for-ask per review-staging' is RED-today because today's matching Backlog capture sentence ends "returned-for-ask, not backlogged" with no review-staging pointer; forbidden sweep matches receiving-review today).
- [x] Run `bash -n` over the Validation Commands block and run a pin-vs-prescription audit: for each pinned span in the Validation Commands, verify it occurs in the prescribed task text (occurrences inside the Validation Commands block itself are the checker's own literals and do not count toward the audit).
- [x] Run the public hygiene scan (exit 0 required).
- [x] Stage ONLY this plan's files (the five skill files plus this plan); leave the foreign modified `scripts/plan_readiness.py` unstaged. Commit: `skills: complete returned-for-ask semantics (scope, record, pre-fold ask gate)`

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-08-28-returned-for-ask-semantics.md: disposition folded into 2026-09-04-returned-for-ask-semantics.md (2026-09-25); per-item file deleted.
