# Plan: learn company-wide lesson scope detection

Backlog: `docs/history/backlog/2026-09-09-learn-company-scope-placement.md` (scope of record) plus rider `docs/history/backlog/2026-09-10-learn-company-vs-project-placement-gate.md` (company-versus-project placement gate, same learn/generalize/done skill surface; folded scope of record). No RFC/ticket.
Follow `python_guidelines.md` (shared docs) for the validator script and its tests.

## Terms

- Scope fork (placement fork): `learn` Step 1.2 item 4 decision ladder that routes a generalized lesson to a canonical home; branches (1) universal, (2) ecosystem, (2b) company-wide, (3) user-level corpus, (4) project-specific.
- Company guidelines master: cross-repo company guideline source of truth resolved from the `company_guidelines_master` facts key; canonical, repo mirrors are sync-only.
- Project lessons corpus: the incident repo's `docs/maintenance/development_lessons.md` (project-level numbered lessons).
- Witness: the short concrete incident example a project corpus may retain after the full rule is placed at a broader scope.
- Placement receipt: temporary `learn`-run output stating the selected scope and why each alternative scope was rejected (`learn` Step 1.2 item 5c; wording amended r3, see Task 3 amendment).
- Scope audit: `done` Step 3 item 4a pre-commit check that a newly created or substantially edited project lesson is not a company-wide rule stored only at project level.
- Duplicate full rule: near-verbatim rule body present in both the project lessons corpus and the company guidelines master.
- Residual dependency: the material dependency on the service domain, module contract, repository architecture, or project-only operational behavior that keeps a rule project-specific (fork 4); every fork (4) placement receipt must state it.
- Blocking placement question: a `learn` stop-and-ask raised when a rule's scope is broader than the project but no canonical destination resolves (company-scope rule with no `company_guidelines_master`); the full lesson is never silently written to the project corpus instead.

## Assumptions

- assume the company branch is inserted as fork (2b) and forks (1), (2), (3), (4) keep their numbers and meaning; basis: existing fork-number cross-references in `learn` (Step 1.7 item 6, Step 2 gate, item 4b) and `generalize`, plus the mirror-fan-out cost that `learn` Step 1.2 item 5b puts on renumbering.
- assume the mechanical check is a small repo validator script rather than persisted placement metadata, and the placement receipt stays temporary run output; basis: backlog "Proposed done changes" item 2 ("Prefer a small validator or structured placement metadata over keyword heuristics") and "Proposed learn changes" item 5 ("This receipt can remain temporary").
- assume the validator compares only the project lessons corpus against the company guidelines master; ecosystem-tier and universal-tier files are not swept; basis: backlog scope line and non-goal "Do not copy company guidance verbatim into every project corpus".
- assume runtime deployment of the validator (a per-file symlink under `~/.ai-playbook/scripts/`, per the registry model verified 2026-09-09) is machine-local work outside this plan; `done`'s audit warns and continues when the script is absent, matching the cold-start pattern of `learn` Step 6.6.
- assume a `done` scope-audit stop rides `done`'s existing blocked semantics (release the lock, report blocked with reason); basis: `done` Step 1 learn-block propagation precedent.
- assume tests run via `python3 -m unittest discover -s scripts -p 'test_*.py'`; basis: `scripts/test_execute_plan_runtime.py` convention and the agent-agnostic execute-plan plan.
- assume the rider's residual-dependency statement rides the existing placement receipt (`learn` Step 1.2 item 5c) rather than a new persisted artifact; basis: rider suggested fix "Require the placement record to state the residual dependency" and the receipt-temporary assumption above.
- assume the rider's missing-canonical-destination stop rides `learn`'s existing placement-question semantics (stop and ask the user; `done` propagates the block per its Step 1 precedent) rather than a new error channel; basis: rider suggested fix "report the missing canonical destination as a blocking placement question" and the done blocked-semantics assumption above.
- assume the rider acceptance "a self-test or dry-run reports the selected tier and the evidence used for the decision" is delivered by the placement receipt in the `learn` run output plus this plan's validator tests and Validation probes, with no new dry-run mode; basis: the receipt is by contract the run-output record of the selected scope and why each broader scope was rejected, and `done` already consumes it as evidence.
- assume the rider acceptance "the implementation remains project-agnostic and contains no real identifiers" is delivered by `learn` Step 1.7 redaction plus this plan's em-dash and public-hygiene gates; basis: the existing Done-when hygiene items.
- assume the rider's fixture-phrased routing acceptances (a team or infrastructure ownership rule routes to the company guideline; a service-only domain invariant stays project-specific and records the residual dependency; a cross-project incident that is not company policy routes to the user-level corpus) are delivered as text-obligation probes because `learn` is a prose skill with no executable routing surface; the only executable artifact this plan adds is the duplicate validator, whose fixtures cover the duplicate-detection slice; basis: rounds r1 through r9 accepted the identical acceptance phrasing for the host backlog's equivalent items, and `done`'s pre-commit audit (Task 3) backstops routing at commit time.

