# Plan: P51 plans/authoring surface hygiene (six origins)

Backlog origins (scope of record; full text read from `docs/history/backlog/`):

- `docs/history/backlog/2026-09-22-deferral-sweeps-must-cross-check-claimed-origins.md` (origin 1, HIGH)
- `docs/history/backlog/2026-09-22-maintenance-authoring-slice-whole-body-vs-payload-practice.md` (origin 2, HIGH)
- `docs/history/backlog/2026-09-22-blueprint-payload-telemetry-paths-keep-literal-prefix.md` (origin 3, LOW)
- `docs/history/backlog/2026-09-23-plans-shared-body-forbidden-term-precheck.md` (origin 4, HIGH)
- `docs/history/backlog/2026-09-23-completed-provenance-convention-consolidation.md` (origin 5)
- `docs/history/backlog/2026-09-23-registry-archived-date-semantics.md` (origin 6)

Coordination note: the ai-harness-friction-audit's Task 5 (rejected/-lifecycle validator changes) landed on main in commit 10aa0147, before this plan's authoring base (1d0e24c1); origin 6's registry edits build on that base, and the final validation re-runs the rejected-archive lifecycle test to prove the two change sets do not interact.

## Terms

- **Authoring slice**: the Step 5 sentence in `agents/skills/maintenance/SKILL.md` that describes what an authoring child's scheduled prompt contains.
- **Payload paragraph**: the authoring blueprint's span opening `Schedule at {schedule_time} the following task:` in `agents/skills/maintenance/prompt-templates.md`; the region observed dispatch practice actually transmits.
- **Blueprint body**: a full fenced body in prompt-templates.md (role line through FINAL STEP). Only the payload paragraph and the deviation ledger are open for edit in this plan; all other body paragraphs are frozen by byte-parity pins.
- **Pins suite**: `scripts/check_maintenance_pins.sh`; variables `$S` (maintenance SKILL.md), `$P` (prompt-templates.md), helpers `pin` and `expect_absent`.
- **Claimed item**: an open backlog item whose filename stem occurs in a top-level plan file (origin list or validation-gate literal); ownership beats triage verdict.
- **Disposition sweep**: a bulk move of open backlog items (defer, close, or reopen in one session).
- **Shared bodies**: the four files covered by the runtime-neutrality gate: `agents/skills/execute-plan/SKILL.md`, `agents/skills/execute-plan/subagent-prompts.md`, `agents/skills/execute-plan/agent-logs.md`, `agents/skills/plans/SKILL.md`.
- **Runtime-neutrality gate**: `scripts/test_execute_plan_runtime.py` `ExecutePlanRuntimeTest#test_shared_skill_bodies_remain_runtime_neutral`; forbids a fixed term tuple (case-insensitive) in the shared bodies, with `context.jsonl` replaced by a sanctioned placeholder before matching.

## Assumptions

