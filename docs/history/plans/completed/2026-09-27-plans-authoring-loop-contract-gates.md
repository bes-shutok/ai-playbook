# Plan: Plans authoring loop contract gates (review-artifact name binding + replacement-span boundary rule)

Backlog origins (scope of record):
- docs/history/backlog/2026-09-18-plans-quality-gate-review-artifact-name-check.md
- docs/history/backlog/2026-09-18-plans-replacement-span-boundary-must-name-its-tail.md

Driving force: efficiency + code-quality

## Outcome

Close the two authoring-loop contract gaps so every staged review round is discoverable by the readiness gate and no replacement prescription can silently drop tail text.

- A per-round probe re-verifies each review artifact pair against the readiness gate's discovery shape (filename glob, sidecar presence, sidecar `artifact_slug`, coverage self-references) before the loop folds findings or relaunches, so a misnamed round is caught in the round that wrote it instead of at the done boundary.
- The orchestrator template, the reviewer skill, and the staging naming rules pin the same feature-slug semantics, so producer, orchestrator, and gate cannot diverge.
- A new plans authoring rule forces every replacement prescription to bound its quoted span at a sentence terminator or name the exact surviving tail, with a contiguous fixed-string validation pin that proves the boundary.

## Terms

- feature slug: the plan filename stem with its leading `YYYY-MM-DD-` prefix stripped; derived by `feature_slug()` in scripts/plan_readiness.py and consumed by the readiness gate's discovery glob.
- discovery shape: the filename form `*-plan-review-<feature-slug>-r<N>.md` (N >= 1) that `latest_review_round()` globs under the configured reviews directory.
- name binding check: the new `--check-review-name` probe mode of scripts/plan_readiness.py.
- coverage self-references: the sidecar `coverage.attempts[].artifact` and `.sidecar` values, the `coverage.inherited_coverage[].artifact` and `.sidecar` values, and the `coverage.replacement[].original_artifact` and `.original_sidecar` values; they embed review artifact filenames and dangle when a pair is renamed.
- replacement span and tail: the quoted text a task prescribes to replace, and the exact text that follows it inside the same sentence or bullet.

## Assumptions

- assume the binding slug semantics is the readiness validator's `feature_slug` (plan filename stem minus its leading date prefix); basis: `feature_slug()` and the `latest_review_round` glob in scripts/plan_readiness.py.
- assume the probe extends scripts/plan_readiness.py (no new file) reusing `feature_slug` and the validate_review_staging helpers already imported there as `vrs`; basis: origin item 1 names exactly these candidate shapes and the `vrs` import exists in scripts/plan_readiness.py.
- assume the archived witness plan docs/history/plans/completed/2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording.md already carries the corrected replacement boundary in its Task 2 prescription (the quoted span now ends at "consult the State file semantics" and the following sentence is named as the verbatim keep; the r5 tail string " and re-arm per the runtime overlay" appears nowhere in the archived bytes), so origin item 2's "fix it when the plan is next touched" clause is discharged as closed-by-prevention and no archived byte is edited; basis: grep over the archived bytes at authoring time (2026-09-27, main b3971208).
- assume prescribed insertions into agents/skills/plans/SKILL.md stay inside the shared-body forbidden-term allowance, and the Validation Commands run that gate; basis: the shared-file set and term tuple of `test_shared_skill_bodies_remain_runtime_neutral` in scripts/test_execute_plan_runtime.py.
- assume probe invocations run from the repository root against the repo-local validator (deployed home copies are symlinks to this repo), mirroring the plans skill rule 29 pre-round invocation shape; basis: plans SKILL.md rule 29.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: review rounds become gate-visible by construction and replacement prescriptions must name their tails, because two witnessed defect classes kept burning done-boundary recovery and review-churn work. Driving force: efficiency + code-quality.

Today nothing re-verifies a round's filename after the round writes it. The sub-agent prompt template prescribes `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md` while the gate derives its glob slug from the plan's full stem minus the date prefix. A run whose round prompts pin a shorter name (origin item 1, second witness) stages rounds the gate cannot see, and the first failure surfaces at the done boundary as `no review artifact for feature slug`, forcing a multi-file rename plus sidecar self-reference patching, because coverage attempts and inherited-coverage links embed the artifact filename. After this plan the round pair is probed in the round that wrote it. Example: plan `2026-09-01-fixture-feature.md` with a round staged as `2026-09-01-plan-review-fixture-r1.md` fails the probe immediately with the expected slug `fixture-feature` named; the correctly named `2026-09-01-plan-review-fixture-feature-r1.md` pair passes; a renamed pair whose sidecar still links an old `inherited_coverage` artifact path fails naming the missing file.

