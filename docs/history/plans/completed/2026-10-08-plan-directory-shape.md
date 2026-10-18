# Plan: plans-as-directory shape (charter plus one file per task)

Backlog origin: docs/history/backlog/2026-10-05-plan-directory-shape.md
Driving force: efficiency (primary) + code quality (secondary); reliability justification: the extraction-fluke class this shape eliminates is a witnessed correctness harm (hand-pinned cuts drifting around pinned offsets; the U1 investigation record), so the work is implemented for reliability despite it not being one of the four driving principles; park triage: not applicable, the origin row is an operator-directed design direction, not a parked row
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-plan-directory-shape-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 5.0h total, largest task 1.5h

## Terms

- Plan directory shape: a plan stored as a directory under the plans root whose charter file `PLAN.md` carries the shared sections (metadata block, Terms, Why, Outcome, Assumptions, Gist & Examples, Evaluation Criteria, Review Scope, Validation Commands) and whose `tasks/` subdirectory carries exactly one Markdown file per task, each holding that task's `### Task N:` section, `Files:` list, Evidence bullets, and acceptance checkboxes; the directory name is the plan slug (`YYYY-MM-DD-<slug>/`).
- Single-file shape: today's plan storage, one `<name>.md` file at the plans root; it stays fully supported and behavior-identical (dual format, migrate on touch; no bulk migration of existing plans).
- Manifest digest: the directory form's `source_digest` payload: sha256 over the sorted `relpath<NUL>sha256(file-bytes)<LF>` lines of the charter plus every task file, order-independent and file-boundary-verbose; the single-file form's digest payload stays the plan file's raw bytes so existing sidecars verify unchanged.
- Shape resolver: the new shared helper `scripts/plan_shape.py` whose `resolve_plan_operand(path)` returns one resolved shape (operand kind, charter text, sorted task-file list with relative paths, digest payload bytes, slug) or a named refusal; the one grammar derivation every consumer imports, mirroring the shared-matcher precedent so no consumer re-derives the grammar.
- Directory egress: a plans-root egress whose source is a plan directory; git reports it as N per-file name-status rows under one `<plans-root>/<slug>/` prefix (git tracks files, never directories), so the guard aggregates those rows into one egress keyed on the directory slug before the evidence legs run.
- Prune witness: the PLAN-PROMPTS prune rule's existence test for a landed plan, implemented in `witness_candidates` in scripts/check_prompt_log_origins.py as a git ls-tree path-depth grammar (exactly 4 path parts at the plans root, 5 under completed/); under the directory shape the grammar accepts the charter path `<slug>/PLAN.md` and the completed twin `<slug>/PLAN.md` beside the file forms.
- Checkbox-flip proof: the delta classifier's exempt verdict for a delta whose only changed lines are task-checkbox flips; under the directory shape a flip touches exactly one `tasks/` file, and the per-file loop with path-named hunk headers lives in the classifier's CLI layer over the resolver's file list.
- Migrate on touch: the storage convention that a plan adopts the directory shape when a substantial edit reopens it, never as a bulk sweep; existing plans keep their landed single-file bytes.
- Worker read contract: the landed U1 contract (whole-file reads, declared context surface); under the directory shape the execution driver assembles each worker payload from the charter plus exactly that worker's one task file, eliminating span extraction for directory plans.

## Why

Every curated worker read from a single-file plan is an extraction, and every extraction scheme carries a residual fluke class: the cut is only as good as the tool and the moment it ran. The repo already proved the durable alternative for skills, a phase-spine file plus whole-file module companions (agents/skills/execute-plan/runtime-contract.md and siblings). Giving plans the same shape makes the worker read whole-file by construction, scopes checkbox flips to one small file, and gives the digest machinery a manifest form. The origin sequences this after U1 (read contract) and U3 (sizing), both landed (completed/ twins witnessed at docs/history/plans/completed/2026-10-05-plan-worker-read-contract.md and 2026-10-05-plan-sizing-execution-budget.md), so the read surface and the seam rule this shape serves already exist.

## Outcome

