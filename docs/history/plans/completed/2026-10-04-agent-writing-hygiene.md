# Plan: Agent writing hygiene (comments, commits, plan readability)

Direct user request, 2026-10-04; no backlog origin, no RFC.

Backlog origin: none
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-agent-writing-hygiene-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make what agents write into code comments, commit messages, and plan documents consistently explain why instead of narrating history or hiding behind jargon.

- Two numbered clauses exist in the coding guidelines as the single source of truth: no temporal commentary in code and config comments, with a ticket or document pointer as the escape for deep context, and commit messages that lead with the why while keeping every strictly required format.
- Every surface that composes commits (done, the plans task template, execute-plan, tdd-guide, github-pr-workflow) points at the commit clause, so run-authored commits carry the reason for the change.
- The code review lens names both finding shapes (temporal commentary; what-only commit messages), so review panels probe them by name instead of by memory.
- The plan format renders the Terms dictionary first and a Why section second, and plan review enforces human-readable, dictionary-covered prose from Why through Evaluation Criteria inclusive.

Gate delta: +1 required plan section (Why) and the Terms placeholder flips from optional to always-rendered first position (template schema growth; witness: operator directive 2026-10-04; paying sibling: the Assumptions always-render precedent this copies); +1 review-layer duty declared separately: plan-readiness findings over the Why through Evaluation Criteria range (missing Terms, Terms not first, missing Why, jargon without a Terms entry) block like required elements (witness: operator-observed jargon-dense plans, operator directive same date); zero new refusal classes, hard gates, fences, validator scripts, or schema state fields; every other edit is a prose rule or a reference pointer.

## Terms

- SOT (source of truth): the single document that owns a rule; here `projects/.ai-playbook/coding_guidelines.md`, whose numbered clauses other files reference instead of restating.
- Lens: a review checklist file under `agents/skills/review-agents/` that a review worker applies to a diff or document; this plan edits the language-agnostic documentation lens and the general lens.
- Done sub-agent: the worker that composes and creates the commit at each executed task boundary per the done skill.
- Authoring worktree: the ad-hoc git worktree this authoring session writes in, keyed as the write target for gates and markers.
- Skill-gate marker: the consent marker under `~/.ai-playbook/runtime/skill-invoked/` that must be refreshed before each plan-file write.
- Gate delta: the plan header line pricing the net machinery change across refusal classes, gates, fences, protocol layers, and schema fields.
- RED-today: a validation gate executed at authoring time against the current tree, where it must fail, flipping green exactly when the prescribed edit lands.

## Assumptions

- assume the two SOT clauses land as sections 39 and 40 in `projects/.ai-playbook/coding_guidelines.md`; basis: that document's own header convention (instruction files reference numbered clauses rather than restating), the plans skill documentation-routing table, and the sibling section 35 comment rule.
- assume "temporal commentary" means comments in code and code-adjacent files (configs, build files) that narrate change history or point at time: dates, version notes, added/removed/changed/previously phrasing, temporary or for-now notes, dated TODOs; exemptions: changelog-type documents whose purpose is history, license and copyright headers, time values that are data (schedules, TTLs, timeouts), and condition-based revisit notes per section 28; basis: the user's request text plus the section 28 and 35 compatibility re-derivation done at authoring.
- assume the commit rule keeps every strictly required format (story-key prefixes, change-type prefixes, structural-versus-behavioral statements); the why is the main content wrapped by those formats; basis: the user's wording "besides other strictly required rules or formats".
- assume wiring edits reference the SOT clauses rather than restating their text; basis: the coding guidelines header convention and the instruction-file cross-reference convention.
- assume `agents-best-practices/` is excluded from this plan: it is vendored from an upstream (frontmatter `upstream`) and covers agent-harness design, not project code hygiene; editing it would create fork drift; basis: repo vendored-sync rules.
- assume `scripts/plan_readiness.py` needs no change: it enforces no plan section order, so the Terms-first reorder is prose-only across the plans skill and review-plan; basis: source grep at authoring found no section-order checks in the validator.
- assume plans already in flight absorb the format flip at their next natural edit rather than retroactively; basis: the plans skill metadata-retrofit rule extended to section order.
- assume no mechanical validator for temporal comments or commit whys ships in this plan (grill receipt: deferred); a backlog item may carry one if the review lens proves too weak; basis: grill Q2 user decision, 2026-10-04.