For the boundary rule: a task saying "replace `keep the listing inverted` with `consult the state file first`" inside the sentence "keep the listing inverted and re-arm only when dark" leaves ` and re-arm only when dark` outside both the replaced span and any verbatim guarantee, so a literal reading drops the re-arm clause. Rule 40 forces either quoting through the sentence terminator or pinning the full pre-replacement sentence (span plus tail) as one contiguous fixed string in validation, making the boundary reading gate-enforced instead of reviewer-inferred. Standing witness: origin item 2, three consecutive review rounds staging the same defect class with one boundary flavor per round (prefix of a longer sentence; replacement duplicating the continuation; mid-sentence tail drop).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the probe reuses (never duplicates) the gate's own slug derivation and discovery shape, with RED canaries for both witnessed defect classes plus sidecar-slug mismatch and mode misuse
- correctness: every prescribed skill-file edit itself satisfies the new rule 40 (sentence-terminator boundary or named verbatim tail), so the plan obeys the rule it adds
- simplicity: one CLI mode, one authoring rule, six prose edits across three skill files; no new files; no staging schema changes
- maintainability: the binding rule prose is single-sourced in the plans skill's Plan Quality Gate; the derivation definition is restated only inside the three naming anchors (the plans gate's sub-agent prompt template line, review-plan Step 4, and the review-staging naming rule), everything else points

**Done when:**
- `python3 scripts/test_plan_readiness.py` passes including the new `ReviewNameCheckTest` class, and `python3 scripts/plan_readiness.py --selftest` passes
- the shared-body gate passes: `python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral`
- `bash scripts/check-no-em-dash.sh file` over the five touched paths exits 0, and `bash scripts/scan-public-hygiene.sh` exits 0
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-27-plans-authoring-loop-contract-gates.md` reports no structural failure
- the probe demonstrates all four behavior arms against a throwaway fixture directory: canonical pair rc 0; short-slug pair rc 1 naming the slug; dangling coverage self-reference rc 1 naming the path; mode combination rc 2

**Ship when:** consumer projects pick the changed skills up through their existing vendored-sync and deployed-home symlink paths (prose only; no release action exists in this repository). The per-round probe requires a same-sync `plan_readiness.py`: non-symlink deployed copies must sync the script together with the skills, and symlinked deployments inherit the landing automatically.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`