Decision points requiring a grill: none remain.

## Gist & Examples

`learn` currently classifies a generalized lesson with a four-way fork: universal coding guidance, ecosystem/language guidance, cross-project user-level corpus, or project-specific corpus. The company tier exists only in later placement tables (Step 2 guideline roles, Step 6 ladder), so the fork itself can stop at "project-specific" for any rule that is not universal across every organization. A rule shared by all company repositories that perform the same kind of work then lands as a full project lesson, and other company repos never discover it.

**Before (today):** a generalized integration rule ("keep the PR title in scope as the PR expands during a config rollout") is captured after an incident in one company repo. The fork asks whether it is universal (no) or project-only (it needs domain context, so yes). The full rule becomes project lesson #N and a pointer goes into that repo's instructions. A sibling company repo with the same integration responsibility re-learns the rule from scratch.

**After (this plan):** the same candidate hits two new gates before fork (4). Item 4a separates the generalized rule from its incident witness. The 4c company-portability gate asks: "Would this rule guide another repository in the same organization that performs the same kind of work, even if its product domain differs?" With a required sibling search of the company guidelines master as evidence, the answer routes the rule to fork (2b): the full rule is written to `company_guidelines_master`, the project corpus keeps at most a concise witness plus a pointer, and repo mirrors sync per the existing Company rule workflow. The learn run emits a placement receipt (selected scope plus why broader scopes were rejected).

`done` gains a matching pre-commit audit (Step 3 item 4a) when the session touched the project lessons corpus: it runs `scripts/check_lesson_scope.py` (a small duplicate-rule validator) and checks the placement receipt.

**Rider fold (backlog 2026-09-10, company-versus-project placement gate):** the rider sharpens the same decision ladder with three additions. First, the placement receipt for a fork (4) placement must state the residual dependency that keeps the rule project-specific; with no residual dependency the full lesson is not written to the project corpus, and the candidate re-routes to fork (2b) or fork (3). Second, a company-scope rule whose `company_guidelines_master` does not resolve (personal repo) raises a blocking placement question instead of silently becoming a full project lesson. Third, the 4c gate names ownership boundaries explicitly: a rule about which team owns which tickets, components, or delivery stages binds sibling repos with the same responsibility, so it is company scope. Example of the first: a rule that survives the portability gates only because of this repo's batch-row accumulation semantics stays in fork (4), and its receipt records that exact dependency. Example of the third: an infrastructure-team-versus-application-team ownership boundary captured in one service repo routes to fork (2b) (full rule in the master, witness pointer in the repo), never a full project lesson.

**Validator example:** project corpus block `## 12. Keep rollout PR titles in sync with scope` whose body matches company master block `## 51. Keep rollout PR titles in sync with scope` near-verbatim (case, whitespace, or numbering differ) produces exit 1 and names both blocks; `done` stops before commit and asks for classification instead of silently committing the narrower placement. A one-line project witness ("see company-guidelines #51") is under the minimum block length and stays clean (exit 0).

**Edge cases that shaped the design:** a temporary session-note-style block sharing topic words with a company rule must not trip keyword matching (the validator compares normalized full-rule bodies, not keywords); a rule duplicated only against a language guidelines file is out of the comparison set (ecosystem tier, not company); an absent company master (personal repo) and an absent corpus are clean cold starts with a warning, matching the `learn` Step 6.6 pattern.