Decision points requiring a grill: plan packaging: one plan covering all arms, source grill Q1 user answer 2026-10-04, affects plan packaging and task structure; enforcement shape: prose rules plus review lens, no validator script, source grill Q2 user answer 2026-10-04, affects Tasks and Review Scope; wiring set: six surfaces plus the SOT, source grill Q3 user answer 2026-10-04, affects Files and Review Scope; readability arm: fold into this plan and rename to 2026-10-04-agent-writing-hygiene.md, source grill Q4 user answer 2026-10-04, affects Gist and task structure; plan-format shape: Terms first and always rendered, new Why section second, Outcome contract unchanged, readability rule binds Why through Evaluation Criteria inclusive, source grill Q5 user answer 2026-10-04, affects Tasks and Review Scope

## Gist & Examples

TLDR: two new numbered coding guidelines (no temporal commentary in code and config comments; commit messages lead with the why) plus a plan-format readability flip (dictionary first, reason second), wired into the six skills that compose or review these artifacts, so agents stop narrating change history and writing what-only commits.

### Arm A: no temporal commentary (SOT section 39)

Comments in code and configs must explain why the code exists, not when or what changed. Git history owns the when; a comment that retells it rots silently. Deep context escapes to a tracker ticket key or a document pointer.

Violation today (the shape the clause bans):

```c
// Removed the retry loop in v2.3 (2026-01-15) after INC-4012;
// reinstate if the queue grows.
```

After this plan:

```c
// Retries are unnecessary: the broker redelivers on its own (see INC-4012).
```

### Arm B: commit messages lead with the why (SOT section 40)

Weak subject today: `PROJ-1234: add retries to invoice sync`. After this plan: `PROJ-1234: retry invoice sync because the billing API drops about 1% of requests under load`, with the body opening on the short why when the subject cannot carry it. Story-key prefixes and other required formats stay exactly as they are.

### Arm C: plan readability (dictionary first, reason second)

The plan template order flips from Outcome, optional Terms to Terms (always rendered, the dictionary), Why (the reason for the change in one to three plain sentences), Outcome (contract unchanged). From Why through Evaluation Criteria inclusive, prose stays human-readable: required jargon only, and every plan- or project-specific term defined in Terms. The review rules change in the same pass: the plans skill template and required-elements prose, review-plan's declaration audit, and a new plan-format gate in the documentation review lens.

## Evaluation Criteria

**Quality dimensions:**
- correctness: sections 39 and 40 each appear exactly once at their site (count gates, not presence); every cross-reference names an existing clause; sections 28 and 35 are pinned unchanged so the new exemptions cannot contradict the existing condition-based revisit rule.
- consistency: wired surfaces reference the SOT clauses; no wiring insertion restates a clause's rule text.
- non-regression: the story-key commit format in done survives; tdd-guide's structural-versus-behavioral item survives; the review-agents portability and doors scripts exit 0; the shared-body runtime-neutrality test passes after the plans and execute-plan insertions.
- writing quality: all prescribed text is plain Globish with zero em-dashes (scan clean) and a passing public-hygiene scan.

**Done when:**
- the nine files carry their prescribed edits on the authoring branch and the full Validation Commands block exits 0 in the authoring worktree.

**Ship when:**
- no external release gate applies: the change is repository-owned prose and takes effect through normal skill usage in this and consumer projects.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `projects/.ai-playbook/coding_guidelines.md` (sections 39 and 40 only; all other sections frozen)
- `agents/skills/plans/SKILL.md` (the task-template commit line, the template block section order, the required-elements Outcome bullet and its new readability sibling, the Writing-section Terms line; all other rules frozen)
- `agents/skills/review-plan/SKILL.md` (declaration audit item 8 only; frozen elsewhere)
- `agents/skills/review-agents/documentation.md` (the new plan-format gate; frozen elsewhere)
- `agents/skills/doing-code-review/general.md` (the new Comments and Commit Messages section; frozen elsewhere)
- `agents/skills/done/SKILL.md` (the Commit message format subsection and its two subject placeholders; frozen elsewhere)
- `agents/skills/execute-plan/SKILL.md` (one sentence appended to the Commit authorization paragraph; frozen elsewhere)
- `agents/skills/tdd-guide/SKILL.md` (one numbered item added to Commit Discipline; frozen elsewhere)
- `agents/skills/github-pr-workflow/SKILL.md` (one bullet added after the gitignored-files bullet; frozen elsewhere)

