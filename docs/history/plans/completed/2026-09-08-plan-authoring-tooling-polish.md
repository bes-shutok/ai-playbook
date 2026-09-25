# Plan: plan-authoring tooling polish (3+1 backlog items)

Backlog origins (scope of record; stay in place until this plan completes):
- docs/history/backlog/2026-09-07-plan-review-scope-path-category-validation.md (Medium, behavioral)
- docs/history/backlog/2026-09-07-plans-233-restatement-governance.md (Low)
- docs/history/backlog/2026-09-07-plans-confidence-gate-plan-execution-checks.md (Low)
- docs/history/backlog/2026-09-08-validation-nomatch-rc2-hardening.md (Info, rides as Task 4)

## Terms

- **Readiness gate**: `scripts/plan_readiness.py`; the fail-closed validator that `execute-plan` and `done` call on a saved plan.
- **Decision-points trailer**: the plain `Decision points requiring a grill:` line inside `## Assumptions`; gated by `decision_marker_problem` since 2026-09-08.
- **Review Scope category gate**: the new mechanical probe this plan adds (Task 1); validates path categories inside a plan's global `## Review Scope` section.
- **Sidecar date exemption**: the trailer-gate rule that a missing, blank, or malformed sidecar `date` field exempts a plan from a date-gated probe; reused verbatim by the new gate.
- **Restatement governance**: the ownership rule (Task 3) deciding which surface owns the trailer acceptance-mechanics prose.
- **RED-today proof**: executing a sweep against the current tree at authoring time and recording that it fires before the fix lands.

## Assumptions

- assume the Review Scope category gate is time-gated like the trailer gate with `REVIEW_SCOPE_MIN_DATE = "2026-09-09"`; basis: the `DECISION_MARKER_MIN_DATE` precedent (no retrofit of already-certified plans; plans whose latest round is dated 2026-09-08 stay exempt).
- assume path-kind classification uses generic module-constant suffix tables (implementation: `.py .java .kt .kts .ts .tsx .js .jsx .go .rb .rs .c .cc .cpp .h .hpp .cs .php .sh .bash .sql .yaml .yml .json .toml .xml .gradle`; documentation: `.md .rst .adoc .txt`), never one repository's layout; basis: backlog requirement "must not encode one consumer repository's file suffixes or layout as the only valid model" (r1-fix deviation 2026-09-09: the shipped table drops the pure-config extensions (.yaml .yml .json .toml .xml .gradle), comment r1 F3 in scripts/plan_readiness.py; doc-pipeline config under Documentation passes).
- assume the task-Files coverage check passes when the path appears anywhere in the `## Review Scope` section (explicit category list, plan-related-extension prose, or out-of-scope list) and flags only a path absent from the entire section; basis: backlog acceptance criterion "does not reject valid extension-only documentation coverage".
- assume the plans-facts r6 corrections land as in-place edits plus a dated errata note in the completed plan document; the backlog's "executing session's review round certifies the amended digest" clause is void because that execution completed 2026-09-07 (main 3056efe) without the fold; basis: the backlog item's own exclusion line ("No changes to the shipped skill or script content") plus git history.
- assume the rc2 hardening rides in this plan as Task 4 rather than dropping to a direct fix; basis: standing pre-authorization and this plan already owning the validation-tooling surfaces.

Decision points requiring a grill: review-scope gate home = a `scripts/plan_readiness.py` probe with sidecar-date-gated wiring (receipt: standing pre-authorization, task prompt 2026-09-08); restatement governance = r2-refined Direction 1, the plans template line is the author-facing source of truth and sibling docs point instead of restating (receipt: standing pre-authorization, task prompt 2026-09-08, resolving the r2-vs-r3 contradiction in the backlog item); plans-facts r6 residuals = in-place errata on the completed plan document (receipt: backlog scope exclusion line, item text 2026-09-07); rc2 item included as Task 4 (receipt: standing pre-authorization, task prompt 2026-09-08).

## Gist & Examples