**Rider acceptance coverage map:** company-convention branch before the project-specific branch: Task 2 fork (2b) insert plus the 4c gate, ordered before fork (4). Team or infrastructure ownership rule routes to the company guideline without a full project lesson: Task 2 4c ownership-boundary sentence plus the 2b sibling search of the master. Service-only domain invariant stays project-specific and records the residual dependency: Task 2 5c residual-dependency receipt contract, mirrored in generalize entry 4, audited by `done` (Task 3 placement-evidence check). Cross-project incident that is not company policy routes to the user-level corpus with the family tag: existing fork (3) strict `**Principle:** Family X` tagging plus the 4c negative branch. Witness preserved through a pointer without duplicating the canonical rule: Task 2 item 4a and the validator's short-block floor (Task 1 `test_witness_pointer_clean`, `test_short_identical_body_stays_clean`). Self-test or dry-run reports the selected tier and its evidence: Task 2 item 5c receipt plus the dedicated Validation probes. Project-agnostic implementation with no real identifiers: `learn` Step 1.7 redaction plus the Task 4 em-dash and public-hygiene gates.

## Design Invariants (CR Guard)

- Existing fork numbers (1), (2), (3), (4) and their cross-references keep their meaning; the company branch is additive (2b). No renumbering.
- The validator performs mechanical duplicate detection only; semantic scope judgment stays with the `learn` workflow (backlog done-change 2).
- `done` never moves, rewrites, or duplicates lessons automatically; an unresolved placement stops before commit and asks (backlog done-change 4 and acceptance criteria).
- The learn placement receipt is temporary run output, not a canonical artifact (backlog learn-change 5).
- A fork (4) placement records its residual dependency in the placement receipt; with no residual dependency the full lesson is not written to the project corpus (rider acceptance: service-only invariant keeps its dependency on record).
- A company-scope rule with no resolvable `company_guidelines_master` is a blocking placement question, never a silent full project lesson (rider suggested fix).

## Evaluation Criteria

**Quality dimensions:**
- correctness: `check_lesson_scope.py` flags verbatim and near-verbatim full-rule duplication (case, whitespace, heading numbering normalized), exits 0 on witness pointers and project-only rules, and honors the exit-code contract 0 clean / 1 duplicate / 2 usage error
- test coverage: fixtures cover company-wide, project-specific, ecosystem-specific, and temporary-lesson examples plus duplicate detection, per the backlog acceptance criteria
- maintainability: stdlib-only script; thresholds are named constants in the script; hermetic tests build fixtures in temp dirs
- consistency: `generalize`'s routing-fork mirror claim and the UL corpus lesson 177 See also line are updated in the same change set as the `learn` fork (learn Step 1.2 item 5b); no stale "four-way fork" claim remains in any living file
- rider coverage: each rider acceptance lands in a named task and Validation probe per the coverage map in Gist & Examples; the residual-dependency, blocking-question, and ownership-boundary obligations each have a dedicated probe

**Done when:**
- `python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py'` exits 0
- every obligation probe in Validation Commands exits 0 (learn fork, receipt, witness separation, residual dependency, blocking placement question, ownership boundary; done audit, stop-before-commit, no-residual stop, commit boundary; generalize mirror incl. its residual-dependency record)
- the stale-claim sweep over `learn`, `generalize`, and the UL corpus finds zero "four-way fork" hits
- em-dash scan and public-hygiene scan exit 0 over the changed files