**Tests:**
- no new or edited test files; the validation commands run existing checkers (`scripts/check_review_agent_portability.py`, `scripts/test_review_agent_doors.py`, the shared-body method of `scripts/test_execute_plan_runtime.py`) unmodified.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/agents-best-practices/`; vendored from an upstream, wrong domain; see Assumptions.
- `scripts/plan_readiness.py`; the validator enforces no section order and gains none in this plan (grill receipt: prose-only enforcement shape).
- `docs/maintenance/glossary.md`; the repo glossary is not the plan dictionary; the per-plan Terms section is.
- this repository's workspace `AGENTS.md`; the user-directed surfaces are the skill library and the coding guidelines.

## Validation Commands

The block anchors itself to the repository root and fails closed on every check: a missing presence pin aborts, a forbidden match aborts, and a grep tool error (rc 2 and above) aborts instead of passing. Zero-match sweeps target only the named skill files, never this plan file: the plan's own quotes are the checker literals, not stale references. The presence pins are RED-today: at authoring time the first gate fails because sections 39 and 40 do not exist yet, and every arm gate flips green exactly when its task lands. The regression pins (story-key format, sections 28 and 35, tdd-guide item 4) are checked against the target files' current bytes and pass both before and after.

Authoring-time execution record (2026-10-04, authoring worktree branch plan-cchw-authoring): the em-dash touched scan is clean after one trailer-line fix; the public-hygiene scan returned `OUTCOME: pass`; `plan_readiness.py --pre-round` returned `OUTCOME: pass` after the commit checklist items gained their classification tags; the extracted validation block passes `bash -n`. RED-today execution recorded: the first actually-failing gate is the section 39 presence pin (`FAIL: missing pin in projects/.ai-playbook/coding_guidelines.md: ## 39. No Temporal Commentary in Code or Config Comments`, exit 1), every insertion gate failing the same absent-pin way today, and the regression-guard pins passing against the current tree (sections 28 and 35 headings, the section 28 revisit sentence, done's story-key prose, execute-plan's push-policy sentence, tdd-guide item 4, the github-pr-workflow gitignored-files bullet). The rule 22 mechanical audit ran the pin-versus-prescription sweep over all 37 validation needles and repaired three pins to byte-match their prescribed spans (the done subject sentence capital T, the two lens bullet bold prefixes); pins with no task-snippet occurrence are the declared regression guards, which check the target files' current bytes instead of a snippet. Post-r1 fold record (2026-10-04): review round 1 returned ready=no with one blocking finding; the fold batch fixed the shared-body invocation (class-qualified form, reviewer-verified rc 0), renumbered the new lens gate to 6 against the existing gate 5, added the rule 40 tail pin to Task 3, reworded the eight task commit subjects why-first per the plan's own section 40, and corrected the Task 2 edit 4 bold quote; the validation block was re-extracted and re-executed RED-today after the fold, with the first failing gate still the section 39 presence pin.