**Tests:**
- `scripts/test_plan_readiness.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reason: staging schema and its coverage existence checks are unchanged, the probe consumes its helpers read-only (a finding here is plan-related only when probe reuse breaks its behavior)
- `docs/history/plans/completed/2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording.md`; reason: archived plan bytes are immutable and the r5 boundary was already folded correct before archival (see Assumptions)
- `agents/skills/review-agents/**`; reason: neither origin item requires catalog or lens changes
- `agents/skills/execute-plan/**`; reason: execution-side gates consume the same validator unchanged

## Validation Commands

Authoring-time gate record (2026-09-27, worktree at main b3971208): em-dash scan over the five touched paths exits 0 today; hygiene scan exits 0 today; pre-round structural gate reports PRE-ROUND OK (structural checks clean, review record not consulted) over these exact bytes, recorded 2026-09-27 before review round 1.
Execution-time gate record (2026-09-27, execution worktree branch 2026-09-27-execute-plans-authoring-loop-contract-gates): the whole Validation Commands block ran GREEN after Tasks 1 through 5; pre-round structural gate again reports PRE-ROUND OK (outcome class: structural-clean, review record not consulted); all three test/selftest gates exit 0 (16 tests OK, selftest ALL PASS, shared-body gate OK).

```bash
# Run from the repository root. Every command fails loudly on a miss.
python3 scripts/test_plan_readiness.py -v
python3 scripts/plan_readiness.py --selftest
python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral
bash scripts/check-no-em-dash.sh file agents/skills/plans/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/review-staging/SKILL.md scripts/plan_readiness.py scripts/test_plan_readiness.py
bash scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-27-plans-authoring-loop-contract-gates.md
```

### Task 1: Probe mode `--check-review-name` in the readiness validator (RED first)

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

- [x] `ReviewNameCheckTest#test_accepts_canonical_pair`; given plan `2026-09-01-fixture-feature.md` and round pair `2026-09-01-plan-review-fixture-feature-r1.md` plus a sidecar JSON object declaring `"artifact_slug": "fixture-feature"` under a temp reviews directory, expects `main([plan_arg, "--check-review-name", round_arg])` to return 0 and stdout to contain `review name check OK` [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_short_slug`; given the same plan with a round staged as `2026-09-01-plan-review-fixture-r1.md`, expects return code 1 and the failure reason to name the expected slug `fixture-feature` and the discovery shape (second witnessed defect class: short slug in the round prompt) [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_missing_sidecar`; given a canonical round Markdown with no `.stats.json` beside it, expects return code 1 with a reason containing `missing stats sidecar` [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_sidecar_slug_mismatch`; given a canonical pair whose sidecar declares `"artifact_slug": "fixture"`, expects return code 1 naming the slug mismatch [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_dangling_inherited_coverage`; given a canonical pair whose sidecar carries `coverage.inherited_coverage[0].artifact` pointing at an absent file, expects return code 1 naming the dangling path (rename-orphan hazard from origin item 1) [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_dangling_attempt_reference`; given a canonical pair whose sidecar carries `coverage.attempts[0].artifact` pointing at an absent file, expects return code 1 naming the dangling path [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_dangling_replacement_reference`; given a canonical pair whose sidecar carries `coverage.replacement[0].original_artifact` pointing at an absent file, expects return code 1 naming the dangling path (third witnessed link kind) [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_corrupt_sidecar`; given a canonical round whose `.stats.json` is unparseable JSON, expects return code 1 with a reason containing `malformed stats sidecar` and no traceback [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_rejects_round_outside_reviews_dir`; given the canonical pair staged under a directory that is not the configured reviews directory, expects return code 1 naming the parent-directory requirement [class: REPOSITORY_TEST]
- [x] `ReviewNameCheckTest#test_mode_combination_is_usage_error`; parametrized over `--selftest`, `--sweep`, and `--pre-round`, given `--check-review-name` combined with each excluded flag in turn, expects exit code 2 through `parser.error` for every combination [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_plan_readiness.py ReviewNameCheckTest` exits non-zero (the `--check-review-name` flag does not exist yet, so every arm errors or fails) while the existing `ScopeClassificationPlacementTest` and `PlanReadinessFenceBalanceTest` classes stay green [class: REPOSITORY_TEST]
- [x] Implement in scripts/plan_readiness.py: add argument `--check-review-name` taking the round Markdown path (metavar `ROUND_MD`); add parse-time mutual exclusion against `--selftest`, `--sweep`, and `--pre-round` through `parser.error` (exit 2, same pattern as the existing `--pre-round` exclusions); require `plan_path` when the mode is set (`parser.error` otherwise); add a `check_review_name(plan_path, round_md, reviews_dir)` helper returning success or a reason, which: derives the slug via the existing `feature_slug`, requires the round file's parent directory to be the configured reviews directory, fullmatches the round filename against the discovery shape through ONE shared shape source, a module-level helper or constant that BOTH `latest_review_round`'s glob and the probe's fullmatch consume so the shape exists in a single encoding and cannot drift (the slug is escaped inside that shared helper), requires the sidecar via the existing `vrs.stats_sidecar_path` (reason mirrors the gate's `missing stats sidecar` wording), parses it as a JSON object (a parse failure or non-object prints `review name check FAILED: malformed stats sidecar ...` mirroring the gate's own classification, never a traceback), requires `artifact_slug == slug`, and when a `coverage` object is present requires every non-empty `attempts[]` entry `artifact`/`sidecar` value, every `inherited_coverage[]` entry `artifact`/`sidecar` value, and every `replacement[]` entry `original_artifact`/`original_sidecar` value to pass the existing `vrs._coverage_artifact_exists`, naming the dangling path and the entry in the reason; main dispatch prints `review name check OK: <round filename> binds plan slug <slug> (r<N>)` and returns 0 on success, prints `review name check FAILED: <reason>` and returns 1 on any failure; the probe parses only the fields it checks and never runs staging schema validation (that stays `validate_review_staging.py --hard`'s duty); the reviews directory resolves exactly as the existing modes resolve it [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_plan_readiness.py` exits 0 (whole file; no existing class regressed) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: plan_readiness --check-review-name probe binds rounds to gate discovery` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Plans skill Plan Quality Gate: pin the template slug and add the per-round check

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the `Sub-agent prompt template` block, replace the line `Write the review output to: `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md`` with `Write the review output to: `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md`, where `<feature-name>` is exactly the plan filename stem with its leading `YYYY-MM-DD-` prefix stripped (the readiness gate's feature slug; the gate discovers rounds only through the glob `*-plan-review-<feature-name>-r*.md`, so a shortened or otherwise adjusted slug is invisible to it and surfaces at the done boundary as "no review artifact for feature slug").`; the template's following line, exactly `(use `-r1`, `-r2`, … for each loop iteration)`, stays verbatim byte-for-byte [class: IMPLEMENTATION_REQUIRED]
- [x] Immediately after that same template block's closing fence and before the `**Review severity:**` line, insert this exact paragraph (the `**Review severity:**` line and everything after it stay verbatim): [class: IMPLEMENTATION_REQUIRED]

````markdown
**Per-round name binding check (run after every round, before folding or relaunching):** as soon as a round's artifact pair exists under `{reviews_dir}`, run the readiness validator's name-shape probe and require exit 0 before folding that round's findings or launching the next round (same repository-root invocation shape as the rule 29 pre-round gate):

```bash
python3 scripts/plan_readiness.py <plan-path> --check-review-name {reviews_dir}/<round-filename>.md
```

The probe re-derives the feature slug from the plan stem with the readiness gate's own derivation, so the check and the done-boundary discovery cannot diverge. It fails loudly when the round filename does not match the gate's discovery glob, when the sidecar is missing or its `artifact_slug` differs, or when the sidecar's coverage self-references (`coverage.attempts[].artifact`/`sidecar`, `coverage.inherited_coverage[].artifact`/`sidecar`, `coverage.replacement[].original_artifact`/`original_sidecar`) name files that do not exist. Fix a failure inside the same round: rename the pair to the canonical shape and patch the sidecar self-references in one pass; never fold findings, launch the next round, or finalize while the probe fails. (Witnesses: two authoring runs reached the done boundary with rounds invisible to the gate and recovered only by renaming six files and patching sidecar references, 2026-09-18 and 2026-09-20.)
````

- [x] Commit: `feat: plans gate pins review-artifact slug and probes it per round` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Review-plan skill: bind the Step 4 filename to the gate's slug

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] In `## Step 4: Output`, replace the parenthetical `(read `{reviews_dir}` from `.ai-playbook/facts.md` TOML; use `-r1`, `-r2`, … per loop iteration)` with `(read `{reviews_dir}` from `.ai-playbook/facts.md` TOML; use `-r1`, `-r2`, … per loop iteration; `<feature-name>` is the plan filename stem minus its leading `YYYY-MM-DD-` prefix, exactly the readiness gate's feature slug, so every round you write matches the gate's `*-plan-review-<feature-name>-r*.md` discovery glob)`; everything in that paragraph from the sentence period onward (`. Follow the staged hierarchy` and later bytes) stays verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] In `## Integration Points`, at the end of the `### With the plan readiness gate (`scripts/plan_readiness.py`)` section, append exactly one sentence after the section's existing final sentence: `The Step 4 filenames are bound to that same discovery shape by construction, and the plans skill's Plan Quality Gate re-verifies every written round pair against it with the `--check-review-name` probe after each round.` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review-plan binds Step 4 staging names to the readiness slug` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Review-staging skill: bind the plan-source artifact slug

Files:
- `agents/skills/review-staging/SKILL.md`

- [x] In `## File naming rules`, replace the bullet `- `<artifact-slug>` is the caller-provided slug` with `- `<artifact-slug>` is the caller-provided slug; when the reviewed source is a plan, it MUST be the plan's readiness-gate feature slug (the plan filename stem minus its leading `YYYY-MM-DD-` prefix) so the round stays discoverable through the readiness validator's `*-plan-review-<feature-slug>-r*.md` glob, which the plans skill's per-round name binding check enforces after every round`; the following bullet, exactly `- `<mode_or_round>` must be stable and specific enough to avoid collisions in the same day, for example `light`, `full`, `review-local`, `r1``, stays verbatim byte-for-byte [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review-staging pins plan-source artifact slug to the readiness gate` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Plans skill authoring rule 40: replacement-span boundary (name the tail)

Files:
- `agents/skills/plans/SKILL.md`

- [x] In `## Validation Commands (authoring rules)`, insert rule 40 between rule 39 (the line beginning `39. **Pins over live sources carry derivation provenance:**`) and the `## Budget gate (plan-authoring pause and resume)` heading; the rule 39 line and the Budget gate heading both stay verbatim; exact rule text: [class: IMPLEMENTATION_REQUIRED]

```markdown
40. **Replacement-span boundary rule (name the tail, guarantee its survival):** when a task prescribes replacing a quoted span inside a live sentence or bullet, the prescription must either quote the span ending at a sentence terminator, or name the exact tail text that follows the quoted span and assert verbatim that the tail survives the replacement; a replacement text that duplicates or paraphrases the quoted span's continuation clauses is invalid, and a mid-sentence boundary that leaves tail bytes outside both the replaced span and the verbatim guarantee lets a literal reading silently drop real content (standing witness: origin item docs/history/backlog/2026-09-18-plans-replacement-span-boundary-must-name-its-tail.md, three consecutive review rounds staging the same defect class with one boundary flavor per round: prefix of a longer sentence, replacement duplicating the continuation, mid-sentence tail drop). The mechanically enforceable pattern: the task's validation lines pin the pre-replacement span and its tail as ONE contiguous fixed string against the target file, so the boundary reading is forced by the gate instead of reviewer inference, and the pin executes RED-today at authoring per rule 19.
```

- [x] Commit: `feat: plans rule 40 forces replacement prescriptions to name their tails` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items (fold-then-delete, closed at landing)

Both origins delivered-closed by the tasks above; per-item backlog files deleted, no per-item archives.

- `2026-09-18-plans-quality-gate-review-artifact-name-check.md`: CLOSED by Tasks 1-4. The `--check-review-name` probe in scripts/plan_readiness.py re-verifies every written round pair against the gate's own discovery shape and coverage self-references; the plans Plan Quality Gate runs it per round, and the review-plan Step 4 and review-staging naming anchors pin the same feature-slug semantics, so producer, orchestrator, and gate cannot diverge. Review r1's symlink-identity finding was fixed (lexical claimed-path checks) and re-certified r2 ready=yes; the residual round-number shape divergence is filed as docs/history/backlog/2026-09-27-review-name-probe-round-number-shape-divergence.md.
- `2026-09-18-plans-replacement-span-boundary-must-name-its-tail.md`: CLOSED by Task 5. Plans authoring rule 40 forces every replacement prescription to bound its quoted span at a sentence terminator or name the exact surviving tail, with the mechanically enforceable contiguous fixed-string pin pattern; the archived witness plan docs/history/plans/completed/2026-09-18-maintenance-loop-residuals-occupancy-anchors-rearm-wording.md was already correct before archival (closed-by-prevention per Assumptions, no archived byte edited).

Execution record: executed 2026-09-27 in worktree branch `2026-09-27-execute-plans-authoring-loop-contract-gates` off main 486d630d (plan digest b01a75cd, r4 ready=yes zero blocking carried the Step 0.5 gate). Tasks 1-6 committed with the prescribed messages; full Validation Commands block green post-implementation (18 readiness tests OK including 12 ReviewNameCheckTest arms, selftest ALL PASS, shared-body gate OK, em-dash scan rc 0, hygiene scan rc 0, pre-round PRE-ROUND OK); mechanical pin/text audit 11/11 and rule 40 self-audit recorded; execution review r1 staged ready=yes with one Medium (symlink identity false-OK, fixed in 68ec20fb) and two Lows (F2 backlogged, F3 test witness added), focused re-cert r2 ready=yes zero blocking with one Low comment fix folded (fdf7bd35).
