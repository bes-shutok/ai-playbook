# Plan: skill-audit-artifact-ignore-default

| Field | Value |
| --- | --- |
| Date | 2026-10-13 |
| Dispatch entry | PLAN-PROMPTS `skill-audit-artifact-ignore-default` (frozen b13ddc624) |
| Origins | docs/history/backlog/2026-10-12-skill-audit-artifact-folders-gitignore-default.md; docs/history/backlog/2026-10-11-review-certs-home-missing-from-docs-branch-sync.md |
| Work type | Cross-surface path consolidation; behavior-preserving for every gate and retention contract |
| Authoring session | sess_5c51c846 (worktree 2026-10-13-said-authoring) |
| Review budget | At most 3 review rounds within 3 hours (D-8); delta rounds do not consume the budget |

## Terms

- Audit artifact: a generated review record, certification seal, or efficiency/telemetry metric produced by running this playbook's skills; distinct from execution claims and scratch, which stay transient.
- The one-home rule: docs/AGENTS.md line 76 (landed e246265d2) requires audit artifacts under one canonical, already-ignored home per project with type-specific subdirectories, across company, personal, and pet projects.
- Live surface: any tracked file a runtime, skill, hook, or validator loads outside docs/history/ and outside dated maintenance records (docs/maintenance/machinery-blocker-audit-2026-10-09.md and docs/maintenance/development_lessons.md are historical records; their path mentions stay).
- Census of record: `rg -ln "docs/history/reviews|docs/history/review-certs|docs/history/metrics|docs/metrics" --glob '!docs/history/**'` at the base commit; its hits minus the two historical records are the complete migration surface (49 live files at authoring time, enumerated across the tasks below).

## Why

Audit artifacts sit in three ignored siblings under docs/history/ (reviews, review-certs, metrics) plus a legacy docs/metrics exact rule. docs/history/ is a mixed tracked-and-ignored documentation tier, so it is not an "already-ignored home", and the one-home rule's own text points at this backlog row for selection and consolidation. The choice is forced by existing charters: `{tmp_dir}` (docs/tmp/) is transient by charter ("promote or delete same cycle; never reference from canonical docs", docs/AGENTS.md line 102) and is excluded from docs-branch retention, so the durable, sha-cited corpus cannot live there. `.ai-playbook/` is the wholesale-ignored, bootstrap-owned runtime dir (`.gitignore` line 9) that already hosts audit-family outputs (friction-audit, done-session). Selected home of record: `.ai-playbook/` with type-specific subdirectories `.ai-playbook/reviews/`, `.ai-playbook/review-certs/`, `.ai-playbook/metrics/`; `tmp_dir` stays docs/tmp/ for transient artifacts. The facts keys (`reviews_dir`, `review_certs_dir`, `metrics_dir`) are the resolution layer, so consumers reading facts follow the re-aim; every hardcoded literal and default must move in the same change.

## Second origin disposition

The sibling row `2026-10-11-review-certs-home-missing-from-docs-branch-sync.md` is already covered at tip: the seal-home-untracked execution landing a2a4c271a added the review-certs retention root to scripts/docs_branch_sync.sh (sync roots at lines 266-268 carry `review_certs_dir`) and the facts key. Its "Problem" evidence (grep returns nothing, facts declare two keys) is stale. This plan's landing flips that row covered with witness a2a4c271a through the existing lifecycle; no code or text change is owed to it beyond this plan's own path migration, which carries the retention roots to the new home.

## Task 1: re-aim the path facts, bootstrap seed map, and top-level docs

- [x] Flip the three facts values in `.ai-playbook/facts.md`: `reviews_dir` to `.ai-playbook/reviews/`, `review_certs_dir` to `.ai-playbook/review-certs/`, `metrics_dir` to `.ai-playbook/metrics/`; `tmp_dir`, `facts_path`, and every other key stay byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim agents/skills/bootstrap-ai-playbook/SKILL.md: the required-keys TOML example, the canonical greenfield history map, the metrics_dir creation flow (create the subdir under the audit home beside the runtime dir; no per-type .gitignore lines are added because `/.ai-playbook/` is wholesale-ignored), and the seed wording that names docs/history/ audit paths, all move to the `.ai-playbook/` subdirectory forms. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the docs/AGENTS.md one-home bullet's backlog pointer to name the landed plan as the selection record, and update projects/.ai-playbook/agent-runtime-layout.md's runtime-dir mapping to list the three audit subdirectories beside the existing runtime entries. [class: IMPLEMENTATION_REQUIRED]