```bash
#!/usr/bin/env bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

expect_present() {
  needle="$1"; file="$2"
  if ! grep -qF -- "$needle" "$file"; then echo "FAIL: missing pin in $file: $needle"; exit 1; fi
}

expect_absent() {
  needle="$1"; file="$2"
  rc=0; grep -qF -- "$needle" "$file" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden match in $file: $needle"; exit 1; fi
  if [ "$rc" -gt 1 ]; then echo "FAIL: grep tool error rc=$rc for $needle in $file"; exit 1; fi
}

expect_count() {
  needle="$1"; file="$2"; want="$3"
  got=$(grep -oF -- "$needle" "$file" | wc -l | tr -d ' ')
  if [ "$got" -ne "$want" ]; then echo "FAIL: count of '$needle' in $file is $got, want $want"; exit 1; fi
}

CG=projects/.ai-playbook/coding_guidelines.md

# Arm A SOT
expect_present '## 39. No Temporal Commentary in Code or Config Comments' "$CG"
expect_count '## 39. No Temporal Commentary in Code or Config Comments' "$CG" 1
expect_present 'point at the owning record instead: a tracker ticket key or a document path' "$CG"
expect_present 'Not commentary (out of scope of this rule)' "$CG"
expect_present 'a revisit trigger stated as a condition (per Minimal Solution Ladder), not as a date' "$CG"

# Arm B SOT
expect_present '## 40. Commit Messages Lead With the Why' "$CG"
expect_count '## 40. Commit Messages Lead With the Why' "$CG" 1
expect_present 'Strictly required formats stay' "$CG"

# SOT freeze pins: existing sections untouched
expect_present '## 28. Minimal Solution Ladder (Before Writing Code)' "$CG"
expect_present '## 35. Do Not Duplicate Relocatable Identifiers in Comments (D)' "$CG"
expect_present 'leave a short comment naming the ceiling and the trigger to revisit' "$CG"

# Arm B wiring: done
expect_present '<why-first concise subject>' agents/skills/done/SKILL.md
expect_absent '<concise description of what and why>' agents/skills/done/SKILL.md
expect_present 'The subject leads with the why after the story key (see coding_guidelines.md 40)' agents/skills/done/SKILL.md
expect_present 'With a story key:' agents/skills/done/SKILL.md
expect_present '[PROJ-1234] <why-first concise subject>' agents/skills/done/SKILL.md

# Arm B wiring: plans template commit line
expect_present '- [ ] Commit: `feat: <why-first short description>`' agents/skills/plans/SKILL.md
expect_absent '- [ ] Commit: `feat: <short description>`' agents/skills/plans/SKILL.md

# Arm B wiring: execute-plan pointer
expect_present 'Run-authored comments and commit messages follow the writing clauses in `projects/.ai-playbook/coding_guidelines.md` (section 39 no temporal commentary; section 40 commit messages lead with the why)' agents/skills/execute-plan/SKILL.md
expect_present '(see user `AGENTS.md` Git Push Policy)' agents/skills/execute-plan/SKILL.md

# Arm B wiring: tdd-guide
expect_present '5. The message leads with the why for the change (see coding_guidelines.md section 40)' agents/skills/tdd-guide/SKILL.md
expect_present '4. Commit message clearly states whether it contains structural or behavioral changes' agents/skills/tdd-guide/SKILL.md

# Arm B wiring: github-pr-workflow
expect_present '- Commit messages follow coding_guidelines.md section 40: the subject leads with a compressed why after any required prefix; when the subject cannot carry the reason, the body opens with the short why.' agents/skills/github-pr-workflow/SKILL.md
expect_present 'Never reference gitignored files' agents/skills/github-pr-workflow/SKILL.md

# Arm C: plans template order and readability prose
tpl_terms=$(grep -nF '[Required: ## Terms; always renders even when empty; the FIRST section immediately after the header metadata block; the plan dictionary]' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)
tpl_why=$(grep -nF '[Required: ## Why; the second section; the reason for the change in one to three plain sentences, per the plain-globish bar]' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)
tpl_outcome=$(grep -nF '[Required: ## Outcome; after Terms and Why; see the required-elements prose for the plain-globish bar]' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)
if [ -z "$tpl_terms" ] || [ -z "$tpl_why" ] || [ -z "$tpl_outcome" ]; then echo "FAIL: template spec lines missing"; exit 1; fi
if [ "$tpl_terms" -lt "$tpl_why" ] && [ "$tpl_why" -lt "$tpl_outcome" ]; then :; else echo "FAIL: template order Terms < Why < Outcome broken ($tpl_terms, $tpl_why, $tpl_outcome)"; exit 1; fi
expect_absent '[Optional: ## Terms' agents/skills/plans/SKILL.md
expect_absent 'before the optional ## Terms' agents/skills/plans/SKILL.md
expect_absent 'as the first section immediately after the header metadata block' agents/skills/plans/SKILL.md
expect_present '## Why' agents/skills/plans/SKILL.md
expect_present 'Every plan carries the readability contract over the section range from `## Why` through `## Evaluation Criteria` inclusive' agents/skills/plans/SKILL.md
expect_present 'Render `## Terms` as the first section' agents/skills/plans/SKILL.md

