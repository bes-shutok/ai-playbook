# Plan: review staging and infra quality

Backlog origins (scope of record; full text read from `docs/history/backlog/`):

- `docs/history/backlog/2026-09-16-review-staging-coverage-attempt-shadowing.md` (HIGH: the validator's shadowed variable masks coverage outcomes, forcing producers to omit attempts telemetry)
- `docs/history/backlog/2026-09-16-review-retention-and-safe-pruning.md` (3,300+ review files, no pruning policy)
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md` (every round rediscovers the sidecar's hard structural requirements)
- `docs/history/backlog/2026-09-19-review-staging-canonical-pattern-retrofit.md` (the gate cannot parse panel-layout docs; witnessed twice in one session)
- `docs/history/backlog/2026-09-19-review-staging-integration-points-row-accuracy.md` (over-claiming consumer rows cause spurious twin-gate failures)

## Terms

- **Staging doc**: the Markdown review record under `{reviews_dir}` that carries Metadata, Review Statistics, and `#### F<N>.` finding blocks per the review-staging gold source.
- **Stats sidecar**: the `<same-basename>.stats.json` JSON record paired with a staging doc; the machine-readable half of one review record.
- **Coverage contract**: the `coverage` object gate in the validator (`validate_coverage_contract`) that cross-checks the sidecar verdict against the coverage-level `outcome`.
- **Attempts telemetry**: the `coverage.attempts[]` records (per-attempt outcome, failure class, timing, contributed coverage) the schema exists to carry.
- **Panel layout**: the execute-plan review-panel doc shape where findings are `### N. <title> (Severity)` headers (round appends `### R<N>-F<M>. <title> (Severity)`) instead of `### <Severity>` groups with `#### F<N>.` blocks.
- **Panel profile**: the documented, date-fenced, read-only validator path for records dated on or before `PANEL_PROFILE_MAX_DATE` (inclusive). Inside the window the validator runs ONLY the documented reduced gate set (the anti-stub core: the Markdown and sidecar pair parses; a Metadata section and a Findings section exist, matched by heading-text prefix so suffixed era headings count; the sidecar carries a verdict; the sidecar's counts agree with its own findings array when both are present; and whole-document finding conservation by document order when the Markdown parses into recognized finding blocks, with the panel header shapes `### N.` / `### R<N>-F<M>.` recognized across the Findings section and round-append sections alike). Every other gate, present or future, is reported as a warning and never fails an in-window record. Outside the window nothing changes. No schema routing and no per-gate waiver list exist: the record date alone selects the path, because era-mismatched format conformance is exactly what the window exists to excuse.
- **Retention cutoff**: the review filename date boundary (default three calendar months back) that decides pruning candidacy; never filesystem mtime.
- **Pruning unit**: a staging Markdown file plus its matching `.stats.json` sidecar; the pair is deleted as one unit or not at all.
- **Explicit delete**: a docs-branch commit that removes tracked review paths, the only mechanism the docs-branch add-only sync invariant accepts as a durable deletion.

## Assumptions

- assume the origin-1 code defect is already fixed on the default branch (commit 7baa8ce1 renamed the attempts-loop outcome to `attempt_outcome` with an anti-shadowing comment); this plan adds the missing positive regression fixture and the same-family sweep instead of re-fixing; basis: executed probe of `validate_coverage_contract` shows the verdict cross-check reads the coverage-level outcome after the loop, and the selftest has no positive attempts-telemetry check today.
- assume the retention window follows the user-confirmed 2026-09-16 cleanup semantics: three calendar months, cutoff by the record filename date, never mtime; basis: the retention origin's "Current disposition" paragraph.
- assume a new optional `review_retention_months` facts key read through the existing facts TOML pattern; basis: `.ai-playbook/facts.md` TOML block and the origin's suggested fix item 1.
- assume the origin-4 direction is the documented freshness-gated read-only panel profile plus shape-aware finding-block parsing, and NOT a one-off retrofit script; basis: standing pre-authorization (task prompt) accepting the origin's option (b) as narrowed by its witness 2.
- assume one plan covers all five origins as separately reviewable tasks; basis: the task prompt mandates a single plan titled "review staging and infra quality".

Decision points requiring a grill: profile direction: documented panel profile plus shape-aware parser, no retrofit script (source: standing pre-authorization accepting origin option b per witness-2 narrowing, 2026-09-22, Tasks 5); profile fence: inclusive on or before 2026-09-19 so both witnessed docs qualify (source: witness-2 doc dates in the origin text, 2026-09-22, Task 5); done-gate disposition: the hard staging gate stays and historical docs pass under the profile when content is complete (source: standing pre-authorization, 2026-09-22, Task 5); retention scope: the origin's full five-part suggested fix including the docs-branch transaction (source: standing pre-authorization accepting the origin's suggested fix, 2026-09-22, Tasks 2 and 3); checklist placement: a new section adjacent to Output discipline plus a confidence-enum remediation hint (source: standing pre-authorization accepting the origin's prevention items, 2026-09-22, Task 4)

## Gist & Examples

Five review-infrastructure defects close in one plan, each as its own reviewable task.

**Attempts telemetry un-shadowed (origin 1).** The shadowing fix itself already landed: the attempts loop now writes `attempt_outcome`, and the verdict cross-check reads the coverage-level `outcome`. What never landed is the regression fixture that would catch a reintroduction, and the same-family sweep the origin demands. Example: a verdict-yes sidecar whose coverage carries two attempts (one failed with a failure class, one complete with `contributed_coverage: true`) must pass the coverage contract today and must still pass after any future refactor. Task 1 pins that with a selftest check and proves the check discriminates by reintroducing the historical shadow under a mutation probe (authoring-time baseline: zero existing checks flip under that mutation).

**Review artifact retention (origin 2).** Review directories accumulate without a lifecycle; the 2026-09-16 one-off cleanup removed 37 live records by hand. Task 2 adds `scripts/review_retention.py`: an optional `review_retention_months` facts key (default three months), a deterministic dry-run report of candidates by directory, filename date, record kind, and pairing (no document bodies), pairing-aware pruning (Markdown plus `.stats.json` as one unit; unpaired records retained and reported), explicit keep rules, and a sanitized manifest of counts, cutoff, and path hashes. Undated files are never auto-pruned. Task 3 adds the docs-branch transaction the origin requires: deletions become explicit-delete commits on the docs branch through a temporary worktree (the live checkout never holds the docs branch), verified, then applied to the live shadow files, aborting before mutation if the candidate set changed. Example: pruning `2026-04-01-foo-plan-review-r1.md` removes `2026-04-01-foo-plan-review-r1.stats.json` in the same step or fails.

**Synthesis gates documented where synthesis happens (origin 3).** Every synthesizing round rediscovers the sidecar's hard gates as validator errors. Task 4 puts a "Synthesis-time hard gates" checklist in review-staging at the point the orchestrator writes the doc: closed enums, the per-worker finding budget with overflow mechanics, the `#### F<N>.` block shape with ordered severity groups, the freshness Metadata lines, the post-fix Witness ledger, and the plan-Validation-block fence-stripping note. The confidence-enum validator error gains a remediation hint (map to the closed enum; do not downgrade); the overflow errors already carry one.

**Panel profile for historical docs (origin 4).** The `--hard` gate parses zero findings from panel-layout docs and demands row shapes historical docs predate. Two folds tried to enumerate waived gate families, and both measurably missed (the 2026-09-19 record is version-1 with header-shaped findings; the 2026-09-18 phase3 records are version-1 with pipe-table findings and era-mismatched fields), so Task 5 now defines the profile as a date-fenced reduced path: records dated on or before `PANEL_PROFILE_MAX_DATE` (`2026-09-19`, inclusive, so every witnessed record qualifies) are validated ONLY against the anti-stub core (pair parses, Metadata and Findings sections exist, sidecar verdict present, sidecar counts self-consistent, and whole-document finding conservation by document order when the Markdown parses into recognized blocks, with the panel header shapes recognized across the Findings section and round-append sections alike); every other gate emits a warning and never fails the record. The record date alone selects the path, so no gate family can fall outside the profile by existing or evolving after the fold. Current-format in-window records are validated by the same reduced set, which is a documented consequence of the fence. Post-window records keep the full contract byte-for-byte, the parser flag is threaded at the Markdown-parse call sites the conservation leg uses, and the selftest fixtures are derived from both witnessed shapes. The done gate needs no change: it keeps running `--hard`, and complete historical docs now pass under the profile. Example: the witnessed r1 doc's nine sidecar findings stop reporting "Markdown lists 0 finding(s)", and the phase3 r1-r5 records stop failing on families their era never carried.

**Integration Points rows that match producer bytes (origin 5).** Task 6 applies the r3 narrowing uniformly in the review-staging consumer table: `review-confluence-doc` and `review-reconciliation` rows state the sidecar field and attribute the Metadata twin to the universal review-staging template (their own bytes never write the twin); the execute-plan Phase 3 row drops the record-selection-helper claim no execute-plan byte wires; the doing-code-review row gains the helper note its Step 1 review-artifact preflight (item 4) mandates. Each edited row is re-verified against the consumer's actual bytes.

## Evaluation Criteria

**Quality dimensions:**

- correctness: `python3 scripts/validate_review_staging.py --selftest` exits 0 including every new check; `python3 scripts/test_review_retention.py` exits 0 (unittest, the repo's test convention; the pytest module is not installed in this environment).
- backward compatibility: current-format records parse exactly as today (the panel-shape parser keyword defaults off); a post-window panel-layout record still fails finding-block parsing.
- historical compatibility: both witnessed shapes dated on or before 2026-09-19 pass `--hard` under the reduced path (the header-shaped record with its conservation enforced; the pipe-table record with its unparsed conservation leg reported as a warning), a stub in-window record still fails the anti-stub core, and post-window records of both shapes keep failing their current families.
- safety: the retention helper defaults to dry-run; deletion is pairing-aware, manifest-gated, aborts on candidate drift, never scans `{tmp_dir}`, and never auto-prunes undated files; the docs-branch add-only sync invariant is untouched.
- documentation accuracy: every edited Integration Points row claim is true of the consumer's own bytes.

**Done when:**

- the coverage-contract selftest has a positive attempts-telemetry check and a genuine-mismatch negative check, and the mutation probe flips the positive check.
- the same-family sweep over the validator's for-loops is logged with a per-hit verdict.
- `scripts/review_retention.py` passes its unittest file: deterministic dry run, filename-date cutoff, default and override windows, pairing-aware prune, abort-on-drift, sanitized manifest, keep rules.
- the docs-branch transaction tests pass: explicit-delete commit via temp worktree, verify-then-shadow-removal, abort on change, absent-branch skip.
- the synthesis-time hard gates section exists with all seven obligations and the confidence error carries the remediation hint.
- the five panel-profile selftests pass (witnessed header-shape record in-window, phase3 pipe-table record in-window, both re-dated post-window fail, a stub in-window record fails the anti-stub core, count agreement still enforced when parseable).
- the four Integration Points row edits land and each row's claim matches the consumer's bytes.
- `CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file` exits 0 over the changed files including both new Python files.

**Ship when:**

- none; every acceptance check above is local and repository-verifiable. No external gate, deployment, or cross-team condition exists for this plan.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/validate_review_staging.py` (in scope only for: the new `PANEL_PROFILE_MAX_DATE` constant beside `EXTENDED_SIDECAR_MIN_DATE`; the profile date branch and the reduced validator path it selects, including the warning-not-error plumbing; `_selftest_coverage_contract`; the profile selftests; `parse_markdown_findings` and `split_finding_blocks` plus the call sites the conservation leg threads; the confidence-enum error string; the same-family sweep's loop-local renames wherever a genuine hit exists. All other regions of this file are frozen; reject any review finding that touches them.)
- `scripts/review_retention.py` *(new)*

**Tests:**

- `scripts/test_review_retention.py` *(new)*
- selftest additions live inside `scripts/validate_review_staging.py` (region-frozen as listed above)

**Skills and docs:**

- `agents/skills/review-staging/SKILL.md` (new `## Synthesis-time hard gates` section; panel-profile paragraph in the historical compatibility prose; Integration Points table rows; Documentation paths retention note)
- `agents/skills/review-loop/SKILL.md` (one retention pointer in the `## Staging doc (required every round)` section)
- `agents/skills/docs-branch/SKILL.md` (one sanctioned-producer note near the explicit-deletes rule)
- `README.md` (one script table row for `scripts/review_retention.py`)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `docs/history/backlog/*.md`; reason: origins stay in place while the plan is open and are moved only by the completion step of the plan lifecycle.
- `agents/skills/done/SKILL.md`; reason: the done staging gate needs no edit under the done-gate disposition receipt (profile dissolves the historical-doc failures).
- any one-off retrofit script for historical canonical_pattern backfill; reason: rejected direction per the profile receipt (reconstruction, not completion).

## Design Invariants (CR Guard)

- The version-1 sidecar contract, its closed enums, key allowlists, and the `EXTENDED_SIDECAR_MIN_DATE` fence semantics are unchanged; the panel profile is additive and strictly date-fenced (inclusive `PANEL_PROFILE_MAX_DATE`).
- The profile path is record-date-gated only: a current-format gold doc dated after the window is parsed byte-for-byte as today, post-window panel layout keeps failing, and the warning-not-error behavior never applies outside the window.
- The docs-branch add-only sync invariant is untouched: retention deletions reach the docs branch only as explicit-delete commits, and the sync's restore path for everything else stays as documented.
- The coverage contract's enums (`ATTEMPT_OUTCOME_VALUES`, `COVERAGE_ALLOWED_KEYS`, retry-budget keys) are unchanged; Task 1 edits only the selftest and never production code.
- The record selection helper's behavior is unchanged; Task 6 edits prose rows only.
- Retention deletion is never implicit: default is dry-run, pruning requires an explicit flag plus a matching manifest, and the sanitized manifest never carries review text.

## Validation Commands

```bash
python3 scripts/validate_review_staging.py --selftest || { echo "validator selftest failed"; exit 1; }
python3 scripts/test_review_retention.py || { echo "retention unittest failed"; exit 1; }
python3 scripts/review_retention.py --dry-run >/dev/null || { echo "retention dry-run smoke failed"; exit 1; }
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file docs/plans/2026-09-22-review-staging-infra-quality.md scripts/review_retention.py scripts/test_review_retention.py agents/skills/review-staging/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/docs-branch/SKILL.md README.md || { echo "em-dash scan failed"; exit 1; }
test -f scripts/review_retention.py || { echo "retention helper missing"; exit 1; }
grep -qF "review_retention_months" scripts/review_retention.py || { echo "retention facts key unread"; exit 1; }
grep -qF "review_retention_months" agents/skills/review-staging/SKILL.md || { echo "retention key undocumented"; exit 1; }
grep -qF "review_retention.py" agents/skills/review-loop/SKILL.md || { echo "review-loop retention pointer missing"; exit 1; }
grep -qF "review_retention.py" agents/skills/docs-branch/SKILL.md || { echo "docs-branch producer note missing"; exit 1; }
grep -qF "scripts/review_retention.py" README.md || { echo "README script row missing"; exit 1; }
grep -qF "PANEL_PROFILE_MAX_DATE" scripts/validate_review_staging.py || { echo "profile constant missing"; exit 1; }
grep -qF "map to the closed confidence enum" scripts/validate_review_staging.py || { echo "confidence remediation hint missing"; exit 1; }
SEC="$(mktemp)"; TBL="$(mktemp)"; trap 'rm -f "$SEC" "$TBL"' EXIT
awk '/^## Synthesis-time hard gates/{f=1;next} /^## /{f=0} f' agents/skills/review-staging/SKILL.md > "$SEC"
test -s "$SEC" || { echo "synthesis gates section missing or empty"; exit 1; }
grep -qiF 'hypothesis' "$SEC" || { echo "gates: confidence enum missing"; exit 1; }
grep -qiF 'risk_signals' "$SEC" || { echo "gates: risk_signals enum missing"; exit 1; }
grep -qiF 'overflow' "$SEC" || { echo "gates: budget and overflow missing"; exit 1; }
grep -qF '#### F' "$SEC" || { echo "gates: block shape missing"; exit 1; }
grep -qF 'Review mode' "$SEC" || { echo "gates: freshness lines missing"; exit 1; }
grep -qiF 'witness ledger' "$SEC" || { echo "gates: witness ledger missing"; exit 1; }
grep -qiF 'fence' "$SEC" || { echo "gates: fence-stripping note missing"; exit 1; }
awk '/^\| `doing-code-review`/{print} /^\| `review-loop`/{print} /^\| `rfc-design`/{print} /^\| `review-confluence-doc`/{print} /^\| `review-reconciliation`/{print} /^\| `execute-plan` Phase 3/{print}' agents/skills/review-staging/SKILL.md > "$TBL"
test "$(wc -l < "$TBL")" -eq 6 || { echo "integration points rows not all found"; exit 1; }
grep -F '`review-confluence-doc`' "$TBL" | grep -qF 'universal review-staging template' || { echo "confluence row not narrowed"; exit 1; }
grep -F '`review-reconciliation`' "$TBL" | grep -qF 'universal review-staging template' || { echo "reconciliation row not narrowed"; exit 1; }
grep -F '`doing-code-review`' "$TBL" | grep -qF 'review_record_selection.py' || { echo "doing-code-review helper note missing"; exit 1; }
if grep -F '`execute-plan` Phase 3' "$TBL" | grep -qF 'review_record_selection.py'; then echo "execute-plan row still claims the helper"; exit 1; fi
if grep -F '`review-confluence-doc`' "$TBL" | grep -qF 'sidecar field + Metadata'; then echo "confluence row still over-claims the twin"; exit 1; fi
if grep -F '`review-reconciliation`' "$TBL" | grep -qF 'sidecar field + Metadata'; then echo "reconciliation row still over-claims the twin"; exit 1; fi
```

Note on the two trailing over-claim sweeps: the phrase `sidecar field + Metadata` is legitimate on other rows (doing-code-review, execute-plan-adjacent producers whose bytes do write the twin); the sweep is scoped per-row through the extracted table so only the two narrowed rows are policed.

### Task 1: Coverage-contract attempts regression fixture and same-family sweep

Files:
- `scripts/validate_review_staging.py`

- [x] `_selftest_coverage_contract` adds the positive check `coverage contract: verdict-yes with attempts telemetry passes`; given a post-constant verdict-ready=yes payload whose coverage outcome is clean, whose attempts list is non-empty (first attempt outcome `failed` with a non-empty `failure_class`, second attempt outcome `complete` with `contributed_coverage: true` and the full material lens set in `lenses`), and whose retry_budget carries positive `per_attempt_timeout_minutes` and `per_worker_max`, expects `validate_coverage_contract` to report zero errors [class: REPOSITORY_TEST]
- [x] `_selftest_coverage_contract` adds the negative check `coverage contract: genuine verdict and outcome mismatch still fails with attempts present`; given the same fixture shape with coverage outcome `failed` against verdict `ready=yes`, expects at least the verdict cross-check error naming the coverage-level outcome (not any attempt's) [class: REPOSITORY_TEST]
- [x] Mutation probe (observed set recorded): insert `outcome = attempt_outcome` on the line after the `attempt_outcome = attempt.get("outcome")` assignment inside the attempts loop, run `python3 scripts/validate_review_staging.py --selftest`, and expect the new positive check to print a FAIL line on stderr with the selftest exiting non-zero; authoring-time baseline with today's checks: zero checks flip (observed set: empty); revert the mutation and expect the selftest green again [class: REPOSITORY_TEST]
- [x] Same-family sweep: walk every `for` loop in `scripts/validate_review_staging.py` with a small AST script that flags a loop-body assignment whose name is read by the enclosing function after the loop; fix each genuine hit with the `attempt_outcome` rename shape or record it as a non-hit; log the per-hit verdict in the task log [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: `python3 scripts/validate_review_staging.py --selftest` exits 0 with both new checks OK (whole-suite state at this task: selftest green; the retention test file does not exist yet and is not run) [class: REPOSITORY_TEST]
- [x] Commit: `test: pin coverage-contract attempts telemetry unshadowed (review staging infra quality task 1)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Retention policy core helper (dry run, pairing, manifest)

Files:
- `scripts/review_retention.py` *(new)*
- `scripts/test_review_retention.py` *(new)*

- [x] `scripts/test_review_retention.py#test_dry_run_deterministic`; given a temp reviews dir with paired and unpaired records dated inside and outside the window, expects two consecutive dry runs to emit byte-identical candidate reports naming directory, filename date, record kind, and pairing, with no document bodies [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_cutoff_by_filename_date_not_mtime`; given a record whose filename date precedes the cutoff but whose mtime is fresh, expects it listed as a candidate, and the mirror case (fresh filename date, old mtime) retained [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_retention_months_default_and_override`; given no facts key, expects a three-calendar-month window; given `review_retention_months: 1` in a temp facts file or `--months 1`, expects the one-month window [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_prune_pairing_aware`; given `--prune` over a manifest-matched candidate set, expects each paired Markdown and `.stats.json` removed as one unit and any unpaired record retained and reported [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_prune_aborts_when_candidates_changed`; given `--prune --from-manifest` whose recorded set no longer matches the directory, expects a non-zero exit and zero deletions [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_manifest_sanitized`; given a completed prune with `--manifest`, expects counts, cutoff, and per-path SHA-256 hashes with no review text or document bodies [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_keep_rules`; given a path under the tmp dir root and an explicit `--keep PATH`, expects both excluded from candidacy, and undated files reported in a retained undated bucket [class: REPOSITORY_TEST]
- [x] Implement the CLI: default dry run, `--prune`, `--from-manifest`, `--manifest`, `--months`, repeatable `--keep`, repeatable `--reviews-dir` override for tests, facts-key read with documented default, never scans `{tmp_dir}` [class: IMPLEMENTATION_REQUIRED]
- [x] Write the test file in the repo's unittest convention (mirror `scripts/test_review_record_selection.py`: stdlib unittest cases calling `unittest.main()`, hermetic temp dirs; the pytest module is not installed in this environment) [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect RED first (the helper module is missing, so the cases error on import) then GREEN: `python3 scripts/test_review_retention.py` exits 0 (whole-suite state: selftest green from Task 1, this file green) [class: REPOSITORY_TEST]
- [x] Commit: `scripts: add review retention dry-run and pairing-aware pruning helper (review staging infra quality task 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: docs-branch deletion transaction and lifecycle wiring

Files (the two script paths this task edits are created by Task 2 and stay listed there; the checklist bullets name the subcommand and test additions):
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `README.md`

- [x] `scripts/test_review_retention.py#test_docs_branch_transaction_records_explicit_deletes`; given a temp repo with a `docs` branch tracking pruned paths, expects the `docs-branch-commit` subcommand to commit the deletions on the docs branch through a temporary worktree (never checking out the docs branch in the live checkout), verify the commit removed the paths, then remove the live shadow files [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_docs_branch_transaction_aborts_on_change`; given the candidate set changed between the manifest and the transaction, expects an abort before any mutation on either branch or the live tree [class: REPOSITORY_TEST]
- [x] `scripts/test_review_retention.py#test_docs_branch_absent_skips_reported`; given a repo without the docs branch, expects the docs-branch leg reported as skipped with the live tree untouched, while the live-side pairing rules still apply through the manifest gate [class: REPOSITORY_TEST]
- [x] Implement `docs-branch-commit` (default branch `docs`, `--docs-branch` override) building on the docs-branch skill's explicit-delete rule: only paths removed in the latest docs commit are dropped from sync restore, so the transaction's commits are what make a prune durable [class: IMPLEMENTATION_REQUIRED]
- [x] `agents/skills/review-staging/SKILL.md` Documentation paths section: document the `review_retention_months` key and one helper reference sentence [class: IMPLEMENTATION_REQUIRED]
- [x] `agents/skills/review-loop/SKILL.md`: one sentence in the `## Staging doc (required every round)` section pointing at `scripts/review_retention.py` (dry run first, pairing-aware) as the pruning path for records past the retention window [class: IMPLEMENTATION_REQUIRED]
- [x] `agents/skills/docs-branch/SKILL.md`: one sentence near the explicit-deletes rule naming the retention helper's `docs-branch-commit` as a sanctioned producer of explicit-delete commits [class: IMPLEMENTATION_REQUIRED]
- [x] `README.md` script table: add the `scripts/review_retention.py` row (one line: retention dry-run report and pairing-aware pruning for review artifacts) [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: full retention test file green including the three new cases (whole-suite state: selftest green, retention unittest green) [class: REPOSITORY_TEST]
- [x] Commit: `scripts+skills: retention docs-branch transaction and lifecycle wiring (review staging infra quality task 3)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Synthesis-time hard gates checklist and confidence hint

Files:
- `agents/skills/review-staging/SKILL.md`
- `scripts/validate_review_staging.py`

- [x] Insert the H2 section `## Synthesis-time hard gates` between `## Severity and ordering` and `## Output discipline` listing exactly these seven obligations (one to one with the section greps in Validation Commands): (1) the closed confidence enum `hypothesis` / `strong-evidence` / `verified`, with the discard reason codes and the `review_mode` enum named in the same item's sentence; (2) kebab-case `risk_signals` tags; (3) the per-worker finding budget with overflow mechanics (extras go to the sidecar overflow list, not the findings conservation set); (4) the `#### F<N>.` block shape with `- **Severity**:` and `- **Blocking**:` bullets and severity groups in Critical, High, Medium, Low order; (5) the freshness Metadata lines required on or after `EXTENDED_SIDECAR_MIN_DATE`; (6) the post-fix Witness ledger requirement; (7) the fence-stripping note (extracting a plan's Validation Commands bash block must strip the fence lines or bash wedges inside a command substitution) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the confidence-enum validation error to append the remediation phrase `map to the closed confidence enum (hypothesis, strong-evidence, verified); do not downgrade`; keep any selftest assertions pinned to that message in sync in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: `python3 scripts/validate_review_staging.py --selftest` exits 0 and `python3 scripts/test_review_retention.py` exits 0 (whole-suite state: both green; the seven section greps in Validation Commands pass) [class: REPOSITORY_TEST]
- [x] Commit: `skills: synthesis-time hard gates checklist and confidence remediation hint (review staging infra quality task 4)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Date-fenced reduced validator path and panel-shape conservation

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`

- [x] Add `PANEL_PROFILE_MAX_DATE = "2026-09-19"` beside `EXTENDED_SIDECAR_MIN_DATE`; a record whose date (staging filename date, falling back to the sidecar `date` field) is on or before it validates under the reduced path [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the reduced path as a single early branch in the hard-mode entry: run only the anti-stub core, which is (a) the Markdown and sidecar pair parses, (b) a `## Metadata` section and a `## Findings` section exist in the Markdown (heading-text PREFIX match for the Findings leg, so the suffixed era headings witnesses carry, for example `## Findings (zero blocking)`, count as present; the Metadata leg uses the same prefix principle), (c) the sidecar carries a verdict, (d) the sidecar's counts agree with its own findings array length when both are present, and (e) finding conservation by document order over every recognized finding block in the WHOLE document, the Findings section plus round-append sections (this leg does not go through the Findings-section extractor, which stops at the next `## ` heading and would miss round-append blocks); every other existing or future gate runs in warning mode for in-window records and never contributes to the exit code [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the finding-block parser and splitter with opt-in recognition of the panel header shapes `### N. <title> (Severity)` and `### R<N>-F<M>. <title> (Severity)` (severity from the parenthesized suffix; the keyword defaults off so current-format parsing is byte-for-byte unchanged) and thread it at the call sites the conservation leg uses, so header-shaped panel records get a real whole-document conservation check inside the reduced path [class: IMPLEMENTATION_REQUIRED]
- [x] In the reduced path, when the Findings section parses into zero recognized blocks while the sidecar lists findings, report the unparsed conservation leg as a warning (the pipe-table era layout), never an error [class: IMPLEMENTATION_REQUIRED]
- [x] Selftest check `panel profile: witnessed header-shape record on or before 2026-09-19 passes --hard`; given a staged fixture derived from the witnessed record's real shape (`### 1.` through `### 5.` blocks under `## Findings` plus `### R2-F1.` through `### R2-F4.` blocks under a `## Round 2 (r2)` section, Metadata and Findings sections present, sidecar verdict and counts matching all nine findings), expects `--hard` to exit 0 with whole-document conservation enforced [class: REPOSITORY_TEST]
- [x] Selftest check `panel profile: phase3-shape pipe-table record passes under the reduced path`; given a staged fixture with a version-1 sidecar, a suffixed `## Findings (zero blocking)` heading (the witnessed era shape), and pipe-table finding rows dated in-window, expects `--hard` to exit 0 with the unparsed conservation leg reported as a warning [class: REPOSITORY_TEST]
- [x] Selftest check `panel profile: both shapes after the window still fail`; given both fixtures re-dated after the window, expects each to fail its current-contract error family [class: REPOSITORY_TEST]
- [x] Selftest check `panel profile: a stub in-window record still fails the anti-stub core`; given an in-window record missing its Metadata or Findings section or its sidecar verdict, expects `--hard` to exit non-zero [class: REPOSITORY_TEST]
- [x] Selftest check `panel profile: count agreement still enforced when parseable`; given an in-window header-shape fixture whose sidecar carries one more finding than the Markdown headers, expects a conservation error [class: REPOSITORY_TEST]
- [x] Extend the historical compatibility paragraph in `agents/skills/review-staging/SKILL.md`: the reduced path, the fence constant, the anti-stub core, and the warning-not-error rule for everything else, with the explicit note that the record date alone selects the path [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: selftest exits 0 including the five profile checks, retention unittest file still green (whole-suite state: all green) [class: REPOSITORY_TEST]
- [x] Commit: `validator: date-fenced reduced path and panel-shape conservation for historical staging records (review staging infra quality task 5)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Integration Points row accuracy

Files:
- `agents/skills/review-staging/SKILL.md`

- [x] Narrow the `review-confluence-doc` and `review-reconciliation` rows to the rfc-design phrasing: declare the sidecar `record_kind` field and attribute the Metadata twin to the universal review-staging template [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the record-selection-helper claim from the `execute-plan` Phase 3 row (no execute-plan byte wires it); keep the staging path pattern and statistics sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Add the helper note to the `doing-code-review` row: its Step 1 review-artifact preflight (item 4) mandates `scripts/review_record_selection.py select` before workers launch [class: IMPLEMENTATION_REQUIRED]
- [x] Verify every edited row against the consumer's own bytes (search each consumer skill for `review_record_selection` and for its `record_kind` producer line) and record the per-row evidence in the task log [class: REPOSITORY_TEST]
- [x] Run, expect GREEN: the Integration Points row greps in Validation Commands pass; selftest and the retention unittest file stay green (whole-suite state: all green) [class: REPOSITORY_TEST]
- [x] Commit: `skills: integration points row accuracy for record kind twin and selection helper (review staging infra quality task 6)` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Final validation sweep

Files:
- none (verification only; commit only if the sweep surfaces residue)

- [x] Run the whole `## Validation Commands` block top to bottom and record each command's outcome in the task log (whole-suite state: every command exits 0) [class: REPOSITORY_TEST]
- [x] Negated residue sweep over the touched skills: no remaining `sidecar field + Metadata` over-claim on the two narrowed rows and no retrofit-script language introduced by this plan (the plan's own bytes are the checker literal for these phrases and are excluded from the sweep) [class: REPOSITORY_TEST]
- [ ] Commit only if the sweep fixed residue: `docs: review staging infra quality final sweep (task 7)` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-19-review-staging-canonical-pattern-retrofit.md: disposition folded into 2026-09-22-review-staging-infra-quality.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-19-review-staging-integration-points-row-accuracy.md: disposition folded into 2026-09-22-review-staging-infra-quality.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md: disposition folded into 2026-09-22-review-staging-infra-quality.md (2026-09-25); per-item file deleted.