Four backlog items, one plan: three tighten the plan-authoring toolchain and one rides along.

**Review Scope category gate (Task 1, the only behavioral change).** Today the readiness gate checks review artifacts, sidecars, digests, verdicts, and the decision-points trailer, but never checks WHERE a plan lists its own file paths. An author can place `src/Foo.java` under the `Documentation:` block of `## Review Scope`; the Markdown stays valid, completeness greps still pass, and reviewers read a wrong category mapping.

- **Before (today):** a plan lists production and test paths under `**Documentation:**`. `plan_readiness.py` exits 0 (everything else about the plan is fine); reviewers treat implementation files as documentation.
- **After (this plan):** the same plan bytes fail the gate with a named reason that reports the path, its declared category, and the expected category. A plan with documentation paths under `Documentation:` still passes. Duplicate paths across categories fail. A task `Files:` path absent from the whole Review Scope inventory fails. A documentation path covered only by the plan-related-extension policy passes.

The gate is forward-looking (sidecar-date gated, `REVIEW_SCOPE_MIN_DATE = "2026-09-09"`) so no already-certified plan retroactively fails. The same rule is referenced by the plans authoring workflow (Task 2) and the review-plan validation checklist (Task 2); the validator is the single source of truth.

**Restatement governance (Task 3).** Two review rounds gave contradictory directions for the plans template line that restates the trailer acceptance mechanics (plans SKILL.md line 256: r2 said document them there; r3 said compress to a pointer). This plan settles the governance: the template line IS the author-facing source of truth for acceptance mechanics (authors must be able to see the vocabulary where they write); the validator owns enforcement and points back; sibling skill documents (review-plan) must LINK to the owner, never restate the mechanics. Applied effect: review-plan's Integration Points clause loses its restated sidecar-date exemption mechanics and gains a pointer.

**plans-facts r6 residuals (Task 5).** The completed plans-facts plan carries three valid but unfixed review residuals in its own execution checks: the Task 8 scope-integrity equality omits the plan document and its review artifacts (and does not fence the done commit-all path), Task 1's RED-today sweep bullet sits after the edits it must precede, and the em-dash command lists a `.py` operand the scanner skips unless `CHECK_NO_EM_DASH_ALL=1`. The corrections land in the completed document as in-place edits with a dated errata note; execution is already finished, so the document is corrected as a record, not re-certified.