A plan may be a directory (charter `PLAN.md` plus `tasks/NN-<name>.md` per task); the digest becomes a manifest hash; plan_readiness, the review-staging validator's source-plan verification, the delta classifier, the origins checker, the reverse-squash guard with its done-library archive twin, the execution driver's plan read/seed/digest surface, the authoring liveness probe, and the prune witnesses accept the directory shape beside the single-file shape; workers read the charter plus their one task file whole; single-file plans behave exactly as today.

Gate delta: one new shared helper module, dual-shape operand acceptance in eight scripts and three skill/wording surfaces, per-file classification and evidence inside existing verdict vocabularies, and named refusal arms for malformed directories; no new refusal class over correctly-shaped plans (the one deliberate divergence, the directory ordinal grammar, is recorded in the edge cases), no schema state field, no protocol layer, and no behavior change for single-file plans.

## Assumptions

- assume the shared resolver is the single grammar derivation and every consumer imports it; basis: the anti-duplication rule and the shared-matcher precedent; a per-consumer re-derivation would reopen the drift class this plan closes.
- assume the manifest digest is a new canonical serialization, not a concatenation of raw bytes, so the digest is order-independent and file-boundary-verbose; basis: the sorted-manifest Expected sentence in the origin row; the single-file digest bytes stay raw so existing sidecars verify unchanged.
- assume the digest swap has exactly two production sites, plan_readiness.py's compute call and validate_review_staging.py's `--source-plan` verification routing (whose operand gate is `source_path.is_file()` then `read_bytes()` today, so a directory operand reads as a tool error), plus the execution driver's closeout receipt re-hash; basis: the r1 panel's consumer sweep (worker B findings 2 and 3) over scripts/validate_review_staging.py and scripts/execute_plan_runtime.py.
- assume Tasks 2, 3, and 4 strictly follow Task 1 (header-declared execution dependency) because all three import the resolver; Tasks 2, 3, and 4 are mutually independent after Task 1 and may run in any order; basis: the seam rule, a shared-file set is never cut by a parallel boundary; the four tasks share no production file with each other beyond that dependency.
- assume the charter filename is exactly `PLAN.md` and task files sort lexicographically under `tasks/` with the `### Task N:` heading inside each file; basis: the origin row's Expected paragraph (charter `PLAN.md` carrying Terms, Outcome, Why, Review Scope, and Validation Commands; one file per task under `tasks/`).
- assume fence-balance and section validation run per file (charter and each task file) with file-named errors, because a per-file scan localizes the cut-drift class the shape eliminates; basis: the readiness gate's existing fence scanner operating on one text today.
- assume the budget gate, certification oracle, readiness prerequisite, and archive-ceremony evidence schema keep their semantics, reading charter-plus-tasks as the plan's bytes; basis: the origin's dual-acceptance Expected line and the reverse-squash guard's existing evidence schema, whose docstring binds the check-archive schema to the done library's archive-ceremony twin so both named sites change together.
- assume the liveness probe discovers an untracked plans-root directory from the git untracked enumeration it already runs (scripts/check_authoring_plans_liveness.py `enumerate_candidates`, whose untracked-file listing today drops every file of a directory plan because the candidate filter rejects paths whose dirname is not the plans root), by deriving directory candidates from untracked `PLAN.md` paths under the plans root and expanding them; a charterless untracked directory is reported stranded with that named reason; basis: the r1 panel's enumeration experiment (worker B finding 12) and the probe's live/stranded contract.
- assume the directory ordinal grammar refuses a missing `### Task N:` ordinal and refuses two task files claiming the same ordinal, while the single-file form keeps its position-identity acceptance of repeated ordinals in one document; this is the one deliberate divergence between shapes and it is recorded in the edge cases rather than unified; basis: worker B finding 11 and the file-per-task mapping semantics (two files claiming Task N is a real file-identity ambiguity, unlike two sections in one document).
- assume anchors re-derive from live bytes at execution and a moved anchor re-keys its pin in the same edit; basis: the standing-constraints rule and the concurrent-peer reality of this checkout.
- assume authoring runs under the standing D-4 authoring directive plus the live operator directive to author the most urgent untaken issue, so the plans skill's Phase 1 confirmation is satisfied by the frozen entry's validated record; basis: the frozen PLAN-PROMPTS entry `execution-pipeline-friction` unit U4 and the operator's live message.

