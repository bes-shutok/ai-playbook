# Plan: authoring staging preflight and certification-order gates

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-authoring-certification-staging-series-gate.md`
- `docs/history/backlog/2026-10-05-review-staging-authoring-validator-feedback.md`

Driving force: efficiency (primary) + token-usage (secondary)

Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-authoring-staging-preflight-gates-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 2.5h total, largest task 1.5h

## Terms

- preflight mode: the staging validator's report-only `--preflight` run that reports every stage's findings in one pass, naming a missing stage input's required inventory (for example the version-1 sidecar's required fields while the sidecar file is absent) instead of stopping at the first absent input.
- staging pair: one review round's staging Markdown file plus its `.stats.json` sidecar.
- staging series: the ordered set of one plan's staging pairs under the reviews home.
- full-gate mode: `python3 scripts/plan_readiness.py <plan-path>` invoked with no mode flag; the authoritative structural plus review-record readiness verdict.
- round-close step: the Plan Quality Gate step that records the certification seal entry before the review loop exits.
- record-side repair: fixing a defect inside a staged pair (Markdown or sidecar bytes) without editing plan bytes, so the certified digest binding is untouched.
- cascade discovery cost: the sequential-refusal cost where each stage's fix unblocks the next stage's findings, so one defect class surfaces per validator run.
- scaffold arm: the origin row's alternative of authoring staging records from a scaffold/template rather than deriving the required-shape inventory from the validator's schema constants.
- certification seal entry: the committed `docs/history/review-certs/<artifact-slug>.md` line the round-close step records for the round it certified.

## Why

Three witnessed authoring cycles folded their review findings, claimed certification, and only then failed the authoritative readiness gate at closeout on staging-record defects (an illegal enum value, a 40-hex digest, a missing last-fix-commit spelling, an unstaged round pair), so each defect cost a closeout repair and, in one cycle, a re-dispatched verification round. Separately, a careful first-draft staging pair needed four sequential hard-gate re-runs because the validator surfaces one stage's findings per run. Both defects are timing defects, not missing machinery: the gates exist, the loop runs them too late.

## Outcome

Validation moves left in the authoring loop: staging defects surface in the round that produced them, and the authoritative gate passes before certification is claimed.

- A first-draft staging pair converges in one preflight pass that names every missing or malformed surface together, instead of one run per stage.
- Every returned round's staging pair is hard-validated before the round is folded, so a sidecar defect is repaired in its own round at record-side cost.
- The review loop cannot exit on a digest whose staging series fails the full gate, so the closeout and landing boundaries stop rediscovering staging defects after review rounds already spent.

Required: Gate delta: none in the five counted classes (no refusal class, hard gate, fence, protocol layer, or schema state field is added or removed; the preflight mode is report-only and adds no gate; the staging validator's grading semantics and the readiness gate's checked-condition set are unchanged). Declared blocking review-layer duties, witnessed in their own text: (1) the post-round staging-pair hard-validation duty and (2) the round-close full-gate precondition (both in the plans skill's Plan Quality Gate, the second mirrored into the authoring payload's ready-state sentence in `agents/skills/maintenance/prompt-templates.md`); their paying witnesses are the origin rows' evidence and witness sections (three cycles repairing staging defects at closeout; four sequential hard-gate re-runs on one first draft).

## Assumptions

- assume origin row `2026-10-05-review-staging-authoring-validator-feedback.md` is fix-class, judged from its body (the row carries no `Class:` line); basis: the body's Desired outcome asks for an authoring aid "while keeping the existing validator as the final gate", which this plan honors by adding a report-only mode and no refusal path; the row's own Witness paragraph names the residual as "the sequential-refusal discovery cost".
- assume the preflight-inventory arm over the scaffold arm for that row; basis: the row's Witness paragraph carries "it supports the scaffold or preflight arm (surface the full required-shape inventory before the round is treated as staged)"; the scaffold and recipe side already landed (`2026-10-05-review-staging-finding-template`, main `c9105351`); and the 2026-10-06 authoring probe witnessed the cascade live: a clean recipe-shaped staging Markdown with no sidecar file reports exactly one error ("missing required stats sidecar") and exits 0 in the non-hard posture, teaching the author nothing about the sidecar inventory; the validator selftest counted 581 OK checks at this base (invocation recorded in the Validation Commands, 2026-10-06).
- assume origin row `2026-10-05-authoring-certification-staging-series-gate.md` takes its candidate arms (a) and (b) together, per the row's own "(c) both" candidate; basis: the row's Suspected root area text; its constraint that the pre-round structural gate stays unchanged and the authoritative-round digest binding is respected is carried into Standing constraints.
- assume unattended authoring under the operator's standing directive: the Phase 1 grilling interview is not available; basis: the active directive record (`docs/maintenance/operator-directives.md` D-4, witnessed by its armed automation, and the loop directive's tracked form in `docs/maintenance/document-registry.md`: investigating untaken backlog and authoring the most urgent items in uninterrupted cycles) orders authoring one by one without stops; both origin rows delegate the arm adjudication to authoring time in their own text, so no material decision point is left open by this session.
- assume the grouped origin count is two rows in one plan; basis: both rows share one root shape (validation arrives after the certification claim and after the round closes), precedent grouped cycles exist (2026-10-05 cycles landed grouped plans), and the task files are disjoint so the shared-file seam rule holds.
Decision points requiring a grill: none remain.

## Standing constraints

- The authoritative readiness gate stays `scripts/plan_readiness.py`; the staging validator's `--hard` posture stays the grading gate; neither script's existing reporting or semantics change (Task 1 adds a mode; Task 2 sequences invocations of existing modes).
- Every new validator invocation literal in a task resolves repo-local first, then the deployed home copy (`~/.ai-playbook/scripts/`), matching the repo's existing convention.
- Added lines in every edited file are em-dash free (repo gate `scripts/check-no-em-dash.sh`).
- Edits to `agents/skills/plans/SKILL.md` must keep the runtime-neutral shared-body gate green; edits to `agents/skills/maintenance/prompt-templates.md` must keep the pins suite green, reconciling any touched pinned span beside its provenance in the same edit.
- The origin row's constraint is binding: the pre-round structural gate and the authoritative-round digest binding (the latest round's sidecar carries the final bytes' canonical digest) stay exactly as they are.

## Gist & Examples

TLDR: validation moves left in the authoring loop, staging records report their whole defect inventory at staging time and the full gate runs before certification is claimed, so closeout stops rediscovering staging defects after review rounds already spent (efficiency).

**Before (today):** an authoring cycle folds its last review round, records ready=yes, and proceeds to landing. At landing time the readiness gate runs over the assembled staging series for the first time and refuses: the latest sidecar carries a 40-hex SHA-1 digest where the schema demands 64-hex SHA-256. The cycle repairs the sidecar, re-runs the gate, hits the next defect (a last-fix-commit line the validator does not recognize), repairs again, and in the witnessed variant re-dispatches a verification round over plan bytes that were never the problem. On the drafting side, an author writes a staging pair from the recipe, runs the validator, and gets one finding (the missing sidecar file); after creating the sidecar the next run reports the schema defects; after those are fixed the next run reports finding conservation; four runs to reach a clean draft.

**After (this plan):** the same author drafts the pair and runs `--preflight` once: the run reports the missing sidecar file and, in the same output, names the version-1 sidecar's required fields so the first sidecar draft starts from the inventory instead of from memory. When a round returns, the orchestrator hard-validates the pair before folding it, so a bad digest or an illegal enum is that round's own repair, executed while the producing worker's context is one message old. At the last round's close, the full gate runs before the certification seal entry is recorded; a staging defect found there is a record-side repair and a gate re-run in the same step, never a landing-time re-dispatch.

## Evaluation Criteria

**Quality dimensions:**
- correctness: on a fixture with defects in several stages at once, one `--preflight` run reports every stage's findings together, asserted by the selftest family; the `--hard` posture's reporting and exit codes on existing fixtures are unchanged (regression pin inside the selftest).
- maintainability: the missing-input inventory is derived from the validator's own schema constants in the same file, never from a second hand-written list, so a schema change cannot drift the inventory.
- efficiency: a first-draft staging pair converges in one preflight pass instead of one run per stage (the witnessed four sequential re-runs collapse to one).

**Done when:**
- `python3 scripts/validate_review_staging.py --selftest` passes including the new preflight family.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- `python3 scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral` passes.
- `python3 scripts/test_plan_readiness.py`, `python3 scripts/test_execute_plan_address_fanout.py`, and `python3 scripts/test_review_record_selection.py` each pass (the external suites importing validator internals).
- `python3 scripts/test_execute_plan_runtime.py` (full suite) passes.
- `bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"` reports no added-line hits on the touched files.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-06-authoring-staging-preflight-gates.md --pre-round` exits 0 with `OUTCOME: pass`.
- Every positive per-obligation grep in Validation Commands exits 0, and the forbidden sweep exits clean (grep rc 1).