# Arm C: review-plan declaration audit
expect_present 'after the always-rendered `## Terms` dictionary and the `## Why` reason-for-change section' agents/skills/review-plan/SKILL.md
expect_absent '(first section after the header metadata block; one aim sentence' agents/skills/review-plan/SKILL.md

# Arm C: documentation lens plan-format gate
expect_present '#### 6. Plan-format readability gates (plans only)' agents/skills/review-agents/documentation.md
expect_present 'Dictionary coverage over the rule range' agents/skills/review-agents/documentation.md

# Arm A+B detection lens
expect_present '## Comments and Commit Messages' agents/skills/doing-code-review/general.md
expect_present '**Temporal commentary in code or config comments (coding_guidelines.md section 39):**' agents/skills/doing-code-review/general.md
expect_present '**What-only commit message (coding_guidelines.md section 40):**' agents/skills/doing-code-review/general.md

# Shared-body and review-agents gates (run the real checkers)
python3 scripts/test_execute_plan_runtime.py ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral || { echo "FAIL: shared-body runtime-neutrality"; exit 1; }
python3 scripts/check_review_agent_portability.py >/dev/null || { echo "FAIL: review-agent portability"; exit 1; }
python3 scripts/test_review_agent_doors.py >/dev/null || { echo "FAIL: review-agent doors"; exit 1; }

echo "ALL GATES GREEN"
```

### Task 1: SOT clauses 39 and 40 in the coding guidelines

Files:
- `projects/.ai-playbook/coding_guidelines.md`

Evidence:
- `grep -cF '## 39. No Temporal Commentary in Code or Config Comments' projects/.ai-playbook/coding_guidelines.md` returns 1; covers the section 39 presence and once-only criteria
- `grep -cF '## 40. Commit Messages Lead With the Why' projects/.ai-playbook/coding_guidelines.md` returns 1; covers the section 40 presence and once-only criteria

Append the two clauses after section 38, verbatim:

```markdown
## 39. No Temporal Commentary in Code or Config Comments

**Shape trigger:** A comment in code, a config file, or any file a program reads at runtime narrates when something happened or what changed: dates, release or version numbers, "added", "removed", "changed", "previously", "no longer", "temporary", "for now", "until X migrates", or a dated TODO.

**Rule:** Comments explain why the code exists and what invariants it keeps. Git history owns when things changed and what the diff was; a comment that retells it rots the first time someone edits the code and cannot fail CI. Do not write temporal commentary. When a comment seems to need deeper context than a few lines can give, do not narrate the history: point at the owning record instead: a tracker ticket key or a document path, so one canonical source carries the story.

Allowed: a comment that states why the code is the way it is; a bare ticket key or document reference left where a future reader would otherwise reverse-engineer the reason; a revisit trigger stated as a condition (per Minimal Solution Ladder), not as a date.

Not commentary (out of scope of this rule): license and copyright headers; changelog-type documents whose only purpose is history; time values that are data (a schedule expression, a TTL, a timeout); a condition-based revisit note.

**Example:** Bad: `// Removed the retry loop in v2.3 (2026-01-15) after INC-4012; reinstate if the queue grows.` Good: `// Retries are unnecessary: the broker redelivers on its own (see INC-4012).` The bad comment forces every future reader to reconcile two histories; the good one states the invariant and names the record that carries the evidence.

## 40. Commit Messages Lead With the Why

**Shape trigger:** Any commit message: a one-line subject, or a subject plus body.

