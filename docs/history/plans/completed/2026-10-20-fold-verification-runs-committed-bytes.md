# Plan: A fold's mechanical verification runs the committed bytes

Backlog origin: docs/history/backlog/2026-10-19-fold-verification-runs-committed-bytes.md
Driving force: reliability (a certified fold's verification must be evidence about the committed bytes, not about a hand-typed equivalent; this plan adds no machinery, so simplicity is not its force)
Authoring claim: docs/tmp/authoring-claims/2026-10-19-fold-verification-runs-committed-bytes.md (session zcode-maintenance-auth-20261020-0300)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- Fix-and-fold batch step: the review-loop one-iteration table's steps 2 and 3 and their surrounding fold duties, the operative home where accepted findings are folded into the plan between review rounds.
- Fold-time staged-record duty: the landed precondition paragraph beside that table requiring the round's staged record to exist before findings fold.
- Mechanical artifact: a fold-authored command block, loop, witness sentence, or gate sentence whose text prescribes or reports a machine-checkable behavior.
- Fold-output verification duty: this plan's new duty; a fold that introduces or rewords a mechanical artifact verifies that artifact by extracting and running the exact bytes it will commit.
- Verification surface: the extracted artifact bytes, identified by their own sha256 short digest, recorded in the outcome line as `staged@<digest>` or `committed@<digest>` (the sha256 digest truncated to its first 12 hex characters); the commit-time re-assertion re-extracts the artifact from the committed bytes and compares digests (a mismatch re-runs the duty); a batch edit that touches a verified artifact after its run also invalidates the earlier run.
- Substitution assertion: a post-edit check that every intended replacement actually changed its target file; an unchanged file fails the fold.
- Vacuity signature: a locator-class witness whose dry run classifies every checked item as the benign arm; the fold then runs one positive control (re-run the locator on one input known to require the non-benign arm) and refuses when the locator still classifies that input benign, passing only when the locator flags it (lesson 126's investigate-the-tool discipline, made falsifiable).
- Fold handling: the review-plan Step 5 fold-discipline numbered rules, the second skill's voice over the same fold step.
- Verification outcome line: the fold commit message line recording what the duty ran and its result, additive to the commit message body.

## Why

Twice in one session a certified fold shipped an unverified artifact: the smme r4 fold's quote-strip fix silently no-op'd (a substitution-escaping mismatch) and its dry run executed a hand-typed loop instead of the plan's committed bytes, so the recorded "zero misses" was vacuous; the r5 panel caught both. The landed fold-time staged-record duty owns record staging before folds; nothing owns verifying the fold's own output, and unverified mechanical artifacts seed the next round's findings. This plan scopes the duty to mechanical artifacts; prose-only folds and invented-citation defects stay governed by the existing review surfaces.

## Gist & Examples

TLDR: folds that introduce or reword mechanical artifacts verify those artifacts by running the exact staged bytes, re-asserted at the fold commit, and by asserting their substitutions took effect, for reliability.

Before (today): a fold's prose prescribes the right duty, but the fold's own new command block, loop, or witness is never executed; a no-op substitution passes silently, and a locator witness that classifies everything benign reads as a pass without investigation.

After (this plan): the fix-and-fold batch step's fold arm runs each new or reworded mechanical artifact extracted from the exact bytes it will commit (the staged bytes, re-asserted at commit time), asserts every substitution changed its file, positive-controls a vacuous locator witness and refuses when the control fails, and records the outcome in the fold commit message; review-plan's fold handling carries the same bar by reference with a provider-side Integration Points row holding the reference.

Edge cases: a fold that only reflows prose (no mechanical artifact) owes no run; a fold whose artifact cannot run without the executor's environment records the skipped run and the reason in the outcome line rather than silently passing, except a witness-sentence artifact, which always runs its locator and is never skipped; a batch edit touching a verified artifact after its run invalidates that run and re-runs the duty before the fold commit; all-benign dry runs pass only when the positive control flags the known-defective input.

## Outcome

Every fold's new or reworded mechanical artifact is verified by evidence about the bytes that land, so a no-op fix or a vacuous witness fails at fold time instead of seeding the next review round. Text-only change: no new gate, validator, lock, ledger, or state-schema field. The duty's refusal wording implements lesson 126's investigate-the-tool discipline (a lessons-corpus record, not skill machinery) and the admission fields ride this declaration: expected catch is the witnessed smme r4-class defects (a vacuous locator witness, a silently no-op substitution) on any fold introducing or rewording a mechanical artifact, false-positive cost is one positive-control re-run, review date 2027-04-20. Machinery rejection witness: the PLAN-PROMPTS entry for this item rejected the validator arm with the missing-incident absence named (the Machinery admission protocol section of the repository guidelines); the origin row itself reserves the routing decision and records no rejection, and this Outcome is the routing the investigate pass produced.

Scope disposition of the origin row's second mandate (its title's "folds of certification findings get a machinery check before the fold commits"): out of scope here. A per-fold machinery check is a candidate gate and carries no admission case (no incident names a fold that needed machinery triage; the witnessed defects are verification gaps, not classification gaps). Dispositioning this mandate in the origin row's covered flip is plan-related extension work in Task 2.

Gate delta: add one fold-output verification duty paragraph in the review-loop fix-and-fold batch step, one numbered fold rule in review-plan's fold discipline, and one provider-side Integration Points row in review-loop; remove nothing. Current guard-liveness ratio: not applicable (no gate added or removed).

## Assumptions

- The duty binds at fold authoring time (steps 2 and 3 of the review-loop one-iteration table and the review-plan Step 5 fold pass), not at certification; a certification round with no folds runs nothing new. Basis: the origin row's Skill/step fields.
- Both skills carry one bar with the review-loop paragraph as the bar's home and review-plan's rule referencing it; the repository guidelines' Skill Design Guidelines bidirectional rule (each direction documents the integration) is the pattern, and Task 1 lands the provider-side Integration Points row beside Task 2's consumer rule. Basis: the guidelines' integration-documentation rule; no existing review-plan-to-review-loop reference exists (verified by grep during the r1 panel).
- Verification runs against the staged bytes and is re-asserted at the fold commit: the fold composes its commit from the same staged set, and a batch edit that touched a verified artifact after its run re-runs the duty; the outcome line records `staged@<sha>` or `committed@<sha>` so the surface of record is explicit. Basis: the origin row's Expected wording "committed (or staged) bytes" plus the r1 staged-stale finding.
- Reconciling voices means the same bar, not duplicated procedure text: review-plan's rule names the bar and delegates the how to the review-loop paragraph. Basis: the origin row's Orientation.

Decision points requiring a grill: none (unattended authoring; the origin row's investigate pass already fixed the routing this plan implements).

## Standing constraints

- Text-only change: no new gate, validator, lock, ledger, or state-schema field; the refusal wording implements lesson 126's investigate-the-tool discipline and prices itself through the admission fields in the Outcome.
- The staged-record precondition's text stays unchanged; this plan adds beside it, never rewords it.
- The fold commit message gains only the additive outcome line; no other commit-message grammar is introduced or required.
- Neither skill restates the other's procedure; one bar, one home, one reference in each direction.
- The vacuity arm never refuses without the positive control, and never passes an all-benign dry run the control failed; witness-sentence artifacts always run their locator (the skip arm never applies to them).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: a fold introducing or rewording a mechanical artifact triggers the run-the-bytes duty, the substitution assertion, the investigate-before-refusing vacuity arm, and the outcome line; a prose-only fold triggers none of them.
- Safety: a skipped run (environment-unavailable) is recorded with its reason in the outcome line, never silent; a stale staged verification is re-asserted before the fold commit; the vacuity arm never refuses without a recorded investigation.
- Maintainability: one bar in one home; review-plan references it; the provider-side Integration Points row names the consumer; no duplicated procedure text to drift.

**Done when:** the review-loop paragraph, the review-plan rule, and the provider-side Integration Points row all carry the bar; the vacuity positive-control arm and the substitution assertion are named in operative text; a validation grep pins each contract line; the plan carries no execution-branching wording.

**Ship when:** none; repository-only behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:** none (text-only change).

**Tests:** none (no executable surface changes; validation is by pinned greps with expected counts).

**Docs:**
- `docs/history/backlog/2026-10-19-fold-verification-runs-committed-bytes.md` - the origin row; edited only by Task 2's covered-flip disposition amendment (plan-related extension).
- `agents/skills/review-loop/SKILL.md` - the fold-output verification duty paragraph beside the fold-time staged-record duty, and one provider-side Integration Points row.
- `agents/skills/review-plan/SKILL.md` - one numbered fold-discipline rule referencing the bar.

**Plan-related extension:** amend the origin backlog row's covered-flip disposition to record the second mandate's out-of-scope disposition and the complete fix-class rationale; record the reason in the review report.

**Out of scope; reject unless plan-related:**
- The review-staging validator and its schema (no gate changes).
- The one-iteration table's existing steps 1, 2, and 4 behavior.
- A per-fold machinery check (the origin row's second mandate; no admission case).
- Any machinery admission surface: no gate, validator, lock, or ledger is added.

## Validation Commands

```bash
rg -c 'exact bytes it will commit' agents/skills/review-loop/SKILL.md   # expect: 1
rg -c 'benign-arm witness' agents/skills/review-loop/SKILL.md           # expect: 1
rg -c 'leaves the file unchanged' agents/skills/review-loop/SKILL.md    # expect: 1
rg -c 'Step 5 fold-discipline rule' agents/skills/review-loop/SKILL.md  # expect: 1
rg -n 'fold-output verification duty' agents/skills/review-loop/SKILL.md agents/skills/review-plan/SKILL.md  # expect: at least one match per file (inspect recorded output)
```

A command's expected count on its comment line is the pass bar: the checkbox owning the command fails unless the command exits 0 with its expected count (command 5's bar is the recorded output showing at least one match in each file).

### Task 1: Land the fold-output verification duty and its provider-side integration row in review-loop

Context surface: this task, `## Terms`, `## Standing constraints`, and the landed fold-time staged-record duty paragraph this task extends beside.

Files:
- `agents/skills/review-loop/SKILL.md` *(edited)*

Primary class anchors:
- `Fold-time staged-record duty` in `agents/skills/review-loop/SKILL.md`

- [x] [class: IMPLEMENTATION_REQUIRED] Add one paragraph directly after the fold-time staged-record duty, opening with the sentence "The fold-output verification duty binds every fold that introduces or rewords a mechanical artifact (command block, loop, witness sentence, gate sentence): verify that artifact by extracting it from the exact bytes it will commit and running those bytes, never a hand-typed equivalent." The paragraph is the bar's home.
- [x] [class: IMPLEMENTATION_REQUIRED] In the same paragraph: carry the substitution clause "a substitution that leaves the file unchanged fails the fold" for every intended replacement.
- [x] [class: IMPLEMENTATION_REQUIRED] In the same paragraph: carry the vacuity clause in its single control-decides form: a locator-class witness whose dry run classifies every checked item as the benign arm runs one positive control (the locator re-run on one input known to require the non-benign arm), the fold refuses when the locator still classifies that input benign, and the benign-arm witness is never trusted without its positive control.
- [x] [class: IMPLEMENTATION_REQUIRED] In the same paragraph: the verification runs against the staged bytes and is re-asserted at the fold commit; a batch edit that touched a verified artifact after its run invalidates that run and re-runs the duty.
- [x] [class: IMPLEMENTATION_REQUIRED] In the same paragraph: record the verification outcome (surface as staged@ or committed@ with the 12-hex digest, what ran, pass or skip-with-reason) in the fold commit message as the additive verification outcome line; a fold with no mechanical artifact owes no run and no outcome line, and a witness-sentence artifact is never skipped (it always runs its locator).
- [x] [class: IMPLEMENTATION_REQUIRED] Add one row to the review-loop Integration Points section naming review-plan's consumer fold rule as the consumer of this bar and how it integrates (the rule references this paragraph as the bar's home); the row names the consumer by the literal "Step 5 fold-discipline rule".
- [x] [class: IMPLEMENTATION_REQUIRED] Keep the staged-record precondition paragraph's existing text byte-unchanged; the new paragraph extends beside it.
- [x] [class: IMPLEMENTATION_REQUIRED] Run Validation Commands 1, 2, 3, and 4 over the edited file from the run's checkout and record the outputs with their expected counts in the run record; a count other than its expectation or a non-zero exit fails this checkbox.

### Task 2: Add the consumer rule in review-plan and disposition the origin row

Context surface: this task, `## Terms`, `## Standing constraints`, and the review-plan Step 5 fold-discipline numbered rules.

Files:
- `agents/skills/review-plan/SKILL.md` *(edited)*
- `docs/history/backlog/2026-10-19-fold-verification-runs-committed-bytes.md` *(edited, plan-related extension: the covered flip disposition)*

Primary class anchors:
- `Accounting-surface re-derivation` in `agents/skills/review-plan/SKILL.md`

- [x] [class: IMPLEMENTATION_REQUIRED] Append one numbered fold-discipline rule at the end of the Step 5 fold-discipline list: a fold's mechanical artifacts are verified per the review-loop fold-output verification duty (the bar's home), so neither skill voices a different fold verification bar; the rule names the bar and references, never restates, the how.
- [x] [class: IMPLEMENTATION_REQUIRED] Run Validation Command 5 over both edited files from the run's checkout and record the output in the run record; the recorded output must show at least one match in each file (inspect the recorded lines), and a non-zero exit fails this checkbox.
- [x] [class: IMPLEMENTATION_REQUIRED] Amend the origin row's covered-flip disposition (the flip rides this plan's completion closeout) to record the second mandate's out-of-scope disposition with the no-admission-case rationale from this plan's Outcome.