- assume the deciding turn's assembly transmits the payload paragraph only, not the whole fenced body; basis: the prompt-templates.md deviation-ledger 2026-09-23 claim-tail entry and the two witnessed runs named in origin 2 (automation-197f75a7 and automation-ae88c54e received only the payload paragraph).
- assume the re-arm duty must still reach payload-born sessions; basis: the dispatch ladder's parent-XOR-child constraint (agents/skills/maintenance/zcode.md "Dispatch ladder") makes the armed child the re-arm carrier.
- assume canonical completed-provenance is the status-line shape with an appended section allowed as an optional supplement; basis: origin 5's stated recommendation plus this authoring pass's corpus measurement (261 completed files; 222 with a `Status: done` line; 62 matching `^Status: done \(`, the status-line provenance variants; exactly 3 carrying an appended `## Implementation` section).
- assume the registry `archived` column means the actual archive date (the date the row's move executed); basis: origin 6's stated recommendation and the newest precedent row `tool-script-runtime-statistics` (archived 2026-09-23, filename dated 2026-09-22).
- assume the claimed-origin checker matches hyphen-bounded segments (the full filename stem, and also the stem with its leading date prefix stripped); basis: the maintenance SKILL.md External-gate slug-form matching precedent, applied in the conservative direction (a missed claim is the witnessed failure; a false positive only annotates).

Decision points requiring a grill: none remain.

## Gist & Examples

Six hygiene origins, one plan, six task clusters plus a final validation task.

1. **Claimed-origin mechanical checker (origin 1).** The 2026-09-22 formal-deferral sweep deferred 72 items by triage verdict alone and three had to be un-deferred: they were claimed by certified plans. This plan turns the learn item into a mechanical checker, `scripts/check_backlog_claimed.py`: given candidate backlog items, it greps each candidate's filename stem (with and without its date prefix) over top-level plan files and exits 1 naming each claiming plan and line. The maintenance SKILL.md survey gains a bulk disposition sweep gate ordering that run before any bulk move. Example: item `2026-09-16-review-staging-coverage-attempt-shadowing.md` is claimed by the open plan `docs/plans/2026-09-23-review-staging-leftovers-disposition.md`; the checker reports it claimed and the sweep skips it.
2. **Authoring slice reconciliation (origin 2).** The Step 5 authoring slice claims the whole fenced body is transmitted; observed practice transmits the payload paragraph only, so body-side duties (re-arm, checkpoints, compaction) never reached payload-born sessions. This plan aligns the slice text with the payload-paragraph assembly and moves compact duty sentence sets (re-arm, context checkpoints, final compaction) into the payload paragraph, following the claim-duty-tail precedent that landed 2026-09-23; the blueprint body paragraphs stay untouched, and the pins suite count-gates the new spans so slice text and transmitted region cannot drift apart again.
3. **Telemetry literal-prefix coupling (origin 3).** Accepted residual, made load-bearing: the execute-plan telemetry exception sentence gains the same-edit rule naming the two pins-suite freeze pins, so a future facts override cannot move the payload telemetry paths without moving the pins in the same edit.
4. **Shared-body forbidden-term precheck (origin 4).** A plan-prescribed insertion containing a forbidden term turned the consumer repo's mid-run suite RED outside declared scope. The plans skill gains the authoring rule: sweep every prescribed shared-body insertion against the runtime-neutrality gate's term list before certification; reword or declare the gate amendment in Review Scope. Validation Commands must run the gate itself.
5. **Completed provenance consolidation (origin 5).** One canonical status-line provenance shape (`Status: done (executed <YYYY-MM-DD> via <plan-path>)`); the three driver-batch-3 completed files gain that Status line and keep their appended `## Implementation` sections as the sanctioned optional supplement; the plans skill's completion step pins the canonical shape.
6. **Registry archived-date semantics (origin 6).** The `archived` column means the actual archive date: the three driver-batch-3 completed rows normalize 2026-09-22 to 2026-09-23, the registry header comment states the semantics (never the filename date prefix, never a plan-prescribed literal), and the plans skill's lifecycle step pins the cell rule so future plan tasks stop prescribing literal dates.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every Validation Command green on the executed tree, including the pins suite, the runtime-neutrality gate, the registry validator, and the rejected-archive lifecycle test.
- drift-resistance: every new contract span (slice wording, payload sentence sets, telemetry coupling, provenance shape, archived-date semantics) is covered by a mechanical gate (pin or exact-text grep), not prose alone.
- minimality: frozen regions stay byte-identical (blueprint bodies, the 258 other completed files, the execution blueprint); each partially-in-scope file names its open regions.
- portability: shared-body insertions pass the runtime-neutrality gate; no tool-specific tokens enter shared files.

**Done when:**
- the checker script and its unittest exist and pass; the maintenance survey gate bullet is present.
- the Step 5 slice names the payload-paragraph assembly; the payload paragraph carries the three compact sentence sets; pins count-gate all of them.
- the telemetry exception sentence names the same-edit pins rule; the pins comment records the coupling.
- the plans skill carries the precheck rule and the VC authoring rule; the completion step pins the canonical provenance shape; the three minority files carry the canonical Status line.
- the three registry rows carry 2026-09-23; the header comment states the actual-archive-date semantics; the lifecycle step pins the cell rule.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md` exits 0 at execution PRE-STEP.

**Ship when:**
- nothing external; all conditions are repo-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_backlog_claimed.py` *(new)*
- `scripts/check_maintenance_pins.sh` (checkpoint-pin block replacement, payload/slice pin additions, telemetry coupling comment)
- `agents/skills/maintenance/SKILL.md` (survey bullet insert, Step 5 slice sentence, Revisions-ledger entry; all other regions frozen)
- `agents/skills/maintenance/prompt-templates.md` (payload paragraph, the `Legend:` fill-in sentence, plus deviation-ledger entry only; all body paragraphs frozen by byte-parity pins)
- `agents/skills/execute-plan/SKILL.md` (telemetry exception sentence only; frozen otherwise)
- `agents/skills/plans/SKILL.md` (Exploration discipline append, VC authoring rule 37, completion step provenance shape, lifecycle archived-cell rule; frozen otherwise)
- `docs/maintenance/document-registry.md` (header comment sentence and the three named completed rows only)
- `docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md` (Status line only)
- `docs/history/backlog/completed/2026-09-18-execute-plan-test-suite-concurrency-safety.md` (Status line only)
- `docs/history/backlog/completed/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md` (Status line only)

**Tests:**
- `scripts/test_check_backlog_claimed.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the other 258 files under `docs/history/backlog/completed/`; reason: frozen provenance corpus, measured and deliberately not migrated.
- `agents/skills/execute-plan/subagent-prompts.md`, `agents/skills/execute-plan/agent-logs.md`; reason: shared-body set members this plan does not touch.
- `agents/skills/maintenance/zcode.md`; reason: recipe source of record, referenced but not edited.
- the six origin backlog items under `docs/history/backlog/`; reason: they ride the completion pass per the lifecycle, not this plan's edit targets.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1

# Task 1: checker unit suite (scratch fixtures; the suite owns mktemp and teardown)
( cd scripts && python3 -m unittest test_check_backlog_claimed ) || { echo "FAIL: checker unittest"; exit 1; }
grep -qF 'Bulk disposition sweep gate' agents/skills/maintenance/SKILL.md \
  || { echo "FAIL: survey gate bullet absent"; exit 1; }

# Task 1: checker gate semantics on the real corpus; exact exit codes required
# The known-claimed stem is this plan's own origin 1 stem: the claim surface is
# this plan's own top-level text (its origins block and this gate's own
# invocation literal), stable for the run's lifetime. The unclaimed probe stem
# is built at run time so the plan bytes never contain the expanded stem (a
# verbatim synthetic stem in this file would claim itself and pin the gate RED).
python3 scripts/check_backlog_claimed.py --slug 2026-09-22-deferral-sweeps-must-cross-check-claimed-origins
rc=$?
[ "$rc" -eq 1 ] || { echo "FAIL: known-claimed slug expected exit 1, got $rc"; exit 1; }
SYN="no-such-backlog-item-stem-xyz-$(date +%s)"
python3 scripts/check_backlog_claimed.py --slug "$SYN"
rc=$?
[ "$rc" -eq 0 ] || { echo "FAIL: synthetic unclaimed slug expected exit 0, got $rc"; exit 1; }

# Tasks 2-3: pins suite green after payload/slice/pin edits (byte-parity pins prove frozen bodies)
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }

# Task 3: telemetry coupling sentence present in the execute-plan skill
grep -qF 'moves the pins-suite freeze pins naming those payload paths' agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: telemetry coupling sentence"; exit 1; }
grep -qF 'pin "authoring blueprint checkpoint duty"' scripts/check_maintenance_pins.sh \
  || { echo "FAIL: checkpoint pin name lost"; exit 1; }
grep -qF 'pin "execution blueprint checkpoint duty"' scripts/check_maintenance_pins.sh \
  || { echo "FAIL: checkpoint pin name lost"; exit 1; }

# Task 4: runtime-neutrality gate over the shared bodies (the plans-skill insertions must pass it)
( cd scripts && python3 -m unittest \
  test_execute_plan_runtime.ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral ) \
  || { echo "FAIL: runtime-neutrality gate"; exit 1; }
grep -qF 'Shared-body forbidden-term precheck' agents/skills/plans/SKILL.md \
  || { echo "FAIL: precheck rule absent"; exit 1; }
grep -qF 'the Validation Commands block runs that gate itself' agents/skills/plans/SKILL.md \
  || { echo "FAIL: VC rule 37 absent"; exit 1; }

# Task 5: canonical provenance on exactly the three migrated files; bare Status line gone from them
for f in \
  docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md \
  docs/history/backlog/completed/2026-09-18-execute-plan-test-suite-concurrency-safety.md \
  docs/history/backlog/completed/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md; do
  grep -qF 'Status: done (executed 2026-09-23 via docs/plans/completed/2026-09-22-execute-plan-driver-batch-3.md)' "$f" \
    || { echo "FAIL: canonical provenance missing in $f"; exit 1; }
  if grep -q '^Status: done$' "$f"; then echo "FAIL: bare Status line remains in $f"; exit 1; fi
  grep -qF '## Implementation' "$f" || { echo "FAIL: supplement section lost in $f"; exit 1; }
done
grep -qF 'canonical provenance shape' agents/skills/plans/SKILL.md \
  || { echo "FAIL: completion-step provenance pin absent"; exit 1; }
test "$(grep -l '^## Implementation' docs/history/backlog/completed/*.md | wc -l | tr -d ' ')" -eq 3 \
  || { echo "FAIL: appended-section file count drifted (mass migration witness)"; exit 1; }

# Task 6: registry rows normalized and header comment states the semantics
grep -qF '| runtime-driver-blocked-claim-recovery-gap | no | completed | 2026-09-23 | executed |' docs/maintenance/document-registry.md \
  || { echo "FAIL: row 1 not normalized"; exit 1; }
grep -qF '| execute-plan-worktree-gitignored-bootstrap-gap | no | completed | 2026-09-23 | executed |' docs/maintenance/document-registry.md \
  || { echo "FAIL: row 2 not normalized"; exit 1; }
grep -qF '| execute-plan-test-suite-concurrency-safety | no | completed | 2026-09-23 | executed |' docs/maintenance/document-registry.md \
  || { echo "FAIL: row 3 not normalized"; exit 1; }
if grep -qF 'archived date from the filename date' docs/maintenance/document-registry.md; then
  echo "FAIL: filename-date semantics comment still present"; exit 1
fi
if grep -qF 'prefix. Aliases only where' docs/maintenance/document-registry.md; then
  echo "FAIL: wrapped-anchor remnant remains"; exit 1
fi
grep -qF 'Rows are backfilled; the archived column carries the actual archive date' docs/maintenance/document-registry.md \
  || { echo "FAIL: new header-comment sentence absent"; exit 1; }
grep -qF 'the actual archive date of this completion pass' agents/skills/plans/SKILL.md \
  || { echo "FAIL: lifecycle archived-cell rule absent"; exit 1; }
python3 scripts/doc_registry_validator.py validate || { echo "FAIL: registry validate"; exit 1; }

# Coordination: audit Task 5 lifecycle still green beside the registry edits
( cd scripts && python3 -m unittest test_rejected_archive_lifecycle ) \
  || { echo "FAIL: rejected-archive lifecycle"; exit 1; }

# Plan hygiene gates
bash scripts/check-no-em-dash.sh file docs/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md \
  || { echo "FAIL: em dash in plan"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "FAIL: hygiene scan"; exit 1; }
```

### Task 1: Claimed-origin mechanical checker (origin 1)

Files:
- `scripts/check_backlog_claimed.py` *(new)*
- `scripts/test_check_backlog_claimed.py` *(new)*
- `agents/skills/maintenance/SKILL.md`

- [x] `test_check_backlog_claimed#test_claimed_by_origin_list`; given a fixture plans dir whose top-level plan quotes `docs/history/backlog/2026-09-20-example-origin-item.md` in an origins block, expects `check_backlog_claimed.py --slug 2026-09-20-example-origin-item` exits 1 and prints the claiming plan path and line number [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_unclaimed_stem_passes`; given the same fixture and a stem no plan names, expects exit 0 with no findings [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_undated_stem_matches`; given a plan line referencing `example-origin-item` without the date prefix, expects exit 1 via the date-stripped match form [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_hyphen_bounded_no_partial_word`; given a plan line containing `example-origin-itemx` (stem extended mid-token), expects no match and exit 0 [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_completed_and_deferred_plans_ignored`; given a match only under the fixture plans dir's `completed/` and `deferred/` subdirectories, expects exit 0 (top-level plans only claim) [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_missing_plans_dir_exits_two`; given `--plans-dir` pointing at a nonexistent path, expects exit 2 with an error line, not exit 0 [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_repeatable_slug_multi_candidate`; given one run carrying two repeatable `--slug` occurrences (one claimed by the fixture plan, one unclaimed), expects exit 1 with a finding naming only the claimed stem [class: REPOSITORY_TEST]
- [x] `test_check_backlog_claimed#test_md_path_form_normalized_to_stem`; given `--slug docs/history/backlog/2026-09-20-example-origin-item.md` (the `.md` path form), expects the same exit-1 claimed finding via stem normalization [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd scripts && python3 -m unittest test_check_backlog_claimed )` fails on the missing module [class: REPOSITORY_TEST]
- [x] Write `scripts/check_backlog_claimed.py`: stdlib-only argparse; repeatable `--slug` accepting stems or `.md` paths (normalized to stems); `--plans-dir` override resolved from the repo facts file (`plans_dir` key, default `docs/plans/`), anchored at the repo root, no machine-specific absolute paths; matching = a candidate's filename stem, or the stem with its leading `YYYY-MM-DD-` prefix stripped, occurring as a hyphen-bounded segment of any line of a top-level plan file; output one finding line per hit (`CLAIMED <stem> -> <plan-path>:<line>`); exit 0 when no candidate is claimed, 1 when any is, 2 on usage or path errors [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the unittest suite passes [class: REPOSITORY_TEST]
- [x] Survey gate bullet in `agents/skills/maintenance/SKILL.md`: insert a new bullet immediately after the `Priority profile resolution` survey bullet, exact text: `- Bulk disposition sweep gate (P51 origin 1; origin docs/history/backlog/2026-09-22-deferral-sweeps-must-cross-check-claimed-origins.md): before a bulk deferral/disposition sweep moves open backlog items (a git mv into the backlog directory's deferred/ or rejected/ archive, or a bulk Status flip over many items), the sweep runs the claimed-origin checker (python3 scripts/check_backlog_claimed.py, one invocation carrying every candidate slug) and treats a claimed report as skip-and-annotate: the claimed item is never moved (ownership beats triage verdict; a top-level plan's origin list or validation-gate literal naming the item is the claim), and the sweep's output records the skip with the claiming plan path. Manual sweep prompts order the same run; the checker's exit 1 is the gate's stop signal.` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: claimed-origin checker and bulk disposition sweep gate (P51 origin 1)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Authoring slice reconciliation and payload duty sentence sets (origin 2)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] In `agents/skills/maintenance/SKILL.md` Step 5, replace the sentence beginning `Authoring slice: for an authoring child the scheduled prompt is the authoring blueprint's fenced body` with, exactly: `Authoring slice: observed dispatch practice transmits the authoring blueprint's payload paragraph (the span opening Schedule at {schedule_time} the following task: through the paragraph's end) as the authoring child's scheduled prompt, not the whole fenced body: the deciding turn fills {REPO_ROOT} (in the payload paragraph's RE-ARM DUTY sentence set), {schedule_time}, and {backlog_item} and transmits that paragraph; the payload paragraph is self-contained for the duties a child session must see (re-arm, claim lifecycle, context checkpoints, compaction, review, landing), and the rest of the fenced body is the body-side specification that the payload's compact sentence sets mirror; the two field lines after the block are fill-in spec and are never part of the payload.` [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/prompt-templates.md`, insert into the authoring payload paragraph, immediately before the sentence beginning `AUTHORING CLAIM DUTY (apply in this authoring session`, this exact sentence set: `RE-ARM DUTY (apply as this session's FIRST ACTION, before any plan work): restore the maintenance loop parent state-first, without listing first, exactly per the re-arm duty recipe in agents/skills/maintenance/zcode.md ("Recurring automation recipe"): read .ai-playbook/scheduler-state.json first, take the last matching children[] entry as your record (no matching entry means proceed with a null record), and apply the first applicable step of the recipe's steps with the recipe's HOST CAVEAT (a recycling echo not verifiably the intended form is a refusal routed to the delete-plus-create path), its loop guard and one-recorded-mutation carve-out, and its pending_rearm park path; {REPO_ROOT} is the repository root the recipe's recognition matchers require. This payload carries the re-arm duty because payload-born sessions are the dispatch ladder's re-arm carriers.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to the end of the same payload paragraph (after the sentence ending `and the next turn's landing-completion work lands from them.`), this exact sentence set: `CONTEXT CHECKPOINTS: after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: plans-authoring) to docs/tmp/authoring/<plan-slug>/context.jsonl (create the run's telemetry directory if needed), measure context per the overlay's measurement primitive (agents/skills/maintenance/zcode.md, "Context measurement primitive"; a char-count proxy fallback result is labeled an estimate in the record), and act per the threshold ladder of the execute-plan "Context budget checkpoints" policy. FINAL STEP, after the report: compact this session with the runtime's session-compact command (in ZCode, /compact) so the next scheduled payload inherits a short transcript; if your runtime gives you no way to trigger compaction yourself, end the report with that stated in one sentence.` [class: IMPLEMENTATION_REQUIRED]
- [x] Deviation-ledger entry in `agents/skills/maintenance/prompt-templates.md`, appended as the last list entry before the `Legend:` line, exact text: `- Payload compact duty sentence sets and slice reconciliation (2026-09-23, plan docs/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md Task 2; origin: docs/history/backlog/2026-09-22-maintenance-authoring-slice-whole-body-vs-payload-practice.md): the authoring payload paragraph gains compact RE-ARM DUTY, CONTEXT CHECKPOINTS, and FINAL STEP sentence sets (the re-arm set delegating to the zcode.md recipe as its single source), and the Step 5 authoring slice in SKILL.md is rewritten to describe the payload-paragraph assembly practice, reconciling the slice-versus-assembly contradiction the 2026-09-23 claim-tail entry records; the blueprint body paragraphs are untouched (byte-parity pins unchanged) and the pins suite count-gates the new spans. Not part of the backlog source text.` [class: IMPLEMENTATION_REQUIRED]
- [x] Legend fill-in spec in `agents/skills/maintenance/prompt-templates.md`: in the `Legend:` paragraph, extend the `{REPO_ROOT}` location parenthetical, replacing `(in the execution blueprint's opening sentence and in the re-arm duty paragraph of both blueprints)` with exactly `(in the execution blueprint's opening sentence, in the re-arm duty paragraph of both blueprints, and in the authoring payload paragraph's RE-ARM DUTY sentence set)`, so the two in-repo assembly descriptions (Legend and Step 5 slice) agree after Task 2 [class: IMPLEMENTATION_REQUIRED]
- [x] Revisions-ledger entry in `agents/skills/maintenance/SKILL.md`, inserted at the top of the Revisions ledger (newest-first), exact text: `- 2026-09-23 (P51 plans/authoring surface hygiene, docs/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md Task 2; origin docs/history/backlog/2026-09-22-maintenance-authoring-slice-whole-body-vs-payload-practice.md): the Step 5 authoring slice is rewritten from whole-fenced-body wording to the observed payload-paragraph assembly (the deciding turn transmits the payload paragraph with {REPO_ROOT}, {schedule_time}, and {backlog_item} filled); the authoring blueprint's payload paragraph carries compact RE-ARM DUTY, CONTEXT CHECKPOINTS, and FINAL STEP sentence sets so payload-born sessions see the duties that must reach them (the claim lifecycle set landed earlier the same day); the body paragraphs stay the body-side specification and the pins suite count-gates the new spans (authoring checkpoint span body + payload = 2, execution body = 1).` [class: IMPLEMENTATION_REQUIRED]
- [x] Pins in `scripts/check_maintenance_pins.sh`: replace the two `grep -qF` checkpoint pins with count-gated pins KEEPING the existing pin descriptions (`pin "authoring blueprint checkpoint duty"`, `pin "execution blueprint checkpoint duty"`; Task 3's inserted sentence hardcodes these names), exact expectations: the authoring checkpoint span (`after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: plans-authoring) to docs/tmp/authoring/<plan-slug>/context.jsonl`) occurs exactly 2 times in `$P` (body + payload); the execution checkpoint span (same shape with `skill: execute-plan` and `docs/tmp/execute-plan/`) occurs exactly 1 time in `$P` (body only); and add: `pin "authoring slice payload-region wording" grep -qF 'observed dispatch practice transmits the authoring blueprint' "$S"`; count gate `restore the maintenance loop parent state-first, without listing first` exactly 1 in `$P` (payload re-arm set); count gate `FINAL STEP, after the report: compact this session` exactly 3 in `$P` (execution body + authoring body + payload) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 with the new pins in place (the byte-parity re-arm pins prove the body paragraphs are untouched) [class: REPOSITORY_TEST]
- [x] Run → expect RED-proof today, then GREEN after the edit: before Task 2's edits exactly four of the five new or retyped pins fail (the authoring checkpoint count gate reads 1 against its expected 2, the re-arm needle count 0 against 1, the FINAL STEP needle count 2 against 3, and the slice-wording presence pin finds no span), while the execution-checkpoint count gate passes both runs (its expectation of exactly 1 is already satisfied by the untouched execution body; the retyped gate's expectation is unchanged); record both runs in the task log [class: REPOSITORY_TEST]
- [x] Commit: `feat: authoring slice reconciled to payload-paragraph assembly with payload duty sentence sets (P51 origin 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Telemetry literal-prefix same-edit coupling (origin 3)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] In `agents/skills/execute-plan/SKILL.md`, in the telemetry exception sentence (the sentence beginning `The maintenance blueprints' payload paths`), replace the sentence's closing period with exactly: `; that revisit moves the pins-suite freeze pins naming those payload paths (pin "authoring blueprint checkpoint duty", pin "execution blueprint checkpoint duty" in scripts/check_maintenance_pins.sh) in the same edit, so the pinned literal never silently diverges from the payload it freezes.` (the appendage ends with the sentence's period) [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/check_maintenance_pins.sh`, add one comment line directly above the checkpoint pins block: `# Same-edit coupling (P51 origin 3): a payload telemetry path change edits the body text and these pins in one edit; see the execute-plan skill's telemetry exception sentence.` [class: IMPLEMENTATION_REQUIRED]
- [x] Neutrality proof: the inserted sentence text carries no forbidden term from the runtime-neutrality tuple (its `context.jsonl` mention rides the gate's sanctioned path-literal replacement); run the gate per Validation Commands [class: REPOSITORY_TEST]
- [x] Commit: `feat: telemetry literal-prefix same-edit coupling recorded at both ends (P51 origin 3)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Shared-body forbidden-term precheck authoring rule (origin 4)

Files:
- `agents/skills/plans/SKILL.md`

- [x] Append to the `Exploration discipline` paragraph in `agents/skills/plans/SKILL.md`, exactly: `Shared-body forbidden-term precheck (P51 origin 4): when a plan prescribes literal insertions into a shared skill body covered by the consumer repository's shared-body forbidden-term gates (this repository: the shared-file set and forbidden-term tuple of test_shared_skill_bodies_remain_runtime_neutral in scripts/test_execute_plan_runtime.py), sweep each prescribed insertion's exact text against that gate's term list before certification, honoring the gate's sanctioned path-literal replacements, and either reword the prescribed text or declare the gate amendment in the plan's Review Scope; an insertion that ships a forbidden term turns the consumer repo's mid-run full suite RED outside the plan's declared scope, and the executor then widens a frozen test file as plan-related regression repair.` (placement note: the Exploration discipline paragraph is the pre-certification authoring pass where the sweep belongs; the companion rule lands in the Validation Commands authoring rules area origin 4 names) [class: IMPLEMENTATION_REQUIRED]
- [x] Add a new numbered rule to the `Validation Commands (authoring rules)` list after rule 36, exactly: `37. **Shared-body gate exercise:** when any task prescribes literal insertions into a shared skill body covered by a shared-body forbidden-term gate, the Validation Commands block runs that gate itself (this repository: the runtime-neutrality test) rather than relying on presence greps; a gate the plan never executes can be broken by the insertion and stay unproven.` [class: IMPLEMENTATION_REQUIRED]
- [x] Self-application proof (record in the task log): this plan's own shared-body insertions (Task 3 into execute-plan SKILL.md; this task and Tasks 5-6 into plans SKILL.md) were swept against the tuple before certification and carry none of the forbidden terms [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the runtime-neutrality gate passes on the edited tree [class: REPOSITORY_TEST]
- [x] Commit: `feat: shared-body forbidden-term precheck rule and gate-exercise validation rule (P51 origin 4)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Completed provenance consolidation (origin 5)

Files:
- `docs/history/backlog/completed/2026-09-18-runtime-driver-blocked-claim-recovery-gap.md`
- `docs/history/backlog/completed/2026-09-18-execute-plan-test-suite-concurrency-safety.md`
- `docs/history/backlog/completed/2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`
- `agents/skills/plans/SKILL.md`

- [x] In each of the three files, replace the bare `Status: done` line with exactly `Status: done (executed 2026-09-23 via docs/plans/completed/2026-09-22-execute-plan-driver-batch-3.md)`; keep each file's appended `## Implementation` section untouched (it becomes the sanctioned optional supplement) [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/plans/SKILL.md` Plan Lifecycle completion step, extend the promoted-item sentence with two edits in one pass: replace the Markdown code span carrying `Status: done` (the anchor includes its backticks; keep the replacement inside code-span backticks) with `Status: done (executed <YYYY-MM-DD> via <plan-path>)`, and insert exactly `(the canonical provenance shape; a completed file may additionally carry a richer appended ## Implementation / Implementation source: section as an optional supplement, never as the only provenance)` immediately after the words `in the same edit`, before the following comma [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the three exact-text greps and the negated bare-Status check per Validation Commands pass; the other 258 completed files are untouched [class: REPOSITORY_TEST]
- [x] Commit: `feat: canonical completed provenance shape on the driver-batch-3 minority files (P51 origin 5)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Registry archived-date semantics (origin 6)

Files:
- `docs/maintenance/document-registry.md`
- `agents/skills/plans/SKILL.md`

- [x] In `docs/maintenance/document-registry.md`, change the `archived` cell from `2026-09-22` to `2026-09-23` on exactly the three completed rows whose identity is `runtime-driver-blocked-claim-recovery-gap`, `execute-plan-worktree-gitignored-bootstrap-gap`, and `execute-plan-test-suite-concurrency-safety`; no other row changes [class: IMPLEMENTATION_REQUIRED]
- [x] In the same file's header comment, replace the wrapped two-line span (the line reading `Rows are backfilled: archived date from the filename date` together with the leading `prefix.` of the following line) with the single-line sentence exactly: `Rows are backfilled; the archived column carries the actual archive date (the date the row's move executed), never the filename date prefix and never a plan-prescribed literal date.`; a partial replace that leaves the `prefix. Aliases only where` line beginning intact is a defect the Validation Commands detect [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/plans/SKILL.md` Plan Lifecycle first bullet, extend the registry-row cell list, replacing `archived: YYYY-MM-DD` with exactly `archived: YYYY-MM-DD (the actual archive date of this completion pass; never a date copied from the plan filename or prescribed by a plan task)` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/doc_registry_validator.py validate` exits 0; the three row greps and the negated filename-date check per Validation Commands pass [class: REPOSITORY_TEST]
- [x] Commit: `feat: registry archived column means the actual archive date (P51 origin 6)` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Final validation suite

Files:
- none (verification only)

- [x] Run the whole `## Validation Commands` block from the repo root; expect every gate green with no skipped check, and record the full output in the task log [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md`; expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `chore: P51 final validation suite green` [class: IMPLEMENTATION_REQUIRED]
