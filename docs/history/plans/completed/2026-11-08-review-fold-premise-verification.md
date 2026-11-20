# Plan: Review-plan Step 5 premise-verification fold-discipline item

Backlog origin: docs/history/backlog/2026-11-07-review-fold-premise-verification-duty.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-review-fold-premise-verification-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (f4fae6cd3781e350803a2c177a665cfa07e1d67b)
Authoring claim: review-fold-premise-verification.md (session sess_0831b9c3-12c1-4bd6-9bff-2312c4f3f59d)

## Terms

- **Fold batch**: a review-plan Step 5 pass that folds accepted findings into the plan artifact before the next round.
- **Load-bearing premise**: a factual claim a folded finding's fix wording leans on (a named function's signature and inputs, a cited call site's shape, a cross-family contract claim) whose falsehood would make the folded text wrong.
- **Accounting-surface re-derivation**: the existing Step 5 item 6 duty that mechanically re-derives the plan's accounting set after each fold batch.
- **Reconciliation fold batch**: the fold batch a review-reconciliation trigger runs, whose Fold-propagation probe binds the accounting-surface re-derivation; this plan's new item rides that same batch.
- **Premise-verification pass**: the new fold-discipline duty this plan adds beside it: re-derive each folded finding's load-bearing premises from the on-disk source in the same bounded pass.
- **Lesson 423**: the corpus record of the witnessed failure, `docs/maintenance/development_lessons.md` #423.

## Why

A fold batch restates each folded finding's claims as plan text without verifying them against the source. When a worker's code claim is wrong, the fold imports the error into the reviewed artifact and the next round's panel returns it as blocking findings, spending a whole round on fold defects. One bounded verification pass at fold time removes that round of churn.

## Gist & Examples

TLDR: review-plan Step 5 gains one fold-discipline item, a premise-verification pass over each folded finding's load-bearing factual claims against the on-disk source, so unverified worker premises stop importing fold-defect blocking findings into the next round; efficiency (the witnessed unverified triple cost four blocking findings and forced a reconciliation one round before the cap).

Before (today): the 2026-11-07 budget-resume-carrier-gc r3 fold batch wrote three unverified premises from worker reports into the plan (that clocked-order requests carry the discriminator field, that the census operation could register under the state-path-requiring dispatch family, that the fire path preserves the receipt the closeout discharge reads). The r4 panel code-verified the claims against source and returned four blocking findings plus a stale accounting surface, tripling the open-blocking count and firing the churn triggers; recovery forced a reconciliation with an operator gate one round before the loop's cap.

After (this plan): the same fold batch runs the premise-verification pass beside the accounting-surface re-derivation, and the duty binds every fold batch that runs Step 5, the reconciliation fold batch included (that batch already runs the sibling accounting-surface re-derivation under review-reconciliation's Fold-propagation probe, so the premise pass rides the same batch, not a second duty). Each folded finding's named signatures and inputs, cited call-site shapes, and cross-family claims are re-derived from the on-disk source in the same bounded pass; a premise the folder cannot verify in one read is verified with one more targeted read or reworded to the verified subset before it enters the artifact. Each of the three witnessed premises is one read away from its refutation (the family id on the request type, the required state path on the survey call, the supersede's receipt clearing on the fire path), so at fold time the folder either corrects the claim or rewords to the verified subset, and the r4 blocking inflation never forms.

Edge cases named: a premise verified false is reworded to the verified subset or corrected, never silently dropped together with the finding it carried; a premise needing more than the bounded pass's two reads is reworded to the verified subset rather than stalling the batch; the duty adds no validator and no new finding class, so a skipped verification surfaces through the existing fold-defect and accounting triggers, not through a new gate; the reconciliation batch inherits the duty through the same Step 5 item rather than a mirrored rule in review-reconciliation.

## Outcome

Fold batches verify imported factual claims before writing them, so fold-defect blocking findings stop recurring across review loops.

- The next fold batch that imports a wrong code claim catches it at fold time in the same bounded pass instead of spending the next review round on it.
- The witnessed failure class stays durably witnessed by one citation line in the skill text, with lesson 423 as the corpus record.
- No validator, gate, ledger, or other machinery is added.

Gate delta: one prose-only requirement added to the review loop's fold flow (the Step 5 premise-verification item), priced by the completed-integrity-failure witness (the 2026-11-07 r3-to-r4 fold-defect blocking inflation, four blocking findings recorded in the origin row and lesson 423); no machinery removed (the Gate delta counts machinery classes, not bytes; the byte growth is paid in the same edit by tightening item 6's witness-citation tail); no gate, validator, lock, ledger, refusal class, protocol layer, or schema field added or removed.

## Assumptions

- assume the new item inserts as Step 5 item 7 directly after the accounting-surface re-derivation (item 6) and the following items renumber (old 7 through 10 become 8 through 11); basis: the origin's placement instruction ("beside the accounting-surface re-derivation") and the verified absence of living references to the moved item numbers outside the pruned prompt-log entry prose (repo-wide grep, 2026-11-08; the pruned entry's own "Step 5 item 10" mention is removed by this landing's prune, and the completed 2026-09-30 fidelity-duties plan's frozen item-number tokens are immutable history, not living references).
- assume the skill-text citation of the witnessed failure is one line naming the failure class, with the narrative kept in the origin row and lesson 423; basis: the repository guidelines' witness-budget rule (the Skill text anti-growth rules section).
- assume lesson 423 stays the corpus record and is not edited; basis: the origin row's Suggested fix ("Place the project-corpus witness (lesson 423, same date) as the lesson-side record; this row is the fix-tracking artifact for the skill-text change").