**Rule:** The reason for the change is the main content of a commit message. The subject leads with a compressed why, after any prefix the repository requires (a story key, a change type); the body opens with the short why explanation when the subject cannot carry it. Strictly required formats stay: story-key prefixes, change-type prefixes, structural-versus-behavioral statements, and review-marker trailers are all kept; they wrap the why, they do not replace it. A message that says only what changed is a defect: git already shows what changed; only the author knows why it was worth changing.

**Example:** Weak: `PROJ-1234: add retries to invoice sync`. Strong: `PROJ-1234: retry invoice sync because the billing API drops about 1% of requests under load`. With a body: the body opens with the why in one to three sentences, then the notes.
```

- [x] Add sections 39 and 40 to `projects/.ai-playbook/coding_guidelines.md` after section 38 with the verbatim text above [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 1 evidence greps; both return 1 [class: REPOSITORY_TEST]
- [x] Commit: `feat: stop comments retelling history and commits naming only what changed (guidelines 39/40)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: plans skill template reorder and readability prose

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- `grep -nF` chain over the three new template spec lines in `agents/skills/plans/SKILL.md` proves Terms line less than Why line less than Outcome line; covers the template-order criterion
- `! grep -qF '[Optional: ## Terms' agents/skills/plans/SKILL.md` (negated, rc 1 expected); covers the optional-Terms removal criterion

Edits, all in `agents/skills/plans/SKILL.md`:

1. Template block: insert immediately before the `## Outcome` template heading:

```markdown
## Terms

<The plan dictionary: one bullet per plan- or project-specific term with a one-line definition; render even when empty, as: none.>

## Why

<The reason for this change in one to three plain sentences.>
```

2. Template block: replace the line
`[Required: ## Outcome; the first section immediately after the header metadata block, before the optional ## Terms; see the required-elements prose for the plain-globish bar]`
with the three lines:

```markdown
[Required: ## Terms; always renders even when empty; the FIRST section immediately after the header metadata block; the plan dictionary]
[Required: ## Why; the second section; the reason for the change in one to three plain sentences, per the plain-globish bar]
[Required: ## Outcome; after Terms and Why; see the required-elements prose for the plain-globish bar]
```

3. Template block: delete the line `[Optional: ## Terms; required when 3+ project-specific terms; see agent_workflow_guidelines.md §45]`.

4. Required-elements prose: in the bullet beginning `- Every plan must include an **Outcome section** (`## Outcome`) as the first section immediately after the header metadata block: one plain-globish aim sentence`, replace the span `as the first section immediately after the header metadata block` with `after the always-rendered `## Terms` dictionary and the `## Why` reason-for-change section`; the tail from `: one plain-globish aim sentence` onward survives verbatim.

5. Required-elements prose: add this bullet directly after the Outcome bullet:

```markdown
- Every plan carries the readability contract over the section range from `## Why` through `## Evaluation Criteria` inclusive: plain human-readable prose, only required jargon, and every plan- or project-specific term used in that range defined in the `## Terms` dictionary; the plans review and the documentation lens flag violations like any other required element.
```

6. Writing section: replace the sentence `Add `## Terms` after the title when the plan uses 3+ project-specific words.` with `Render `## Terms` as the first section (the plan dictionary, always present even when empty); every plan- or project-specific word used from `## Why` through `## Evaluation Criteria` gets a Terms entry.`

7. Task template: replace the line `- [ ] Commit: `feat: <short description>`` with `- [ ] Commit: `feat: <why-first short description>``.

- [x] Apply edits 1 through 7 to `agents/skills/plans/SKILL.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 2 evidence checks; template order green, optional-Terms sweep clean [class: REPOSITORY_TEST]
- [x] Commit: `feat: put the plan dictionary and the reason first so plans read without tribal jargon` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review-plan declaration audit follows the new order

Files:
- `agents/skills/review-plan/SKILL.md`