## Task 2: re-aim retention and closeout scripts and their tests

- [x] Re-aim the sync runner's audit-root containment in scripts/docs_branch_sync.sh: `normalize_root`'s below-docs check and `resolve_roots`' docs-containment re-check accept the audit home as the sanctioned root prefix; the root's basename-matches-role check and the facts-key resolution layer stay byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim every `docs/history/reviews`, `docs/history/review-certs`, and `docs/history/metrics` default literal in scripts/docs_branch_sync.sh and scripts/done_run.sh to the `.ai-playbook/` subdirectory forms; the add-only docs-branch semantics stay byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the same literals in scripts/worktree_closeout_migrate.py and scripts/corrections_record.py and their suites scripts/test_worktree_closeout_migrate.py, scripts/test_done_sweep_gates_lib.py, scripts/test_done_sweep_gates_wrapper.py, scripts/test_done_run_wrapper.py, scripts/test_corrections_record.py, scripts/test_docs_branch_sync.py, scripts/test_review_retention.py: fixtures and expected paths move to the new home; no gate arm's logic changes. [class: IMPLEMENTATION_REQUIRED]

## Task 3: re-aim review-surface validators, hooks, and ledgers

- [x] Re-aim the path literals in scripts/validate_review_staging.py, scripts/code_delta_classifier.py, scripts/summarize_review_stats.py, and scripts/doc_registry_validator.py to the `.ai-playbook/` subdirectory forms; defaults and doc examples only, no check logic changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the reviews-home spans in scripts/reverse_squash_guard.py: both `REVIEWS_HOME_PREFIXES` and `REVIEWS_HOMES` become `(".ai-playbook/reviews/",)` so the egress deny set and the record leg's walk follow the corpus home (the old prefixes protect and walk no live corpus after the migration), and the two docstring mentions of the old homes re-aim; the refusal arms and the digest-bound record-leg mechanism stay byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the pins suite's audit-path surfaces in scripts/check_maintenance_pins.sh: the passing pin over the guard tuple (the `reviews-home prefix set present in the guard` pin's expected literal) re-aims to the new tuple bytes, and the P37 telemetry provenance comment's `docs/history/metrics/` carve-out wording re-aims to the new metrics home; no checked span outside these two moves. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the path literals in cursor/hooks/git-safety.sh, cursor/hooks/README.md, and cursor/hooks/review-staging-gate.sh (the staging gate's component-assembled old-home fallback in `newest_staging` re-aims to the new home; its facts-first resolution stays byte-identical), plus scripts/OUTCOME_CONTRACT.md, scripts/gate_liveness_ledger.json, and scripts/machinery_registry.json; defaults, docs, and ledger entries only, no check logic changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the path fixtures in scripts/test_review_record_selection.py, scripts/test_reverse_squash_guard.py, scripts/test_check_run_continuity.py, and scripts/test_plan_readiness.py to the new home; each touched suite must pass after this task. [class: REPOSITORY_TEST]
- [x] Re-aim the path fixtures in scripts/test_land_squash.py (the guard's record-leg suite: its fixture record homes follow the re-aimed `REVIEWS_HOMES`), scripts/test_review_retention.py, scripts/test_parallel_work_regressions.py, scripts/test_execute_plan_worktree_bootstrap.py, and scripts/test_rejected_archive_lifecycle.py to the new home; each touched suite must pass after this task. [class: REPOSITORY_TEST]

## Task 4: re-aim skill text and the promulgated schema

- [x] Re-aim hardcoded audit-path literals in agents/skills/plans/SKILL.md, agents/skills/execute-plan/SKILL.md, agents/skills/done/SKILL.md, agents/skills/review-plan/SKILL.md, and agents/skills/review-staging/SKILL.md to the `.ai-playbook/` subdirectory forms. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim hardcoded audit-path literals in agents/skills/docs-branch/SKILL.md, agents/skills/rfc-design/SKILL.md, and agents/skills/review-confluence-doc/SKILL.md to the `.ai-playbook/` forms; facts-placeholder references (`{reviews_dir}` style) stay untouched across all skill text because they follow the re-aimed facts. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the doc-hierarchy schema surfaces: agents/skills/doc-hierarchy/SKILL.md, agents/skills/doc-hierarchy/migration-map.md, agents/skills/doc-hierarchy/company-decisions.md, agents/skills/doc-hierarchy/instruction-templates.md, and agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh: audit-home guidance and literals move to the `.ai-playbook/` forms; the schema's tracked documentation tiers stay byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the maintenance and rider surfaces: agents/skills/maintenance/decisions.md, agents/skills/maintenance/template-execution.md, agents/skills/maintenance/template-authoring.md, agents/skills/maintenance/templates-CHANGELOG.md, docs/maintenance/recurring-tasks/weekly-measurement-rider.md, and docs/maintenance/recurring-tasks/friction-audit.md to the `.ai-playbook/` forms. [class: IMPLEMENTATION_REQUIRED]

## Task 5: corpus migration, ignore-rule cleanup, and dispositions

- [x] At the executing checkout, migrate the untracked corpus: create `.ai-playbook/reviews/`, `.ai-playbook/review-certs/`, `.ai-playbook/metrics/` and move the contents of docs/history/reviews/, docs/history/review-certs/, docs/history/metrics/ into them, preserving file names; then remove the obsolete exact ignore rules for the three migrated homes and docs/metrics from .gitignore, keeping `/.ai-playbook/`, `/docs/reviews` (legacy-layout compatibility), and `/docs/tmp/`. [class: IMPLEMENTATION_REQUIRED]
- [x] Flip both origin rows covered in the same landing: 2026-10-12-skill-audit-artifact-folders-gitignore-default.md (this plan as witness) and 2026-10-11-review-certs-home-missing-from-docs-branch-sync.md (a2a4c271a as witness), using the canonical `covered (<witness>)` status form; tidy the surviving Cluster pointers at the flipped rows. [class: IMPLEMENTATION_REQUIRED]
- [x] Validation: run the pins suite and require its PIN FAIL name set to be identical to a base run at the merge base (21 failures at authoring time); any new or vanished failure is a foldable result. [class: REPOSITORY_TEST]
- [x] Validation: a census re-run at the landing head returns no live-surface hit for the old audit paths outside the two named historical maintenance records; the moved corpus resolves at the new home (`ls .ai-playbook/reviews` non-empty); the touched docs-branch sync suite passes with its root-resolution fixtures asserting the three new-path roots. [class: REPOSITORY_TEST]
- [x] Validation: `CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file` over every non-Markdown touched file exits 0 (the all-files switch is required because the default prose filter skips scripts and JSON), and the public hygiene scan (user facts key public_hygiene_scan_script) exits 0. [class: REPOSITORY_TEST]

## Assumptions

- assume `.ai-playbook/` over `docs/tmp/`: the tmp charter makes docs/tmp transient and unreferencable from canonical docs, while the audit corpus is durable, sha-cited, and retention-synced; `.ai-playbook/` is wholesale-ignored and already hosts audit-family outputs; basis: docs/AGENTS.md line 102, the docs-branch exclusion of docs/tmp, and the .gitignore line 9 rule.
- assume facts-resolved consumers need no code change: validators and gates reading `reviews_dir`/`review_certs_dir`/`metrics_dir` from facts follow the re-aimed values, so only hardcoded literals and defaults migrate; basis: the facts resolution layer in facts_paths.py and the sync runner's facts.get roots.
- assume the docs-branch retention contract carries over with one recorded carried change: the sync is add-only over facts-resolved roots, so the corpus lands at `.ai-playbook/*` paths on the docs orphan branch after the re-aim; the landing composes an archive-only tree from the active roots (`build_archive` keeps only branch paths under current roots), so the old docs/history copies leave the branch TIP at the first post-migration sync while remaining retrievable in the branch's commit history, their content preserved at the new paths; basis: scripts/docs_branch_sync.sh `index_tree` (read-tree --empty plus kept only) and `build_archive`'s root-filtered branch scan.
- assume worktree-transfer behavior is unchanged: the audit home was already untracked and absent from fresh worktrees, requiring provisioning; the move does not change that property; basis: the gate-removal provisioning duty in worktree_closeout_migrate.py.
- assume no new machinery: no setting, helper, validator, or gate is added; every check keeps its existing mechanism with a re-aimed path; basis: the entry's no-new-machinery arm and the machinery-admission protocol.

Decision points requiring a grill: none remain.

## Standing constraints

- Plan scripts and validators run under `python3.14`; all commands stay repo-relative with no machine-specific absolute paths; nothing in this plan authorizes a push to origin; review records and seals stay in their untracked homes and are never git-added.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/docs_branch_sync.sh`, `scripts/done_run.sh`, `scripts/worktree_closeout_migrate.py`, `scripts/corrections_record.py`, `scripts/validate_review_staging.py`, `scripts/code_delta_classifier.py`, `scripts/reverse_squash_guard.py`, `scripts/summarize_review_stats.py`, `scripts/doc_registry_validator.py`, `scripts/check_maintenance_pins.sh`, `cursor/hooks/git-safety.sh`, `cursor/hooks/README.md`, `cursor/hooks/review-staging-gate.sh` (path literals, defaults, the egress deny-set and record-leg tuples, and the two named pin surfaces only)
- `scripts/gate_liveness_ledger.json`, `scripts/machinery_registry.json` (path literals only)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py`, `scripts/test_done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_wrapper.py`, `scripts/test_done_run_wrapper.py`, `scripts/test_corrections_record.py`, `scripts/test_docs_branch_sync.py`, `scripts/test_review_retention.py`, `scripts/test_review_record_selection.py`, `scripts/test_reverse_squash_guard.py`, `scripts/test_land_squash.py` (fixture paths only)
- `scripts/test_check_run_continuity.py`, `scripts/test_plan_readiness.py`, `scripts/test_parallel_work_regressions.py`, `scripts/test_execute_plan_worktree_bootstrap.py`, `scripts/test_rejected_archive_lifecycle.py` (fixture paths only)
- `agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh` (path literals only)

**Documentation:**
- `.ai-playbook/facts.md`, `.gitignore`, `docs/AGENTS.md`, `projects/.ai-playbook/agent-runtime-layout.md`, `scripts/OUTCOME_CONTRACT.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`, `agents/skills/plans/SKILL.md`, `agents/skills/execute-plan/SKILL.md`, `agents/skills/done/SKILL.md`, `agents/skills/review-plan/SKILL.md`, `agents/skills/review-staging/SKILL.md`, `agents/skills/docs-branch/SKILL.md`, `agents/skills/rfc-design/SKILL.md`, `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`, `agents/skills/doc-hierarchy/migration-map.md`, `agents/skills/doc-hierarchy/company-decisions.md`, `agents/skills/doc-hierarchy/instruction-templates.md`, `agents/skills/maintenance/decisions.md`, `agents/skills/maintenance/template-execution.md`, `agents/skills/maintenance/template-authoring.md`, `agents/skills/maintenance/templates-CHANGELOG.md`
- `docs/maintenance/recurring-tasks/weekly-measurement-rider.md`, `docs/maintenance/recurring-tasks/friction-audit.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The landing's own riders (the frozen entry's prune line, both origin-row covered flips, the PLAN-PROMPTS-PRUNE receipt) ride the landing branch per the log charter. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- docs/history/ records and the two named historical maintenance records; reason: historical context keeps old paths (Terms).
- the doc-hierarchy tracked documentation tiers beyond audit-path guidance; reason: the schema change is bounded to audit artifacts (Task 4).
- any new audit root, setting, helper, validator, or gate; reason: Assumption 5, the entry's rejected alternatives.
- the legacy-layout ignore rules `/docs/reviews` and `/docs/tmp/`; reason: Task 5 keeps them as compatibility.

## Ship-when

The three audit families resolve from facts and every default to `.ai-playbook/` subdirectories; the corpus lives at the new home; the obsolete ignore rules are gone; both origin rows are covered with witnesses; the pins failure set is byte-identical to base; every touched test suite passes; the census finds no live-surface literal of the old paths; no gate arm, retention contract, or worktree-transfer property changed.