**Ship when:**
- Consumer projects that run the authoring loop pick the changes up through the normal skills sync; no separate deployment step exists (the deployed validator copy is a symlink to this repository's file).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (the `--preflight` mode plus its selftest family live in this one file; the file embeds its own fixture checks under `--selftest`)
- `agents/skills/review-staging/SKILL.md` (the drafting-time preflight sentence, step 6 of the fill order)
- `agents/skills/plans/SKILL.md` (the Plan Quality Gate: post-round staging-pair validation paragraph and the rule 6 round-close precondition)
- `agents/skills/maintenance/prompt-templates.md` (the authoring payload's ready-state sentence in the Schedule-at payload paragraph)
- `agents/skills/review-plan/SKILL.md` (rule 8's sanctioned-post-round-record-edit enumeration span only; the rest of the file is frozen)

**Tests:**
- the validator selftest family inside `scripts/validate_review_staging.py` (the file's own `--selftest` fixture suite is the behavior-test layer; no separate test file exists for this validator); four external suites import validator internals and are regression-pinned by this plan's Done when gates: `scripts/test_plan_readiness.py`, `scripts/test_execute_plan_runtime.py`, `scripts/test_execute_plan_address_fanout.py`, `scripts/test_review_record_selection.py` (findings on those files are in scope only when Task 1's changes break their imports or pinned behavior; the plan does not edit them)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. One named extension: `scripts/check_maintenance_pins.sh` gains or reconciles a pin row only when a touched span in `agents/skills/maintenance/prompt-templates.md` is already pinned or must be pinned to keep an exactly-once count true.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: the full gate is consumed as-is, its checked conditions and modes are frozen by the origin row's constraint.
- `agents/skills/execute-plan/` including its `SKILL.md` and blueprint sentences; reason: the execution side already runs its own gate set, and both origin rows witness the authoring loop only.
- the validator's schema of record, enum vocabularies, and date-fence constants; reason: frozen by the same origin constraint, the plan adds no schema field.

## Validation Commands

Preamble (authoring-time record, 2026-10-06, worktree wt-aspf at base 187e9692): the structural pre-round gate passed (`OUTCOME: pass`, no failure class) over the final draft bytes; the em-dash touched scan and the public hygiene scan passed; the Validation Commands block was executed against the current tree in a set -e pass up to its first failure and the remaining gates were then executed individually: the FIRST failing gate is the Task 1 `def cmd_preflight` presence grep (RED today, expected), with every earlier gate green (selftest, pins, shared-body, em-dash vacuous over the empty branch delta, pre-round), the Task 2 duty greps red by the same absence (expected), and the forbidden sweep executed separately fired today (the old boundary span is present at exactly one hit in the payload home); the rule 22 mechanical audit ran: `bash -n` over the extracted block exits 0, and every gate literal ('staging-pair hard-validation duty', 'full-gate precondition', 'certification-ordering duty', 'def cmd_preflight', '_selftest_preflight_inventory') occurs in this plan's own prescribed task text, so each gate is satisfiable by a faithful implementation; the cascade defect claim was probed live against the real validator (clean recipe-shaped Markdown, no sidecar: exactly one error, non-hard exit 0), and the prescription for the payload boundary replacement quotes the byte-exact current span (verified unique in the payload home).

```bash
set -e
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"

# Both tasks: the repo's cheap mechanical gates over the final bytes
python3 scripts/validate_review_staging.py --selftest
bash scripts/check_maintenance_pins.sh
python3 scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
python3 scripts/plan_readiness.py docs/history/plans/2026-10-06-authoring-staging-preflight-gates.md --pre-round

# Task 1 obligations, each on its own anchor (fail-closed, dedicated searches)
grep -qF 'def cmd_preflight' scripts/validate_review_staging.py \
  || { echo 'missing preflight entry point'; exit 1; }
grep -qF '_selftest_preflight_inventory' scripts/validate_review_staging.py \
  || { echo 'missing preflight selftest family'; exit 1; }

# Task 2 obligations, one dedicated search per home and duty (fail-closed)
grep -qF 'staging-pair hard-validation duty' agents/skills/plans/SKILL.md \
  || { echo 'missing post-round staging validation duty in plans skill'; exit 1; }
grep -qF 'full-gate precondition' agents/skills/plans/SKILL.md \
  || { echo 'missing round-close full-gate precondition in plans skill'; exit 1; }
grep -qF 'certification-ordering duty' agents/skills/maintenance/prompt-templates.md \
  || { echo 'missing certification-ordering sentence in authoring payload'; exit 1; }
grep -qF -- '--preflight' agents/skills/review-staging/SKILL.md \
  || { echo 'missing preflight mode mention in review-staging skill'; exit 1; }

# The payload continuation tail survives Task 2 verbatim (positive contiguous pin)
grep -qF 'and the workflow is processed with the done skill (committing only files this task created or edited' agents/skills/maintenance/prompt-templates.md \
  || { echo 'payload continuation tail lost'; exit 1; }

# The replaced payload boundary is gone after Task 2 (forbidden form; the old
# boundary text quoted in this plan file is the prescription record, the sweep
# is scoped to the payload home only)
rc=0
grep -qF 'in the plan), and the workflow is processed' agents/skills/maintenance/prompt-templates.md || rc=$?
if [ "$rc" -ne 1 ]; then echo 'old payload boundary present or sweep tool error'; exit 1; fi

# The review-plan rule 8 amendment landed beside the plans skill's rule 16 amendment
grep -qF "beside the plans skill's round-close step record-side repair" agents/skills/review-plan/SKILL.md \
  || { echo 'review-plan rule 8 enumeration not amended'; exit 1; }

# The two spans with exactly-once obligations carry count gates; the other two duty spans carry presence gates (their anchors verified unique today)
test "$(grep -oF 'staging-pair hard-validation duty' agents/skills/plans/SKILL.md | wc -l)" -eq 1
test "$(grep -oF 'certification-ordering duty' agents/skills/maintenance/prompt-templates.md | wc -l)" -eq 1
```

### Task 1: preflight full-inventory mode in the staging validator

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/validate_review_staging.py` (the mode and its selftest family live in this file; the file already carries its fixture suite under `--selftest`)

Evidence:
- `python3 scripts/validate_review_staging.py --selftest`; covers the preflight family and the unchanged-hard regression pin
- `bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"`; covers the em-dash constraint on this task's added lines

- `Selftest#preflight_missing_sidecar_reports_field_inventory`; given a clean recipe-shaped staging Markdown with no sidecar file, expects one `--preflight` run to exit 0 and to report, in the same output, the missing sidecar file AND the version-1 sidecar's required top-level fields by name (the inventory derived from the validator's own schema constants); given the same input today, the non-hard run reports only the one missing-sidecar error (RED today, recorded in the Validation preamble)
- `Selftest#preflight_reports_all_stages_in_one_run`; given a staging Markdown missing two required sections and a sidecar carrying three schema defects (a bad enum value, a 40-hex digest, a missing extended field), expects one `--preflight` run to report, in one output, at least both section-absence findings AND all three named sidecar findings (a faithful fixture run reports additional cascaded Markdown findings alongside them, so the assertion is a superset, never an exact count); the item's discriminating power for the preflight delta rests on the missing-sidecar sibling item, because for inputs that exist today's engine already reports every stage together, so this item doubles as the continuation regression pin
- `Selftest#preflight_leaves_hard_posture_unchanged`; given the same two fixtures, expects the `--hard` runs' error sets and exit codes to equal the pre-change behavior exactly (regression pin, green at RED, characterization over the existing suite)
- `Selftest#preflight_report_only_exit_contract`; given any fixture with findings, expects `--preflight` to exit 0 (report-only, no grading posture), and given an unreadable input path, expects a non-zero exit with the outcome contract's tool_error class (beside usage violations), matching the existing non-hard run's behavior for the same input
- Register the selftest family under the anchor `_selftest_preflight_inventory` beside the existing `_selftest_embedded_recipe_example` family: fixtures only, asserting the four contract items above
- Run → expect RED: `python3 scripts/validate_review_staging.py --selftest` (the new family fails; the existing checks stay green)
- Implement the `--preflight` mode: one entry point (the `def cmd_preflight` anchor), full defensive continuation across the validator's stages (a stage whose input is absent reports that stage's required-input inventory, derived from the file's own schema constants, and the remaining stages still execute against the inputs that do exist), report-only exit semantics per the contract item above, and the `--json` output carrying the same inventory so tooling can read it
- Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` (whole suite green, new family included)
- Commit: `validators: staging validator preflight reports every stage's inventory in one run`

### Task 2: certification ordering and staging-time validation duties in the three doc homes

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md` (rule 8's parallel sanctioned-record-edit enumeration, amended in the same edit as rule 16)

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the pins constraint on the payload home edit
- `python3 scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral`; covers the runtime-neutral constraint on the plans skill edit
- the Task 2 dedicated greps in the Validation Commands block; covers each duty span's presence and exactly-once count per home

- In `agents/skills/plans/SKILL.md`, insert one new paragraph immediately after the per-round name binding check paragraph (after the witness parenthetical ending "2026-09-18 and 2026-09-20.)" and before the `**Review severity:**` line), the staging-pair hard-validation duty (the inserted paragraph carries the literal duty name staging-pair hard-validation duty; the orchestrator-side twin of review-plan Step 4's worker-side staging gate): as soon as a round's artifact pair exists, after the name probe passes, the orchestrator runs `python3 scripts/validate_review_staging.py --hard --source-plan <plan-path> <round-staging-path>` and treats a staging-record defect as that round's own repair, routed back to the round's producer for re-staging (a record-side repair), never deferred to closeout; the duty names the deployed-home fallback for the validator invocation per the standing convention
- In `agents/skills/plans/SKILL.md` rule 6, append after the sentence ending "and the round-close commit." the full-gate precondition (the inserted sentence carries the literal name full-gate precondition): the round-close step runs the readiness validator's full-gate mode over the final plan bytes and requires exit 0 with the final `OUTCOME: pass` line before recording the certification seal entry; a staging-record defect found there is repaired record-side and the gate re-run inside the same round-close step (that record-side repair is a sanctioned post-round record edit class beside corrections rows and triage marks, scoped to this step); the same edit amends rule 16's enumeration span in this file to read "beside the triage marks and the round-close step's record-side repair rule 6 defines", and amends review-plan/SKILL.md rule 8's parallel span "with `extensions.corrections` rows as the only other sanctioned post-round record edit outside that shape" to read "with `extensions.corrections` rows as the only other sanctioned post-round record edit outside that shape, beside the plans skill's round-close step record-side repair (the plans skill's Plan Quality Gate rule 6)", so every exhaustive enumeration of sanctioned post-round record edits names the third class in the same landing; exit 2 (`OUTCOME: indeterminate`), exit 3 (`OUTCOME: tool_error`), and a run with no final `OUTCOME:` line stop the round-close step for re-derivation from disk, never read as pass or failure, per the outcome contract; a failure keeps the loop open (the round is not exited), and the seal's round-start digest binding is unchanged
- In `agents/skills/maintenance/prompt-templates.md`, replace the payload boundary span "record the residual findings in the plan), and the workflow is processed" with the certification-ordering form "record the residual findings in the plan), the ready state carrying the certification-ordering duty (before it is treated as reached, run the readiness validator's full gate over the final plan bytes and require its final `OUTCOME: pass` line, repairing any staging-record defect record-side and re-running the gate before proceeding, so the authoritative gate never first runs at landing time), and the workflow is processed": the duty rides the original conditional as an absolute clause, so the payload sentence stays one grammatical conditional; the continuation text after "is processed" is preserved verbatim and its survival is pinned by the Validation Commands
- In `agents/skills/review-staging/SKILL.md` Integration Points table, add one consumer row naming the plans skill's Plan Quality Gate as an orchestrator-side consumer that re-runs the `--hard` posture per returned round before folding; the row's Staging path pattern cell reuses the review-plan row's plan-review pattern (`{reviews_dir}/YYYY-MM-DD-plan-review-<slug>-r<N>.md`) and the Notes cell names the orchestrator-side twin relationship
- In `agents/skills/review-staging/SKILL.md` fill-order step 6, re-target the step's operative drafting command to the preflight full-inventory mode and reword the step body in the same edit: the command becomes `python3 ~/.ai-playbook/scripts/validate_review_staging.py --preflight <staging-path>` and the parenthetical describes the report-only mode (every stage's findings reported together in one pass, the missing sidecar's required-field inventory included), so the legacy plain non-hard run and the `--preflight` mode are distinguished and the step's own instruction owns the one-converging-pass outcome (the command deliberately preserves that line's existing deployed-home convention, which the standing constraint defers to); the step's tail "re-run until it passes" becomes "re-run until the report is clean" because the report-only mode has no pass/fail exit posture, and the round's `--hard` gate still grades substance and is never replaced
- Run the pins suite and, if a touched span in `agents/skills/maintenance/prompt-templates.md` is pinned or its exactly-once count moved, reconcile the pin row beside its provenance in the same edit
- Run → expect GREEN: the Task 2 dedicated greps and count gates in the Validation Commands block, plus the whole block end to end
- Commit: `skills: authoring loop validates staging pairs per round and gates certification on the full gate`

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-aspf on branch 2026-10-06-authoring-staging-preflight (base 7c3abb2a). Task 1 commit 039a309d (the report-only preflight mode in scripts/validate_review_staging.py, 401 added lines and zero deletions so the hard posture is byte-identical by construction, inventory derived from the file's own schema constants, selftest family _selftest_preflight_inventory green-first at 611 OK checks vs 581 at base). Task 2 commit ac4beafd (the staging-pair hard-validation duty and rule 6 full-gate precondition in the plans skill, rule 16 and review-plan rule 8 enumeration amendments, the certification-ordering payload boundary in prompt-templates.md, the review-staging Integration Points row and the preflight-retargeted fill-order step 6; no pin reconciliation needed). Phase 3 panel zero blocking; three Lows and one info recorded as deferred residuals below.

Shared-file seam event (the overlap row's predicted collision): this execution is the first executor of the payload certification span, so the landed bytes carry the certification-ordering form and the sibling plan docs/history/plans/2026-10-07-done-readiness-closeout-boundary.md Task 2's quoted anchor is now stale; per arm (a) of docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md its executor corrects through the normal anchor-failure path at its own execution.

Deferred residuals (staged Lows, riding the landing): the --hard --preflight combination silently degrades to report-only (argparse mutual-exclusion guard is the hardening); the continuation half of the contract lacks its own discriminating selftest fixture (absent sidecar plus defective Markdown in one family arm); the digest syntax check stays presence-only without a declared source_kind (informational, pre-existing posture).

Backlog capture (off-plan): none; the shared-payload-span row was filed before this execution and carries the seam event.