Evidence:
- `grep -qF 'after the always-rendered `## Terms` dictionary and the `## Why` reason-for-change section' agents/skills/review-plan/SKILL.md`; covers the audit-order criterion
- `! grep -qF '(first section after the header metadata block; one aim sentence' agents/skills/review-plan/SKILL.md` (negated, rc 1 expected); covers the old-pin removal criterion
- grep -qF with the needle: one aim sentence plus two to four plain-globish result bullets, plus the backtick-quoted Gate delta line per the plans template, priced per the Declaration findings paragraph; findings on its absence or jargon density block like any other required element) -- against agents/skills/review-plan/SKILL.md; covers the rule 40 tail-survival criterion: the pin is the pre-replacement tail as one contiguous string, green today and required green after the replacement

The replacement span ends mid-parenthetical; the tail from ` plus two to four plain-globish result bullets` through `like any other required element)` is load-bearing audit text and must survive the replacement verbatim (the evidence pin above asserts it).

Replace in the declaration audit item 8 the span
`the required `## Outcome` section (first section after the header metadata block; one aim sentence`
with
`the required `## Outcome` section (after the always-rendered `## Terms` dictionary and the `## Why` reason-for-change section; one aim sentence`
, and append to the same item, after `findings on its absence or jargon density block like any other required element)`:

```markdown
; the plan-readability duty lives in the documentation lens (`review-agents/documentation.md`): human-readable prose, required jargon only, and every plan- or project-specific term in the Why through Evaluation Criteria range defined in Terms, with Terms first and Why present, findings blocking like required elements
```

- [x] Apply the item 8 edit to `agents/skills/review-plan/SKILL.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 3 evidence checks; all three green [class: REPOSITORY_TEST]
- [x] Commit: `feat: keep the declaration audit from enforcing a section order the template no longer has` [class: IMPLEMENTATION_REQUIRED]

### Task 4: documentation lens plan-format gate

Files:
- `agents/skills/review-agents/documentation.md`

Evidence:
- `grep -qF '#### 6. Plan-format readability gates (plans only)' agents/skills/review-agents/documentation.md`; covers the new-gate criterion
- `python3 scripts/check_review_agent_portability.py` exits 0 and `python3 scripts/test_review_agent_doors.py` exits 0; covers the review-agents gates criterion

Append after the `#### 5. Language and doc-type conventions` block, immediately before the `### Living-doc gates:` heading (documentation.md already numbers gates 1 through 5; the new gate takes 6):

```markdown
#### 6. Plan-format readability gates (plans only)

For plan documents, run after the decision-order gates:

- **Terms first and always rendered:** the `## Terms` section is the plan dictionary; it is the first section after the header metadata block and renders even when empty. A plan whose Terms is missing, is not first, or is absent while the prose uses plan- or project-specific terms is a finding.
- **Why section present and plain:** the `## Why` section follows Terms and carries the reason for the change in one to three plain sentences. A missing Why, or a Why that narrates history instead of the reason, is a finding.
- **Dictionary coverage over the rule range:** from `## Why` through `## Evaluation Criteria` inclusive, prose stays human-readable with only required jargon, and every plan- or project-specific term used in that range has a `## Terms` entry. A range term without a Terms entry is a finding; this tightens gate 4 for this range, the reader's working surface.
- **Counterparts:** the declaration audit (`review-plan` item 8) flags the section-order half; the plans skill template owns the format. Findings block like required elements.

Suggest: reword to plain English, add the one-line Terms bullet, or (for a missing Terms or Why) add the section per the plans template.
```

- [x] Add gate 6 to `agents/skills/review-agents/documentation.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the review-agents portability and doors scripts; both exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: give plan review the readability gate so jargon without a Terms entry is caught every round` [class: IMPLEMENTATION_REQUIRED]

### Task 5: done skill commit format leads with the why

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -cF '<why-first concise subject>' agents/skills/done/SKILL.md` returns 2 (both heredoc examples); covers the subject-pin criterion
- `! grep -qF '<concise description of what and why>' agents/skills/done/SKILL.md` (negated, rc 1 expected); covers the old-placeholder removal criterion

Edits:

1. In the `### Commit message format` section, replace both subject placeholder lines `[PROJ-1234] <concise description of what and why>` and `<concise description of what and why>` with `[PROJ-1234] <why-first concise subject>` and `<why-first concise subject>` respectively; the surrounding heredoc fences and prose survive.
2. Immediately after the second heredoc example in the same section, add:

