# Plan: Outcome contract migration, batch 1: the landing and closeout gates

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-03-outcome-contract-migration-landing-parentage-gate.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-prestage-freshness-gate.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-done-lock.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-done-sweep-gates.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-done-sweep-gates-lib.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-check-plan-origins-closed.md`

Driving force: automation + code-quality
Plan review record: the staging series docs/reviews/2026-10-03-plan-review-outcome-contract-migration-batch-1-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The five top-ranked rows of scripts/OUTCOME_CONTRACT.md's migration register (the landing and closeout gate family) report the contract's four outcomes, so their agent-facing callers can branch explicitly on pass, fail, indeterminate, and tool error instead of guessing from legacy exit codes.

- scripts/landing_parentage_gate.py, scripts/prestage_freshness_gate.py, and scripts/check_plan_origins_closed.py retire the guard-family exit-2 tool-failure vocabulary: the former exit-2 class splits per Task 1's mappings into indeterminate (exit 2, the plumbing cannot answer over resolved inputs) and tool error (exit 3, usage, environment, or unheld assumptions), with every former exit-2 site mapped explicitly, and every non-metadata run ends with a final `OUTCOME:` line.
- scripts/done-lock.sh classifies held, ambiguous-holder, stale-clean refusal, and environment failures as distinct outcomes through a per-subcommand outcome table, with the acquire subcommands' eval-consumed stdout kept parseable.
- scripts/done_sweep_gates.sh maps gate results into contract outcomes, captures a crashed gate helper as an indeterminate run instead of a traceback abort, and the done-sweep lib's origins consumer branches on all four outcomes instead of collapsing indeterminate and tool error into a refuse.
- The five register rows record each script's declared operating-context assumptions, and the primary caller recipes branch on every outcome plus the missing-OUTCOME-line rule.

Gate delta: counted classes (refusal classes, hard gates, fences, protocol layers, schema state fields) +0 net-new machinery: the exit-vocabulary remap, the per-script indeterminate arms (including the new prestage type-change detection and the origins unreadable-origin remap), and the sweep crash-capture replace the documented guard-family contract under the landed contract document scripts/OUTCOME_CONTRACT.md, which is the doctrine receipt pricing this migration (a grown checked-condition set and a contract change witnessed by the landed register; no new incident is required, per the migration entry's authoring constraint); the final `OUTCOME:` line is an output convention, not a counted class.

## Terms

- **outcome contract**: the four-outcome convention of scripts/OUTCOME_CONTRACT.md (exit 0 pass, 1 fail, 2 indeterminate, 3 tool error, plus the final `OUTCOME:` line).
- **guard-family contract**: the three python gates' current documented vocabulary (0 pass, 1 refuse, 2 tool failure) that this migration retires.
- **answer-vocabulary criterion**: the classification rule separating the two former tool-failure buckets: inputs both resolved and the git plumbing answered outside its 0/1 answer vocabulary is indeterminate; an input that never resolved, an unreadable input, a usage error, or an unheld environment assumption is tool error.
- **migration register**: the per-script table in scripts/OUTCOME_CONTRACT.md whose Status column tracks queued and migrated rows and whose Assumptions column is filled at each migration's authoring.
- **eval-consumed stdout**: subcommand output whose stdout is consumed by shell eval (the lock exports), which cannot carry extra lines.
- **caller obligation**: the rule that an agent must not treat indeterminate or tool error as pass or fail, nor continue a dependent destructive or landing action on such a result.

## Assumptions

- assume batch 1 is the five table rows the migration entry's ranking note names (landing_parentage_gate, prestage_freshness_gate, done_sweep_gates pair, done-lock, check_plan_origins_closed), six origin files; basis: the entry's arm 6 text ("landing and closeout gates ... outrank advisory checks") and its delegation of batch sizing to the authoring pass.
- assume the remaining eight register rows stay queued with their backlog origins open, and the register table itself is the tracked successor path: each row's Status column and the contract's ranking note are what a successor authoring pass re-derives from; basis: the register's declared purpose ("the table is the migration register, not a claim of complete coverage") and the entry's coordination clause making this plan the sequencer of its own batches.
- assume done-lock's held result maps to fail (a definitive, evidenced state: holder alive) and the ambiguous-holder shapes (meta-less lock past the incomplete age, crash-leftover adjudication) map to indeterminate; basis: the contract's definitions (fail = evidence establishes a modeled violation, with evidence identified; indeterminate = insufficient or contradictory evidence) applied to the lock's documented exit semantics.
- assume the acquire subcommands emit their `OUTCOME:` line on STDERR because their stdout is eval-consumed (the exports); every other subcommand emits it on stdout; basis: done-lock.sh's usage documents the MERGE_LOCK exports consumed by eval, and the contract's no-extra-line requirement for eval parsing wins over the default stdout placement, recorded here as a declared deviation.
- assume callers' exit-2 branching is enumerated rather than assumed absent, and the enumeration known at authoring is: agents/skills/maintenance/prompt-templates.md line 87 routes a landing-gate exit 2 to the stranding-report path, and scripts/done_sweep_gates_lib.py's origins consumer branches zero-versus-nonzero on the origins gate; both surfaces gain explicit four-outcome branches in Tasks 1 and 3, and each migration task's probe re-derives the enumeration live at execution rather than trusting this list.
- assume the origins corpus-scan warn arm keeps its always-exit-0 survey contract only for fully-resolved runs: observed indeterminate evidence flips it to exit 2 under the contract's dominance rule, and the maintenance survey consumer is updated in Task 4 accordingly; basis: the contract's multi-input rule and the survey's warn-only role.
- assume the sibling scanner-validator refactor (landed d3cba8a5, refactor-first recorded) needs no re-sequencing here: none of the five batch-1 scripts is in its refactored set, and the validate_review_staging and scan-public-hygiene rows stay queued; basis: the landed plan's sequencing assumption and the register rows.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: migrates the five landing and closeout gate rows to the outcome contract's four-outcome vocabulary with declared assumptions and caller branching, automation for the agent loop that today cannot tell a modeled refusal from a broken check.

Today a landing recipe that runs scripts/landing_parentage_gate.py sees exit 2 and cannot distinguish "the gate could not run" from "the evidence was insufficient" except by reading prose; the done-sweep lib's origins consumer turns any non-zero origins result into a modeled refuse, so after this batch every run ends with a parseable outcome, the lock's ambiguous-holder case reports indeterminate instead of masquerading as a held state, a crashed sweep gate helper is captured as an indeterminate run instead of a traceback abort, and the origins consumer stops converting "cannot determine" into a violation.

## Evaluation Criteria

**Quality dimensions:**
- contract conformance: every migrated script emits exactly one final `OUTCOME:` line per non-metadata run (stderr for done-lock's acquire subcommands; none for `--help`/usage text, per the contract's metadata exemption), with exit codes matching the contract including the argparse override.
- behavior preservation for modeled cases: every pre-migration pass and refuse case keeps its verdict, with exactly two declared exceptions this plan introduces as new modeled arms: the prestage type-change case (previously a stale refuse or a bogus byte-equality pass) and the origins unreadable-origin case (previously a straggler refuse; remapped because evidence-insufficient is the contract's indeterminate definition, not a modeled violation).
- caller explicitness: each primary caller recipe branches on all four outcomes and on the missing-OUTCOME-line rule (treat as tool error, stop, re-derive from disk), and no caller collapses indeterminate or tool error into a refuse.
- regression net: all five existing test files and the done-lock built-in selftest stay green after each task, with their legacy exit-2 arms renewed per the checklist items.

**Done when:**
- The five scripts' test files pass under the test venv with the new outcome fixtures (pass, fail, indeterminate, tool error, one previously unmodeled input each) and the renewed legacy arms.
- scripts/OUTCOME_CONTRACT.md shows the five batch rows flipped to migrated with declared assumptions and the compatibility note extended for batch 1.
- The caller surfaces (agents/skills/done/SKILL.md gate sections and its Step 0 and Step 2 done-lock recipes, agents/skills/maintenance/prompt-templates.md landing recipes, agents/skills/execute-plan/SKILL.md, agents/skills/plans/SKILL.md, agents/skills/maintenance/SKILL.md) branch on every outcome where they gate on these scripts.

**Ship when:**
- Nothing; the work is repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/landing_parentage_gate.py`
- `scripts/prestage_freshness_gate.py`
- `scripts/check_plan_origins_closed.py`
- `scripts/done-lock.sh`
- `scripts/done_sweep_gates.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/OUTCOME_CONTRACT.md`