Decision points requiring a grill: none remain (the frozen entry's prompt is the validated requirements record; the r1 panel's findings are folded into the assumptions and tasks above).

## Gist & Examples

TLDR: a plan can be a directory whose workers read the charter plus one whole task file, and every plan consumer accepts both shapes (efficiency, with a witnessed reliability harm closed by construction).

Before (today): a worker's context is extracted from one big plan file; the extraction carries the cut-drift fluke class; checkbox flips rewrite one large file so the classifier's flip proof scans a blob; the digest binds to one blob; the execution driver refuses any non-regular plan operand.

After (this plan): `docs/history/plans/2026-10-08-<slug>/PLAN.md` plus `tasks/01-<name>.md`; the driver assembles each worker payload from the charter plus its one task file; a checkbox flip touches one small task file; the digest is a manifest hash verified by the same sidecar contract; readiness, validator, classifier, origins checker, guard with its done twin, driver, liveness probe, and prune witnesses accept both shapes; single-file plans are untouched.

Edge cases pinned: a directory without `PLAN.md` refuses with a named error naming the operand path; a directory with an empty `tasks/` refuses (a plan has tasks); a directory whose task files disagree with the charter's `### Task N:` ordinals refuses, naming the duplicated or missing ordinals (the deliberate divergence from the single-file position-identity semantics is recorded here); a file operand resolves exactly as today (existing suites green unmodified); a directory plan whose charter carries `## Review Scope` and `## Validation Commands` passes readiness with sections read from the charter and tasks from `tasks/`; the manifest digest is stable under file reordering and sensitive to any file-byte change; the prune witness accepts `<slug>/PLAN.md` at the same plans-root depth the file form occupies; an egress ack names the directory path and refuses a path that is not the egress; a directory egress aggregates N per-file rows into one finding, not N findings.

## Evaluation Criteria

**Quality dimensions:**
- Every consumer imports the resolver; no consumer re-derives the directory grammar (grep: no second `PLAN.md` literal outside the helper and its tests and the documented contract text).
- Single-file behavior is identical: every existing suite passes unmodified or with additive fixtures only.
- Every new refusal arm names the defect and the operand path (no bare tracebacks, no silent skips).
- The manifest digest is pinned by fixtures for ordering stability and boundary sensitivity.
- Skill text and pin updates land in the same edit as the spans they reword.

**Done when:**
- All four tasks' acceptance boxes are checked with their suites green; plan_readiness certifies these bytes; the touched skill spans and pins agree (pins suite exit 0).

**Ship when:**
- Done when holds and the landing closeout gates pass (claims, staging, reverse-squash, hygiene, em-dash added-lines over the branch delta).

## Review Scope