Decision points requiring a grill: item placement beside item 6 with renumbering (source-resolved: origin row placement instruction, 2026-11-07, Task 1; living-reference absence outside the pruned prompt-log entry verified 2026-11-08); witness citation limited to one line in skill text (source-resolved: repository witness-budget rule, 2026-11-08, Task 1); no validator added (source-resolved: origin row machinery admission evidence and entry Rejected alternatives, 2026-11-07, Gate delta)

## Evaluation Criteria

**Quality dimensions:**
- correctness: the added item names the premise classes from the origin's Expected text (named function signature and inputs, cited call sites' shapes, cross-family claims the fix wording leans on) and carries the verify-or-reword escape with the same-bounded-pass bound
- anti-growth: the added item's bytes are offset by tightening the existing item 6 witness-citation tail in the same edit, the new item's own witness citation inside it is one line, and no Step 5 item's rule text changes beyond item 6's tightened citation tail and the renumbered item numbers
- compatibility: after renumbering, a repo-wide grep finds no stale numeric reference to the moved Step 5 items outside the pruned prompt-log entry prose

**Done when:**
- review-plan Step 5 carries the premise-verification item directly after the accounting-surface re-derivation item, with the following items renumbered and their text unchanged
- `bash scripts/check-no-em-dash.sh added-lines --base ca7181bf543421675d38b6f43fe5bfdb83b0ce63`, `bash scripts/scan-public-hygiene.sh`, and `bash scripts/check_maintenance_pins.sh` all exit 0
- the branch diff over `agents/skills/review-plan/SKILL.md` touches only the new item 7, the renumbered item numbers, and item 6's tightened witness-citation tail (diff inspection recorded in the task evidence)

**Ship when:**
- none stated (no external release condition; the change is repository skill text)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-plan/SKILL.md` (Task 1)

**Tests:**
- none (the change is skill text; verification rides the sweep suite and the grep witness, no test files are added)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; reason: lesson 423 stays the corpus record unchanged per the origin row
- `scripts/` validators and gates; reason: the machinery admission test rejects a validator for this duty (no witnessed mechanical shape; the entry's Rejected alternatives record the validator arm's refusal)

## Validation Commands

```bash
bash scripts/check-no-em-dash.sh added-lines --base ca7181bf543421675d38b6f43fe5bfdb83b0ce63
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
```

Validation preamble (authoring-time record, rule 29; per-round state lives in the review series):
- `bash scripts/check-no-em-dash.sh added-lines --base ca7181bf543421675d38b6f43fe5bfdb83b0ce63`: exit 0 (2026-11-08, worktree run over the authored plan bytes)
- `bash scripts/scan-public-hygiene.sh`: `=== PASS (public hygiene) ===`, `OUTCOME: pass` (2026-11-08)
- `bash scripts/check_maintenance_pins.sh`: `OUTCOME: pass` with one pre-existing advisory `PIN WARN` on the EXEC-PROMPTS prune-range pin, unrelated to this plan's files (2026-11-08)

### Task 1: Add the premise-verification item to review-plan Step 5

Context surface: the plan's Terms, this task.

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] Step 5 gains item 7 directly after the accounting-surface re-derivation (item 6): a premise-verification pass re-deriving each folded finding's load-bearing premises (named signatures and inputs, cited call-site shapes, cross-family claims) from the on-disk source in the same bounded pass; an unverifiable premise gets one more targeted read or is reworded to the verified subset before it enters the artifact [class: IMPLEMENTATION_REQUIRED]
- [x] The new item binds every fold batch that runs Step 5, the reconciliation fold batch included (that batch already runs the sibling accounting re-derivation under review-reconciliation's Fold-propagation probe) [class: IMPLEMENTATION_REQUIRED]
- [x] The new item's witness citation is one line naming the witnessed failure class (the 2026-11-07 r3-to-r4 fold-defect blocking inflation), with no failure narrative in the skill text [class: IMPLEMENTATION_REQUIRED]
- [x] Item 6's witness-citation tail is tightened in the same edit so the file's net growth from this task is bounded by the added item minus the bytes removed there, with item 6's citation still naming its witnessed r2/r4 accounting-drift incident [class: IMPLEMENTATION_REQUIRED]
- [x] The following items renumber (old 7 through 10 become 8 through 11) with their text unchanged, and a repo-wide grep for the moved item numbers finds no stale cross-reference outside the pruned prompt-log entry prose [class: IMPLEMENTATION_REQUIRED]
- [x] No Step 5 item's rule text changes besides item 7's addition, the renumbered item numbers, and item 6's tightened witness-citation tail; lesson 423 stays unedited [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check-no-em-dash.sh added-lines --base ca7181bf543421675d38b6f43fe5bfdb83b0ce63` passes, `bash scripts/scan-public-hygiene.sh` passes, and `bash scripts/check_maintenance_pins.sh` passes [class: REPOSITORY_TEST]
- [x] Commit: `review-plan: add premise-verification fold-discipline item to Step 5` [class: IMPLEMENTATION_REQUIRED]