```markdown
The subject leads with the why after the story key (see coding_guidelines.md 40): git shows what changed, the message carries why it was worth changing. When the subject cannot carry the reason, the body opens with the short why explanation in one to three sentences, then any notes.
```

- [x] Apply both edits to `agents/skills/done/SKILL.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 5 evidence checks; count is 2, sweep clean [class: REPOSITORY_TEST]
- [x] Commit: `feat: make run-authored commits carry the why so history explains itself` [class: IMPLEMENTATION_REQUIRED]

### Task 6: run-loop and commit-hygiene pointers

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/tdd-guide/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`

Evidence:
- `grep -qF 'Run-authored comments and commit messages follow the writing clauses' agents/skills/execute-plan/SKILL.md`; covers the execute-plan pointer criterion
- `grep -qF '5. The message leads with the why for the change (see coding_guidelines.md section 40)' agents/skills/tdd-guide/SKILL.md`; covers the tdd-guide item criterion
- `grep -qF 'Commit messages follow coding_guidelines.md section 40' agents/skills/github-pr-workflow/SKILL.md`; covers the PR-workflow bullet criterion

Edits:

1. `agents/skills/execute-plan/SKILL.md`, Commit authorization paragraph: append after its final sentence `(see user `AGENTS.md` Git Push Policy).` the sentence: `Run-authored comments and commit messages follow the writing clauses in `projects/.ai-playbook/coding_guidelines.md` (section 39 no temporal commentary; section 40 commit messages lead with the why).`
2. `agents/skills/tdd-guide/SKILL.md`, Commit Discipline list: after item 4 add `5. The message leads with the why for the change (see coding_guidelines.md section 40)`; the existing items and the small-commits sentence survive.
3. `agents/skills/github-pr-workflow/SKILL.md`, PR Descriptions and Stats list: after the bullet beginning `Never reference gitignored files` add the bullet `- Commit messages follow coding_guidelines.md section 40: the subject leads with a compressed why after any required prefix; when the subject cannot carry the reason, the body opens with the short why.`

- [x] Apply the three pointer edits [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 6 evidence greps; all green [class: REPOSITORY_TEST]
- [x] Commit: `feat: point every commit-composing surface at the clauses so wiring cannot drift into what-only habits` [class: IMPLEMENTATION_REQUIRED]

### Task 7: general review lens for comments and commit messages

Files:
- `agents/skills/doing-code-review/general.md`

Evidence:
- `grep -qF '## Comments and Commit Messages' agents/skills/doing-code-review/general.md`; covers the new-section criterion

Append at end of file:

```markdown
## Comments and Commit Messages

- **Temporal commentary in code or config comments (coding_guidelines.md section 39):** a comment that narrates when something happened or what changed (dates, version notes, added/removed/changed phrasing, temporary or for-now notes, dated TODOs) is a finding. The fix states the invariant or why and, when deeper context is genuinely needed, points at the owning tracker ticket or document instead of narrating history. License headers, changelog-type documents, time values that are data, and condition-based revisit notes are not findings.
- **What-only commit message (coding_guidelines.md section 40):** a subject that says what changed without the why, where the why is not carried in a body, is a finding. Required formats (story keys, change types, structural-versus-behavioral statements) are never findings; their absence or replacement by prose is.
```

- [x] Append the lens section to `agents/skills/doing-code-review/general.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Task 7 evidence grep; green [class: REPOSITORY_TEST]
- [x] Commit: `feat: name the two finding shapes so review panels probe them without relying on memory` [class: IMPLEMENTATION_REQUIRED]

### Task 8: full validation sweep and shared-body gate

Files:
- none new; runs the complete Validation Commands block

Evidence:
- the full Validation Commands block; covers every criterion at once, including the shared-body runtime-neutrality test over the Task 2 and Task 6 insertions

- [x] Run the full Validation Commands block in the worktree; expect `ALL GATES GREEN` [class: REPOSITORY_TEST]
- [x] Commit: `feat: prove every prescribed gate green before the plan is called executable` [class: IMPLEMENTATION_REQUIRED]