**rc2 hardening (Task 4).** The forbidden-match recipe in plans Validation rule 10 treats any non-zero grep exit as clean once a `test -f` pre-check passes; an unreadable file (rc 2) silently passes as "no match". Rule 10 gains the three-way exit split: rc 0 = forbidden match (fail), rc 1 = clean pass, rc >= 2 = tool error (fail).

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/plan_readiness.py --selftest` green including the new `selftest#review_scope/` fixture family (the fixture family is every selftest#review_scope/ arm pinned in Validation Commands; 17 at record-fix time; the pins are the count of record), every arm a dedicated fail-closed check with a distinctive multi-word span.
- single sourcing: the category rule is enforced in exactly one place (the validator); plans and review-plan reference it by name; no restated mechanics survive in review-plan (flattened sweep silent post-edit).
- project agnosticism: the gate and all fixtures contain no repository names, ticket identifiers, or consumer-repo layout assumptions; suffix tables are generic module constants.
- hygiene: no-em-dash scan over the prose and docs operands (the `.py` operand is deliberately dropped from the sweep, practicing Task 5's F3, and covered by the selftest plus dedicated pins instead) and public-hygiene scan exit 0 over every touched file.

**Done when:**
- All tasks checked; full Validation Commands block exits 0 from a clean shell at the repo root.
- Scope integrity: with `<base>` recorded before Task 1's commit, `git log --format:'' --name-only <base>..HEAD | sort -u` equals this plan's declared artifact set (union of task Files lists, this plan document, this plan's review artifacts); any extra path is a defect fixed before completion.

**Ship when:** prose only; no external or human-owned conditions. The readiness gate's own deployment to `~/.ai-playbook/scripts` copies is already symlink-wired and outside this plan's scope.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`

**Documentation:**
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `docs/plans/completed/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md`
- `docs/plans/2026-09-08-plan-authoring-tooling-polish.md` *(new; this plan)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; shared sibling module, no contract change intended (only the existing compat handshake applies)
- `README.md`; no skill catalog entry (name, path, trigger, usage) changes in this plan
- `projects/.ai-playbook/development_lessons.md`; lesson capture belongs to the done flow, not to plan tasks

## Validation Commands

```bash
set -e
cd "$(git rev-parse --show-toplevel)"
P=agents/skills/plans/SKILL.md
R=agents/skills/review-plan/SKILL.md
V=scripts/plan_readiness.py
E=docs/plans/completed/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md
S=docs/plans/2026-09-08-plan-authoring-tooling-polish.md

# Mechanical gates (behavioral truth). The em-dash sweep deliberately drops
# the .py operand (r1 F1): plan_readiness.py carries legacy em-dashes in
# comments this plan never touches, and CHECK_NO_EM_DASH_ALL=1 would make the
# sweep fail forever on untouched frozen content (rule 28). The validator is
# covered by its selftest and the dedicated pins instead.
python3 scripts/plan_readiness.py --selftest
python3 scripts/validate_review_staging.py --selftest
bash scripts/check-no-em-dash.sh file "$P" "$R" "$E" "$S"
bash scripts/scan-public-hygiene.sh

# Task 1 pins: category gate constant, probe, wiring, fixture family
grep -qF 'REVIEW_SCOPE_MIN_DATE = "2026-09-09"' "$V" || { echo "MISS: min-date constant"; exit 1; }
grep -qF "def review_scope_problem(plan_text: str) -> str | None" "$V" || { echo "MISS: probe entry point"; exit 1; }
grep -qF "review_scope_problem(plan_text)" "$V" || { echo "MISS: evaluate_readiness wiring"; exit 1; }
grep -qF "selftest#review_scope/doc_under_documentation_ok" "$V" || { echo "MISS: valid-docs fixture"; exit 1; }
grep -qF "selftest#review_scope/implementation_under_documentation" "$V" || { echo "MISS: mismatch fixture"; exit 1; }
grep -qF "selftest#review_scope/duplicate_across_categories" "$V" || { echo "MISS: duplicate fixture"; exit 1; }
grep -qF "selftest#review_scope/task_file_missing_from_inventory" "$V" || { echo "MISS: coverage fixture"; exit 1; }
grep -qF "selftest#review_scope/extension_only_coverage_ok" "$V" || { echo "MISS: extension fixture"; exit 1; }
grep -qF "selftest#review_scope/sidecar_date_missing_exempt" "$V" || { echo "MISS: date-missing exemption fixture"; exit 1; }
grep -qF "selftest#review_scope/sidecar_date_below_min_exempt" "$V" || { echo "MISS: below-min exemption fixture"; exit 1; }
# r1 fix-round arms (2026-09-09, 567f180) plus r2 fix-round arms
grep -qF "selftest#review_scope/template_files_above_checkboxes_ok" "$V" || { echo "MISS: checkbox-bleed fixture"; exit 1; }
grep -qF "selftest#review_scope/inline_files_line_ok" "$V" || { echo "MISS: inline-files fixture"; exit 1; }
grep -qF "selftest#review_scope/annotated_implementation_under_documentation" "$V" || { echo "MISS: annotated mismatch fixture"; exit 1; }
grep -qF "selftest#review_scope/annotated_task_path_coverage_ok" "$V" || { echo "MISS: annotated coverage fixture"; exit 1; }
grep -qF "selftest#review_scope/doc_config_under_documentation_ok" "$V" || { echo "MISS: doc-config fixture"; exit 1; }
grep -qF "selftest#review_scope/spec_dir_doc_under_documentation_ok" "$V" || { echo "MISS: spec-dir fixture"; exit 1; }
grep -qF "selftest#review_scope/test_path_under_documentation" "$V" || { echo "MISS: test-path fixture"; exit 1; }
grep -qF "selftest#review_scope/substring_superstring_not_inventory" "$V" || { echo "MISS: superstring fixture"; exit 1; }
grep -qF "selftest#review_scope/nested_subbullet_not_path_ok" "$V" || { echo "MISS: nested-subbullet fixture"; exit 1; }
grep -qF "selftest#review_scope/directory_scope_entry_covers_ok" "$V" || { echo "MISS: directory-scope fixture"; exit 1; }
grep -qF "selftest#review_scope/directory_slash_polarity_ok" "$V" || { echo "MISS: slash-polarity fixture"; exit 1; }
grep -qF "selftest#review_scope/bare_token_boundary_not_covered" "$V" || { echo "MISS: bare-token boundary fixture"; exit 1; }

# Task 2 pins: both authoring and review workflows reference the validator rule
grep -qF "Path-category gate (mechanical)" "$P" || { echo "MISS: plans authoring rule"; exit 1; }
grep -qF "review_scope_problem" "$P" || { echo "MISS: plans rule names the validator"; exit 1; }
grep -qF "Review Scope path-category audit" "$R" || { echo "MISS: review-plan audit item"; exit 1; }
grep -qF "review_scope_problem" "$R" || { echo "MISS: review-plan item names the validator"; exit 1; }

# Task 3 pins: governance sentence up, sibling restatement gone
grep -qF "author-facing source of truth for trailer acceptance mechanics" "$P" || { echo "MISS: governance sentence"; exit 1; }
grep -qF "owned by scripts/plan_readiness.py" "$R" || { echo "MISS: review-plan pointer"; exit 1; }
# RED-today proven at authoring (2026-09-08: the restated mechanics phrase occurs
# exactly once in $R). The sweep targets ONLY $R; this plan quotes the phrase but
# is never a sweep operand. Flatten first: the clause can line-wrap.
if tr '\n' ' ' < "$R" | tr -s ' ' | grep -qF "sidecar date field is dated on or after"; then echo "STALE: review-plan still restates sidecar-date exemption mechanics"; exit 1; fi

# Task 4 pin: three-way exit split in the forbidden-match recipe rule
grep -qF "fail on rc >= 2 as a tool error" "$P" || { echo "MISS: rc split rule"; exit 1; }

# Task 5 pins: errata note, corrected Task 8 invariant, corrected em-dash command
grep -qF "Errata (2026-09-08" "$E" || { echo "MISS: errata note"; exit 1; }
grep -qF "this plan document, and this plan's review artifacts" "$E" || { echo "MISS: corrected Task 8 invariant"; exit 1; }
grep -qF '"$D" "$R" docs/plans/2026-09-07' "$E" || { echo "MISS: corrected em-dash command"; exit 1; }
# RED-today proven at authoring (2026-09-08: the old invariant span occurs
# exactly once in $E). Targets ONLY $E.
if grep -qF "must equal the union of the task Files lists" "$E"; then echo "STALE: old Task 8 equality invariant remains"; exit 1; fi
```

### Task 1: Review Scope category gate in the readiness validator

Files:
- `scripts/plan_readiness.py`

- [x] Record the current HEAD sha as `<base>` in the session notes before this task's commit (the final task's scope-integrity check uses it).
- [x] Add module constants beside `DECISION_MARKER_MIN_DATE`: `REVIEW_SCOPE_MIN_DATE = "2026-09-09"`, plus `REVIEW_SCOPE_IMPLEMENTATION_SUFFIXES` and `REVIEW_SCOPE_DOC_SUFFIXES` tuples with the generic values listed in Assumptions, each with a comment stating they are the generic default and must not encode one consumer repository's layout. (r1-fix deviation 2026-09-09: the shipped tables deviate from the Assumptions list per the r1 F3 receipt above; see the constants' own comment in scripts/plan_readiness.py.)
- [x] RED: add the selftest fixture arms below to the selftest dispatcher, mirroring the `selftest#decision_marker/` family builders (gate-level arms build a minimal plan, review Markdown, and sidecar in a temp reviews dir exactly as the decision-marker arms do). Run `python3 scripts/plan_readiness.py --selftest`; expect RED on the three violation arms (they fail because `review_scope_problem` and its wiring do not exist yet); the four pass-arms are vacuously green until the wiring exists and only become meaningful probes after the implement step.
  - `selftest#review_scope/doc_under_documentation_ok`; given a valid minimal plan whose Review Scope lists `docs/guide.md` under `**Documentation:**` and a conforming sidecar dated 2026-09-09, expects gate exit 0.
  - `selftest#review_scope/implementation_under_documentation`; given the same shape but `src/service.py` under `**Documentation:**`, expects exit 1 with a reason naming the path, the declared category, and the expected category.
  - `selftest#review_scope/duplicate_across_categories`; given `src/service.py` listed under both `**Production code:**` and `**Tests:**`, expects exit 1 with a duplicate-path reason.
  - `selftest#review_scope/task_file_missing_from_inventory`; given a `### Task` section whose `Files:` lists `src/missing.py` and a Review Scope section that never mentions it, expects exit 1 with an omitted-from-inventory reason.
  - `selftest#review_scope/extension_only_coverage_ok`; given a task `Files:` path that appears only in the plan-related-extension prose of the Review Scope section, expects exit 0.
  - `selftest#review_scope/sidecar_date_missing_exempt`; given a plan whose Review Scope lists `src/service.py` under `**Documentation:**` but whose sidecar carries NO `date` field, expects exit 0 (the malformed-or-missing-date exemption applies; this arm proves the date guard exists, since the violation-only arms cannot).
  - `selftest#review_scope/sidecar_date_below_min_exempt`; given the same violation plan but a sidecar dated 2026-09-08 (below the minimum), expects exit 0 (no retrofit of already-certified plans).
  - Fixture plans dated on or after 2026-09-08 (the shipped `DECISION_MARKER_MIN_DATE`, which is earlier than this gate's own 2026-09-09 minimum) also activate the decision-marker gate, so every fixture plan text above, including the below-min exemption arm, carries a plain `Decision points requiring a grill: none remain.` line inside its `## Assumptions` section; otherwise the new arms fail on the trailer gate instead of exercising the category gate.
- [x] Implement `def review_scope_problem(plan_text: str) -> str | None` beside `decision_marker_problem`, reusing `_strip_fences` and `md_section`: extract the `## Review Scope` section; parse explicit category blocks (a `**<label>:**` line starts a block; subsequent `- ` list items belong to it; a label containing `Out of scope` is not a category block); then (a) flag an implementation-suffix or test-detectable path (path segment `test`, `tests`, or `spec`) listed under a label matching `documentation` (case-insensitive), with a reason reporting path, declared category, and expected category (`Tests` for test-detectable, `Production code` otherwise); (b) flag a path listed under two different category blocks; (c) extract every `Files:` list path from `### Task` sections (fences stripped) and flag one that appears nowhere in the Review Scope section text; the extraction reads ONLY the list items in the `Files:` block of each task section, from the line starting `Files:` until the first line that is neither a `- ` item nor blank, so checkbox bullets elsewhere in the task are never collected as paths; return the FIRST problem, `None` otherwise.
- [x] Wire into `evaluate_readiness` after the trailer block as condition 7 with the same sidecar-date guard (`re.fullmatch` on `YYYY-MM-DD` and `>= REVIEW_SCOPE_MIN_DATE`) and a named reason embedding `review_scope_problem`'s output plus the round and date, mirroring the trailer reason shape. Decode sharing without widening the decode failure (r2 F2): do NOT hoist the `plan_text` decode above both date guards unconditionally, or an undecodable plan whose round is date-exempt would newly fail; instead decode once only when at least one of the two date guards fires (keep the trailer block's existing decode-failure reason text for that case) and pass the decoded text to whichever probe runs.
- [x] Run `python3 scripts/plan_readiness.py --selftest`; expect GREEN (all arms, old and new). Run the gate once against a copy of this plan with a synthetic dated sidecar to smoke the wiring; expect exit 0 for this plan's own Review Scope shape.
- [x] Commit (only the file listed above): `validator: review-scope path-category gate`

### Task 2: single-source the rule into authoring and review workflows

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] In plans SKILL.md, in the **Review Scope** authoring rules area (after the partially-in-scope/freeze guidance paragraph), insert exactly: `**Path-category gate (mechanical):** the readiness validator enforces Review Scope path categories (scripts/plan_readiness.py, review_scope_problem): implementation and test paths under a Documentation category, duplicates across category blocks, and task Files paths absent from the Review Scope inventory each fail the gate; the validator is the single source of truth for this rule, so this section must not restate its mechanics.` For plans reviewed on or after 2026-09-09 the gate is date-gated like the trailer gate. (r1 review fix 2026-09-09, 567f180: the shipped sentence is the compressed pointer form; the anchor strings this bullet pins are retained.)
- [x] In review-plan SKILL.md, in the `Each worker receives:` list after item 8 (Checklist inclusion backstop), insert item 9 exactly: `9. **Review Scope path-category audit**: run the readiness validator's Review Scope category rule (scripts/plan_readiness.py, review_scope_problem) over the plan under review; implementation or test paths under a Documentation category, duplicates across category blocks, and task Files paths absent from the Review Scope inventory are findings (blocking when the misplacement would change reviewer behavior, e.g. production paths read as documentation).` (r1 review fix 2026-09-09, 567f180: the shipped sentence is the compressed pointer form; the anchor strings this bullet pins are retained.)
- [x] Run the Task 2 pins from Validation Commands; expect GREEN.
- [x] Commit (only the files listed above): `skills: review-scope category rule single-sourced in validator`

### Task 3: restatement governance for acceptance-mechanics prose

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] In plans SKILL.md, in `## Plan Format`, insert directly AFTER the line `Every plan follows this exact structure; no variations:` and BEFORE the opening fence of the plan-template block (the governance sentence is skill guidance, not template content, so it must sit outside the fence; r1 F2): `The template block below carries the author-facing source of truth for trailer acceptance mechanics (the bracketed Assumptions line inside it); the readiness validator (scripts/plan_readiness.py, decision_marker_problem) owns enforcement and points here, and sibling skill documents must link to one of these two surfaces instead of restating the mechanics.` (Decision receipt: standing pre-authorization 2026-09-08; resolves the r2-vs-r3 contradiction in docs/history/backlog/2026-09-07-plans-233-restatement-governance.md in r2's favor for the author-facing surface.)
- [x] In review-plan SKILL.md, in the plan readiness gate Integration Points clause, replace the sentence from `The gate additionally requires the plan's decision-points trailer` through `blocking documentation finding.` with exactly: `The gate additionally requires the plan's decision-points trailer under the sidecar-date rule owned by scripts/plan_readiness.py (the DECISION_MARKER_MIN_DATE comment in evaluate_readiness owns the exact date and exemption semantics); treat a missing or unresolved trailer in such a plan as a blocking documentation finding.` (r1+r2 review fixes 2026-09-09, 567f180+dac29c6: the shipped parenthetical names the DECISION_MARKER_MIN_DATE constant and the evaluate_readiness step-6 comment as joint owners; the pinned anchor "owned by scripts/plan_readiness.py" is retained.)
- [x] RED-today proof: run the Task 3 flattened sweep over `$R` BEFORE this edit and record that it fires (authoring-time verification 2026-09-08: the restated mechanics phrase occurs exactly once in review-plan SKILL.md). After the edit, expect the sweep silent.
- [x] Run the Task 3 pins; expect GREEN.
- [x] Commit (only the files listed above): `skills: acceptance-mechanics prose single-owner governance`

### Task 4: forbidden-match rc-split hardening in the plans template rule

Files:
- `agents/skills/plans/SKILL.md`

- [x] In Validation Commands authoring rule 10, replace the sentence `The hole inverts for forbidden-match sweeps: \`if grep ...; then fail\` treats grep's exit 2 (missing file) as "no forbidden match"; pre-check \`test -f\` on every swept path.` with: `The hole inverts for forbidden-match sweeps: a \`if grep ...; then fail\` recipe treats every non-zero exit as clean, so a pre-check \`test -f\` on every swept path is not enough; the recipe must capture the grep exit status and fail on rc >= 2 as a tool error (unreadable file, ELOOP, missing binary), so only rc 1 passes and rc 0 fails as a forbidden match; this is the same three-way split the \`expect_rg_no_match\` helper implements for rg.` Keep the surrounding sentences and the rg helper example unchanged; the tail clause names the existing helper so the sentence extends rather than duplicates it (r1 F5).
- [x] Run the Task 4 pin; expect GREEN. (Origin: docs/history/backlog/2026-09-08-validation-nomatch-rc2-hardening.md; template-level, no instance plans touched.)
- [x] Commit (only the file listed above): `skills: forbidden-match greps fail on tool-error exit codes`

### Task 5: plans-facts r6 execution-check residuals as errata

Files:
- `docs/plans/completed/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md`

- [x] Directly under the plan title, add the note: `> Errata (2026-09-08, from docs/history/backlog/2026-09-07-plans-confidence-gate-plan-execution-checks.md): three r6 review residuals are folded below as in-place corrections. Execution completed 2026-09-07 without these corrections, so the backlog's certify-the-amended-digest clause is void; the corrections fix the document as a record, they do not re-open or re-certify the completed execution.`
- [x] F2, Task 1 ordering: split the combined pins/sweep bullet into two bullets and reorder, so the first bullet reads `- [x] Run the stale-tier sweep against the PRE-EDIT tree once first to record it fires (RED-today proof); expect it to fire.` placed ABOVE the edit bullets, and the second (last) bullet reads `- [x] Run the dedicated pins for this task (dividers, materiality test, carve-out, regression cases) in the fail-closed form of Validation Commands, then re-run the stale-tier sweep post-edit; expect both GREEN and the sweep silent.` The `[x]` marks stay (historical completion state is preserved; the errata note explains the edit).
- [x] F1, Task 8 invariant: replace `must equal the union of the task Files lists; any extra path in this plan's commit history is a defect to fix before completion` with `must equal the plan's declared artifact set: the union of the task Files lists, this plan document, and this plan's review artifacts; the done commit-all path must be fenced by enumerating any additional paths the done step commits; any extra path in this plan's commit history is a defect to fix before completion`.
- [x] F3, em-dash command: drop the `.py` operand from the em-dash line's scanner invocation (the backlog's alternative arm; the all-extensions prefix would fail forever on legacy em-dashes in untouched validator comments) so it reads `bash scripts/check-no-em-dash.sh file "$P" "$G" "$D" "$R" docs/plans/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md`.
- [x] Run the Task 5 pins and the Task 5 negative sweep from Validation Commands; expect GREEN and silent respectively (the sweep is RED-today: authoring-time verification 2026-09-08 recorded the old invariant span occurring exactly once).
- [x] Commit (only the file listed above): `plans: fold r6 execution-check residuals into completed plans-facts doc`

### Task 6: final validation and scope integrity

Files: none new (validation only; fixes commit to the owning file)

- [x] Run the full Validation Commands block from a clean shell at the repo root; expect exit 0 end to end.
- [x] Verify scope integrity of this plan's own commits: with `<base>` recorded before Task 1's commit, `git log --format:'' --name-only <base>..HEAD | sort -u` must equal the plan's declared artifact set: the union of the task Files lists, this plan document, and this plan's review artifacts; the done commit-all path must be fenced by enumerating any additional paths the done step commits. Any extra path is a defect to fix before completion.
- [x] Commit any validation-driven fixes individually to their owning files; expect none needed.