Production:
- scripts/plan_shape.py *(new)*
- scripts/plan_readiness.py
- scripts/validate_review_staging.py (the `--source-plan` operand gate and digest verification routing only)
- scripts/plan_delta_classifier.py
- scripts/check_plan_origins_closed.py
- scripts/reverse_squash_guard.py
- scripts/done_sweep_gates_lib.py (the archive-ceremony twin section only)
- scripts/execute_plan_runtime.py (the plan read gate, task parsing, and closeout receipt digest surfaces only)
- scripts/execute_plan_resume_watcher.py (plan operand passthrough only)
- scripts/check_authoring_plans_liveness.py
- scripts/check_prompt_log_origins.py
- scripts/plan_task_span.py
- agents/skills/plans/SKILL.md (Plan Format region, rule 9 digest verification wording, and any pin-keyed span)
- agents/skills/execute-plan/SKILL.md (Prerequisite paragraph, plan-path heuristic, seven-file copy remedy inventory sentence)
- agents/skills/maintenance/SKILL.md (the plan-file-existence predicate spans only)
- docs/history/backlog/PLAN-PROMPTS.md (prune-rule standing text only; the frozen entries are untouched)
- scripts/check_maintenance_pins.sh (same-edit pin re-keying only)
- scripts/runtime-scripts.list (the new helper module's deployment row)

Tests:
- scripts/test_plan_shape.py *(new)*
- scripts/test_plan_readiness.py
- scripts/test_plan_delta_classifier.py
- scripts/test_check_plan_origins_closed.py
- scripts/test_reverse_squash_guard.py
- scripts/test_execute_plan_runtime.py (additive directory-form tests inside the existing suite file)
- scripts/test_execute_plan_resume_watcher.py
- scripts/test_check_prompt_log_origins.py
- scripts/test_authoring_plans_liveness.py
- scripts/test_plan_task_span.py

## Validation Commands

- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_shape.py scripts/test_plan_readiness.py scripts/test_plan_delta_classifier.py scripts/test_check_plan_origins_closed.py scripts/test_reverse_squash_guard.py scripts/test_check_prompt_log_origins.py scripts/test_authoring_plans_liveness.py scripts/test_plan_task_span.py scripts/test_execute_plan_runtime.py scripts/test_execute_plan_resume_watcher.py -q` (bare `python3 -m pytest` off-venv fails rc 1 with a pytest import error, per the landed plans' runner note)
- bash scripts/check_maintenance_pins.sh
- bash scripts/check-no-em-dash.sh added-lines --base main
- bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
- python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-08-plan-directory-shape.md

## Standing constraints

(origin docs/history/backlog/2026-10-05-plan-directory-shape.md carries no restriction beyond its sequencing precondition, satisfied: the U1 read-contract and U3 sizing plans are landed completed/ twins)

- Re-derive every anchor from live bytes before editing; a moved anchor re-keys its naming pin in scripts/check_maintenance_pins.sh in the same edit.
- No `Co-Authored-By:` trailers, no `--no-verify`, never stage gitignored files; landing commits use explicit pathspecs.
- The hygiene scan (exit 0) gates every commit; the em-dash added-lines scan gates plan and skill text edits (scanner: bash scripts/check-no-em-dash.sh added-lines).
- The frozen PLAN-PROMPTS entry is untouched by execution; the standing-rules wording edits in Task 4 are the prune-rule line and its predicate spans only.
- Per-task fixtures land beside the mechanism in the same task; the two-round alarm and seam rule govern any split question (the shared resolver keeps Tasks 2-4 strictly sequenced behind Task 1).
- The house section order used by this plan and the certified precedent (Gist & Examples after Assumptions) is the accepted deviation from the template's Gist-after-Why placement; adjudicated at r1, not a defect to re-litigate.

### Task 1: the shape resolver, readiness and validator acceptance, and the charter template (TDD)

Files:
- `scripts/plan_shape.py` *(new)*: `resolve_plan_operand(path)` with the named refusal arms (charterless directory, empty tasks/, unreadable operand), the canonical manifest-digest serialization, and the slug derivation for both shapes
- `scripts/test_plan_shape.py` *(new)*: fixtures for the well-formed directory plan, charterless directory, empty tasks/, ordinal collision between charter and task files, ordering-stability and boundary-sensitivity digest pins, file-operand passthrough
- `scripts/plan_readiness.py`: operand resolution through the helper; charter/tasks section assembly for the directory form (Review Scope and Validation Commands from the charter, `### Task N:` sections from the sorted task files); slug from the directory name; per-file fence scanning with file-named errors; the digest call site swaps the payload bytes for the manifest digest while the `source_digest` contract keeps its shape; the readiness prerequisite and pre-round paths accept both forms; the directory ordinal grammar (missing ordinal refuses; duplicate ordinal across task files refuses) beside the unchanged single-file position semantics
- `scripts/test_plan_readiness.py`: additive directory-form fixtures; the full readiness pass over a directory fixture; the byte-identical single-file pin
- `scripts/validate_review_staging.py`: the `--source-plan` routing resolves the operand through the helper before the `is_file()` gate so a directory verifies against the manifest digest and a missing operand still fails as the tool error (anchor: the source-plan freshness verifier around lines 17958-17984 and its gate at the `source_path.is_file()` check)
- `agents/skills/plans/SKILL.md`: the `## Plan Format` region gains the directory charter shape (charter sections, one file per task under `tasks/`, the worker read contract sentence, migrate-on-touch; no bulk-migration instruction); rule 9's `shasum -a 256 <plan-file>` digest-verification wording gains the manifest form for directory plans
- `scripts/runtime-scripts.list`: the deployment row for the new helper module
- `scripts/check_maintenance_pins.sh`: same-edit re-keying of any pin naming a reworded plans-skill span

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_readiness.py -q` passes today (the single-file baseline this task must keep green)
- python3 scripts/plan_readiness.py docs/history/plans/completed/2026-10-05-plan-sizing-execution-budget.md exits 0 today (the certification-oracle baseline; worktree precondition: the full-gate oracle and Done-when certification need the gitignored `{reviews_dir}` provisioned into a fresh authoring worktree first, the standing fresh-worktree provisioning duty, since a missing reviews dir fails the gate as a configured-path error before any plan byte is read)

- [x] Re-derive the anchors from live bytes: plan_readiness.py `main` plan_path operand, the `vrs.compute_source_digest("plan", plan_bytes)` production call site, `feature_slug`'s stem derivation, validate_review_staging.py's `--source-plan` routing and its `source_path.is_file()` gate, plans SKILL.md `## Plan Format` and rule 9, runtime-scripts.list rows, and whether any pin keys a span this task rewords; a moved anchor re-keys its pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] `test_resolve_directory_operand`; given a well-formed directory fixture, returns the charter text, the sorted task-file list with relative paths, and the directory slug [class: REPOSITORY_TEST]
- [x] `test_resolve_refusal_arms`; given a charterless directory, an empty tasks/ directory, and a nonexistent path, each refusal names the defect and the operand path with no traceback [class: REPOSITORY_TEST]
- [x] `test_manifest_digest_ordering_and_boundary`; the digest is identical when task files are renamed to reorder them lexicographically with content fixed, and changes when any file's bytes change [class: REPOSITORY_TEST]
- [x] `test_file_operand_passthrough`; a single-file operand returns the raw bytes digest and the file text, matching today's values exactly [class: REPOSITORY_TEST]
- [x] `test_readiness_directory_end_to_end`; plan_readiness passes a well-formed directory fixture (sections from charter, tasks from files, slug from directory name, per-file fence scanning, manifest digest) [class: REPOSITORY_TEST]
- [x] `test_readiness_directory_ordinal_grammar`; a task file missing its charter ordinal refuses; two task files claiming the same ordinal refuse naming both files; the single-file repeated-ordinal acceptance is unchanged [class: REPOSITORY_TEST]
- [x] `test_readiness_single_file_unchanged`; the existing single-file suite passes unmodified and a byte-identical-output pin over one landed plan holds [class: REPOSITORY_TEST]
- [x] `test_validator_source_plan_directory`; the `--source-plan` verification accepts a directory operand against the manifest digest and still reports the tool error for a missing operand [class: REPOSITORY_TEST]
- [x] Run → RED confirmed under the venv runner (the resolver does not exist; the directory fixtures fail on the missing module) [class: REPOSITORY_TEST]
- [x] Implement Task 1 per the Files contracts above; the plans skill and runtime-scripts.list edits land in the same commit as the code [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: the full task suite green and the baseline suites unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: plan shape resolver with directory-form readiness and validator acceptance` [class: IMPLEMENTATION_REQUIRED]

Primary class anchors: plan_readiness.py `main` plan_path operand and `vrs.compute_source_digest("plan", plan_bytes)` production call site; `feature_slug`'s `plan_path.stem` derivation; validate_review_staging.py `--source-plan` routing with its `source_path.is_file()` gate; plans SKILL.md `## Plan Format` heading and rule 9 digest wording; scripts/runtime-scripts.list deployment rows.

### Task 2: directory operands for the classifier, origins checker, guard, and the archive twin (TDD)

Files:
- `scripts/plan_delta_classifier.py`: the `--plan` CLI layer resolves the operand through the helper and loops per file, decorating each hunk header with the file's relative path; the checkbox-flip proof applies per task file; a manifest-level add or remove of a task file classifies as a structural delta, not exempt; the corrections chain records one row per changed file (anchor: `classify_lines(old_bytes, new_bytes)` and the CLI operand entry; read-only anchor, edits out of scope: the corrections single-blob sites in scripts/corrections_record.py, which this plan verifies but never modifies)
- `scripts/test_plan_delta_classifier.py`: per-file flip fixture over a directory plan with path-named headers; structural add/remove fixture; single-file fixtures unchanged
- `scripts/check_plan_origins_closed.py`: `--plan` directory reads the origins block from the charter; the corpus scan walk includes plans-root directories beside files; `_witness_plan_exists`'s basename match re-derives the directory slug; the undercount audit, `--check-coverage`, and `--mark-covered` parse the charter's block (anchor: the `plan_path.read_text` sites, the corpus walk, and `_witness_plan_exists`)
- `scripts/test_check_plan_origins_closed.py`: directory-form archive gate fixture with an unbackticked plural block; corpus scan fixture discovering a directory plan; witness match on the directory slug
- `scripts/reverse_squash_guard.py`: the name-status layer aggregates per-file rows under a common `<plans-root>/<slug>/` prefix into one directory egress keyed on the directory slug before `egress_findings` runs; the archive-evidence leg requires the exec-review record keyed on the directory slug and zero unchecked boxes across all task files plus the charter; `--ack-egress` names the directory path once and refuses a path that is not the egress; `plan_slug` re-derives from the directory operand; the check-claim-fence arm's `claim_stem_matches_path` matches a claim keyed to the directory slug for paths under `<slug>/` (anchors: `parse_numstat_z`, `egress_findings`, `is_archive`, the single-slot `--ack-egress` logic, and the claim-fence stem match)
- `scripts/test_reverse_squash_guard.py`: directory egress fixtures, the archive rename with evidence, the sideways rename refusal, N-rows-one-finding aggregation, the ack slot exactness, and the claim-fence match on a directory plan's deletion
- `scripts/done_sweep_gates_lib.py`: the archive-ceremony twin section changes with the guard per the guard docstring's both-named-sites clause; `_archive_twin_at_head`'s basename keying accepts the directory twin and the per-archive checkbox leg spans all task files (anchor: the archive-ceremony section and `_archive_twin_at_head`)

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_delta_classifier.py scripts/test_check_plan_origins_closed.py scripts/test_reverse_squash_guard.py -q` passes today (the single-file baseline)
- `git diff --numstat -z` over a staged directory rename records N per-file rows and no directory row (the aggregation premise, re-derivable at execution)

- [x] Re-derive the anchors from live bytes: the classifier CLI operand and `classify_lines` signature, the origins checker's read/walk/witness sites, the guard's numstat/egress/ack/claim-fence sites, the done library's archive-ceremony twin, and any pin naming these spans; a moved anchor re-keys its pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] `test_classifier_per_file_headers`; a checkbox-flip-only delta on one task file of a directory plan returns the exempt verdict with the task file named in the hunk header; removing a task file is structural [class: REPOSITORY_TEST]
- [x] `test_origins_directory_archive_gate`; the archive gate passes a directory plan whose charter carries the witnessed unbackticked plural origins block; the undercount audit fires on a dispositions/parsed gap [class: REPOSITORY_TEST]
- [x] `test_origins_directory_witness`; `_witness_plan_exists` matches a covering directory plan by its slug [class: REPOSITORY_TEST]
- [x] `test_guard_directory_egress_aggregation`; N per-file rows under one `<slug>/` prefix yield exactly one egress finding keyed on the slug, and the evidence leg spans charter plus all task files [class: REPOSITORY_TEST]
- [x] `test_guard_ack_exactness`; `--ack-egress` names the directory path exactly once and a non-egress path refuses [class: REPOSITORY_TEST]
- [x] `test_guard_claim_fence_directory`; a plans-root directory deletion while a live claim names the slug refuses through the check-claim-fence arm [class: REPOSITORY_TEST]
- [x] `test_done_twin_directory_archive`; the archive twin accepts a directory-shaped archived plan with the checkbox leg across task files [class: REPOSITORY_TEST]
- [x] Run → RED confirmed under the venv runner [class: REPOSITORY_TEST]
- [x] Implement Task 2 per the Files contracts above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: the full task suite green and the baseline suites unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: directory operands for the plan delta classifier, origins checker, egress guard, and archive twin` [class: IMPLEMENTATION_REQUIRED]

Primary class anchors: classifier `classify_lines(old_bytes, new_bytes)` and its CLI operand entry; origins checker `plan_path.read_text` sites, corpus walk, and `_witness_plan_exists`; guard `parse_numstat_z`, `egress_findings`, `is_archive`, the `--ack-egress` slot logic, and `claim_stem_matches_path`; done_sweep_gates_lib.py `_archive_twin_at_head` and the archive-ceremony section.

### Task 3: the execution driver's directory plan surface (TDD)

Files:
- `scripts/execute_plan_runtime.py`: the plan read gate resolves the operand through the helper instead of refusing non-regular files outright; task parsing assembles the `### Task N:` sections from the charter-plus-tasks forms; the worker payload for a directory plan is the charter plus exactly the worker's one task file whole; the closeout receipt digest re-hash uses the manifest digest for a directory plan (anchors: the S_ISREG plan read gate, the single-file task parse, and the closeout `plan_digest` re-hash)
- `scripts/test_execute_plan_runtime.py` *(new tests inside the existing suite file)*: the directory-plan seed, the per-task worker payload contract, and the receipt digest fixture
- `scripts/execute_plan_resume_watcher.py`: plan operand passthrough resolves directory operands through the helper
- `scripts/test_execute_plan_resume_watcher.py`: the passthrough fixture

Evidence:
- the runtime's plan read gate refuses a directory operand today (the S_ISREG check), so the directory fixtures go RED on the refusal
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_execute_plan_runtime.py scripts/test_execute_plan_resume_watcher.py -q` passes today (the single-file baseline)

- [x] Re-derive the anchors from live bytes: the plan read gate's S_ISREG check, the task parse, the closeout receipt digest re-hash, the resume watcher's plan operand, and any pin naming these spans; a moved anchor re-keys its pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] `test_runtime_directory_seed`; the runtime seeds a directory plan, parsing tasks from the task files and the shared sections from the charter [class: REPOSITORY_TEST]
- [x] `test_runtime_worker_payload_charter_plus_task`; a directory plan's worker payload contains the charter and exactly the addressed task file, whole, with no span extraction [class: REPOSITORY_TEST]
- [x] `test_runtime_receipt_manifest_digest`; the closeout receipt re-hash for a directory plan equals the manifest digest [class: REPOSITORY_TEST]
- [x] `test_resume_watcher_directory_passthrough`; the watcher resolves a directory operand and refuses a malformed one [class: REPOSITORY_TEST]
- [x] Run → RED confirmed under the venv runner [class: REPOSITORY_TEST]
- [x] Implement Task 3 per the Files contracts above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: the full task suite green and the baseline suites unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: execution driver accepts directory-shaped plans with charter-plus-task worker payloads` [class: IMPLEMENTATION_REQUIRED]

Primary class anchors: execute_plan_runtime.py plan read gate (the S_ISREG refusal), the `### Task N:` parse, and the closeout `plan_digest` re-hash; execute_plan_resume_watcher.py plan operand entry.

### Task 4: liveness, prune witnesses, and the skill/wording contract (TDD)

Files:
- `scripts/check_authoring_plans_liveness.py`: directory candidates derive from untracked `PLAN.md` paths under the plans root in the enumeration `enumerate_candidates` already runs (the current candidate filter drops every file whose dirname is not the plans root, so directory plans are invisible today); each directory candidate classifies live/stranded by claim match on the directory slug; a charterless untracked directory reports stranded naming that reason; the report names directory candidates with their charter path
- `scripts/test_authoring_plans_liveness.py`: directory candidate fixtures, live with a fresh claim on the slug, stranded without, stranded charterless
- `scripts/check_prompt_log_origins.py`: the prune witness accepts the charter path form beside the file forms in `witness_candidates`' ls-tree depth grammar (anchor: `witness_candidates`, the path-depth parse; the backlog-origin `is_file()` sites elsewhere in the file are NOT prune witnesses and stay untouched)
- `scripts/test_check_prompt_log_origins.py`: directory-witness prune receipt fixture; the backlog-origin sites unchanged
- `scripts/plan_task_span.py`: a directory operand refuses loud with a pointer to whole-file charter-plus-task reads; no span extraction across files
- `scripts/test_plan_task_span.py`: the refusal fixture
- `docs/history/backlog/PLAN-PROMPTS.md`: the prune-rule standing sentence gains the directory form; the frozen entries and the rest of the standing rules are untouched
- `agents/skills/maintenance/SKILL.md`: the spans whose predicate reads that an entry is removed when its plan file exists in the plans root gain the directory form, same-edit
- `agents/skills/execute-plan/SKILL.md`: the Prerequisite paragraph accepts the directory shape beside the plan file, the plan-path heuristic line accepts a directory operand, and the seven-file copy remedy inventory sentence names the helper module
- `scripts/check_maintenance_pins.sh`: same-edit re-keying of any pin naming a reworded span, including the execute-plan prerequisite pins (the pin family at the `the create boundary's repository discovery derives the task's concrete scope` span and its sibling)

Evidence:
- python3 scripts/check_authoring_plans_liveness.py --repo . reports zero directory candidates today (the untracked plan under review is the one file candidate, so the baseline run reports it and exits non-zero; the directory fixtures go RED on invisibility)
- `git ls-files --others --exclude-standard` inside an untracked plans-root directory lists the nested files individually, so the charter-path derivation is the discovery mechanism (re-derivable at execution)

- [x] Re-derive the anchors from live bytes: the liveness enumeration and candidate filter, `witness_candidates`' depth grammar, the prune-rule and census predicate spans, the execute-plan prerequisite paragraph and its pin family, plan_task_span's operand entry; a moved anchor re-keys its pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] `test_liveness_directory_candidates`; an untracked directory plan classifies live with a fresh claim on the slug and stranded without; a charterless untracked directory reports stranded naming the reason [class: REPOSITORY_TEST]
- [x] `test_prune_witness_directory`; the prune audit accepts a `<slug>/PLAN.md` witness at the plans-root depth and still fails closed on a removal with neither form at the plans root [class: REPOSITORY_TEST]
- [x] `test_plan_task_span_directory_refusal`; a directory operand refuses with the named pointer; file behavior unchanged [class: REPOSITORY_TEST]
- [x] The three wording surfaces carry the directory form; every pin naming a reworded span re-keyed in the same edit and the pins suite exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Run → RED confirmed under the venv runner [class: REPOSITORY_TEST]
- [x] Implement Task 4 per the Files contracts above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: the full task suite green and the baseline suites unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: directory-form liveness candidates, prune witnesses, and skill wording` [class: IMPLEMENTATION_REQUIRED]

Primary class anchors: check_authoring_plans_liveness.py `enumerate_candidates` and its candidate filter; check_prompt_log_origins.py `witness_candidates` ls-tree depth grammar; the PLAN-PROMPTS prune-rule sentence; the execute-plan Prerequisite paragraph and its pin family in scripts/check_maintenance_pins.sh; plan_task_span.py operand entry.

## Disposition

- Execution dependency: Tasks 2, 3, and 4 strictly after Task 1 (all import the Task 1 resolver); Tasks 2, 3, and 4 are mutually independent after Task 1 and may run in any order.
- The execution budget declares 5.0h total against the 3.0h sizing cap; the justification is pinned: the four tasks are one migration mechanism across disjoint file seams whose split would strand the Task 2-4 consumers without the Task 1 resolver and manufacture second authoring cycles over the same investigation; the r1 panel proved the narrow scope false (the validator, driver, and archive-twin consumers refuse directory operands today), so the wider task set is the honest scope; the caps are split-questions, not refusals (the sizing row's recorded rejected alternative).
- No external gate: the sequencing precondition (U1 + U3 landed) is witnessed at authoring time by the completed/ twins, so no `External gate:` line is carried.
- On landing: the origin row flips covered by the landing rider (the delete-on-coverage pattern the sizing and read-contract riders used), the frozen PLAN-PROMPTS entry prunes with this plan file as its plans-root witness, and the machinery registry gains rows for the new helper module and the touched surfaces.
- Deliberate residuals recorded for the execution review: the corrections-chain per-file row semantics are assigned at the classifier CLI layer (Task 2) and deeper corrections-chain rework stays out of scope; the worktree_closeout_migrate sweep's plans-completed tree keying reads directory archives as nested tree entries and is verified, not reworked, by this plan's fixtures.