**Ship when:**
- the validator is reachable at `~/.ai-playbook/scripts/check_lesson_scope.py` (per-file symlink deployment) on machines that run `done`; until then the audit warns and continues on the missing script by design.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_lesson_scope.py` *(new)*
- `agents/skills/learn/SKILL.md` (open only: Step 1.2 items 3b, 4 intro, the 2b branch bullet, 4a, 4c, 5, 5c and the Completion Checklist company line; all other content frozen; reject findings touching frozen regions)
- `agents/skills/done/SKILL.md` (open only: Step 3 items 4a through 4b region, the Step 6 blocked-report line, and the hard-rules list; all other content frozen; reject findings touching frozen regions)
- `agents/skills/generalize/SKILL.md` (open only: the routing fork intro line and entries 2b and 4 of its Integration Points "With learn" section; all other content frozen; reject findings touching frozen regions)
- `projects/.ai-playbook/development_lessons.md` (open only: the See also line of lesson 177; all other content frozen; reject findings touching frozen regions)

**Tests:**
- `scripts/test_check_lesson_scope.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-09-learn-company-scope-placement.md` and rider `docs/history/backlog/2026-09-10-learn-company-vs-project-placement-gate.md`; scope of record, stays under the backlog dir until plan completion per the plans Plan Lifecycle
- `~/.ai-playbook/scripts/*` runtime deployment; machine-local, not repository content
- `.ai-playbook/facts.md`; no path-key changes in either facts file; the `company_guidelines_master` key resolves from the user-level facts file (`~/.ai-playbook/facts.md`), not this repo file
- any other skill's `SKILL.md`; a repo-wide grep on 2026-09-09 found living fork mirror claims only in `learn`, `generalize`, and the lesson 177 See also line of the UL corpus (mentions under docs/plans, docs/reviews, and docs/history are frozen records, not living claims)

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || { echo "not inside a git repo" >&2; exit 1; }
cd "$REPO" || exit 1
fail() { echo "FAIL: $1" >&2; exit 1; }
expect_line() { grep -qF "$1" "$2" || fail "missing obligation in $2: $1"; }
expect_absent() {
  local pat="$1"; shift
  local rc=0
  grep -iqF "$pat" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present: $pat"; fi
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc for: $pat"; fi
  return 0
}

# 1. Validator unit tests (the canonical executable artifact behind the done scope audit)
python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py' || fail "validator unit tests"

# 2. learn Step 1.2 fork obligations; one dedicated probe per obligation
expect_line "Five-branch fork (resolve" agents/skills/learn/SKILL.md
expect_line "(2b) Company-wide convention" agents/skills/learn/SKILL.md
expect_line "Sibling search is required before choosing fork (4)" agents/skills/learn/SKILL.md
expect_line "Separate the generalized rule from its incident witness" agents/skills/learn/SKILL.md
expect_line "Would this rule guide another repository in the same organization" agents/skills/learn/SKILL.md
expect_line "Placement receipt (required in the learn run output)" agents/skills/learn/SKILL.md
expect_line "fork 1, 2, or 2b" agents/skills/learn/SKILL.md
expect_line "company-portability gate (Step 1.2 item 4c)" agents/skills/learn/SKILL.md
expect_line "A team or infrastructure ownership boundary" agents/skills/learn/SKILL.md
expect_line "must also state the residual dependency" agents/skills/learn/SKILL.md
expect_line "do not write the full lesson to the project corpus" agents/skills/learn/SKILL.md
expect_line "blocking placement question" agents/skills/learn/SKILL.md
expect_line "item 5c conditions the write, it does not follow it" agents/skills/learn/SKILL.md
expect_line "If no, continue down the ladder" agents/skills/learn/SKILL.md

# 3. generalize routing-fork mirror (learn Step 1.2 item 5b fan-out, same change set)
expect_line "five-branch fork" agents/skills/generalize/SKILL.md
expect_line "2b. **Company-wide convention**" agents/skills/generalize/SKILL.md
expect_line "company-portability gate" agents/skills/generalize/SKILL.md
expect_line "records its residual dependency" agents/skills/generalize/SKILL.md
expect_line "company-wide conventions are fork 2b" projects/.ai-playbook/development_lessons.md

# 4. done Step 3 audit obligations
expect_line "Pre-commit lesson scope audit" agents/skills/done/SKILL.md
expect_line 'LESSON_SCOPE_SCRIPT:-${HOME}/.ai-playbook/scripts/check_lesson_scope.py' agents/skills/done/SKILL.md
expect_line "do NOT silently commit the narrower placement" agents/skills/done/SKILL.md
expect_line "is a tool failure: stop, report the validator error" agents/skills/done/SKILL.md
expect_line "must not move or duplicate lessons to reconcile placements" agents/skills/done/SKILL.md
expect_line "Never commit a new or substantially edited project lesson whose scope audit" agents/skills/done/SKILL.md
expect_line "or the Step 3 item 4a lesson scope audit" agents/skills/done/SKILL.md
expect_line "fork (4) receipt with no residual dependency stops before commit" agents/skills/done/SKILL.md

# 5. Stale mirror-claim sweep; zero matches expected (forbidden pattern, case-insensitive)
expect_absent "four-way fork" agents/skills/learn/SKILL.md agents/skills/generalize/SKILL.md projects/.ai-playbook/development_lessons.md

# 6. Em-dash gate over the changed files (repo policy, agent_workflow_guidelines.md §39)
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file docs/plans/2026-09-09-learn-company-scope-placement.md agents/skills/learn/SKILL.md agents/skills/done/SKILL.md agents/skills/generalize/SKILL.md scripts/check_lesson_scope.py scripts/test_check_lesson_scope.py || fail "em-dash scan"

# 7. Public hygiene scan from the repo root
bash scripts/scan-public-hygiene.sh || fail "public hygiene scan"
```

Authoring-time RED state (recorded 2026-09-09, pre-execution; rider-fold probes added 2026-09-11): command 1 fails (test module absent), every probe in blocks 2 through 4 fails (obligations not yet inserted, including the rider-fold probes for the residual dependency, blocking placement question, ownership boundary, write-ordering condition, negative-branch ladder, generalize residual record, and done no-residual stop), and the block 5 sweep fires (all four living "four-way" sites still present: learn line 89 twice, learn line 90 once, generalize line 239 once, and the lesson 177 See also line of `projects/.ai-playbook/development_lessons.md` once). The block flips green exactly when Tasks 1 through 3 land. The rider-fold probes were executed against the pre-execution tree at fold time and confirmed RED (zero hits today).

### Task 1: Lesson scope duplicate validator (RED then GREEN)

Files:
- `scripts/check_lesson_scope.py` *(new)*
- `scripts/test_check_lesson_scope.py` *(new)*

- [x] `test_check_lesson_scope.py#test_verbatim_duplicate_flagged`; given a project corpus block and a company master block carrying the identical rule body, expects exit 1 and output naming both blocks
- [x] `test_check_lesson_scope.py#test_near_verbatim_duplicate_flagged`; given the same rule body differing in letter case, whitespace runs, and heading numbering, expects exit 1 and a `DUPLICATE:` output line naming both blocks
- [x] `test_check_lesson_scope.py#test_multiple_duplicates_each_reported`; given two distinct rule blocks in the project corpus each duplicated in the company master, expects exit 1 and two `DUPLICATE:` output lines, one per pair
- [x] `test_check_lesson_scope.py#test_project_only_rule_clean`; given a rule present only in the project corpus, expects exit 0
- [x] `test_check_lesson_scope.py#test_witness_pointer_clean`; given a project corpus entry that is a short pointer line to the company rule without its body, expects exit 0
- [x] `test_check_lesson_scope.py#test_temporary_note_no_false_positive`; given a short temporary session-note-style block sharing topic words but not the rule body with a company rule, expects exit 0
- [x] `test_check_lesson_scope.py#test_ecosystem_tier_out_of_comparison`; given the rule duplicated only against a third file (a language guidelines file) that is not passed as an argument, expects exit 0
- [x] `test_check_lesson_scope.py#test_missing_company_master_clean`; given a present corpus and an absent company master path, expects exit 0 with a warning line on stderr
- [x] `test_check_lesson_scope.py#test_missing_corpus_clean`; given an absent project corpus path, expects exit 0
- [x] `test_check_lesson_scope.py#test_usage_error_exit_two`; given fewer than two path arguments, expects exit 2 with usage on stderr
- [x] `test_check_lesson_scope.py#test_extra_argument_exit_two`; given three path arguments, expects exit 2 with usage on stderr
- [x] `test_check_lesson_scope.py#test_unreadable_corpus_exit_two`; given a corpus file that exists but is unreadable (created then `chmod 0o000`, restored in teardown; skip when running as root), expects exit 2 with an error line on stderr
- [x] `test_check_lesson_scope.py#test_unreadable_company_master_exit_two`; given a company master file that exists but is unreadable (created then `chmod 0o000`, restored in teardown; skip when running as root), expects exit 2 with an error line on stderr
- [x] `test_check_lesson_scope.py#test_short_identical_body_stays_clean`; given a corpus block and a company master block with identical normalized bodies but each under `MIN_RULE_WORDS` words, expects exit 0 (short blocks are witness pointers by design)
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py'` (the test module and the script do not exist yet, discovery errors)
- [x] Write `scripts/check_lesson_scope.py` (minimal implementation of the contract below)
- [x] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py'`
- [x] Commit: `feat: add lesson scope duplicate validator`

Validator contract (the full behavior the implementation must deliver):

- CLI: `python3 check_lesson_scope.py <project_corpus> <company_master>`; exactly two positional path arguments.
- Exit codes: 0 = no duplicate full rule (including cold starts), 1 = at least one duplicate full rule, 2 = usage or IO error.
- Cold starts: an absent corpus or an absent company master prints a one-line warning to stderr and exits 0 (personal-repo and pre-adoption cases; mirrors the `learn` Step 6.6 pattern). An unreadable (existing but unopenable) file is an IO error: exit 2.
- Block model: split each file into blocks at markdown headings (`^#{1,3} `); a block is its heading plus body until the next heading; a file with no headings is one block.
- Normalization: per block, strip leading `#` characters and a leading enumeration token (`12.` or `12.3.`) from the heading, lowercase, and collapse all whitespace runs to single spaces.
- Duplicate rule: a corpus block and a master block are a duplicate full rule when `difflib.SequenceMatcher(None, corpus_text, master_text).ratio() >= DUPLICATE_RATIO` and the shorter block has at least `MIN_RULE_WORDS` normalized words; `DUPLICATE_RATIO = 0.90` and `MIN_RULE_WORDS = 25` as named module constants. Shorter blocks are witness pointers by design and never match.
- Output on exit 1: one line per pair, `DUPLICATE: <file>:<line> <heading> <-> <file>:<line> <heading>`, where `<line>` is the heading line number.
- Style: `#!/usr/bin/env python3`, module docstring stating the mechanical-only scope (semantic scope judgment stays with the learn workflow), `from __future__ import annotations`, stdlib only.

### Task 2: learn company-wide branch, witness separation, receipt, and mirror fan-out

Files:
- `agents/skills/learn/SKILL.md`
- `agents/skills/generalize/SKILL.md` (same change set; `learn` Step 1.2 item 5b mandates updating every living mirror claim in the same edit)
- `projects/.ai-playbook/development_lessons.md` (same change set; lesson 177 See also line)

- [x] In Step 1.2 item 4, replace `Four-way fork (resolve` with `Five-branch fork (resolve`, keeping the rest of the line unchanged
- [x] In Step 1.2 item 3b, replace both `four-way fork` occurrences with `five-branch fork` (the parenthetical and the "Item 4's ... is judgment" sentence)
- [x] Insert new branch bullet between the (2) and (3) bullets of the item 4 fork:

```markdown
   - **(2b) Company-wide convention -> `company_guidelines_master` (facts key)**: a do/do-not rule or convention shared by repositories of the same company or organization because they perform the same kind of work (same integration responsibility, shared platform or delivery conventions), even when their product domains differ and the rule is not universal across organizations. Place the **full rule** in the company guidelines master and keep at most a concise project witness plus a pointer in the incident repo's project corpus; sync repo mirrors after editing the master (Company rule workflow, Step 2). Add a one-line cross-reference in instruction files per the Step 6 placement ladder. **Sibling search is required before choosing fork (4)**: grep the company guidelines master for the lesson's topic keywords first; a hit is strong evidence the company scope applies.
```

- [x] Insert new item between items 4 and 4b:

```markdown
4a. **Separate the generalized rule from its incident witness (required for every candidate lesson).** The generalized rule determines placement; the incident witness (the concrete failure, files, and reproduction) may remain in the project corpus as a short example or pointer. Never let a long witness narrative justify a narrower placement: placement follows the rule, not the story.
```

- [x] Insert new item after item 4b:

```markdown
4c. **Company-portability gate (required before fork (4) full project lesson).** Ask: "Would this rule guide another repository in the same organization that performs the same kind of work, even if its product domain differs?" If **yes**, you are in fork **(2b)**: write the full rule to `company_guidelines_master` first, keep only a concise project witness and pointer in the project corpus, and sync repo mirrors. If you almost chose fork (4) because the incident happened in one company repo, re-run this gate after the 4b stack-portability gate. Anti-pattern: storing a company-wide integration convention as a full project lesson because "it is not universal across every possible project" (that is fork (2b), not fork (4)). A team or infrastructure ownership boundary (which team owns which tickets, components, or delivery stages) binds sibling repos with the same responsibility, so it is company scope, not project scope. If no, continue down the ladder: fork (3) when the witness is the reusable value, fork (4) only with a stated residual dependency.
```

- [x] In Step 1.2 item 5, change `(fork 1 or 2)` to `(fork 1, 2, or 2b)` keeping the rest of the sentence unchanged
- [x] Insert new item after item 5b:

```markdown
5c. **Placement receipt (required in the learn run output).** For every placed lesson, state the selected scope and why each broader scope was rejected (one line per lesson; for example "fork (2b): company-wide convention; not universal (org-specific), not fork (4) (guides sibling repos with the same responsibility)"). Evaluate the residual dependency and the canonical-destination resolution BEFORE executing item 5's corpus write: item 5c conditions the write, it does not follow it. For a fork (4) placement the receipt must also state the residual dependency that keeps the rule project-specific (a material dependency on the service domain, module contract, repository architecture, or project-only operational behavior). If no residual dependency remains, do not write the full lesson to the project corpus: re-route to fork (2b) or fork (3). When the rule is company-scope but `company_guidelines_master` does not resolve (personal repo), report the missing canonical destination as a blocking placement question instead of writing a full project lesson. The receipt is temporary run output; it need not become part of the canonical lesson, but `done`'s pre-commit scope audit uses it as placement evidence.
```

- [x] In the Completion Checklist, insert a new bullet directly after the bullet beginning `incident-repo == cwd-repo verified`:

```markdown
- company-portability gate (Step 1.2 item 4c) ran before every project-specific placement, and the sibling search of `company_guidelines_master` ran before every full project lesson; a placement receipt (item 5c), stating the residual dependency for every fork (4) placement, was emitted for every placed lesson
```

- [x] In `agents/skills/generalize/SKILL.md` "With learn" section, replace the routing fork intro `(mirrors \`learn\` Step 1.2 item 4 four-way fork + 4b)` with `(mirrors \`learn\` Step 1.2 item 4 five-branch fork + 4b/4c)`
- [x] In the same section, insert entry between listed entries 2 and 3:

```markdown
2b. **Company-wide convention** -> `company_guidelines_master` (facts key): a do/do-not rule shared by repositories of the same company or organization because they perform the same kind of work, even when product domains differ and the rule is not universal. Full rule in the company master; incident repos keep at most a concise witness pointer. Require the sibling search and company-portability gate (`learn` 4c) before choosing this over fork (4).
```

- [x] In the same section entry 4, extend the sentence beginning `Require a residual-domain pass` so its gate list reads `... the stack-portability gate (`learn` 4b) and the company-portability gate (`learn` 4c) before choosing this over fork (2)`, and append the follow-on sentence: `a fork (4) placement records its residual dependency in the placement receipt (`learn` Step 1.2 item 5c).`; the sentence is wrapped across two source lines in the file, so locate it by content, not by line
- [x] In `projects/.ai-playbook/development_lessons.md` lesson #177, update its See also line (the one citing `learn` SKILL Step 1.2 item 4): replace `the four-way fork` with `the five-branch fork`, and insert `company-wide conventions are fork 2b, ` immediately before `stack-portable precepts are fork 2`, keeping the rest of the line unchanged
- [x] Verification: `grep -oi "five-branch fork" agents/skills/learn/SKILL.md | wc -l` reports at least 3 and `grep -ci "four-way" agents/skills/learn/SKILL.md agents/skills/generalize/SKILL.md projects/.ai-playbook/development_lessons.md` reports 0 for all three files
- [x] Commit: `skills: add company-wide branch to learn scope fork with mirror fan-out`

### Task 3: done pre-commit lesson scope audit

> **Amendment (2026-09-12, Phase 3 r1-r2 review folds).** The certified verbatim insert block below is the byte-level record as authored; the live `done` Step 3 item 4a text now diverges by these accepted post-review deltas:
> - explicit check order in item 4a.1: resolve `company_guidelines_master` first (trivial pass when absent), then `test -f` the script (warn and continue when absent), then run with stderr captured;
> - any WARNING line on stderr is treated as a placement-path resolution failure (stop before commit and report the unresolved path, like a tool failure), not a clean pass;
> - exit 1 with no `DUPLICATE:` line, and any exit code other than 0/1/2 (including interpreter codes), is treated as a tool failure per the exit 2 path;
> - a mirror-sync precondition clause was added in r1 and removed in r2 as unverifiable; the canonical-master pin (added in r1) remains;
> - item 2's conjunction ("no receipt and the scope cannot be established") was widened to a disjunction ("no receipt, or its scope cannot be established");
> - the validator's matching runs difflib.SequenceMatcher with `autojunk=False` (Task 1 contract, documented in the script docstring);
> - the generalize entry-4 alternates now name fork (2) or fork (2b) (Task 2 mirror, fixed in r2);
> - the r2 rewrite of the 4a.1 tool-failure sentence retired the old probe string "is a tool failure, not a clean pass" (it survives only inside the certified fenced block above), so the Validation Commands probe was updated to the live wording "is a tool failure: stop, report the validator error" (r3 fold F1);
> - learn Step 1.2 item 5c changed "why each broader scope was rejected" to "why each alternative scope was rejected" (one-word delta against the certified Task 2 block, r3 fold F8); the certified block keeps the original wording as the byte-level record;
> - the block model is fence-aware (a `#`-prefixed line inside an open ```/~~~ fence is body text, not a heading boundary; pinned by fence tests) and an unclosed fence is a tool failure (exit 2), amendment r4.

Files:
- `agents/skills/done/SKILL.md`

- [x] Insert new step between Step 3 item 4 and item 4b:

````markdown
4a. **Pre-commit lesson scope audit (when the project lessons corpus is touched).** If the session's staged or unstaged diff creates or substantially edits the project lessons corpus (`docs/maintenance/development_lessons.md`, or `PROJECT_CORPUS_REL` from `lessons_recall.py`), audit scope BEFORE staging it:
   1. **Mechanical duplicate check.** When the company guidelines master resolves (`company_guidelines_master` in facts) and the validator exists, run (with `$PROJECT_CORPUS` and `$COMPANY_MASTER` set to the resolved corpus and master paths; override the script path via `LESSON_SCOPE_SCRIPT` for local testing only):
   ```bash
   python3 "${LESSON_SCOPE_SCRIPT:-${HOME}/.ai-playbook/scripts/check_lesson_scope.py}" "$PROJECT_CORPUS" "$COMPANY_MASTER"
   ```
   Exit 0 = clean; exit 1 = a full rule is duplicated across the project corpus and the company master. Exit 2 (usage or IO error) is a tool failure, not a clean pass: stop, report the validator error, release the lock per Step 6, and return blocked; do not stage the corpus. When the script is absent, print a one-line warning and continue with the placement-evidence check (cold-start; do not block the session on a missing optional validator). When the company master does not resolve (personal repo), the mechanical check passes trivially.
   2. **Placement-evidence check.** Confirm the learn run's placement receipt (`learn` Step 1.2 item 5c) covers every new or substantially edited lesson. If a lesson has no receipt and the scope cannot be established from the receipt, stop before commit and request classification from the user; do NOT silently commit the narrower placement. For a fork (4) lesson, the receipt must state the residual dependency; a fork (4) receipt with no residual dependency stops before commit for reclassification, exactly like a missing receipt.
   3. **On exit 1 (duplicate full rule):** stop before commit, release the lock per Step 6, and return blocked with the validator output; ask the user to classify the lesson (company master vs project corpus). Never move, rewrite, or duplicate lessons automatically.
   4. **Commit boundary:** the project witness and the company guidelines change are committed in the same pass ONLY when both were intentionally produced by the same workflow (`learn` placed them deliberately). done must not move or duplicate lessons to reconcile placements.
````

- [x] In the Step 6 report wording, extend the line `If `blocked` at Step 0 or learn: state why and what the user should run (`stale-clean`, fix corpus, retry).` to `If `blocked` at Step 0, learn, or the Step 3 item 4a lesson scope audit: state why and what the user should run (`stale-clean`, fix corpus, classify the duplicated lesson, retry).`
- [x] In the hard rules list near the end of the skill, insert directly after the rule beginning `Never skip a session-touched, non-gitignored project lessons corpus`:

```markdown
- Never commit a new or substantially edited project lesson whose scope audit (Step 3 item 4a) has not passed.
```

- [x] Verification: `grep -c "check_lesson_scope.py" agents/skills/done/SKILL.md` reports at least 1 and the Step 3 item sequence reads 4, 4a, 4b
- [x] Commit: `skills: add pre-commit lesson scope audit to done`

### Task 4: Final validation and hygiene

Files: none expected (residual fixes land in the files above)

- [x] Run the full Validation Commands block from the repo root → expect every command green
- [x] Commit residual validation fixes, if any: `fix: lesson scope audit residue`