**Tests:**
- `scripts/test_landing_parentage_gate.py`
- `scripts/test_prestage_freshness_gate.py`
- `scripts/test_check_plan_origins_closed.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_wrapper.py`

**Skills and recipes:**
- `agents/skills/done/SKILL.md` (the sweep-gate sections, the dirt-gate outcome paragraph, and the Step 0 and Step 2 done-lock recipes)
- `agents/skills/maintenance/prompt-templates.md` (the landing and closeout recipes, including the line-87 stranding-report routing)
- `agents/skills/maintenance/SKILL.md` (gate invocations)
- `agents/skills/execute-plan/SKILL.md` (landing tail and lock recipes)
- `agents/skills/plans/SKILL.md` (archive gate invocation)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** in the five scripts, only the exit-code vocabulary, the result-emission paths, the new indeterminate arms (including the prestage type-change detection and the origins consumer branch in the sweep lib), their docstrings, and their usage texts are in scope; each script's classification logic for existing pass and refuse cases is frozen (findings there are pre-existing defects, filed separately, not fixed here), with the single exception of the origins-consumer arm in the sweep lib that Task 3 rewires. In the five skill files, only the recipe steps that invoke the five scripts and their outcome-handling text are in scope; everything else is frozen.

**Out of scope; reject unless plan-related:**
- `scripts/release-authoring.sh`, `scripts/release-rewrite.sh`, `agents/skills/lessons-migrate/SKILL.md`, `agents/skills/cursor-agent-diagnose/run.sh`, `agents/skills/maintenance/zcode.md`; their done-lock references are exit-agnostic (release-authoring dies on any lock failure, release-rewrite greps status text, the diagnostic runner checks presence only), a property each migration task's probe re-verifies live.
- `scripts/dirt_regression_gate.py`; already migrated by the contract plan (the compatibility note's precedent).
- The eight still-queued register rows and their origins; successor batches own them.

## Validation Commands

```bash
PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
$PY scripts/test_landing_parentage_gate.py
$PY scripts/test_prestage_freshness_gate.py
$PY scripts/test_check_plan_origins_closed.py
$PY scripts/test_done_sweep_gates_lib.py
$PY scripts/test_done_sweep_gates_wrapper.py
bash scripts/done-lock.sh selftest
if grep -n 'Exit codes: 0 pass, 1 refuse, 2 tool failure' scripts/landing_parentage_gate.py scripts/prestage_freshness_gate.py; then echo "guard-family vocabulary survived"; exit 1; fi
python3 scripts/check_plan_origins_closed.py --plan docs/history/backlog/PLAN-PROMPTS-does-not-exist.md; rc=$?; if [ "$rc" -ne 3 ]; then echo "origins gate tool failure is not exit 3 (got $rc)"; exit 1; fi
test "$(grep -c '| migrated' scripts/OUTCOME_CONTRACT.md)" -eq 6 || { echo "register rows not all flipped (want 6)"; exit 1; }
for f in agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/maintenance/SKILL.md; do test -f "$f" || { echo "missing caller surface $f"; exit 1; }; grep -q 'OUTCOME' "$f" || { echo "no outcome branching text in $f"; exit 1; }; done
```

Authoring-time gate evidence: the stale-vocabulary sweep is RED today (the guard-family line stands in landing_parentage_gate.py line 17 and prestage_freshness_gate.py line 19) and flips GREEN when those scripts migrate; the origins probe is RED today (an unreadable plan exits 2 at authoring time, verified by execution) and flips GREEN at exit 3; the register count gate is RED today (`grep -c '| migrated'` counts 1, the dirt-gate precedent row) and flips GREEN at 6 (the five batch rows plus the precedent); the caller-surface greps are RED today (no OUTCOME text in the three files) and flip GREEN in Task 1's caller step; the six run-gates are GREEN today under the test venv (the two done-sweep suites import pytest and fail with ModuleNotFoundError under the bare python3, witnessed at authoring time) and must stay green through every task boundary; the plan bytes passed the no-em-dash touched scan, the public-hygiene scan, and `python3 scripts/plan_readiness.py --pre-round` before round 1.

### Task 1: Migrate the guard-family trio to the four-outcome contract

Files:
- `scripts/landing_parentage_gate.py`
- `scripts/prestage_freshness_gate.py`
- `scripts/check_plan_origins_closed.py`
- `scripts/test_landing_parentage_gate.py`
- `scripts/test_prestage_freshness_gate.py`
- `scripts/test_check_plan_origins_closed.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `$PY scripts/test_landing_parentage_gate.py`; covers the landing-gate fixtures, the renewed legacy arms, and every pre-existing arm
- `$PY scripts/test_prestage_freshness_gate.py`; covers the prestage fixtures, the renewed legacy arm, and every pre-existing arm
- `$PY scripts/test_check_plan_origins_closed.py`; covers the origins fixtures, the aggregation arm, and every pre-existing arm

- [x] RED: add per-script outcome fixtures first: for each of the three scripts a pass case (exit 0 plus final `OUTCOME: pass`), a fail case (exit 1 plus `OUTCOME: fail` with the offending evidence), a tool-error case (an unresolvable-rev or unreadable-input shape, now exit 3 plus `OUTCOME: tool_error`), and the indeterminate cases pinned below; run → expect RED: the landing and prestage tool-error fixtures see legacy exit 2 (an unresolvable rev, an unreadable fresh list), the origins tool-error fixture has no exit-3 path either (an absent plans dir exits 0 with a warning, an unreadable one silently scans as empty and also exits 0: pathlib rglob suppresses the permission error, verified by execution), the never-modeled indeterminate shapes see legacy exit 0 or 1, usage errors see argparse's default exit 2, and no run emits an OUTCOME line [class: REPOSITORY_TEST]
- [x] `LandingParentageGateOutcomeTest#test_plumbing_failure_over_resolved_revs_is_indeterminate`; given both the merge-base ancestry check and the pre-swap parents rev-list failing internally (exit above the 0/1 answer vocabulary) while both revs resolved, expects exit 2 and `OUTCOME: indeterminate` with an observed/could-not-determine evidence line, per the answer-vocabulary criterion; and `LandingParentageGateOutcomeTest#test_usage_error_is_tool_error`; given a malformed argument, expects exit 3 with `OUTCOME: tool_error` (the argparse exit override), while `--help` stays metadata-exempt with no OUTCOME line [class: REPOSITORY_TEST]
- [x] `PrestageFreshnessGateOutcomeTest#test_typechange_path_is_indeterminate`; given a candidate path whose HEAD tree mode disagrees with the disk lstat type (file versus symlink, including the dangling-symlink subcase), detected by the NEW explicit type check this task adds ahead of the byte comparison, expects exit 2 and `OUTCOME: indeterminate` naming the path; the RED expectation records today's legacy behavior for the same input (a stale refuse at exit 1, or a bogus byte-equality pass at exit 0 when a symlink's target bytes equal the HEAD blob), which is why this arm is a declared preservation exception [class: REPOSITORY_TEST]
- [x] `CheckPlanOriginsClosedOutcomeTest#test_unreadable_origin_is_indeterminate`; given an origins block whose origin file exists but cannot be read at classification time, expects exit 2 and `OUTCOME: indeterminate` naming that origin (a declared preservation exception: today this shape straggles at exit 1); `CheckPlanOriginsClosedOutcomeTest#test_mixed_corpus_is_indeterminate`; given one open origin and one unreadable origin, expects exit 2 with BOTH named per the contract's dominance rule; and `CheckPlanOriginsClosedOutcomeTest#test_unreadable_plans_dir_is_tool_error`; given an unreadable plans directory, expects exit 3 [class: REPOSITORY_TEST]
- [x] Remap each script's exit vocabulary site by site under the answer-vocabulary criterion: plumbing failures over resolved inputs become indeterminate (exit 2), input-resolution failures, unreadable inputs, usage and argparse errors (overridden to exit 3 with an OUTCOME line), and unheld environment assumptions become tool error (exit 3), modeled refusals stay exit 1, and every non-metadata run ends with exactly one final `OUTCOME:` line after the human-readable evidence; the corpus-scan warn arm keeps exit 0 only for fully-resolved runs and reports indeterminate (exit 2) when unreadable evidence was observed [class: IMPLEMENTATION_REQUIRED]
- [x] Update each script's docstring exit-code line to the four-outcome vocabulary (metadata exemption named) and draft the per-script operating-context assumptions for the register (invocation inside a git repository with resolvable revs for the landing gate; an existing repository and readable candidate paths for the prestage gate; a readable backlog and plans directory for the origins gate) [class: IMPLEMENTATION_REQUIRED]
- [x] Renew the pre-existing legacy-exit-2 arms the remap invalidates: the tool-failure-shape arms in scripts/test_landing_parentage_gate.py and scripts/test_prestage_freshness_gate.py that assert returncode 2 now assert 3, keeping every other arm untouched [class: REPOSITORY_TEST]
- [x] Probe the three scripts' callers for exit-2 branching, verifying the enumerated assumption live and recording the receipt (known member: the prompt-templates line-87 stranding-report routing, rewritten in Task 4); update the outcome-handling text in the three caller surfaces in this task's Files so each branches explicitly on the four outcomes and the missing-OUTCOME-line rule, and re-verify the exit-agnostic claim for scripts/release-authoring.sh, scripts/release-rewrite.sh, and agents/skills/maintenance/zcode.md [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the three test files under `$PY` [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate guard-family gates to the outcome contract` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Migrate done-lock to the four-outcome contract

Files:
- `scripts/done-lock.sh`

Evidence:
- `bash scripts/done-lock.sh selftest`; covers the built-in race and fence fixtures plus the new outcome arms

- [x] RED: add selftest arms for the outcome mapping, passing DONE_LOCK_POLL_SECS=1 through the harness so the max-wait arm exhausts in seconds: an acquired acquire emits exit 0 with `OUTCOME: pass` on stderr; a max-wait exhaustion against a live holder emits exit 1 with `OUTCOME: fail` naming the holder evidence; an ambiguous-holder case (meta-less lock past the incomplete age) emits exit 2 with `OUTCOME: indeterminate`; a usage error emits exit 3 with `OUTCOME: tool_error`; run → expect RED [class: REPOSITORY_TEST]
- [x] Remap the vocabulary through a per-subcommand outcome table covering every existing exit site (r2-verified inventory: non-acquire usage-class exits follow the same tool-error rule the acquire family states): acquire family (success pass; held and max-wait exhaustion fail with holder evidence; ambiguous holder indeterminate; usage and not-a-git-repo tool error); stale-clean (incomplete-too-new indeterminate: safety cannot be adjudicated; lock-changed-under-us fail with the race evidence; still-active fail with the holder evidence; unreadable lock metadata at the `load_lock_meta || exit 1` guard tool error: unsupported lock data); status (pass with the reported state in the evidence lines); release (success pass; release-mismatch and lock-changed-under-us fail; missing-env refusal tool error (invocation unheld); meta-missing refusal tool error (the token cannot be verified against absent metadata, so the release check cannot run reliably)); selftest (pass or fail by harness result); non-acquire subcommands emit `OUTCOME:` on stdout, the acquire subcommands on STDERR so their eval-consumed stdout stays export-only, and the usage text documents the placement deviation and the metadata exemption [class: IMPLEMENTATION_REQUIRED]
- [x] Renew the pre-existing selftest arms that assert merge-acquire over a hold exits 2 (the want-2 arms in the selftest harness) to assert exit 1 with the fail outcome [class: REPOSITORY_TEST]
- [x] Probe the eval consumers (the landing recipes in agents/skills/maintenance/prompt-templates.md and agents/skills/execute-plan/SKILL.md, plus the done skill's Step 0 and Step 2 recipes) for exit-2 branching, record the receipt, and update their outcome-handling text to branch on the four outcomes and the missing-OUTCOME-line rule [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/done-lock.sh selftest` [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate done-lock to the outcome contract` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Migrate the done-sweep pair to the four-outcome contract

Files:
- `scripts/done_sweep_gates.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_wrapper.py`

Evidence:
- `$PY scripts/test_done_sweep_gates_lib.py`; covers the lib fixtures, the origins-consumer arm, and every pre-existing arm
- `$PY scripts/test_done_sweep_gates_wrapper.py`; covers the wrapper aggregation arms

- [x] RED: add wrapper arms reflecting the real architecture (gates are in-process helpers returning gate results; a raising helper aborts the run with a traceback and exit 1 today): a clean run emits exit 0 with `OUTCOME: pass`; a gate reporting a modeled violation emits exit 1 with `OUTCOME: fail`; a gate helper that raises is captured as an indeterminate gate result and the run emits exit 2 with `OUTCOME: indeterminate` naming the failed gate; an environment failure emits exit 3 with `OUTCOME: tool_error`; a subprocess child (the plan-readiness validator) exiting outside the 0/1 answer vocabulary maps to indeterminate; run → expect RED [class: REPOSITORY_TEST]
- [x] `DoneSweepGatesLibOutcomeTest#test_origins_consumer_branches_on_outcomes`; given the lib's execute-plan-closeout origins consumer (which today collapses any non-zero origins exit into a refuse), a child origins run reporting indeterminate yields an indeterminate gate result (never a refuse), a tool-error child yields a tool-error result, and a missing final OUTCOME line from a migrated child yields tool error per the contract's no-line rule [class: REPOSITORY_TEST]
- [x] Migrate the wrapper's aggregation to map gate results through the contract (indeterminate dominates fail for the same run per the contract's multi-input rule), add the per-gate exception capture behind the new indeterminate arm, migrate the origins consumer per the fixture above, and keep the lib's internal classification of existing pass and fail cases frozen except the origins-consumer arm this task rewires [class: IMPLEMENTATION_REQUIRED]
- [x] Declare the pair's operating-context assumptions in the register row (Task 4 carries the edit): a readable repository and gate scripts resolvable through the documented resolution order for the wrapper; per-gate assumptions inherited from each child's own row once that child migrates [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the two test files under `$PY` [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate the done-sweep pair to the outcome contract` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Record the batch in the migration register and the caller surfaces

Files:
- `scripts/OUTCOME_CONTRACT.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `test "$(grep -c '| migrated' scripts/OUTCOME_CONTRACT.md)" -eq 6`; covers the five batch rows plus the dirt-gate precedent row carrying the migrated status
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-03-outcome-contract-migration-batch-1.md`; covers the certification gate on the final bytes

- [x] Flip the five batch table rows' Status from queued to migrated (the done-sweep pair is one row across two files), fill each row's Assumptions declared column with the per-script text drafted in Tasks 1 through 3, and extend the compatibility note with the batch-1 entry (the guard-family contract retired on these scripts; their former exit-2 readings are gone; the two declared preservation exceptions named) [class: IMPLEMENTATION_REQUIRED]
- [x] Land the caller-obligation text where the two primary surfaces own it: the done skill's sweep-gate sections and its Step 0 and Step 2 done-lock recipes, and the maintenance landing recipes including the line-87 stranding-report routing (now an explicit four-outcome branch), gain the branch-on-every-outcome rule and the missing-OUTCOME-line rule for these five scripts, and the maintenance survey's origins-corpus consumer is updated for the warn arm's indeterminate flip, without re-litigating the contract's landed convention [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect exit 0: the full Validation Commands block [class: REPOSITORY_TEST]
- [x] Commit: `docs: record outcome-contract batch 1 in the register and caller surfaces` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Six promoted origins, one per migrated script; the outcome contract's register rows flipped queued to migrated by this plan (register complete at 14 migrated with batch-2's eight):

- `docs/history/backlog/2026-10-03-outcome-contract-migration-check-plan-origins-closed.md`: scripts/check_plan_origins_closed.py migrated to the four-outcome contract.
- `docs/history/backlog/2026-10-03-outcome-contract-migration-done-lock.md`: scripts/done-lock.sh migrated.
- `docs/history/backlog/2026-10-03-outcome-contract-migration-done-sweep-gates.md`: scripts/done_sweep_gates.sh migrated.
- `docs/history/backlog/2026-10-03-outcome-contract-migration-done-sweep-gates-lib.md`: scripts/done_sweep_gates_lib.py migrated (its three child arms branch on every outcome).
- `docs/history/backlog/2026-10-03-outcome-contract-migration-landing-parentage-gate.md`: scripts/landing_parentage_gate.py migrated.
- `docs/history/backlog/2026-10-03-outcome-contract-migration-prestage-freshness-gate.md`: scripts/prestage_freshness_gate.py migrated.

Execution evidence docs/reviews/2026-10-03-exec-review-outcome-contract-migration-batch-1-r1.md; all six origins fold-deleted 2026-10-04 in the backlog-root fold pass.
